"""Connect an owning native adapter to the existing session executor.

Owner adapters supply their qualified edit, measurement, correction, finish and
independent reopen operations. Native subprocesses use the owner's bounded
operation wrapper; all phases share the controller's absolute edit deadline.
"""
from pathlib import Path
import shutil
from tempfile import mkdtemp
import time

from session_plan import sha
from shared_blueprint_contract import measurement_issues


def execute_factory_stage(root, source, stage, target, request, adapter, deadline, guard):
    """Run one protected precision stage and return a controller checkpoint."""
    root = Path(root).resolve()
    source = Path(source)
    if sha(source) != request["source_sha256"]:
        raise ValueError("factory source SHA mismatch")
    attempt = Path(mkdtemp(prefix="factory-", dir=root))
    native = attempt / ("native" + source.suffix)

    def perform(operation, *args):
        if time.monotonic() >= deadline:
            raise TimeoutError("factory edit deadline reached")
        guard()
        result = operation(*args, deadline=deadline)
        if time.monotonic() >= deadline:
            raise TimeoutError("factory operation exceeded edit deadline")
        return result

    def observe(operation):
        observation = perform(operation, native, target)
        issues = measurement_issues(target, request, observation)
        if not isinstance(observation, dict) or observation.get("native_sha256") != sha(native):
            issues.append("native_sha256")
        return observation, issues

    def require_pass(issues):
        if issues:
            raise RuntimeError("factory measurement blocked: " + ", ".join(issues))

    try:
        shutil.copyfile(source, native)
        if sha(native) != request["source_sha256"]:
            raise ValueError("factory source changed during copy")
        perform(adapter.edit, native, target)
        observed, issues = observe(adapter.measure)
        if issues and all(issue.startswith("tolerance:") for issue in issues) and all(
            abs(observed["residuals"][key]) > target["tolerances"][key]
            + target["uncertainty"][key] + observed["uncertainty"][key]
            for _, key in (issue.split(":", 1) for issue in issues)
        ):
            perform(adapter.correct, native, target, observed)
            _, issues = observe(adapter.measure)
        require_pass(issues)
        # The owner adapter performs material/preview and technical QA here.
        # Independent G2 remains on the owning review path.
        evidence = perform(adapter.finish, native, target)
        files = {}
        if evidence is not None:
            if not isinstance(evidence, dict):
                raise ValueError("factory evidence must map relative paths to SHA-256")
            for name, expected in evidence.items():
                if not isinstance(name, str) or Path(name).is_absolute():
                    raise ValueError("factory evidence path must be relative")
                path = (attempt / name).resolve()
                if not path.is_relative_to(attempt) or not path.is_file() or sha(path) != expected:
                    raise ValueError("factory evidence missing, outside attempt or SHA mismatched")
                files[path.relative_to(root).as_posix()] = expected
        saved_sha = sha(native)
        reopened, issues = observe(adapter.reopen)
        if sha(native) != saved_sha:
            issues.append("reopen_changed_native")
        require_pass(issues)
        return {
            "path": native.relative_to(root).as_posix(),
            "sha256": reopened["native_sha256"],
            "reopened": True,
            "fingerprint": stage["fingerprint"],
            "observation": reopened,
            "files": files,
        }
    except BaseException:
        quarantine = root / "quarantine"
        quarantine.mkdir(exist_ok=True)
        attempt.rename(quarantine / attempt.name)
        raise

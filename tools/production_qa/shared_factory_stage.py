"""Connect an owning native adapter to the existing session executor.

Owner adapters supply their qualified edit, measurement, correction, finish and
independent reopen operations. Native subprocesses use the owner's bounded
operation wrapper; all phases share the controller's absolute edit deadline.
"""
import json
from pathlib import Path
import shutil
from tempfile import mkdtemp
import time

from session_plan import sha
from shared_blueprint_contract import finite, measurement_issues, metric_state


def correction_states(target, observation):
    return {
        key: metric_state(residual, target["tolerances"][key],
                          target["uncertainty"][key] + observation["uncertainty"][key])
        for key, residual in observation["residuals"].items()
    }


def correct_items(adapter, native, target, observed, issues, perform, observe, journal):
    """Run only qualified, dependency-safe metric operations on the working copy."""
    attempted = set()
    remeasured = False
    while issues and all(issue.startswith("tolerance:") for issue in issues):
        states = correction_states(target, observed)
        choice = None
        blocked = {}
        for key, state in states.items():
            if state != "OUTSIDE":
                continue
            rule = target["corrections"].get(key)
            if key in attempted or rule is None:
                blocked[key] = "already_attempted" if key in attempted else "unqualified"
                continue
            if (any(states[metric] == "HOLD" for metric in rule["affects"])
                    or any(states[metric] != "PASS" for metric in rule["requires_pass"])):
                blocked[key] = "interference_or_dependency"
                continue
            choice = key
            break
        if choice is None:
            if "HOLD" in states.values() and not remeasured:
                remeasured = True
                observed, issues = observe(adapter.measure)
                journal.append(dict(phase="remeasure", issues=issues, observation=observed))
                continue
            journal.append(dict(phase="stop", states=states, blocked=blocked))
            break

        attempted.add(choice)
        rule = target["corrections"][choice]
        entry = dict(phase="correction", metric=choice, operation_id=rule["operation_id"],
                     before=observed["residuals"], evidence_sha256=observed["evidence_sha256"],
                     blocked=blocked)
        journal.append(entry)
        before_sha = sha(native)
        amount = perform(adapter.propose_correction, native, target, observed, choice)
        if sha(native) != before_sha:
            raise RuntimeError("correction proposal modified the native copy")
        if not finite(amount) or not 0 < abs(amount) <= rule["max_delta"]:
            raise RuntimeError("correction proposal exceeds qualified bounds")
        entry["requested_delta"] = amount
        applied = perform(adapter.correct_metric, native, target, choice, amount)
        if not finite(applied) or applied != amount:
            raise RuntimeError("adapter did not confirm the qualified correction amount")
        entry["applied_delta"] = applied
        updated, issues = observe(adapter.measure)
        entry.update(issues=issues, observation=updated)
        if any(not issue.startswith("tolerance:") for issue in issues):
            return issues
        after_states = correction_states(target, updated)
        response = {key: updated["actual"][key] - old for key, old in observed["actual"].items()}
        entry["response"] = response
        if updated["intersections"] > observed["intersections"]:
            raise RuntimeError("correction increased intersections")
        for key, delta in response.items():
            uncertainty = observed["uncertainty"][key] + updated["uncertainty"][key]
            if ((key not in rule["affects"] and abs(delta) > uncertainty)
                    or (states[key] == "PASS" and after_states[key] != "PASS")
                    or (states[key] == "HOLD" and after_states[key] == "OUTSIDE")
                    or (key != choice and abs(updated["residuals"][key])
                        > abs(observed["residuals"][key]) + uncertainty)):
                raise RuntimeError("correction interfered with metric: " + key)
        if abs(updated["residuals"][choice]) >= abs(observed["residuals"][choice]):
            raise RuntimeError("correction did not reduce its measured residual")
        observed = updated
    return issues


def execute_factory_stage(root, source, stage, target, request, adapter, deadline, guard):
    """Run one protected precision stage and return a controller checkpoint."""
    root = Path(root).resolve()
    source = Path(source)
    if sha(source) != request["source_sha256"]:
        raise ValueError("factory source SHA mismatch")
    attempt = Path(mkdtemp(prefix="factory-", dir=root))
    native = attempt / ("native" + source.suffix)
    journal = []
    journal_path = attempt / "correction-journal.json"

    def write_journal(status, reason=None):
        record = dict(status=status, reason=reason, events=journal)
        try:
            serialized = json.dumps(record, indent=2, allow_nan=False)
        except (TypeError, ValueError):
            if status == "PASS":
                raise
            serialized = json.dumps(dict(status=status, reason=reason, invalid_events=repr(journal)))
        journal_path.write_text(serialized + "\n")

    def perform(operation, *args):
        if time.monotonic() >= deadline:
            raise TimeoutError("factory edit deadline reached")
        guard()
        result = operation(*args, deadline=deadline)
        if time.monotonic() >= deadline:
            raise TimeoutError("factory operation exceeded edit deadline")
        return result

    def observe(operation):
        before_sha = sha(native)
        observation = perform(operation, native, target)
        issues = measurement_issues(target, request, observation)
        if (not isinstance(observation, dict) or observation.get("native_sha256") != before_sha
                or sha(native) != before_sha):
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
        if target.get("corrections") is not None:
            journal.append(dict(phase="initial_measure", observation=observed, issues=issues))
            issues = correct_items(adapter, native, target, observed, issues, perform, observe, journal)
        elif issues and all(issue.startswith("tolerance:") for issue in issues) and all(
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
        if target.get("corrections") is not None:
            journal.append(dict(phase="reopen", observation=reopened))
            write_journal("PASS")
            files[journal_path.relative_to(root).as_posix()] = sha(journal_path)
        return {
            "path": native.relative_to(root).as_posix(),
            "sha256": reopened["native_sha256"],
            "reopened": True,
            "fingerprint": stage["fingerprint"],
            "observation": reopened,
            "files": files,
        }
    except BaseException as exc:
        quarantine = root / "quarantine"
        quarantine.mkdir(exist_ok=True)
        attempt.rename(quarantine / attempt.name)
        if target.get("corrections") is not None:
            journal_path = quarantine / attempt.name / journal_path.name
            write_journal("BLOCKED", str(exc))
        raise

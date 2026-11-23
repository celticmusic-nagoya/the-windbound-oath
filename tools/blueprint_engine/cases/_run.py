"""Shared case runner: engine measurement -> residual -> hand-off -> #468 Factory stage."""
import copy
from pathlib import Path
import shutil
import time

from .. import digest_record
from ..contract import compile_target, handoff
from ..export import write_json
from ..residual import evaluate
from ..sources import file_sha256

ENGINE_DIR = Path(__file__).resolve().parents[1]
ENGINE_FILES = ("measure.py", "residual.py", "contract.py", "geometry.py", "evidence.py")


def engine_dependencies():
    """SHA of the engine code that computes values/states; part of every target fingerprint."""
    return {f"engine/{name}": file_sha256(ENGINE_DIR / name) for name in ENGINE_FILES}

from shared_factory_stage import execute_factory_stage  # #468 (Codex)


def run_group(blueprint, target_id, registry, adapter, *, native, native_sha, baseline,
              dependencies, out, factory=True):
    dependencies = {**dependencies, **engine_dependencies()}
    target, request, engine_issues = compile_target(
        blueprint, target_id, registry, native_sha256=native_sha,
        protected_baseline_sha256=baseline, dependency_hashes=dependencies)
    gate = handoff(target, request, engine_issues, current_dependency_hashes=dependencies,
                   current_protected_sha256=baseline)
    safe = target_id.replace("/", "_")
    write_json(out / "targets" / f"{safe}.json", dict(target=target, request=request))
    write_json(out / "handoff" / f"{safe}.json", gate)

    # Engine measurement on a disposable copy (read-only; for the residual report).
    work = out / "work" / safe
    work.mkdir(parents=True, exist_ok=True)
    copy_path = work / ("native" + Path(native).suffix)
    shutil.copyfile(native, copy_path)
    probe_target = copy.deepcopy(target)
    probe = copy.deepcopy(adapter)
    probe.evidence_files = {}
    observation = probe.measure(copy_path, probe_target)
    report = evaluate(target, observation)
    report.update(target_id=target_id, observation_evidence_sha256=observation["evidence_sha256"],
                  protected_match=observation["protected_sha256"] == baseline,
                  native_sha256=observation["native_sha256"])
    write_json(out / "residual" / f"{safe}.json", report)
    shutil.rmtree(work)

    result = dict(target_id=target_id, residual=report["overall"], counts=report["counts"],
                  factory_ready=gate["factory_ready"], handoff_issues=gate["issues"],
                  target_contract_sha256=digest_record(target), factory="NOT_RUN")
    if factory and gate["factory_ready"]:
        stage = dict(id=f"measure:{target_id}", requires_actual_edit=False,
                     fingerprint=digest_record(dict(target=digest_record(target),
                                                    dependencies=dependencies)))
        root = out / "factory"
        root.mkdir(exist_ok=True)
        adapter.evidence_files = {}
        try:
            checkpoint = execute_factory_stage(root, native, stage, target, request, adapter,
                                               time.monotonic() + 1800, lambda: None)
            result.update(factory="PASS", checkpoint=dict(
                path=checkpoint["path"], sha256=checkpoint["sha256"],
                reopened=checkpoint["reopened"], files=checkpoint["files"],
                requires_actual_edit=checkpoint.get("requires_actual_edit")))
        except Exception as exc:  # Factory fails closed and quarantines the attempt
            result.update(factory="BLOCKED", factory_reason=str(exc)[:400])
    elif factory:
        result.update(factory="BLOCKED", factory_reason="handoff: " + ", ".join(gate["issues"]))
    return result, target, report

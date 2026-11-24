"""Engine acceptance: real native measure -> correct -> re-measure through the #468 Factory.

Input: the #468 cross-run checkpoint (run 45305587537, artifact 14880921255, ZIP SHA
f4fe7108..., bundle 29bdbef2..., revision d6411635..., native fcce6167...; Codex fixture,
not a game asset). The engine supplies blueprint, measurement, residual and correction
contract; editing uses only the #468 qualified fixture operation
(production_qa/native_edit_qa/blender_stage.py `correct`). Lease/fencing, checkpoint
store and restore are the #468 implementations on a job-local transport.

Scenarios (each on its own disposable copy; the restored source is never modified):
  correct      OUTSIDE -> qualified correction -> PASS, saved, reopened, independent
               engine re-measure in a new process, checkpoint stored and read back.
  fault_width  correction that also changes a non-affected metric -> Factory stops.
  fault_gap    correction that pushes a PASS lower-bound clearance below L -> stops.
  stale_token  correction after the lease moved to a new fence -> guard refuses.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import mkdtemp
import time

from .. import digest_record
from ..contract import OperationRegistry, compile_target, handoff
from ..evidence import NATIVE_MEASURED, PROVISIONAL_DESIGN
from ..export import write_json
from ..geometry import Blueprint
from ..measure import BlenderAdapter, baseline_protected_sha
from ..residual import evaluate
from ..sources import file_sha256, register_source
from ._run import engine_dependencies

TOOLS = Path(__file__).resolve().parents[2]
STAGE_SCRIPT = TOOLS / "production_qa" / "native_edit_qa" / "blender_stage.py"   # #468 op
FAULT_SCRIPT = Path(__file__).resolve().parent / "fault_injection_blender.py"     # test only
BUNDLE_SHA = "29bdbef26f3c3afc67eea4a15a9e6bcd0cd8e71efb8b6e732cc20d0698d39b41"
REVISION = "d6411635b93f20a6d89ccc74ba5e86299252ff52"
NATIVE_SHA = "fcce6167a3bb5f5f870fa48178be111ea7e2cd905118909f423c2f5155898d82"
STAGE_KEY = "cube-continuation"
ASSET = "LIND-HOME"   # registered #468 key; used only on this job-local transport (as run_qa)
FIXTURE_ID = "BLUEPRINT-ENGINE-FIXTURE"
CS = "fixture object-aligned world, Z-up"
TARGET_LENGTH = 1.45                      # provisional engine-acceptance design value
GAP_LOWER = 3.9                           # clearance target->protected along Y, lower bound
TOL = 1e-4


def bpy_python():
    return [sys.executable, "-I"]


def run_stage(script, mode, path, value, deadline):
    cmd = [*bpy_python(), str(script), "--", mode, str(path), str(value)]
    timeout = max(1, deadline - time.monotonic())
    subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=timeout)


class CorrectionAdapter(BlenderAdapter):
    """Engine read-only measurement + #468 qualified correction for this fixture.

    The metric x_max is half the object length (symmetric scale about the object
    origin, checked by the anchor_x metric), so a metric delta d is applied as a
    length delta 2d through the #468 `correct` operation.
    """

    def __init__(self, *args, script=STAGE_SCRIPT, extra=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.script, self.extra = script, extra

    def edit(self, native, target, *, deadline):
        return None                        # correction-only stage (edit_mode None)

    def propose_correction(self, native, target, observation, key, *, deadline):
        return -observation["residuals"][key]

    def correct_metric(self, native, target, key, amount, *, deadline):
        value = 2 * amount if self.extra is None else f"{2 * amount}:{self.extra}"
        run_stage(self.script, "correct", native, value, deadline)
        return amount


def restore(artifact_dir, work):
    """Restore the #468 cross-run checkpoint with the #468 store (SHA-verified)."""
    from shared_asset_lease import git
    from shared_git_checkpoint_store import restore_checkpoint
    bundle = Path(artifact_dir) / "checkpoint.bundle"
    if file_sha256(bundle) != BUNDLE_SHA:
        raise ValueError("checkpoint bundle SHA mismatch")
    record = json.loads((Path(artifact_dir) / "restore.json").read_text())
    if record["checkpoint_revision"] != REVISION or record["bundle_sha256"] != BUNDLE_SHA:
        raise ValueError("restore record does not match the pinned checkpoint")
    remote = work / "source.git"
    git("clone", "--bare", "-q", str(bundle), str(remote))
    cwd = os.getcwd()
    os.chdir(remote)
    try:
        records = restore_checkpoint(str(remote), record["seed"].get("asset", "LIND-HOME"),
                                     REVISION, work / "restored", time.monotonic() + 120)
    finally:
        os.chdir(cwd)
    native = work / "restored" / records[STAGE_KEY]["path"]
    if file_sha256(native) != NATIVE_SHA:
        raise ValueError("restored native SHA mismatch")
    return native, record


def blueprint(native):
    bp = Blueprint(blueprint_id="engine-acceptance.native-correction-loop.v1",
                   asset_id=FIXTURE_ID, stage="engine-acceptance-correction",
                   status="ENGINE_ACCEPTANCE_FIXTURE", canon_status="NOT_CANON_FIXTURE")
    bp.add_source(register_source(
        native, source_id="native.fixture", role="NATIVE_WORKING", projection="native-3d",
        coordinate_system=CS, units="m", expected_sha256=NATIVE_SHA,
        provenance=f"#468 cross-run checkpoint {REVISION}, run 45305587537, artifact "
                   "14880921255", license="project-original"))
    metrics = {}
    design = dict(gap_y=GAP_LOWER, x_max=TARGET_LENGTH / 2, x_min=-TARGET_LENGTH / 2, y_max=0.5, y_min=-0.5,
                  anchor_x=0.0)
    for key, value in design.items():
        bp.add_element(element_id="dim." + key, kind="dimension", module="fixture",
                       sources=["native.fixture"], evidence=PROVISIONAL_DESIGN,
                       coordinate_system=CS, units="m", dims=1, value=value, uncertainty=0.0)
        lower = key == "gap_y"
        metrics[key] = dict(element="dim." + key, value=value, tolerance=0.0 if lower else TOL,
                            uncertainty=0.0, evidence=PROVISIONAL_DESIGN,
                            **({"bound": "lower"} if lower else {}))
    bp.add_group(target_id="fixture.length", measurement_id="blueprint_engine.blender_bbox.v1",
                 coordinate_system=CS, units="m", projection="native-3d",
                 operation_id="fixture.scale-x", protection_scope_id="fixture.non-target",
                 tolerance_basis="engine acceptance (float32 bound << 1e-4 m)",
                 metrics=metrics, intersection_limit=0,
                 corrections={"x_max": dict(operation_id="fixture.correct-x", max_delta=0.1,
                                            affects=["x_max", "x_min"],
                                            requires_pass=["y_max", "y_min", "anchor_x",
                                                           "gap_y"])})
    return bp


SELECTORS = {"x_max": ("bounds", ["target"], "max", 0), "x_min": ("bounds", ["target"], "min", 0),
             "y_max": ("bounds", ["target"], "max", 1), "y_min": ("bounds", ["target"], "min", 1),
             "anchor_x": ("anchor", "target", 0), "gap_y": ("gap", "target", "protected", 1)}
PROTECT = ["Camera", "protected"]


def make_adapter(**kwargs):
    return CorrectionAdapter(SELECTORS, "fixture.non-target", protect_objects=PROTECT,
                             python=bpy_python(), **kwargs)


def run(artifact_dir, out):
    from shared_asset_lease import acquire, assert_owned, git, release
    from shared_factory_stage import execute_factory_stage
    from shared_git_checkpoint_store import GitCheckpointStore, restore_checkpoint
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    work = Path(mkdtemp(prefix="loop-", dir=out))
    native, record = restore(artifact_dir, work)
    source_sha = file_sha256(native)
    registry = OperationRegistry()
    evidence = file_sha256(STAGE_SCRIPT)
    registry.register("fixture.scale-x", kind="native_edit", qualified=True,
                      evidence_sha256=evidence, scope="#468 native_edit_qa fixture")
    registry.register("fixture.correct-x", kind="native_correction", qualified=True,
                      evidence_sha256=evidence, scope="#468 native_edit_qa fixture")
    deps = {"468/blender_stage.py": evidence, "checkpoint_bundle": BUNDLE_SHA,
            **engine_dependencies()}
    bp = blueprint(native)
    baseline = baseline_protected_sha(make_adapter(), native)
    target, request, issues = compile_target(bp, "fixture.length", registry,
                                             native_sha256=source_sha,
                                             protected_baseline_sha256=baseline,
                                             dependency_hashes=deps)
    request.update(asset_id=ASSET, stage="engine-acceptance-correction")
    gate = handoff(target, request, issues, current_dependency_hashes=deps,
                   current_protected_sha256=baseline)
    write_json(out / "blueprint.json", bp.to_dict())
    write_json(out / "target.json", dict(target=target, request=request))
    write_json(out / "handoff.json", gate)
    if not gate["factory_ready"]:
        raise SystemExit("handoff refused: " + ", ".join(gate["issues"]))
    stage = dict(id="engine-acceptance-correction",
                 fingerprint=digest_record(dict(target=digest_record(target), deps=deps)))

    # job-local lease transport (#468 single writer / fencing); fixed identity for commit-tree
    for var, val in (("GIT_AUTHOR_NAME", "blueprint-engine"), ("GIT_COMMITTER_NAME", "blueprint-engine"),
                     ("GIT_AUTHOR_EMAIL", "engine@localhost"), ("GIT_COMMITTER_EMAIL", "engine@localhost")):
        os.environ.setdefault(var, val)
    os.chdir(work)
    git("init", "-q")
    git("commit", "--allow-empty", "-qm", "engine acceptance root")
    remote = str(work / "transport.git")
    git("init", "--bare", "-q", remote)
    head = git("rev-parse", "HEAD")

    def scenario(name, adapter, guard_factory):
        root = work / name
        root.mkdir()
        token = acquire(remote, ASSET, head)
        guard = guard_factory(token)
        before = evaluate(target, make_adapter().measure(_copy(native, root), target))
        try:
            checkpoint = execute_factory_stage(root, native, stage, target, request, adapter,
                                               time.monotonic() + 900, guard)
            result = dict(status="PASS", checkpoint=checkpoint, token=token)
        except Exception as exc:
            result = dict(status="BLOCKED", reason=str(exc)[:300])
            q = sorted((root / "quarantine").glob("factory-*"))
            if q:
                journal = json.loads((q[0] / "correction-journal.json").read_text())
                result["quarantine_journal"] = journal
                done = [e for e in journal["events"] if e.get("phase") == "correction"
                        and "observation" in e]
                if done:
                    result["states_after_rejected_correction"] = {
                        k: r["state"] for k, r in
                        evaluate(target, done[-1]["observation"])["metrics"].items()}
            release(remote, ASSET, token) if _owned(remote, token) else None
        result["residual_before"] = before["overall"]
        result["source_unchanged"] = file_sha256(native) == source_sha
        return result

    results = {}
    results["correct"] = scenario("correct", make_adapter(), lambda t: (lambda: assert_owned(remote, ASSET, t)))
    ok = results["correct"]
    if ok["status"] == "PASS":
        cp = ok["checkpoint"]
        out_native = work / "correct" / cp["path"]
        independent = make_adapter().measure(_copy(out_native, work / "independent"), target)
        ok["independent_remeasure"] = evaluate(target, independent)
        ok["output_native_sha256"] = file_sha256(out_native)
        store = GitCheckpointStore(remote, ASSET, work / "correct")
        release(remote, ASSET, store({"engine-acceptance-correction": cp}, ok.pop("token"),
                                     time.monotonic() + 120))
        readback = restore_checkpoint(remote, ASSET, store.previous, work / "readback",
                                      time.monotonic() + 120)
        ok["checkpoint_revision"] = store.previous
        ok["readback_equal"] = readback["engine-acceptance-correction"] == cp
        ok["journal"] = json.loads((work / "correct" / [p for p in cp["files"]
                                    if p.endswith("correction-journal.json")][0]).read_text())
    results["fault_width"] = scenario("fault_width", make_adapter(script=FAULT_SCRIPT, extra="width"),
                                      lambda t: (lambda: assert_owned(remote, ASSET, t)))
    results["fault_gap"] = scenario("fault_gap", make_adapter(script=FAULT_SCRIPT, extra="gap"),
                                    lambda t: (lambda: assert_owned(remote, ASSET, t)))

    def stale(token):
        state = {"calls": 0}

        def guard():
            state["calls"] += 1
            if state["calls"] == 2:            # another writer takes over mid-stage
                release(remote, ASSET, token)
                acquire(remote, ASSET, head)
            assert_owned(remote, ASSET, token)
        return guard
    results["stale_token"] = scenario("stale_token", make_adapter(), stale)

    summary = dict(
        input=dict(run_id="45305587537", artifact_id="14880921255", bundle_sha256=BUNDLE_SHA,
                   revision=REVISION, native_sha256=NATIVE_SHA, restore_run=record["run_id"]),
        target_contract_sha256=digest_record(target), design_sha256=target["sha256"],
        expected=dict(correct="PASS", fault_width="BLOCKED", fault_gap="BLOCKED",
                      stale_token="BLOCKED"),
        results={k: {f: v for f, v in r.items() if f != "checkpoint"} for k, r in results.items()},
        correct_checkpoint=dict((k, results["correct"].get("checkpoint", {}).get(k))
                                for k in ("sha256", "reopened", "files")))
    summary["verdict"] = "PASS" if (
        all(results[k]["status"] == v for k, v in summary["expected"].items())
        and all(r["source_unchanged"] for r in results.values())
        and results["correct"].get("independent_remeasure", {}).get("overall") == "PASS"
        and results["correct"].get("readback_equal") is True
        and results["correct"]["residual_before"] == "OUTSIDE"
        and "interfered" in results["fault_width"].get("reason", "")
        and "interfered" in results["fault_gap"].get("reason", "")) else "FAIL"
    write_json(out / "native_correction_loop.json", summary)
    os.chdir(TOOLS)
    shutil.rmtree(work)                    # native bytes never leave the job
    return summary


def _copy(src, directory):
    Path(directory).mkdir(parents=True, exist_ok=True)
    dst = Path(directory) / ("probe-" + Path(src).name)
    shutil.copyfile(src, dst)
    return dst


def _owned(remote, token):
    from shared_asset_lease import assert_owned
    try:
        assert_owned(remote, ASSET, token)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    s = run(a.artifact, a.out)
    print(json.dumps(dict(verdict=s["verdict"],
                          states={k: v["status"] for k, v in s["results"].items()}), indent=1))
    sys.exit(0 if s["verdict"] == "PASS" else 1)

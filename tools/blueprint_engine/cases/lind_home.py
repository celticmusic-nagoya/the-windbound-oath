"""Map connection case: LIND-HOME (Aidan house) measured candidate blueprint vs native checkpoint.

Design source: measurements.json from the archived measured candidate
(artifact 14684514477; native d35432e4...; MEASURED_CANDIDATE_NOT_CANON, G1 blocked).
Native: home_portal_checkpoint.blend (artifact 14741418957, run 44990707649).
Read-only. Tolerances are regression-audit tolerances, not design tolerances.
"""
import argparse
from pathlib import Path
import json
import shutil

from .. import digest_record
from ..contract import OperationRegistry
from ..evidence import NATIVE_MEASURED, PROVISIONAL_DESIGN
from ..export import bbox_plan_svg, ledger, studio_record, write_json
from ..geometry import Blueprint
from ..measure import BLENDER_SCRIPT, BlenderAdapter, baseline_protected_sha
from ..sources import file_sha256, register_source
from ._run import run_group

DESIGN_SHA = "a06eb61f405ff9883dad71dee7a919e1acde333dea78d5bd88a7b50f90814a55"
NATIVE_SHA = "5adda2956e195504c974271b54a12cf93c50ae53f51f337f63bcb2f03a2db412"
CS = "LIND-HOME asset-local provisional world, Z-up, right-handed"
UNITS = "BU"
ROUNDING_U = 5e-7          # design file stores 6 decimals
AUDIT_TOL = 1e-4           # unchanged-scope regression tolerance (engine default)
AXES = "xyz"
SPLIT = {"COL_AIDANHOUSE_porch_posts": ["COL_AIDANHOUSE_porch_post_east",
                                        "COL_AIDANHOUSE_porch_post_west"]}


def qualify_measurement(native, design, work, python):
    """Repeatability (2 processes) + agreement with the independent design measurement."""
    work.mkdir(parents=True, exist_ok=True)
    copy_path = work / "native.blend"
    shutil.copyfile(native, copy_path)
    probe = BlenderAdapter({}, "qualification", python=python)
    first, second = probe.raw(copy_path), probe.raw(copy_path)
    agreement = {}
    for obj in design["objects"]:
        rec = first["objects"].get(obj["name"])
        if rec and "bbox_min" in rec:
            agreement[obj["name"]] = max(abs(a - b) for a, b in zip(
                obj["bounds"][0] + obj["bounds"][1], rec["bbox_min"] + rec["bbox_max"]))
    record = dict(operation="blueprint_engine.measure.blender_bbox.v1", kind="read_only_measure",
                  native_sha256=file_sha256(copy_path), bpy=first["bpy_version"],
                  build_hash=first["build_hash"], repeat_identical=first == second,
                  agreement_max_abs=max(agreement.values()), agreement_objects=len(agreement),
                  unmatched=[o["name"] for o in design["objects"] if o["name"] not in agreement],
                  script_sha256=file_sha256(BLENDER_SCRIPT))
    record["qualified"] = record["repeat_identical"] and record["agreement_max_abs"] <= 2 * ROUNDING_U
    shutil.rmtree(work)
    return record


def build(design_path, native_path):
    design = json.loads(Path(design_path).read_text())
    bp = Blueprint(blueprint_id="LIND-HOME-01.measured-audit.v1", asset_id="LIND-HOME-01",
                   stage="blueprint-measurement-audit", status="ENGINE_CONNECTION_TEST",
                   canon_status="MEASURED_CANDIDATE_NOT_CANON")
    bp.add_source(register_source(
        design_path, source_id="design.measured_candidate", role="CANDIDATE",
        projection="native-3d", coordinate_system=CS, units=UNITS, expected_sha256=DESIGN_SHA,
        provenance=f"{design['status']}; native {design['source_sha256']}; commit "
                   f"{design['source_commit']}; {design['provenance']}; lind branch evidence.zip "
                   "(artifact 14684514477)", license="project-original"))
    bp.add_source(register_source(
        native_path, source_id="native.checkpoint", role="NATIVE_WORKING",
        projection="native-3d", coordinate_system=CS, units=UNITS, expected_sha256=NATIVE_SHA,
        provenance="home_portal_checkpoint.blend, artifact 14741418957, run 44990707649",
        license="project-original"))
    groups = {"collision": {}, "shell": {}, "porch": {}, "anchors": {}}
    selectors = {}
    for obj in design["objects"]:
        name = obj["name"]
        eid = "bounds." + name
        bp.add_element(element_id=eid, kind="bounds", module=name.split("_")[0].lower(),
                       sources=["design.measured_candidate"], evidence=NATIVE_MEASURED,
                       coordinate_system=CS, units=UNITS, dims=3,
                       value=obj["bounds"][0] + obj["bounds"][1], uncertainty=ROUNDING_U,
                       notes=f"{obj['vertices']} verts; collections {obj['collections']}")
        group = ("porch" if name in SPLIT else "collision" if name.startswith("COL_")
                 else "shell")
        names = SPLIT.get(name, [name])
        for i, side in enumerate(("min", "max")):
            for axis in range(3):
                key = f"{name}.{side}.{AXES[axis]}"
                groups[group][key] = dict(element=eid, select=3 * i + axis,
                                          value=obj["bounds"][i][axis], tolerance=AUDIT_TOL,
                                          uncertainty=ROUNDING_U, evidence=NATIVE_MEASURED)
                selectors[key] = ("bounds", names, side, axis)
    for anchor in design["anchors"]:
        name = anchor["name"]
        eid = "anchor." + name
        xyz = [anchor["transform"][i][3] for i in range(3)]
        bp.add_element(element_id=eid, kind="anchor", module="gameplay",
                       sources=["design.measured_candidate"], evidence=NATIVE_MEASURED,
                       coordinate_system=CS, units=UNITS, dims=3, value=xyz,
                       uncertainty=ROUNDING_U)
        for axis in range(3):
            key = f"{name}.{AXES[axis]}"
            groups["anchors"][key] = dict(element=eid, select=axis, value=xyz[axis],
                                          tolerance=AUDIT_TOL, uncertainty=ROUNDING_U,
                                          evidence=NATIVE_MEASURED)
            selectors[key] = ("anchor", name, axis)
    bp.add_element(element_id="spec.porch_collision_gap", kind="dimension", module="collision",
                   sources=["native.checkpoint"], evidence=PROVISIONAL_DESIGN,
                   coordinate_system=CS, units=UNITS, dims=1, value=1.0, uncertainty=0.0,
                   notes="owner checkpoint.json porch_target_min 1.0 BU; design minimum, "
                         "not measured")
    bp.add_question("porch-split", "Design measured one COL_AIDANHOUSE_porch_posts proxy; the "
                    "native checkpoint has east/west posts. Union-bbox mapping is an engine "
                    "hypothesis; owner must re-issue the porch target.", ["lind-home.porch"])
    bp.add_question("g1-provenance", "Design source is G1_BLOCKED (QA hash mismatch); targets "
                    "are candidate measurements, not canon.", list(groups))
    for name, metrics in groups.items():
        bp.add_group(target_id=f"lind-home.{name}", measurement_id=f"bpy-bbox.{name}",
                     coordinate_system=CS, units=UNITS, projection="native-3d", metrics=metrics,
                     operation_id="blueprint_engine.measure.blender_bbox.v1",
                     protection_scope_id="LIND-HOME.scene-all",
                     tolerance_basis="regression audit 1e-4 BU; not a design tolerance",
                     corrections=({k: dict(operation_id="lind-home.porch.collision_move",
                                           max_delta=1.0, affects=[k], requires_pass=[])
                                   for k in metrics if ".y" in k[-2:]} if name == "porch"
                                  else None),
                     intersection_limit=0 if name == "porch" else None)
    return bp, design, selectors


def run(design_path, native_path, out, python=None):
    out = Path(out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    bp, design, selectors = build(design_path, native_path)
    qual = qualify_measurement(native_path, design, out / "qual-work", python)
    write_json(out / "qualification.json", qual)
    registry = OperationRegistry()
    registry.register("blueprint_engine.measure.blender_bbox.v1", kind="read_only_measure",
                      qualified=qual["qualified"],
                      evidence_sha256=file_sha256(out / "qualification.json"))
    registry.register("lind-home.porch.collision_move", kind="correction", qualified=False,
                      notes="owner operation; not qualified in this engine")
    write_json(out / "blueprint.json", bp.to_dict())
    dependencies = {"design": DESIGN_SHA, "measure_blender.py": file_sha256(BLENDER_SCRIPT),
                    "blueprint": bp.digest()}
    adapter_proto = dict(protected_scope_id="LIND-HOME.scene-all", python=python)
    baseline = baseline_protected_sha(BlenderAdapter({}, **adapter_proto), _copy(native_path, out))
    results, plan_boxes, plan_anchors = [], [], []
    for target_id, group in bp.data["groups"].items():
        adapter = BlenderAdapter({k: selectors[k] for k in group["metrics"]}, **adapter_proto)
        result, target, report = run_group(bp, target_id, registry, adapter, native=native_path,
                                           native_sha=NATIVE_SHA, baseline=baseline,
                                           dependencies=dependencies, out=out)
        results.append(result)
        rows = report["metrics"]
        for eid in sorted({m["element"] for m in group["metrics"].values()}):
            keys = [k for k, m in group["metrics"].items() if m["element"] == eid]
            state = ("OUTSIDE" if any(rows[k]["state"] == "OUTSIDE" for k in keys) else
                     "HOLD" if any(rows[k]["state"] == "HOLD" for k in keys) else "PASS")
            label = eid.split(".", 1)[1]
            if eid.startswith("bounds."):
                t = bp.element_value(eid)
                pick = lambda s, a: rows[f"{label}.{s}.{a}"]
                plan_boxes.append((label, [t[0], t[1], t[3], t[4]],
                                   [pick("min", "x")["actual"], pick("min", "y")["actual"],
                                    pick("max", "x")["actual"], pick("max", "y")["actual"]], state))
            else:
                plan_anchors.append((label, bp.element_value(eid)[:2], state))
    (out / "_native.blend").unlink()
    shutil.rmtree(out / "work", ignore_errors=True)
    preview = bbox_plan_svg(out / "preview_plan.svg", "LIND-HOME blueprint vs native (top view, BU)",
                            [b for b in plan_boxes if not b[0].startswith("STG_")], plan_anchors)
    summary = dict(case="lind-home", qualification=qual, results=results,
                   open_questions=bp.data["open_questions"])
    write_json(out / "case_summary.json", summary)
    files = ledger(out)
    write_json(out / "studio.json", studio_record(
        asset_id="LIND-HOME-01", case_id="lind-home.measured-audit", blueprint_summary=bp.summary(),
        groups=results, readiness="ISOLATED_PASS" if any(r["factory"] == "PASS" for r in results)
        else "BLOCKED",
        qa=dict(G1="BLOCKED", G2="NOT_RUN", G3="NOT_RUN", G4="NOT_RUN"),
        files={k: v["sha256"] for k, v in files.items()},
        limitations=["read-only measurement; no edit or correction executed",
                     "design source is G1-blocked candidate, not canon",
                     "cross-run restore NOT_RUN in this case", "independent art QA not applicable"]))
    ledger(out)
    return summary


def _copy(native, out):
    path = Path(out) / "_native.blend"
    shutil.copyfile(native, path)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", required=True)
    parser.add_argument("--native", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--python", nargs="+", help="command running a bpy-capable Python")
    args = parser.parse_args()
    summary = run(args.design, args.native, args.out, args.python)
    print(json.dumps([{k: r[k] for k in ("target_id", "residual", "counts", "factory")}
                      for r in summary["results"]], indent=1))


if __name__ == "__main__":
    main()

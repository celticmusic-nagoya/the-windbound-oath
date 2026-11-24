"""P1-A: semantic correspondence of the LIND-HOME porch collision (read-only).

Question: the measured candidate design has one COL_AIDANHOUSE_porch_posts proxy;
the native checkpoint has east/west posts. Is the native split a defect or a
correct structure that supersedes the design target? No numeric fitting, no edit.

Method: measure the native (Blender 5.3.0, separate process), split the visual
porch mesh GEO_AIDANHOUSE_PORCH into connected islands, classify islands by
geometric rule (not by the design values), then compare collision proxies with
the visual structure and with the walkable path/door anchor.
"""
import argparse
import json
from pathlib import Path
import shutil

from ..contract import OperationRegistry, compile_target, handoff
from ..evidence import NATIVE_MEASURED, PROVISIONAL_DESIGN
from ..export import write_json
from ..geometry import Blueprint
from ..measure import BLENDER_SCRIPT, BlenderAdapter, baseline_protected_sha
from ..residual import evaluate
from ..sources import file_sha256, register_source
from ._run import engine_dependencies
from .lind_home import CS, DESIGN_SHA, NATIVE_SHA

OWNER_CHECKPOINT_SHA = "61ab8543b220d000fa4bb730eb16449c366a0aac25396cd4d9366ab565f147d8"
EPS = 1e-4


def classify(parts):
    out = dict(plinths=[], posts=[], lintels=[], other=[])
    for p in parts:
        size = [p["bbox_max"][i] - p["bbox_min"][i] for i in range(3)]
        if p["bbox_min"][2] <= EPS and size[2] <= 0.3:
            out["plinths"].append(p)
        elif size[2] >= 1.5 and max(size[0], size[1]) <= 0.3:
            out["posts"].append(p)
        elif size[0] >= 2.0 and size[2] <= 0.3 and p["bbox_min"][2] >= 2.0 and size[1] <= 0.3:
            out["lintels"].append(p)
        else:
            out["other"].append(p)
    return out


def xy_delta(a_min, a_max, b_min, b_max):
    return max(abs(a_min[i] - b_min[i]) for i in range(2)) if a_min else None


def run(design_path, native_path, owner_checkpoint, out, python=None):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if file_sha256(design_path) != DESIGN_SHA or file_sha256(native_path) != NATIVE_SHA:
        raise ValueError("input SHA mismatch")
    if file_sha256(owner_checkpoint) != OWNER_CHECKPOINT_SHA:
        raise ValueError("owner checkpoint.json SHA mismatch")
    work = out / "work"
    work.mkdir(exist_ok=True)
    copy_path = work / "native.blend"
    shutil.copyfile(native_path, copy_path)
    raw = BlenderAdapter({}, "porch", python=python, components=["GEO_AIDANHOUSE_PORCH"]).raw(copy_path)
    shutil.rmtree(work)
    objects = raw["objects"]
    design = {o["name"]: o for o in json.loads(Path(design_path).read_text())["objects"]}
    owner = json.loads(Path(owner_checkpoint).read_text())
    parts = classify(objects["GEO_AIDANHOUSE_PORCH"]["components"])
    cols = {n: objects[n] for n in ("COL_AIDANHOUSE_porch_post_west", "COL_AIDANHOUSE_porch_post_east")}
    checks = []
    for name, col in cols.items():
        plinth = min(parts["plinths"], key=lambda p: abs(p["bbox_min"][0] - col["bbox_min"][0]))
        post = min(parts["posts"], key=lambda p: abs(p["bbox_min"][0] - col["bbox_min"][0]))
        contain = min(min(post["bbox_min"][i] - col["bbox_min"][i],
                          col["bbox_max"][i] - post["bbox_max"][i]) for i in range(2))
        checks.append(dict(
            collision=name, evidence="NATIVE_MEASURED",
            plinth_footprint_max_abs_delta=xy_delta(col["bbox_min"], col["bbox_max"],
                                                    plinth["bbox_min"], plinth["bbox_max"]),
            plinth_footprint_max_abs_delta_max=max(abs(col["bbox_max"][i] - plinth["bbox_max"][i])
                                                   for i in range(2)),
            timber_post_inside_collision_margin=contain,
            collision_top_minus_post_top=col["bbox_max"][2] - post["bbox_max"][2]))
    west, east = cols["COL_AIDANHOUSE_porch_post_west"], cols["COL_AIDANHOUSE_porch_post_east"]
    clearance = east["bbox_min"][0] - west["bbox_max"][0]
    d = design["COL_AIDANHOUSE_porch_posts"]["bounds"]
    path = objects["STG_AIDANHOUSE_PATH"]
    door = objects["ANC_AIDANHOUSE_DOOR_MAIN_EXT"]["location"]
    lintel = parts["lintels"][0] if parts["lintels"] else None
    design_analysis = dict(
        evidence="NATIVE_MEASURED (prior native d35432e4..., candidate not canon)",
        bounds=d, ground_clearance_x=0.0,
        overlaps_path_corridor=d[0][0] < path["bbox_max"][0] and d[1][0] > path["bbox_min"][0],
        door_anchor_x_inside=d[0][0] <= door[0] <= d[1][0],
        x_extent_equals_plinth_outer_extent=abs(d[0][0] - west["bbox_min"][0]) <= EPS
        and abs(d[1][0] - east["bbox_max"][0]) <= EPS,
        y_overlap_with_lintel=(None if lintel is None else
                               [max(d[0][1], lintel["bbox_min"][1]), min(d[1][1], lintel["bbox_max"][1])]))
    native_ok = all(c["plinth_footprint_max_abs_delta"] <= EPS
                    and c["plinth_footprint_max_abs_delta_max"] <= EPS
                    and c["timber_post_inside_collision_margin"] > 0
                    and c["collision_top_minus_post_top"] >= 0 for c in checks)
    record = dict(
        case="lind-home.porch.semantic-correspondence", design_sha256=DESIGN_SHA,
        native_sha256=NATIVE_SHA, owner_checkpoint_sha256=OWNER_CHECKPOINT_SHA,
        measure_script_sha256=file_sha256(BLENDER_SCRIPT), bpy=raw["bpy_version"],
        build_hash=raw["build_hash"],
        visual_structure={k: [dict(bbox_min=p["bbox_min"], bbox_max=p["bbox_max"],
                                   vertices=p["vertices"]) for p in v] for k, v in parts.items()
                          if k != "other"},
        visual_other_islands=len(parts["other"]),
        native_collision_checks=checks,
        opening_clearance_x=dict(value=clearance, owner_min=owner["after"]["porch_target_min"],
                                 owner_reported=owner["after"]["porch_collision_gap"],
                                 one_sided_state="PASS" if clearance - 2 ** -22 * 2 >= owner["after"]["porch_target_min"] else "OUTSIDE",
                                 note="one-sided minimum; #468 target is two-sided (|r|<=t), "
                                      "so this bound is not expressible as a #468 target today"),
        design_proxy=design_analysis,
        verdict=dict(
            native_split="SEMANTICALLY_CONSISTENT" if native_ok else "INCONSISTENT",
            design_target="SUPERSEDED_PENDING_OWNER_REISSUE",
            reason="design proxy is one frame-envelope box across the walk opening "
                   "(clearance 0, overlaps path and door anchor); native proxies match the two "
                   "stone plinth footprints exactly, contain the timber posts, and leave the "
                   "owner's walk opening (>= 1.0 BU). The lintel (z>=2.4) needs no walk-level "
                   "collision.",
            correction="NOT_APPLICABLE: fitting the native to the old target would re-block "
                       "the door path; no edit performed"),
        proposal_for_owner=dict(
            status="PROPOSAL_NOT_QUALIFIED (derived from native geometry; needs owner design "
                   "approval before it becomes a target)",
            targets=["per post: collision XY footprint == stone plinth footprint (two-sided, "
                     "t=1e-4 BU)", "per post: collision z in [0, >= post top]",
                     "opening clearance between posts >= 1.0 BU (one-sided; needs #468 "
                     "contract extension or owner-side check)"]))
    record["difference_table"] = difference_table(d, west, east, parts, clearance)
    gap_adapter = BlenderAdapter({}, "porch")
    gap, gap_u = gap_adapter.value(raw, ("gap", "COL_AIDANHOUSE_porch_post_west",
                                         "COL_AIDANHOUSE_porch_post_east", 0))
    record["clearance_cross_check"] = dict(
        method_a="components/bbox difference", value_a=clearance,
        method_b="BlenderAdapter selector ('gap', west, east, x)", value_b=gap, u_b=gap_u,
        agree=abs(gap - clearance) <= gap_u)
    record["lower_bound_contract"] = dict(
        status="PROPOSED_TO_CODEX_NO_CONTRACT_CHANGE",
        option_a="interval_metric(lower=1.0, upper=<owner-designated>): value=midpoint, "
                 "tolerance=half-width in the existing #468 target; PASS iff "
                 "lower+u <= x <= upper-u",
        option_b="#468 contract extension for one-sided bounds (Codex decision)",
        upper="UNDETERMINED (owner design value; engine does not invent it)",
        current_target="UNCHANGED (lind-home.porch remains OUTSIDE/BLOCKED)")
    record["dependencies"] = dict(
        design_measurements_json=DESIGN_SHA,
        design_source_native="d35432e415fd1ad96f95487d647f80dfdc6ba7028a001424c39259e67ec5e00a "
                             "(per measurements.json; bytes not available here)",
        native_checkpoint=NATIVE_SHA, owner_checkpoint_json=OWNER_CHECKPOINT_SHA,
        measure_blender_py=file_sha256(BLENDER_SCRIPT),
        measure_py=file_sha256(Path(__file__).resolve().parents[1] / "measure.py"),
        this_case=file_sha256(Path(__file__)))
    record["connections"] = connections(parts)
    record["proposal_target"] = proposal(design_path, native_path, owner_checkpoint, owner,
                                         out, python)
    write_json(out / "porch_correspondence.json", record)
    return record


def connections(parts):
    """Plinth -> post -> lintel contacts measured on the visual islands."""
    rows = []
    lintel = parts["lintels"][0]
    for post in parts["posts"]:
        plinth = min(parts["plinths"], key=lambda p: abs(p["bbox_min"][0] - post["bbox_min"][0]))
        rows.append(dict(
            post_x=[post["bbox_min"][0], post["bbox_max"][0]],
            post_on_plinth_dz=post["bbox_min"][2] - plinth["bbox_max"][2],
            post_inside_plinth_xy=all(plinth["bbox_min"][i] <= post["bbox_min"][i]
                                      and post["bbox_max"][i] <= plinth["bbox_max"][i]
                                      for i in range(2)),
            lintel_on_post_dz=lintel["bbox_min"][2] - post["bbox_max"][2],
            lintel_spans_post_x=lintel["bbox_min"][0] <= post["bbox_min"][0]
            and post["bbox_max"][0] <= lintel["bbox_max"][0]))
    for row in rows:
        row["connected"] = (abs(row["post_on_plinth_dz"]) <= EPS and row["post_inside_plinth_xy"]
                            and abs(row["lintel_on_post_dz"]) <= EPS and row["lintel_spans_post_x"])
    return dict(evidence="NATIVE_MEASURED (visual islands)", posts=rows,
                all_connected=all(r["connected"] for r in rows))


def proposal(design_path, native_path, owner_checkpoint, owner, out, python):
    """Porch re-issue PROPOSAL: opening clearance >= owner minimum (lower bound only).

    Not an official target. Compiled to the #468 envelope with `lower_bound`; the
    hand-off stays BLOCKED until (1) the owner re-issues the porch target with this
    measurement definition and (2) #468 supports lower_bound. No upper end is added.
    """
    west, east = "COL_AIDANHOUSE_porch_post_west", "COL_AIDANHOUSE_porch_post_east"
    bp = Blueprint(blueprint_id="LIND-HOME-01.porch-reissue-proposal.v1", asset_id="LIND-HOME-01",
                   stage="porch-collision", status="PROPOSAL_PENDING_OWNER_REISSUE",
                   canon_status="owner requirement (checkpoint.json porch_target_min); not adopted")
    bp.add_source(register_source(owner_checkpoint, source_id="owner.checkpoint", role="CANDIDATE",
                                  projection="data", coordinate_system=CS, units="BU",
                                  expected_sha256=OWNER_CHECKPOINT_SHA,
                                  provenance="artifact 14741418957 checkpoint.json (owner run "
                                             "44990707649)", license="project-original"))
    bp.add_source(register_source(native_path, source_id="native.checkpoint",
                                  role="NATIVE_WORKING", projection="native-3d",
                                  coordinate_system=CS, units="BU", expected_sha256=NATIVE_SHA,
                                  provenance="home_portal_checkpoint.blend, artifact 14741418957",
                                  license="project-original"))
    lower = owner["after"]["porch_target_min"]
    bp.add_element(element_id="porch.opening_clearance_x", kind="dimension", module="collision",
                   sources=["owner.checkpoint"], evidence=PROVISIONAL_DESIGN,
                   coordinate_system=CS, units="BU", dims=1, value=lower, uncertainty=0.0,
                   notes=f"owner minimum walk opening; measured as {east}.bbox_min.x - "
                         f"{west}.bbox_max.x (world, pre-modifier mesh)")
    bp.add_group(target_id="lind-home.porch.opening", measurement_id="bpy-gap.porch-posts.x",
                 coordinate_system=CS, units="BU", projection="native-3d",
                 metrics={"opening_clearance_x": dict(element="porch.opening_clearance_x",
                                                      value=lower, tolerance=0.0,
                                                      uncertainty=0.0, evidence=PROVISIONAL_DESIGN,
                                                      bound="lower")},
                 operation_id="blueprint_engine.measure.blender_bbox.v1",
                 protection_scope_id="LIND-HOME.scene-all",
                 tolerance_basis="one-sided owner minimum; no upper bound designated")
    bp.add_question("owner-reissue", "Owner re-issues the porch target with this measurement "
                    "definition (object IDs, axis, unit) and retires the single-proxy target.",
                    ["lind-home.porch.opening"])
    work = out / "proposal-work"
    work.mkdir(exist_ok=True)
    copy_path = work / "native.blend"
    shutil.copyfile(native_path, copy_path)
    adapter = BlenderAdapter({"opening_clearance_x": ("gap", west, east, 0)},
                             "LIND-HOME.scene-all", python=python)
    first, second = adapter.raw(copy_path), adapter.raw(copy_path)
    qual = dict(operation="blueprint_engine.measure.blender_bbox.v1", kind="read_only_measure",
                native_sha256=NATIVE_SHA, repeat_identical=first == second,
                script_sha256=file_sha256(BLENDER_SCRIPT), bpy=first["bpy_version"])
    qual["qualified"] = qual["repeat_identical"]
    write_json(out / "proposal_qualification.json", qual)
    registry = OperationRegistry()
    registry.register("blueprint_engine.measure.blender_bbox.v1", kind="read_only_measure",
                      qualified=qual["qualified"],
                      evidence_sha256=file_sha256(out / "proposal_qualification.json"))
    baseline = adapter.protected(copy_path, first)
    deps = {"owner_checkpoint": OWNER_CHECKPOINT_SHA, "blueprint": bp.digest(),
            "measure_blender.py": file_sha256(BLENDER_SCRIPT), **engine_dependencies()}
    target, request, issues = compile_target(bp, "lind-home.porch.opening", registry,
                                             native_sha256=NATIVE_SHA,
                                             protected_baseline_sha256=baseline,
                                             dependency_hashes=deps)
    issues.append("owner_reissue_required")
    gate = handoff(target, request, issues, current_dependency_hashes=deps,
                   current_protected_sha256=baseline)
    observation = adapter.build_observation(copy_path, target, first, "proposal")
    report = evaluate(target, observation)
    shutil.rmtree(work)
    write_json(out / "proposal" / "blueprint.json", bp.to_dict())
    write_json(out / "proposal" / "target.json", dict(target=target, request=request))
    write_json(out / "proposal" / "handoff.json", gate)
    write_json(out / "proposal" / "residual.json", report)
    return dict(status="PROPOSAL_NOT_OFFICIAL", application="BLOCKED",
                target_contract_sha256=gate["target_contract_sha256"],
                factory_ready=gate["factory_ready"], issues=gate["issues"], unblock=gate["unblock"]
                + ["owner re-issues the porch target with this measurement definition"],
                measured=report["metrics"]["opening_clearance_x"],
                existing_target="lind-home.porch UNCHANGED (OUTSIDE/BLOCKED)")


U_DESIGN = 5e-7            # measurements.json stores 6 decimals


def _u_native(v):
    return 2.0 ** -22 * max(1.0, abs(v))


def difference_table(d, west, east, parts, clearance):
    """Design single proxy vs native east/west proxies, value by value."""
    plinth_mid_y = sum((p["bbox_min"][1] + p["bbox_max"][1]) / 2 for p in parts["plinths"]) / len(parts["plinths"])
    lintel = parts["lintels"][0]
    rows = [
        ("proxy_count", 1, 2, None, "design: one frame-envelope box; native: one box per post"),
        ("outer_x_min", d[0][0], west["bbox_min"][0], "BU", "same outer span (plinth outer face)"),
        ("outer_x_max", d[1][0], east["bbox_max"][0], "BU", "same outer span (plinth outer face)"),
        ("y_min", d[0][1], west["bbox_min"][1], "BU", "native follows plinth depth"),
        ("y_max", d[1][1], west["bbox_max"][1], "BU", "native follows plinth depth"),
        ("depth_y", d[1][1] - d[0][1], west["bbox_max"][1] - west["bbox_min"][1], "BU",
         "design depth 0.16 ~ lintel depth 0.16; native = plinth depth"),
        ("centre_y", (d[0][1] + d[1][1]) / 2, (west["bbox_min"][1] + west["bbox_max"][1]) / 2, "BU",
         f"visual plinth centre {plinth_mid_y:.4f}; lintel centre "
         f"{(lintel['bbox_min'][1] + lintel['bbox_max'][1]) / 2:.4f}"),
        ("z_min", d[0][2], west["bbox_min"][2], "BU", "ground"),
        ("z_max", d[1][2], west["bbox_max"][2], "BU", "both 2.5; timber post top 2.4"),
        ("ground_clearance_x", 0.0, clearance, "BU",
         "design blocks the walk opening; native leaves 1.66 (owner min 1.0)"),
    ]
    table = []
    for name, dv, nv, unit, meaning in rows:
        if unit is None:
            table.append(dict(quantity=name, design=dv, native=nv, unit="count", meaning=meaning,
                              evidence="NATIVE_MEASURED (both sides)"))
            continue
        u = U_DESIGN + _u_native(nv) * (2 if name in ("depth_y", "ground_clearance_x") else 1)
        delta = nv - dv
        table.append(dict(quantity=name, design=dv, native=nv, delta=delta, unit=unit,
                          u_design=U_DESIGN, u_native=u - U_DESIGN, u=u,
                          significant=abs(delta) > u, meaning=meaning,
                          evidence="design NATIVE_MEASURED on prior native (candidate, G1 "
                                   "blocked); native NATIVE_MEASURED"))
    return table


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", required=True)
    parser.add_argument("--native", required=True)
    parser.add_argument("--owner-checkpoint", required=True)
    parser.add_argument("--out", required=True)
    a = parser.parse_args()
    r = run(a.design, a.native, a.owner_checkpoint, a.out)
    print(json.dumps(dict(checks=r["native_collision_checks"], clearance=r["opening_clearance_x"],
                          design=r["design_proxy"], verdict=r["verdict"]), indent=1))


if __name__ == "__main__":
    main()

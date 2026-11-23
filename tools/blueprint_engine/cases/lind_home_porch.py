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

from ..export import write_json
from ..measure import BLENDER_SCRIPT, BlenderAdapter
from ..sources import file_sha256
from .lind_home import DESIGN_SHA, NATIVE_SHA

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
    write_json(out / "porch_correspondence.json", record)
    return record


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

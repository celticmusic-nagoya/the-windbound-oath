"""Validate MORWEN-LOCAL-RETOPO-03 evidence (plain Python, no Blender).

Checks provenance, technical result, relative acceptance against the original mesh, expression
status labelling (unreviewed transfers must be BLOCKED, never PASS), required renders/sheets,
that G2 is never PASS, and reproducibility of key metrics against expected_reference_run.json.
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("MORWEN_OUT", "render_output/morwen_local_retopo_03"))
VRM = "1995f174f6c8f2211f3c56c9e5fe4f9daf27ee5e648f129479582a259238149b"
STATUSES = {"UNAFFECTED", "TECH_PASS_RENDERED", "BLOCKED_TRANSFER_UNREVIEWED", "FAIL"}
TOL = 1e-4


def summary(r):
    return {
        "build": {k: r["build"][k] for k in ("region_faces", "deleted_vertices", "boundary_vertices", "new_vertices", "new_faces")},
        "checks": {k: v for k, v in r["technical_checks"].items()},
        "baseline_region_geometry": r["baseline_region_geometry"],
        "design_range": {d: {"geometry": v["geometry"], "tip": v["tip"], "proj": v["nose_projection_from_pupil_U"]}
                         for d, v in r["design_range"].items()},
        "expressions": {k: [v["status"], v.get("edge_ratio_p99"), v.get("inner_dihedral_deg_max")] for k, v in r["expressions"].items()},
        "calibrated": r["calibrated_layer0_deltas_U"],
    }


def close(a, b, path, errs):
    if isinstance(b, dict):
        for k in b:
            if k not in a:
                errs.append(f"missing {path}.{k}")
            else:
                close(a[k], b[k], f"{path}.{k}", errs)
    elif isinstance(b, list):
        if len(a) != len(b):
            errs.append(f"length {path}")
        for i, (x, y) in enumerate(zip(a, b)):
            close(x, y, f"{path}[{i}]", errs)
    elif isinstance(b, (bool, str)) or b is None:
        if a != b:
            errs.append(f"{path}: {a} != {b}")
    elif abs(float(a) - float(b)) > TOL:
        errs.append(f"{path}: {a} != {b}")


def main():
    errs = []
    r = json.loads((OUT / "NOSE_RETOPO_03_REPORT.json").read_text())
    if r["source_vrm_sha256"] != VRM or r["source_modified"] is not False:
        errs.append("source provenance")
    if r["technical_result"] != "PASS":
        errs.append("technical result is not PASS")
    if str(r["G2"]).startswith("PASS") or str(r["G4"]).startswith("PASS"):
        errs.append("G2/G4 must not be PASS from automated evidence")
    c = r["technical_checks"]
    for k in ("untouched_faces_identical", "body_mesh_unchanged", "shape_keys_original_preserved", "design_key_added"):
        if c[k] is not True:
            errs.append(f"check {k}")
    for k in ("winding_conflicts", "uv_flipped_faces", "uv_out_of_range_loops"):
        if c[k] != 0:
            errs.append(f"check {k} = {c[k]}")
    g0 = r["design_range"]["0.0"]["geometry"]
    b0 = r["baseline_region_geometry"]
    if g0["inner_dihedral_deg_max"] > b0["inner_dihedral_deg_max"] or g0["border_dihedral_deg_max"] > b0["border_dihedral_deg_max"]:
        errs.append("candidate geometry worse than original region")
    for d, v in r["design_range"].items():
        if v["geometry"].get("folded_vs_basis", 0) != 0 or v["geometry"]["non_manifold_edges"] != 0:
            errs.append(f"design value {d}: folds/non-manifold")
    blocked = []
    for k, v in r["expressions"].items():
        if v["status"] not in STATUSES:
            errs.append(f"expression {k}: bad status")
        if v["status"] == "FAIL":
            errs.append(f"expression {k}: FAIL")
        if v["status"] == "BLOCKED_TRANSFER_UNREVIEWED":
            blocked.append(k)
    if sorted(blocked) != sorted(r["expression_keys_blocked"]):
        errs.append("blocked expression list mismatch")
    for f in r["renders"]:
        if not (OUT / f).is_file():
            errs.append(f"missing render {f}")
    for name in ("SHEET_NOSE_CLAY_DESIGN_RANGE.png", "SHEET_NOSE_WIRE.png", "SHEET_NOSE_EXPRESSIONS.png",
                 "SHEET_NOSE_VS_3D_TARGET_UNCALIBRATED.png"):
        if not (OUT / name).is_file():
            errs.append(f"missing sheet {name}")
    for d in ("0.0", "0.5", "1.0"):
        for v in ("front", "right", "back", "left"):
            if not (OUT / f"LANDMARK_COMPARE_NOSE_D{d}_{v}.png").is_file():
                errs.append(f"missing calibrated comparison {d} {v}")
    s = summary(r)
    (OUT / "NOSE_EVIDENCE_SUMMARY.json").write_text(json.dumps(s, indent=2) + "\n")
    ref = HERE / "expected_reference_run.json"
    if ref.is_file():
        close(s, json.loads(ref.read_text()), "summary", errs)
    else:
        errs.append("expected_reference_run.json missing (reproducibility not checked)")
    if errs:
        print("FAIL\n" + "\n".join(errs[:60]))
        sys.exit(1)
    print("PASS: nose retopo evidence, relative acceptance, BLOCKED labelling, reproducibility")


if __name__ == "__main__":
    main()

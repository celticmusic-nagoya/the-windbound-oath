"""Validate MORWEN-EYELID-RETOPO-05 evidence (plain Python, no Blender)."""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("MORWEN_OUT", "render_output/morwen_eyelid_retopo_05"))
VRM = "1995f174f6c8f2211f3c56c9e5fe4f9daf27ee5e648f129479582a259238149b"
L0_FRONT = "b0a5d9f6c77c4a73a9f8bcca3dd2d8acad62403f374e04ebb2b0cb9b1b1199ed"
TOL = 1e-4
SHEETS = ("SHEET_VIEWS_316_VS_05.png", "SHEET_EYELID_STATES_TOON.png", "SHEET_EYE_CLOSEUPS.png",
          "SHEET_LAYER0_FIT.png", "SHEET_GAME_SIZE_64_32.png")


def summary(r, t):
    pen = lambda ix: {s: {k: [v["penetrating_samples"], v["max_depth_mm"]] for k, v in d["line_penetration"].items()}  # noqa: E731
                      for s, d in ix.items()}
    return {"targets": {"decision": t["symmetry_decision"], "mirror_px": t["mirror_comparison_px"],
                        "targets_3d": t["targets_3d"]},
            "build": {k: v for k, v in r["build"].items() if k != "cards"},
            "card_lift_mm": r["build"]["cards"]["max_lift_mm_by_state"],
            "opening": r["opening"], "corners": r["canthus_corner_metrics"],
            "candidate_pen": pen(r["candidate_intersections"]), "baseline316_pen": pen(r["baseline316_intersections"]),
            "candidate_eye_visible": {s: d["eye_visible_samples"] for s, d in r["candidate_intersections"].items()},
            "socket": r["socket_show_through"], "protrusion": {k: {s: {kk: v[kk] for kk in ("uncovered_outside_rim", "uncovered_max_dist_outside_rim_mm")}
                                                                    for s, v in d.items()} for k, d in r["eye_surface_protrusion"].items()},
            "patch_relative": {n: {s: v["candidate"] for s, v in rows.items()} for n, rows in r["patch_relative"].items()},
            "technical": r["technical_checks"]}


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
    r = json.loads((OUT / "EYELID_05_REPORT.json").read_text())
    t = json.loads((OUT / "EYE_TARGETS_05.json").read_text())
    if r["source_vrm_sha256"] != VRM or r["source_modified"] is not False:
        errs.append("source provenance")
    if r["layer0_front_sha256"] != L0_FRONT or t["source"]["sha256"] != L0_FRONT:
        errs.append("Layer 0 front reference SHA")
    if r["method_family"] == "LOCAL_RETOPO_ANNULUS_RING_PATCH":
        errs.append("stopped method family reused")
    # the delivered state is evidence of a STOPPED method: technical FAIL is expected and must be
    # reported as such (never PASS-washed); G3 must follow the technical result
    if r["technical_result"] not in ("PASS", "FAIL"):
        errs.append("technical result missing")
    if (r["technical_result"] == "PASS") != (r["G3"] == "PASS"):
        errs.append("G3 inconsistent with the technical result")
    if str(r["G2"]).startswith("PASS") or str(r["G4"]).startswith("PASS"):
        errs.append("G2/G4 must not be PASS")
    tc = r["technical_checks"]
    for k in ("nose_locked_geometry_unchanged", "body_mesh_unchanged", "mouth_unchanged_vs_316", "eye_material_unchanged_vs_316",
              "shape_keys_preserved", "canthus_ok"):
        if tc.get(k) is not True:
            errs.append(f"protection check {k} = {tc.get(k)}")
    if r["build"]["nose"]["design_value"] != 0.5 or not r["build"]["nose"]["hash_verified"]:
        errs.append("nose lock")
    if r["build"]["mouth"].get("built", True):
        errs.append("mouth is out of scope")
    for d, v in t["symmetry_decision"].items():
        if v not in ("SYMMETRIC_WITHIN_UNCERTAINTY", "MEASURED_ASYMMETRY_UNCONFIRMED"):
            errs.append(f"symmetry decision {d}")
    for f in r["renders"]:
        if not (OUT / f).is_file():
            errs.append(f"missing render {f}")
    for n in SHEETS:
        if not (OUT / n).is_file():
            errs.append(f"missing {n}")
    s = summary(r, t)
    (OUT / "EYELID_05_EVIDENCE_SUMMARY.json").write_text(json.dumps(s, indent=2) + "\n")
    ref = HERE / "expected_reference_run.json"
    if ref.is_file():
        close(s, json.loads(ref.read_text()), "summary", errs)
    else:
        errs.append("expected_reference_run.json missing")
    if errs:
        print("FAIL\n" + "\n".join(errs[:60]))
        sys.exit(1)
    print("PASS: EYELID-05 evidence, protections, reproducible")


if __name__ == "__main__":
    main()

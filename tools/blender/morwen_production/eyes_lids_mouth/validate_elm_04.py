"""Validate MORWEN-EYES-LIDS-MOUTH-04 evidence (plain Python, no Blender)."""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("MORWEN_OUT", "render_output/morwen_eyes_lids_mouth_04"))
VRM = "1995f174f6c8f2211f3c56c9e5fe4f9daf27ee5e648f129479582a259238149b"
TOL = 1e-4


def summary(r):
    pen = lambda ix: {s: {k: [v["penetrating_ratio"], v["max_depth_mm"]] for k, v in d["line_penetration"].items()}  # noqa: E731
                      for s, d in ix.items()}
    return {"build": {k: v for k, v in r["build"].items() if k != "cards"},
            "card_lift_mm": r["build"]["cards"]["max_lift_mm_by_state"],
            "baseline_pen": pen(r["baseline_intersections"]), "candidate_pen": pen(r["candidate_intersections"]),
            "candidate_eye_visible": {s: d["eye_visible_samples"] for s, d in r["candidate_intersections"].items()},
            "patch_relative": {rn: {s: v["candidate"] for s, v in rows.items()} for rn, rows in r["patch_relative"].items()},
            "eye": {k: v for k, v in r["eye_opening_vs_canonical"].items() if k != "note"}, "technical": r["technical_checks"],
            "priority": [[p["key"], p["max_mm"], p["status"]] for p in r["unreviewed_keys_priority"]],
            "annulus_trial": r["annulus_trial"],
            "socket": {k: r["socket_show_through"][k] for k in ("baseline", "candidate")},
            "protrusion": {s_: {k: v[k] for k in ("uncovered_outside_rim", "uncovered_max_dist_outside_rim_mm")}
                           for s_, v in r["eye_surface_protrusion"]["by_state"].items()}}


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
    r = json.loads((OUT / "ELM_04_REPORT.json").read_text())
    if r["source_vrm_sha256"] != VRM or r["source_modified"] is not False:
        errs.append("source provenance")
    if r["technical_result"] != "PASS":
        errs.append(f"technical result {r['technical_result']}: {r['technical_checks']}")
    if str(r["G2"]).startswith("PASS") or str(r["G4"]).startswith("PASS"):
        errs.append("G2/G4 must not be PASS")
    if r["retopo_status"]["status"] != "STOPPED_AFTER_2_FAILURES" or not isinstance(r["annulus_trial"], dict):
        errs.append("stopped annulus method must be recorded with trial evidence")
    elif any(v["verdict"] != "FAIL" for v in r["annulus_trial"]["configs"].values()):
        errs.append("trial verdict changed: re-evaluate the stopped method before reusing evidence")
    for n in ("lid_R", "lid_L", "mouth"):
        if r["build"][n].get("built", True):
            errs.append(f"{n}: the stopped method must not be in the candidate")
    if not r["technical_checks"]["socket_show_through_zero"] or r["technical_checks"]["eye_surface_protrusion_neutral"] != 0:
        errs.append("eye socket: head interior visible or eye surface outside the head")
    if not r["technical_checks"]["nose_locked_geometry_unchanged"]:
        errs.append("locked nose changed")
    if not r["build"]["nose"]["hash_verified"] or r["build"]["nose"]["design_value"] != 0.5:
        errs.append("nose lock")
    for p in r["unreviewed_keys_priority"]:
        if p["key"] in ("target_4", "target_40"):
            continue
        if p["status"] != "BLOCKED_UNREVIEWED":
            errs.append(f"{p['key']} must stay BLOCKED")
    for f in r["renders"]:
        if not (OUT / f).is_file():
            errs.append(f"missing render {f}")
    for n in ("SHEET_BASELINE_VS_CANDIDATE_TOON.png", "SHEET_EYES_LIDS_CLAY.png", "SHEET_EXPRESSIONS_TOON.png",
              "SHEET_MOUTH_CLAY.png", "SHEET_NEUTRAL_VIEWS.png", "SHEET_GAME_SIZE_PREVIEW.png", "SHEET_EYE_SOCKET_45.png"):
        if not (OUT / n).is_file():
            errs.append(f"missing {n}")
    s = summary(r)
    (OUT / "ELM_EVIDENCE_SUMMARY.json").write_text(json.dumps(s, indent=2) + "\n")
    ref = HERE / "expected_reference_run.json"
    if ref.is_file():
        close(s, json.loads(ref.read_text()), "summary", errs)
    else:
        errs.append("expected_reference_run.json missing")
    if errs:
        print("FAIL\n" + "\n".join(errs[:50]))
        sys.exit(1)
    print("PASS: ELM-04 evidence, locked nose, BLOCKED keys preserved, reproducible")


if __name__ == "__main__":
    main()

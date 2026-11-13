"""Validate MORWEN-LOCAL-RETOPO-03-REVIEW evidence (plain Python, no Blender)."""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("MORWEN_OUT", "render_output/morwen_local_retopo_03_review"))
TOL = 1e-4


def summary(r):
    return {"candidate_hash": r["candidate"]["face_geometry_hash_rebuilt"],
            "technical_qa": r["technical_qa"],
            "expressions": {p: {"shape_key": e["shape_key"], "motion": e["region_max_motion_mm"],
                                "consistent": e["mapping_consistent"], "nose_patch": e["nose_patch"]}
                            for p, e in r["expressions"].items()},
            "pairwise": r["pairwise_max_difference_mm"],
            "still_blocked": r["still_blocked_unreviewed_keys"]}


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
    r = json.loads((OUT / "REVIEW_03R_REPORT.json").read_text())
    P = json.loads((HERE / "review_params_03r.json").read_text())
    if r["source_modified"] is not False or r["nose_regenerated"] is not False:
        errs.append("source/nose must be untouched")
    if r["candidate"]["face_geometry_hash_rebuilt"] != P["candidate"]["face_geometry_hash"]:
        errs.append("reviewed mesh is not the #312 candidate")
    t = r["technical_qa"]
    if not (t["candidate_identical"] and t["mapping_consistent_all"] and t["nose_patch_no_folds_all"]):
        errs.append(f"technical QA: {t}")
    if t["identical_expression_pairs"]:
        errs.append("identical expression keys found")
    if any(str(r[g]).startswith("PASS") for g in ("G2", "G4")):
        errs.append("G2/G4 must not be PASS")
    blocked0 = set(json.loads((HERE / "blocked_before_review.json").read_text()))
    reviewed = {e["shape_key"] for e in r["expressions"].values()}
    if set(r["still_blocked_unreviewed_keys"]) != blocked0 - reviewed:
        errs.append("still-blocked list must equal previous BLOCKED minus reviewed priority keys")
    for f in r["renders"]:
        if not (OUT / f).is_file():
            errs.append(f"missing render {f}")
    for n in ("SHEET_DEPTH_0_VS_05.png", "SHEET_TOON_FRONT_45.png", "SHEET_PRIORITY_EXPRESSIONS.png"):
        if not (OUT / n).is_file():
            errs.append(f"missing {n}")
    s = summary(r)
    (OUT / "REVIEW_EVIDENCE_SUMMARY.json").write_text(json.dumps(s, indent=2) + "\n")
    ref = HERE / "expected_reference_run.json"
    if ref.is_file():
        close(s, json.loads(ref.read_text()), "summary", errs)
    else:
        errs.append("expected_reference_run.json missing")
    if errs:
        print("FAIL\n" + "\n".join(errs[:50]))
        sys.exit(1)
    print("PASS: existing candidate reviewed, mapping consistent, BLOCKED keys preserved, reproducible")


if __name__ == "__main__":
    main()

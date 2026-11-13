"""Validate MORWEN-HEAD-LANDMARK-02 evidence (plain Python; no Blender needed).

Checks provenance, status labelling, calibration consistency, technical fit checks, that no
report ever claims G2 PASS, and reproducibility against the committed reference numbers in
expected_reference_run.json (tolerance 1e-4 in U units / metres). Writes EVIDENCE_SUMMARY.json.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("MORWEN_OUT", "render_output/morwen_head_landmark_02"))
MANIFEST = Path(os.environ.get("MORWEN_LAYER0_MANIFEST",
                               "tools/blender/production_mesh_08/layer0_reference_manifest.json"))
VRM = "1995f174f6c8f2211f3c56c9e5fe4f9daf27ee5e648f129479582a259238149b"
STATUS_3D = {"MEASURED", "MEASURED_IN_DEFINED_ROI", "ESTIMATED"}
STATUS_2D = {"MEASURED", "ESTIMATED", "NOT_MEASURABLE"}
TOL = 1e-4


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def summary(l3, l2, cmp, fit):
    pick = lambda rows: {f'{r["view"]}:{r["landmark"]}': r["delta_U"] for r in rows if "delta_U" in r}  # noqa: E731
    return {
        "U_m": l3["normalisation"]["unit_U_m"],
        "s_px_per_m": cmp["calibration"]["s_px_per_m"],
        "U_px": l2["scale_consistency"]["U_px_by_view"],
        "landmarks_3d": {k: v["position"] for k, v in l3["landmarks"].items()},
        "baseline_delta_U": pick(cmp["landmark_deltas"]),
        "proportions": {k: v["model_U"] for k, v in cmp["proportions"].items()},
        "fit_technical": fit["technical_checks"],
        "fit_residual_U": {f'{r["view"]}:{r["landmark"]}': r["candidate_delta_U"] for r in fit["landmark_residuals"]},
    }


def close(a, b, path, errs):
    if isinstance(a, dict):
        for k in b:
            if k not in a:
                errs.append(f"missing {path}.{k}")
            else:
                close(a[k], b[k], f"{path}.{k}", errs)
    elif isinstance(a, list):
        if len(a) != len(b):
            errs.append(f"length {path}")
        for i, (x, y) in enumerate(zip(a, b)):
            close(x, y, f"{path}[{i}]", errs)
    elif isinstance(a, bool) or a is None or isinstance(a, str):
        if a != b:
            errs.append(f"{path}: {a} != {b}")
    elif abs(float(a) - float(b)) > TOL:
        errs.append(f"{path}: {a} != {b}")


def main():
    errs = []
    l3 = json.loads((OUT / "HEAD_LANDMARKS_3D.json").read_text())
    l2 = json.loads((OUT / "CANONICAL_LANDMARKS_2D.json").read_text())
    cmp = json.loads((OUT / "LANDMARK_COMPARISON.json").read_text())
    fit = json.loads((OUT / "FIT_CANDIDATE_REPORT.json").read_text())
    for name, doc in (("3D", l3), ("cmp", cmp), ("fit", fit)):
        if doc.get("source_vrm_sha256") != VRM or doc.get("source_modified") is not False:
            errs.append(f"{name}: source provenance")
    man = {i["view"]: i["sha256"] for i in json.loads(MANIFEST.read_text())["images"]}
    for v, d in l2["views"].items():
        if d["source"]["sha256"] != man[v]:
            errs.append(f"2D {v}: Layer 0 SHA")
        for k, p in d["landmarks"].items():
            if p["status"] not in STATUS_2D:
                errs.append(f"2D {v}.{k}: status {p['status']}")
            if (p["status"] == "NOT_MEASURABLE") != (p["px"] is None):
                errs.append(f"2D {v}.{k}: NOT_MEASURABLE must have null px")
    for k, p in l3["landmarks"].items():
        if p["status"] not in STATUS_3D or not p.get("method"):
            errs.append(f"3D {k}: status/method")
    if max(l3["mirror_deviation_abs_x_m"].values()) > 1e-3:
        errs.append("3D base is expected mirror-symmetric (deviation > 1 mm)")
    if l2["scale_consistency"]["max_relative_spread"] > 0.03:
        errs.append("Layer 0 views disagree on U by > 3 %: single-sheet scale invalid")
    for v in ("front", "right", "back", "left"):
        for tag in ("", "_CANDIDATE"):
            if not (OUT / f"LANDMARK_COMPARE{tag}_{v}.png").is_file():
                errs.append(f"missing comparison PNG {tag} {v}")
    for name, p in cmp["outputs"].items():
        if sha(OUT / name) != p:
            errs.append(f"output hash {name}")
    for r in cmp["landmark_deltas"]:
        if "delta_U" in r and r["status"] not in ("MEASURED", "ESTIMATED", "ANCHOR", "ANCHOR_PAIR"):
            errs.append(f"delta status {r}")
    if fit["technical_result"] != "PASS":
        errs.append(f"fit technical checks failed: {fit['technical_checks']}")
    if fit.get("candidate_saved_to_disk") is not False:
        errs.append("candidate must not be saved")
    for name, doc in (("fit", fit),):
        if str(doc.get("G2", "")).startswith("PASS"):
            errs.append(f"{name}: G2 must never be PASS from automated evidence")
    s = summary(l3, l2, cmp, fit)
    (OUT / "EVIDENCE_SUMMARY.json").write_text(json.dumps(s, indent=2) + "\n")
    ref = HERE / "expected_reference_run.json"
    if ref.is_file():
        close(s, json.loads(ref.read_text()), "summary", errs)
    else:
        errs.append("expected_reference_run.json missing (reproducibility not checked)")
    if errs:
        print("FAIL\n" + "\n".join(errs[:60]))
        sys.exit(1)
    print("PASS: landmark evidence, provenance, status labels, technical fit, reproducibility")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Non-destructive cross-view 2D landmark audit; never infer 3D measurements."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/qa/morwen-rebuild-01/layer0-landmark-review/layer0-landmarks.json"
VIEWS = ("front", "right", "back", "left")
PAIRS = (("front", "back"), ("right", "left"))
FEATURES = ("hair", "chin", "crotch", "knee_R", "knee_L", "ankle_R", "ankle_L", "sole_R", "sole_L")
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    a = parser.parse_args()
    if a.output.resolve() == SOURCE.resolve():
        raise ValueError("Refusing to overwrite canonical annotation")
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert data["canvas_px"] == [384, 1024]
    views = {name: {p["feature_id"]: p for p in data["views"][name]["points"]} for name in VIEWS}
    observations = []
    for left, right in PAIRS:
        for feature in FEATURES:
            # Opposite profile views expose opposite anatomical sides. Match homologous\n            # features, not the same side suffix (R vs L) across profiles.\n            counterpart = feature\n            if (left, right) == ("right", "left") and feature.endswith(("_R", "_L")):\n                counterpart = feature[:-2] + ("_L" if feature.endswith("_R") else "_R")\n            p, q = views[left].get(feature), views[right].get(counterpart)
            if p is None or q is None:
                observations.append({"pair": [left, right], "feature": feature, "counterpart": counterpart, "status": "MISSING", "missing": [v for v, obj in ((left,p),(right,q)) if obj is None]})
                continue
            if p.get("v_px") is None or q.get("v_px") is None or p.get("bounds_px") is None or q.get("bounds_px") is None:
                observations.append({"pair": [left, right], "feature": feature, "counterpart": counterpart, "status": "UNMEASURABLE", "statuses": [p["status"], q["status"]]})
                continue
            delta = q["v_px"] - p["v_px"]
            intervals_overlap = max(p["bounds_px"][1], q["bounds_px"][1]) <= min(p["bounds_px"][3], q["bounds_px"][3])
            observations.append({"pair": [left,right], "feature": feature, "counterpart": counterpart, "status": "COMPARABLE_2D_ONLY" if p["status"] == q["status"] == "observed" else "INFERRED_OR_MIXED", "v_px": [p["v_px"],q["v_px"]], "delta_v_px": delta, "vertical_intervals_overlap": intervals_overlap, "statuses": [p["status"],q["status"]]})
    out = {"schema":"morwen-crossview-audit-v1", "source":str(SOURCE.relative_to(ROOT)), "projection_calibrated":False, "independent_annotation":"BLOCKED", "physical_dimensions":"NOT_ESTABLISHED", "note":"Pixel-row differences across distinct images are screening signals only; unknown projection, pose and framing prevent anatomical conclusions.", "observations":observations}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("CROSSVIEW_AUDIT_PASS",len(observations),"observations",a.output)
if __name__ == "__main__":
    main()

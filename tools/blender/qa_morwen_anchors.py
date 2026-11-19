"""MORWEN-RIG-06: read-only QA for measured normalized anchors."""
import argparse
import json
from pathlib import Path

def validate(doc, require_measured=False):
    errors = []
    expected = {"front", "left", "right", "back"}
    if set(doc.get("facings", {})) != expected:
        errors.append("Four distinct facings are required")
    if doc.get("asymmetry_policy", {}).get("mirror_between_facings") is not False:
        errors.append("Mirroring asymmetrical art is forbidden")
    if doc.get("production_use") is not False:
        errors.append("Candidate anchors must not be marked production")
    required = set(doc.get("required_anchors", []))
    for facing, data in doc.get("facings", {}).items():
        anchors = data.get("anchors", {})
        if require_measured and set(anchors) != required:
            errors.append(f"{facing}: missing/extra measured anchors")
        for name, xy in anchors.items():
            if name not in required or not isinstance(xy, dict):
                errors.append(f"{facing}/{name}: unexpected anchor")
                continue
            if not all(isinstance(xy.get(axis), (float, int)) and not isinstance(xy.get(axis), bool)
                       and 0 <= xy[axis] <= 1 for axis in ("x", "y")):
                errors.append(f"{facing}/{name}: coordinates must be in [0,1]")
    return errors

def main():
    p = argparse.ArgumentParser()
    p.add_argument("file", type=Path)
    p.add_argument("--require-measured", action="store_true")
    args = p.parse_args()
    data = json.loads(args.file.read_text(encoding="utf-8"))
    errors = validate(data, args.require_measured)
    if errors:
        print("FAIL: " + "; ".join(errors))
        raise SystemExit(1)
    if any(not f["anchors"] for f in data["facings"].values()):
        print("SCHEMA_PASS_MEASUREMENT_PENDING")
    else:
        print("ANCHOR_DATA_PASS_NOT_VISUAL_APPROVAL")

if __name__ == "__main__":
    main()

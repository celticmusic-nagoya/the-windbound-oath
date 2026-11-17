#!/usr/bin/env python3
"""Read-only validation of MORWEN Layer 0 annotation metadata.
No Blender, image regeneration, source modification, or external dependencies.
Usage: python tools/morwen_rebuild01/validate_layer0_landmarks.py
       python tools/morwen_rebuild01/validate_layer0_landmarks.py --output /tmp/morwen-landmarks-qa.json
"""
import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / "docs/qa/morwen-rebuild-01/layer0-landmark-review/layer0-landmarks.json"
EXPECTED = {"front": "7809.png", "right": "7807.png", "back": "7810.png", "left": "7808.png"}
SHA = {
    "front": "b0a5d9f6c77c4a73a9f8bcca3dd2d8acad62403f374e04ebb2b0cb9b1b1199ed",
    "right": "9f4873cf331f55b72510159412bd0bfc4c606499f792626e03cffcdace7bf737",
    "back": "b9d6d6667be8d9bbed1538a42cbaea0e51bab68371366962e43463fbe394976f",
    "left": "69f23ce23cf9c56228e1e4d9a23fbab6b6607456a35239c853718a84da2298fa",
}
VALID_STATUS = {"observed", "inferred", "unmeasurable"}

def validate(doc):
    failures, warnings = [], []
    if doc.get("schema") != "morwen-layer0-landmarks-v1":
        failures.append("Unexpected annotation schema")
    if doc.get("canvas_px") != [384, 1024]:
        failures.append("Canvas dimensions mismatch")
    views = doc.get("views", {})
    if set(views) != set(EXPECTED):
        failures.append("Missing or unexpected views")
    counts = Counter()
    for view, expected_file in EXPECTED.items():
        record = views.get(view, {})
        if record.get("source") != expected_file or record.get("source_sha256") != SHA[view]:
            failures.append(f"{view}: reference identity mismatch")
        markers = set()
        for p in record.get("points", []):
            status = p.get("status")
            counts[status] += 1
            marker = p.get("marker")
            if marker in markers:
                failures.append(f"{view}: duplicate marker {marker}")
            markers.add(marker)
            if status not in VALID_STATUS:
                failures.append(f"{view}/{marker}: unknown status {status}")
            u, v = p.get("u_px"), p.get("v_px")
            bounds = p.get("bounds_px")
            if status == "unmeasurable":
                if u is not None or v is not None:
                    failures.append(f"{view}/{marker}: unmeasurable must not invent coordinates")
                continue
            if not all(isinstance(q, (int, float)) for q in (u, v)):
                failures.append(f"{view}/{marker}: missing coordinates")
                continue
            if not (0 <= u < 384 and 0 <= v < 1024):
                failures.append(f"{view}/{marker}: outside canvas")
            if not (isinstance(bounds, list) and len(bounds) == 4 and
                    all(isinstance(q, (int, float)) for q in bounds)):
                failures.append(f"{view}/{marker}: invalid uncertainty bounds")
            elif not (0 <= bounds[0] <= u <= bounds[2] < 384 and
                      0 <= bounds[1] <= v <= bounds[3] < 1024):
                failures.append(f"{view}/{marker}: point outside bounds or bounds outside canvas")
    if sum(counts.values()) != 69:
        failures.append(f"Expected 69 annotations, got {sum(counts.values())}")
    if doc.get("independent_annotation", {}).get("status") != "PASS":
        warnings.append("Independent second human annotation not available: G1 review remains BLOCKED")
    if doc.get("projection") == "unknown":
        warnings.append("Projection not calibrated: do not infer physical dimensions")
    return {"result": "FAIL" if failures else "LIMITED_PASS",
            "scope": "metadata consistency only; NOT independent art QA or calibrated geometry",
            "counts": dict(counts), "failures": failures, "warnings": warnings}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(json.loads(args.input.read_text(encoding="utf-8")))
    serialized = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 1 if result["result"] == "FAIL" else 0

if __name__ == "__main__":
    raise SystemExit(main())

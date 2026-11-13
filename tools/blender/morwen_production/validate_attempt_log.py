"""Validate non-destructive quality-first production attempt records."""
import argparse
import json
from pathlib import Path

GATES = {"PASS", "FAIL", "BLOCKED", "NOT_RUN"}
REQUIRED = {"asset_id", "canonical_references", "method", "defect_id",
            "attempt_number", "hypothesis", "observed_delta",
            "failure_category", "next_method", "gates"}
CATEGORIES = {"geometry", "reference", "material", "structure",
              "rendering", "tool_limit", "none"}

def validate(data):
    errors = []
    if data.get("schema") != "TWO-3D-ATTEMPT-LOG-01":
        errors.append("invalid schema")
    entries = data.get("attempts")
    if not isinstance(entries, list):
        return ["attempts must be an array"]
    counts = {}
    for i, entry in enumerate(entries):
        missing = REQUIRED - set(entry)
        if missing:
            errors.append(f"attempt {i}: missing {sorted(missing)}")
            continue
        if not isinstance(entry["canonical_references"], list) or not entry["canonical_references"]:
            errors.append(f"attempt {i}: canonical references required")
        if entry["failure_category"] not in CATEGORIES:
            errors.append(f"attempt {i}: invalid failure category")
        if set(entry["gates"]) != {"G1", "G2", "G3", "G4"} or any(v not in GATES for v in entry["gates"].values()):
            errors.append(f"attempt {i}: invalid G1-G4 gate status")
        key = (entry["asset_id"], entry["defect_id"], entry["method"])
        counts[key] = counts.get(key, 0) + (entry["gates"]["G2"] == "FAIL")
        if counts[key] > 2:
            errors.append(f"attempt {i}: anti-loop STOP: >2 G2 failures with same method for {key}")
        if not isinstance(entry["attempt_number"], int) or entry["attempt_number"] < 1:
            errors.append(f"attempt {i}: invalid attempt_number")
    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    errors = validate(json.loads(args.path.read_text(encoding="utf-8")))
    for error in errors:
        print("FAIL:", error)
    if errors:
        raise SystemExit(1)
    print("PASS: 3D attempt log anti-loop validation")

if __name__ == "__main__":
    main()

"""Validate cross-team TWO 3D attempt ledgers without changing approved assets.

Schema TWO-3D-SHARED-LEDGER-01. Counts persist across chats/branches by
stable asset_id, defect_id and method_family, not filename or branch name.
"""
import argparse
import json
from pathlib import Path

GATES = {"PASS", "FAIL", "BLOCKED", "NOT_RUN"}
CATEGORIES = {"shape", "reference", "material", "structure", "render", "tool"}
REQUIRED = {
    "task_id", "asset_id", "defect_id", "method_id", "method_family",
    "source_sha256", "input_sha256", "output_sha256", "canonical_references",
    "visual_defects", "root_cause", "next_action", "stop_reason",
    "gates", "outcome",
}
OUTCOMES = {"PASS", "FAIL", "BLOCKED", "NOT_RUN"}


def validate(data):
    errors = []
    if data.get("schema") != "TWO-3D-SHARED-LEDGER-01":
        errors.append("schema must be TWO-3D-SHARED-LEDGER-01")
    entries = data.get("attempts")
    if not isinstance(entries, list):
        return ["attempts must be a list"]
    counts = {}
    for i, item in enumerate(entries):
        if not isinstance(item, dict):
            errors.append(f"attempt {i}: must be object")
            continue
        missing = REQUIRED - set(item)
        if missing:
            errors.append(f"attempt {i}: missing {sorted(missing)}")
            continue
        for field in ("task_id", "asset_id", "defect_id", "method_id",
                      "method_family", "source_sha256", "next_action"):
            if not isinstance(item[field], str) or not item[field].strip():
                errors.append(f"attempt {i}: {field} must be nonempty")
        for field in ("input_sha256", "output_sha256", "canonical_references",
                      "visual_defects"):
            if not isinstance(item[field], list):
                errors.append(f"attempt {i}: {field} must be a list")
        if not item["canonical_references"]:
            errors.append(f"attempt {i}: canonical_references required")
        if item["root_cause"] not in CATEGORIES:
            errors.append(f"attempt {i}: invalid root_cause")
        if item["outcome"] not in OUTCOMES:
            errors.append(f"attempt {i}: invalid outcome")
        if not isinstance(item["stop_reason"], str):
            errors.append(f"attempt {i}: stop_reason must be string")
        gates = item["gates"]
        if not isinstance(gates, dict) or set(gates) != {"G1", "G2", "G3", "G4"} or any(v not in GATES for v in gates.values()):
            errors.append(f"attempt {i}: invalid gates")
            continue
        key = (item["asset_id"], item["defect_id"], item["method_family"])
        if item["outcome"] == "FAIL":
            counts[key] = counts.get(key, 0) + 1
            if counts[key] > 2:
                errors.append(f"attempt {i}: STOP: method family already failed twice: {key}")
            if counts[key] == 2 and not item["stop_reason"].strip():
                errors.append(f"attempt {i}: second failure must state stop_reason")
        if counts.get(key, 0) >= 2 and item["outcome"] == "NOT_RUN" and not item["stop_reason"].strip():
            errors.append(f"attempt {i}: stopped method requires stop_reason")
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
    print("PASS: shared attempt ledger")


if __name__ == "__main__":
    main()

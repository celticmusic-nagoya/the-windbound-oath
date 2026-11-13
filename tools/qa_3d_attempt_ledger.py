#!/usr/bin/env python3
"""Validate 3D attempt records and prevent repeating a twice-failed method."""
import argparse
import json
from pathlib import Path

GATES = {"PASS", "FAIL", "BLOCKED", "NOT_RUN"}
CATEGORIES = {"shape", "reference", "material", "structure", "render", "tool", "other"}

def validate(doc):
    errors = []
    if doc.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not isinstance(doc.get("asset_id"), str) or not doc["asset_id"].strip():
        errors.append("asset_id required")
    attempts = doc.get("attempts")
    if not isinstance(attempts, list):
        return errors + ["attempts must be an array"]
    seen = set()
    failures = {}
    for i, a in enumerate(attempts):
        tag = f"attempts[{i}]"
        if not isinstance(a, dict):
            errors.append(f"{tag} must be an object")
            continue
        for k in ("attempt_id", "defect_id", "method_id", "input_sha256", "hypothesis", "evidence", "result"):
            if not isinstance(a.get(k), str) or not a[k].strip():
                errors.append(f"{tag}.{k} required")
        aid = a.get("attempt_id")
        if aid in seen:
            errors.append(f"{tag}: duplicate attempt_id")
        seen.add(aid)
        gates = a.get("gates")
        if not isinstance(gates, dict) or set(gates) != {"G1", "G2", "G3", "G4"} or any(v not in GATES for v in gates.values()):
            errors.append(f"{tag}: gates must include G1-G4 with valid status")
        result = a.get("result")
        if result not in ("PASS", "FAIL", "BLOCKED"):
            errors.append(f"{tag}: result must be PASS/FAIL/BLOCKED")
        if result == "FAIL":
            if a.get("failure_category") not in CATEGORIES:
                errors.append(f"{tag}: failure_category required")
            key = (a.get("defect_id"), a.get("method_id"))
            failures[key] = failures.get(key, 0) + 1
            if failures[key] > 2:
                errors.append(f"{tag}: method exceeded two failures for defect {key}")
        if result == "PASS" and any(v == "FAIL" for v in gates.values()) if isinstance(gates, dict) else False:
            errors.append(f"{tag}: PASS conflicts with failing gate")
    blocked = {(a.get("defect_id"), a.get("method_id")) for a in attempts if isinstance(a, dict) and a.get("result") == "FAIL"}
    for defect, method in blocked:
        if failures.get((defect, method), 0) >= 2:
            for a in attempts:
                if isinstance(a, dict) and a.get("defect_id") == defect and a.get("method_id") == method and a.get("result") == "PASS":
                    errors.append(f"defect {defect}: review pass after two failures of same method")
    return errors

def main():
    p = argparse.ArgumentParser()
    p.add_argument("ledger", type=Path)
    args = p.parse_args()
    try:
        doc = json.loads(args.ledger.read_text(encoding="utf-8"))
        errors = validate(doc)
    except (OSError, ValueError) as exc:
        errors = [str(exc)]
    for error in errors:
        print("FAIL:", error)
    if errors:
        raise SystemExit(1)
    print("PASS: ledger schema and two-failure guard")

if __name__ == "__main__":
    main()

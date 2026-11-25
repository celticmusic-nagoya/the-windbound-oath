#!/usr/bin/env python3
"""Fail-closed, standard-library-only validation of a candidate Blender -> browser handoff.

No renderer, scale, camera or canonical asset is approved by this validator.
"""
import argparse
import hashlib
import json
from pathlib import Path

ALLOWED_LANES = {"WORLD", "HOME", "BUILD", "ECO", "CHARACTER"}
REQUIRED = {"schema_version", "lane", "status", "source_commit", "source_sha256",
            "blender_version", "generator_version", "random_seed",
            "coordinate_contract", "outputs", "gates"}
HEX = set("0123456789abcdef")


def validate(manifest_path):
    p = Path(manifest_path).resolve()
    data = json.loads(p.read_text(encoding="utf-8"))
    errors = []
    if not isinstance(data, dict):
        return ["manifest must be an object"]
    errors += [f"missing {key}" for key in sorted(REQUIRED - data.keys())]
    if errors:
        return errors
    if data["schema_version"] != "two-3d-handoff-candidate-v1":
        errors.append("unsupported schema_version")
    if data["lane"] not in ALLOWED_LANES:
        errors.append("unknown lane")
    if data["status"] != "candidate":
        errors.append("handoff cannot assert canonical/adopted status")
    for field in ("source_sha256",):
        value = data[field]
        if not isinstance(value, str) or len(value) != 64 or any(c not in HEX for c in value):
            errors.append(f"invalid {field}")
    contract = data["coordinate_contract"]
    if not isinstance(contract, dict):
        errors.append("coordinate_contract must be an object")
    else:
        for field in ("world_scale_m", "world_origin", "camera_projection", "character_height_m"):
            if field not in contract:
                errors.append(f"missing coordinate_contract.{field}")
            elif contract[field] is not None:
                errors.append(f"unapproved coordinate_contract.{field}; candidate contract must be null")
    gates = data["gates"]
    if not isinstance(gates, dict) or set(gates) != {"G1", "G2", "G3", "G4"}:
        errors.append("gates must contain exactly G1-G4")
    else:
        for name, value in gates.items():
            if value not in {"BLOCKED", "NOT_RUN", "FAIL"}:
                errors.append(f"{name} cannot assert PASS in candidate handoff")
    outputs = data["outputs"]
    if not isinstance(outputs, list) or not outputs:
        errors.append("outputs must be a nonempty list")
    else:
        for item in outputs:
            if not isinstance(item, dict) or not {"path", "sha256", "kind"} <= item.keys():
                errors.append("invalid output record")
                continue
            relative = item["path"]
            if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
                errors.append("unsafe output path")
                continue
            target = (p.parent / relative).resolve()
            if not target.is_relative_to(p.parent) or not target.is_file():
                errors.append(f"missing/unsafe output: {relative}")
                continue
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            if digest != item["sha256"]:
                errors.append(f"output SHA mismatch: {relative}")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    args = parser.parse_args()
    errors = validate(args.manifest)
    print(json.dumps({"status": "FAIL" if errors else "PASS", "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

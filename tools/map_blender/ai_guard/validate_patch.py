"""Validate untrusted AI numeric proposals; do not execute model-supplied code."""
import argparse
import json
import math
import pathlib
import sys

LIMITS = {
    "light_energy_multiplier": (0.8, 1.2),
    "light_size_multiplier": (0.9, 1.1),
    "camera_ortho_multiplier": (0.95, 1.05),
    "exposure_delta": (-0.2, 0.2),
    "roughness_delta": (-0.05, 0.05),
}

def validate(obj):
    fields = {"schema", "asset_id", "method_family", "root_cause", "adjustments"}
    if not isinstance(obj, dict) or set(obj) != fields:
        raise ValueError("unknown or missing top-level fields")
    if obj["schema"] != "two-render-patch-v1":
        raise ValueError("unsupported schema")
    for key in ("asset_id", "method_family", "root_cause"):
        value = obj[key]
        if not isinstance(value, str) or not (1 <= len(value) <= 120) or not all(
            c.isalnum() or c in "-_." for c in value
        ):
            raise ValueError("invalid " + key)
    changes = obj["adjustments"]
    if not isinstance(changes, dict) or not (1 <= len(changes) <= 3):
        raise ValueError("adjustments must have 1..3 entries")
    normalized = {}
    for key, value in changes.items():
        if key not in LIMITS or type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError("forbidden or nonfinite adjustment: " + str(key))
        low, high = LIMITS[key]
        normalized[key] = round(max(low, min(high, float(value))), 4)
    return {
        **{key: obj[key] for key in ("schema", "asset_id", "method_family", "root_cause")},
        "adjustments": normalized,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("proposal")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = pathlib.Path(args.proposal)
    if source.stat().st_size > 8192:
        raise ValueError("oversized proposal")
    safe = validate(json.loads(source.read_text(encoding="utf-8")))
    output = pathlib.Path(args.output)
    if output.exists():
        raise FileExistsError("refusing overwrite")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(safe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("VALIDATED", output)

if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print("REJECTED:", exc, file=sys.stderr)
        sys.exit(2)

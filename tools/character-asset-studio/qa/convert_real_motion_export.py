#!/usr/bin/env python3
"""Convert validated authored world-space contacts into stance audit input.

No guessed anatomical mapping, coordinate transforms, or foot planting.
"""
import argparse
import json
from pathlib import Path
from validate_real_motion_export import validate


def convert(data):
    report = validate(data)
    if report["status"] != "PASS":
        return {"status": "BLOCKED", "issues": report["issues"], "adoptionReady": False}
    # Structural validation does not establish provenance truth. The exporter
    # must supply evidence for anatomical identity and world transforms.
    frames = []
    active = {"L": None, "R": None}
    for frame in data["frames"]:
        contacts = {}
        for side in ("L", "R"):
            foot = frame["feet"][side]
            phase = foot["phase"]
            if phase == "stance":
                sid = foot["stanceId"]
                if active[side] is not None and active[side] != sid:
                    return {"status": "BLOCKED", "issues": [f"STANCE_ID_SWITCH:{frame['id']}:{side}"],
                            "adoptionReady": False}
                active[side] = sid
                contacts[side] = {"phase": "stance", "worldPx": foot["worldPx"]}
            else:
                active[side] = None
                contacts[side] = {"phase": "swing"}
        frames.append({"id": frame["id"], "contacts": contacts})
    return {"schema": "cas/stance-frames/1.0", "frames": frames}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    if args.input.resolve() == args.output.resolve() or args.output.exists():
        p.error("refusing overwrite")
    result = convert(json.loads(args.input.read_text(encoding="utf-8")))
    if result.get("status") == "BLOCKED":
        print(json.dumps(result, indent=2))
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(str(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Independent, read-only per-frame stance-contact QA for Character Asset Studio.

Input JSON:
{"schema":"cas/stance-frames/1.0","frames":[
 {"id":"f0","contacts":{"L":{"phase":"stance","worldPx":[100,200]},
                       "R":{"phase":"swing"}}},
 {"id":"f1","contacts":{"L":{"phase":"stance","worldPx":[101,200]}}}
]}
Only frames explicitly marked stance are checked. No inferred gait data.
"""
import argparse
import json
import math
from pathlib import Path


def audit_stance(data, tolerance_px=2.0):
    if not math.isfinite(tolerance_px) or tolerance_px < 0:
        raise ValueError("tolerance must be finite and nonnegative")
    if data.get("schema") != "cas/stance-frames/1.0":
        raise ValueError("unexpected frame schema")
    frames = data.get("frames")
    if not isinstance(frames, list) or not frames:
        raise ValueError("frames must be nonempty")
    planted = {}
    displacements = {"L": [], "R": []}
    observations = []
    for i, frame in enumerate(frames):
        contacts = frame.get("contacts", {})
        if not isinstance(contacts, dict):
            raise ValueError(f"frame {i}: contacts must be object")
        for side in ("L", "R"):
            item = contacts.get(side, {"phase": "swing"})
            phase = item.get("phase")
            if phase not in ("stance", "swing"):
                raise ValueError(f"frame {i} {side}: invalid phase")
            if phase == "swing":
                planted.pop(side, None)
                continue
            pt = item.get("worldPx")
            if (not isinstance(pt, list) or len(pt) != 2 or
                    any(not isinstance(v, (int, float)) or isinstance(v, bool)
                        or not math.isfinite(v) for v in pt)):
                raise ValueError(f"frame {i} {side}: invalid worldPx")
            if side not in planted:
                planted[side] = pt[:]
            drift = math.dist(planted[side], pt)
            displacements[side].append(drift)
            observations.append({"frame": frame.get("id", i), "side": side,
                                 "driftPx": drift,
                                 "status": "PASS" if drift <= tolerance_px else "FAIL"})
    if not observations:
        return {"status": "NOT_RUN", "reason": "no stance samples", "adoptionReady": False}
    # Keep full precision for both evidence and the gate: display rounding can
    # otherwise turn a slightly over-tolerance FAIL into an overall PASS.
    maximum = max(v["driftPx"] for v in observations)
    return {"schema": "cas/stance-contact-qa/1.0",
            "status": "PASS" if maximum <= tolerance_px else "FAIL",
            "tolerancePx": tolerance_px, "maxDriftPx": maximum,
            "stanceSamples": len(observations),
            "perFootMaxPx": {side: max(values) if values else None
                             for side, values in displacements.items()},
            "observations": observations, "adoptionReady": False}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("frames_json", type=Path)
    p.add_argument("--tolerance-px", type=float, default=2.0)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    result = audit_stance(json.loads(args.frames_json.read_text(encoding="utf-8")),
                          args.tolerance_px)
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        if args.output.resolve() == args.frames_json.resolve():
            p.error("output cannot overwrite input")
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 1 if result["status"] == "FAIL" else (2 if result["status"] == "NOT_RUN" else 0)


if __name__ == "__main__":
    raise SystemExit(main())

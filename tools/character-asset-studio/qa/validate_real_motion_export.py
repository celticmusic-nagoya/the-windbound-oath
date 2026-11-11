#!/usr/bin/env python3
"""Fail-closed validator for evidence-backed real motion contact exports.

Does not infer foot identity or transform local ankles into world contacts.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


def validate(data):
    issues = []
    def require(ok, code):
        if not ok:
            issues.append(code)

    require(data.get("schema") == "cas/real-motion-contact-export/1.0", "SCHEMA")
    require(data.get("rigVersion") == "1.0", "RIG_VERSION")
    source = data.get("source") or {}
    require(isinstance(source.get("path"), str) and bool(source.get("path")), "SOURCE_PATH")
    sha = source.get("sha256")
    require(isinstance(sha, str) and len(sha) == 64 and all(c in "0123456789abcdef" for c in sha), "SOURCE_SHA")
    coords = data.get("coordinateSystem") or {}
    require(coords.get("units") == "worldPx", "UNITS")
    require(isinstance(coords.get("origin"), str) and bool(coords.get("origin")), "ORIGIN")
    scale = coords.get("scale")
    require(isinstance(scale, (int, float)) and not isinstance(scale, bool) and math.isfinite(scale) and scale > 0, "SCALE")
    frames = data.get("frames")
    require(isinstance(frames, list) and bool(frames), "FRAMES")
    seen = set()
    if isinstance(frames, list):
        for i, frame in enumerate(frames):
            if not isinstance(frame, dict):
                issues.append(f"FRAME_{i}_INVALID")
                continue
            fid = frame.get("id")
            require(isinstance(fid, (str, int)) and fid not in seen, f"FRAME_{i}_ID")
            seen.add(fid)
            t = frame.get("timeMs")
            require(isinstance(t, (int, float)) and not isinstance(t, bool) and math.isfinite(t) and t >= 0, f"FRAME_{i}_TIME")
            transform = frame.get("actorTransform") or {}
            xy = transform.get("translationPx")
            require(isinstance(xy, list) and len(xy) == 2 and all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in xy), f"FRAME_{i}_TRANSFORM")
            for key in ("rotationDeg", "scale"):
                v = transform.get(key)
                require(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and (key != "scale" or v > 0), f"FRAME_{i}_{key}")
            feet = frame.get("feet") or {}
            require(set(feet) == {"L", "R"}, f"FRAME_{i}_FOOT_IDS")
            for side in ("L", "R"):
                foot = feet.get(side)
                if not isinstance(foot, dict):
                    issues.append(f"FRAME_{i}_{side}_MISSING")
                    continue
                phase = foot.get("phase")
                require(phase in ("stance", "swing"), f"FRAME_{i}_{side}_PHASE")
                require(isinstance(foot.get("provenance"), str) and bool(foot.get("provenance")), f"FRAME_{i}_{side}_PROVENANCE")
                if phase == "stance":
                    require(isinstance(foot.get("stanceId"), str) and bool(foot.get("stanceId")), f"FRAME_{i}_{side}_STANCE_ID")
                    require(foot.get("contactPoint") in ("heel", "ball", "toe"), f"FRAME_{i}_{side}_POINT")
                    pt = foot.get("worldPx")
                    require(isinstance(pt, list) and len(pt) == 2 and all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in pt), f"FRAME_{i}_{side}_WORLD")
    return {"schema": "cas/real-motion-export-validation/1.0", "status": "BLOCKED" if issues else "PASS", "issues": issues, "adoptionReady": False}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    result = validate(json.loads(args.source.read_text(encoding="utf-8")))
    out = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        if args.output.resolve() == args.source.resolve():
            ap.error("cannot overwrite input")
        args.output.write_text(out, encoding="utf-8")
    else:
        print(out, end="")
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

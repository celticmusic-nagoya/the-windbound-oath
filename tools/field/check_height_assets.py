#!/usr/bin/env python3
"""Non-mutating Phase-2 height-piece validation. PNGs are optional until delivered."""
import argparse
import json
import struct
import sys
from pathlib import Path

EXPECTED = {
    "height_cliff_rock_01": (160, 112),
    "height_cliff_ruin_01": (160, 112),
    "height_foreground_canopy_01": (280, 300),
}

def validate_pieces(spec):
    errors = []
    seen = set()
    for v in spec.get("visuals", []):
        if isinstance(v, dict) and isinstance(v.get("id"), str):
            seen.add(v["id"])
    for i, piece in enumerate(spec.get("pieces", [])):
        if not isinstance(piece, dict):
            errors.append(f"pieces[{i}]: not an object")
            continue
        pid = piece.get("id")
        if not isinstance(pid, str) or not pid:
            errors.append(f"pieces[{i}]: missing id")
        elif pid in seen:
            errors.append(f"pieces[{i}]: duplicate id {pid}")
        else:
            seen.add(pid)
        anchor = piece.get("anchor")
        if not isinstance(anchor, list) or len(anchor) != 2 or any(type(v) not in (int, float) for v in anchor):
            errors.append(f"pieces[{i}]: anchor must be [x,y]")
    return errors

def validate_png(path, expected):
    errors = []
    data = path.read_bytes()
    if len(data) < 33 or data[:8] != b"\\x89PNG\\r\\n\\x1a\\n":
        return [f"{path}: invalid PNG signature"]
    if data[12:16] != b"IHDR":
        return [f"{path}: missing IHDR"]
    width, height, depth, color = struct.unpack(">IIBB", data[16:26])
    if (width, height) != expected:
        errors.append(f"{path}: expected {expected}, got {(width, height)}")
    if depth != 8 or color != 6:
        errors.append(f"{path}: expected 8-bit RGBA, got depth={depth} color={color}")
    return errors

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spec", type=Path, help="JSON height object or map with height key")
    ap.add_argument("--assets", type=Path, help="directory containing approved PNGs")
    ap.add_argument("--require-assets", action="store_true")
    args = ap.parse_args()
    errors = []
    if args.spec:
        doc = json.loads(args.spec.read_text(encoding="utf-8"))
        errors.extend(validate_pieces(doc.get("height", doc)))
    if args.assets:
        for stem, dimensions in EXPECTED.items():
            path = args.assets / (stem + ".png")
            if not path.exists():
                if args.require_assets:
                    errors.append(f"{path}: missing")
                else:
                    print(f"SKIP {path}: not delivered")
                continue
            errors.extend(validate_png(path, dimensions))
    for e in errors:
        print("FAIL", e)
    print(f"HEIGHT ASSET CHECK: {'FAIL' if errors else 'PASS'}")
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())

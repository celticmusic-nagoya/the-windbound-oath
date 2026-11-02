#!/usr/bin/env python3
"""Validate Phase 2 candidate PNGs against repair_plan.json; fail closed."""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("FAIL: Pillow missing. Install with: python -m pip install Pillow")

ROOT = Path(__file__).resolve().parent
PLAN = json.loads((ROOT / "repair_plan.json").read_text(encoding="utf-8"))
errors = []
checked = 0

def check(path: Path, width: int, height: int) -> None:
    global checked
    if not path.is_file():
        errors.append(f"MISSING: {path.relative_to(ROOT)}")
        return
    try:
        with Image.open(path) as img:
            img.load()
            if img.format != "PNG" or img.mode != "RGBA":
                errors.append(f"FORMAT: {path.name} expected PNG RGBA; got {img.format} {img.mode}")
                return
            if img.size != (width, height):
                errors.append(f"SIZE: {path.name} {img.size} != {(width, height)}")
            pixels = img.getdata()
            if any(a not in (0, 255) for _, _, _, a in pixels):
                errors.append(f"ALPHA: {path.name} contains non-binary alpha")
            if any(a == 0 and (r or g or b) for r, g, b, a in pixels):
                errors.append(f"RGB: {path.name} contains residual RGB in transparent pixels")
            checked += 1
            print(f"CHECKED {path.relative_to(ROOT)} {img.size} {img.mode}")
    except Exception as exc:
        errors.append(f"UNREADABLE: {path.name}: {exc}")

for asset in PLAN["assets"]:
    name = asset["filename"]
    path = ROOT / ("fireplace" if name == "furn_h01_fireplace.png" else "new_drawings") / name
    check(path, asset["width"], asset["height"])

for name in ("furn_h01_fireplace_body.png", "furn_h01_fireplace_fire.png"):
    check(ROOT / "fireplace" / name, 304, 272)

# Validate the fireplace module composite pixel-for-pixel (body below fire).
try:
    body = Image.open(ROOT / "fireplace/furn_h01_fireplace_body.png").convert("RGBA")
    fire = Image.open(ROOT / "fireplace/furn_h01_fireplace_fire.png").convert("RGBA")
    complete = Image.open(ROOT / "fireplace/furn_h01_fireplace.png").convert("RGBA")
    if Image.alpha_composite(body, fire).tobytes() != complete.tobytes():
        errors.append("COMPOSITE: fireplace body + fire does not match final image pixel-for-pixel")
    else:
        print("PASS: fireplace pixel-exact alpha composite")
except Exception as exc:
    errors.append(f"COMPOSITE: cannot verify: {exc}")

print(f"Checked {checked} PNG files; {len(errors)} error(s)")
for error in errors:
    print(f"FAIL: {error}")
if checked == 0:
    errors.append("NO_ASSETS: zero files checked")
sys.exit(1 if errors else 0)

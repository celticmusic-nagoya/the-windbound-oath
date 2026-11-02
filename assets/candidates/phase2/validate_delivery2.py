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
# Stand items must touch the bottom row (anchor = feet). Floor/wall items are exempt.
STAND = {"table_small", "chair_back", "stool", "spinning_wheel", "barrel", "jar", "bed", "bed_small", "fireplace", "fireplace_body"}
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
            if path.stem.replace("furn_h01_", "") in STAND:
                bottom = max((i // width for i, (_, _, _, a) in enumerate(pixels) if a), default=-1)
                if bottom != height - 1:
                    errors.append(f"GROUND: {path.name} lowest opaque row {bottom} != {height - 1}")
            checked += 1
            print(f"CHECKED {path.relative_to(ROOT)} {img.size} {img.mode}")
    except Exception as exc:
        errors.append(f"UNREADABLE: {path.name}: {exc}")

for asset in PLAN["assets"]:
    name = asset["filename"]
    path = ROOT / ("fireplace" if name == "furn_h01_fireplace.png" else "new_drawings") / name
    check(path, asset["width"], asset["height"])

# Repairs: prefer the director's Delivery 3 files when registered, else Claude's documented repair of Delivery 1.
for asset in PLAN.get("repairs", []):
    name = asset["filename"]
    path = next((ROOT / d / name for d in ("delivery3", "claude_repair") if (ROOT / d / name).is_file()), ROOT / "delivery3" / name)
    check(path, asset["width"], asset["height"])

# Delivery 1 PASS items kept as-is.
for asset in PLAN.get("preserve_pass", []):
    check(ROOT / "delivery1" / (asset["id"] + ".png"), asset["width"], asset["height"])

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

#!/usr/bin/env python3
"""Candidate-only HD pixel sprite QA. Does not modify images or production assets."""
import argparse
import hashlib
import json
from pathlib import Path

DIRECTIONS = ("down", "left", "right", "up")
ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "assets" / "candidates" / "field-hd-pixel"

def validate(directory: Path) -> dict:
    from PIL import Image
    directory = directory.resolve()
    if not directory.is_relative_to(CANDIDATES.resolve()):
        raise ValueError("Only candidate assets may be validated")
    results = []
    dimensions = set()
    for direction in DIRECTIONS:
        file = directory / f"{direction}.png"
        if not file.is_file():
            raise ValueError(f"Missing required direction: {file}")
        with Image.open(file) as im:
            im.load()
            if im.format != "PNG" or im.mode != "RGBA":
                raise ValueError(f"{file.name}: expected RGBA PNG")
            dimensions.add(im.size)
            alpha = im.getchannel("A")
            low, high = alpha.getextrema()
            if low != 0 or high != 255:
                raise ValueError(f"{file.name}: must contain fully transparent and opaque pixels")
            bounds = alpha.getbbox()
            if not bounds or bounds[3] < im.height // 2:
                raise ValueError(f"{file.name}: missing foot-area sprite content")
            results.append({"direction": direction, "file": file.name, "width": im.width,
                            "height": im.height, "alpha_bbox": list(bounds),
                            "sha256": hashlib.sha256(file.read_bytes()).hexdigest()})
    if len(dimensions) != 1:
        raise ValueError(f"Direction canvas sizes differ: {dimensions}")
    return {"character": directory.name, "status": "technical_candidate_only",
            "files": results, "visual_official_match": "NOT_RUN",
            "android_physical_device": "NOT_RUN"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--character", help="Character directory under assets/candidates/field-hd-pixel/")
    args = parser.parse_args()
    if not args.character:
        print(json.dumps({"status": "NO_CANDIDATES_SELECTED", "note": "No art has been validated; pass --character NAME"}, ensure_ascii=False))
        return
    if not args.character.replace("-", "").replace("_", "").isalnum() or args.character.startswith("."):
        parser.error("invalid character name")
    try:
        result = validate(CANDIDATES / args.character)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"FAIL: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

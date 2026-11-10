#!/usr/bin/env python3
"""DEV walk-frame gate for Morwen HD v2. Read-only. Missing frames are NOT_READY, not PASS.
Usage: python scripts/qa_morwen_hd_walk_v2.py
Requires Pillow. Returns 2 if missing, 1 if invalid, 0 only when all six pass.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "sprite-rig" / "morwen_hd_left_walk6_delivery.json"
REGISTRY = ROOT / "data" / "morwen-hd-canonical-v2.json"


def main():
    from PIL import Image
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    spec = json.loads(MANIFEST.read_text(encoding="utf-8"))
    canonical = registry["assets"]["pixel.left"]["sha256"]
    failures, missing, passes = [], [], []
    if spec["source_sha256"] != canonical:
        failures.append("source SHA differs from canonical left")
    if spec["frame_size"] != [1200, 1600] or spec["ground_anchor"] != [600, 1540]:
        failures.append("unexpected frame space or anchor")
    if len(spec["frames"]) != 6:
        failures.append("expected exactly six frame records")
    if len({f["id"] for f in spec["frames"]}) != len(spec["frames"]):
        failures.append("duplicate frame IDs")
    for frame in spec["frames"]:
        path = ROOT / frame["path"]
        if not path.is_file():
            missing.append(frame["path"])
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if not frame.get("sha256") or digest != frame["sha256"]:
            failures.append(f'{frame["id"]}: SHA mismatch or unapproved image')
        with Image.open(path) as img:
            if img.mode != "RGBA" or list(img.size) != spec["frame_size"]:
                failures.append(f'{frame["id"]}: mode/size mismatch')
                continue
            alpha = img.getchannel("A")
            histogram = alpha.histogram()
            unexpected = [i for i in range(1, 255) if histogram[i]]
            if unexpected:
                failures.append(f'{frame["id"]}: non-binary alpha {unexpected[:10]}')
            if alpha.getbbox() is None:
                failures.append(f'{frame["id"]}: empty image')
            else:
                bounds = alpha.getbbox()
                if bounds[0] == 0 or bounds[2] == img.width or bounds[1] == 0:
                    failures.append(f'{frame["id"]}: silhouette touches canvas edge')
            passes.append(frame["id"])
    status = "FAIL" if failures else ("NOT_READY" if missing else "PASS")
    print(json.dumps({"status": status, "validated_frames": passes,
                      "missing_frames": missing, "failures": failures},
                     ensure_ascii=False, indent=2))
    return 1 if failures else (2 if missing else 0)


if __name__ == "__main__":
    raise SystemExit(main())

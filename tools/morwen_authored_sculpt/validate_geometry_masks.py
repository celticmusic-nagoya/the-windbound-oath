"""Verify rendered candidate silhouettes are nonempty, RGBA and not clipped.

This is camera/PNG technical QA, NOT Morwen design alignment or G2.
Usage: python validate_geometry_masks.py MASK_DIRECTORY
"""
import json
import sys
from pathlib import Path
from PIL import Image

root = Path(sys.argv[1])
report = {"status": "FAIL", "scope": "TECHNICAL_MASK_ONLY_NOT_G2", "images": {}}
failures = []
for part in ("head", "body_female"):
    for view in ("front", "right", "back", "left"):
        name = f"{part}_{view}_mask.png"
        path = root / name
        try:
            with Image.open(path) as image:
                if image.size != (384, 1024) or image.mode != "RGBA":
                    raise ValueError(f"EXPECTED_RGBA_384x1024 got {image.mode} {image.size}")
                alpha = image.getchannel("A")
                bbox = alpha.getbbox()
                if bbox is None:
                    raise ValueError("EMPTY_ALPHA")
                margin = min(bbox[0], bbox[1], 384 - bbox[2], 1024 - bbox[3])
                if margin < 3:
                    raise ValueError(f"CLIPPED_OR_TOO_CLOSE_TO_FRAME margin={margin}")
                report["images"][name] = {"bbox": list(bbox), "minimum_margin_px": margin, "status": "PASS"}
        except Exception as exc:
            failures.append(f"{name}: {exc}")
            report["images"][name] = {"status": "FAIL", "error": str(exc)}
report["failures"] = failures
report["status"] = "PASS" if not failures else "FAIL"
(root / "geometry_mask_qa.json").write_text(json.dumps(report, indent=2) + chr(10))
print(json.dumps(report, indent=2))
if failures:
    raise SystemExit(1)

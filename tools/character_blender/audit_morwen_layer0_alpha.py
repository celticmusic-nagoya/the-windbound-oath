"""Audit immutable Morwen Layer0 alpha masks before 3D silhouette reconstruction.

Never modifies canonical files. Reports actual alpha coverage, background
opacity and per-view bounds; does not award artistic or canonical approval.
Usage: python tools/character_blender/audit_morwen_layer0_alpha.py OUTPUT.json
"""
import hashlib
import json
import pathlib
import sys
from PIL import Image

ROOT = pathlib.Path("assets/canonical/morwen/2026-11-16")
NAMES = ("LAYER0_FRONT.png", "LAYER0_BACK.png",
         "LAYER0_PROFILE_FACING_RIGHT.png", "LAYER0_PROFILE_FACING_LEFT.png")

def audit(root=ROOT):
    manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    index = {item["filename"]: item for item in manifest["files"]}
    results = []
    for name in NAMES:
        path = root / name
        expected = index[name]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected["sha256"]:
            raise ValueError("BLOCKED canonical SHA mismatch: " + name)
        with Image.open(path) as image:
            if image.size != (expected["width"], expected["height"]) or image.mode != "RGBA":
                raise ValueError("BLOCKED reference dimensions/mode: " + name)
            alpha = image.getchannel("A")
            hist = alpha.histogram()
            width, height = image.size
            count = width * height
            corners = [alpha.getpixel((x, y)) for x, y in
                       ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1))]
            bbox = alpha.getbbox()
            results.append({
                "filename": name, "sha256": actual,
                "dimensions": [width, height],
                "alpha_zero_pixels": hist[0],
                "alpha_full_pixels": hist[255],
                "alpha_partial_pixels": sum(hist[1:255]),
                "alpha_nonzero_fraction": round((count - hist[0]) / count, 6),
                "corner_alpha": corners,
                "alpha_bbox": list(bbox) if bbox else None,
                "background_alpha_zero_at_corners": all(v == 0 for v in corners),
            })
    return {"status": "PASS_ALPHA_MEASUREMENTS_ONLY",
            "reference_unchanged": True,
            "views": results,
            "geometry_created": False,
            "G1": "BLOCKED", "G2": "NOT_RUN", "G3": "REFERENCE_ALPHA_MEASURED_ONLY",
            "G4": "NOT_RUN"}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_morwen_layer0_alpha.py OUTPUT.json")
    result = audit()
    dest = pathlib.Path(sys.argv[1])
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"],
                      "corner_alpha": {v["filename"]: v["corner_alpha"] for v in result["views"]}}))

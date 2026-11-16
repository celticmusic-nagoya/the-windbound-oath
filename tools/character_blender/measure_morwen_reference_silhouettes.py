"""Measure reference Layer0 alpha silhouettes without interpreting character design.

Input is immutable source images. Output is candidate measurements only; no
model generation, body-part guesses, or artistic approval.
Usage: python tools/character_blender/measure_morwen_reference_silhouettes.py OUTPUT.json
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path("assets/canonical/morwen/2026-11-16")
VIEWS = {
    "front": "LAYER0_FRONT.png",
    "back": "LAYER0_BACK.png",
    "facing_right": "LAYER0_PROFILE_FACING_RIGHT.png",
    "facing_left": "LAYER0_PROFILE_FACING_LEFT.png",
}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def measure(image):
    from PIL import Image
    if image.mode != "RGBA":
        raise ValueError("reference must be RGBA")
    w, h = image.size
    alpha = image.getchannel("A")
    bounds = alpha.getbbox()
    if bounds is None:
        raise ValueError("empty silhouette")
    lo, hi = alpha.getextrema()
    # Pixel-level bounds and row widths are geometric evidence, NOT body landmarks.
    rows = []
    for y in range(h):
        row = alpha.crop((0, y, w, y + 1)).getbbox()
        if row:
            rows.append({"y_px": y, "left_px": row[0], "right_exclusive_px": row[2]})
    return {
        "image_px": [w, h], "alpha_extrema": [lo, hi],
        "nonzero_alpha_bbox_xyxy_exclusive": list(bounds),
        "silhouette_height_px": bounds[3] - bounds[1],
        "silhouette_width_px": bounds[2] - bounds[0],
        "row_silhouette_extents": rows,
        "anatomical_landmarks": "NOT_MEASURED",
        "artistic_conformance": "NOT_RUN",
    }

def run(root=ROOT):
    from PIL import Image
    manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    indexed = {item["filename"]: item for item in manifest["files"]}
    results = {}
    for direction, filename in VIEWS.items():
        path = root / filename
        if not path.is_file() or filename not in indexed:
            raise ValueError("missing reference or manifest entry: " + filename)
        actual = digest(path)
        if actual != indexed[filename]["sha256"]:
            raise ValueError("reference SHA mismatch: " + filename)
        with Image.open(path) as img:
            img.load()
            result = measure(img)
        if result["image_px"] != [indexed[filename]["width"], indexed[filename]["height"]]:
            raise ValueError("reference dimensions mismatch: " + filename)
        results[direction] = {"filename": filename, "sha256": actual, **result}
    return {
        "status": "PASS_REFERENCE_GEOMETRY_MEASUREMENTS_ONLY",
        "source_authority": "BLOCKED_PENDING_PRECEDENCE",
        "reference_set": str(root),
        "views": results,
        "geometry_created": False,
        "G1": "BLOCKED", "G2": "NOT_RUN", "G3": "NOT_RUN", "G4": "NOT_RUN",
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: measure_morwen_reference_silhouettes.py OUTPUT.json")
    try:
        report = run()
        out = Path(sys.argv[1]); out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"status": report["status"], "views": list(report["views"])}))
    except (OSError, ValueError, KeyError, ImportError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}))
        sys.exit(1)

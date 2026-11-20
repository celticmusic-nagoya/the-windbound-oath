"""Measure transparent Layer 0 reference silhouettes; do not invent anatomical landmarks.
Usage: python3 extract_layer0_silhouette_landmarks.py INPUT_DIR OUTPUT_DIR
Only observed alpha boundaries are measurements. Body-part labels remain inferred.
"""
import hashlib
import json
import pathlib
import sys

from PIL import Image

src, out = (pathlib.Path(x) for x in sys.argv[1:3])
out.mkdir(parents=True, exist_ok=True)
expected = {
    "front": ("7809.png", "b0a5d9f6c77c4a73a9f8bcca3dd2d8acad62403f374e04ebb2b0cb9b1b1199ed"),
    "right": ("7807.png", "9f4873cf331f55b72510159412bd0bfc4c606499f792626e03cffcdace7bf737"),
    "back": ("7810.png", "b9d6d6667be8d9bbed1538a42cbaea0e51bab68371366962e43463fbe394976f"),
    "left": ("7808.png", "69f23ce23cf9c56228e1e4d9a23fbab6b6607456a35239c853718a84da2298fa"),
}
data = {
    "schema_version": "0.1",
    "asset_id": "MORWEN_LAYER0_SILHOUETTE_LANDMARKS",
    "status": "MEASURED_ALPHA_SILHOUETTE_ONLY_NOT_ANATOMICAL_G1_APPROVAL",
    "pixel_origin": "TOP_LEFT",
    "alpha_threshold": 128,
    "source_views": {},
    "qa": {"G1": "PARTIAL", "G2": "NOT_RUN", "G3": "NOT_RUN", "G4": "NOT_RUN"},
}
for view, (filename, sha) in expected.items():
    path = src / filename
    assert hashlib.sha256(path.read_bytes()).hexdigest() == sha, "SOURCE_SHA_MISMATCH:" + view
    with Image.open(path) as im:
        rgba = im.convert("RGBA")
        assert rgba.size == (384, 1024), "SOURCE_DIMENSIONS_MISMATCH"
        w, h = rgba.size
        alpha = rgba.getchannel("A")
        bounds = []
        for y in range(h):
            row = [x for x in range(w) if alpha.getpixel((x, y)) >= 128]
            if row:
                bounds.append((y, min(row), max(row)))
        assert bounds, "EMPTY_ALPHA_SILHOUETTE:" + view
        xmin = min(x0 for _, x0, _ in bounds)
        xmax = max(x1 for _, _, x1 in bounds)
        ymin, ymax = bounds[0][0], bounds[-1][0]
        height = ymax - ymin + 1
        samples = []
        for ratio in (0, .05, .10, .15, .20, .25, .30, .40, .50, .60, .70, .80, .90, .95, 1):
            target = round(ymin + (height - 1) * ratio)
            nearest = min(bounds, key=lambda row: abs(row[0] - target))
            y, x0, x1 = nearest
            samples.append({
                "fraction_of_visible_height": ratio, "y": y, "left_x": x0, "right_x": x1,
                "center_x": (x0 + x1) / 2, "width_pixels": x1 - x0 + 1,
                "normalized_left": x0 / (w - 1), "normalized_right": x1 / (w - 1),
                "measured": True, "anatomical_identity": "UNDETERMINED",
            })
        data["source_views"][view] = {
            "file": filename, "sha256": sha, "image_size": [w, h],
            "alpha_bbox_xyxy": [xmin, ymin, xmax, ymax],
            "visible_height_pixels": height,
            "silhouette_scanlines": samples,
            "projection_type": "UNKNOWN_FROM_PNG",
            "camera_calibration": "NOT_AVAILABLE",
            "3d_landmarks": "NOT_INFERABLE_FROM_ALPHA_ALONE",
        }
(out / "reference_silhouette_landmarks.json").write_text(json.dumps(data, indent=2) + "\n")
print("MORWEN_LAYER0_SILHOUETTE_MEASURED_PASS", len(data["source_views"]))

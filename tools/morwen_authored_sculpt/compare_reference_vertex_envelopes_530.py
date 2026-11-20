"""Diagnostic vertex-envelope projection against SHA-verified Layer 0 alpha silhouettes.
Run in Blender 5.3 with source.blend loaded, -- REFERENCE_JSON OUTPUT_DIR.
Not a rasterized silhouette, not a calibrated camera, and not an art QA PASS.
"""
import bpy
import json
import math
import sys
from pathlib import Path
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
reference = json.loads(Path(args[0]).read_text())
out = Path(args[1]); out.mkdir(parents=True, exist_ok=True)
assert len(reference["source_views"]) == 4
views = {
    "front": (0, 1), "back": (0, -1),
    "right": (1, 0), "left": (-1, 0),
}
# Source object-space vertex coordinates; source objects may carry arbitrary
# world transforms and offsets. Normalize each candidate once in local space.
objects = ("GEO-head_stylized", "GEO-body_female_stylized")
result = {
    "schema_version": "0.1",
    "status": "DIAGNOSTIC_UNCALIBRATED_VERTEX_ENVELOPE_NOT_SILHOUETTE",
    "limitations": [
        "Projected vertices are not visible-surface raster silhouettes",
        "Unknown reference camera and perspective prevent metric 3D recovery",
        "Head-only and body-only source objects are not a complete Morwen assembly",
        "Per-view normalization removes absolute scale and position differences",
        "A low numeric discrepancy does not establish design or G2 quality",
    ],
    "objects": {},
    "qa": {"G1": "PARTIAL", "G2": "NOT_RUN", "G3": "NOT_RUN", "G4": "NOT_RUN"},
}
for name in objects:
    ob = bpy.data.objects.get(name)
    if ob is None or ob.type != "MESH": raise RuntimeError("MISSING_OBJECT:" + name)
    coords = [v.co.copy() for v in ob.data.vertices]
    if not coords: raise RuntimeError("EMPTY_MESH:" + name)
    bounds = [(min(p[i] for p in coords), max(p[i] for p in coords)) for i in range(3)]
    height = bounds[2][1] - bounds[2][0]
    assert height > 0
    result["objects"][name] = {}
    for view, (axis, sign) in views.items():
        # Standard Z-up, front=-Y. Sign controls horizontal screen orientation.
        horizontal = [(p.x if axis == 0 else p.y) * (1 if view in ("front", "left") else -1) for p in coords]
        min_x, max_x = min(horizontal), max(horizontal)
        span_x = max_x - min_x
        assert span_x > 0
        normalized = [((h - min_x) / span_x, (bounds[2][1] - p.z) / height) for h, p in zip(horizontal, coords)]
        measured = reference["source_views"][view]["silhouette_scanlines"]
        rows = []
        for item in measured:
            target = item["fraction_of_visible_height"]
            # Vertex envelope: nearest 4% of source height; sparse mesh may have gaps.
            band = [x for x, y in normalized if abs(y - target) <= 0.02]
            if not band:
                rows.append({"height_fraction": target, "status": "NO_VERTEX_IN_BAND"})
                continue
            predicted_width = max(band) - min(band)
            image_width = item["width_pixels"] / 384
            rows.append({
                "height_fraction": target,
                "candidate_normalized_width": round(predicted_width, 6),
                "reference_fraction_of_image_width": round(image_width, 6),
                "difference": round(predicted_width - image_width, 6),
                "status": "DIAGNOSTIC_ONLY_NOT_DIRECTLY_COMPARABLE",
            })
        result["objects"][name][view] = {
            "sample_count": len(rows), "rows": rows,
            "projection": "ORTHOGRAPHIC_ASSUMED",
            "camera_calibration": "UNKNOWN",
            "alignment": "PER_OBJECT_PER_VIEW_NORMALIZED",
        }
(out / "projection_diagnostic.json").write_text(json.dumps(result, indent=2) + "\n")
print("MORWEN_VERTEX_PROJECTION_DIAGNOSTIC_PASS", len(result["objects"]))

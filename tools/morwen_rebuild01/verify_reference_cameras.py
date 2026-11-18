#!/usr/bin/env python3
"""Independent geometry-only QA of packed reference empties and fixed cameras.

Run on a generated UNAPPROVED workspace; does not save or modify the .blend.
This verifies scene orientation, not pixel-level appearance or anatomical scale.
"""
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

VIEWS = {
    "FRONT": ("CAM_FRONT", Vector((0, -1, 0))),
    "BACK": ("CAM_BACK", Vector((0, 1, 0))),
    "RIGHT": ("CAM_RIGHT", Vector((-1, 0, 0))),
    "LEFT": ("CAM_LEFT", Vector((1, 0, 0))),
}

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 1:
        raise RuntimeError("Expected output JSON path after --")
    output = Path(args[0])
    scene = bpy.context.scene
    assert scene.get("status") == "UNAPPROVED_TEMPLATE_NOT_A_SCULPT"
    assert scene.get("projection_calibrated") is False
    assert len(bpy.data.meshes) == 0
    checks = {}
    for view, outward in VIEWS.items():
        ref = bpy.data.objects[f"REF_{view}_DO_NOT_EDIT"]
        camera = bpy.data.objects[VIEWS[view][0]]
        assert ref.type == "EMPTY" and ref.empty_display_type == "IMAGE"
        assert camera.type == "CAMERA" and camera.data.type == "ORTHO"
        assert ref.data.packed_file and ref.get("reference_sha256")
        normal = (ref.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
        toward_camera = (camera.location - ref.location).normalized()
        camera_forward = (camera.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
        image_right = (ref.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
        camera_right = (camera.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
        facing = normal.dot(toward_camera)
        alignment = camera_forward.dot(-toward_camera)
        horizontal = image_right.dot(camera_right)
        expected_side = toward_camera.dot(outward)
        checks[view] = {
            "normal_faces_camera": round(facing, 6),
            "camera_points_to_reference": round(alignment, 6),
            "image_horizontal_not_mirrored": round(horizontal, 6),
            "camera_on_expected_side": round(expected_side, 6),
        }
        if min(facing, alignment, horizontal, expected_side) < 0.98:
            raise AssertionError(f"{view} camera/reference orientation mismatch: {checks[view]}")
    result = {
        "status": "PASS",
        "scope": "3D orientation geometry only; no rendered image or scale calibration",
        "views": checks,
        "sculpt_mesh_count": len(bpy.data.meshes),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("REFERENCE_CAMERA_ORIENTATION_QA_PASS", output)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Render four orthographic camera views of unapproved reference-only workspace.

No meshes or approved assets are created/modified. Output is visual QA evidence.
"""
import sys
from pathlib import Path
import bpy

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 1:
        raise RuntimeError("Expected output directory after --")
    out = Path(args[0]).resolve()
    scene = bpy.context.scene
    assert scene.get("status") == "UNAPPROVED_TEMPLATE_NOT_A_SCULPT"
    assert scene.get("projection_calibrated") is False
    assert len(bpy.data.meshes) == 0
    out.mkdir(parents=True, exist_ok=True)
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.resolution_x = 768
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.display.shading.light = "STUDIO"
    for view in ("FRONT", "RIGHT", "BACK", "LEFT"):
        cam = bpy.data.objects[f"CAM_{view}"]
        assert cam.type == "CAMERA" and cam.data.type == "ORTHO"
        scene.camera = cam
        scene.render.filepath = str(out / f"MORWEN_L0_CAMERA_{view}_UNCALIBRATED.png")
        bpy.ops.render.render(write_still=True)
        if not Path(scene.render.filepath).is_file():
            raise RuntimeError(f"Render missing: {view}")
        print("REFERENCE_CAMERA_RENDER_CREATED", view, scene.render.filepath)
    print("FOUR_CAMERA_RENDER_PASS")

if __name__ == "__main__":
    main()

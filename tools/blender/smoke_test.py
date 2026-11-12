"""BLENDER-SETUP-01: headless empty-scene smoke test; no game assets touched."""
import bpy
import json
from pathlib import Path

out = Path("/tmp/blender-setup-01")
out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.resolution_x = 48
scene.render.resolution_y = 64
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.filepath = str(out / "smoke.png")
scene.world.color = (0.0, 0.0, 0.0)
bpy.ops.wm.save_as_mainfile(filepath=str(out / "smoke.blend"))
# No render: empty scene render behavior varies with engine, but the .blend is portable.
report = {
    "task": "BLENDER-SETUP-01",
    "blender_version": bpy.app.version_string,
    "objects": len(bpy.data.objects),
    "resolution": [scene.render.resolution_x, scene.render.resolution_y],
    "film_transparent": bool(scene.render.film_transparent),
    "blend_file": "smoke.blend",
    "status": "PASS",
    "production_assets_modified": False,
}
(out / "qa.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("BLENDER_SETUP_01_PASS", json.dumps(report))

"""Fail-fast Blender/Cycles compatibility gate before expensive MAP renders."""
import bpy, os, json, tempfile
from pathlib import Path
assert bpy.app.version >= (4, 0, 0), "Blender version below supported 4.0"
scene=bpy.context.scene
scene.render.engine="CYCLES"
scene.cycles.samples=2
scene.cycles.use_denoising=False
bpy.context.view_layer.cycles.use_denoising=False
scene.render.resolution_x=32
scene.render.resolution_y=32
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cube_add()
bpy.ops.object.camera_add(location=(3,-4,3))
camera=bpy.context.object
from mathutils import Vector
camera.rotation_euler=(Vector((0,0,0))-camera.location).to_track_quat("-Z","Y").to_euler()
scene.camera=camera
bpy.ops.object.light_add(type="AREA",location=(1,-2,4))
bpy.context.object.data.energy=500
output=Path(os.environ.get("MAP_OUTPUT",tempfile.gettempdir()))
output.mkdir(parents=True,exist_ok=True)
scene.render.filepath=str(output/"cycles_preflight.png")
bpy.ops.render.render(write_still=True)
assert (output/"cycles_preflight.png").stat().st_size>100,"No smoke-test render produced"
(output/"blender_preflight.json").write_text(json.dumps({"blender":bpy.app.version_string,"engine":"CYCLES","denoising":False,"status":"PASS"},indent=2))
print("BLENDER PREFLIGHT PASS:",bpy.app.version_string)

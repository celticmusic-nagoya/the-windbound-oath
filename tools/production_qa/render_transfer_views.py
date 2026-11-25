"""Render four orthographic views from the saved editable blend without saving."""
from mathutils import Vector
from pathlib import Path
import sys

import bpy

out = Path(sys.argv[sys.argv.index("--") + 1])
out.mkdir(exist_ok=False)
scene = bpy.context.scene
corners = [obj.matrix_world @ Vector(point) for obj in scene.objects if obj.type == "MESH"
           for point in obj.bound_box]
if not corners:
    raise RuntimeError("no imported visible mesh bounds")
lo = Vector(tuple(min(v[axis] for v in corners) for axis in range(3)))
hi = Vector(tuple(max(v[axis] for v in corners) for axis in range(3)))
center = (hi + lo) * 0.5
size = max(hi - lo)
if size <= 0:
    raise RuntimeError("degenerate model bounds")
bpy.ops.object.camera_add()
camera = bpy.context.object
camera.data.type = "ORTHO"
camera.data.ortho_scale = size * 1.15
scene.camera = camera
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 16
scene.render.resolution_x = scene.render.resolution_y = 1024
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
for where, strength in [((2, -3, 3), 500), ((-2, 2, 3), 350), ((0, 4, 1), 160)]:
    bpy.ops.object.light_add(type="AREA", location=center + Vector(where) * size)
    light = bpy.context.object
    light.data.energy = strength * size ** 2
    light.rotation_euler = (center - light.location).to_track_quat("-Z", "Y").to_euler()
for axis, offset in [("minus-y", (0,-1,0)), ("plus-x", (1,0,0)),
                     ("plus-y", (0,1,0)), ("minus-x", (-1,0,0))]:
    camera.location = center + Vector(offset) * (size * 3)
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(out / f"{axis}.png")
    bpy.ops.render.render(write_still=True)

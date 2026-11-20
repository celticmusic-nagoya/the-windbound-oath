import bpy,sys,json
from mathutils import Vector
from pathlib import Path
"""Read-only: render carrier-only workbench view at the C11 diagnostic camera."""
src,out=sys.argv[sys.argv.index("--")+1:]
bpy.ops.wm.open_mainfile(filepath=src)
sc=bpy.context.scene
print("SCENE",[ (o.name,o.type,o.hide_render, len(o.data.vertices) if o.type=="MESH" else 0) for o in sc.objects])
obj=bpy.data.objects["Cliff C8 B | joinable coastal segment"]
print("MW",[list(r) for r in obj.matrix_world])
import numpy as np
co=np.array([v.co[:] for v in obj.data.vertices])
print("BBOX",co.min(0),co.max(0))
sc.render.engine="BLENDER_WORKBENCH"
sc.display.shading.light="STUDIO"; sc.display.shading.color_type="SINGLE"
sc.display.shading.show_cavity=True
sc.render.resolution_x=1000; sc.render.resolution_y=720
center=obj.matrix_world@Vector((-5.95,0,2.35))
cam=bpy.data.objects.new("C",bpy.data.cameras.new("C")); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type="ORTHO"; cam.data.ortho_scale=9.5
cam.location=center+Vector((0,-12,5)); cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
for o in sc.objects:
    if o.type=="MESH": o.hide_render = o!=obj
sc.render.filepath=out; bpy.ops.render.render(write_still=True)

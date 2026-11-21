"""Print matched photo and neutral geometry previews from the saved scene."""
from pathlib import Path
import sys
import bpy

out=Path(sys.argv[-1])
scene=bpy.context.scene
assert not [i.name for i in bpy.data.images if i.source=="FILE" and i.users and not i.packed_file]
scene.render.resolution_percentage=55
scene.cycles.samples=8
scene.cycles.use_denoising=True
views=(("sunset","Sunset study"),("oblique","Coast integration"),
       ("front","front"),("elevated","elevated"),("right","right"))
for label,name in views:
    scene.camera=bpy.data.objects[name]
    scene.render.filepath=str(out/f"pbr-{label}.png")
    bpy.ops.render.render(write_still=True)
clay=bpy.data.materials.new("QA neutral geometry")
clay.diffuse_color=(.57,.57,.57,1)
for layer in scene.view_layers:
    layer.material_override=clay
for label,name in views[:3]:
    scene.camera=bpy.data.objects[name]
    scene.render.filepath=str(out/f"clay-{label}.png")
    bpy.ops.render.render(write_still=True)

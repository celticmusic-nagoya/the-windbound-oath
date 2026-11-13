"""Render four orthographic views of the Morwen candidate, not the official art."""
from pathlib import Path
import bpy
from math import radians
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "assets/candidates/mvp-blockout-01"
bpy.ops.wm.open_mainfile(filepath=str(OUT / "morwen_blockout.blend"))
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 512
scene.render.resolution_y = 768
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.film_transparent = True
world = bpy.data.worlds.new("Candidate world") if not bpy.data.worlds else bpy.data.worlds[0]
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
camera_data = bpy.data.cameras.new("Orthographic QA camera")
camera = bpy.data.objects.new("Orthographic QA camera", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera_data.type = "ORTHO"
camera_data.ortho_scale = 2.8
light_data = bpy.data.lights.new("QA key light", type="AREA")
light = bpy.data.objects.new("QA key light", light_data)
scene.collection.objects.link(light)
light.location = (2,-4,6)
light_data.energy = 450
light_data.shape = "DISK"
light_data.size = 5
from mathutils import Vector
target = Vector((0,0,1.15))
views = {"front":(0,-6,2.5),"left":(-6,0,2.5),"right":(6,0,2.5),"back":(0,6,2.5)}
(OUT/"views").mkdir(parents=True, exist_ok=True)
for name, loc in views.items():
    camera.location = loc
    direction = target - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z","Y").to_euler()
    scene.render.filepath = str(OUT/"views"/(name+".png"))
    bpy.ops.render.render(write_still=True)
    print("MORWEN_VIEW_RENDERED",name)

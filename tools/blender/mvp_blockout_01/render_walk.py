"""Render 4 directions x 8 FK walk frames. Candidate only."""
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"assets/candidates/mvp-blockout-01"
bpy.ops.wm.open_mainfile(filepath=str(OUT/"morwen_rig_walk_candidate.blend"))
scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE"
scene.render.resolution_x=512
scene.render.resolution_y=768
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGBA"
scene.render.film_transparent=True
world=scene.world
if world is None:
    world=bpy.data.worlds.new("Candidate world")
    scene.world=world
world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.8
cam_data=bpy.data.cameras.new("Walk QA camera")
cam=bpy.data.objects.new("Walk QA camera",cam_data)
scene.collection.objects.link(cam)
scene.camera=cam
cam_data.type="ORTHO"
cam_data.ortho_scale=2.8
lamp_data=bpy.data.lights.new("Walk QA light","AREA")
lamp=bpy.data.objects.new("Walk QA light",lamp_data)
scene.collection.objects.link(lamp)
lamp.location=(2,-4,6)
lamp_data.energy=450
lamp_data.size=5
views={"front":(0,-6,2.5),"left":(-6,0,2.5),"right":(6,0,2.5),"back":(0,6,2.5)}
target=Vector((0,0,1.15))
for direction,loc in views.items():
    cam.location=loc
    cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
    folder=OUT/"walk_views"/direction
    folder.mkdir(parents=True,exist_ok=True)
    for frame in range(1,9):
        scene.frame_set(frame)
        scene.render.filepath=str(folder/(f"{frame:02d}.png"))
        bpy.ops.render.render(write_still=True)
        print("MORWEN_WALK_RENDER",direction,frame)

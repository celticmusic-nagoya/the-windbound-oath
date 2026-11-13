"""Render orthographic 4-view technical silhouette contact sheet for BODY-04.
Not an art-quality approval. No source image embedded.
"""
import bpy, math, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"assets/candidates/morwen-body-04"
bpy.ops.wm.open_mainfile(filepath=str(OUT/"morwen_body_04_candidate.blend"))
scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE" if bpy.app.version<(4,2,0) else "BLENDER_EEVEE_NEXT"
scene.render.film_transparent=True
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGBA"
scene.render.resolution_x=512
scene.render.resolution_y=768
scene.render.resolution_percentage=100
world=bpy.data.worlds.new("Candidate QA World") if not bpy.data.worlds else bpy.data.worlds[0]
scene.world=world
world.use_nodes=True
world.node_tree.nodes.get("Background").inputs["Color"].default_value=(1,1,1,1)
world.node_tree.nodes.get("Background").inputs["Strength"].default_value=.7
cam_data=bpy.data.cameras.new("candidate_ortho")
cam=bpy.data.objects.new("candidate_ortho",cam_data)
scene.collection.objects.link(cam);scene.camera=cam
cam_data.type="ORTHO";cam_data.ortho_scale=1.9
target=Vector((0,0,.815))
views={"front":(0,-4,.815),"right":(4,0,.815),"back":(0,4,.815),"left":(-4,0,.815)}
for name,loc in views.items():
    cam.location=loc
    direction=target-cam.location
    cam.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
    scene.render.filepath=str(OUT/("silhouette_"+name+".png"))
    bpy.ops.render.render(write_still=True)
(OUT/"silhouette_report.json").write_text(json.dumps({"views":list(views),"camera":"ORTHO_FIXED_SCALE","resolution":[512,768],"art_qa":"NOT_RUN","reference_overlay":"NOT_AVAILABLE_IN_GITHUB","status":"TECHNICAL_RENDER_ONLY"},indent=2)+"\n")
print("MORWEN_BODY_04_FOUR_VIEW_RENDER_PASS")

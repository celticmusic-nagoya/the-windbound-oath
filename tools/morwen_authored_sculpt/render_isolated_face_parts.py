"""Render actual isolated face modules from preserved source; visual QA only."""
import bpy, math, os, sys, json
from mathutils import Vector
out=sys.argv[sys.argv.index("--")+1]
os.makedirs(out,exist_ok=True)
obj=bpy.data.objects["MORWEN_LegacyFaceParts_316_CANDIDATE"]
for o in bpy.data.objects:
    if o.type=="MESH":o.hide_render=o!=obj
obj.hide_render=False
scene=bpy.context.scene
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=24
scene.render.threads_mode="FIXED"
scene.render.threads=4
scene.render.resolution_x=960
scene.render.resolution_y=960
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=True
# Use existing mesh, materials and shape keys; no new substitute geometry.
bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.context.view_layer.objects.active=obj
world_pts=[obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
center=sum(world_pts,Vector())/8
radius=max((p-center).length for p in world_pts)
assert radius>0
camera_data=bpy.data.cameras.new("QA_FaceParts_Camera")
camera=bpy.data.objects.new("QA_FaceParts_Camera",camera_data)
scene.collection.objects.link(camera)
scene.camera=camera
camera_data.type="ORTHO"
camera_data.ortho_scale=radius*2.6
light_data=bpy.data.lights.new("QA_FaceParts_Area","AREA")
light=bpy.data.objects.new("QA_FaceParts_Area",light_data)
scene.collection.objects.link(light)
light_data.energy=800
light_data.shape="DISK"
light_data.size=radius*2
light.location=center+Vector((radius*2,-radius*3,radius*4))
def aim(o,point):
    o.rotation_euler=(point-o.location).to_track_quat("-Z","Y").to_euler()
aim(light,center)
keys=obj.data.shape_keys.key_blocks
for k in keys:k.value=0
views=[("front",Vector((0,-1,0.1))),("three_quarter",Vector((0.55,-1,0.1)))]
for name,axis in views:
    camera.location=center+axis.normalized()*radius*3.5
    aim(camera,center)
    scene.render.filepath=os.path.join(out,name+".png")
    bpy.ops.render.render(write_still=True)
# A key with blink-related naming must exist; never label another expression as blink.
blink=[k for k in keys if any(t in k.name.lower() for t in ("blink","close","eyeclose"))]
manifest={"source_blend":bpy.data.filepath,"views":[v[0] for v in views],"blink_key_candidates":[k.name for k in blink]}
if blink:
    blink[0].value=1
    camera.location=center+Vector((0,-1,0.1)).normalized()*radius*3.5
    aim(camera,center)
    scene.render.filepath=os.path.join(out,"blink_candidate.png")
    bpy.ops.render.render(write_still=True)
    manifest["views"].append("blink_candidate")
else:
    manifest["blink_status"]="BLOCKED_NO_NAMED_BLINK_KEY"
with open(os.path.join(out,"render_manifest.json"),"w") as f:json.dump(manifest,f,indent=2)

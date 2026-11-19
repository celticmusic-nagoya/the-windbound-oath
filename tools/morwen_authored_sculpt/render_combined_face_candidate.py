"""Render legacy face skin, eye mesh and preserved isolated facial regions together.
Candidate comparison only; no source asset edits or official adoption.
"""
import bpy, json, math, os, sys
from mathutils import Vector
out=sys.argv[sys.argv.index("--")+1]
os.makedirs(out,exist_ok=True)
scene=bpy.context.scene
parts=bpy.data.objects["MORWEN_LegacyFaceParts_316_CANDIDATE"]
source=bpy.data.objects["Face"]
eyes=bpy.data.objects.get("MORWEN_Eyes")
assert eyes and source.data.shape_keys and len(source.data.shape_keys.key_blocks)==58
# Copy the original face, then remove ONLY material islands already present in parts.
bpy.ops.object.select_all(action="DESELECT")
source.hide_set(False)
source.select_set(True)
bpy.context.view_layer.objects.active=source
bpy.ops.object.duplicate()
skin=bpy.context.object
skin.name="MORWEN_FaceSkin_Complement_QA"
selected={i for i,m in enumerate(skin.data.materials) if m and any(t in m.name for t in ("FaceEyelash","FaceEyeline","FaceBrow"))}
assert len(selected)==3
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="DESELECT")
bpy.ops.mesh.select_mode(type="FACE")
bpy.ops.object.mode_set(mode="OBJECT")
for v in skin.data.vertices:v.select=False
for e in skin.data.edges:e.select=False
for p in skin.data.polygons:p.select=p.material_index in selected
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.delete(type="FACE")
bpy.ops.object.mode_set(mode="OBJECT")
assert len(skin.data.polygons)+len(parts.data.polygons)==len(source.data.polygons)
for o in bpy.data.objects:
    if o.type=="MESH":o.hide_render=o not in (skin,parts,eyes)
for o in (skin,parts,eyes):o.hide_render=False;o.hide_set(False)
for o in (skin,parts):
    if o.data.shape_keys:
        for k in o.data.shape_keys.key_blocks:k.value=0
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=32
scene.render.threads_mode="FIXED"
scene.render.threads=4
scene.render.resolution_x=960
scene.render.resolution_y=960
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=True
# Fit camera to face only; eyes and separated parts share original object transforms.
pts=[skin.matrix_world @ Vector(p) for p in skin.bound_box]
center=sum(pts,Vector())/8
radius=max((p-center).length for p in pts)
assert radius>0
camd=bpy.data.cameras.new("QA_CombinedFace_Camera")
cam=bpy.data.objects.new("QA_CombinedFace_Camera",camd)
scene.collection.objects.link(cam)
scene.camera=cam
camd.type="ORTHO"
camd.ortho_scale=radius*2.7
def aim(o,pt):o.rotation_euler=(pt-o.location).to_track_quat("-Z","Y").to_euler()
ld=bpy.data.lights.new("QA_CombinedFace_Area","AREA")
lamp=bpy.data.objects.new("QA_CombinedFace_Area",ld)
scene.collection.objects.link(lamp)
ld.energy=800
ld.size=radius*2
lamp.location=center+Vector((radius*2,-radius*3,radius*4))
aim(lamp,center)
views={"front":Vector((0,-1,0.08)),"three_quarter":Vector((0.6,-1,0.08))}
for name,direction in views.items():
    cam.location=center+direction.normalized()*radius*3.5
    aim(cam,center)
    scene.render.filepath=os.path.join(out,name+".png")
    bpy.ops.render.render(write_still=True)
    assert os.path.getsize(scene.render.filepath)>1000
manifest={"source_blend":bpy.data.filepath,"status":"CANDIDATE_NOT_ART_PASS","parts_faces":len(parts.data.polygons),"skin_faces":len(skin.data.polygons),"source_faces":len(source.data.polygons),"eyes_faces":len(eyes.data.polygons),"views":list(views),"notes":"Existing legacy source mesh/materials, not an authored new high-quality sculpt"}
with open(os.path.join(out,"combined_face_manifest.json"),"w") as f:json.dump(manifest,f,indent=2)
print("MORWEN_COMBINED_FACE_RENDER_PASS",json.dumps(manifest))

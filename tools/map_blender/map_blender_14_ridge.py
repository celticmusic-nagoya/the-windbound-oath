"""MAP-BLENDER-14: replace ridge placeholder with a curved occlusion berm."""
import bpy,os,json,hashlib,math
from pathlib import Path
from mathutils import Vector
out=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview")).resolve()
src=out/"rilde_map13.blend"
if not src.is_file():raise RuntimeError("Missing MAP13 predecessor")
source_sha=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(src))
old=bpy.data.objects.get("Intervening ridge")
if old:old.hide_render=True
# The ridge is a curved north-south landform, rather than a rectangular slab.
# Retain both the source object and the source .blend for rollback.
points=[(-16,-1,3.4),(-15,2,4.2),(-14,5,5.0),(-13,8,5.7),(-12,11,5.1),(-11,14,4.2),(-10,17,3.1)]
width=4.4
verts=[]
for x,y,h in points:
 for dx,z in [(-width,0),(-width*.58,h*.78),(0,h),(width*.58,h*.76),(width,0)]:
  verts.append((x+dx,y,z))
faces=[]
for k in range(len(points)-1):
 for j in range(4):
  a=k*5+j;faces.append((a,a+1,a+6,a+5))
mesh=bpy.data.meshes.new("MAP14 ridge mesh")
mesh.from_pydata(verts,[],faces);mesh.update()
ridge=bpy.data.objects.new("MAP14 curved intervening ridge",mesh)
bpy.context.collection.objects.link(ridge)
mat=bpy.data.materials.new("MAP14 weathered hillside")
mat.diffuse_color=(.34,.38,.25,1)
mesh.materials.append(mat)
# Use a deterministic ray test for a candidate cliff-to-village sightline.
# This is not a substitute for full cinematic camera/CG QA.
from mathutils.bvhtree import BVHTree
bvh=BVHTree.FromObject(ridge,bpy.context.evaluated_depsgraph_get())
observer=Vector((-20,10,5.2))
target=Vector((0,2,2.5))
direction=target-observer
hit=bvh.ray_cast(observer,direction.normalized(),direction.length)
occluded=hit[0] is not None
scene=bpy.context.scene
scene.camera=bpy.data.objects["FIELD_27_DEG_PROVISIONAL"]
scene.render.filepath=str(out/"rilde_map14_preview.png")
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/"rilde_map14.blend"))
files=["rilde_map14_preview.png","rilde_map14.blend"]
report={"task":"MAP-BLENDER-14","status":"RIDGE_CANDIDATE","source_sha256":source_sha,"ray_sample":{"observer":list(observer),"target":list(target),"ridge_intersection":occluded},"full_cg_occlusion":"NOT_VERIFIED","visual_qa":"NOT_RUN","runtime_modified":False,"files":{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in files}}
(out/"map14_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report))

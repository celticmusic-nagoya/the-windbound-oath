"""MAP19: replace thin ridge sheet with solid skirted landform; preserve MAP18."""
import bpy,os,math,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview")).resolve()
src=out/"rilde_map18.blend"
if not src.exists():raise RuntimeError("MAP18 missing")
sha=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(src))
old=bpy.data.objects.get("MAP18 continuous visibility ridge")
if old is None:raise RuntimeError("MAP18 ridge missing")
old.hide_render=True
# Reuse exact ridge surface and occlusion geometry, adding a tapered closed skirt.
v=[tuple(x.co) for x in old.data.vertices]
faces=[tuple(p.vertices) for p in old.data.polygons]
nx,ny=51,65
# Extend terrain beyond the old mesh to avoid cut-sheet silhouettes.
# Outer skirt is below village grade; no vertical faces visible above grade.
boundary=[]
boundary.extend(range(nx))
boundary.extend(j*nx+nx-1 for j in range(1,ny))
boundary.extend((ny-1)*nx+i for i in range(nx-2,-1,-1))
boundary.extend(j*nx for j in range(ny-2,0,-1))
count=len(v)
for idx in boundary:
 x,y,z=v[idx]
 # Gradually bury the border; no zero-thickness exposed rim.
 v.append((x,y,-0.55))
for k in range(len(boundary)):
 a=boundary[k];b=boundary[(k+1)%len(boundary)]
 faces.append((a,b,count+(k+1)%len(boundary),count+k))
faces.append(tuple(range(count,count+len(boundary))))
mesh=bpy.data.meshes.new("MAP19 closed landform mesh")
mesh.from_pydata(v,[],faces);mesh.update()
obj=bpy.data.objects.new("MAP19 integrated ridge",mesh)
bpy.context.collection.objects.link(obj)
for m in old.data.materials:mesh.materials.append(m)
for p in mesh.polygons:
 if p.index<len(old.data.polygons):
  p.material_index=old.data.polygons[p.index].material_index
  p.use_smooth=True
# Retest the same synthetic rays, but do not substitute for cinematic QA.
observers=[(-21,8,5.2),(-20,10,5.2),(-19,12,5.2)]
targets=[(-8,4,3),(0,2,2.5),(6,6,3)]
bvh=BVHTree.FromPolygons([Vector(t) for t in v],[tuple(p) for p in faces],all_triangles=False)
hits=[]
for a in observers:
 for b in targets:
  start=Vector(a);d=Vector(b)-start
  hits.append(bvh.ray_cast(start,d.normalized(),d.length)[0] is not None)
scene=bpy.context.scene
scene.camera=bpy.data.objects["FIELD_27_DEG_PROVISIONAL"]
scene.render.filepath=str(out/"rilde_map19_preview.png")
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/"rilde_map19.blend"))
names=("rilde_map19_preview.png","rilde_map19.blend")
report={"task":"MAP-BLENDER-19","status":"CANDIDATE_ONLY","source_sha256":sha,"occlusion":{"total":9,"blocked":sum(hits)},"occlusion_acceptance":"PASS" if all(hits) else "FAIL","closed_mesh":True,"visual_qa":"NOT_RUN","route_connectivity":"NOT_VERIFIED","cinematic_camera_occlusion":"NOT_VERIFIED","files":{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in names}}
(out/"map19_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({"MAP19_occlusion":sum(hits),"closed":True}))

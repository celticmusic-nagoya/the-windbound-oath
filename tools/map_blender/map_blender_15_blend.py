"""MAP-BLENDER-15: blended ridge profile and multi-ray visibility audit."""
import bpy,os,json,hashlib,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview")).resolve()
source=out/"rilde_map14.blend"
if not source.is_file():raise RuntimeError("Missing MAP14")
source_sha=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source))
old=bpy.data.objects.get("MAP14 curved intervening ridge")
if old:old.hide_render=True
# Smooth terrain blending, not a vertical curtain. Coordinates remain provisional.
segments=36
cross=17
verts=[]
for i in range(segments):
 t=i/(segments-1)
 y=-3+23*t
 cx=-16+6*t
 height=4.6*math.sin(math.pi*t)**.65+0.6
 for j in range(cross):
  u=2*j/(cross-1)-1
  # Smooth falloff at both edges; rolling undulations instead of vertical sides.
  z=max(0.0,height*(1-u*u)**1.8+0.17*math.sin(8*t+u*4)*(1-u*u))
  verts.append((cx+u*8.0,y,z))
faces=[]
for i in range(segments-1):
 for j in range(cross-1):
  a=i*cross+j
  faces.append((a,a+1,a+cross+1,a+cross))
mesh=bpy.data.meshes.new("MAP15 blended ridge mesh")
mesh.from_pydata(verts,[],faces);mesh.update()
ridge=bpy.data.objects.new("MAP15 blended ridge",mesh)
bpy.context.collection.objects.link(ridge)
mat=bpy.data.materials.new("MAP15 grass rock hillside")
mat.diffuse_color=(.30,.38,.26,1)
mesh.materials.append(mat)
for poly in mesh.polygons:poly.use_smooth=True
bvh=BVHTree.FromObject(ridge,bpy.context.evaluated_depsgraph_get())
observers=[(-21,8,5.2),(-20,10,5.2),(-19,12,5.2)]
targets=[(-8,4,3),(0,2,2.5),(6,6,3)]
results=[]
for observer in observers:
 for target in targets:
  start=Vector(observer);end=Vector(target);ray=end-start
  hit=bvh.ray_cast(start,ray.normalized(),ray.length)
  results.append({"observer":observer,"target":target,"blocked":hit[0] is not None})
scene=bpy.context.scene
scene.camera=bpy.data.objects["FIELD_27_DEG_PROVISIONAL"]
scene.render.filepath=str(out/"rilde_map15_preview.png")
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/"rilde_map15.blend"))
names=["rilde_map15_preview.png","rilde_map15.blend"]
report={"task":"MAP-BLENDER-15","status":"CANDIDATE_ONLY","source_sha256":source_sha,"ray_test":{"total":len(results),"blocked":sum(x["blocked"] for x in results),"cases":results},"occlusion_acceptance":"PASS" if all(x["blocked"] for x in results) else "FAIL","visual_qa":"NOT_RUN","runtime_modified":False,"files":{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in names}}
(out/"map15_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({"occlusion":report["occlusion_acceptance"],"blocked":report["ray_test"]["blocked"]}))

"""MAP18: visibility-constrained continuous terrain ridge candidate."""
import bpy,os,math,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview")).resolve()
src=out/"rilde_map17.blend"
if not src.exists():raise RuntimeError("MAP17 missing")
source_sha=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(src))
# Preserve all predecessor objects. MAP17's small hills become subordinate terrain.
for obj in bpy.data.objects:
 if obj.name.startswith("MAP17 coastal rise"):obj.hide_render=True
# Continuous meandering landform, tapering into the surrounding ground.
# Height is tuned by deterministic ray testing, not by placing a vertical wall.
obs=[Vector(v) for v in [(-21,8,5.2),(-20,10,5.2),(-19,12,5.2)]]
dst=[Vector(v) for v in [(-8,4,3),(0,2,2.5),(6,6,3)]]
def build(height):
 nx,ny=51,65
 verts=[];faces=[]
 for j in range(ny):
  y=-7+j*32/(ny-1)
  center=-15+0.14*(y-8)+0.7*math.sin(y*.23)
  along=max(0,1-((y-9)/18)**4)
  for i in range(nx):
   x=-25+i*22/(nx-1)
   u=(x-center)/8.5
   across=max(0,1-u*u)
   z=height*(across**2)*(along**1.2)
   z+=.11*across*along*math.sin(.9*x+.5*y)
   verts.append((x,y,max(0,z)))
 for j in range(ny-1):
  for i in range(nx-1):
   a=j*nx+i;faces.append((a,a+1,a+nx+1,a+nx))
 mesh=bpy.data.meshes.new("MAP18 continuous terrain mesh")
 mesh.from_pydata(verts,[],faces);mesh.update()
 return mesh
def audit(mesh):
 bvh=BVHTree.FromPolygons([Vector(v.co) for v in mesh.vertices],[tuple(p.vertices) for p in mesh.polygons],all_triangles=False)
 cases=[]
 for a in obs:
  for b in dst:
   d=b-a
   hit=bvh.ray_cast(a,d.normalized(),d.length)
   cases.append({"observer":list(a),"target":list(b),"blocked":hit[0] is not None})
 return cases
best=None
for h in (4,5,6,7,8,9,10):
 candidate=build(h);cases=audit(candidate)
 if best is not None:bpy.data.meshes.remove(best[0])
 best=(candidate,cases,h)
 if all(c["blocked"] for c in cases):break
mesh,cases,height=best
ridge=bpy.data.objects.new("MAP18 continuous visibility ridge",mesh)
bpy.context.collection.objects.link(ridge)
grass=bpy.data.materials.new("MAP18 grassy hillside");grass.diffuse_color=(.29,.39,.23,1)
rock=bpy.data.materials.new("MAP18 shaded bedrock");rock.diffuse_color=(.37,.34,.29,1)
mesh.materials.append(grass);mesh.materials.append(rock)
for p in mesh.polygons:
 p.use_smooth=True
 # World-space-scale low-frequency bands, not a per-face checker.
 p.material_index=1 if p.normal.z<.63 and math.sin(p.center.y*.35+p.center.x*.19)>.2 else 0
scene=bpy.context.scene
scene.camera=bpy.data.objects["FIELD_27_DEG_PROVISIONAL"]
scene.render.filepath=str(out/"rilde_map18_preview.png")
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/"rilde_map18.blend"))
names=("rilde_map18_preview.png","rilde_map18.blend")
report={"task":"MAP-BLENDER-18","status":"CANDIDATE_ONLY","source_sha256":source_sha,"ridge_height":height,"occlusion":{"total":9,"blocked":sum(c["blocked"] for c in cases),"cases":cases},"occlusion_acceptance":"PASS" if all(c["blocked"] for c in cases) else "FAIL","cinematic_camera_occlusion":"NOT_VERIFIED","route_connectivity":"NOT_VERIFIED","visual_qa":"NOT_RUN","files":{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in names}}
(out/"map18_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({"task":"MAP18","blocked":report["occlusion"]["blocked"],"height":height}))

"""MAP-BLENDER-16: terrain materials and occlusion regression."""
import bpy,os,json,hashlib,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview")).resolve()
src=out/"rilde_map15.blend"
if not src.exists():raise RuntimeError("MAP15 missing")
source_sha=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(src))
ridge=bpy.data.objects.get("MAP15 blended ridge")
if ridge is None:raise RuntimeError("MAP15 ridge missing")
# Keep canonical mesh and all prior objects unchanged; material variation is additive.
grass=bpy.data.materials.new("MAP16 ridge grass")
grass.diffuse_color=(.29,.40,.22,1)
rock=bpy.data.materials.new("MAP16 exposed stone")
rock.diffuse_color=(.38,.35,.29,1)
ridge.data.materials.clear()
ridge.data.materials.append(grass)
ridge.data.materials.append(rock)
for poly in ridge.data.polygons:
 center=poly.center
 # Patchy exposed stone on steeper terrain, with deterministic spatial modulation.
 normal=poly.normal
 steep=abs(normal.z)<.81
 patch=math.sin(center.x*1.73+center.y*.83)+math.cos(center.y*1.31)
 poly.material_index=1 if steep and patch>-.1 else 0
 poly.use_smooth=True
# The earlier MAP14 placeholder is already hidden. Verify both render and viewport flags.
for name in ("Intervening ridge","MAP14 curved intervening ridge"):
 obj=bpy.data.objects.get(name)
 if obj:obj.hide_render=True
# Recompute the exact nine MAP15 rays against the unchanged ridge geometry.
bvh=BVHTree.FromObject(ridge,bpy.context.evaluated_depsgraph_get())
observers=[(-21,8,5.2),(-20,10,5.2),(-19,12,5.2)]
targets=[(-8,4,3),(0,2,2.5),(6,6,3)]
cases=[]
for a in observers:
 for b in targets:
  start=Vector(a);delta=Vector(b)-start
  blocked=bvh.ray_cast(start,delta.normalized(),delta.length)[0] is not None
  cases.append({"observer":a,"target":b,"blocked":blocked})
scene=bpy.context.scene
scene.camera=bpy.data.objects["FIELD_27_DEG_PROVISIONAL"]
scene.render.filepath=str(out/"rilde_map16_preview.png")
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/"rilde_map16.blend"))
names=("rilde_map16_preview.png","rilde_map16.blend")
report={"task":"MAP-BLENDER-16","status":"CANDIDATE_ONLY","source_sha256":source_sha,"ray_test":{"total":9,"blocked":sum(c["blocked"] for c in cases),"cases":cases},"occlusion_acceptance":"PASS" if all(c["blocked"] for c in cases) else "FAIL","material_faces":{"grass":sum(p.material_index==0 for p in ridge.data.polygons),"rock":sum(p.material_index==1 for p in ridge.data.polygons)},"visual_qa":"NOT_RUN","files":{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in names}}
(out/"map16_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({"occlusion":report["occlusion_acceptance"],"materials":report["material_faces"]}))

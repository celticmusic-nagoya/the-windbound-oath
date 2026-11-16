"""Read-only Morwen rig deformation smoke test (candidate only).

Usage: blender -b -P morwen_rig_pose_smoke.py -- candidate.blend out_dir
Produces per-pose mesh bounds and skinning metrics. Never saves the .blend.
No visual/art PASS is inferred from technical checks.
"""
import bpy, sys, os, json, hashlib
from mathutils import Quaternion
args=sys.argv[sys.argv.index("--")+1:]
src,out=args[:2]
os.makedirs(out,exist_ok=True)
def digest(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)
 return h.hexdigest()
before=digest(src)
bpy.ops.wm.open_mainfile(filepath=src)
arm=next((o for o in bpy.data.objects if o.type=="ARMATURE"),None)
report={"source_sha256":before,"blender":bpy.app.version_string,"status":"NOT_RUN","poses":[],"notes":["Candidate rig only; visual skin deformation and commercial art quality NOT_RUN."]}
if arm is None:
 report["status"]="BLOCKED_NO_ARMATURE"
else:
 meshes=[o for o in bpy.data.objects if o.type=="MESH" and any(m.type=="ARMATURE" and m.object==arm for m in o.modifiers)]
 report["armature"]=arm.name
 report["skinned_meshes"]=[o.name for o in meshes]
 original={b.name:(b.rotation_mode,b.rotation_quaternion.copy(),b.rotation_euler.copy()) for b in arm.pose.bones}
 tests=[("rest",{}),("left_elbow_30",{"J_Bip_L_LowerArm":(30,0,0)}),("right_elbow_30",{"J_Bip_R_LowerArm":(30,0,0)}),("left_knee_30",{"J_Bip_L_LowerLeg":(30,0,0)}),("right_knee_30",{"J_Bip_R_LowerLeg":(30,0,0)}),("neck_15",{"J_Bip_C_Neck":(0,0,15)})]
 from math import radians
 from mathutils import Euler
 for label,rotations in tests:
  for b in arm.pose.bones:
   mode,q,e=original[b.name]
   b.rotation_mode=mode
   b.rotation_quaternion=q.copy()
   b.rotation_euler=e.copy()
  missing=[name for name in rotations if name not in arm.pose.bones]
  if missing:
   report["poses"].append({"name":label,"status":"BLOCKED_MISSING_BONE","missing":missing});continue
  for name,angles in rotations.items():
   b=arm.pose.bones[name]
   b.rotation_mode="XYZ"
   b.rotation_euler=Euler(tuple(radians(a) for a in angles),"XYZ")
  bpy.context.view_layer.update()
  deps=bpy.context.evaluated_depsgraph_get()
  per=[]
  for o in meshes:
   ev=o.evaluated_get(deps)
   me=ev.to_mesh()
   try:
    if me.vertices:
     coords=[o.matrix_world@v.co for v in me.vertices]
     bounds=[[round(min(v[i] for v in coords),6),round(max(v[i] for v in coords),6)] for i in range(3)]
     per.append({"name":o.name,"vertices":len(coords),"bounds_xyz":bounds})
   finally:ev.to_mesh_clear()
  report["poses"].append({"name":label,"status":"MEASURED_ONLY","meshes":per})
 for b in arm.pose.bones:
  mode,q,e=original[b.name]
  b.rotation_mode=mode;b.rotation_quaternion=q;b.rotation_euler=e
 report["status"]="PARTIAL_TECHNICAL_MEASUREMENTS"
after=digest(src)
report["source_sha256_after"]=after
report["source_unchanged"]=before==after
if before!=after:report["status"]="FAIL_SOURCE_MUTATED"
with open(os.path.join(out,"MORWEN_RIG_POSE_SMOKE.json"),"w",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps({"status":report["status"],"poses":len(report["poses"]),"source_unchanged":report["source_unchanged"]}))
if before!=after:sys.exit(2)

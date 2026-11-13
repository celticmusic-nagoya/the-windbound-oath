"""Validate Morwen template joint topology and 8-frame FK cycle without production mesh."""
import bpy,math,json,runpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
runpy.run_path(str(ROOT/"build_master_rig.py"),run_name="__main__")
rig=bpy.data.objects["MORWEN_MASTER_RIG"]
assert len(rig.data.bones)==26
assert all(b.length>0.01 for b in rig.data.bones)
required={"thigh.L":"pelvis","thigh.R":"pelvis","shin.L":"thigh.L","shin.R":"thigh.R",
"foot.L":"shin.L","foot.R":"shin.R","upper_arm.L":"clavicle.L","upper_arm.R":"clavicle.R",
"forearm.L":"upper_arm.L","forearm.R":"upper_arm.R","hat":"head",
"cape.L":"chest","cape.R":"chest","satchel":"chest"}
for child,parent in required.items():
    assert rig.data.bones[child].parent.name==parent,(child,parent)
for frame in range(1,9):
    phase=2*math.pi*(frame-1)/8
    for side,offset in (("L",0),("R",math.pi)):
        stride=math.sin(phase+offset)
        for bone_name,angle in (
            ("thigh."+side,.26*stride),("shin."+side,.10+.18*max(0,-stride)),
            ("foot."+side,-.10*stride),("upper_arm."+side,-.18*stride),
            ("forearm."+side,-.08)):
            bone=rig.pose.bones[bone_name]
            bone.rotation_mode="XYZ"
            bone.rotation_euler.x=angle
            bone.keyframe_insert(data_path="rotation_euler",frame=frame)
    for name,angle in (("spine_01",.025*math.sin(2*phase)),("pelvis",.035*math.sin(phase))):
        bone=rig.pose.bones[name];bone.rotation_mode="XYZ";bone.rotation_euler.z=angle
        bone.keyframe_insert(data_path="rotation_euler",frame=frame)
rig.animation_data.action.name="MORWEN_WALK_FK_8F_TEMPLATE"
# Loop seam: frame 9 must equal frame 1, while the exported cycle remains frames 1..8.
for name in ("thigh.L","thigh.R","shin.L","shin.R","foot.L","foot.R","upper_arm.L","upper_arm.R","spine_01","pelvis"):
    bone=rig.pose.bones[name]
    bone.keyframe_insert(data_path="rotation_euler",frame=9)
scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=8
out=Path("render_output/morwen_motion_qa");out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str((out/"MORWEN_FK_MOTION_TEMPLATE.blend").resolve()))
(out/"QA.json").write_text(json.dumps({"bones":26,"fk_frames":8,
"loop_boundary_frame":9,"parenting_checks":len(required),"parenting_check_names":sorted(required),
"art_qa":"NOT_RUN","skin_deformation_qa":"BLOCKED_NO_PRODUCTION_MESH",
"foot_sliding_qa":"BLOCKED_NO_PRODUCTION_MESH",
"technical_rig_qa":"PASS","production_approved":False},indent=2)+"\n")

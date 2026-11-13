"""MORWEN-RIG-02: noncanonical rigid-weight FK walk, 8-frame cycle."""
import bpy, json, math
from pathlib import Path
from mathutils import Quaternion
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"assets/candidates/mvp-blockout-01"
bpy.ops.wm.open_mainfile(filepath=str(OUT/"morwen_blockout.blend"))
from master_rig import create_rig
rig=create_rig()
mapping={"torso":"chest","pelvis":"pelvis","neck":"neck","head":"head","hair_cap":"head"}
for side in ("L","R"):
    mapping.update({f"arm_{side}":f"upper_arm.{side}",f"hand_{side}":f"hand.{side}",
                    f"thigh_{side}":f"thigh.{side}",f"sock_{side}":f"shin.{side}",
                    f"boot_{side}":f"foot.{side}"})
for name,bone in mapping.items():
    obj=bpy.data.objects.get(name)
    assert obj is not None and obj.type=="MESH" and bone in rig.data.bones,(name,bone)
    for g in list(obj.vertex_groups):obj.vertex_groups.remove(g)
    group=obj.vertex_groups.new(name=bone)
    group.add(list(range(len(obj.data.vertices))),1.0,"REPLACE")
    mod=obj.modifiers.new("TWO_Rig","ARMATURE")
    mod.object=rig
    mod.use_vertex_groups=True
    obj.parent=rig
    obj.matrix_parent_inverse=rig.matrix_world.inverted()
assert len(mapping)==15
scene=bpy.context.scene
scene.frame_start=1;scene.frame_end=8
# FK pose: alternate leg swing. Action keys at 1,3,5,7,9.
# All pose bones use quaternion to avoid Euler-axis ambiguity.
for p in rig.pose.bones:
    p.rotation_mode="QUATERNION"
action_name="TWO_WALK_FK_8F_v1"
for frame in (1,3,5,7,9):
    scene.frame_set(frame)
    phase=(frame-1)*math.pi/4
    for p in rig.pose.bones:
        p.rotation_quaternion=Quaternion((1,0,0,0))
        p.location=(0,0,0)
    for suffix,sign in ((".L",1),(".R",-1)):
        swing=math.cos(phase)*sign
        # Local X may differ from global X; validate visually before ART PASS.
        rig.pose.bones["thigh"+suffix].rotation_quaternion=Quaternion((1,0,0),math.radians(17*swing))
        rig.pose.bones["shin"+suffix].rotation_quaternion=Quaternion((1,0,0),math.radians(8*(1-swing)/2))
    rig.pose.bones["pelvis"].location.z=.012*(1-math.cos(2*phase))/2
    for name in ("pelvis","thigh.L","thigh.R","shin.L","shin.R"):
        p=rig.pose.bones[name]
        p.keyframe_insert(data_path="rotation_quaternion",frame=frame)
        if name=="pelvis":p.keyframe_insert(data_path="location",frame=frame)
scene.frame_set(1)
assert rig.animation_data and rig.animation_data.action
rig.animation_data.action.name=action_name
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"morwen_rig_walk_candidate.blend"))
(OUT/"rig_report.json").write_text(json.dumps({"rig":rig.name,"core_bones":len(rig.data.bones),
 "weighted_parts":len(mapping),"action":action_name,"cycle_frames":8,
 "visual_qa":"NOT_RUN","canonical_modified":False},indent=2)+"\n")
print("MORWEN_RIG_02_STRUCTURE_PASS")

"""Independent Blender-12 deformation and weight QA for connected Morwen body."""
import json,math
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"assets/candidates/morwen-blender-12"
RIG="Morwen_unified_17_candidate"
BODY="Morwen_11_voxel_union_candidate"
POSES={"forearm.L":.30,"forearm.R":-.30,"shin.L":.22,"shin.R":-.22,
       "upper_arm.L":.25,"upper_arm.R":-.25,"thigh.L":.18,"thigh.R":-.18}

def evaluated_points(obj):
    deps=bpy.context.evaluated_depsgraph_get()
    deps.update()
    ev=obj.evaluated_get(deps);mesh=ev.to_mesh()
    try:return [ev.matrix_world @ v.co for v in mesh.vertices]
    finally:ev.to_mesh_clear()

def main():
    rig=bpy.data.objects[RIG]
    body=bpy.data.objects[BODY]
    assert len(rig.data.bones)==17
    assert len(body.data.vertices)>100
    assert any(m.type=="ARMATURE" and m.object==rig for m in body.modifiers)
    names={g.index:g.name for g in body.vertex_groups}
    weighted=0;max_error=0;missing=0
    for vertex in body.data.vertices:
        weights=[w.weight for w in vertex.groups if w.group in names]
        if not weights:missing+=1;continue
        weighted+=1
        max_error=max(max_error,abs(sum(weights)-1))
    assert missing==0,(missing,weighted)
    assert max_error<.001,max_error
    before=evaluated_points(body)
    original={name:rig.pose.bones[name].rotation_mode for name in POSES}
    displacement={}
    try:
        for name,angle in POSES.items():
            bone=rig.pose.bones[name]
            bone.rotation_mode="XYZ"
            bone.rotation_euler.x=angle
            after=evaluated_points(body)
            movement=max((a-b).length for a,b in zip(after,before))
            displacement[name]=movement
            bone.rotation_euler.x=0
            assert movement>1e-6,(name,movement)
        reset=evaluated_points(body)
        reset_error=max((a-b).length for a,b in zip(reset,before))
        assert reset_error<1e-5,reset_error
    finally:
        for name,mode in original.items():
            rig.pose.bones[name].rotation_euler=(0,0,0)
            rig.pose.bones[name].rotation_mode=mode
    OUT.mkdir(parents=True,exist_ok=True)
    report={"task":"MORWEN-BLENDER-12","bones":len(rig.data.bones),
        "vertices":len(body.data.vertices),"weighted_vertices":weighted,
        "missing_weights":missing,"max_weight_sum_error":max_error,
        "pose_displacements":displacement,"reset_error":reset_error,
        "visual_qa":"NOT_RUN","production_use":False}
    (OUT/"deformation_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MORWEN_12_DEFORMATION_PASS")

if __name__=="__main__":main()

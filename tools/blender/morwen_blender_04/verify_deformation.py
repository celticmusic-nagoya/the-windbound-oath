"""MORWEN-BLENDER-04: independent rig deformation regression checks.
Run with Blender on MORWEN-BLENDER-03 generated .blend.
Does not save changes to the input file.
"""
import json
import math
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "assets/candidates/morwen-blender-04"
ARM = "Morwen_unified_17_candidate"
BODY = "Morwen_unified_neutral_3d_candidate"

def evaluated_positions(obj):
    deps = bpy.context.evaluated_depsgraph_get()
    deps.update()
    mesh = obj.evaluated_get(deps).to_mesh()
    try:
        return [tuple(v.co) for v in mesh.vertices]
    finally:
        obj.evaluated_get(deps).to_mesh_clear()

def max_distance(a,b):
    assert len(a)==len(b)
    return max(math.dist(p,q) for p,q in zip(a,b))

def main():
    rig=bpy.data.objects[ARM]
    obj=bpy.data.objects[BODY]
    assert rig.type=="ARMATURE" and obj.type=="MESH"
    assert len(rig.data.bones)==17
    assert len(obj.vertex_groups)==16
    assert any(m.type=="ARMATURE" and m.object==rig for m in obj.modifiers)
    assert bpy.context.scene["approval_status"]=="FUTURE_CANON_PENDING_APPROVAL"
    assert rig["depth"]=="INFERRED_FROM_SIDE_VIEWS_NOT_MEASURED"
    groups={g.name for g in obj.vertex_groups}
    assert groups=={b.name for b in rig.data.bones if b.use_deform}
    for vertex in obj.data.vertices:
        w=sum(g.weight for g in vertex.groups)
        assert abs(w-1)<1e-5, (vertex.index,w)
    assert all(p.area>1e-12 for p in obj.data.polygons)
    rest=evaluated_positions(obj)
    tests={}
    for bone_name in ("forearm.L","forearm.R","shin.L","shin.R"):
        pb=rig.pose.bones[bone_name]
        assert pb.rotation_mode in ("QUATERNION","XYZ","XZY","YXZ","YZX","ZXY","ZYX")
        original_mode=pb.rotation_mode
        original_rot=pb.rotation_quaternion.copy()
        try:
            pb.rotation_mode="QUATERNION"
            pb.rotation_quaternion=(math.cos(math.radians(12.5)),0,0,math.sin(math.radians(12.5)))
            moved=evaluated_positions(obj)
            delta=max_distance(rest,moved)
            assert delta>1e-5, (bone_name,delta)
            tests[bone_name]={"deformation_delta":round(delta,8),"deformed":True}
        finally:
            pb.rotation_quaternion=original_rot
            pb.rotation_mode=original_mode
        restored=evaluated_positions(obj)
        assert max_distance(rest,restored)<1e-5, bone_name
    # Explicitly keep visual, anatomical depth and skin continuity unresolved.
    report={"task":"MORWEN-BLENDER-04","status":"PASS_TECHNICAL_ONLY",
            "bones":17,"vertex_groups":16,"vertex_weights_normalized":True,
            "deformation_tests":tests,"restoration":"PASS",
            "visual_comparison":"NOT_RUN","four_view_projection":"NOT_RUN",
            "continuous_skin":False,"depth_validation":"NOT_RUN",
            "production_use":False}
    OUTPUT.mkdir(parents=True,exist_ok=True)
    (OUTPUT/"deformation_qa.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MORWEN_BLENDER_04_DEFORMATION_PASS")

if __name__=="__main__":
    main()

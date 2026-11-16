"""Analyze frozen Blender inventory; diagnostic only, never canon approval."""
import argparse,json,math
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--inventory",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Refuse overwrite")
    src=json.loads(a.inventory.read_text(encoding="utf-8"))
    if src.get("schema")!="TWO_CHARACTER_INTERFACE_INVENTORY_V1":raise ValueError("Unknown inventory")
    objects={o["name"]:o for o in src["objects"]}
    rig=objects["Armature"]
    bones={b["name"]:b for b in rig["bones"]}
    chain=["Root","J_Bip_C_Hips","J_Bip_C_Spine","J_Bip_C_Chest","J_Bip_C_UpperChest","J_Bip_C_Neck","J_Bip_C_Head"]
    problems=[]
    for parent,child in zip(chain,chain[1:]):
        if bones[child]["parent"]!=parent:problems.append("chain_parent_mismatch:"+child)
    for name in ("Body","Face"):
        o=objects[name]
        if "Armature" not in o.get("bound_armature_modifiers",[]):problems.append("missing_armature_binding:"+name)
        if len(o.get("vertex_groups",[]))!=len(bones):problems.append("group_count_diff:"+name)
    neck=bones["J_Bip_C_Neck"]
    head=bones["J_Bip_C_Head"]
    distance=math.dist(neck["tail_local"],head["head_local"])
    body=objects["Body"]
    face=objects["Face"]
    report={"schema":"TWO_CHARACTER_INTERFACE_BONE_REVIEW_V1",
      "status":"CANDIDATE_DIAGNOSTIC_ONLY" if not problems else "CANDIDATE_DIAGNOSTIC_ISSUES",
      "source_inventory_sha256":src["input_sha256"],
      "blender_version":src["blender_version"],
      "unit_system":src["scene_unit_system"],
      "scale_length":src["scene_scale_length"],
      "rig_name":rig["name"],"bone_count":len(bones),
      "neck_head_chain":[{"bone":name,"parent":bones[name]["parent"],
         "head_local":bones[name]["head_local"],"tail_local":bones[name]["tail_local"]} for name in chain],
      "neck_tail_to_head_root_distance_m":round(distance,9),
      "body_bbox_m":[body["world_bbox_min"],body["world_bbox_max"]],
      "face_bbox_m":[face["world_bbox_min"],face["world_bbox_max"]],
      "face_mesh_height_m":round(face["world_bbox_max"][2]-face["world_bbox_min"][2],8),
      "candidate_body_height_m":round(body["world_bbox_max"][2]-body["world_bbox_min"][2],8),
      "face_mesh_bbox_not_anatomical_head_length":True,
      "head_ratio":"NOT_MEASURED; do not divide bounding boxes to certify 7.5–8 heads",
      "axis_handedness":"BLOCKED_CONFLICTING_DOCUMENTS",
      "neck_seam":"BLOCKED_BONE_LOCATIONS_NOT_MESH_SEAM",
      "source_visual_alignment":"BLOCKED_REFERENCE_BINARY_UNVERIFIED",
      "problems":problems,
      "G1":"BLOCKED","G2":"NOT_RUN","G3":"PARTIAL_MEASUREMENT_ONLY","G4":"NOT_RUN"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("CHAR_BONE_REVIEW="+json.dumps({"status":report["status"],"bone_count":len(bones),
      "neck_head_distance_m":report["neck_tail_to_head_root_distance_m"],"problems":problems}),flush=True)
    if problems:raise SystemExit(1)
if __name__=="__main__":main()

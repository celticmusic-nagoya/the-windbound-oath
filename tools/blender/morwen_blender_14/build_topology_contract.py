"""Generate landmark-locked anatomy topology contract before mesh construction."""
import json, hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
ANCHORS=ROOT/"assets/candidates/morwen-blender-01/anchors_candidate.json"
OUT=ROOT/"assets/candidates/morwen-blender-14"
EXPECTED={
"front":"b0a5d9f6c77c4a73a9f8bcca3dd2d8acad62403f374e04ebb2b0cb9b1b1199ed",
"right":"9f4873cf331f55b72510159412bd0bfc4c606499f792626e03cffcdace7bf737",
"left":"69f23ce23cf9c56228e1e4d9a23fbab6b6607456a35239c853718a84da2298fa",
"back":"b9d6d6667be8d9bbed1538a42cbaea0e51bab68371366962e43463fbe394976f"}
# Explicit ring plan. These are candidate mesh design parameters, not canonical art.
REGIONS={
"torso":{"ring_vertices":24,"loops":["pelvis","waist","chest","shoulder","neck_base"]},
"arm.L":{"ring_vertices":12,"loops":["shoulder.L","upper_arm_mid.L","elbow.L","forearm_mid.L","wrist.L"]},
"arm.R":{"ring_vertices":12,"loops":["shoulder.R","upper_arm_mid.R","elbow.R","forearm_mid.R","wrist.R"]},
"leg.L":{"ring_vertices":16,"loops":["hip.L","thigh_mid.L","knee.L","shin_mid.L","ankle.L"]},
"leg.R":{"ring_vertices":16,"loops":["hip.R","thigh_mid.R","knee.R","shin_mid.R","ankle.R"]},
"neck":{"ring_vertices":16,"loops":["neck_base","neck","jaw_base"]},
"head":{"ring_vertices":24,"loops":["jaw_base","head","head_top"]}}
JOIN_CONTRACT=[
{"from":"torso","to":"arm.L","joint":"shoulder.L","require_shared_boundary":True},
{"from":"torso","to":"arm.R","joint":"shoulder.R","require_shared_boundary":True},
{"from":"torso","to":"leg.L","joint":"hip.L","require_shared_boundary":True},
{"from":"torso","to":"leg.R","joint":"hip.R","require_shared_boundary":True},
{"from":"torso","to":"neck","joint":"neck_base","require_shared_boundary":True},
{"from":"neck","to":"head","joint":"jaw_base","require_shared_boundary":True}]
def main():
    data=json.loads(ANCHORS.read_text())
    assert data["common_pixel_scale"]>0
    refs={}
    for facing,digest in EXPECTED.items():
        src=ROOT/data["facings"][facing]["source"]
        assert src.exists(),src
        actual=hashlib.sha256(src.read_bytes()).hexdigest()
        assert actual==digest,(facing,actual)
        assert data["facings"][facing]["source_sha256"]==digest
        refs[facing]={"path":str(src.relative_to(ROOT)),"sha256":actual}
    front=data["facings"]["front"]["rig_points_pixels"]
    required=["head_top","head","neck","chest","waist","pelvis",
              "shoulder.L","shoulder.R","elbow.L","elbow.R",
              "wrist.L","wrist.R","hip.L","hip.R","knee.L",
              "knee.R","ankle.L","ankle.R"]
    assert all(k in front for k in required),[k for k in required if k not in front]
    assert front["shoulder.L"][0]>front["shoulder.R"][0]
    assert front["hip.L"][0]>front["hip.R"][0]
    assert front["head_top"][1]<front["pelvis"][1]<front["ankle.L"][1]
    assert all(v["ring_vertices"]>=12 and v["ring_vertices"]%4==0 for v in REGIONS.values())
    assert len(JOIN_CONTRACT)==6
    spec={"schema_version":1,"task":"MORWEN-BLENDER-14",
          "stage":"ANATOMICAL_TOPOLOGY_CONTRACT_ONLY",
          "reference_lock":refs,"coordinate_source":str(ANCHORS.relative_to(ROOT)),
          "front_landmarks_pixels":{k:front[k] for k in required},
          "regions":REGIONS,"join_contract":JOIN_CONTRACT,
          "geometry_rules":{"no_voxel_remesh":True,"no_ellipsoid_union":True,
              "watertight_target":True,"single_component_target":True,
              "shared_vertex_joint_seams":True,"preserve_left_right_asymmetry":True},
          "mesh_generated":False,"art_approval":"NOT_RUN","production_use":False}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"topology_contract.json").write_text(json.dumps(spec,indent=2,ensure_ascii=False)+"\n")
    print("MORWEN_14_TOPOLOGY_CONTRACT_PASS")

if __name__=="__main__":main()

#!/usr/bin/env python3
"""Fail-closed semantic/approval gate for WORLD macro cliff candidate.

No mesh generation, no fabricated units, no adoption. Pure stdlib.
"""
import argparse,json,re,sys
from pathlib import Path

SHA=re.compile(r"^[0-9a-f]{64}$")
GATES={"PASS","FAIL","BLOCKED","NOT_RUN"}
REQUIRED_NULL=("local_origin","bounding_box_m","world_transform","elevation_reference","camera_projection","game_renderer","character_nominal_height","lod_budgets","collision_contract")
EXPECTED={"windward_cliffs_wnw":"ocean_cliff","raid_riverside_cliff":"river_cliff","downstream_landing":"story_landing"}
STOPPED={"GLOBAL_DECIMATE","GLOBAL_VOXEL_REMESH_SMART_UV","BLIND_FACE_RING_EROSION"}

def validate(d):
 errors=[]
 def check(ok,msg):
  if not ok:errors.append(msg)
 check(d.get("status")=="CANDIDATE_NON_CANONICAL","must remain candidate")
 check(d.get("lane")=="WORLD","WORLD lane required")
 check(d.get("scene_collection")=="LIND_TERRAIN","collection ownership mismatch")
 check(d.get("source_image_sha256")=="abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620","official visual source SHA mismatch")
 check(d.get("scan_source_sha256")=="645cadf494f60e247434451af6a88291d3be3019aa0973d635596810b0fe2d11","publisher scan SHA mismatch")
 for k in REQUIRED_NULL:check(k in d and d[k] is None,f"unapproved metric/runtime field: {k}")
 check(d.get("source_scan_is_collision") is False,"source scan must never be collision")
 check(d.get("story_jump_is_walkable") is False,"story jump must not be walkable")
 regs=d.get("regions",[])
 check(isinstance(regs,list),"regions must be list")
 if isinstance(regs,list):
  ids=[r.get("id") for r in regs if isinstance(r,dict)]
  check(len(ids)==len(set(ids)) and set(ids)==set(EXPECTED),"region ids mismatch")
  for r in regs:
   if not isinstance(r,dict):continue
   check(r.get("kind")==EXPECTED.get(r.get("id")),"region kind mismatch")
   check(r.get("macro_support")=="REQUIRED","macro terrain support mandatory")
   check(r.get("contact_zone_qa")=="NOT_RUN","unverified contact QA must remain NOT_RUN")
   if r.get("id") in ("windward_cliffs_wnw","raid_riverside_cliff"):
    check(r.get("source_scan_usage")=="surface_dressing_only","scan must be dressing only")
 edges=d.get("directed_story_edges",[])
 check(edges==[{"from":"raid_riverside_cliff","to":"downstream_landing","type":"STORY_JUMP","walkable":False}],"directed jump contract mismatch")
 qa=d.get("qa",{})
 check(qa=={"G1":"BLOCKED","G2":"NOT_RUN","G3":"NOT_RUN","G4":"NOT_RUN"},"QA must not claim unperformed work")
 check(d.get("art_status")=="REFERENCE_ONLY","unapproved art status")
 check(set(d.get("stopped_method_families",[]))==STOPPED,"failure history must remain protected")
 return errors

def main():
 p=argparse.ArgumentParser();p.add_argument("contract",type=Path)
 a=p.parse_args()
 d=json.loads(a.contract.read_text())
 errs=validate(d)
 print(json.dumps({"status":"PASS" if not errs else "FAIL","checks":"fail_closed_candidate_contract","errors":errs},indent=2))
 return 1 if errs else 0
if __name__=="__main__":sys.exit(main())

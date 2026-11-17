#!/usr/bin/env python3
"""Compute target head-height intervals from independently measured body bounds.
This is planning arithmetic, NOT anatomical landmark identification or art QA.
"""
import argparse,json,pathlib
MESH_HEIGHTS={"GEO-body_female_stylized":1.616915,"GEO-body_female_realistic":1.639320}
def main():
 p=argparse.ArgumentParser();p.add_argument("--output",required=True);a=p.parse_args()
 data={"status":"PASS_TARGET_ARITHMETIC_ONLY","target_heads":[7.5,8.0],"working_target_heads":7.75,"actual_head_counts":"BLOCKED_UNREVIEWED_ANATOMICAL_LANDMARKS","model_approval":False,"models":{}}
 for name,h in MESH_HEIGHTS.items():
  data["models"][name]={"measured_mesh_bounds_height":h,"target_head_height_range_world_units":[round(h/8,6),round(h/7.5,6)],"target_head_height_at_7_75":round(h/7.75,6),"actual_anatomical_head_height":None,"actual_head_count":None,"source":"MORWEN_BASEMESH_VERTEX_EVIDENCE_20261117.md; bounding box, not reviewer-confirmed skull/sole"}
 out=pathlib.Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(data,indent=2)+"\n")
 print(json.dumps({"status":data["status"],"models":len(data["models"])}))
if __name__=="__main__":main()

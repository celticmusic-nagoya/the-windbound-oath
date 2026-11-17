#!/usr/bin/env python3
"""Create an editable, non-destructive anatomical measurement rig in Blender.

The initial crown/chin positions are hypotheses only; user must adjust and
explicitly confirm landmarks before a head-count can be accepted.
"""
import argparse,hashlib,json,pathlib
import bpy
from mathutils import Vector

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--stage",required=True);p.add_argument("--output",required=True)
 a=p.parse_args();src=pathlib.Path(a.stage).resolve();out=pathlib.Path(a.output).resolve()
 if not src.is_file() or src==out or out.is_relative_to(src):raise SystemExit("BLOCKED invalid paths")
 source_sha=hashlib.sha256(src.read_bytes()).hexdigest()
 bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
 body=bpy.data.objects.get("MORWEN_PROPORTION_STAGE_UNAPPROVED")
 if body is None or body.type!="MESH":raise SystemExit("BLOCKED stage mesh missing")
 coords=[body.matrix_world@v.co for v in body.data.vertices]
 lo=min(v.z for v in coords);hi=max(v.z for v in coords);height=hi-lo
 if height<=0:raise SystemExit("BLOCKED invalid body height")
 coll=bpy.data.collections.new("ANATOMICAL_LANDMARKS_UNVERIFIED")
 bpy.context.scene.collection.children.link(coll)
 # Only top/bottom body bounds are geometry-derived. Chin location is a
 # placeholder, deliberately not interpreted as a measured anatomical point.
 positions={"FOOT_SOLE_BOUND":lo,"CROWN_BOUND_CANDIDATE":hi,
            "CHIN_UNVERIFIED_PLACEHOLDER":hi-height/7.75}
 for label,z in positions.items():
  ob=bpy.data.objects.new("MEASURE_"+label,None);coll.objects.link(ob)
  ob.empty_display_type="SPHERE";ob.empty_display_size=height*.012
  ob.location=(0,0,z);ob.hide_render=True
  ob["verification"]="GEOMETRY_BOUND_ONLY" if label!="CHIN_UNVERIFIED_PLACEHOLDER" else "UNVERIFIED_PLACEHOLDER"
  ob["editable"]=True
 body["head_count_target"]=7.75
 body["head_count_actual"]="NOT_MEASURED"
 body["head_landmarks_confirmed"]=False
 body["head_scaling_performed"]=False
 out.parent.mkdir(parents=True,exist_ok=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
 bpy.ops.wm.open_mainfile(filepath=str(out),load_ui=False)
 assert len([o for o in bpy.data.objects if o.name.startswith("MEASURE_")])==3
 if hashlib.sha256(src.read_bytes()).hexdigest()!=source_sha:raise SystemExit("FAIL stage modified")
 report={"status":"PASS_EDITABLE_LANDMARK_RIG","source_sha256":source_sha,
         "output_sha256":hashlib.sha256(out.read_bytes()).hexdigest(),
         "body_height_bounds":height,"target_head_count":7.75,
         "actual_head_count":"NOT_MEASURED","chin_landmark":"UNVERIFIED_PLACEHOLDER",
         "head_sculpt":"NOT_RUN","source_unchanged":True}
 (out.parent/"head_landmark_rig_manifest.json").write_text(json.dumps(report,indent=2)+"\n")
 print(json.dumps({"status":report["status"],"height":height,"head_count":"NOT_MEASURED"}))
if __name__=="__main__":main()

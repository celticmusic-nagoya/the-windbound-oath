#!/usr/bin/env python3
"""Pack SHA-verified canonical reference images into an editable Blender stage.

Reference empties are viewport-only, never rendered as geometry. Source files
and source stage are not modified; output is an explicitly unapproved copy.
"""
import argparse,hashlib,json,pathlib
import bpy
from mathutils import Vector

IMAGE_MAP={
 "MORWEN_DESIGN_SHEET_APPROVED_SOURCE.jpg":("DESIGN_SHEET",(-2.1,0,1.0)),
 "LAYER0_FRONT.png":("FRONT",(0,-1.2,0.9)),
 "LAYER0_BACK.png":("BACK",(0,1.2,0.9)),
 "LAYER0_PROFILE_FACING_LEFT.png":("LEFT",(-1.2,0,0.9)),
 "LAYER0_PROFILE_FACING_RIGHT.png":("RIGHT",(1.2,0,0.9)),
}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--stage",required=True);p.add_argument("--canonical",required=True);p.add_argument("--output",required=True)
 a=p.parse_args();stage=pathlib.Path(a.stage).resolve();root=pathlib.Path(a.canonical).resolve();output=pathlib.Path(a.output).resolve()
 if not stage.is_file() or not root.is_dir() or output==stage or output.is_relative_to(root):
  raise SystemExit("BLOCKED invalid stage, canonical or output")
 stage_sha=hashlib.sha256(stage.read_bytes()).hexdigest()
 manifest=json.loads((root/"MANIFEST.json").read_text())
 declared={v["filename"]:v for v in manifest["files"]}
 if set(declared)!=set(IMAGE_MAP):raise SystemExit("BLOCKED unexpected canonical set")
 for name,item in declared.items():
  b=(root/name).read_bytes()
  if hashlib.sha256(b).hexdigest()!=item["sha256"] or len(b)!=item["bytes"]:
   raise SystemExit("FAIL source SHA/length "+name)
 bpy.ops.wm.open_mainfile(filepath=str(stage),load_ui=False)
 mesh=bpy.data.objects.get("MORWEN_PROPORTION_STAGE_UNAPPROVED")
 if mesh is None or mesh.type!="MESH":raise SystemExit("BLOCKED missing stage mesh")
 collection=bpy.data.collections.new("CANONICAL_REFERENCE_IMAGES_VIEWPORT_ONLY")
 bpy.context.scene.collection.children.link(collection)
 record=[]
 for name,(label,location) in IMAGE_MAP.items():
  image=bpy.data.images.load(str(root/name),check_existing=False)
  image.pack()
  if image.packed_file is None:raise SystemExit("FAIL image packing "+name)
  empty=bpy.data.objects.new("CANONICAL_REF_"+label,None)
  collection.objects.link(empty)
  empty.empty_display_type="IMAGE";empty.data=image
  empty.location=location
  empty.empty_display_size=1.5 if label=="DESIGN_SHEET" else 1.65
  empty.show_in_front=True
  empty.hide_render=True
  empty["source_sha256"]=declared[name]["sha256"]
  empty["role"]="REFERENCE_ONLY_NOT_3D_GEOMETRY"
  # Reference images are not orthographic silhouette-calibrated.
  # Never claim these viewport planes align to the body mesh.
  record.append({"name":name,"object":empty.name,"sha256":declared[name]["sha256"],"packed":True,"render_hidden":True})
 mesh["canonical_reference_pack_status"]="FIVE_SOURCES_SHA_VERIFIED_PACKED"
 output.parent.mkdir(parents=True,exist_ok=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True)
 bpy.ops.wm.open_mainfile(filepath=str(output),load_ui=False)
 packed=[o for o in bpy.data.objects if o.name.startswith("CANONICAL_REF_") and o.type=="EMPTY"]
 if len(packed)!=5 or not all(o.data and o.data.packed_file and o.hide_render for o in packed):
  raise SystemExit("FAIL reopen packed references")
 if hashlib.sha256(stage.read_bytes()).hexdigest()!=stage_sha:raise SystemExit("FAIL input stage changed")
 report={"status":"PASS_PACKED_REFERENCES_ONLY","stage_sha256":stage_sha,
         "output_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
         "canonical_sources":record,"reference_alignment":"NOT_CALIBRATED",
         "character_model_art_qa":"NOT_RUN","source_stage_unchanged":True}
 (output.parent/"canonical_reference_pack_manifest.json").write_text(json.dumps(report,indent=2)+"\n")
 print(json.dumps({"status":report["status"],"packed_images":len(packed),"output_bytes":output.stat().st_size}))
if __name__=="__main__":main()

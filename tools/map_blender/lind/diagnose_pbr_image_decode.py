"""Isolated JPEG and Blender image decoding diagnostic; never edits source assets."""
import argparse,hashlib,json,sys
from pathlib import Path
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument("--source",required=True);p.add_argument("--out",required=True)
 a=p.parse_args(sys.argv[sys.argv.index("--")+1:])
 source=Path(a.source).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
 provenance=json.loads((source/"source_provenance.json").read_text())
 import bpy
 results=[]
 for asset in provenance["assets"]:
  assert asset["status"]=="DOWNLOADED_UNREVIEWED"
  model=source/asset["file"];assert sha(model)==asset["sha256"]
  gltf=json.loads(model.read_text())
  dependencies={d["uri"]:d for d in asset["dependencies"]}
  for entry in gltf.get("images",[]):
   uri=entry.get("uri");assert uri in dependencies,"Untracked image dependency"
   d=dependencies[uri];path=source/d["file"]
   assert path.is_file() and sha(path)==d["sha256"]
   # bpy.data.images.load is deliberately independent of the glTF importer.
   img=bpy.data.images.load(str(path),check_existing=False)
   row={"asset":asset["id"],"uri":uri,"sha256":d["sha256"],"file_size":path.stat().st_size,"image_name":img.name,"width":int(img.size[0]),"height":int(img.size[1]),"has_data":bool(img.has_data),"filepath":img.filepath,"packed":bool(img.packed_file)}
   try:
    row["first_pixel_rgba"]=[round(float(x),6) for x in img.pixels[:4]]
    row["pixels_access"]="PASS"
   except Exception as exc:
    row["pixels_access"]="FAIL";row["pixels_error"]=repr(exc)
   results.append(row)
 report={"blender_version":bpy.app.version_string,"images":results,"jpeg_sha_and_bpy_load":"PASS" if results and all(x["pixels_access"]=="PASS" and x["width"]>0 and x["height"]>0 for x in results) else "FAIL","production_pbr_render":"NOT_RUN","G1":"BLOCKED","G2":"NOT_RUN","G4":"NOT_RUN"}
 (out/"blender_image_decode_diagnostic.json").write_text(json.dumps(report,indent=2)+"\n")
 print("BLENDER_IMAGE_DIAGNOSTIC",json.dumps(report),flush=True)
 assert report["jpeg_sha_and_bpy_load"]=="PASS","Blender standalone image decode failed; stop"
if __name__=="__main__":main()

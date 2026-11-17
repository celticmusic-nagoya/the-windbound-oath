#!/usr/bin/env python3
"""Read-only canonical Layer0 reference silhouette audit. No art PASS inference."""
import hashlib,json,pathlib,sys
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[2]
DIR=ROOT/"assets/canonical/morwen/2026-11-16"
manifest=json.loads((DIR/"MANIFEST.json").read_text())
results=[]
for spec in manifest["files"]:
 p=DIR/spec["filename"]
 actual=hashlib.sha256(p.read_bytes()).hexdigest()
 if actual!=spec["sha256"]:raise SystemExit("BLOCKED SHA mismatch: "+p.name)
 with Image.open(p) as im:
  if im.size!=(spec["width"],spec["height"]):raise SystemExit("BLOCKED size mismatch: "+p.name)
  entry={"file":p.name,"sha256":actual,"dimensions":list(im.size),"role":"design authority" if p.suffix==".jpg" else "Layer0 inner-body reference only"}
  if im.mode=="RGBA":
   alpha=im.getchannel("A")
   bbox=alpha.point(lambda v:255 if v>=128 else 0).getbbox()
   if bbox is None:raise SystemExit("BLOCKED empty alpha: "+p.name)
   x0,y0,x1,y1=bbox
   entry["alpha128_bbox_px"]=[x0,y0,x1,y1]
   entry["alpha128_bbox_normalized"]=[round(x0/im.width,5),round(y0/im.height,5),round(x1/im.width,5),round(y1/im.height,5)]
   entry["alpha_values_extrema"]=list(alpha.getextrema())
  results.append(entry)
report={"status":"REFERENCE_HASH_AND_IMAGE_METADATA_PASS_ONLY","warning":"Layer0 alpha silhouettes are NOT approved finished costume/body silhouette. No 3D model has been compared; G1 art BLOCKED, G2 NOT_RUN.","references":results}
out=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path("morwen_reference_silhouette_audit.json")
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"status":report["status"],"references":len(results),"output":str(out)}))

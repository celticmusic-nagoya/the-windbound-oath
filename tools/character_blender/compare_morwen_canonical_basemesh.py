#!/usr/bin/env python3
"""Create a human-reviewable canonical-vs-neutral-basemesh board.
Only geometric normalization of image framing; no automatic art approval.
"""
import argparse,hashlib,json,pathlib
from PIL import Image,ImageDraw,ImageFont
CANON=("LAYER0_FRONT.png","LAYER0_BACK.png","LAYER0_PROFILE_FACING_LEFT.png","LAYER0_PROFILE_FACING_RIGHT.png")
VIEWS=("front","back","left","right")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frame(image,size=(360,720)):
 im=image.convert("RGBA")
 alpha=im.getchannel("A")
 bb=alpha.point(lambda p:255 if p>=128 else 0).getbbox()
 if bb is None:raise ValueError("empty alpha image")
 im=im.crop(bb)
 w,h=im.size
 s=min((size[0]-36)/w,(size[1]-48)/h)
 im=im.resize((max(1,round(w*s)),max(1,round(h*s))),Image.Resampling.LANCZOS)
 canvas=Image.new("RGBA",size,(43,46,52,255))
 canvas.alpha_composite(im,((size[0]-im.width)//2,(size[1]-im.height)//2))
 return canvas.convert("RGB"),{"alpha_bbox":bb,"crop_size":[w,h],"fit_scale":round(s,6)}
def main():
 p=argparse.ArgumentParser();p.add_argument("--canonical",required=True);p.add_argument("--render-dir",required=True);p.add_argument("--output",required=True);a=p.parse_args()
 root=pathlib.Path(a.canonical);renders=pathlib.Path(a.render_dir);out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((root/"MANIFEST.json").read_text())
 expected={f["filename"]:f["sha256"] for f in manifest["files"]}
 for name in CANON:
  if sha(root/name)!=expected[name]:raise SystemExit("BLOCKED canonical hash mismatch: "+name)
 rows=[];board=Image.new("RGB",(360*3,780*4),(26,28,32));draw=ImageDraw.Draw(board)
 for i,(name,view) in enumerate(zip(CANON,VIEWS)):
  sources=[root/name,renders/("GEO-body_female_realistic_"+view+"_lowglare.png"),renders/("GEO-body_female_stylized_"+view+"_lowglare.png")]
  entry={"view":view,"canonical":name,"files":[]}
  for j,src in enumerate(sources):
   if not src.is_file():raise SystemExit("BLOCKED missing "+str(src))
   img=Image.open(src);panel,details=frame(img)
   board.paste(panel,(j*360,i*780+36))
   draw.text((j*360+12,i*780+12),("CANONICAL","REALISTIC","STYLIZED")[j]+" / "+view.upper(),fill=(240,240,240))
   entry["files"].append({"path":src.name,"sha256":sha(src),**details})
  rows.append(entry)
 board_path=out/"canonical_vs_basemesh_4views.png";board.save(board_path)
 report={"status":"PASS_COMPARISON_BOARD_ONLY","canonical_hashes_verified":True,"views":rows,
         "warning":"Independent auto-fit for each panel: silhouette and costume comparison only, NOT calibrated physical scale or head-count measurement.",
         "canonical_match":"BLOCKED","anatomical_qa":"BLOCKED","production_approval":False}
 (out/"comparison_manifest.json").write_text(json.dumps(report,indent=2)+"\n")
 print(json.dumps({"status":report["status"],"views":len(rows)}))
if __name__=="__main__":main()

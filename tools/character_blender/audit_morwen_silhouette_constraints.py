#!/usr/bin/env python3
"""Canonical silhouette evidence: measure four-view widths, reject uncalibrated auto-fitting.
No mesh deformation, anatomical inference, or approval.
"""
import argparse,hashlib,json,pathlib
from PIL import Image,ImageDraw
VIEWS={"front":"LAYER0_FRONT.png","back":"LAYER0_BACK.png","left":"LAYER0_PROFILE_FACING_LEFT.png","right":"LAYER0_PROFILE_FACING_RIGHT.png"}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bbox(im):
 a=im.convert("RGBA").getchannel("A")
 return a.point(lambda x:255 if x>=128 else 0).getbbox()
def profile(im,bb,n=64):
 a=im.convert("RGBA").getchannel("A")
 x0,y0,x1,y1=bb
 out=[]
 for k in range(n):
  y=min(y1-1,y0+int((k+.5)*(y1-y0)/n))
  occupied=[x for x in range(x0,x1) if a.getpixel((x,y))>=128]
  if occupied:
   out.append({"band":k,"height_fraction_top":round((k+.5)/n,6),"left":min(occupied),"right":max(occupied),"width_px":max(occupied)-min(occupied)+1,"components_unresolved":True})
  else:out.append({"band":k,"height_fraction_top":round((k+.5)/n,6),"width_px":0,"components_unresolved":True})
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument("--canonical",required=True);p.add_argument("--candidate",required=True);p.add_argument("--output",required=True);a=p.parse_args()
 root=pathlib.Path(a.canonical);candidate=pathlib.Path(a.candidate);out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((root/"MANIFEST.json").read_text());expected={x["filename"]:x["sha256"] for x in manifest["files"]}
 report={"status":"PASS_SILHOUETTE_EVIDENCE_ONLY","calibrated_projection":False,"canonical_mesh_alignment":"BLOCKED","head_chin_landmarks":"BLOCKED","source_unchanged":True,"views":{},"warnings":["Canonical Layer0 contains hairstyle, stockings, garments and potentially different arm poses; its alpha silhouette is not a naked-body shape target.","Profiles are height-normalized for inspection, NOT camera calibrated. No automatic body deformation is authorized from these ratios."]}
 board=Image.new("RGB",(960,4*400),(27,30,36));draw=ImageDraw.Draw(board)
 for row,(view,name) in enumerate(VIEWS.items()):
  cp=root/name;rp=candidate/("MORWEN_BODY_CANDIDATE_01_"+view+".png")
  if not rp.is_file() or sha(cp)!=expected[name]:raise SystemExit("BLOCKED missing candidate or canonical SHA mismatch: "+view)
  ci=Image.open(cp);ri=Image.open(rp);cb=bbox(ci);rb=bbox(ri)
  if cb is None or rb is None:raise SystemExit("BLOCKED empty alpha")
  cprof=profile(ci,cb);rprof=profile(ri,rb)
  def place(img,bb,x):
   img=img.convert("RGBA").crop(bb);scale=min(310/img.width,350/img.height)
   img=img.resize((round(img.width*scale),round(img.height*scale)),Image.Resampling.LANCZOS)
   panel=Image.new("RGBA",img.size,(48,51,58,255));panel.alpha_composite(img)
   board.paste(panel.convert("RGB"),(x+(310-img.width)//2,row*400+40+(350-img.height)//2))
  place(ci,cb,12);place(ri,rb,332)
  draw.text((12,row*400+12),view.upper()+"  CANONICAL",fill=(242,242,242));draw.text((332,row*400+12),"CANDIDATE 01",fill=(242,242,242))
  for k in range(64):
   y=row*400+40+int((k+.5)*350/64)
   cw=cprof[k]["width_px"]/max(1,cb[2]-cb[0]);rw=rprof[k]["width_px"]/max(1,rb[2]-rb[0])
   draw.line((670,y,670+int(cw*125),y),fill=(105,189,234),width=2)
   draw.line((810,y,810+int(rw*125),y),fill=(255,183,117),width=2)
  draw.text((670,row*400+12),"RELATIVE WIDTH PROFILE",fill=(240,240,240))
  report["views"][view]={"canonical_sha256":sha(cp),"candidate_sha256":sha(rp),"canonical_bbox":cb,"candidate_bbox":rb,"canonical_bands":cprof,"candidate_bands":rprof,"calibration":"NOT_CALIBRATED"}
 board.save(out/"silhouette_constraint_evidence.png")
 (out/"silhouette_constraint_evidence.json").write_text(json.dumps(report,indent=2)+"\n")
 print("PASS evidence only; morphology inference BLOCKED pending camera/pose and layer segmentation")
if __name__=="__main__":main()

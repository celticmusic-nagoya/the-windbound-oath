"""Fail-closed visibility audit of unapproved Morwen head renders; never art PASS.

Usage: python audit_morwen_render_visibility.py RENDER_DIR OUTPUT_JSON
Exit 0 when report written, even on image FAIL: rejected candidate is preserved as
QA evidence and does not falsely break unrelated technical lanes.
"""
import hashlib,json,pathlib,sys
from PIL import Image
if len(sys.argv)!=3:raise SystemExit("usage: RENDER_DIR OUTPUT_JSON")
root=pathlib.Path(sys.argv[1]);dest=pathlib.Path(sys.argv[2])
names=["FRONT","BACK","FACING_RIGHT","FACING_LEFT","THREE_QUARTER"]
rows=[]
for name in names:
 p=root/("MORWEN_HEAD_"+name+".png")
 row={"view":name,"path":p.name,"status":"BLOCKED"}
 if p.is_file():
  try:
   im=Image.open(p).convert("RGBA");w,h=im.size
   pix=list(im.getdata());subject=[(r,g,b) for r,g,b,a in pix if a>=128]
   if subject:
    clipped=sum(1 for r,g,b in subject if min(r,g,b)>=245)/len(subject)
    bright=sum(1 for r,g,b in subject if max(r,g,b)>=250)/len(subject)
    occupied=len(subject)/(w*h)
    row.update({"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
     "dimensions":[w,h],"subject_pixels":len(subject),
     "near_white_fraction":round(clipped,5),"channel_clipping_fraction":round(bright,5),
     "subject_occupancy":round(occupied,5),
     "status":"FAIL" if clipped>.12 or bright>.55 or occupied<.02 else "PASS_VISIBILITY_ONLY"})
  except Exception as e:row["reason"]=type(e).__name__
 rows.append(row)
report={"schema":"MORWEN_RENDER_VISIBILITY_V1","status":"FAIL" if any(x["status"]=="FAIL" for x in rows) else ("BLOCKED" if any(x["status"]=="BLOCKED" for x in rows) else "PASS_VISIBILITY_ONLY"),"views":rows,"art_qa":"NOT_RUN","production_approval":False,"thresholds":{"near_white_fraction_max":.12,"channel_clipping_fraction_max":.55,"subject_occupancy_min":.02}}
dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(report,indent=2))
print(json.dumps({"status":report["status"],"views":{x["view"]:x["status"] for x in rows}}))

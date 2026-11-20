#!/usr/bin/env python3
"""Verify adopted Windward CG source bytes; make a contact sheet without altering originals."""
import hashlib, json, struct, sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[3]
MANIFEST=ROOT/"docs/art/approved-rilde-story-20261107.json"
NAMES=("sunset_background.png","sunset_two_characters_back_view.png","stargazing_seated.png","stargazing_standing_final.png","stargazing_dialogue_background.png")
def main():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
    entries=json.loads(MANIFEST.read_text())["files"]
    matches=[x for x in entries if Path(x["path"]).name in NAMES]
    if len(matches)!=len(NAMES):raise RuntimeError("Manifest lacks exact five cliff CG originals")
    sheet=Image.new("RGB",(1000,((len(matches)+1)//2)*350),"#161d27")
    draw=ImageDraw.Draw(sheet);report=[]
    for i,x in enumerate(matches):
        f=ROOT/x["path"]; rec={"path":x["path"],"expected_sha256":x["sha256"],"status":"MISSING"}
        if f.is_file():
            raw=f.read_bytes();rec.update(actual_sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
            if rec["actual_sha256"]!=x["sha256"] or len(raw)!=x["bytes"]:rec["status"]="MISMATCH"
            else:
                with Image.open(f) as im:
                    im.verify()
                with Image.open(f) as im:
                    rec["dimensions"]=list(im.size)
                    thumb=im.convert("RGB");thumb.thumbnail((480,300))
                    px=(i%2)*500+10;py=(i//2)*350+12
                    sheet.paste(thumb,(px,py+26))
                    draw.text((px,py),Path(x["path"]).name,fill="white")
                rec["status"]="PASS"
        report.append(rec)
    sheet.save(out/"windward-cg-contact-sheet.png")
    (out/"windward-cg-source-verification.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(report,indent=2))
    if any(x["status"]!="PASS" for x in report):raise SystemExit("Originals missing or mismatched; G1 FAIL/BLOCKED")
if __name__=="__main__":main()

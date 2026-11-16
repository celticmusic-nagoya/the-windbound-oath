#!/usr/bin/env python3
"""Produce preview contact sheet + manifest for chat review; never infer art PASS."""
import argparse,hashlib,json,pathlib
from PIL import Image,ImageDraw

def build(source,dest):
    files=sorted(p for p in source.rglob("*.png") if p.is_file() and p.name!="RENDER_PREVIEW_CONTACT_SHEET.png")
    dest.mkdir(parents=True,exist_ok=True)
    files=[p for p in files if dest not in p.parents]
    entries=[]; tiles=[]
    for p in files[:24]:
        with Image.open(p) as im:
            original_size=list(im.size)
            thumb=im.convert("RGBA")
            thumb.thumbnail((350,280),Image.Resampling.LANCZOS)
            tile=Image.new("RGB",(380,325),"#e5e7eb")
            bg=Image.new("RGB",thumb.size,"#ffffff")
            bg.paste(thumb,mask=thumb.getchannel("A"))
            tile.paste(bg,((380-thumb.width)//2,10+(280-thumb.height)//2))
            label=p.relative_to(source).as_posix()
            ImageDraw.Draw(tile).text((12,298),label[:55],fill="#111827")
            tiles.append(tile)
        entries.append({"path":p.relative_to(source).as_posix(),"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"dimensions":original_size})
    report={"schema":"TWO_RENDER_PREVIEW_V1","source_images_total":len(files),"shown":len(entries),"images":entries,"independent_art_qa":"NOT_RUN","production_approval":False}
    (dest/"RENDER_PREVIEW_MANIFEST.json").write_text(json.dumps(report,indent=2)+"\n")
    if tiles:
        columns=min(3,len(tiles));rows=(len(tiles)+columns-1)//columns
        sheet=Image.new("RGB",(columns*380,rows*325),"#f3f4f6")
        for i,t in enumerate(tiles):sheet.paste(t,((i%columns)*380,(i//columns)*325))
        sheet.save(dest/"RENDER_PREVIEW_CONTACT_SHEET.png",optimize=True)
    print(json.dumps({"images":len(files),"preview":len(tiles),"status":"PREVIEW_ONLY" if tiles else "BLOCKED_NO_IMAGES"}))
    if not tiles:
        raise SystemExit("BLOCKED_NO_IMAGES: render preview cannot be created without source PNGs")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("source");p.add_argument("output");a=p.parse_args()
    build(pathlib.Path(a.source),pathlib.Path(a.output))

"""Package 32 Morwen candidate walk frames into contact sheets and a ZIP.
No canonical art is modified. Run after qa_walk_frames.py.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import json, zipfile, hashlib
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"assets/candidates/mvp-blockout-01"
DIRECTIONS=("front","right","back","left")
assert json.loads((OUT/"walk_visual_qa.json").read_text())["status"]=="TECHNICAL_PASS"
thumb=(160,240)
sheet=Image.new("RGB",(8*thumb[0],4*(thumb[1]+28)),(42,46,54))
draw=ImageDraw.Draw(sheet)
for row,direction in enumerate(DIRECTIONS):
    for idx in range(8):
        source=OUT/"walk_views"/direction/f"{idx+1:02d}.png"
        with Image.open(source) as im:
            assert im.mode=="RGBA" and im.size==(512,768)
            # Checkerboard makes alpha defects immediately visible.
            tile=Image.new("RGBA",im.size,(0,0,0,255))
            td=ImageDraw.Draw(tile)
            for y in range(0,768,64):
                for x in range(0,512,64):
                    td.rectangle((x,y,x+63,y+63),fill=(98,101,108,255) if (x//64+y//64)%2 else (132,135,142,255))
            tile.alpha_composite(im)
            tile=tile.convert("RGB").resize(thumb,Image.Resampling.LANCZOS)
        sheet.paste(tile,(idx*thumb[0],row*(thumb[1]+28)+28))
        draw.text((idx*thumb[0]+6,row*(thumb[1]+28)+6),f"{direction} {idx+1:02d}",fill=(255,255,255))
sheet_path=OUT/"MORWEN_WALK_4DIR_8F_CONTACT_SHEET.png"
sheet.save(sheet_path,optimize=True)
report=json.loads((OUT/"walk_visual_qa.json").read_text())
report["package"]={"directions":list(DIRECTIONS),"frames_per_direction":8,
 "total_pngs":32,"contact_sheet":sheet_path.name,
 "visual_joint_qa":"REQUIRES_DIRECTOR","art_qa":"NOT_RUN"}
report_path=OUT/"MORWEN_RIG_02_QA_REPORT.json"
report_path.write_text(json.dumps(report,indent=2)+"\n")
zip_path=OUT/"MORWEN_RIG_02_VISUAL_QA.zip"
with zipfile.ZipFile(zip_path,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for direction in DIRECTIONS:
        for frame in range(1,9):
            p=OUT/"walk_views"/direction/f"{frame:02d}.png"
            archive.write(p,arcname=f"walk_views/{direction}/{frame:02d}.png")
    archive.write(sheet_path,arcname=sheet_path.name)
    archive.write(report_path,arcname=report_path.name)
with zipfile.ZipFile(zip_path) as archive:
    assert len(archive.namelist())==34
    assert archive.testzip() is None
print("MORWEN_RIG_02_VISUAL_PACKAGE_PASS",zip_path.stat().st_size)

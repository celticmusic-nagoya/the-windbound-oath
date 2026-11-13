"""BODY-04 visual QA package: four transparent orthographic PNGs + overview.
Never marks candidate as canon or art-approved.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import json,zipfile
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"assets/candidates/morwen-body-04"
names=("front","right","back","left")
canvas=Image.new("RGB",(4*384,608),(32,36,44))
draw=ImageDraw.Draw(canvas)
for i,name in enumerate(names):
    path=OUT/f"silhouette_{name}.png"
    with Image.open(path) as src:
        assert src.mode=="RGBA" and src.size==(512,768),(name,src.mode,src.size)
        alpha=src.getchannel("A")
        assert alpha.getbbox() and alpha.getextrema()[0]==0,name
        tile=Image.new("RGBA",src.size,(100,103,110,255))
        tile.alpha_composite(src)
        tile=tile.convert("RGB").resize((384,576),Image.Resampling.LANCZOS)
        canvas.paste(tile,(i*384,32))
    draw.text((i*384+12,10),name.upper(),fill="white")
overview=OUT/"MORWEN_BODY_04_FOUR_VIEW_OVERVIEW.png"
canvas.save(overview)
qa={"status":"TECHNICAL_PASS","frames":4,"directions":list(names),
    "reference_comparison":"BLOCKED_SOURCE_IMAGE_NOT_IN_REPO",
    "art_qa":"NOT_RUN","canonical_modified":False}
report=OUT/"MORWEN_BODY_04_VISUAL_QA.json"
report.write_text(json.dumps(qa,indent=2)+"\n")
archive=OUT/"MORWEN_BODY_04_VISUAL_QA.zip"
with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as z:
    for name in names:
        z.write(OUT/f"silhouette_{name}.png",f"views/{name}.png")
    z.write(overview,overview.name)
    z.write(report,report.name)
with zipfile.ZipFile(archive) as z:
    assert len(z.namelist())==6 and z.testzip() is None
print("MORWEN_BODY_04_VISUAL_QA_PACKAGE_PASS")

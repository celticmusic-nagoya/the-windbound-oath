"""Audit the exact approved Morwen reference before production topology work.
Usage: python3 tools/blender/production_mesh_05/audit_reference.py /path/to/source.png --out /tmp/audit
Requires Pillow. This does not alter the reference or promote a model.
"""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3]
REG=ROOT/"docs/design/MORWEN_LAYER0_REFERENCE_REGISTRY.json"
LAND=ROOT/"docs/design/MORWEN_LAYER0_LANDMARKS_CANDIDATE.json"
def main():
    p=argparse.ArgumentParser();p.add_argument("source",type=Path);p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    reg=json.loads(REG.read_text());lm=json.loads(LAND.read_text())
    raw=a.source.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    assert digest==reg["source_sha256"],"REFERENCE_SHA_MISMATCH"
    with Image.open(a.source) as im:
        assert im.size==(1536,1024),"REFERENCE_DIMENSION_MISMATCH"
        src=im.convert("RGB")
    a.out.mkdir(parents=True,exist_ok=True)
    # Markers are approximate, NOT confirmed anatomy measurements.
    overlay=src.copy();draw=ImageDraw.Draw(overlay)
    for direction in ("front","right","left","back"):
        d=lm[direction];axis=d["axis_x_approx"]
        draw.line((axis,50,axis,700),fill=(0,220,255),width=2)
        draw.text((axis+5,45),direction,fill=(0,220,255))
    for key,y in lm["front_view"].items():
        if key.endswith("_y") or key.endswith("_approx"):
            if key!="axis_x_approx" and isinstance(y,(int,float)):
                draw.line((170,y,310,y),fill=(255,80,50),width=2)
                draw.text((315,y-7),key,fill=(255,80,50))
    overlay.save(a.out/"MORWEN_REFERENCE_LANDMARK_OVERLAY.png")
    report={"source_sha256":digest,"source_dimensions":[1536,1024],
        "source_integrity":"PASS","landmark_accuracy":"UNVERIFIED",
        "orthographic_registration":"NOT_RUN","visual_art_qa":"NOT_RUN",
        "promotion_eligible":False,"note":"Guides are approximate; not an art-approved topology target"}
    (a.out/"MORWEN_REFERENCE_AUDIT.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report))
if __name__=="__main__":main()

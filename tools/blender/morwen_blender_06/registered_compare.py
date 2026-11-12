"""Registered silhouette diagnostic; never modifies canonical references."""
import hashlib, json
from pathlib import Path
from PIL import Image, ImageChops

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"assets/candidates/morwen-blender-05"
REF=ROOT/"assets/references/morwen/reference_20261112"
NAMES={"front":"REFERENCE_front.png","right":"REFERENCE_profile_facing_right.png",
       "back":"REFERENCE_back.png","left":"REFERENCE_profile_facing_left.png"}

def mask(im):
    return im.convert("RGBA").getchannel("A").point(lambda x:255 if x>=128 else 0)

def iou(a,b):
    n=ImageChops.multiply(a,b).histogram()[255]
    u=a.histogram()[255]+b.histogram()[255]-n
    return round(n/u,5) if u else 0.0

def registered(a,b):
    ab,bb=a.getbbox(),b.getbbox()
    assert ab and bb
    # Rigid translation only: no scaling, deformation, or hidden fitting.
    ax=(ab[0]+ab[2])//2;ay=(ab[1]+ab[3])//2
    bx=(bb[0]+bb[2])//2;by=(bb[1]+bb[3])//2
    dx,dy=ax-bx,ay-by
    shifted=Image.new("L",a.size,0)
    shifted.paste(b,(dx,dy))
    return shifted,dx,dy

def main():
    receipt=json.loads((ROOT/"tools/blender/morwen_blender_01/SOURCE_RECEIPT.json").read_text())
    pinned={entry["path"]:entry["sha256"] for entry in receipt["files"]}
    result={"task":"MORWEN-BLENDER-06","method":"BBOX_CENTER_TRANSLATION_ONLY",
            "art_approval":"NOT_RUN","production_use":False,"facings":{}}
    for facing,name in NAMES.items():
        p=REF/name
        assert hashlib.sha256(p.read_bytes()).hexdigest()==pinned[str(p.relative_to(ROOT))]
        with Image.open(p) as ref,Image.open(OUT/(facing+"_projection.png")) as render:
            a,b=mask(ref),mask(render)
        assert a.size==b.size==(384,1024)
        shifted,dx,dy=registered(a,b)
        result["facings"][facing]={"raw_iou":iou(a,b),"registered_iou":iou(a,shifted),
            "translation_px":[dx,dy],"reference_bbox":a.getbbox(),
            "candidate_bbox":b.getbbox(),"registered_bbox":shifted.getbbox(),
            "reference_sha256":pinned[str(p.relative_to(ROOT))]}
        # Red: reference only; blue: candidate only; white: overlap.
        red=ImageChops.subtract(a,shifted)
        blue=ImageChops.subtract(shifted,a)
        both=ImageChops.multiply(a,shifted)
        composite=Image.merge("RGBA",(ImageChops.lighter(red,both),
            both,ImageChops.lighter(blue,both),Image.new("L",a.size,255)))
        composite.save(OUT/(facing+"_registered_overlay.png"))
    (OUT/"registered_silhouette_diagnostics.json").write_text(
        json.dumps(result,indent=2)+"\n")
    print("MORWEN_06_REGISTERED_METRICS_PASS")
if __name__=="__main__":main()

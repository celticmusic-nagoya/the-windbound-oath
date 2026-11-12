"""Compare 4 candidate silhouettes with immutable reference PNGs.
Metrics are diagnostic only: source illustrations include clothing/hair.
"""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops

ROOT=Path(__file__).resolve().parents[3]
REF=ROOT/"assets/references/morwen/reference_20261112"
OUT=ROOT/"assets/candidates/morwen-blender-05"
SOURCES={"front":"REFERENCE_front.png","right":"REFERENCE_profile_facing_right.png",
         "back":"REFERENCE_back.png","left":"REFERENCE_profile_facing_left.png"}
def bbox_ratio(box):
    if not box: return None
    return [round((box[2]-box[0])/384,4),round((box[3]-box[1])/1024,4)]
def main():
    receipt=json.loads((ROOT/"tools/blender/morwen_blender_01/SOURCE_RECEIPT.json").read_text())
    pinned={e["path"]:e["sha256"] for e in receipt["files"]}
    report={"task":"MORWEN-BLENDER-05","status":"NUMERICAL_DIAGNOSTICS_ONLY",
            "visual_approval":"NOT_RUN","production_use":False,"facings":{}}
    for facing,name in SOURCES.items():
        refpath=REF/name
        assert hashlib.sha256(refpath.read_bytes()).hexdigest()==pinned[str(refpath.relative_to(ROOT))]
        with Image.open(refpath) as ref_im,Image.open(OUT/(facing+"_projection.png")) as render_im:
            ref=ref_im.convert("RGBA")
            render=render_im.convert("RGBA")
            assert ref.size==render.size==(384,1024)
            a=ref.getchannel("A").point(lambda v:255 if v>=128 else 0)
            b=render.getchannel("A").point(lambda v:255 if v>=128 else 0)
            aa=a.histogram()[255];bb=b.histogram()[255]
            intersection=ImageChops.multiply(a,b).histogram()[255]
            union=aa+bb-intersection
            report["facings"][facing]={"reference_sha256":pinned[str(refpath.relative_to(ROOT))],
                "reference_bbox":list(a.getbbox() or []),"render_bbox":list(b.getbbox() or []),
                "reference_bbox_fraction":bbox_ratio(a.getbbox()),
                "render_bbox_fraction":bbox_ratio(b.getbbox()),
                "silhouette_iou_unregistered":round(intersection/union,5) if union else None,
                "reference_foreground_px":aa,"candidate_foreground_px":bb}
    (OUT/"reference_silhouette_diagnostics.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MORWEN_05_REFERENCE_SHA_AND_SILHOUETTE_METRICS_PASS")
if __name__=="__main__":main()

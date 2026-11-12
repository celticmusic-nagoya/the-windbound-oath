"""BLENDER-21: extract review-only torso contour candidates from canonical alpha.

DO NOT use these unreviewed candidates as anatomical fitting targets.
"""
import json
from pathlib import Path
from importlib.util import spec_from_file_location,module_from_spec

ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/"tools/blender/morwen_blender_20/extract_reference_contours.py"
OUT=ROOT/"assets/candidates/morwen-blender-21"
spec=spec_from_file_location("canonical_contours",SRC)
mod=module_from_spec(spec);spec.loader.exec_module(mod)

def segments(row,threshold=128):
    spans=[];start=None
    for x,a in enumerate(row):
        if a>=threshold and start is None:start=x
        elif a<threshold and start is not None:
            spans.append((start,x-1));start=None
    if start is not None:spans.append((start,len(row)-1))
    return spans

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    a=json.loads((ROOT/"assets/candidates/morwen-blender-01/anchors_candidate.json").read_text())
    report={"task":"MORWEN-BLENDER-21","review_required":True,
            "anatomical_target":False,"art_approval":"NOT_RUN","views":{}}
    for name,sha in mod.EXPECTED.items():
        p=mod.REF/("REFERENCE_"+name+".png")
        import hashlib
        raw=p.read_bytes()
        assert hashlib.sha256(raw).hexdigest()==sha
        rows=mod.rgba_png_alpha(raw)
        facing={"front":"front","back":"back","profile_facing_left":"left","profile_facing_right":"right"}[name]
        points=a["facings"][facing]["rig_points_pixels"]
        center_x=points["chest"][0]
        y_chest=points["chest"][1]
        y_waist=points["waist"][1]
        y_pelvis=points["pelvis"][1]
        # Sample at anatomical joint heights, but do not infer anatomy from clothing.
        sample_ys=sorted(set([y_chest,y_waist,y_pelvis]+list(range(y_chest,y_pelvis+1,12))))
        samples=[]
        for y in sample_ys:
            if not (0<=y<len(rows)):continue
            ss=segments(rows[y])
            central=[s for s in ss if s[0]<=center_x<=s[1]]
            # Central alpha component may be a dress/corset/cape, not the body.
            chosen=central[0] if len(central)==1 else None
            samples.append({"y":y,"center_x":center_x,"segments":[list(s) for s in ss],
                "center_segment":list(chosen) if chosen else None,
                "ambiguous":len(central)!=1,
                "note":"clothing-inclusive; human review required"})
        report["views"][name]={"source_sha256":sha,"samples":samples}
    assert len(report["views"])==4
    (OUT/"torso_candidate_segments.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MORWEN_21_REVIEW_ONLY_TORSO_SEGMENTS_PASS")
if __name__=="__main__":main()

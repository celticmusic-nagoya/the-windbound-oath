#!/usr/bin/env python3
"""Calculate anatomy ratios only from reviewer-confirmed Blender-world landmarks."""
import argparse,json,math,pathlib
KEYS=("head_top","chin","shoulder","waist","hip","crotch","knee","ankle","sole")
def analyze(entry):
    pts=entry.get("landmarks",{})
    if any(k not in pts or pts[k] is None for k in KEYS):
        return {"status":"BLOCKED_UNCONFIRMED_LANDMARKS","missing":[k for k in KEYS if pts.get(k) is None]}
    if entry.get("reviewer_confirmed") is not True:
        return {"status":"BLOCKED_UNCONFIRMED_LANDMARKS","reason":"reviewer_confirmed must be true"}
    if not all(isinstance(pts[k],(int,float)) and math.isfinite(pts[k]) for k in KEYS):
        return {"status":"FAIL_INVALID_COORDINATES"}
    top,chin,sole=pts["head_top"],pts["chin"],pts["sole"]
    if not (top>chin>sole):
        return {"status":"FAIL_INVALID_HEAD_OR_HEIGHT"}
    height=top-sole;head=top-chin
    if not (head>0 and height>head):return {"status":"FAIL_INVALID_PROPORTIONS"}
    return {"status":"PASS_REVIEWER_LANDMARK_MEASUREMENT_ONLY","head_count":round(height/head,4),
            "head_height":round(head,5),"body_height":round(height,5),
            "leg_ratio_crotch_to_sole":round((pts["crotch"]-sole)/height,5),
            "landmarks_z":pts,"target_heads":[7.5,8.0],
            "target_head_height_for_current_body_7_75":round(height/7.75,5),
            "head_count_within_target":7.5<=height/head<=8.0}
def main():
    p=argparse.ArgumentParser();p.add_argument("input");p.add_argument("--output",required=True);a=p.parse_args()
    data=json.loads(pathlib.Path(a.input).read_text())
    result={"source":data.get("source"),"models":{k:analyze(v) for k,v in data["models"].items()},
            "canonical_match":"BLOCKED","art_qa":"NOT_RUN","production_approval":False}
    dest=pathlib.Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:v["status"] for k,v in result["models"].items()}))
if __name__=="__main__":main()

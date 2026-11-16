"""Compare baseline and redesigned EYELID-09 BVH reports without modifying meshes."""
import argparse,hashlib,json
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    for key in ("baseline","candidate","out"):
        p.add_argument("--"+key,required=True,type=Path)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Refuse overwrite")
    base_raw=a.baseline.read_bytes()
    new_raw=a.candidate.read_bytes()
    base=json.loads(base_raw)
    new=json.loads(new_raw)
    if base["status"]!="FAIL_SURFACE_INTERSECTIONS" or new["status"] not in ("FAIL_SURFACE_INTERSECTIONS","PASS_SURFACE_ONLY_LIMITED"):
        raise ValueError("Unexpected QA status")
    if base["source_model_sha256"]!=new["source_model_sha256"]:
        raise ValueError("Different model: cannot compare")
    sides={}
    for side in ("R","L"):
        old=base["intersection_counts"][side]
        current=new["intersection_counts"][side]
        if len(old["per_strip"])!=9 or len(current["per_strip"])!=9:raise ValueError("Expected 9 strips")
        per=[]
        for before,after in zip(old["per_strip"],current["per_strip"]):
            if before["name"]!=after["name"]:raise ValueError("Strip name mismatch")
            per.append({"name":before["name"],"baseline_pairs":before["cage_surface_triangle_pairs"],
                        "new_pairs":after["cage_surface_triangle_pairs"],
                        "delta":after["cage_surface_triangle_pairs"]-before["cage_surface_triangle_pairs"]})
        sides[side]={"baseline_pairs":old["cage"],"new_pairs":current["cage"],
                     "new_intersecting_strips":[x["name"] for x in per if x["new_pairs"]>0],
                     "per_strip":per}
    before=sum(sides[s]["baseline_pairs"] for s in sides)
    after=sum(sides[s]["new_pairs"] for s in sides)
    report={"status":"CANDIDATE_REDESIGN_COMPARISON_ONLY","baseline_pairs":before,
            "new_pairs":after,"reduction_fraction":round((before-after)/before,6),
            "sides":sides,"model_sha256":new["source_model_sha256"],
            "baseline_report_sha256":hashlib.sha256(base_raw).hexdigest(),
            "candidate_report_sha256":hashlib.sha256(new_raw).hexdigest(),
            "G1":"BLOCKED","G2":"NOT_RUN",
            "G3":"FAIL" if after>0 else "PARTIAL_SURFACE_ONLY",
            "G4":"NOT_RUN",
            "unverified":["contained geometry","swept eyelid motion","visual silhouette","canonical source images"]}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print("M09_SURFACE_FRAME_COMPARISON="+json.dumps({"before":before,"after":after,
         "new_intersecting_strips":{s:sides[s]["new_intersecting_strips"] for s in sides}},sort_keys=True),flush=True)

if __name__=="__main__":main()

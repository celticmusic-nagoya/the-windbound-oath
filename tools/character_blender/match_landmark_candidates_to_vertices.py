#!/usr/bin/env python3
"""Match unreviewed pixel-derived world-Z candidate marks to indexed source vertices.

Z alone cannot identify an anatomical surface point. Output is a review shortlist,
never an approved landmark measurement.
"""
import argparse,json,math,pathlib
ALLOWED_VIEWS={"front","back","left","right"}
def match(data,evidence,limit=12):
    if data.get("reviewer_confirmed") is True:
        raise ValueError("candidate input unexpectedly marked confirmed")
    if evidence.get("status")!="PASS_GEOMETRY_EVIDENCE_ONLY" or not evidence.get("source_unchanged"):
        raise ValueError("source geometry evidence not verified")
    result={"status":"CANDIDATE_VERTEX_SHORTLIST_ONLY","reviewer_confirmed":False,
            "anatomical_qa":"BLOCKED","source_sha256":evidence.get("source_sha256"),"matches":[]}
    for mark in data.get("marks",[]):
        name=mark.get("model");view=mark.get("view")
        z=mark.get("world_z_candidate")
        if name not in evidence["models"] or view not in ALLOWED_VIEWS:
            raise ValueError("unknown mesh/view")
        if not isinstance(z,(int,float)) or not math.isfinite(z):
            raise ValueError("invalid Z candidate")
        model=evidence["models"][name]
        lo,hi=model["bounds_world_xyz"]["min"][2],model["bounds_world_xyz"]["max"][2]
        if not lo-1e-4<=z<=hi+1e-4:raise ValueError("candidate outside mesh Z bounds")
        # Available evidence has nearest 12 source vertices at 13 Z bands,
        # not all vertices. Never claim these are globally nearest vertices.
        candidates={}
        for band in model["horizontal_sampling_bands_NOT_anatomical_landmarks"].values():
            for v in band["vertices"]:
                candidates[v["index"]]=v["world_xyz"]
        shortlist=sorted(({"index":idx,"world_xyz":xyz,"delta_z":round(abs(xyz[2]-z),6)}
                          for idx,xyz in candidates.items()),key=lambda v:(v["delta_z"],v["index"]))[:limit]
        result["matches"].append({"model":name,"view":view,"landmark_label_UNREVIEWED":mark.get("landmark"),
                                  "world_z_candidate":z,
                                  "search_scope":"13-band sparse vertex samples ONLY; no X/Y raycast",
                                  "vertex_shortlist_NOT_anatomical_matches":shortlist})
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument("--candidates",required=True)
    p.add_argument("--evidence",required=True);p.add_argument("--output",required=True);a=p.parse_args()
    result=match(json.loads(pathlib.Path(a.candidates).read_text()),
                 json.loads(pathlib.Path(a.evidence).read_text()))
    path=pathlib.Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(result["status"],len(result["matches"]))
if __name__=="__main__":main()

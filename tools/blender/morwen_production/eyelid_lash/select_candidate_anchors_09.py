"""Generate deterministic *candidate-only* lash anchors from real lid correspondence QA."""
import argparse,json,hashlib
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--match",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Refuse to overwrite evidence")
    raw=a.match.read_bytes()
    d=json.loads(raw)
    if d.get("status")!="CORRESPONDENCE_SURVEY_ONLY":raise ValueError("Unverified input status")
    result={"status":"UNAPPROVED_ANCHOR_CANDIDATES","source_match_sha256":hashlib.sha256(raw).hexdigest(),
            "root_count_per_side":9,"mesh_created":False,"art_qa":"NOT_RUN",
            "collision_qa":"NOT_RUN","canonical_approval":"BLOCKED","sides":{}}
    for side in ("R","L"):
        matches=d["sides"][side]["matches"]
        if len(matches)!=75:raise ValueError("Expected 75 matched margin points")
        indices=[round(i*(len(matches)-1)/8) for i in range(9)]
        roots=[]
        for i in indices:
            m=matches[i]
            if m["distance_m"]>1e-6:raise ValueError("Margin not on cage surface")
            roots.append({"margin_index":i,"triangle_vertices":m["nearest_triangle_vertices"],
                "root_world_m":m["nearest_world_m"],
                "normal_world":m["normal_world"],
                "approval":"CANDIDATE_ONLY"})
        result["sides"][side]=roots
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print("EYELID09_ANCHORS="+json.dumps({"status":result["status"],"counts":{k:len(v) for k,v in result["sides"].items()}},sort_keys=True))
if __name__=="__main__":main()

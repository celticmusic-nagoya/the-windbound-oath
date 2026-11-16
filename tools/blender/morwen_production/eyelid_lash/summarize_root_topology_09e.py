"""Summarize existing 09E JSON without generating or modifying geometry."""
import argparse,json,statistics
from pathlib import Path

def summarize(side):
    sections=side["root_cross_sections"]
    points=[p for sec in sections for p in sec["points"]]
    edges=side["edge_samples"]
    pairs=side["pairs"]
    def sign(v):
        return "negative" if v < -1e-8 else "positive" if v > 1e-8 else "zero"
    return {"pairs":len(pairs),
        "pair_details":[{"lash_face":p["lash_face"],"lash_triangle":p["lash_triangle"],
                         "cage_triangle":p["cage_triangle"],
                         "cage_winding_normal":p["cage_winding_normal"]} for p in pairs],
        "root_sections":[{"section":sec["section"],
            "signed_distances_m":[p["signed_winding_distance_m"] for p in sec["points"]],
            "nearest_cage_triangles":[p["nearest_triangle"] for p in sec["points"]]}
            for sec in sections[:4]],
        "negative_vertex_count":sum(p["signed_winding_distance_m"] < -1e-8 for p in points),
        "negative_edge_sample_count":sum(p["signed_winding_distance_m"] < -1e-8 for p in edges),
        "min_abs_vertex_distance_m":min(p["distance_m"] for p in points),
        "min_abs_edge_sample_distance_m":min(p["distance_m"] for p in edges),
        "edge_negative_samples":[{"segment":p["segment"],"side":p["side"],"t":p["t"],
            "signed_distance_m":p["signed_winding_distance_m"],
            "nearest_cage_triangle":p["nearest_triangle"]}
            for p in edges if p["signed_winding_distance_m"] < -1e-8],
        "winding_warning":"Nearest local winding sign is not a closed-mesh inside/outside test."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Refuse overwrite")
    data=json.loads(a.input.read_text())
    if data.get("status")!="READ_ONLY_TOPOLOGY_EVIDENCE":raise ValueError("Unexpected evidence")
    report={"status":"DIAGNOSIS_ONLY_NO_GEOMETRY",
        "09b":summarize(data["before_09b"]),
        "09d":summarize(data["after_09d"]),
        "G1":"BLOCKED","G2":"NOT_RUN","G3":"FAIL","G4":"NOT_RUN"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print("M09_TOPOLOGY_SUMMARY_09E="+json.dumps(report,sort_keys=True),flush=True)

if __name__=="__main__":main()

"""Read-only evidence classification for the EYELID-09 lash/cage collision failure.

Do not adjust geometry blindly. Classify which candidate roots/strips contribute
to the failed BVH gate, and preserve input hashes for reproducibility.
"""
import argparse
import hashlib
import json
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--intersections",type=Path,required=True)
    p.add_argument("--anchors",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():
        raise ValueError("Refuse overwrite")
    raw=a.intersections.read_bytes()
    data=json.loads(raw)
    anchor_raw=a.anchors.read_bytes()
    anchors=json.loads(anchor_raw)
    if data["status"]!="FAIL_SURFACE_INTERSECTIONS":
        raise ValueError("Expected current failing candidate; never misclassify")
    if anchors["status"]!="UNAPPROVED_ANCHOR_CANDIDATES":
        raise ValueError("Unapproved roots required")
    sides={}
    total=0
    for side in ("R","L"):
        strips=data["intersection_counts"][side]["per_strip"]
        roots=anchors["sides"][side]
        if len(strips)!=9 or len(roots)!=9:
            raise ValueError("Unexpected strip/root cardinality")
        items=[]
        for index,(strip,root) in enumerate(zip(strips,roots)):
            expected=f"M09_{side}_LASH_CANDIDATE_{index:02d}"
            if strip["name"]!=expected:
                raise ValueError("Strip order mismatch: "+expected)
            count=strip["cage_surface_triangle_pairs"]
            eye=strip["eye_surface_triangle_pairs"]
            if count<0 or eye<0:
                raise ValueError("Invalid collision count")
            total+=count+eye
            items.append({"strip":expected,"margin_index":root["margin_index"],
                          "cage_pairs":count,"eye_pairs":eye,
                          "classification":"INTERSECTING" if count or eye else "NO_SURFACE_OVERLAP_DETECTED"})
        sides[side]={"intersecting_strip_count":sum(x["classification"]=="INTERSECTING" for x in items),
                     "cage_pairs":sum(x["cage_pairs"] for x in items),
                     "eye_pairs":sum(x["eye_pairs"] for x in items),
                     "strips":items}
    if total!=sum(data["intersection_counts"][s][k] for s in ("R","L") for k in ("cage","eyes")):
        raise ValueError("Summary mismatch")
    report={"status":"DIAGNOSIS_ONLY_NO_GEOMETRY_CHANGED",
            "input_intersections_sha256":hashlib.sha256(raw).hexdigest(),
            "input_anchors_sha256":hashlib.sha256(anchor_raw).hexdigest(),
            "total_surface_triangle_pairs":total,"sides":sides,
            "next_design":"Use lid-margin tangent and outward surface normal to define a local lash frame; validate normal orientation and clearance by sampling swept strip geometry before any canonical adoption.",
            "known_limitations":["BVH triangle overlap is not containment testing",
                                 "No eyelid-motion swept collision test",
                                 "No image/art approval","No canonical v5.61 binary match"],
            "G1":"BLOCKED","G2":"NOT_RUN","G3":"FAIL","G4":"NOT_RUN"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print("M09_COLLISION_DIAGNOSIS="+json.dumps({"status":report["status"],"total_pairs":total,
          "counts":{s:{"strips":sides[s]["intersecting_strip_count"],"pairs":sides[s]["cage_pairs"]} for s in ("R","L")}},sort_keys=True),flush=True)

if __name__=="__main__":
    main()

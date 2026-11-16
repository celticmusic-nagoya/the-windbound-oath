"""EYELID-09 compare authored upper half-margin to nearest cage triangle, read-only."""
import argparse,hashlib,json
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

EXPECTED="9bff525ea293886f0aafdc79509f57d761d4a22a5f52e2700decae05c84ea9c4"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidate",type=Path,required=True)
    p.add_argument("--design",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Evidence output exists")
    if hashlib.sha256(a.candidate.read_bytes()).hexdigest()!=EXPECTED:
        raise ValueError("Unexpected candidate SHA")
    design=json.loads(a.design.read_text())
    if design["source_sha256"]!="a30b05af5369864578aea85b72f6c8e5100630d2ceb638c8a9a52add6e5defd7":
        raise ValueError("Unexpected design source SHA")
    bpy.ops.wm.open_mainfile(filepath=str(a.candidate.resolve()))
    report={"status":"CORRESPONDENCE_SURVEY_ONLY","canonical_anchor_approval":"BLOCKED",
            "actual_lash_generation":"NOT_RUN","collision_qa":"NOT_RUN","sides":{}}
    for side in ("R","L"):
        ob=bpy.data.objects[f"M08_{side}_CONTACT_CAGE_050"]
        me=ob.data
        me.calc_loop_triangles()
        coords=[ob.matrix_world@v.co for v in me.vertices]
        triangles=[tuple(t.vertices) for t in me.loop_triangles]
        bvh=BVHTree.FromPolygons(coords,triangles,all_triangles=True)
        margin=design["sides"][side]["half_margin_upper"]
        rows=[]
        for idx,point in enumerate(margin):
            nearest,normal,tri_index,dist=bvh.find_nearest(Vector(point))
            if tri_index is None:raise ValueError("No triangle found")
            tri=triangles[tri_index]
            # Explicitly record the nearest point on surface, not the unverified anatomical lash root.
            rows.append({"margin_index":idx,"margin_world_m":point,
                "nearest_triangle_vertices":list(tri),
                "nearest_world_m":list(nearest),"distance_m":dist,
                "normal_world":list(normal)})
        report["sides"][side]={"margin_count":len(margin),"max_nearest_distance_m":max(x["distance_m"] for x in rows),
            "mean_nearest_distance_m":sum(x["distance_m"] for x in rows)/len(rows),
            "matches":rows,"warning":"Nearest cage triangle does not prove anatomically correct lash-root position"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print("EYELID09_CORRESPONDENCE="+json.dumps({"status":report["status"],"sides":{
        side:{"count":x["margin_count"],"max_distance_m":x["max_nearest_distance_m"]}
        for side,x in report["sides"].items()}},sort_keys=True))
if __name__=="__main__":main()

"""EYELID-09 surface intersection QA for isolated candidate strips vs saved model.

BVH triangle overlap detects surface intersections, not fully contained geometry,
alpha card occlusion, or swept intersections through eyelid motion.
"""
import argparse,json,hashlib
from pathlib import Path
import bpy
from mathutils.bvhtree import BVHTree

CANDIDATE_SHA="9bff525ea293886f0aafdc79509f57d761d4a22a5f52e2700decae05c84ea9c4"

def world_bvh(obj):
    mesh=obj.to_mesh()
    try:
        mesh.calc_loop_triangles()
        pts=[obj.matrix_world@v.co for v in mesh.vertices]
        tris=[tuple(t.vertices) for t in mesh.loop_triangles]
        if not tris:raise ValueError("No triangles: "+obj.name)
        return BVHTree.FromPolygons(pts,tris,all_triangles=True)
    finally:obj.to_mesh_clear()

def main():
    p=argparse.ArgumentParser()
    for k in ("model","strips","out"):p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Refuse overwrite")
    if hashlib.sha256(a.model.read_bytes()).hexdigest()!=CANDIDATE_SHA:raise ValueError("Wrong model")
    bpy.ops.wm.open_mainfile(filepath=str(a.model.resolve()))
    with bpy.data.libraries.load(str(a.strips.resolve()),link=False) as (src,dst):
        dst.objects=[n for n in src.objects if n.startswith("M09_") and "_LASH_CANDIDATE_" in n]
    if len(dst.objects)!=18:raise ValueError("Expected 18 strips")
    obstacles={n:world_bvh(bpy.data.objects[n]) for n in
        ("M08_R_CONTACT_CAGE_050","M08_L_CONTACT_CAGE_050","MORWEN_Eyes")}
    result={"status":"SURFACE_INTERSECTION_QA_ONLY","source_model_sha256":CANDIDATE_SHA,
        "strip_file_sha256":hashlib.sha256(a.strips.read_bytes()).hexdigest(),
        "intersection_counts":{},"art_qa":"NOT_RUN","alpha_occlusion":"NOT_RUN",
        "swept_motion_collision":"NOT_RUN","contained_geometry":"NOT_RUN",
        "canonical_approval":"BLOCKED"}
    for side in ("R","L"):
        cage=obstacles[f"M08_{side}_CONTACT_CAGE_050"]
        counts={"cage":0,"eyes":0,"per_strip":[]}
        for j in range(9):
            name=f"M09_{side}_LASH_CANDIDATE_{j:02d}"
            ob=bpy.data.objects.get(name)
            if ob is None:
                ob=next((x for x in dst.objects if x and x.name==name),None)
            if ob is None:raise ValueError("Missing strip "+name)
            lash=world_bvh(ob)
            c=len(lash.overlap(cage));e=len(lash.overlap(obstacles["MORWEN_Eyes"]))
            counts["cage"]+=c;counts["eyes"]+=e
            counts["per_strip"].append({"name":name,"cage_surface_triangle_pairs":c,"eye_surface_triangle_pairs":e})
        result["intersection_counts"][side]=counts
    result["status"]="FAIL_SURFACE_INTERSECTIONS" if any(
        result["intersection_counts"][s][k]>0 for s in ("R","L") for k in ("cage","eyes")
    ) else "PASS_SURFACE_ONLY_LIMITED"
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print("EYELID09_SURFACE_QA="+json.dumps({"status":result["status"],
        "counts":{s:{k:v for k,v in result["intersection_counts"][s].items() if k!="per_strip"}
        for s in ("R","L")}},sort_keys=True))
    # A geometric failure is evidence, not an infrastructure error; retain artifact.
if __name__=="__main__":main()

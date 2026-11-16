"""09Q read-only root collision localization for the rejected 09P candidate.

Report actual intersecting triangle indices, world-space vertices and root
distance. No geometry edits, no claims about visual quality.
"""
import argparse,hashlib,json
from pathlib import Path
import bpy
from mathutils.bvhtree import BVHTree

MODEL_SHA="9bff525ea293886f0aafdc79509f57d761d4a22a5f52e2700decae05c84ea9c4"
LASH="M09_L_LASH_CANDIDATE_00"
CAGE="M08_L_CONTACT_CAGE_050"

def triangles(ob):
    m=ob.to_mesh()
    try:
        m.calc_loop_triangles()
        points=[ob.matrix_world@v.co for v in m.vertices]
        faces=[tuple(t.vertices) for t in m.loop_triangles]
        return points,faces
    finally:ob.to_mesh_clear()

def main():
    p=argparse.ArgumentParser()
    for k in ("model","strips","out"):p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Refuse overwrite")
    if hashlib.sha256(a.model.read_bytes()).hexdigest()!=MODEL_SHA:raise ValueError("Unexpected model SHA")
    bpy.ops.wm.open_mainfile(filepath=str(a.model.resolve()))
    with bpy.data.libraries.load(str(a.strips.resolve()),link=False) as (src,dst):
        dst.objects=[LASH]
    lash=dst.objects[0]
    if lash is None:raise ValueError("Missing 09P left root")
    if not lash.users_collection:bpy.context.collection.objects.link(lash)
    cage=bpy.data.objects[CAGE]
    lv,lf=triangles(lash)
    cv,cf=triangles(cage)
    lb=BVHTree.FromPolygons(lv,lf,all_triangles=True)
    cb=BVHTree.FromPolygons(cv,cf,all_triangles=True)
    pairs=sorted(lb.overlap(cb))
    root=lv[0]
    details=[]
    for li,ci in pairs:
        ls=lf[li];cs=cf[ci]
        centroid=sum((lv[i] for i in ls),root*0)/3
        details.append({"lash_triangle":li,"lash_vertex_ids":list(ls),
            "cage_triangle":ci,"cage_vertex_ids":list(cs),
            "lash_world_vertices_m":[list(lv[i]) for i in ls],
            "cage_world_vertices_m":[list(cv[i]) for i in cs],
            "lash_centroid_distance_from_root_m":(centroid-root).length})
    report={"status":"REJECTED_09P_COLLISION_LOCALIZATION",
      "model_sha256":MODEL_SHA,
      "strips_sha256":hashlib.sha256(a.strips.read_bytes()).hexdigest(),
      "root_world_m":list(root),"collision_triangle_pairs":len(pairs),
      "affected_lash_triangle_ids":sorted(set(d["lash_triangle"] for d in details)),
      "pairs":details,"G1":"BLOCKED","G2":"FAIL_PREVIOUS_REVIEW",
      "G3":"FAIL" if pairs else "PARTIAL_PASS","G4":"NOT_RUN"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print("M09_COLLISION_LOCALIZATION_09Q="+json.dumps({
        "pairs":len(pairs),"affected_lash_triangles":report["affected_lash_triangle_ids"]}),flush=True)
if __name__=="__main__":main()

"""09E read-only evidence: cage winding, signed-side heuristics, and ribbon clearance.

No geometry edits. Nearest signed distance is local-normal signed only; not a
watertight inside/outside verdict. Reports actual intersection face pairs.
"""
import argparse,hashlib,json,math
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
SHA="9bff525ea293886f0aafdc79509f57d761d4a22a5f52e2700decae05c84ea9c4"

def surface(ob):
    mesh=ob.to_mesh()
    try:
        mesh.calc_loop_triangles()
        vs=[ob.matrix_world@v.co for v in mesh.vertices]
        tris=[tuple(t.vertices) for t in mesh.loop_triangles]
        return vs,tris,BVHTree.FromPolygons(vs,tris,all_triangles=True)
    finally:ob.to_mesh_clear()

def v3(v):return [round(float(x),9) for x in v]

def inspect(model,strip_path):
    bpy.ops.wm.open_mainfile(filepath=str(model.resolve()))
    cage=bpy.data.objects["M08_L_CONTACT_CAGE_050"]
    cv,ct,cb=surface(cage)
    with bpy.data.libraries.load(str(strip_path.resolve()),link=False) as (src,dst):
        dst.objects=["M09_L_LASH_CANDIDATE_00"]
    lash=dst.objects[0]
    if lash is None:raise ValueError("Missing L00")
    lv,lt,lb=surface(lash)
    pairs=sorted(lb.overlap(cb))
    report={"strip_sha256":hashlib.sha256(strip_path.read_bytes()).hexdigest(),
            "pairs":[],"root_cross_sections":[],"mesh_signed_distance_not_containment":True}
    # Cage winding from actual vertex order, independent of nearest BVH normal.
    for li,ci in pairs:
        ids=ct[ci];a,b,c=(cv[i] for i in ids)
        n=(b-a).cross(c-a)
        n.normalize()
        report["pairs"].append({"lash_triangle":li,"lash_face":li//2,
            "cage_triangle":ci,"cage_winding_normal":v3(n),
            "lash_vertices":list(lt[li]),"cage_vertices":list(ids)})
    for k in range(6):
        section=[]
        for index in (2*k,2*k+1):
            point=lv[index]
            nearest,n,tri,d=cb.find_nearest(point)
            if nearest is None:raise ValueError("Nearest cage query failed")
            ids=ct[tri];a,b,c=(cv[i] for i in ids)
            winding=(b-a).cross(c-a).normalized()
            section.append({"vertex":index,"nearest_triangle":tri,
                "distance_m":round(d,9),"signed_winding_distance_m":
                round((point-nearest).dot(winding),9),
                "winding_normal":v3(winding),"nearest_world_m":v3(nearest),
                "vertex_world_m":v3(point)})
        report["root_cross_sections"].append({"section":k,"points":section})
    # Midpoint sampling along every ribbon triangle edge to catch obvious
    # inter-vertex clearance dips; not an exhaustive continuous proof.
    sampled=[]
    for k in range(5):
        for u in (0.25,0.5,0.75):
            for side in (0,1):
                a=lv[2*k+side];b=lv[2*(k+1)+side]
                point=a.lerp(b,u)
                hit,n,tri,d=cb.find_nearest(point)
                ids=ct[tri];x,y,z=(cv[i] for i in ids)
                winding=(y-x).cross(z-x).normalized()
                sampled.append({"segment":k,"side":side,"t":u,
                    "distance_m":round(d,9),
                    "signed_winding_distance_m":round((point-hit).dot(winding),9),
                    "nearest_triangle":tri})
    report["edge_samples"]=sampled
    report["pair_count"]=len(pairs)
    return report

def main():
    p=argparse.ArgumentParser()
    for name in ("model","before","after","out"):p.add_argument("--"+name,required=True,type=Path)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Refuse overwrite")
    if hashlib.sha256(a.model.read_bytes()).hexdigest()!=SHA:raise ValueError("Wrong canonical-candidate cage")
    before=inspect(a.model,a.before)
    after=inspect(a.model,a.after)
    result={"status":"READ_ONLY_TOPOLOGY_EVIDENCE","model_sha256":SHA,
            "before_09b":before,"after_09d":after,
            "caution":"Signed nearest-winding distance is NOT a watertight containment proof; edge samples are NOT exhaustive swept clearance.",
            "G1":"BLOCKED","G2":"NOT_RUN","G3":"FAIL","G4":"NOT_RUN"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print("M09_TOPOLOGY_09E="+json.dumps({
        "09b_pairs":before["pair_count"],"09d_pairs":after["pair_count"],
        "09b_lash_faces":sorted(set(x["lash_face"] for x in before["pairs"])),
        "09d_lash_faces":sorted(set(x["lash_face"] for x in after["pairs"])),
        "09d_cage_triangles":sorted(set(x["cage_triangle"] for x in after["pairs"]))},
        sort_keys=True),flush=True)

if __name__=="__main__":main()

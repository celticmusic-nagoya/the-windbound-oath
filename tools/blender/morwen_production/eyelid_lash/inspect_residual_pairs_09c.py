"""Read-only exact BVH triangle-pair inspection of residual 09B intersections."""
import argparse,hashlib,json
from pathlib import Path
import bpy
from mathutils.bvhtree import BVHTree

MODEL_SHA="9bff525ea293886f0aafdc79509f57d761d4a22a5f52e2700decae05c84ea9c4"

def mesh_data(obj):
    mesh=obj.to_mesh()
    try:
        mesh.calc_loop_triangles()
        vertices=[tuple(obj.matrix_world@v.co) for v in mesh.vertices]
        triangles=[tuple(t.vertices) for t in mesh.loop_triangles]
        return vertices,triangles,BVHTree.FromPolygons(vertices,triangles,all_triangles=True)
    finally:
        obj.to_mesh_clear()

def main():
    p=argparse.ArgumentParser()
    for key in ("model","strips","out"):p.add_argument("--"+key,required=True,type=Path)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Refuse overwrite")
    if hashlib.sha256(a.model.read_bytes()).hexdigest()!=MODEL_SHA:raise ValueError("Wrong contact-cage input")
    bpy.ops.wm.open_mainfile(filepath=str(a.model.resolve()))
    with bpy.data.libraries.load(str(a.strips.resolve()),link=False) as (src,dst):
        dst.objects=["M09_L_LASH_CANDIDATE_00"]
    lash=dst.objects[0]
    if lash is None:raise ValueError("Missing left endpoint strip")
    cage=bpy.data.objects["M08_L_CONTACT_CAGE_050"]
    lv,lt,lb=mesh_data(lash)
    cv,ct,cb=mesh_data(cage)
    overlaps=sorted(lb.overlap(cb))
    details=[]
    for ltri,ctri in overlaps:
        if ltri<0 or ltri>=len(lt) or ctri<0 or ctri>=len(ct):
            raise ValueError("Out of range BVH triangle index")
        details.append({"lash_triangle_index":ltri,"lash_face_index":ltri//2,
                        "lash_vertex_indices":list(lt[ltri]),
                        "lash_triangle_world_m":[list(lv[v]) for v in lt[ltri]],
                        "cage_triangle_index":ctri,
                        "cage_vertex_indices":list(ct[ctri]),
                        "cage_triangle_world_m":[list(cv[v]) for v in ct[ctri]]})
    report={"status":"READ_ONLY_RESIDUAL_PAIR_INSPECTION","source_model_sha256":MODEL_SHA,
            "strips_sha256":hashlib.sha256(a.strips.read_bytes()).hexdigest(),
            "overlap_pair_count":len(details),"pairs":details,
            "G1":"BLOCKED","G2":"NOT_RUN","G3":"FAIL" if details else "PARTIAL_SURFACE_ONLY",
            "G4":"NOT_RUN","contained_geometry":"NOT_RUN","swept_motion":"NOT_RUN"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print("M09_RESIDUAL_PAIRS="+json.dumps({"pairs":len(details),
         "lash_faces":sorted(set(d["lash_face_index"] for d in details)),
         "cage_triangles":sorted(set(d["cage_triangle_index"] for d in details))},sort_keys=True),flush=True)

if __name__=="__main__":main()

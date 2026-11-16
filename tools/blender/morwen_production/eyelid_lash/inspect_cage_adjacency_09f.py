"""09F read-only triangle adjacency and winding audit; no mesh modifications."""
import argparse,hashlib,json
from collections import defaultdict
from pathlib import Path
import bpy
from mathutils import Vector
SOURCE_SHA="9bff525ea293886f0aafdc79509f57d761d4a22a5f52e2700decae05c84ea9c4"
TARGETS={938,940,941,946,950}

def vec(v):return [round(float(x),9) for x in v]
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Refuse overwrite")
    if hashlib.sha256(a.model.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError("Source mismatch")
    bpy.ops.wm.open_mainfile(filepath=str(a.model.resolve()))
    ob=bpy.data.objects["M08_L_CONTACT_CAGE_050"]
    mesh=ob.to_mesh()
    try:
        mesh.calc_loop_triangles()
        verts=[ob.matrix_world@v.co for v in mesh.vertices]
        triangles=[tuple(t.vertices) for t in mesh.loop_triangles]
        edges=defaultdict(list)
        for i,tri in enumerate(triangles):
            for j in range(3):
                x,y=tri[j],tri[(j+1)%3]
                edges[tuple(sorted((x,y)))].append({"triangle":i,"directed":[x,y]})
        selected=set(TARGETS)
        for edge,incidents in edges.items():
            if any(x["triangle"] in TARGETS for x in incidents):
                selected.update(x["triangle"] for x in incidents)
        items=[]
        for i in sorted(selected):
            ids=triangles[i]
            a0,b0,c0=[verts[j] for j in ids]
            n=(b0-a0).cross(c0-a0)
            area=n.length/2
            if n.length:n.normalize()
            neighbors=[]
            for j in range(3):
                x,y=ids[j],ids[(j+1)%3]
                incidents=edges[tuple(sorted((x,y)))]
                neighbors.append({"edge":[x,y],
                    "incident_triangles":[q["triangle"] for q in incidents],
                    "same_direction_incidents":[q["triangle"] for q in incidents
                        if q["triangle"]!=i and q["directed"]==[x,y]]})
            items.append({"triangle":i,"vertex_ids":list(ids),
                "world_vertices_m":[vec(verts[j]) for j in ids],
                "winding_normal":vec(n),"area_m2":area,"edges":neighbors})
        nonmanifold=[{"edge":list(edge),"incidents":[x["triangle"] for x in incidents]}
            for edge,incidents in edges.items() if len(incidents)>2]
        boundaries=[list(edge) for edge,incidents in edges.items() if len(incidents)==1]
        inconsistent=[{"edge":list(edge),"triangles":[x["triangle"] for x in incidents]}
            for edge,incidents in edges.items() if len(incidents)==2 and
                incidents[0]["directed"]==incidents[1]["directed"]]
        result={"status":"READ_ONLY_TOPOLOGY_AUDIT","model_sha256":SOURCE_SHA,
            "target_triangles":sorted(TARGETS),"selected_triangle_count":len(items),
            "triangles":items,"total_triangles":len(triangles),
            "boundary_edge_count":len(boundaries),"boundary_edges":boundaries[:100],
            "nonmanifold_edge_count":len(nonmanifold),"nonmanifold_edges":nonmanifold[:100],
            "inconsistent_winding_edge_count":len(inconsistent),
            "inconsistent_winding_edges":inconsistent[:100],
            "watertight_by_edge_incidence":not boundaries and not nonmanifold,
            "warning":"Watertight edge incidence does not alone establish reliable containment or outward orientation.",
            "G1":"BLOCKED","G2":"NOT_RUN","G3":"FAIL","G4":"NOT_RUN"}
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(result,indent=2)+"\n")
        print("M09_ADJACENCY_09F="+json.dumps({k:result[k] for k in (
            "selected_triangle_count","total_triangles","boundary_edge_count",
            "nonmanifold_edge_count","inconsistent_winding_edge_count",
            "watertight_by_edge_incidence")},sort_keys=True),flush=True)
    finally:ob.to_mesh_clear()
if __name__=="__main__":main()

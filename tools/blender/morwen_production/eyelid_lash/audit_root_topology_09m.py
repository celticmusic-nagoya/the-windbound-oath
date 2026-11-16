"""09M geometry audit: evaluate root-fan triangulation, face winding and silhouette risks.

Read-only candidate inspection. No canonical changes and no automatic art PASS.
Measures triangle quality and root-to-distal normal discontinuity in world space.
"""
import argparse,hashlib,json,math
from pathlib import Path
import bpy
from mathutils import Vector

def triangle_metrics(a,b,c):
    ab=(b-a).length;bc=(c-b).length;ca=(a-c).length
    area=(b-a).cross(c-a).length/2
    longest=max(ab,bc,ca)
    quality=4*math.sqrt(3)*area/max(ab*ab+bc*bc+ca*ca,1e-20)
    normal=(b-a).cross(c-a)
    if normal.length>1e-12:normal.normalize()
    return {"area_m2":area,"longest_edge_m":longest,"quality_0_to_1":quality,"normal":normal}

def main():
    p=argparse.ArgumentParser()
    for k in ("strips","out"):p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Refuse overwrite")
    bpy.ops.wm.open_mainfile(filepath=str(a.strips.resolve()))
    ob=bpy.data.objects["M09_L_LASH_CANDIDATE_00"]
    if len(ob.data.vertices)!=9 or len(ob.data.polygons)!=4:raise ValueError("09G topology mismatch")
    v=[ob.matrix_world@x.co for x in ob.data.vertices]
    triangles=[]
    for i,p in enumerate(ob.data.polygons):
        indices=list(p.vertices)
        if len(indices)==3:groups=[indices]
        elif len(indices)==4:groups=[[indices[0],indices[1],indices[2]],[indices[0],indices[2],indices[3]]]
        else:raise ValueError("Unexpected polygon")
        for ids in groups:
            m=triangle_metrics(*(v[j] for j in ids))
            triangles.append({"face":i,"indices":ids,"area_m2":m["area_m2"],"longest_edge_m":m["longest_edge_m"],"quality_0_to_1":m["quality_0_to_1"],"normal":list(m["normal"])})
    root=Vector(triangles[0]["normal"])
    distal=Vector(triangles[1]["normal"])
    angle=math.degrees(root.angle(distal)) if root.length and distal.length else None
    report={"status":"MEASURED_CANDIDATE_ONLY","strips_sha256":hashlib.sha256(a.strips.read_bytes()).hexdigest(),
       "root_face_vertex_indices":list(ob.data.polygons[0].vertices),
       "root_triangle_quality":triangles[0]["quality_0_to_1"],
       "root_to_next_triangle_dihedral_deg":angle,
       "triangles":triangles,
       "recommendation":"Assess triangle aspect, normals, contact seam and 48px silhouette before topology edits",
       "G1":"BLOCKED","G2":"NOT_RUN","G3":"DIAGNOSTIC_ONLY","G4":"NOT_RUN"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print("M09_TOPOLOGY_AUDIT_09M="+json.dumps({k:report[k] for k in ("status","root_triangle_quality","root_to_next_triangle_dihedral_deg")}),flush=True)
if __name__=="__main__":main()

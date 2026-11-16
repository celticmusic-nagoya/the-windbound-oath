"""Read-only topology/weights/UV/material audit of frozen candidate Blender model.
No bpy save calls. All findings are candidate-only; not artistic or canonical approval.
"""
import argparse,hashlib,json,math
from pathlib import Path
import bpy
from mathutils import Vector

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--expected-sha256",required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Refusing to overwrite report")
    actual=hashlib.sha256(a.input.read_bytes()).hexdigest()
    if actual!=a.expected_sha256:raise ValueError("Input hash mismatch")
    bpy.ops.wm.open_mainfile(filepath=str(a.input.resolve()))
    report={"schema":"TWO_CHARACTER_SURFACE_AUDIT_V1","status":"CANDIDATE_DIAGNOSTIC_ONLY",
            "source_sha256":actual,"blender_version":bpy.app.version_string,
            "objects":{},"G1":"BLOCKED","G2":"NOT_RUN","G3":"PARTIAL_MEASUREMENT_ONLY","G4":"NOT_RUN"}
    for name in ("Body","Face"):
        obj=bpy.data.objects.get(name)
        if not obj or obj.type!="MESH":raise ValueError("Missing mesh "+name)
        mesh=obj.data
        bound=[m.object.name for m in obj.modifiers if m.type=="ARMATURE" and m.object]
        rig=bpy.data.objects.get("Armature")
        valid_bones={b.name for b in rig.data.bones} if rig and rig.type=="ARMATURE" else set()
        group_names={g.index:g.name for g in obj.vertex_groups}
        unweighted=0; zero_total=0; unknown_groups=set(); multi_over4=0
        for v in mesh.vertices:
            active=[(group_names.get(g.group,"UNKNOWN"),float(g.weight)) for g in v.groups if g.weight>1e-7]
            if not active:unweighted+=1
            if sum(w for _,w in active)<1e-7:zero_total+=1
            if len(active)>4:multi_over4+=1
            unknown_groups.update(n for n,w in active if n not in valid_bones)
        edges={}
        for poly in mesh.polygons:
            for key in poly.edge_keys:edges[key]=edges.get(key,0)+1
        boundary=sum(1 for count in edges.values() if count==1)
        nonmanifold=sum(1 for count in edges.values() if count>2)
        materials=[]
        for slot in obj.material_slots:
            m=slot.material
            materials.append({"name":m.name if m else None,"uses_nodes":bool(m and m.use_nodes),
                "node_count":len(m.node_tree.nodes) if m and m.use_nodes and m.node_tree else 0})
        report["objects"][name]={"vertex_count":len(mesh.vertices),"polygon_count":len(mesh.polygons),
            "uv_layers":[{"name":u.name,"active":u.active} for u in mesh.uv_layers],
            "materials":materials,"bound_armatures":bound,
            "unweighted_vertices":unweighted,"vertices_over_4_influences":multi_over4,
            "unknown_weight_group_names":sorted(unknown_groups),
            "boundary_edges":boundary,"nonmanifold_edges":nonmanifold,
            "boundary_edges_not_necessarily_defects":True,
            "world_bbox_min":[round(min((obj.matrix_world@v.co)[i] for v in mesh.vertices),8) for i in range(3)],
            "world_bbox_max":[round(max((obj.matrix_world@v.co)[i] for v in mesh.vertices),8) for i in range(3)]}
    report["neck_skin_seam"]="NOT_VERIFIED: mesh boundary classification and matching vertex coordinates require approved anatomical seam labels"
    report["camera_axis_handedness"]="BLOCKED: contradictory source metadata and no verified image-to-rig registration"
    report["head_ratio"]="NOT_VERIFIED: face mesh bbox is not an anatomical head measurement"
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SURFACE_AUDIT="+json.dumps({name:{k:v for k,v in item.items() if k in ("unweighted_vertices","boundary_edges","nonmanifold_edges","vertices_over_4_influences")} for name,item in report["objects"].items()}),flush=True)
if __name__=="__main__":main()

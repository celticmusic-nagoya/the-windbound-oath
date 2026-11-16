"""Read-only Blender object/armature/material/interface inventory.

Run on an existing candidate .blend; never saves the blend or changes accepted files.
Output is diagnostic, not a canonical coordinate contract.
"""
import argparse,hashlib,json
from pathlib import Path
import bpy

def vec(v):return [round(float(x),8) for x in v]
def matrix(m):return [vec(row) for row in m]
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--expected-sha256",required=True)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Refuse to overwrite report")
    raw=a.input.read_bytes()
    sha=hashlib.sha256(raw).hexdigest()
    if sha!=a.expected_sha256:raise ValueError("Source SHA mismatch")
    bpy.ops.wm.open_mainfile(filepath=str(a.input.resolve()))
    objects=[]
    for ob in sorted(bpy.data.objects,key=lambda x:x.name):
        item={"name":ob.name,"type":ob.type,"parent":ob.parent.name if ob.parent else None,
            "matrix_world":matrix(ob.matrix_world),"location":vec(ob.location),
            "rotation_mode":ob.rotation_mode,"scale":vec(ob.scale)}
        if ob.type=="MESH":
            mesh=ob.data
            item.update({"vertices":len(mesh.vertices),"polygons":len(mesh.polygons),
                "uv_layers":[uv.name for uv in mesh.uv_layers],
                "material_slots":[{"name":s.name,"blend_method":getattr(s.material,"surface_render_method",None) if s.material else None} for s in ob.material_slots],
                "bound_armature_modifiers":[m.object.name if m.object else None for m in ob.modifiers if m.type=="ARMATURE"],
                "vertex_groups":[g.name for g in ob.vertex_groups]})
            if mesh.vertices:
                coords=[ob.matrix_world@v.co for v in mesh.vertices]
                item["world_bbox_min"]=vec([min(p[i] for p in coords) for i in range(3)])
                item["world_bbox_max"]=vec([max(p[i] for p in coords) for i in range(3)])
        if ob.type=="ARMATURE":
            item["bones"]=[{"name":b.name,"parent":b.parent.name if b.parent else None,
                "head_local":vec(b.head_local),"tail_local":vec(b.tail_local),
                "matrix_local":matrix(b.matrix_local)} for b in ob.data.bones]
        objects.append(item)
    report={"schema":"TWO_CHARACTER_INTERFACE_INVENTORY_V1",
        "status":"CANDIDATE_MEASUREMENT_NOT_CANON_APPROVED",
        "input_path":str(a.input),"input_sha256":sha,
        "blender_version":bpy.app.version_string,
        "scene_unit_system":bpy.context.scene.unit_settings.system,
        "scene_scale_length":bpy.context.scene.unit_settings.scale_length,
        "objects":objects,
        "object_count":len(objects),
        "armature_count":sum(o["type"]=="ARMATURE" for o in objects),
        "notes":["World bounding boxes are candidate mesh geometry, not approved body landmarks.",
                 "Character-left/right convention cannot be inferred from +X without verified source and camera.",
                 "No source file was saved or modified."],
        "G1":"BLOCKED","G2":"NOT_RUN","G3":"PARTIAL_MEASUREMENT_ONLY","G4":"NOT_RUN"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("CHAR_INTERFACE_INVENTORY="+json.dumps({
        "status":report["status"],"objects":len(objects),
        "armatures":report["armature_count"],"sha256":sha}),flush=True)
if __name__=="__main__":main()

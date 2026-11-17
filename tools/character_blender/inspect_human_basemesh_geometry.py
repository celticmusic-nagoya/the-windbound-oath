#!/usr/bin/env python3
"""Read-only Blender asset-library geometry inspection; NOT artistic approval.
Usage: python -m bpy -b --python SCRIPT -- input.blend output.json
"""
import bpy,hashlib,json,pathlib,sys
from mathutils import Vector
args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(args)!=2:raise SystemExit("usage: -- input.blend report.json")
src=pathlib.Path(args[0]).resolve();dest=pathlib.Path(args[1]).resolve()
if src==dest or not src.is_file():raise SystemExit("BLOCKED invalid source")
before=hashlib.sha256(src.read_bytes()).hexdigest()
report={"source_sha256":before,"blender_version":bpy.app.version_string,"status":"BLOCKED","geometry":[],"art_qa":"NOT_RUN","canonical_match":"BLOCKED","production_approval":False}
try:
    # Asset libraries may contain many unlinked objects; inspect bpy.data.objects too.
    bpy.ops.wm.open_mainfile(filepath=str(src))
    rows=[]
    for obj in bpy.data.objects:
        if obj.type!="MESH":continue
        mesh=obj.data
        vertices=len(mesh.vertices);faces=len(mesh.polygons)
        verts=[obj.matrix_world@v.co for v in mesh.vertices] if vertices else []
        bounds=[[round(min(v[k] for v in verts),5),round(max(v[k] for v in verts),5)] for k in range(3)] if verts else None
        rows.append({"name":obj.name,"mesh":mesh.name,"vertices":vertices,"faces":faces,"quads":sum(len(p.vertices)==4 for p in mesh.polygons),"triangles":sum(len(p.vertices)==3 for p in mesh.polygons),"ngons":sum(len(p.vertices)>4 for p in mesh.polygons),"bounds_xyz":bounds,"uv_layers":len(mesh.uv_layers),"materials":len(mesh.materials),"linked_to_scene":bool(obj.users_collection),"modifiers":[m.type for m in obj.modifiers]})
    report["geometry"]=rows
    report["status"]="PASS_GEOMETRY_INVENTORY_ONLY" if rows else "BLOCKED_NO_MESHES"
except Exception as e:report["reason"]=type(e).__name__+": "+str(e)
report["source_unchanged"]=hashlib.sha256(src.read_bytes()).hexdigest()==before
if not report["source_unchanged"]:report["status"]="FAIL_SOURCE_CHANGED"
dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"status":report["status"],"mesh_objects":len(report["geometry"]),"source_unchanged":report["source_unchanged"]}))
if report["status"]!="PASS_GEOMETRY_INVENTORY_ONLY":raise SystemExit(2)

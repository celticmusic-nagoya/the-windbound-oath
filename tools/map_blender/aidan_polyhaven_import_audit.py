"""Inspect actual downloaded Poly Haven .blend source in isolated headless Blender.
Usage: blender -b source.blend --python this_script.py
"""
import bpy,json,hashlib,os,pathlib,bmesh
out=pathlib.Path(os.environ.get("AIDAN_IMPORT_OUT","/tmp/aidan-import"))
out.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
items=[]
for obj in bpy.data.objects:
    if obj.type!="MESH":continue
    mesh=obj.data
    bm=bmesh.new()
    try:
        bm.from_mesh(mesh)
        items.append({"name":obj.name,"vertices":len(bm.verts),
          "faces":len(bm.faces),"triangles":sum(max(0,len(f.verts)-2) for f in bm.faces),
          "boundary_edges":sum(e.is_boundary for e in bm.edges),
          "nonmanifold_edges":sum(not e.is_manifold for e in bm.edges),
          "dimensions":[round(float(x),5) for x in obj.dimensions],
          "materials":[m.name for m in mesh.materials if m]})
    finally:bm.free()
report={"status":"IMPORTED_SOURCE_NOT_ART_APPROVED","blender":bpy.app.version_string,
 "source":bpy.data.filepath,"objects":items,"mesh_count":len(items),
 "total_triangles":sum(o["triangles"] for o in items),
 "g1":"BLOCKED","g2":"NOT_RUN","g3":"PARTIAL_PASS" if items else "FAIL",
 "g4":"NOT_RUN"}
(out/"import_audit.json").write_text(json.dumps(report,indent=2))
print("AIDAN_IMPORT_AUDIT="+json.dumps(report))
assert items,"No mesh objects in source .blend"

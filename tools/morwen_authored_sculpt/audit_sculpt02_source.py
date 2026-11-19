"""Read-only SCULPT02 Blender source inventory. Blender 5.2.4; never saves input."""
import bpy, bmesh, hashlib, json, sys
from pathlib import Path
a=sys.argv[sys.argv.index("--")+1:]
if len(a)!=3: raise SystemExit("Usage: -- source.blend expected_sha output.json")
source=Path(a[0]).resolve(); expected=a[1]; output=Path(a[2]).resolve()
digest=hashlib.sha256(source.read_bytes()).hexdigest()
if digest!=expected: raise SystemExit("BLOCKED_SOURCE_SHA_MISMATCH: "+digest)
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False,load_ui=False)
rows=[]; totals={"meshes":0,"vertices":0,"edges":0,"faces":0,"quads":0,"triangles":0,"ngons":0,"nonmanifold_edges":0,"loose_edges":0,"degenerate_faces":0,"uv_layers":0,"shape_keys":0,"vertex_groups":0,"armatures":0}
for obj in sorted(bpy.data.objects,key=lambda x:x.name):
 if obj.type=="ARMATURE":
  totals["armatures"]+=1
  rows.append({"name":obj.name,"type":"ARMATURE","bones":len(obj.data.bones)})
 elif obj.type=="MESH":
  m=obj.data; bm=bmesh.new();bm.from_mesh(m);bm.normal_update()
  faces=len(bm.faces);quads=sum(len(f.verts)==4 for f in bm.faces);tris=sum(len(f.verts)==3 for f in bm.faces)
  stats={"name":obj.name,"type":"MESH","vertices":len(m.vertices),"edges":len(m.edges),"faces":faces,"quads":quads,"triangles":tris,"ngons":faces-quads-tris,"nonmanifold_edges":sum(not e.is_manifold for e in bm.edges),"loose_edges":sum(e.is_wire for e in bm.edges),"degenerate_faces":sum(f.calc_area()<1e-12 for f in bm.faces),"uv_layers":len(m.uv_layers),"shape_keys":len(m.shape_keys.key_blocks) if m.shape_keys else 0,"vertex_groups":len(obj.vertex_groups),"armature_modifiers":sum(mod.type=="ARMATURE" for mod in obj.modifiers)}
  for k in totals:
   if k in stats:totals[k]+=stats[k]
  rows.append(stats);bm.free();totals["meshes"]+=1
packed=[{"name":i.name,"sha256":hashlib.sha256(i.packed_file.data).hexdigest()} for i in bpy.data.images if i.packed_file]
result={"status":"MEASURED_SOURCE_ONLY_NOT_ART_ACCEPTANCE","source":str(source),"sha256":digest,"blender":bpy.app.version_string,"units":{"system":bpy.context.scene.unit_settings.system,"scale_length":bpy.context.scene.unit_settings.scale_length,"world_scale_canonical":False},"totals":totals,"objects":rows,"packed_images":packed,"license":"BLOCKED_REQUIRES_EXTERNAL_PROVENANCE","lineage":"BLOCKED_NOT_PROVEN_FROM_SCENE","Layer0_visual_match":"NOT_RUN","G1":"BLOCKED","G2":"NOT_RUN","G3":"PARTIAL_INVENTORY_ONLY","G4":"NOT_RUN"}
output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
print("SCULPT02_READONLY_INVENTORY",output)

"""Read-only legacy .blend facial component inventory. Run with bpy available.

python tools/character_blender/inventory_morwen_legacy_face.py -- INPUT.blend OUTPUT.json
Never promotes a legacy mesh to production.
"""
import hashlib,json,pathlib,sys
if len(sys.argv)!=4 or sys.argv[1]!="--":raise SystemExit("usage: -- INPUT.blend OUTPUT.json")
src=pathlib.Path(sys.argv[2]);out=pathlib.Path(sys.argv[3])
if not src.is_file():raise SystemExit("missing input")
before=hashlib.sha256(src.read_bytes()).hexdigest()
import bpy
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),load_ui=False)
tokens={"eye":("eye","ocular","iris","pupil","sclera"),
"eyelid":("lid","eyelid","palpebral"),
"eyelash":("lash","eyelash","cilia"),
"nose":("nose","nasal"),
"mouth":("mouth","lip","jaw")}
items={k:[] for k in tokens}
for ob in bpy.data.objects:
 name=ob.name.lower()
 for key,words in tokens.items():
  if any(w in name for w in words):
   entry={"name":ob.name,"type":ob.type,"mesh_vertices":len(ob.data.vertices) if ob.type=="MESH" else None,
   "mesh_polygons":len(ob.data.polygons) if ob.type=="MESH" else None,
   "dimensions":[round(float(v),6) for v in ob.dimensions],
   "modifiers":[m.type for m in ob.modifiers]}
   items[key].append(entry)
after=hashlib.sha256(src.read_bytes()).hexdigest()
report={"status":"PASS_INVENTORY_ONLY" if before==after else "FAIL_SOURCE_CHANGED",
"source":str(src),"source_sha256_before":before,"source_sha256_after":after,
"blender_version":bpy.app.version_string,"total_objects":len(bpy.data.objects),
"components":items,"method":"OBJECT_NAME_HEURISTIC_ONLY",
"caveat":"Absence of a matching name does not prove absence of geometry; embedded topology and shape keys require visual review.",
"reuse_verdict":"BLOCKED_PENDING_MESH_VISUAL_AND_TOPOLOGY_REVIEW","G1":"BLOCKED","G2":"NOT_RUN","G4":"NOT_RUN"}
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2,ensure_ascii=False))
print(json.dumps({"status":report["status"],"counts":{k:len(v) for k,v in items.items()},"source_unchanged":before==after}))
if before!=after:raise SystemExit(1)

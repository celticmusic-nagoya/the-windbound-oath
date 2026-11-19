"""Read-only SCULPT02 mesh/rig/UV/shape-key inventory. Blender 5.2.4.
Never save source. Counts are diagnostics, not independent art approval.
"""
import bpy,sys,json,hashlib,collections,pathlib
src=pathlib.Path(sys.argv[sys.argv.index('--')+1]).resolve()
out=pathlib.Path(sys.argv[sys.argv.index('--')+2]).resolve()
out.mkdir(parents=True,exist_ok=True)
sha=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
objects=[]
for obj in bpy.data.objects:
 d={'name':obj.name,'type':obj.type}
 if obj.type=='MESH':
  mesh=obj.data
  counts=collections.Counter(len(p.vertices) for p in mesh.polygons)
  edges=collections.Counter(tuple(sorted((e.vertices[0],e.vertices[1]))) for e in mesh.edges)
  # edge incidence derived from polygon loops, not wire edge existence
  incidence=collections.Counter()
  for p in mesh.polygons:
   vs=list(p.vertices)
   for i in range(len(vs)):incidence[tuple(sorted((vs[i],vs[(i+1)%len(vs)])))]+=1
  d.update(vertices=len(mesh.vertices),faces=len(mesh.polygons),triangles=sum(max(0,len(p.vertices)-2) for p in mesh.polygons),quads=counts[4],quad_ratio=round(counts[4]/max(1,len(mesh.polygons)),4),nonmanifold_edges=sum(v!=2 for v in incidence.values()),wire_edges=sum(k not in incidence for k in edges),uv_layers=len(mesh.uv_layers),uv_names=[u.name for u in mesh.uv_layers],shape_keys=[k.name for k in mesh.shape_keys.key_blocks] if mesh.shape_keys else [],vertex_groups=len(obj.vertex_groups),armature_modifiers=[m.object.name if m.object else None for m in obj.modifiers if m.type=='ARMATURE'],materials=[m.name if m else None for m in mesh.materials])
 elif obj.type=='ARMATURE':
  d.update(bones=len(obj.data.bones),bone_names=[x.name for x in obj.data.bones])
 objects.append(d)
report={'source_path':str(src),'source_sha256':sha,'status':'UNAPPROVED_READ_ONLY_INSPECTION','local_coordinates':'SOURCE_UNMODIFIED; CANONICAL_WORLD_SCALE_NOT_ASSERTED','objects':objects,'source_file_saved':False,'G1':'BLOCKED_REFERENCE_VISUAL_MATCH','G2':'NOT_RUN_INDEPENDENT_ART','G3':'PARTIAL_MESH_INVENTORY_ONLY','G4':'NOT_RUN'}
(out/'sculpt02_inspection.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
# Preview only; leave .blend source unchanged. Rendered screenshots require validated camera framing.
print('SCULPT02_INSPECTION_DONE',sha,len(objects))

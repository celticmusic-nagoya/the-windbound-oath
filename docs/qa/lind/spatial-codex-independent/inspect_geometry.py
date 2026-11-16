import bpy,bmesh,math,json,sys
from pathlib import Path
rows=[]
for o in bpy.data.objects:
 if o.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(o.data)
 rows.append({'name':o.name,'vertices':len(bm.verts),'faces':len(bm.faces),'edges':len(bm.edges),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-10 for f in bm.faces),'nonfinite_vertices':sum(not all(math.isfinite(x) for x in v.co) for v in bm.verts),'uv_layers':len(o.data.uv_layers),'materials':[m.name if m else None for m in o.data.materials],'bounds':[[min(v.co[i] for v in bm.verts),max(v.co[i] for v in bm.verts)] for i in range(3)]})
 bm.free()
out=Path(sys.argv[sys.argv.index('--')+1]);out.write_text(json.dumps(rows,indent=2)+'\n');print('INDEPENDENT_GEOMETRY_INSPECTED',len(rows))

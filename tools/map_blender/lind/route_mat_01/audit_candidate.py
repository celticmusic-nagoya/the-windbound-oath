"""Read-only audit of saved candidate; never interprets technical results as art PASS."""
import bpy,bmesh,json,sys,math,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=Path(sys.argv[sys.argv.index('--')+1]).resolve();rows=[];trees={};bounds={};failures=[]
objs=[o for o in bpy.data.objects if o.type=='MESH' and o.get('role')!='qa_stage']
for o in objs:
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=list(bm.faces))
 boundary=sum(e.is_boundary for e in bm.edges);nonmanifold=sum(not e.is_manifold for e in bm.edges)
 badface=sum(f.calc_area()<1e-10 for f in bm.faces);volume=bm.calc_volume(signed=True)
 coords=[o.matrix_world@v.co for v in bm.verts];lo=[min(v[j] for v in coords) for j in range(3)];hi=[max(v[j] for v in coords) for j in range(3)]
 uv=o.data.uv_layers.active;uvarea=[]
 if uv:
  for f in o.data.polygons:
   a=[uv.data[i].uv for i in f.loop_indices];uvarea.append(abs(sum(a[i].x*a[(i+1)%len(a)].y-a[(i+1)%len(a)].x*a[i].y for i in range(len(a)))/2))
 missinguv=not uv or not uvarea or min(uvarea)<1e-12
 row={'name':o.name,'role':o.get('role'),'vertices':len(bm.verts),'triangles':len(bm.faces),'boundary_edges':boundary,'nonmanifold_edges':nonmanifold,'degenerate_triangles':badface,'signed_volume_study_m3':volume,'dimensions_study_m':[hi[j]-lo[j] for j in range(3)],'bounds_study_m':[lo,hi],'uv_layers':len(o.data.uv_layers),'minimum_uv_polygon_area':min(uvarea) if uvarea else None,'scan_source':o.get('scan_source')}
 rows.append(row);bounds[o.name]=(lo,hi);trees[o.name]=BVHTree.FromBMesh(bm,epsilon=0.000001);bm.free()
 if boundary or nonmanifold or badface or volume<=0 or missinguv:failures.append({'object':o.name,'reason':'mesh/volume/UV inspection failed'})
# Triangle-surface intersections are evidence requiring review, not Boolean volume.
intersections=[]
for i,a in enumerate(objs):
 if a.get('role')=='support_core':continue
 for b in objs[i+1:]:
  if b.get('role')=='support_core':continue
  al,ah=bounds[a.name];bl,bh=bounds[b.name]
  if any(ah[j]<bl[j] or bh[j]<al[j] for j in range(3)):continue
  pairs=trees[a.name].overlap(trees[b.name])
  if pairs:intersections.append({'a':a.name,'b':b.name,'triangle_surface_crossings':len(pairs)})
# Independently report stone/core engagement. Embedding mortar is intentional.
core=trees['BondedLimeRubbleCore'];engagement=[]
for o in objs:
 if o.get('role') in ['support_core','foundation']:continue
 crossings=len(trees[o.name].overlap(core));engagement.append({'name':o.name,'core_surface_crossings':crossings,'interpretation':'crossings show contact/embedding, not structural load certification'})
report={'saved_file_reopened':bpy.data.filepath,'blender':bpy.app.version_string,'mesh_count':len(rows),'triangles':sum(r['triangles'] for r in rows),'per_mesh_failures':failures,'stone_surface_intersections_requiring_review':intersections,'core_engagement':engagement,'meshes':rows,'G1':'BLOCKED_UNAPPROVED_METRICS','G2':'NOT_RUN_INDEPENDENT','G3':'FAIL' if failures or intersections else 'PASS_MESH_UV_REOPEN_SUBSET','G4':'NOT_RUN','limits':['No structural engineering load simulation','No game/navmesh/Android test','BVH surface crossings require review; containment overlaps are not comprehensively detected','Canonical world transform remains null; actual dimensions are study measurements']}
out.mkdir(parents=True,exist_ok=True);(out/'mesh-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:report[k] for k in ['mesh_count','triangles','per_mesh_failures','stone_surface_intersections_requiring_review','G3']}))

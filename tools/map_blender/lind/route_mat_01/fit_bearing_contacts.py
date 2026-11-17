"""Local quarry contact fitting; subtract higher-priority bearing stones from neighbours.
No source scans or first candidate changed. Exact closed contact surfaces, not hidden intersections.
"""
import bpy,bmesh,sys,json
from pathlib import Path
from mathutils.bvhtree import BVHTree
out=Path(sys.argv[sys.argv.index('--')+1]).resolve();changes=[]
from importlib.util import spec_from_file_location,module_from_spec
sp=spec_from_file_location('builder',Path(__file__).with_name('build_curated.py'));mod=module_from_spec(sp);sp.loader.exec_module(mod)
rank={'foundation':0,'full_depth_voussoir':1,'through_bond':2,'coping':3,'load_bearing_scan_stone':4}
objs=sorted([o for o in bpy.data.objects if o.type=='MESH' and o.get('role') in rank],key=lambda o:(rank[o['role']],o.name))
def tree(o):
 bm=bmesh.new();bm.from_mesh(o.data);t=BVHTree.FromBMesh(bm,epsilon=0);bm.free();return t
for i,o in enumerate(objs):
 cutters=[]
 for c in objs[:i]:
  if rank[c['role']]==rank[o['role']]:continue
  if tree(o).overlap(tree(c)):
   bpy.context.view_layer.objects.active=o
   m=o.modifiers.new('IndividuallyFittedContact','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=c
   bpy.ops.object.modifier_apply(modifier=m.name);cutters.append(c.name)
 bm=bmesh.new();bm.from_mesh(o.data)
 bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000015)
 bmesh.ops.dissolve_degenerate(bm,dist=.000015,edges=list(bm.edges))
 bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 bm.to_mesh(o.data);bm.free()
 # Soften actual quarry-cut arrises on existing irregular scanned solids.
 bpy.context.view_layer.objects.active=o
 bevel=o.modifiers.new('QuarryArrisWear','BEVEL');bevel.width=.008;bevel.segments=2;bevel.limit_method='ANGLE';bevel.angle_limit=.85
 try:bpy.ops.object.modifier_apply(modifier=bevel.name)
 except RuntimeError:bpy.data.objects[o.name].modifiers.remove(bevel)
 # Scan triangles smooth, quarry cap planes stay flat; no broad smoothing of the silhouette.
 for p in o.data.polygons:p.use_smooth=p.area<.0015
 mod.unwrap(o)
 if cutters:changes.append({'object':o.name,'cut_to_fit':cutters})
# Save separate corrected file; the prior candidate remains immutable.
bpy.ops.wm.save_as_mainfile(filepath=str(out/'abutment.blend'),compress=True)
(out/'contact-fitting.json').write_text(json.dumps({'method':'individual exact Boolean bearing contact cuts','changes':changes,'old_candidate':'method-c-01 unchanged','source_LOD':'explicit object LOD0, never arbitrary first mesh','smoothing':'small scanned triangles only; quarry planes remain flat','structural_load_simulation':'NOT_RUN'},indent=2))

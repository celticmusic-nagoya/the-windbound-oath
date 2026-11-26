"""V5 isolated mid-distance scanned rock shoulders, preserve V4 composition and near cliff."""
import bpy,bmesh,sys,math,json,hashlib
from pathlib import Path
from array import array
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
src,rock,boulder,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
locks={src:'affd4725b3a3d5a2c537abe01160021c29e5b432f5200057ebb2d64481e7dc78',rock:'da8010774291c5d0acfbcc3b82b367be06c5ed0926640147de5f17371ef227d1',boulder:'8f8004fb52ebd00c4702a50873ac799e7bd7a0bea3415f2d8bc9986e1c58e371'}
assert bpy.app.version[:3]==(5,3,0) and all(sha(p)==v for p,v in locks.items())
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),load_ui=False)
scene=bpy.context.scene;coast=bpy.data.objects['Offshore coastal strata | provisional'];bpy.context.view_layer.update()
def dg(data,prop,count,typ):
    a=array(typ,[0])*count
    if count:data.foreach_get(prop,a)
    return hashlib.sha256(a.tobytes()).hexdigest()
def snap():
    return {o.name:(dg(o.data.vertices,'co',len(o.data.vertices)*3,'f'),dg(o.data.loops,'vertex_index',len(o.data.loops),'i'),dg(o.data.polygons,'material_index',len(o.data.polygons),'i'),tuple((u.name,dg(u.data,'uv',len(u.data)*2,'f')) for u in o.data.uv_layers),tuple(tuple(row) for row in o.matrix_world),tuple(m.name if m else None for m in o.data.materials),o.hide_render) for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.startswith('V5_scan_')}
old=snap();assert len(old)==381
def bvh(o):
    return BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons])
coast_bvh=bvh(coast)
# Geometry-only import of known historical CC0 source meshes (same exact inputs as PR363).
# Remove only new unused source dependencies before packing; preserve all existing scene datablocks.
templates={};source_stats={}
for filename,name,count in [(rock,'rock_07_LOD3',929),(boulder,'boulder_01_LOD3',4134)]:
    pre_ids=set(bpy.data.user_map())
    with bpy.data.libraries.load(str(filename.resolve()),link=False) as (a,b):
        assert name in a.objects,a.objects;b.objects=[name]
    raw=b.objects[0];assert raw.type=='MESH' and len(raw.data.vertices)==count
    imported=set(bpy.data.user_map())-pre_ids
    assert raw in imported and raw.data in imported and not raw.users_collection
    # Reconstruct geometry/UV into a clean derivative, so no source node-group or material reference survives.
    original=raw.data
    mesh=bpy.data.meshes.new('V5_scan_template_'+name)
    mesh.from_pydata([v.co.copy() for v in original.vertices],[],[tuple(p.vertices) for p in original.polygons])
    mesh.update()
    for p,q in zip(mesh.polygons,original.polygons):
        p.use_smooth=q.use_smooth
        assert tuple(p.vertices)==tuple(q.vertices)
    for layer in original.uv_layers:
        uv=mesh.uv_layers.new(name=layer.name)
        assert len(uv.data)==len(layer.data)
        for i,item in enumerate(layer.data):uv.data[i].uv=item.uv
    user_map=bpy.data.user_map()
    external={f'{i.bl_rna.identifier}:{i.name}':[f'{u.bl_rna.identifier}:{u.name}' for u in user_map.get(i,set()) if u not in imported] for i in imported}
    external={k:v for k,v in external.items() if v}
    print('SCAN_DEPENDENCY_EXTERNAL',json.dumps(external),flush=True)
    assert not external,external
    removed=sorted(f'{i.bl_rna.identifier}:{i.name}' for i in imported)
    bpy.data.batch_remove(ids=tuple(imported))
    assert pre_ids.issubset(set(bpy.data.user_map()))
    print('SCAN_DEPENDENCY_BATCH_REMOVED',json.dumps(removed),flush=True)
    pts=[v.co.copy() for v in mesh.vertices];lo=Vector(tuple(min(v[i] for v in pts) for i in range(3)));hi=Vector(tuple(max(v[i] for v in pts) for i in range(3)));assert min(hi-lo)>0
    for v in mesh.vertices:
        v.co=Vector(((v.co.x-(lo.x+hi.x)/2)/(hi.x-lo.x),(v.co.y-(lo.y+hi.y)/2)/(hi.y-lo.y),(v.co.z-lo.z)/(hi.z-lo.z)))
    mesh.update();mesh.calc_loop_triangles()
    bm=bmesh.new();bm.from_mesh(mesh);source_stats[name]=dict(vertices=len(mesh.vertices),triangles=len(mesh.loop_triangles),boundary_edges=sum(e.is_boundary for e in bm.edges),nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),degenerate_faces=sum(f.calc_area()<1e-10 for f in bm.faces));bm.free()
    templates[name]=mesh
mat=coast.data.materials[0].copy();mat.name='V5_scan_coast_shared_rock'
nt=mat.node_tree;n=nt.nodes;l=nt.links
scale=next(q for q in n if q.type=='VECT_MATH' and q.operation=='SCALE')
geo=n.new('ShaderNodeNewGeometry');l.new(geo.outputs['Position'],scale.inputs[0])
for mesh in templates.values():
    mesh.materials.append(mat)
    for p in mesh.polygons:p.material_index=0
# Art-directed, provisional selected face positions on the two major headlands.
# Measure actual sea-facing surface at requested z; skip absent samples, test actual contact.
# Individual varied masses; no change to original coast silhouette or geometry.
spec=[
    ('left_outer','rock_07_LOD3',-64,1.2,4.8,3.4,3.1,-.18),
    ('left_shoulder','boulder_01_LOD3',-50,1.9,6.2,4.4,4.2,.31),
    ('left_tip','rock_07_LOD3',-35,1.0,3.9,3.2,2.6,.77),
    ('centre_outer','boulder_01_LOD3',-28,1.8,5.5,3.8,3.8,-.49),
    ('centre_crest','rock_07_LOD3',-10,2.8,6.5,4.7,5.3,.12),
    ('right_shoulder','boulder_01_LOD3',5,2.0,4.5,3.8,3.8,1.04),
]
coll=bpy.data.collections.new('V5 offshore scanned shoulders | scenic only');scene.collection.children.link(coll)
rows=[];omitted=[]
for label,name,x,z,sx,sy,sz,yaw in spec:
    hit,normal,idx,dist=coast_bvh.ray_cast(Vector((x,-25,z)),Vector((0,-1,0)),100)
    if hit is None or hit.y>-34 or hit.y<-82:omitted.append(dict(label=label,reason='no eligible offshore face'));continue
    mesh=templates[name];o=bpy.data.objects.new('V5_scan_'+label,mesh);coll.objects.link(o)
    # Base embedded under the waterline; attach at measured surface. Avoid floating standalone boulders.
    loc=Vector((x,hit.y+.12*sy,-.35))
    lin=Matrix.Rotation(yaw,4,'Z')@Matrix.Diagonal((sx,sy,sz,1))
    o.matrix_world=Matrix.Translation(loc)@lin;bpy.context.view_layer.update()
    pairs=bvh(o).overlap(coast_bvh)
    if not pairs:
        omitted.append(dict(label=label,reason='no surface intersection'));bpy.data.objects.remove(o,do_unlink=True);continue
    # Existing offshore body and added scan intentionally intersect; not watertight union.
    o['scenic_only']=True;o['canonical_transform']='UNDETERMINED'
    rows.append(dict(name=o.name,source=name,source_face=list(hit),location=list(loc),scale=[sx,sy,sz],yaw=yaw,intersecting_face_pairs=len(pairs),triangles=len(mesh.loop_triangles)))
assert len(rows)>=3,(rows,omitted)
bpy.context.view_layer.update();assert snap()==old and all(sha(p)==v for p,v in locks.items())
missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()]
assert not missing,missing
scene.camera=bpy.data.objects['F01_diagnostic'];scene.render.image_settings.file_format='PNG'
dest=out/'cliff_coast_scan_v5_UNAPPROVED.blend';assert not dest.exists()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()),load_ui=False);scene=bpy.context.scene
assert snap()==old and all(sha(p)==v for p,v in locks.items())
q=dict(status='ISOLATED_SCAN_SHOULDER_FEASIBILITY',sources={p.name:v for p,v in locks.items()},source_licence='CC0 Poly Haven rock_07 and boulder_01, PR363 historical exact source manifest; not Irish provenance',protected_meshes=len(old),scan_stats=source_stats,placements=rows,omitted=omitted,added_triangles=sum(r['triangles'] for r in rows),native_reopen='PASS',limits=['Intentional scenic intersection with offshore body; no watertight union or structural collision.','Provisional BU only. No C13 edits, D4, G1, G2 or G4 acceptance. No GLB bake.'])
def finish():
    q['outputs']={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.blend','.png')}
    (out/'qa.json').write_text(json.dumps(q,indent=2)+'\n')
finish()
scene.render.filepath=str((out/'candidate.png').resolve());bpy.ops.render.render(write_still=True);finish()
d=bpy.data.cameras.new('V5 scan oblique');o=bpy.data.objects.new('V5 scan oblique',d);scene.collection.objects.link(o)
o.location=(-105,-1,37);o.rotation_euler=(Vector((-25,-100,5))-o.location).to_track_quat('-Z','Y').to_euler();d.lens=34;d.clip_end=500
scene.camera=o;scene.render.filepath=str((out/'oblique.png').resolve());bpy.ops.render.render(write_still=True);finish()

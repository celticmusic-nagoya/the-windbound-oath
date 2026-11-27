"""V8: existing BUILD kit A/B, exact V7 source, independent west-neighborhood scenery."""
import bpy,sys,json,hashlib,math
from pathlib import Path
from mathutils import Vector
from array import array
src,kit,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
lock='6cd524bfe139db1ed39038c4ba4a57eb4dea60231190b875dae25fcb9f02696a'
assert bpy.app.version[:3]==(5,3,0) and sha(src)==lock
sys.path.insert(0,str(kit/'tools/map_blender/lind/buildings'))
import build_village_buildings as B
B.reset_scene();cfg,info=B.kit_config.load_config(B.REPO)
records=[];names=[]
for kind,offset in [('house_a',(-16,8,0)),('house_b',(-26,9,0))]:
    b=B.Building(kind,cfg,'peaceful',offset=offset);b.build();objs=b.emit()
    assert objs
    for o in objs:o.name='V8_'+o.name
    bpy.context.view_layer.update()
    pts=[o.matrix_world@v.co for o in objs for v in o.data.vertices]
    lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
    assert lo[0]>=-32 and hi[0]<=-10.4 and lo[1]>=2.8 and hi[1]<=15,(kind,lo,hi)
    assert all(o.data.uv_layers for o in objs)
    records.append(dict(kind=kind,offset=offset,bounds=[lo,hi],mesh=B.mesh_stats(objs),objects=[o.name for o in objs]))
    names.extend(o.name for o in objs)
assert records[1]['bounds'][1][0]<records[0]['bounds'][0][0]
assert not B.KM.REPORT['missing'],B.KM.REPORT
texture_report=dict(loaded=list(B.KM.REPORT['loaded']),missing=list(B.KM.REPORT['missing']))
bpy.ops.file.pack_all()
# Separate building checkpoint, never alter existing source.
built=out/'v8_build_kit_checkpoint.blend';bpy.ops.wm.save_as_mainfile(filepath=str(built.resolve()),compress=True);buildsha=sha(built)
def dg(data,prop,n,t):
    a=array(t,[0])*n
    if n:data.foreach_get(prop,a)
    return hashlib.sha256(a.tobytes()).hexdigest()
def signature(o):
    m=o.data
    return (dg(m.vertices,'co',len(m.vertices)*3,'f'),dg(m.loops,'vertex_index',len(m.loops),'i'),dg(m.polygons,'material_index',len(m.polygons),'i'),tuple((u.name,dg(u.data,'uv',len(u.data)*2,'f')) for u in m.uv_layers),tuple(tuple(row) for row in o.matrix_world),tuple(q.name if q else None for q in m.materials),o.hide_render)
built_shapes={n:signature(bpy.data.objects[n])[:5] for n in names}
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),load_ui=False);scene=bpy.context.scene
def snap():return {o.name:signature(o) for o in scene.objects if o.type=='MESH' and not o.name.startswith('V8_')}
old=snap();assert len(old)==219
ground=bpy.data.objects['V3_village_reconstructed_patch'];bpy.context.view_layer.update()
# Extension with identical seam vertices and UV coordinate scale. Original terrain is never edited.
seam=sorted([(v.co.y,v.co.z) for v in ground.data.vertices if abs(v.co.x+10)<1e-6]);assert len(seam)==11,seam
xs=[-32.5+2.5*i for i in range(10)];assert xs[-1]==-10
verts=[(x,y,z*(1-max(0,min(1,(-10-x)/5)))) for y,z in seam for x in xs]
faces=[]
for j in range(len(seam)-1):
    for i in range(len(xs)-1):
        a=j*len(xs)+i;faces.extend([(a,a+1,a+len(xs)+1),(a,a+len(xs)+1,a+len(xs))])
m=bpy.data.meshes.new('V8_west_grade');m.from_pydata(verts,[],faces);m.update();m.materials.append(ground.data.materials[0])
uv=m.uv_layers.new(name='UVMap')
for p in m.polygons:
    for i in p.loop_indices:
        v=m.vertices[m.loops[i].vertex_index].co;uv.data[i].uv=(v.x/2.5,v.y/2.5)
o=bpy.data.objects.new('V8_west_grade',m);scene.collection.objects.link(o)
seam_after=sorted([(v.co.y,v.co.z) for v in m.vertices if abs(v.co.x+10)<1e-6]);assert seam_after==seam
# Append only scenic visual meshes, no new active portals/collision/game state.
with bpy.data.libraries.load(str(built.resolve()),link=False) as (a,b):
    assert all(n in a.objects for n in names);b.objects=names
coll=bpy.data.collections.new('V8_WEST_NEIGHBORHOOD_SCENIC_ONLY');scene.collection.children.link(coll)
for o in b.objects:
    assert o.name in built_shapes and not o.users_collection
    coll.objects.link(o);o['scenic_only']=True;o['canonical_transform']='UNDETERMINED'
bpy.context.view_layer.update()
assert all(signature(bpy.data.objects[n])[:5]==s for n,s in built_shapes.items())
assert snap()==old and sha(src)==lock and sha(built)==buildsha
missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()]
assert not missing,missing
dest=out/'village_neighborhood_v8_UNAPPROVED.blend';assert not dest.exists()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()),load_ui=False);scene=bpy.context.scene
assert snap()==old and all(signature(bpy.data.objects[n])[:5]==s for n,s in built_shapes.items())
q=dict(status='SCENIC_NEIGHBORHOOD_FEASIBILITY',source_sha256=lock,build_kit_commit='f54a6856494d2cd5ad5124cf85b02981e05c8b63',building_checkpoint_sha256=buildsha,buildings=records,texture_report=texture_report,protected_meshes=len(old),seam_vertices=len(seam),seam_delta=0,missing_images=missing,native_reopen='PASS',limits=['Regenerated existing BUILD code, not previously saved native; temporary scene only. No approved world placement or unit conversion.','No runtime anchors, collision, interior, G1/D4/G2/G4 acceptance. West grade extension and two buildings are scenic; no new terrain traversal.'])
def finish():
    q['outputs']={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.blend','.png')}
    (out/'qa.json').write_text(json.dumps(q,indent=2)+'\n')
finish()
scene.render.resolution_x=1200;scene.render.resolution_y=675;scene.cycles.samples=16
for name,eye,aim,lens in [('street',(11,-14,6),(0,6,1.8),34),('neighborhood',(-5,-18,10),(-15,7,2.7),29),('overview',(-11,-5,27),(-13,7,0),30)]:
    d=bpy.data.cameras.new('V8 '+name);o=bpy.data.objects.new('V8 '+name,d);scene.collection.objects.link(o);o.location=eye;o.rotation_euler=(Vector(aim)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=200
    scene.camera=o;scene.render.filepath=str((out/(name+'.png')).resolve());bpy.ops.render.render(write_still=True);finish()

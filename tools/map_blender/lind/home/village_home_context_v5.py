"""Isolated scenic context: verified HOME and verge V4, never edit input files."""
import bpy,sys,math,json,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
from array import array
home,verge,out,engine=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
locks={home:'dff3a32df533c8786f3122e07cf681c18f4805bd913d750f04ce15b321b10fed',verge:'c314c40e861b7fabba61da8f1b430321cdf126b6d0af1b26180bb2b1f8990776'}
assert bpy.app.version[:3]==(5,3,0) and all(sha(p)==s for p,s in locks.items())
def digest(data,prop,count,typ):
    a=array(typ,[0])*count
    if count:data.foreach_get(prop,a)
    return hashlib.sha256(a.tobytes()).hexdigest()
def shape(o):
    m=o.data
    return [digest(m.vertices,'co',len(m.vertices)*3,'f'),digest(m.loops,'vertex_index',len(m.loops),'i'),digest(m.polygons,'loop_total',len(m.polygons),'i'),tuple((u.name,digest(u.data,'uv',len(u.data)*2,'f')) for u in m.uv_layers)]
def box(o):
    pts=[o.matrix_world@Vector(p) for p in o.bound_box]
    return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
bpy.ops.wm.open_mainfile(filepath=str(home.resolve()),load_ui=False)
bpy.context.view_layer.update()
source={o.name:dict(matrix=o.matrix_world.copy(),shape=shape(o),bounds=box(o),hidden=o.hide_render) for o in bpy.context.scene.objects if o.type=='MESH' and (o.name.startswith('GEO_') or o.name.startswith('COL_AIDANHOUSE_'))}
assert 'GEO_AIDANHOUSE_PORCH' in source and len(source)>10
assert 'COL_AIDANHOUSE_porch_post_west' in source and 'COL_AIDANHOUSE_porch_post_east' in source
visual=[v['bounds'] for n,v in source.items() if n.startswith('GEO_') and not v['hidden']]
lo=[min(v[0][i] for v in visual) for i in range(3)];hi=[max(v[1][i] for v in visual) for i in range(3)]
bpy.ops.wm.open_mainfile(filepath=str(verge.resolve()),load_ui=False)
scene=bpy.context.scene;ground=bpy.data.objects['V3_village_reconstructed_patch']
old_vertices=[v.co.copy() for v in ground.data.vertices];old_faces=[tuple(p.vertices) for p in ground.data.polygons]
assert len(old_vertices)==81 and len(old_faces)==128
# Scene-local proposed house placement: external portal start at y=3.0; no canonical BU-to-m assertion.
offset=Vector((0,8.2,0));reservation=[lo[0]-.5,hi[0]+.5,lo[1]+offset.y-.5,hi[1]+offset.y+.5]
before=set(bpy.data.objects)
with bpy.data.libraries.load(str(home.resolve()),link=False) as (a,b):b.objects=list(source)
collection=bpy.data.collections.new('V5_HOME_ISOLATED_CONTEXT');scene.collection.children.link(collection)
houses={}
for o in b.objects:
    assert o and o.name in source and o.type=='MESH'
    rec=source[o.name];assert shape(o)==rec['shape']
    for c in list(o.users_collection):c.objects.unlink(o)
    collection.objects.link(o);o.parent=None;o.matrix_world=Matrix.Translation(offset)@rec['matrix'];o.hide_render=rec['hidden'] or o.name.startswith('COL_')
    if o.name.startswith('COL_'):o.hide_set(True)
    houses[o.name]=o
# Preserve house mesh bytes (including UVs), not a new authored house.
bpy.context.view_layer.update()
assert all(shape(o)==source[n]['shape'] for n,o in houses.items())
# Grid extension on north side, smooth transition to level grade at porch/building.
# Southern geometry at y<=2.5 retains exact source heights.
old={(round(v.x,5),round(v.y,5)):v.z for v in old_vertices}
x0=min(-10,math.floor((reservation[0]-1)/2.5)*2.5);x1=max(10,math.ceil((reservation[1]+1)/2.5)*2.5)
y1=max(10,math.ceil((reservation[3]+2)/2.5)*2.5)
def plateau(x,y):
    X=100+x;return 18+3*math.sin(math.pi*y/300)+.006*(X+175)+.85*math.sin((X+175)/74)*math.sin(y/85)-(18+.006*275)
def z(x,y):
    raw=old.get((round(x,5),round(y,5)),plateau(x,y))
    t=max(0,min(1,(y-2.5)/2.5));return raw*(1-t*t*(3-2*t))
nx=round((x1-x0)/2.5)+1;ny=round((y1+10)/2.5)+1
verts=[(x0+2.5*i,-10+2.5*j,z(x0+2.5*i,-10+2.5*j)) for j in range(ny) for i in range(nx)]
faces=[]
for j in range(ny-1):
    for i in range(nx-1):
        a=j*nx+i;faces.extend([(a,a+1,a+nx+1),(a,a+nx+1,a+nx)])
mat=ground.data.materials[0];m=bpy.data.meshes.new('V5_context_grade');m.from_pydata(verts,[],faces);m.update();m.materials.append(mat.copy());ground.data=m
uv=m.uv_layers.new(name='UVMap')
for p in m.polygons:
    for i in p.loop_indices:
        v=m.vertices[m.loops[i].vertex_index].co;uv.data[i].uv=(v.x/2.5,v.y/2.5)
# Add a T-shaped access strip to the existing world-coordinate road material without changing its main road.
nt=m.materials[0].node_tree;n=nt.nodes;l=nt.links
sep=next(x for x in n if x.type=='SEPXYZ')
# Identify final road blend by the existing smoothstep parameters.
mask=next(x for x in n if x.type=='MAP_RANGE' and abs(x.inputs['From Min'].default_value-2.15)<.001)
orig=mask.inputs['Value'].links[0].from_socket
def mathn(op,a,b=None):
    q=n.new('ShaderNodeMath');q.operation=op
    for i,v in enumerate((a,b)):
        if v is None:continue
        if isinstance(v,(int,float)):q.inputs[i].default_value=v
        else:l.new(v,q.inputs[i])
    return q.outputs[0]
# Convert 1.05m half-width approach to existing 2.15--2.65m blend domain.
side=mathn('ADD',mathn('ABSOLUTE',sep.outputs['X']),1.35)
# Start at main road and stop at porch entrance. Use max distance SDF.
end=mathn('ADD',mathn('SUBTRACT',sep.outputs['Y'],3.95),2.4)
start=mathn('ADD',mathn('SUBTRACT',0,sep.outputs['Y']),2.4)
d=mathn('MAXIMUM',side,mathn('MAXIMUM',end,start))
l.new(mathn('MINIMUM',orig,d),mask.inputs['Value'])
# Existing foliage outside the building/approach stays; exclude full bounds and conform roots to changed grade.
bpy.context.view_layer.update()
kept=[];omitted=[];root=[]
for o in list(scene.objects):
    if not o.name.startswith('V3_') or o.type!='MESH' or o==ground:continue
    a,b=box(o)
    overlap=lambda r:not (b[0]<r[0] or a[0]>r[1] or b[1]<r[2] or a[1]>r[3])
    if overlap(reservation) or overlap([-1.35,1.35,2.0,4.1]):
        omitted.append(o.name);o.hide_render=True;o.hide_set(True);continue
    pts=[o.matrix_world@v.co for v in o.data.vertices];mn=min(p.z for p in pts)
    roots=[p for p in pts if p.z<=mn+.025]
    offsets=[]
    for p in roots:
        ok,q,_,_=ground.ray_cast(Vector((p.x,p.y,10)),Vector((0,0,-1)),distance=20)
        if ok:offsets.append(q.z-p.z)
    if len(offsets)!=len(roots) or max(offsets)-min(offsets)>.05:
        omitted.append(o.name);o.hide_render=True;o.hide_set(True);continue
    w=o.matrix_world.copy();w.translation.z+=max(offsets)-.01;o.matrix_world=w
    root.extend([max(offsets)-.01-d for d in offsets]);kept.append(o.name)
bpy.context.view_layer.update()
# Measure route clearance against actual imported collision boxes. No runtime or headroom assertion.
proxies={name:box(o) for name,o in houses.items() if name.startswith('COL_AIDANHOUSE_')}
assert proxies
clear=[]
for i in range(123):
    y=offset.y-5.2+i*.025
    clear.append(min(math.hypot(max(a[0],0,-b[0]),max(a[1]-y,0,y-b[1])) for a,b in proxies.values()))
south=max(abs(z(x,y)-v) for (x,y),v in old.items() if y<=2.5)
sys.path[:0]=[str(engine/'tools'),str(engine/'tools/production_qa')]
from blueprint_engine.residual import evaluate
actual={'south_geometry_delta':south,'portal_clearance':min(clear),'max_root_abs':max(map(abs,root),default=0)}
metrics=evaluate(dict(values={'south_geometry_delta':0,'portal_clearance':.45,'max_root_abs':0},tolerances={'south_geometry_delta':.00001,'portal_clearance':0,'max_root_abs':.05},uncertainty={k:0 for k in actual},lower_bound={'portal_clearance':.45}),dict(actual=actual,uncertainty={k:.000001 for k in actual}))
assert all(sha(p)==s for p,s in locks.items())
def cam(name,eye,aim,lens):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=eye;o.rotation_euler=(Vector(aim)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=200;return o
c=cam('V5 village street',(11,-14,6),(0,6,1.8),34)
scene.camera=c;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.render.resolution_x=1200;scene.render.resolution_y=675;scene.render.resolution_percentage=100
# Missing external image data remains explicitly recorded, not silently substituted.
missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()]
bpy.ops.file.pack_all()
dest=out/'village_home_context_v5_UNAPPROVED.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()),load_ui=False);scene=bpy.context.scene
assert all(shape(bpy.data.objects[name])==v['shape'] for name,v in source.items())
q=dict(status='ISOLATED_ARCHITECTURAL_CONTEXT_FEASIBILITY',sources={p.name:s for p,s in locks.items()},home_meshes=len(source),home_local_bounds=[lo,hi],offset=list(offset),terrain_bounds=[x0,-10,x1,y1],terrain_triangles=len(faces),kept_vegetation=len(kept),excluded_vegetation=omitted,root_samples=len(root),actual=actual,engine_metrics=metrics,missing_external_images=missing,native_reopen='PASS',limits=['Provisional independent scene; no approved unit conversion between HOME BU and region m. No world placement, no D4/G1/G2/G4 acceptance.','Ground grade and approach are scenic; portal clearance XY only. No GLB bake of V4 material, no gameplay integration.'])
def finish():
    q['outputs']={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.blend','.png')}
    (out/'qa.json').write_text(json.dumps(q,indent=2)+'\n')
finish()
for name,eye,aim,lens in [('street',(11,-14,6),(0,6,1.8),34),('entry',(0,-5,2.1),(0,5,1.4),27),('oblique',(13,15,15),(0,5,0),34)]:
    scene.camera=cam('V5 '+name,eye,aim,lens);scene.render.filepath=str((out/(name+'.png')).resolve());bpy.ops.render.render(write_still=True);finish()

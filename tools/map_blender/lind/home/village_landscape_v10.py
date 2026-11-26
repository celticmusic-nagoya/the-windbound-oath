"""V10 scenic village perimeter: exact boundary seams, road continuation, plaza and ECO trees."""
import bpy,sys,math,json,hashlib,random
from pathlib import Path
from array import array
from mathutils import Vector,Matrix
src,eco,out,engine=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
lock='0326b9b05eeb7fc03ab92eda15cf8d33517796c448a5b71684552d5bf604bfd2'
assert bpy.app.version[:3]==(5,3,0) and sha(src)==lock
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),load_ui=False)
scene=bpy.context.scene;bpy.context.view_layer.update()
grounds=[bpy.data.objects[n] for n in ['V3_village_reconstructed_patch','V8_west_grade','V9_east_grade']]
def dg(data,prop,n,t):
    a=array(t,[0])*n
    if n:data.foreach_get(prop,a)
    return hashlib.sha256(a.tobytes()).hexdigest()
def signature(o):
    m=o.data
    return (dg(m.vertices,'co',len(m.vertices)*3,'f'),dg(m.loops,'vertex_index',len(m.loops),'i'),dg(m.polygons,'material_index',len(m.polygons),'i'),tuple((u.name,dg(u.data,'uv',len(u.data)*2,'f')) for u in m.uv_layers),tuple(tuple(row) for row in o.matrix_world),tuple(q.name if q else None for q in m.materials) if o.name not in [g.name for g in grounds] else (),o.hide_render)
def snap():return {o.name:signature(o) for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.startswith('V10_')}
old=snap();assert len(old)==269
grid={}
for g in grounds:
    for v in g.data.vertices:
        p=g.matrix_world@v.co;k=(round(p.x,5),round(p.y,5))
        if k in grid:assert abs(grid[k]-p.z)<1e-6
        grid[k]=p.z
xmin,xmax=min(x for x,y in grid),max(x for x,y in grid);ymin,ymax=min(y for x,y in grid),max(y for x,y in grid)
assert (xmin,xmax,ymin,ymax)==(-32.5,42.5,-10,15),(xmin,xmax,ymin,ymax)
def clamp(v,a,b):return max(a,min(b,v))
def smooth(t):t=clamp(t,0,1);return t*t*(3-2*t)
def curve(x):
    # C1 smooth connection at old ends, no change to inner route.
    return -8*smooth((xmin-x)/27.5)+9*smooth((x-xmax)/30)
def terrain(x,y):
    if (x,y) in grid:return grid[x,y]
    cx,cy=clamp(x,xmin,xmax),clamp(y,ymin,ymax)
    edge=grid[(cx,cy)]
    distance=math.hypot(x-cx,y-cy)
    fade=smooth(distance/17.5)
    hill=1.7+1.8*math.sin(x*.068+y*.032)+1.3*math.cos(y*.12-x*.033)
    ridge=3.0*math.exp(-((y-44)/21)**2)
    roadflat=smooth((abs(y-curve(x))-3.5)/7)
    return edge*(1-fade)+fade*(hill+ridge)*roadflat
xs=[-72.5+2.5*i for i in range(63)];ys=[-42.5+2.5*j for j in range(40)]
vertices=[];indices={};faces=[]
def ix(x,y):
    k=(x,y)
    if k not in indices:indices[k]=len(vertices);vertices.append((x,y,terrain(x,y)))
    return indices[k]
for y,Y in zip(ys,ys[1:]):
    for x,X in zip(xs,xs[1:]):
        if xmin<=x and X<=xmax and ymin<=y and Y<=ymax:continue
        a,b,c,d=ix(x,y),ix(X,y),ix(X,Y),ix(x,Y);faces.extend([(a,b,c),(a,c,d)])
m=bpy.data.meshes.new('V10_perimeter_heightfield');m.from_pydata(vertices,[],faces);m.update()
outer=bpy.data.objects.new('V10_perimeter_heightfield',m);scene.collection.objects.link(outer)
uv=m.uv_layers.new(name='UVMap')
for p in m.polygons:
    p.use_smooth=True
    for i in p.loop_indices:
        v=m.vertices[m.loops[i].vertex_index].co;uv.data[i].uv=(v.x/2.5,v.y/2.5)
boundary=[(x,y) for x,y in grid if x in (xmin,xmax) or y in (ymin,ymax)]
assert all(k in indices for k in boundary)
seam=max(abs(vertices[indices[k]][2]-grid[k]) for k in boundary);assert seam==0
# Copy shared V9 PBR shader: alter the road mask only. Existing surface geometry remains byte-identical.
base=grounds[0].data.materials[0];mat=base.copy();mat.name='V10_curving_road_plaza_PBR'
n=mat.node_tree.nodes;l=mat.node_tree.links
mask=next(q for q in n if q.type=='MAP_RANGE' and abs(q.inputs['From Min'].default_value-2.15)<.001)
orig=mask.inputs['Value'].links[0].from_socket
sep=next(q for q in n if q.type=='SEPXYZ');X,Y=sep.outputs['X'],sep.outputs['Y']
def op(kind,a,b=None):
    q=n.new('ShaderNodeMath');q.operation=kind
    for i,v in enumerate((a,b)):
        if v is None:continue
        if isinstance(v,(int,float)):q.inputs[i].default_value=v
        else:l.new(v,q.inputs[i])
    return q.outputs[0]
def ramp(v,lo,hi):
    q=n.new('ShaderNodeMapRange');q.interpolation_type='SMOOTHSTEP';q.clamp=True
    q.inputs['From Min'].default_value=lo;q.inputs['From Max'].default_value=hi;l.new(v,q.inputs['Value']);return q.outputs['Result']
# Find original main road absolute-Y input; leave T approach and existing noise unchanged.
abs_y=[q for q in n if q.type=='MATH' and q.operation=='ABSOLUTE' and q.inputs[0].is_linked and q.inputs[0].links[0].from_socket==Y]
assert len(abs_y)==1,len(abs_y)
center=op('ADD',op('MULTIPLY',ramp(op('SUBTRACT',xmin,X),0,27.5),-8),op('MULTIPLY',ramp(op('SUBTRACT',X,xmax),0,30),9))
l.new(op('SUBTRACT',Y,center),abs_y[0].inputs[0])
# Plaza south of the inn (inside local reservation, no change to north building frontage).
dx=op('DIVIDE',op('SUBTRACT',X,19),7.2);dy=op('DIVIDE',op('SUBTRACT',Y,-2.8),3.7)
ellipse=op('MULTIPLY',op('SQRT',op('ADD',op('MULTIPLY',dx,dx),op('MULTIPLY',dy,dy))),2.4)
l.new(op('MINIMUM',orig,ellipse),mask.inputs['Value'])
for g in grounds:g.data.materials[0]=mat
m.materials.append(mat)
# ECO archive is historical verified integration candidate, not latest branch and not art-approved.
manifest=json.loads((eco/'manifest.v2.json').read_text())
assets={'tree':'glb/eco_tree_deciduous_a_LOD1.glb','shrub':'glb/eco_shrub_round_a_LOD1.glb'}
expected={'tree':'9d2c284a54645900e309e69ffe5e6a831680b8913227b502a9f9beca45616aae','shrub':'6d16ebf1a269ff9714ec6c46d36b33b7005ca8e1032a5133e5732c96e561f1af'}
templates={}
for kind,rel in assets.items():
    p=eco/rel;assert sha(p)==expected[kind]==manifest['files'][rel]['sha256']
    before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(p.resolve()))
    added=[o for o in set(bpy.data.objects)-before if o.type=='MESH'];assert len(added)==1,added
    t=added[0];t.name='V10_template_'+kind;t.hide_render=True;t.hide_set(True)
    templates[kind]=t
bpy.context.view_layer.update()
# Real terrain raycasts in world space for all proposed roots.
def ground_hit(x,y):
    for g in [*grounds,outer]:
        inv=g.matrix_world.inverted();o=inv@Vector((x,y,30));d=inv.to_3x3()@Vector((0,0,-1))
        hit,p,_,_=g.ray_cast(o,d,distance=100)
        if hit:return (g.matrix_world@p).z
    return None
rng=random.Random(2026112610);placements=[];rootres=[]
coll=bpy.data.collections.new('V10 scenic vegetation');scene.collection.children.link(coll)
# Asymmetric groups outside existing footprint, plus the empty southern strip of east/west extension.
centers=[(-49,18),(-25,25),(-6,30),(20,25),(42,24),(57,15),(-44,-17),(-12,-22),(28,-22),(50,-19)]
for idx,(cx,cy) in enumerate(centers):
    for j in range(5):
        kind='tree' if j<2 else 'shrub';t=templates[kind];mesh=t.data;mesh.calc_loop_triangles()
        x=cx+rng.uniform(-5,5);y=cy+rng.uniform(-4,4)
        s=rng.uniform(.78,1.18) if kind=='tree' else rng.uniform(.8,1.4)
        lin=Matrix.Rotation(rng.uniform(0,math.tau),4,'Z')@Matrix.Scale(s,4)@t.matrix_world.to_3x3().to_4x4()
        pts=[lin@v.co for v in mesh.vertices];lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
        bx=(x+lo[0],x+hi[0],y+lo[1],y+hi[1])
        if bx[0]<xs[0]+.1 or bx[1]>xs[-1]-.1 or bx[2]<ys[0]+.1 or bx[3]>ys[-1]-.1:continue
        if not(bx[1]<xmin-.3 or bx[0]>xmax+.3 or bx[3]<ymin-.3 or bx[2]>ymax+.3):continue
        if min(abs(p-curve(x)) for p in (bx[2],bx[3],y))<4.8+max(abs(lo[0]),abs(hi[0]))*.25:continue
        if any(math.hypot(x-p['x'],y-p['y'])<(3 if kind=='tree' and p['kind']=='tree' else 1.1) for p in placements):continue
        low=[p for p in pts if p.z<=lo[2]+.025];heights=[ground_hit(x+p.x,y+p.y) for p in low]
        if not heights or any(v is None for v in heights):continue
        offsets=[a-p.z for a,p in zip(heights,low)];z=max(offsets)-.01;rr=[z-a for a in offsets]
        if max(map(abs,rr))>.10:continue
        o=bpy.data.objects.new('V10_'+kind+'_%03d'%len(placements),mesh);coll.objects.link(o);o.matrix_world=Matrix.Translation(Vector((x,y,z)))@lin
        placements.append(dict(name=o.name,kind=kind,x=x,y=y,z=z,root_max=max(rr),triangles=len(mesh.loop_triangles)));rootres.extend(rr)
assert sum(p['kind']=='tree' for p in placements)>=8 and len(placements)>=20,placements
bpy.context.view_layer.update();assert snap()==old and sha(src)==lock
sys.path[:0]=[str(engine/'tools'),str(engine/'tools/production_qa')]
from blueprint_engine.residual import evaluate
actual={'seam_delta':seam,'root_abs_max':max(map(abs,rootres)),'protected_mesh_changes':0}
metrics=evaluate(dict(values={k:0 for k in actual},tolerances={'seam_delta':.000001,'root_abs_max':.10,'protected_mesh_changes':0},uncertainty={k:0 for k in actual}),dict(actual=actual,uncertainty={'seam_delta':0,'root_abs_max':.000001,'protected_mesh_changes':0}))
dest=out/'village_landscape_v10_UNAPPROVED.blend';assert not dest.exists()
missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()];assert not missing,missing
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True);bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()),load_ui=False)
scene=bpy.context.scene;grounds=[bpy.data.objects[n] for n in ['V3_village_reconstructed_patch','V8_west_grade','V9_east_grade']]
assert snap()==old and all(bpy.data.objects.get(p['name']) for p in placements)
q=dict(status='SCENIC_LANDSCAPE_FEASIBILITY',source_sha256=lock,eco_sources=expected,protected_meshes=len(old),changed_existing_material_scope=[g.name for g in grounds],seam_vertices=len(boundary),terrain_triangles=len(faces),outer_bounds=[xs[0],xs[-1],ys[0],ys[-1]],vegetation=placements,root_samples=len(rootres),actual=actual,engine_metrics=metrics,native_reopen='PASS',limits=['Provisional local BU, not approved world placement. Existing buildings not moved. Road curve and plaza are shader features, not new collision/navigation. Historical ECO LOD1 candidates, not current ECO branch.','No runtime, G1/D4/G2/G4 acceptance; no GLB bake.'])
def finish():
    q['outputs']={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.blend','.png')}
    (out/'qa.json').write_text(json.dumps(q,indent=2)+'\n')
finish()
scene.render.resolution_x=1200;scene.render.resolution_y=675;scene.cycles.samples=16
for name,eye,aim,lens in [('overview',(3,-34,48),(3,7,0),28),('market',(13,-19,8),(24,8,3),30),('arrival',(-53,-15,4),(-14,5,3),35)]:
    d=bpy.data.cameras.new('V10 '+name);o=bpy.data.objects.new('V10 '+name,d);scene.collection.objects.link(o);o.location=eye;o.rotation_euler=(Vector(aim)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=300
    scene.camera=o;scene.render.filepath=str((out/(name+'.png')).resolve());bpy.ops.render.render(write_still=True);finish()

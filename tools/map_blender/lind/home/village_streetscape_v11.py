"""V11 provisional two-sided street. Preserve all geometry except scoped outer grade vertices."""
import bpy,sys,math,hashlib,json
from pathlib import Path
from array import array
from mathutils import Vector,Matrix
src,out,engine=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
lock='6964953322cd2cf53add08011a37c5853ec4b9f49ccffaa11152f3b53317b730'
assert bpy.app.version[:3]==(5,3,0) and sha(src)==lock
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),load_ui=False)
scene=bpy.context.scene;bpy.context.view_layer.update()
def dg(data,prop,count,typ):
    a=array(typ,[0])*count
    if count:data.foreach_get(prop,a)
    return hashlib.sha256(a.tobytes()).hexdigest()
def sig(o):
    m=o.data
    return (dg(m.vertices,'co',len(m.vertices)*3,'f'),dg(m.loops,'vertex_index',len(m.loops),'i'),dg(m.polygons,'material_index',len(m.polygons),'i'),tuple((u.name,dg(u.data,'uv',len(u.data)*2,'f')) for u in m.uv_layers),tuple(tuple(row) for row in o.matrix_world),tuple(q.name if q else None for q in m.materials),o.hide_render)
def box(objs):
    pts=[o.matrix_world@Vector(v) for o in objs for v in o.bound_box]
    return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
def snap():return {o.name:sig(o) for o in bpy.context.scene.objects if o.type=='MESH'}
old=snap();assert len(old)==320,len(old)
outer=bpy.data.objects['V10_perimeter_heightfield']
groundnames=['V3_village_reconstructed_patch','V8_west_grade','V9_east_grade','V10_perimeter_heightfield']
groups={}
for prefix in ['GEO_AIDANHOUSE_','V8_GEO_DWELL01_','V8_GEO_DWELL02_','V9_GEO_INN_','V9_GEO_SHOP_']:
    groups[prefix]=[o for o in scene.objects if o.type=='MESH' and o.name.startswith(prefix) and not o.hide_render]
assert all(groups.values()) and len(groups['V8_GEO_DWELL02_'])==len(groups['V9_GEO_SHOP_'])==12
# Source V8/V9 actual placement anchors. Rotated fronts face north, toward the street.
placements=[]
moved={}
for prefix,origin,dest in [('V8_GEO_DWELL02_',(-26,9,0),(-24,-9.1,0)),('V9_GEO_SHOP_',(31.5,8.8,0),(26,-9.8,0))]:
    objs=groups[prefix];before=box(objs)
    T=Matrix.Translation(Vector(dest))@Matrix.Rotation(math.pi,4,'Z')@Matrix.Translation(-Vector(origin))
    for o in objs:
        o.matrix_world=T@o.matrix_world;moved[o.name]=tuple(tuple(row) for row in o.matrix_world)
    bpy.context.view_layer.update()
    after=box(objs)
    assert after[1][1]<-3.15 and after[0][1]>-17 and after[0][0]>-32.5 and after[1][0]<42.5,(prefix,after)
    placements.append(dict(group=prefix,old_bounds=before,new_bounds=after,translation=dest,rotation_deg=180))
# Flatten only the new south-side foundation reservations on the outer heightfield.
# Old inner terrain is already level in these x ranges. Keep seam positions unchanged.
def clamp(x,a,b):return max(a,min(b,x))
def smooth(t):t=clamp(t,0,1);return t*t*(3-2*t)
pads=[]
for p in placements:
    a,b=p['new_bounds'];pads.append([a[0]-.8,b[0]+.8,a[1]-.8,b[1]+.8])
old_z={v.index:float(v.co.z) for v in outer.data.vertices}
changed=[]
for v in outer.data.vertices:
    x,y=v.co.x,v.co.y
    if y>=-10:continue
    d=min(math.hypot(max(p[0]-x,0,x-p[1]),max(p[2]-y,0,y-p[3])) for p in pads)
    w=1-smooth(d/4.0)
    if w>0 and abs(v.co.z)>1e-9:
        oldv=v.co.z;v.co.z*=1-w;changed.append((v.index,x,y,float(oldv),float(v.co.z)))
assert changed
outer.data.update();bpy.context.view_layer.update()
assert all(v.co.z==old_z[v.index] for v in outer.data.vertices if v.co.y>=-10)
# Verify the ground under each moved building by raycasts in actual mesh geometry.
def hit(x,y):
    for name in groundnames:
        g=bpy.data.objects[name];inv=g.matrix_world.inverted()
        ok,p,_,_=g.ray_cast(inv@Vector((x,y,30)),inv.to_3x3()@Vector((0,0,-1)),distance=100)
        if ok:return float((g.matrix_world@p).z)
    return None
foundation=[]
for p in placements:
    a,b=p['new_bounds'];samples=[]
    for i in range(15):
        for j in range(15):
            x=a[0]+(b[0]-a[0])*i/14;y=a[1]+(b[1]-a[1])*j/14
            z=hit(x,y);assert z is not None;samples.append(z)
    p['foundation_min']=min(samples);p['foundation_max']=max(samples);foundation+=samples
assert max(map(abs,foundation))<=.08,max(map(abs,foundation))
# Protect existing ecology near terrain changes; no new contact checks on unrelated vegetation.
for o in scene.objects:
    if o.type!='MESH' or not o.name.startswith(('V10_tree_','V10_shrub_')):continue
    a,b=box([o])
    assert all(not (a[0]-2.5<=x<=b[0]+2.5 and a[1]-2.5<=y<=b[1]+2.5) for _,x,y,_,_ in changed),(o.name,a,b)
# Sample centreline against actual building mesh bounds (conservative aggregate AABB); terrain only, not runtime collision.
bounds={k:box(v) for k,v in groups.items()}
def curve(x):return -8*smooth((-32.5-x)/27.5)+9*smooth((x-42.5)/30)
route=[]
for i in range(641):
    x=-70+i*150/640;y=curve(x);z=hit(x,y);assert z is not None
    clearance=min(math.hypot(max(a[0]-x,0,x-b[0]),max(a[1]-y,0,y-b[1])) for a,b in bounds.values())
    route.append([x,y,z,clearance])
min_clear=min(p[3] for p in route)
grade=max(abs(b[2]-a[2])/math.hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(route,route[1:]))
assert min_clear>=.6 and grade<=.30,(min_clear,grade)
# All geometry/UV/materials untouched except explicitly scoped outer Z; only chosen building transforms changed.
def verify():
    new=snap();assert new.keys()==old.keys()
    for name,s in old.items():
        t=new[name]
        if name==outer.name:assert t[1:]==s[1:],name
        elif name in moved:assert t[:4]==s[:4] and t[5:]==s[5:] and t[4]==moved[name],name
        else:assert t==s,name
verify();assert sha(src)==lock
sys.path[:0]=[str(engine/'tools'),str(engine/'tools/production_qa')]
from blueprint_engine.residual import evaluate
actual={'foundation_abs_max':max(map(abs,foundation)),'route_clearance':min_clear,'route_grade':grade,'protected_mesh_changes':0}
metrics=evaluate(dict(values={'foundation_abs_max':0,'route_clearance':.6,'route_grade':0,'protected_mesh_changes':0},tolerances={'foundation_abs_max':.08,'route_clearance':0,'route_grade':.30,'protected_mesh_changes':0},uncertainty={k:0 for k in actual},lower_bound={'route_clearance':.6}),dict(actual=actual,uncertainty={k:0 for k in actual}))
assert metrics['overall']=='PASS',metrics
dest=out/'village_streetscape_v11_UNAPPROVED.blend';assert not dest.exists()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True);bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()),load_ui=False);scene=bpy.context.scene;outer=bpy.data.objects['V10_perimeter_heightfield']
verify();assert sha(src)==lock
assert all(abs(outer.data.vertices[i].co.z-z)<1e-7 for i,_,_,_,z in changed)
q=dict(status='SCENIC_TWO_SIDED_STREET_FEASIBILITY',source_sha256=lock,moved_groups=placements,moved_meshes=len(moved),changed_outer_vertices=len(changed),protected_meshes=len(old)-len(moved)-1,foundation_samples=len(foundation),route_samples=len(route),actual=actual,engine_metrics=metrics,native_reopen='PASS',limits=['Provisional local BU; no canonical layout or scale. Two unadopted building groups repositioned, original V10 unchanged. Only outer grade Z edited under foundations.','Route XY building AABB clearance and terrain slope proxy, not actual collision, portal or Android QA. G1/D4/G2/G4 unresolved.'])
(out/'route_samples.json').write_text(json.dumps(dict(units='provisional BU',columns=['x','y','z','building_AABB_clearance'],samples=route),indent=2))
def finish():
    q['outputs']={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.blend','.png') or p.name=='route_samples.json'}
    (out/'qa.json').write_text(json.dumps(q,indent=2)+'\n')
finish()
scene.render.resolution_x=1200;scene.render.resolution_y=675;scene.cycles.samples=16
for name,eye,aim,lens in [('overview',(3,-34,48),(3,7,0),28),('street',(-12,-.7,2.3),(18,1,2.2),27),('market',(38,-1,4),(16,0,3),31)]:
    d=bpy.data.cameras.new('V11 '+name);o=bpy.data.objects.new('V11 '+name,d);scene.collection.objects.link(o);o.location=eye;o.rotation_euler=(Vector(aim)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=300
    scene.camera=o;scene.render.filepath=str((out/(name+'.png')).resolve());bpy.ops.render.render(write_still=True);finish()

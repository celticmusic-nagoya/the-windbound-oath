"""V21 native floor reconstruction. V19B checkpoint is immutable.
Rock/moss source meshes match V15C; original stump LOD0 instead of V15C LOD2.
Placement is quantized, not full GLB equivalence. Record conflicts; no silent corrections."""
import bpy,sys,math,hashlib,json,base64,zlib,struct,collections
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import convex_hull_2d
src,inputs,manifest,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lock='6b79f7e7f056cdbfa278c4662bd100eb2f778e638225421dfef060564d7c1cc1'
assert bpy.app.version[:3]==(5,3,0) and sha(src)==lock
dst=out/'forest_v21_native_floor.blend';assert not dst.exists()
raw=zlib.decompress(base64.b64decode(manifest.read_text().strip(),validate=True))
assert hashlib.sha256(raw).hexdigest()=='2268e0b2727bad82c2704b60d4d04bb0a5aa5d009e328a7025af080745c1aba2'
rows=list(struct.iter_unpack('<BHhhhHH',raw))
assert collections.Counter(m for m,*_ in rows)=={0:2,1:2,2:2,3:2,4:2,5:2,6:70,7:3}
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()))
scene=bpy.context.scene
def stats():
    oo=[o for o in bpy.context.scene.objects if o.type=='MESH']
    for o in oo:o.data.calc_loop_triangles()
    return dict(mesh_objects=len(oo),triangles=sum(len(o.data.loop_triangles) for o in oo),packed_images=sum(bool(i.packed_file) for i in bpy.data.images),external_images=[i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file])
before=stats();assert before['mesh_objects']==401 and before['triangles']==763977 and not before['external_images'],before
def geom(o):
    h=hashlib.sha256()
    for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
    for p in o.data.polygons:h.update(struct.pack('<I',len(p.vertices)));h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
    return (h.hexdigest(),tuple(tuple(r) for r in o.matrix_world))
replace={'R03','R04','R05','R06','R07','U02','U03'}
assert replace<=set(bpy.data.objects.keys())
protected={o.name:geom(o) for o in scene.objects if o.type=='MESH' and o.name not in replace}
assert len(protected)==394
# Delete only prior approximate floor instances in independent in-memory copy.
for n in replace:bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True)
def path(s):
    a=list(inputs.rglob(s));assert len(a)==1,(s,a);return a[0]
def imp(s):
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path(s)))
    created=set(bpy.data.objects)-before
    assert all(o.type=='MESH' for o in created),[o.name for o in created]
    return sorted(created,key=lambda o:o.name)
rr=imp('rock_moss_set_01_1k.gltf')
assert [o.name for o in rr]==['rock_moss_set_01_rock%02d'%i for i in range(1,7)]
moss=path('eco_moss_cushion_a_LOD0.glb')
assert sha(moss)=='d074175139e19ab93ff872fb381aadf1404169e761b0fe14f144a8d8ded079c1'
mm=imp(moss.name);uu=imp('tree_stump_01_1k.gltf');assert len(mm)==len(uu)==1
templates=rr+mm+uu
tri=[]
for o in templates:
    o.data.calc_loop_triangles();tri.append(len(o.data.loop_triangles))
assert tri==[11000,10996,5000,10589,16548,8994,680,41046],tri
placed={}
for m,i,x,y,z,a,s in rows:
    name=f'V21_{"R" if m<6 else "M" if m==6 else "U"}_{i:03d}'
    assert name not in placed
    o=bpy.data.objects.new(name,templates[m].data);scene.collection.objects.link(o)
    loc=(x/100,-z/100,y/100);angle=a*2*math.pi/65536;scale=s/10000
    o.location=loc;o.rotation_euler=(0,0,angle);o.scale=(scale,)*3
    placed[name]=dict(mesh=m,location=loc,yaw=angle,scale=scale)
for o in templates:bpy.data.objects.remove(o,do_unlink=True)
bpy.context.view_layer.update()
assert all(geom(bpy.data.objects[n])==v for n,v in protected.items())
terrain=bpy.data.objects['A3 provisional reconstructed terrain']
inv=terrain.matrix_world.inverted()
def hit(x,y):
    a=inv@Vector((x,y,100));direction=inv.to_3x3()@Vector((0,0,-1))
    ok,p,n,i=terrain.ray_cast(a,direction,distance=200)
    assert ok,(x,y)
    return (terrain.matrix_world@p).z
def footprint(o,root=False):
    xyz=[o.matrix_world@v.co for v in o.data.vertices]
    bottom=min(v.z for v in xyz)
    xy=[Vector((v.x,v.y)) for v in xyz if not root or v.z<=bottom+1.2]
    pts=[xy[i] for i in convex_hull_2d(xy)]
    assert len(pts)>=3,o.name
    return pts
def ps(p,a,b):
    v=b-a;d=v.length_squared
    return (p-a-v*max(0,min(1,(p-a).dot(v)/d))).length if d>1e-18 else (p-a).length
def cross(a,b):return a.x*b.y-a.y*b.x
def inside(p,h):
    v=[cross(b-a,p-a) for a,b in edges(h)]
    return min(v)>=-1e-8 or max(v)<=1e-8
def edges(h):return zip(h,h[1:]+h[:1])
def seg(a,b,c,d):
    x=cross(b-a,c-a);y=cross(b-a,d-a);u=cross(d-c,a-c);v=cross(d-c,b-c)
    if x*y<0 and u*v<0:return 0.
    return min(ps(a,c,d),ps(b,c,d),ps(c,a,b),ps(d,a,b))
def pointpoly(p,h):return 0. if inside(p,h) else min(ps(p,a,b) for a,b in edges(h))
def linepoly(a,b,h):
    if inside(a,h) or inside(b,h):return 0.
    return min(seg(a,b,c,d) for c,d in edges(h))
def poly_gap(a,b):
    if inside(a[0],b) or inside(b[0],a):return 0.
    return min(seg(p,q,r,s) for p,q in edges(a) for r,s in edges(b))
def bbox(h):return (min(p.x for p in h),max(p.x for p in h),min(p.y for p in h),max(p.y for p in h))
def bboxgap(a,b):return math.hypot(max(0,a[0]-b[1],b[0]-a[1]),max(0,a[2]-b[3],b[2]-a[3]))
route=(Vector((-205,140)),Vector((90,-90)))
reserved=[((67.536852,-72.486359),11),((45.876293,-75.886764),8),((49.408698,-58.352544),10),((93.943160,-93.074328),7)]
rays=[((65.4663,-80.2138),(45.876293,-75.886764),4),((65.4663,-80.2138),(93.943160,-93.074328),3)]
def reserved_gap(h):
    return min([linepoly(*route,h)-5]+[pointpoly(Vector(c),h)-r for c,r in reserved]+[linepoly(Vector(a),Vector(b),h)-r for a,b,r in rays])
obs=[]
for o in scene.objects:
    if o.type!='MESH' or o==terrain or o.name in placed:continue
    h=footprint(o,o.name.startswith(('V18_T_','V18_D_','V19_BG_')))
    obs.append((o.name,h,bbox(h)))
floor=[]
for name,rec in placed.items():
    o=bpy.data.objects[name];h=footprint(o);bb=bbox(h)
    xyz=[o.matrix_world@v.co for v in o.data.vertices];bottom=min(v.z for v in xyz)
    root=[v for v in xyz if v.z<=bottom+.12]
    residual=[v.z-hit(v.x,v.y) for v in root]
    assert residual,name
    rec.update(protected_gap=reserved_gap(h),min_root_residual=min(residual),nearest_root_abs=min(abs(x) for x in residual),root_samples=len(root))
    floor.append((name,h,bb))
for name,h,bb in floor:
    best=1000.;nearest=None
    for n,k,kb in obs+floor:
        if n==name or bboxgap(bb,kb)>best:continue
        d=poly_gap(h,k)
        if d<best:best=d;nearest=n
    placed[name].update(nearest_planar_obstacle=nearest,planar_obstacle_gap=best)
issues=[dict(name=n,protected_gap=v['protected_gap'],nearest_obstacle=v['nearest_planar_obstacle'],gap=v['planar_obstacle_gap'],burial=v['min_root_residual'],nearest_root=v['nearest_root_abs']) for n,v in placed.items() if v['protected_gap']<.0 or v['planar_obstacle_gap']<.02 or v['min_root_residual']<-.20 or v['nearest_root_abs']>.05]
(out/'floor_preflight.json').write_text(json.dumps(dict(status='HOLD' if issues else 'SAMPLED_PLANAR_PASS',rows=placed,issues=issues),indent=2)+'\n')
# Keep all exact source-derived placements in an isolated review copy; do not claim playable safety.
views=[((8,35.00075988769531,36),(12.2,33.3,38.5)),((18,34.22273864746094,37),(12,33.2,42))]
def camera(i):
    co=bpy.context.scene.camera;e,a=views[i];cv=lambda v:Vector((v[0],-v[2],v[1]))
    co.location=cv(e);co.rotation_euler=(cv(a)-co.location).to_track_quat('-Z','Y').to_euler()
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=800;scene.render.resolution_y=450;scene.render.resolution_percentage=100
camera(0);bpy.ops.file.pack_all();mid=stats()
assert mid['mesh_objects']==479 and mid['triangles']==926746 and not mid['external_images'],mid
bpy.ops.wm.save_as_mainfile(filepath=str(dst.resolve()))
bpy.ops.wm.open_mainfile(filepath=str(dst.resolve()));scene=bpy.context.scene;after=stats();assert mid==after
assert all(geom(bpy.data.objects[n])==v for n,v in protected.items())
assert all((Vector(bpy.data.objects[n].location)-Vector(v['location'])).length<1e-5 for n,v in placed.items())
for i in range(2):
    camera(i);scene.render.filepath=str((out/('forest_v21_view_%d.png'%(i+1))).resolve());bpy.ops.render.render(write_still=True)
assert sha(src)==lock
q=dict(status='NATIVE_FLOOR_ASSEMBLY_CANDIDATE',source_sha256=lock,blender=bpy.app.version_string,before=before,after=after,protected_geometry_transforms_exact=len(protected),floor_instances=len(placed),floor_triangles=sum(tri[m] for m,*_ in rows),original_stump_lod0=True,placement_manifest_sha256=hashlib.sha256(raw).hexdigest(),preflight_status='HOLD' if issues else 'SAMPLED_PLANAR_PASS',issue_count=len(issues),views=views,limits=['Source-derived reconstructed V19B plus floor, not full V15C. Quantized positions and source LOD0 stump. Planar hull and sampled root QA only, not collision/navigation. No independent G2 or Android.'])
q['sha256']={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.png','.blend')}
(out/'qa.json').write_text(json.dumps(q,indent=2)+'\n');print(q)

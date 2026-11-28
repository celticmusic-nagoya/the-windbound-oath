"""V58 noncanonical scenic extension and native comparison, no production placement.
Exact V57 source. All prior meshes, transforms and render flags protected."""
import bpy,sys,math,hashlib,json,struct
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.geometry import convex_hull_2d
src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lock='1b17e3196479142ddb4258586f3d9b953f33fde4d3b7a504dc32f5cdacbac6ee'
assert bpy.app.version[:3]==(5,3,0) and sha(src)==lock
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()));scene=bpy.context.scene
def meshhash(m):
    h=hashlib.sha256()
    for v in m.vertices:h.update(struct.pack('<3f',*v.co))
    for p in m.polygons:h.update(struct.pack('<I',len(p.vertices)));h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
    return h.hexdigest()
def snapshot(names):
    cache={}; result={}
    for n in names:
        o=bpy.data.objects[n]
        if o.data.name not in cache:cache[o.data.name]=meshhash(o.data)
        result[n]=(cache[o.data.name],tuple(tuple(r) for r in o.matrix_world),o.hide_render)
    return result

old=[o.name for o in scene.objects if o.type=='MESH'];assert len(old)==495
protected=snapshot(old)
terrain=bpy.data.objects['A3 provisional reconstructed terrain']
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def recipe(x,y):
    x+=600;y-=400
    p=18+3*math.sin(math.pi*y/300)+.006*(x+175)+.85*math.sin((x+175)/74)*math.sin(y/85)
    t=max(0,min(1,(x-375)/45))
    return f32(p+t*t*(3-2*t)*(5*math.sin((x-375)/39)*math.cos((y+245)/50)+9*math.exp(-((x-610)/86)**2-((y+395)/95)**2)))
source={(round(v.x,5),round(v.y,5)):float(v.z) for v in (terrain.matrix_world@v.co for v in terrain.data.vertices)}
def height_vertex(x,y):return source[(x,y)] if (x,y) in source else recipe(x,y)
def ray(o,x,y):
    inv=o.matrix_world.inverted()
    ok,p,n,i=o.ray_cast(inv@Vector((x,y,100)),inv.to_3x3()@Vector((0,0,-1)),distance=200)
    return float((o.matrix_world@p).z) if ok else None
# Matched cameras; retain previous V57 camera object and all meshes. Only study camera/light state changed.
cam=scene.camera;camdata=cam.data
pad=Vector((93.9431596631828,-93.0743278729908,27.988129971478276))
d=Vector((.788631932636555,-.6148655745981655,0))
e=pad-d*20;e.z=ray(terrain,e.x,e.y)+2.15
views=[(tuple(e),tuple(pad+Vector((0,0,3))),22),((83,-84,30.1),(94,-93,30),28),((71,-73,53),(96,-96,32),32)]
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.cycles.use_denoising=True
scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100
def render(name,i):
    a,b,l=views[i];cam.location=a;cam.rotation_euler=(Vector(b)-cam.location).to_track_quat('-Z','Y').to_euler();camdata.lens=l
    scene.render.filepath=str((out/name).resolve());bpy.ops.render.render(write_still=True)
for i in (0,1):render('v58_before_%d.png'%i,i)
# Add separate L-shaped extrapolated terrain beyond A3; copy existing material and UV scale, not original mesh edits.
v=[];faces=[];idx={}
def vertex(x,y):
    k=(x,y)
    if k not in idx:idx[k]=len(v);v.append((x,y,height_vertex(x,y)))
    return idx[k]
for i in range(24,54):
    x=i*2.5
    for j in range(-54,-24):
        y=j*2.5
        if x<100 and y>=-100:continue
        a,b,c,e=[vertex(*k) for k in ((x,y),(x+2.5,y),(x+2.5,y+2.5),(x,y+2.5))]
        faces.extend(((a,b,c),(a,c,e)))
m=bpy.data.meshes.new('V58_scenic_extension_mesh');m.from_pydata(v,[],faces);m.update()
ext=bpy.data.objects.new('V58_SCENIC_ONLY_terrain_extension',m);scene.collection.objects.link(ext);m.materials.append(terrain.data.materials[0])
uv=m.uv_layers.new(name='UVMap')
for loop in m.loops:
    x,y,z=v[loop.vertex_index];uv.data[loop.index].uv=(x/2,y/2)
seam=[(x,y,z) for x,y,z in v if (x==100 and y>=-100) or (y==-100 and x<=100)]
assert len(v)==705 and len(faces)==1288 and len(seam)==33
assert all((x,y) in source and source[(x,y)]==z for x,y,z in seam)
bpy.context.view_layer.update()
def ground(x,y):
    z=ray(terrain,x,y) if -100<=x<=100 and -100<=y<=0 else ray(ext,x,y)
    assert z is not None,(x,y)
    return z
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


# Build conservative root footprint obstacle list. Dense scan objects use only low-band vertices; skip upper meshes.
def hull_low_group(objects,zcut):
    p=[Vector((w.x,w.y)) for o in objects for w in (o.matrix_world@v.co for v in o.data.vertices) if w.z<=zcut]
    return [p[i] for i in convex_hull_2d(p)]
obs=[]
for name in old:
    o=bpy.data.objects[name]
    if o==terrain or name.startswith('V57_hero_'):continue
    h=footprint(o,name.startswith(('V18_T_','V18_D_','V19_BG_')))
    obs.append((name,h,bbox(h)))
for prefix,z in [('V57_hero_A',28.65093231201172),('V57_hero_B',27.257186889648438)]:
    group=[o for o in scene.objects if o.name.startswith(prefix) and o.type=='MESH']
    assert group
    h=hull_low_group(group,z+1.2);obs.append((prefix,h,bbox(h)))
def gap(h):
    bb=bbox(h);g=1e6;near=None
    for n,p,b in obs:
        if bboxgap(bb,b)>g:continue
        s=poly_gap(h,p)
        if s<g:g=s;near=n
    return g,near
def linkcopy(o,name,mat):
    no=bpy.data.objects.new(name,o.data);scene.collection.objects.link(no);no.matrix_world=mat;return no
# C is a scenic proxy across the source tile edge, never an official placement.
B=[o for o in scene.objects if o.name.startswith('V57_hero_B') and o.type=='MESH'];assert B
x,y=92,-105;z=ground(x,y);base=Vector((94,-81,27.257186889648438))
trans=Matrix.Translation((x,y,z))@Matrix.Rotation(math.pi,4,'Z')@Matrix.Translation(-base)
C=[linkcopy(o,'V58_SCENIC_C_'+str(i),trans@o.matrix_world) for i,o in enumerate(B)]
bpy.context.view_layer.update()
ch=hull_low_group(C,z+1.2);g,near=gap(ch);rg=reserved_gap(ch)
rootv=[w for o in C for w in (o.matrix_world@v.co for v in o.data.vertices) if w.z<=z+.15]
res=[w.z-ground(w.x,w.y) for w in rootv]
third=dict(position=[x,y,z],nearest=near,root_gap_m=g,reservation_gap_m=rg,root_sample_range_m=[min(res),max(res)],root_samples=len(res))
# Reject conflicting C in scene, preserve evidence and continue backdrop. This deletes only newly created isolated candidates.
if min(g,rg)<.05:
    for o in C:bpy.data.objects.remove(o,do_unlink=True)
    third['placed']=False
else:
    third['placed']=True;obs.append(('V58_SCENIC_C',ch,bbox(ch)))
# Reuse existing mesh assets (linked), not another generic tree generation. Ground contact relative to source lowest band.
templates={}
for n in old:
    o=bpy.data.objects[n]
    if n.startswith(('V18_T_','V18_D_','V19_BG_')):templates.setdefault(o.data.name,o)
assert templates,'no native tree templates'
templates=list(sorted(templates.values(),key=lambda o:o.name))
points=[[105.97244,-91.74441,0.8482185,318.68685],[104.1633,-100.54478,0.9265181,249.95796],[104.81208,-83.65229,0.7860787,314.84715],[113.45342,-91.86729,0.8924349,186.64379],[104.54697,-110.87759,0.867987,31.1363],[104.56983,-75.0209,0.7952045,71.03512],[113.58368,-101.45239,0.8954756,234.81163],[113.04161,-82.43784,0.9150793,251.94993],[77.42693,-109.98348,1.0194395,74.87753],[113.21562,-74.88566,0.9489749,248.44722],[114.0531,-110.68841,0.9757407,115.01462],[87.21958,-119.18723,0.9304778,301.73303],[96.53255,-119.93795,0.8607331,78.89594],[104.84759,-119.43788,1.0191736,298.83283],[70.02496,-110.19317,0.842723,38.21574],[122.07604,-101.98009,0.9221188,222.40329],[123.73097,-92.12461,0.7832619,301.34708],[78.67331,-118.79215,0.9211203,294.71707],[123.03189,-84.09338,0.9548333,225.71839],[104.37905,-64.20148,0.9485882,335.74625],[113.09498,-118.17618,0.8112117,227.59478],[122.57366,-75.04061,0.825667,241.40784],[114.38472,-65.92432,0.9430857,278.47277],[123.61433,-110.29366,1.0013665,258.05331],[95.02791,-128.91141,1.0390816,171.67162],[69.78454,-119.58185,0.8189086,140.87869]]
placed=[];rejected=[]
for i,(x,y,s,yaw) in enumerate(points):
    o=templates[i%len(templates)]
    loc=o.matrix_world.translation.copy();rot=Matrix.Rotation(math.radians(yaw),4,'Z')
    mat=Matrix.Translation((x,y,ground(x,y)))@rot@Matrix.Scale(s,4)@Matrix.Translation(-loc)@o.matrix_world
    no=linkcopy(o,'V58_SCENIC_GROVE_%02d'%i,mat);bpy.context.view_layer.update()
    h=footprint(no,True)
    # minimum root residual used only for scenic placement; screen native and prior candidate root hulls.
    low=[w for w in (no.matrix_world@v.co for v in no.data.vertices) if w.z<no.matrix_world.translation.z+1.2]
    if not low or any(not (60<=w.x<=135 and -135<=w.y<=-60) for w in low):
        rejected.append(dict(i=i,reason='outside extension'));bpy.data.objects.remove(no,do_unlink=True);continue
    res=[w.z-ground(w.x,w.y) for w in low];no.location.z-=min(res)+.07;bpy.context.view_layer.update()
    g,near=gap(h);rg=reserved_gap(h)
    if min(g,rg)<.10:
        rejected.append(dict(i=i,reason='protected or obstacle gap',gap=g,reserve_gap=rg));bpy.data.objects.remove(no,do_unlink=True);continue
    obs.append((no.name,h,bbox(h)));placed.append(dict(name=no.name,template=o.name,location=list(no.location),gap_m=g,reservation_gap_m=rg,initial_root_range_m=[min(res),max(res)]))
assert snapshot(old)==protected and sha(src)==lock
# First compare scene geometry only at the same lighting and camera.
for i in (0,1):render('v58_geometry_%d.png'%i,i)
# Lighting is separately changed, retaining original lighting objects and positions.
# Reduce world background strength for forest shade; add broad warm focal key and cool side fill.
world=scene.world
if world and world.use_nodes:
    for n in world.node_tree.nodes:
        if n.type=='BACKGROUND':n.inputs['Strength'].default_value*=.55
def light(name,loc,target,power,color,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='DISK';data.size=size
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
light('V58_scenic_warm_key',(96,-90,40),(94,-93,28),2400,(1,.82,.57),6)
light('V58_scenic_cool_fill',(80,-107,39),(90,-94,30),1100,(.57,.76,1),12)
bpy.ops.file.pack_all();dest=out/'v58_scenic_composition.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()));bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()));scene=bpy.context.scene;cam=scene.camera;camdata=cam.data
assert snapshot(old)==protected and sha(src)==lock
for i in (0,1,2):render('v58_lighting_%d.png'%i,i)
q=dict(status='SCENIC_EXTENSION_CANDIDATE_HOLD',source_sha256=lock,blender=bpy.app.version_string,protected_meshes_exact=len(old),extension_vertices=705,extension_triangles=1288,seam_samples=33,seam_max_delta_m=0,third=third,grove_placed=placed,grove_rejected=rejected,mesh_objects=sum(o.type=='MESH' for o in scene.objects),packed_images=sum(bool(i.packed_file) for i in bpy.data.images),external_images=[i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file],views=views,outputs={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.blend','.png')},limits=['Scenic extrapolation outside A3 only, not official terrain. No V47B actual pad, root 3D collision, species or crown fit. No D4, independent G2, runtime, formal adoption or main merge.'])
(out/'v58_qa.json').write_text(json.dumps(q,indent=2)+'\n');print(q)

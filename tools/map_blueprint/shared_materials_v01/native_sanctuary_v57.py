"""V57 isolated native composition study. No canonical placement, D4 or precision production.
Two scan visual proxies, V05 altar and V53 scenic-frame envelopes, protected existing native geometry.
Actual source Blender and provider archive are locked. No source save."""
import bpy,bmesh,sys,math,hashlib,json,struct
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.geometry import convex_hull_2d
src,inputs,out=map(Path,sys.argv[sys.argv.index('--')+1:])
out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lock='69789159a2f0502706fb0d1bc0e9f3a62fdb68dfea852fc81ee2b0d7ee86ce05'
assert bpy.app.version[:3]==(5,3,0) and sha(src)==lock
# Validate source bytes, provider MD5 and dependency list before import.
report=json.loads((inputs/'v55-report.json').read_text())
assert not report['errors'] and len(report['files'])==12
for row in report['files']:
    p=inputs/'v55-source'/row['path']; data=p.read_bytes()
    assert len(data)==row['bytes'] and sha(p)==row['sha256'] and hashlib.md5(data).hexdigest()==row['provider_md5']
treepath=inputs/'v55-source/island_tree_01/island_tree_01_1k.gltf'
assert sha(treepath)=='78e905a40670bfabb2760601d4d9a6c17193a50d68e6271c66893eb7bd75906d'
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()))
scene=bpy.context.scene
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
old=[o.name for o in scene.objects if o.type=='MESH']
assert len(old)==479
for n in old:bpy.data.objects[n].data.calc_loop_triangles()
assert sum(len(bpy.data.objects[n].data.loop_triangles) for n in old)==926746
protected=snapshot(old)
terrain=bpy.data.objects['A3 provisional reconstructed terrain'];inv=terrain.matrix_world.inverted()
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

# Existing reserve proxy and original objects are retained even if pre-existing conflicts exist.
obs=[]
for name in old:
    o=bpy.data.objects[name]
    if o==terrain:continue
    h=footprint(o,o.name.startswith(('V18_T_','V18_D_','V19_BG_')))
    obs.append((name,h,bbox(h)))
# Create camera and study lighting on separate objects. Matched baseline/candidate lighting.
camdata=bpy.data.cameras.new('V57_study_camera');cam=bpy.data.objects.new('V57_study_camera',camdata);scene.collection.objects.link(cam);scene.camera=cam
camdata.lens=34;camdata.clip_end=350
def light(name,loc,target,power,color,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='DISK';data.size=size
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
light('V57_warm_canopy_opening',(89,-87,46),(94,-93,28),1600,(1,.82,.54),8)
light('V57_cool_ambient',(62,-62,44),(75,-82,30),850,(.65,.83,1),16)
views=[((35,-57,35),(76,-82,32),32),((83,-84,30.1),(94,-93,30),28),((64,-57,67),(73,-82,28),38)]
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.cycles.use_denoising=True
scene.render.resolution_x=768;scene.render.resolution_y=432;scene.render.resolution_percentage=100
def render(name,i):
    e,a,l=views[i];cam.location=e;cam.rotation_euler=(Vector(a)-cam.location).to_track_quat('-Z','Y').to_euler();camdata.lens=l
    scene.render.filepath=str((out/name).resolve());bpy.ops.render.render(write_still=True)
for i in (0,1):render('v57_baseline_%d.png'%i,i)
# Native source importer; source tree consists of three material primitives. Correct JPEG alpha from exact separate PNG.
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(treepath.resolve()))
made=list(set(bpy.data.objects)-before);assert len(made)>0 and all(o.type=='MESH' for o in made)
for o in made:o.data.calc_loop_triangles()
assert sum(len(o.data.loop_triangles) for o in made)==1599403
leafmats=[m for o in made for m in o.data.materials if m and 'leaves' in m.name.lower()]
assert leafmats
alpha=next(inputs.rglob('island_tree_01_leaves_alpha_1k.png'))
for mat in set(leafmats):
    nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
    tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(alpha.resolve()),check_existing=True);tex.image.colorspace_settings.name='Non-Color';links.new(tex.outputs['Color'],bs.inputs['Alpha'])
    mat.surface_render_method='DITHERED'
# Native placement uses V56's verified uniform fit (glTF +41 degrees corresponds to Blender -41).
orig={o.name:o.matrix_world.copy() for o in made}
pivot=Vector((.03152092546224594,-.06966163218021393,0))
placements=[('V57_hero_A',45.876293383167,-75.88676445659047,0),('V57_hero_B',94,-81,90)]
records=[];tree_objects=[]
for i,(name,x,y,yaw) in enumerate(placements):
    z=hit(x,y)
    trans=Matrix.Translation((x,y,z))@Matrix.Rotation(math.radians(yaw-41),4,'Z')@Matrix.Scale(2.63,4)@Matrix.Translation(-pivot)
    objs=[]
    for j,o in enumerate(made):
        no=o if i==0 else bpy.data.objects.new(name+'_'+str(j),o.data)
        if i==1:scene.collection.objects.link(no)
        # original keys saved by index to avoid renaming issue
        if i==0: o['v57_original_matrix']=[a for row in orig[o.name] for a in row]
        mm=Matrix([o['v57_original_matrix'][k:k+4] for k in range(0,16,4)])
        no.matrix_world=trans@mm;no.name=name+'_'+str(j);objs.append(no);tree_objects.append(no)
    bpy.context.view_layer.update()
    # low wood vertices (<=1.2m) and full crown hull; source ground patch kept.
    xyz=[o.matrix_world@v.co for o in objs for v in o.data.vertices]
    low=[Vector((v.x,v.y)) for v in xyz if v.z<=z+1.2]
    h=[low[k] for k in convex_hull_2d(low)]
    bb=bbox(h);near=[];min_gap=1000.;nearest=None
    for on,k,kb in obs:
        if bboxgap(bb,kb)>min_gap:continue
        gap=poly_gap(h,k)
        if gap<min_gap:min_gap=gap;nearest=on
        if gap<.02:near.append(on)
    rootv=[v for v in xyz if v.z<=z+.15]
    res=[v.z-hit(v.x,v.y) for v in rootv]
    records.append(dict(name=name,location=[x,y,z],extra_yaw=yaw,root_hull_gap_to_existing_m=min_gap,nearest=nearest,root_overlap_names=near,root_sample_min_m=min(res),root_sample_max_m=max(res),root_samples=len(res)))
# V05 body and V53 ring geometry as separate, plainly marked scene proxies; not V53 exact GLB.
mat=bpy.data.materials.new('V57_stone_proxy');mat.diffuse_color=(.29,.32,.25,1);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.29,.32,.25,1);bs.inputs['Roughness'].default_value=.86
pad=Vector((93.9431596631828,-93.0743278729908,27.988129971478276));d=Vector((.788631932636555,-.6148655745981655,0));n=Vector((.6148655745981655,.788631932636555,0))
def pos(x,y,z):return pad+n*x+d*y+Vector((0,0,z))
def mesh(name,v,f):
    m=bpy.data.meshes.new(name);m.from_pydata([pos(*p) for p in v],[],f);m.update();bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(m);bm.free()
    o=bpy.data.objects.new(name,m);scene.collection.objects.link(o);m.materials.append(mat);return o
def block(name,x,y,z0,z1,w,dep):
    v=[(x+a*w/2,y+b*dep/2,z) for z in (z0,z1) for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]]
    return mesh(name,v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
for nm,w,dep,z0,z1 in [('plinth',2.4,1.2,0,.22),('body',2.1,1.02,.22,1.02),('capstone',2.32,1.16,1.02,1.24)]:block('V57_ALTAR_PROXY_'+nm,0,.8,z0,z1,w,dep)
for side in (-1,1):block('V57_ARCH_PROXY_pier_'+str(side),side*1.65,1.2,0,2.02,.7,.8)
for i in range(9):
    a=i*math.pi/9+(.004 if i else 0);b=(i+1)*math.pi/9-(.004 if i<8 else 0);ang=[a+(b-a)*j/4 for j in range(5)]
    p=[(1.94*math.cos(t),2.02+1.72*math.sin(t)) for t in ang]+[(1.39*math.cos(t),2.02+1.24*math.sin(t)) for t in reversed(ang)]
    v=[(x,y,z) for y in (.89,1.51) for x,z in p];k=len(p);f=[]
    for j in range(4):
        aa=j;bb=j+1;cc=k-2-j;dd=k-1-j
        f.extend([(aa,bb,cc),(aa,cc,dd),(k+aa,k+cc,k+bb),(k+aa,k+dd,k+cc)])
    for j in range(k):f.append((j,(j+1)%k,(j+1)%k+k,j+k))
    mesh('V57_ARCH_PROXY_wedge_%02d'%i,v,f)
bpy.context.view_layer.update()
assert snapshot(old)==protected and sha(src)==lock
# Save/reopen independent Blender checkpoint and render the composition. Prior native terrain is not V47B flat pad.
bpy.ops.file.pack_all();dest=out/'v57_sanctuary_composition.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()));bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()));scene=bpy.context.scene;cam=scene.camera;camdata=cam.data
assert snapshot(old)==protected and sha(src)==lock
for i in (0,1,2):render('v57_candidate_%d.png'%i,i)
q=dict(status='ISOLATED_NATIVE_COMPOSITION_STUDY_HOLD',source_sha256=lock,blender=bpy.app.version_string,protected_meshes_exact=len(old),source_scan_triangles_per_tree=1599403,tree_instances=2,placement_records=records,views=views,all_meshes=sum(o.type=='MESH' for o in scene.objects),packed_images=sum(bool(i.packed_file) for i in bpy.data.images),external_images=[i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file],outputs={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.png','.blend')},limits=['Coastal scan proxies, not V05 crown fit; exact V47B terrain absent, altar and arch simplified scenic proxies, no structural/collision or D4 acceptance.','Original existing meshes retained including conflicts. Root plan gaps and sampled ground only. High triangle count; no Android, independent G2, canon adoption or main merge.'])
(out/'v57_qa.json').write_text(json.dumps(q,indent=2)+'\n');print(q)

"""V71 bounded Irish oakwood-inspired local composition feasibility. Existing meshes only, no precision authoring."""
import bpy,sys,math,hashlib,json,random,collections
from pathlib import Path
from array import array
from mathutils import Vector,Matrix
from mathutils.geometry import convex_hull_2d
src,out=map(Path,sys.argv[sys.argv.index('--')+1:])
out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lock='3c4d31a33e7b5fd5a10dbb7cfd3920a965f738a2196871515ac31c1120e0964d'
assert bpy.app.version[:3]==(5,3,0) and sha(src)==lock
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()))
ext_name='V58_SCENIC_ONLY_terrain_extension'
src_name='A3 provisional reconstructed terrain'
attr='V19_ground_color'
def digest(data,prop,count,code):
    a=array(code,[0])*count
    if count:data.foreach_get(prop,a)
    return hashlib.sha256(a.tobytes()).hexdigest()
def snap():
    result={};cache={}
    for o in bpy.context.scene.objects:
        if o.type!='MESH':continue
        m=o.data
        if m.name not in cache:
            colors={a.name:(a.domain,a.data_type,digest(a.data,'color',len(a.data)*4,'f')) for a in m.color_attributes}
            uv={a.name:digest(a.data,'uv',len(a.data)*2,'f') for a in m.uv_layers}
            cache[m.name]=(digest(m.vertices,'co',len(m.vertices)*3,'f'),digest(m.loops,'vertex_index',len(m.loops),'i'),digest(m.polygons,'loop_start',len(m.polygons),'i'),digest(m.polygons,'loop_total',len(m.polygons),'i'),digest(m.polygons,'material_index',len(m.polygons),'i'),uv,colors,tuple(a.name if a else None for a in m.materials))
        result[o.name]=(cache[m.name],tuple(tuple(r) for r in o.matrix_world),o.hide_render,tuple(s.material.name if s.material else None for s in o.material_slots))
    return result
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



scene=bpy.context.scene;terrain=bpy.data.objects[src_name];ext=bpy.data.objects[ext_name]
old=snap();assert len(old)==523
assert ext.data.color_attributes.get(attr) and terrain.data.color_attributes.get(attr)
def ray(o,x,y):
    inv=o.matrix_world.inverted()
    ok,p,n,i=o.ray_cast(inv@Vector((x,y,100)),inv.to_3x3()@Vector((0,0,-1)),distance=200)
    return float((o.matrix_world@p).z) if ok else None
def ground(x,y):
    if -100<=x<=100 and -100<=y<=0:return ray(terrain,x,y)
    if 60<=x<=135 and -135<=y<=-60:return ray(ext,x,y)
    return None
# Preserve full footprint of low existing assets, low trunk band for trees.
obs=[]
groups=[('V57_hero_A',28.65093231201172),('V57_hero_B',27.257186889648438),('V58_SCENIC_C_',28.70697135925293)]
for name in old:
    o=bpy.data.objects[name]
    if name in (src_name,ext_name) or any(name.startswith(p) for p,z in groups):continue
    h=footprint(o,name.startswith(('V18_T_','V18_D_','V19_BG_','V58_SCENIC_GROVE_')))
    obs.append((name,h,bbox(h)))
for prefix,z in groups:
    p=[Vector((w.x,w.y)) for n in old if n.startswith(prefix) for w in (bpy.data.objects[n].matrix_world@v.co for v in bpy.data.objects[n].data.vertices) if w.z<=z+1.2]
    assert len(p)>=3,prefix
    hh=[p[i] for i in convex_hull_2d(p)];obs.append((prefix,hh,bbox(hh)))
def gap(h):
    bb=bbox(h);g=1e6;near=None
    for n,p,b in obs:
        if bboxgap(bb,b)>g:continue
        s=poly_gap(h,p)
        if s<g:g=s;near=n
    return g,near
# Use linked data already present in exact V69; no new mesh or material authoring.
prefixes={'rock':('V21_R_',),'fern':('V18_0_','V18_1_','V18_2_','V18_3_'),'moss':('V21_M_',),'stump':('V21_U_',)}
templates={};template_info={}
for kind,prefix in prefixes.items():
    unique={}
    for name in sorted(old):
        if name.startswith(prefix):
            o=bpy.data.objects[name];unique.setdefault(o.data.name,o)
    assert unique,kind
    templates[kind]=[]
    for o in unique.values():
        m=o.data;m.calc_loop_triangles()
        vs=[v.co.copy() for v in m.vertices];mn=Vector(tuple(min(v[i] for v in vs) for i in range(3)));mx=Vector(tuple(max(v[i] for v in vs) for i in range(3)))
        pivot=Vector(((mn.x+mx.x)/2,(mn.y+mx.y)/2,mn.z));width=max(mx.x-mn.x,mx.y-mn.y)
        assert width>1e-5 and mx.z>mn.z
        xy=[Vector((v.x-pivot.x,v.y-pivot.y)) for v in vs];hh=[xy[i] for i in convex_hull_2d(xy)]
        low=[v-pivot for v in vs if v.z<=mn.z+min(.08,(mx.z-mn.z)*.12)]
        assert len(hh)>=3 and low
        templates[kind].append((o,pivot,width,hh,low,len(m.loop_triangles)))
        template_info[o.name]={'kind':kind,'mesh':m.name,'triangles':len(m.loop_triangles),'source_width_m':width}
assert len(templates['rock'])>=4 and len(templates['fern'])>=2
patches=[('P01',78,-91,3.2),('P02',80,-97,4),('P03',89,-75,3.8),('P04',103,-82,4),('P05',103,-91,3.8),('P06',108,-103,4),('P07',87,-111,4),('P08',70,-91,3.8)]
targets={'rock':3,'stump':1,'fern':10,'moss':14}
widths={'rock':(.65,1.45),'stump':(.75,1.3),'fern':(.55,1.05),'moss':(.4,.8)}
rng=random.Random(2026112671);placed=[];reject=collections.Counter();counts=collections.Counter();patch_counts={};triangles=0
collection=bpy.data.collections.new('V71_IRISH_FLOOR_FEASIBILITY');scene.collection.children.link(collection)
for pid,cx,cy,r in patches:
    patch_counts[pid]={}
    for kind,goal in targets.items():
        n=0
        for attempt in range(goal*48):
            if n>=goal:break
            o,pivot,w,hh,low,tri=rng.choice(templates[kind])
            if triangles+tri>600000:reject['triangle_budget']+=1;continue
            scale=rng.uniform(*widths[kind])/w
            ang=rng.uniform(0,2*math.pi);rad=r*math.sqrt(rng.random());x=cx+rad*math.cos(ang);y=cy+rad*math.sin(ang)
            yaw=rng.uniform(0,2*math.pi);rot=Matrix.Rotation(yaw,3,'Z')
            h=[]
            for p in hh:
                q=rot@Vector((p.x*scale,p.y*scale,0));h.append(Vector((q.x+x,q.y+y)))
            rg=reserved_gap(h)
            if rg<.10:reject['protected']+=1;continue
            g,near=gap(h)
            if g<.04:reject['existing_or_new_footprint']+=1;continue
            z=ground(x,y)
            if z is None or any(ground(p.x,p.y) is None for p in h):reject['tile_edge']+=1;continue
            rr=[]
            for p in low:
                q=rot@(p*scale);height=ground(x+q.x,y+q.y)
                if height is None:break
                rr.append(z+q.z-height)
            if len(rr)!=len(low):reject['root_outside']+=1;continue
            burial=.055 if kind in ('rock','stump') else .025
            offset=-min(rr)-burial
            residual=[p+offset for p in rr]
            if max(residual)>.22 or min(residual)<-.08:reject['root_residual']+=1;continue
            no=bpy.data.objects.new('V71_%s_%s_%03d'%(pid,kind,n),o.data);collection.objects.link(no)
            no.matrix_world=Matrix.Translation((x,y,z+offset))@rot.to_4x4()@Matrix.Scale(scale,4)@Matrix.Translation(-pivot)
            obs.append((no.name,h,bbox(h)));placed.append({'name':no.name,'source':o.name,'mesh':o.data.name,'kind':kind,'patch':pid,'matrix':[list(row) for row in no.matrix_world],'reserve_gap_m':rg,'obstacle_gap_m':g,'nearest':near,'low_sample_count':len(rr),'root_residual_m':[min(residual),max(residual)],'triangles':tri})
            n+=1;triangles+=tri;counts[kind]+=1
        patch_counts[pid][kind]=n
assert sha(src)==lock
bpy.context.view_layer.update()
s=snap();assert all(s[k]==v for k,v in old.items())
assert all(bpy.data.objects[a['name']].data==bpy.data.objects[a['source']].data for a in placed)
assert triangles<=600000
assert placed,'no viable placements: stop rather than rerun'
dest=out/'v71_irish_floor_feasibility.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()))
scene=bpy.context.scene;s=snap();assert all(s[k]==v for k,v in old.items()) and sha(src)==lock
assert all(bpy.data.objects[a['name']].data==bpy.data.objects[a['source']].data and max(abs(x-y) for row,b in zip(bpy.data.objects[a['name']].matrix_world,a['matrix']) for x,y in zip(row,b))<1e-5 for a in placed)
q={'status':'BOUNDED_EXISTING_ASSET_COMPOSITION_FEASIBILITY','source_sha256':lock,'blender':bpy.app.version_string,'protected_meshes_exact':len(old),'counts':dict(counts),'patch_counts':patch_counts,'placed':placed,'rejections':dict(reject),'source_templates':template_info,'added_instance_triangles':triangles,'budget':600000,'unique_new_mesh_data':0,'min_reserve_gap_m':min(a['reserve_gap_m'] for a in placed),'min_obstacle_gap_m':min(a['obstacle_gap_m'] for a in placed),'native_sha256':sha(dest),'limits':['Provisional local composition only; D4 independent review not performed. No precision mesh authoring, canonical world placement, actual collision, Android or formal adoption. Full planar hull and low-root vertex samples are conservative, not physics. Existing materials, light and geometry unchanged.']}
(out/'v71_qa.json').write_text(json.dumps(q,indent=2)+'\n')
# Exact V58 camera definitions for two matched views; no light adjustment.
views=[((78.1705210104517,-80.77701638102749,0),(93.9431596631828,-93.0743278729908,30.988129971478276),22),((83,-84,30.1),(94,-93,30),28),((71,-73,53),(96,-96,32),32)]
pad=Vector((93.9431596631828,-93.0743278729908,27.988129971478276));d=Vector((.788631932636555,-.6148655745981655,0));e=pad-d*20;e.z=ground(e.x,e.y)+2.15
views[0]=(tuple(e),tuple(pad+Vector((0,0,3))),22)
cam=scene.camera
for i in (0,2):
    a,b,l=views[i];cam.location=a;cam.rotation_euler=(Vector(b)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=l
    scene.render.filepath=str((out/f'v71_view_{i}.png').resolve());bpy.ops.render.render(write_still=True)
q['outputs']={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.blend','.png')}
(out/'v71_qa.json').write_text(json.dumps(q,indent=2)+'\n')
print({k:v for k,v in q.items() if k!='placed'})

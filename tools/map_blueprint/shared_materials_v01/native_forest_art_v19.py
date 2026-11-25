"""V19 isolated native art study, not final map or full V15C equivalence.
Preserve V18 object geometry/transforms; change terrain material and canopy lighting,
place bounded background trees outside reserved corridors using actual mesh bounds."""
import bpy,sys,math,random,json,hashlib
from pathlib import Path
from mathutils import Vector
src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lock='af449df826519bd8568452fd1069a7e69e23aa98823dd9a1397ab16ef4accd4d'
assert bpy.app.version[:3]==(5,3,0) and sha(src)==lock
dst=out/'forest_v19_native_art.blend';assert not dst.exists()
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()))
scene=bpy.context.scene
def stats():
    oo=[o for o in bpy.context.scene.objects if o.type=='MESH']
    for o in oo:o.data.calc_loop_triangles()
    return dict(mesh_objects=len(oo),triangles=sum(len(o.data.loop_triangles) for o in oo),packed_images=sum(bool(i.packed_file) for i in bpy.data.images),external_images=[i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file])
before=stats();assert before['mesh_objects']==399 and before['triangles']==758480 and not before['external_images']
def geom(o):
    h=hashlib.sha256()
    import struct
    for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
    for p in o.data.polygons:h.update(struct.pack('<I',len(p.vertices)));h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
    return (h.hexdigest(),tuple(tuple(r) for r in o.matrix_world))
originals={o.name:geom(o) for o in scene.objects if o.type=='MESH'}
terrain=bpy.data.objects['A3 provisional reconstructed terrain']
def distseg(p,a,b):
    vx,vy=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((p[0]-a[0])*vx+(p[1]-a[1])*vy)/(vx*vx+vy*vy)))
    return math.hypot(p[0]-a[0]-t*vx,p[1]-a[1]-t*vy)
route=((-205,140),(90,-90))
# Local reservations from the V14 provisional scene; conservative circle + line clearances.
reserved=[((67.536852,-72.486359),11),((45.876293,-75.886764),8),((49.408698,-58.352544),10),((93.943160,-93.074328),7)]
rays=[((65.4663,-80.2138),(45.876293,-75.886764),4),((65.4663,-80.2138),(93.943160,-93.074328),3)]
def protected_gap(x,y,r):
    return min([distseg((x,y),*route)-5-r]+[math.hypot(x-c[0],y-c[1])-rr-r for c,rr in reserved]+[distseg((x,y),a,b)-rr-r for a,b,rr in rays])
def radius(o):
    return max(math.hypot((o.matrix_world@Vector(v))[0]-o.location.x,(o.matrix_world@Vector(v))[1]-o.location.y) for v in o.bound_box)
def hit(x,y):
    ok,p,n,i=terrain.ray_cast(Vector((x,y,100)),Vector((0,0,-1)),distance=200)
    assert ok,(x,y)
    return p,n
trees=[o for o in scene.objects if o.name.startswith(('V18_T_','V18_D_'))]
assert len(trees)==75
templates=[trees[0].data,next(o.data for o in trees if o.name.startswith('V18_D_'))]
obstacles=[(o.location.x,o.location.y,radius(o)) for o in scene.objects if o.type=='MESH' and o!=terrain]
rng=random.Random(2026112519);placed=[]
# Distinct background bands inside existing provisional tile. No extension into adjacent areas.
for i in range(1800):
    if len(placed)>=18:break
    if i%2==0:x,y=rng.uniform(25,91),rng.uniform(-94,-70)
    else:x,y=rng.uniform(76,94),rng.uniform(-69,-23)
    m=templates[i%2];s=rng.uniform(1.30,1.80)
    r=max(math.hypot(v.co.x,v.co.y) for v in m.vertices)*s
    if x-r< -100 or x+r>100 or y-r< -100 or y+r>0:continue
    g=protected_gap(x,y,r)
    if g<.75:continue
    gap=min(math.hypot(x-a,y-b)-r-rr for a,b,rr in obstacles)
    if gap<.20:continue
    p,n=hit(x,y)
    if n.z<math.cos(math.radians(20)):continue
    o=bpy.data.objects.new('V19_BG_%02d'%len(placed),m);scene.collection.objects.link(o)
    bottom=min(v.co.z for v in m.vertices)
    o.location=(x,y,p.z-bottom*s-.02);o.scale=(s,)*3;o.rotation_euler.z=rng.uniform(0,2*math.pi)
    obstacles.append((x,y,r));placed.append(dict(name=o.name,location=list(o.location),scale=s,yaw=o.rotation_euler.z,protected_gap=g,obstacle_gap=gap,ground_z=p.z))
assert len(placed)>=4,len(placed)
# Native vertex-color modulation of the original photo ground. No terrain geometry or UV changes.
me=terrain.data
c=me.color_attributes.new(name='V19_ground_color',type='FLOAT_COLOR',domain='POINT')
for v in me.vertices:
    x,y,z=v.co;d=distseg((x,y),*route)
    t=max(0,min(1,(d-1.1)/5.0));t=t*t*(3-2*t)
    patch=.5+.25*math.sin(x*.24+y*.16)+.15*math.cos(y*.37-x*.18)
    green=(.77+.10*patch,.94+.05*patch,.66+.14*patch)
    road=(.98,.90,.77)
    c.data[v.index].color=tuple((1-t)*a+t*b for a,b in zip(road,green))+(1,)
mat=me.materials[0];nt=mat.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
base=bs.inputs['Base Color'];assert base.is_linked
source=base.links[0].from_socket
col=nt.nodes.new('ShaderNodeVertexColor');col.layer_name=c.name
mul=nt.nodes.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1
nt.links.new(source,mul.inputs[1]);nt.links.new(col.outputs['Color'],mul.inputs[2]);nt.links.new(mul.outputs[0],base)
# Low-energy art-directed leaf fill; use existing base-color signal, retain all alpha links.
leaf=[]
for mat in {m for o in trees for m in o.data.materials if m and 'leaf' in m.name.lower()}:
    if not mat.use_nodes:continue
    for bs in [n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED']:
        b=bs.inputs['Base Color'];e=bs.inputs.get('Emission Color');s=bs.inputs.get('Emission Strength')
        if e is None or s is None:continue
        if b.is_linked:mat.node_tree.links.new(b.links[0].from_socket,e)
        else:e.default_value=b.default_value
        s.default_value=.045;leaf.append(mat.name)
assert leaf, 'no leaf material match'
scene.world.node_tree.nodes.get('Background').inputs[1].default_value=1.05
sun=bpy.data.lights['Warm afternoon sun'];sun.energy=1.9;sun.angle=.10
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=800;scene.render.resolution_y=450;scene.render.resolution_percentage=100
views=[((8,35.00075988769531,36),(12.2,33.3,38.5)),((18,34.22273864746094,37),(12,33.2,42))]
def camera(i):
    co=bpy.context.scene.camera;e,a=views[i];cv=lambda v:Vector((v[0],-v[2],v[1]))
    co.location=cv(e);co.rotation_euler=(cv(a)-co.location).to_track_quat('-Z','Y').to_euler()
bpy.context.view_layer.update()
assert all(geom(bpy.data.objects[n])==v for n,v in originals.items())
camera(0);bpy.ops.file.pack_all();mid=stats();assert mid['mesh_objects']==399+len(placed) and not mid['external_images']
bpy.ops.wm.save_as_mainfile(filepath=str(dst.resolve()))
bpy.ops.wm.open_mainfile(filepath=str(dst.resolve()))
scene=bpy.context.scene;after=stats();assert mid==after
assert all(geom(bpy.data.objects[n])==v for n,v in originals.items())
for i in range(2):
    camera(i);scene.render.filepath=str((out/('forest_v19_view_%d.png'%(i+1))).resolve());bpy.ops.render.render(write_still=True)
assert sha(src)==lock
q=dict(status='NATIVE_ART_STUDY_NOT_ADOPTED',source_sha256=lock,blender=bpy.app.version_string,before=before,after=after,original_mesh_geometry_transforms_exact=len(originals),ground_color_vertices=len(me.vertices) if False else len(bpy.data.objects['A3 provisional reconstructed terrain'].data.vertices),leaf_materials=sorted(set(leaf)),background_trees=placed,views=views,limitations=['Original V18 subset, no exact V15C transfer; conservative bounding circle clearance, not collision/navmesh; foreground incomplete; nonphysical low-energy leaf fill; no independent G2 or Android.'])
q['sha256']={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.png','.blend')}
(out/'qa.json').write_text(json.dumps(q,indent=2)+'\n');print(q)

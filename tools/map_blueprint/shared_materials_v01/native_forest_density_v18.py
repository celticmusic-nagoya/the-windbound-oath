"""Independent native lighting/composition study. Never modify original pilot or full V15C.
All 391 source-derived vegetation placements; original pilot mesh data, not V15C geometry."""
import bpy,sys,math,hashlib,json,base64,zlib,struct,collections
from pathlib import Path
from mathutils import Vector
src,manifest,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert bpy.app.version[:3]==(5,3,0)
assert sha(src)=='64a959e42ab7e3b97ce7308de8dd9b73e840ab91f7c074d069662ce72d094504'
raw=zlib.decompress(base64.b64decode(manifest.read_text().strip(),validate=True))
assert hashlib.sha256(raw).hexdigest()=='fe58db17c2e8d8b6a3706c857a615999980673c5f104c7bd3b2987da5ba106bf'
rows=list(struct.iter_unpack('<cHhhhHH',raw))
counts=collections.Counter(k.decode() for k,*_ in rows)
assert counts==dict(T=45,D=30,S=48,G=130,M=90,**{'0':12,'1':12,'2':12,'3':12})
assert not (out/'forest_v18_native_density.blend').exists()
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()))
scene=bpy.context.scene
def stats():
    oo=[o for o in bpy.context.scene.objects if o.type=='MESH']
    for o in oo:o.data.calc_loop_triangles()
    return dict(mesh_objects=len(oo),triangles=sum(len(o.data.loop_triangles) for o in oo),packed_images=sum(bool(i.packed_file) for i in bpy.data.images),external_images=[i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file])
before=stats();assert before['mesh_objects']==89 and before['triangles']==296578 and not before['external_images'],before
def fingerprint(o):
    me=o.data;me.calc_loop_triangles()
    return [len(me.vertices),len(me.loop_triangles),list(o.matrix_world)]
templates={k:bpy.data.objects[n].data for k,n in {'T':'T001','D':'D046','S':'S088','G':'G126','M':'M261','0':'F001','1':'F013','2':'F025','3':'F039'}.items()}
assert all(m is not None for m in templates.values())
protected={o.name:(o.data,len(o.data.vertices),len(o.data.polygons),tuple(tuple(r) for r in o.matrix_world)) for o in scene.objects if o.type=='MESH' and not (len(o.name)==4 and o.name[0] in 'TDSGMF' and o.name[1:].isdigit())}
assert len(protected)==8,protected.keys()
# Only remove temporary prior subset instances from this isolated in-memory copy.
for o in list(scene.objects):
    if o.type=='MESH' and len(o.name)==4 and o.name[0] in 'TDSGMF' and o.name[1:].isdigit():
        bpy.data.objects.remove(o,do_unlink=True)
placed={}
for kb,i,x,y,z,a,s in rows:
    k=kb.decode();name='V18_'+k+f'_{i:03d}'
    assert name not in placed
    o=bpy.data.objects.new(name,templates[k]);scene.collection.objects.link(o)
    loc=(x/100,-z/100,y/100);angle=a*2*math.pi/65536;scale=s/10000
    o.location=loc;o.rotation_euler=(0,0,angle);o.scale=(scale,)*3
    placed[name]=(loc,angle,scale)
bpy.context.view_layer.update()
assert all((bpy.data.objects[n].data,len(bpy.data.objects[n].data.vertices),len(bpy.data.objects[n].data.polygons),tuple(tuple(r) for r in bpy.data.objects[n].matrix_world))==v for n,v in protected.items())
# The existing matched views are retained. First render expanded scene in unchanged pilot lighting.
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.render.resolution_x=640;scene.render.resolution_y=360;scene.render.resolution_percentage=100
co=scene.camera;views=[((8,35.00075988769531,36),(12.2,33.3,38.5)),((18,34.22273864746094,37),(12,33.2,42))]
def cv(v):return Vector((v[0],-v[2],v[1]))
def camera(i):
    e,a=views[i];co.location=cv(e);co.rotation_euler=(cv(a)-co.location).to_track_quat('-Z','Y').to_euler()
def render(i,name):
    camera(i);scene.render.filepath=str((out/name).resolve());bpy.ops.render.render(write_still=True)
render(0,'density_same_light_view1.png');render(1,'density_same_light_view2.png')
# Alternative lighting only, no mesh or transform edit. Increase ambient fill, softer sunlight.
bg=scene.world.node_tree.nodes.get('Background')
bg.inputs[0].default_value=(.50,.64,.78,1);bg.inputs[1].default_value=.8
sun=bpy.data.lights['Warm afternoon sun'];sun.energy=1.8;sun.angle=.13;sun.color=(1,.90,.75)
camera(0);bpy.ops.file.pack_all()
mid=stats();assert mid['mesh_objects']==399 and not mid['external_images'],mid
# Native output is an independent copy, original bytes untouched.
bpy.ops.wm.save_as_mainfile(filepath=str((out/'forest_v18_native_density.blend').resolve()))
bpy.ops.wm.open_mainfile(filepath=str((out/'forest_v18_native_density.blend').resolve()))
scene=bpy.context.scene;co=scene.camera
after=stats();assert mid==after,(mid,after)
max_pos=max((Vector(bpy.data.objects[n].location)-Vector(v[0])).length for n,v in placed.items())
max_yaw=max(abs(bpy.data.objects[n].rotation_euler.z-v[1]) for n,v in placed.items())
max_scale=max(max(abs(x-v[2]) for x in bpy.data.objects[n].scale) for n,v in placed.items())
assert max_pos<1e-5 and max_yaw<1e-5 and max_scale<1e-5,(max_pos,max_yaw,max_scale)
render(0,'density_fill_view1.png');render(1,'density_fill_view2.png')
assert sha(src)=='64a959e42ab7e3b97ce7308de8dd9b73e840ab91f7c074d069662ce72d094504'
q=dict(status='NATIVE_DENSITY_LIGHTING_STUDY_NOT_FULL_V15C',source_pilot_sha256=sha(src),source_full_glb_sha256='09366ffaf5b1f6657b1b9ca158c9681d0d52537a4a90bf94f7ac25ec6f2162f1',manifest_sha256=hashlib.sha256(raw).hexdigest(),counts=dict(counts),before=before,after=after,protected_objects=sorted(protected),reopen_residual=dict(position_m=max_pos,yaw_rad=max_yaw,scale=max_scale),quantization=dict(position_per_axis_m=.005,yaw_rad=math.pi/65536,scale=.00005),blender=bpy.app.version_string,views=views,limits=['Original pilot meshes, 391 vegetation placements; no V15C warp or exact LOD equivalence. 70 moss, seven rocks, one stump absent relative to full V15C. No navigation, independent G2 or Android proof.'])
q['sha256']={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.png','.blend')}
(out/'qa.json').write_text(json.dumps(q,indent=2)+'\n')
print(q)

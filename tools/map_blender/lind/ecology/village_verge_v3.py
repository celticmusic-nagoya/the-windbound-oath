import bpy, sys, math, hashlib, json, random
from pathlib import Path
from mathutils import Vector, Matrix
from array import array
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def metrics(engine, values, actual, tolerance, uncertainty, lower=None):
    sys.path[:0]=[str(engine/'tools'),str(engine/'tools/production_qa')]
    from blueprint_engine.residual import evaluate
    return evaluate(dict(values=values,tolerances=tolerance,uncertainty={k:0 for k in values},lower_bound=lower or {}),dict(actual=actual,uncertainty=uncertainty))
def camera(name,eye,aim,lens=35):
    d=bpy.data.cameras.new(name); o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o)
    o.location=eye;o.rotation_euler=(Vector(aim)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=500
    return o
def render_setup(scene):
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.cycles.use_denoising=True
    scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
def render(scene,cam,path):
    scene.camera=cam;scene.render.filepath=str(path.resolve());bpy.ops.render.render(write_still=True)
def simplemat(name,color):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    b=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=.91
    return m
def finish(out,q):
    q['outputs']={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.suffix in ('.blend','.glb','.png')}
    (out/'qa.json').write_text(json.dumps(q,indent=2)+'\n')

pkg,photos,out,engine=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
assert bpy.app.version[:3]==(5,3,0)
# RILDE_CORE_AREA_SURFACES_V01 (blob 21b2804d...), recorded V01 plateau, 2.5m grid.
# Patch inside provisional IF03 eastbound route. Original bytes and canonical transform unresolved.
def plateau(x,y):return 18+3*math.sin(math.pi*y/300)+.006*(x+175)+.85*math.sin((x+175)/74)*math.sin(y/85)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;origin=(100,0,plateau(100,0));N=9
v=[(i*2.5-10,j*2.5-10,plateau(origin[0]+i*2.5-10,j*2.5-10)-origin[2]) for j in range(N) for i in range(N)]
f=[]
for j in range(N-1):
    for i in range(N-1):
        a=j*N+i;f.extend([(a,a+1,a+N+1),(a,a+N+1,a+N)])
m=bpy.data.meshes.new('V3_village_reconstructed_patch');m.from_pydata(v,[],f);m.update()
ground=bpy.data.objects.new(m.name,m);scene.collection.objects.link(ground)
uv=m.uv_layers.new(name='UVMap')
for poly in m.polygons:
    for l in poly.loop_indices:
        p=m.vertices[m.loops[l].vertex_index].co;uv.data[l].uv=(p.x/2.5,p.y/2.5)
def photo(name,asset):
    src=photos/asset;manifest=json.loads((src/'manifest.json').read_text());assert manifest['license']=='CC0'
    mat=simplemat(name,(.3,.3,.3));nt=mat.node_tree;n=nt.nodes;l=nt.links;bs=next(x for x in n if x.type=='BSDF_PRINCIPLED')
    for role,key in [('basecolor','Base Color'),('roughness','Roughness'),('normal','Normal')]:
        rec=manifest['textures'][role];p=src/rec['path'];assert sha(p)==rec['sha256']
        img=bpy.data.images.load(str(p.resolve()),check_existing=True);img.colorspace_settings.name=rec['color_space'];img.pack()
        node=n.new('ShaderNodeTexImage');node.image=img
        if role=='normal':
            nm=n.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.7;l.new(node.outputs['Color'],nm.inputs['Color']);l.new(nm.outputs['Normal'],bs.inputs[key])
        else:l.new(node.outputs['Color'],bs.inputs[key])
    return mat
m.materials.append(photo('grass','sparse_grass'));m.materials.append(photo('road','stony_dirt_path'))
for p in m.polygons:p.material_index=int(abs(p.center.y)<2.5)
# Existing assets from exact branch manifest, not the earlier historical artifact.
manifest=json.loads((pkg/'manifest.v2.json').read_text());families={'turf':('eco_turf_meadow_a_LOD1',28),'grass':('eco_grass_tuft_short_LOD1',18),'daisy':('eco_flower_daisy_clump_LOD1',12),'spike':('eco_flower_spike_clump_LOD1',10),'moss':('eco_moss_cushion_a_LOD0',8)}
templates={};source_sha={}
for kind,(name,count) in families.items():
    rel='glb/'+name+'.glb';p=pkg/rel;expected=manifest['files'][rel]['sha256'];assert sha(p)==expected;source_sha[rel]=expected
    before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(p.resolve()));new=set(bpy.data.objects)-before
    mesh=[o for o in new if o.type=='MESH'];assert len(mesh)==1 and len(new)==1,(name,len(mesh),len(new))
    o=mesh[0];bpy.context.view_layer.update();d=o.data;d.calc_loop_triangles();templates[kind]=(d,o.matrix_world.to_3x3().to_4x4(),len(d.loop_triangles));bpy.data.objects.remove(o,do_unlink=True)
def hit(x,y):
    ok,p,n,i=ground.ray_cast(Vector((x,y,10)),Vector((0,0,-1)),distance=20)
    return p.z if ok else None
rng=random.Random(202611263);placed=[];tri=0;counts={k:0 for k in families}
for kind,(name,count) in families.items():
    d,base,nt=templates[kind]
    for attempt in range(2500):
        if counts[kind]>=count or tri+nt>140000:break
        x=rng.uniform(-9.5,9.5);y=rng.uniform(-9.5,9.5)
        if abs(y)<2.9:continue
        scale=rng.uniform(.85,1.12);lin=Matrix.Rotation(rng.uniform(0,math.tau),4,'Z')@Matrix.Scale(scale,4)@base
        pts=[lin@p.co for p in d.vertices];mn=Vector(tuple(min(p[i] for p in pts) for i in range(3)));mx=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
        cx=(mn.x+mx.x)/2;cy=(mn.y+mx.y)/2
        radius=max(math.hypot(p.x-cx,p.y-cy) for p in pts)
        if radius<=0 or abs(y)-radius<2.7 or abs(x)+radius>9.95 or abs(y)+radius>9.95:continue
        # Turf interleaving allowed; solid moss and flower/grass use minimum centre distance.
        spacing=1.1 if kind=='turf' else .65
        if any(p['kind']==kind and math.hypot(x-p['x'],y-p['y'])<spacing for p in placed):continue
        roots=[p for p in pts if p.z<=mn.z+.025]
        hs=[hit(x+p.x-cx,y+p.y-cy) for p in roots]
        if not roots or any(h is None for h in hs):continue
        offsets=[h-p.z for h,p in zip(hs,roots)]
        z=max(offsets)-.01;res=[p.z+z-h for p,h in zip(roots,hs)]
        if max(res)>.045:continue
        o=bpy.data.objects.new('V3_%s_%03d'%(kind,counts[kind]),d);scene.collection.objects.link(o);o.matrix_world=Matrix.Translation(Vector((x-cx,y-cy,z)))@lin
        placed.append(dict(name=o.name,kind=kind,x=x,y=y,radius=radius,root_min=min(res),root_max=max(res),samples=len(roots),triangles=nt,route_gap=abs(y)-radius-2.5))
        tri+=nt;counts[kind]+=1
assert len(placed)>=24 and all(counts[k]>0 for k in families),counts
bpy.context.view_layer.update()
# Keep native evidence and recheck saved matrices/mesh counts on reopen.
def snap():
    return {o.name:(len(o.data.vertices),len(o.data.polygons),tuple(tuple(a) for a in o.matrix_world)) for o in bpy.context.scene.objects if o.type=='MESH'}
s=snap()
world=bpy.data.worlds.new('V3 daylight');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.35,.48,.68,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
ld=bpy.data.lights.new('V3 sun','SUN');ld.energy=2.1;ld.angle=.18;light=bpy.data.objects.new('V3 sun',ld);scene.collection.objects.link(light);light.rotation_euler=(math.radians(31),math.radians(-24),math.radians(-30))
cam=camera('V3 matched patch',(13,-16,12),(0,0,0),34);scene.camera=cam;render_setup(scene)
bpy.ops.file.pack_all()
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
    if o.type=='MESH':o.select_set(True)
bpy.context.view_layer.objects.active=ground
bpy.ops.export_scene.gltf(filepath=str((out/'village_verge_v3.glb').resolve()),use_selection=True,export_extras=True,export_attributes=True,export_animations=False)
dest=out/'village_verge_v3_UNAPPROVED.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()));scene=bpy.context.scene;assert snap()==s
actual={'root_abs_max':max(max(abs(p['root_min']),abs(p['root_max'])) for p in placed),'route_gap':min(p['route_gap'] for p in placed)}
q=dict(status='RECONSTRUCTED_LOCAL_PATCH_FEASIBILITY',terrain_source_blob='21b2804db198aaf9429f5f959d68a955e5839593',source_origin_m=origin,source_assets=source_sha,counts=counts,added_triangles=tri,terrain_triangles=len(f),root_samples=sum(p['samples'] for p in placed),actual=actual,placements=placed,native_reopen='PASS',engine_metrics=metrics(engine,{'root_abs_max':0,'route_gap':.20},actual,{'root_abs_max':.05,'route_gap':0},{'root_abs_max':.0001,'route_gap':.0001},{'route_gap':.20}),limits=['20x20m reconstructed test patch, route width 5m is provisional; no world placement or native original equivalence.','Existing glTF source assets checked against branch manifest, wind/runtime not tested.','Blueprint residual evaluation only; no production native edit adapter. D4/G1/G2/G4 not passed.'])
finish(out,q)
render(scene,bpy.data.objects['V3 matched patch'],out/'village.png')
low=camera('V3 approach',(-12,0,2.2),(5,0,.4),25);render(scene,low,out/'approach.png');finish(out,q)

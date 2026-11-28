"""V16 isolated native rendering pilot: selected V15C transforms, original source meshes.
Not the V15C GLB. Original tree morphology and full-resolution stump; no native owner edits."""
import bpy, math, json, sys, hashlib
from pathlib import Path
from mathutils import Vector
root,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
assert bpy.app.version[:3]==(5,3,0)
bpy.ops.wm.read_factory_settings(use_empty=True)
def path(s):
    a=list(root.rglob(s));assert len(a)==1,(s,a);return a[0]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def imp(s):
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path(s)))
    objs=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
    assert objs,s
    return objs
def put(o,name,x,y,z,a,s):
    n=bpy.data.objects.new(name,o.data);bpy.context.collection.objects.link(n)
    # glTF Y-up to Blender Z-up; yaw about glTF +Y becomes Blender +Z.
    n.location=(x,-z,y);n.rotation_euler=(0,0,a);n.scale=(s,)*3
    return n
def tex(nt,p,non=False):
    n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(path(p)),check_existing=True)
    if non:n.image.colorspace_settings.name='Non-Color'
    return n
def pbr(name,diff,norm,arm,box=False):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;n=nt.nodes;l=nt.links
    bs=n.get('Principled BSDF');d=tex(nt,diff);no=tex(nt,norm,True);a=tex(nt,arm,True)
    uv=n.new('ShaderNodeTexCoord')
    if box:
        for t in (d,no,a):t.projection='BOX';t.projection_blend=.25;l.new(uv.outputs['Object'],t.inputs['Vector'])
    else:
        for t in (d,no,a):l.new(uv.outputs['UV'],t.inputs['Vector'])
    l.new(d.outputs['Color'],bs.inputs['Base Color'])
    sn=n.new('ShaderNodeNormalMap');l.new(no.outputs['Color'],sn.inputs['Color']);sn.inputs['Strength'].default_value=.65
    # UV tangent-space normal is only appropriate for the terrain; box bark normal left unconnected.
    if not box:l.new(sn.outputs['Normal'],bs.inputs['Normal'])
    sep=n.new('ShaderNodeSeparateColor');l.new(a.outputs['Color'],sep.inputs['Color']);l.new(sep.outputs['Green'],bs.inputs['Roughness']);l.new(sep.outputs['Blue'],bs.inputs['Metallic'])
    return m
bark=pbr('V16_photo_bark_box_trial','jolcham_oak_bark_01_diff_2k.jpg','jolcham_oak_bark_01_nor_gl_2k.jpg','jolcham_oak_bark_01_arm_2k.jpg',True)
ground=pbr('V16_photo_ground','forrest_ground_01_diff_2k.jpg','forrest_ground_01_nor_gl_2k.jpg','forrest_ground_01_arm_2k.jpg')
# Recreate known provisional V02 heightfield, same 2.5m lattice and triangle split.
v=[];f=[]
for iy in range(41):
    y=-500+2.5*iy
    for ix in range(81):
        x=500+2.5*ix
        p=18+3*math.sin(math.pi*y/300)+.006*(x+175)+.85*math.sin((x+175)/74)*math.sin(y/85)
        t=max(0,min(1,(x-375)/45));z=p+t*t*(3-2*t)*(5*math.sin((x-375)/39)*math.cos((y+245)/50)+9*math.exp(-((x-610)/86)**2-((y+395)/95)**2))
        v.append((x-600,y+400,z))
for iy in range(40):
    for ix in range(80):
        a=iy*81+ix;f.extend([(a,a+1,a+82),(a,a+82,a+81)])
mesh=bpy.data.meshes.new('V02 reconstructed A3 lattice');mesh.from_pydata(v,[],f);mesh.update();uv=mesh.uv_layers.new()
for poly in mesh.polygons:
    poly.use_smooth=True
    for i in poly.loop_indices:
        x,y,z=v[mesh.loops[i].vertex_index];uv.data[i].uv=(x/2,y/2)
terrain=bpy.data.objects.new('A3 provisional reconstructed terrain',mesh);bpy.context.collection.objects.link(terrain);mesh.materials.append(ground)
templates={}
for k,s in [('T','eco_tree_forest_tall_a_LOD1.glb'),('D','eco_tree_deciduous_a_LOD1.glb'),('G','eco_grass_tuft_short_LOD1.glb'),('M','eco_grass_meadow_LOD1.glb'),('S','eco_shrub_round_a_LOD1.glb')]:
    a=imp(s);assert len(a)==1;templates[k]=a[0]
    if k in 'TD':
        for i,m in enumerate(a[0].data.materials):
            if 'bark' in m.name.lower():a[0].data.materials[i]=bark
for o in imp('fern_02_1k.gltf'):
    k={'fern_02_b':'F0','fern_02_c':'F1','fern_02_a':'F2','fern_02_d':'F3'}[o.name];templates[k]=o
# Separate provider alpha, not RGB JPEG alpha. Blender importer may already have Alpha link.
for m in {m for k,o in templates.items() if k.startswith('F') for m in o.data.materials}:
    nt=m.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
    a=tex(nt,'fern_02_alpha_1k.png',True)
    nt.links.new(a.outputs['Color'],bs.inputs['Alpha'])
for o in imp('rock_moss_set_01_1k.gltf'):
    templates['R'+str(int(o.name[-2:])-1)]=o
templates['U']=imp('tree_stump_01_1k.gltf')[0]
# V15C transform extract rounded to six decimals. Subset only; source meshes instead of warped/LOD2 derivatives.
rows="""T001 T .325043 33.259252 46.864435 2.923741 1.556474
T003 T 19.612988 30.539339 64.140747 4.715822 1.758955
T005 T 28.043196 29.126028 80.108629 1.952570 1.650747
T006 T 46.558020 29.039134 40.157737 5.428068 1.786634
T009 T 19.474833 31.236403 55.954145 1.811079 1.859810
T012 T 2.981348 33.821303 39.799547 4.684037 1.631503
T014 T -1.918488 33.941779 42.344403 .936500 2.019100
T016 T -1.180319 34.829875 31.892589 2.109453 1.859522
T020 T 14.369380 31.175590 59.995945 2.092608 1.905393
T021 T -7.875814 30.493684 70.614130 1.899426 1.836358
T025 T 14.439368 30.503633 66.941759 4.255953 1.609664
T027 T 11.802314 29.773649 75.300705 3.858417 1.622547
T033 T 1.427994 32.030206 57.930893 2.428522 1.924509
T036 T -9.060988 34.840624 36.165490 2.730475 1.829785
T042 T 5.567851 33.148720 45.785761 5.279101 1.804468
T043 T -14.381093 30.103672 72.635018 1.738571 1.652740
T044 T 6.370192 29.309800 80.532598 4.807202 1.935704
D046 D 10.674158 30.797362 65.368481 2.860967 1.912335
D047 D 17.398890 31.893706 48.702847 2.653864 1.650844
D048 D 29.877813 29.708062 68.312822 .881066 1.889494
D049 D 18.951426 29.168542 81.422675 .930523 1.803299
D052 D -11.167192 29.781654 75.098406 4.943216 1.666103
D054 D 10.856322 28.929803 84.058859 4.440870 1.968794
D057 D 14.506058 31.549736 55.584144 2.043864 1.773250
D059 D -12.906991 33.930787 45.200388 1.584438 1.813071
D060 D 23.985702 29.489443 75.634259 .571541 1.721609
D066 D 4.737893 31.221531 63.114420 2.998026 1.793149
D072 D .044935 28.910004 82.687544 5.082589 1.884385
D073 D 2.180248 29.622366 77.502166 .396821 2.176064
S088 S 21.652230 31.503935 47.353416 .074276 .824293
S089 S 4.931052 33.857935 37.064160 5.727122 .988506
S108 S 7.805393 33.667168 35.923104 3.198856 .903594
G126 G 12.544423 32.896378 39.574033 3.727321 1.318315
G140 G 9.058346 33.361219 37.733779 1.377003 1.197786
G143 G 14.253120 32.536556 42.168034 1.031817 1.273403
G147 G 14.289777 32.591928 41.342660 4.622642 .912750
G162 G 9.186155 33.130192 40.381456 4.398488 1.363903
G171 G 11.195757 33.217436 37.022986 2.522092 1.142116
G172 G 17.841691 32.196640 42.036315 .988601 .947755
G188 G 14.778517 32.700593 39.267233 3.922187 .973339
G195 G 8.233303 33.162782 40.928970 4.475933 1.295397
G197 G 15.143963 32.306160 44.066317 5.040079 1.015892
G201 G 16.267728 32.068034 45.821403 .436194 1.281433
G216 G 6.920151 33.410454 39.338125 .617209 1.097417
G232 G 7.920249 33.249951 40.242272 4.068470 1.015767
M261 M 4.029536 33.643121 39.213213 1.281038 1.144827
M262 M 19.476350 31.684049 47.067060 2.663753 1.046764
M266 M 18.732551 31.967431 44.031154 2.984349 1.144558
M268 M 14.882231 32.284267 44.689581 5.888747 1.124416
M297 M 12.976234 32.738212 41.111772 5.248990 1.256258
M299 M 11.336666 33.089909 38.502850 1.943950 1.102763
M307 M 12.169607 33.102450 37.339465 6.036483 1.062062
M311 M 9.415675 32.911433 42.793848 3.614246 1.222270
M316 M 13.455126 32.396120 44.858334 5.036712 1.078459
M320 M 8.911106 33.278515 38.919304 3.820412 1.108196
M322 M 17.955468 32.123932 42.928782 2.576064 1.023409
F001 F0 15.411126 32.020203 47.488152 1.973661 1.308233
F005 F0 9.422277 33.443285 36.397609 5.430377 1.145486
F007 F0 11.955653 32.733306 42.395733 3.933720 1.393266
F009 F0 15.802243 32.475696 41.149847 4.624983 1.695207
F011 F0 13.281561 32.803200 39.989789 4.584508 1.158635
F013 F1 18.671702 31.823492 46.220312 .734595 1.355067
F014 F1 22.160382 31.539758 45.395019 .151956 1.405159
F015 F1 13.226694 32.147269 48.125112 4.700080 1.360850
F018 F1 12.939649 32.943822 38.564513 5.006125 1.608151
F019 F1 9.400640 32.438796 48.053257 4.275955 1.175023
F022 F1 19.793896 31.841632 44.390853 3.461083 1.324436
F023 F1 16.364345 32.263654 43.212783 5.467807 1.188171
F024 F1 10.940803 32.995024 40.251476 .565803 1.247244
F025 F2 14.521962 32.217678 45.929908 5.191143 1.229232
F027 F2 13.210899 32.586401 42.833745 5.554984 1.431495
F030 F2 10.510914 33.150439 38.728766 4.586634 1.440427
F032 F2 10.633120 33.231441 37.641789 .418931 1.241638
F034 F2 12.878050 32.519967 43.987047 5.841200 1.162507
F035 F2 2.127664 32.896919 48.027857 2.928352 1.572052
F036 F2 13.636339 31.902310 50.630342 1.781539 1.382560
F039 F3 20.791582 31.760474 43.977320 2.589925 1.384359
F041 F3 11.740293 32.864763 40.915441 .792348 1.374551
F043 F3 3.695485 34.000995 35.369401 1.809202 1.452560
F046 F3 23.715535 31.289030 46.761246 1.505385 1.236269
F048 F3 17.026686 32.079332 44.821811 .766629 1.457388
R03 R2 4.734111 34.469385 31.129622 4.800000 .62
R04 R3 17.629763 33.467141 25.967635 .916000 .53
R05 R4 23.147027 32.582624 30.269231 3.316000 .68
R06 R5 28.664291 31.591119 34.570827 5.716000 .57
R07 R0 34.181556 30.765420 38.872423 1.834000 .58
U02 U .306615 32.958723 50.323898 1.091000 .979490
U03 U 11.638891 32.443535 48.589619 5.430000 .940736"""
placed=[]
for row in rows.splitlines():
    name,k,*args=row.split();placed.append(put(templates[k],name,*map(float,args)))
for o in set(templates.values()):bpy.data.objects.remove(o,do_unlink=True)
# Remove imported non-mesh remnants, not scene geometry.
for o in list(bpy.context.scene.objects):
    if o.type=='EMPTY':bpy.data.objects.remove(o,do_unlink=True)
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.render.resolution_x=640;scene.render.resolution_y=360;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.world=bpy.data.worlds.new('Cool woodland sky');scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.40,.52,.70,1)
scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.38
sun=bpy.data.lights.new('Warm afternoon sun','SUN');sun.energy=2.0;sun.angle=.08;sun.color=(1,.86,.67)
so=bpy.data.objects.new('Sun',sun);scene.collection.objects.link(so);so.rotation_euler=Vector((-.55,.30,-.76)).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.cameras.new('V15 matched camera');co=bpy.data.objects.new('V15 matched camera',cam);scene.collection.objects.link(co);scene.camera=co
cam.sensor_fit='VERTICAL';cam.angle=math.radians(60);cam.clip_start=.08;cam.clip_end=250
views=[((8,35.00075988769531,36),(12.2,33.3,38.5)),((18,34.22273864746094,37),(12,33.2,42))]
def conv(v):return Vector((v[0],-v[2],v[1]))
def camera(i):
    e,a=views[i];co.location=conv(e);co.rotation_euler=(conv(a)-co.location).to_track_quat('-Z','Y').to_euler()
camera(0)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(out/'forest_v16_native_pilot.blend'))
def stats():
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    for o in objects:o.data.calc_loop_triangles()
    return dict(mesh_objects=len(objects),triangles=sum(len(o.data.loop_triangles) for o in objects),packed_images=sum(bool(i.packed_file) for i in bpy.data.images),external_images=[i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file])
before=stats();assert not before['external_images']
# Real save/reopen before rendering.
bpy.ops.wm.open_mainfile(filepath=str(out/'forest_v16_native_pilot.blend'))
scene=bpy.context.scene;co=scene.camera;after=stats();assert before==after,(before,after)
for i in range(2):
    camera(i);scene.render.filepath=str(out/('forest_v16_view_%d.png'%(i+1)));bpy.ops.render.render(write_still=True)
q=dict(status='NATIVE_SUBSET_PILOT_NOT_V15C_EQUIVALENT',blender=bpy.app.version_string,source_scene='09366ffaf5b1f6657b1b9ca158c9681d0d52537a4a90bf94f7ac25ec6f2162f1',before=before,after=after,placement_rows=len(rows.splitlines()),views=views,limits=['subset, original source tree forms and stump LOD0, reconstructed terrain and bark box mapping; approximate rock/stump yaw','no collision, final design, independent G2 or Android QA'])
q['sha256']={p.name:sha(p) for p in out.glob('*') if p.suffix in ('.png','.blend')}
(out/'qa.json').write_text(json.dumps(q,indent=2)+'\n')
print(q)

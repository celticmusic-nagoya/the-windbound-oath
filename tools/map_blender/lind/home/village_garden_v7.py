"""V7 garden context: low loose stone edging and flower clusters, non-structural and unadopted."""
import bpy,sys,math,random,hashlib,json
from pathlib import Path
from array import array
from mathutils import Vector,Matrix
src,rock,photos,out,engine=map(Path,sys.argv[sys.argv.index('--')+1:])
out.mkdir(parents=True,exist_ok=True)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
lock='e3c92ee2cffcae1830171ca49d71adb221bcb532a21758de6c09544183c66696'
rocklock='da8010774291c5d0acfbcc3b82b367be06c5ed0926640147de5f17371ef227d1'
assert bpy.app.version[:3]==(5,3,0) and sha(src)==lock and sha(rock)==rocklock
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),load_ui=False)
scene=bpy.context.scene;ground=bpy.data.objects['V3_village_reconstructed_patch'];bpy.context.view_layer.update()
def dg(data,prop,count,typ):
    a=array(typ,[0])*count
    if count:data.foreach_get(prop,a)
    return hashlib.sha256(a.tobytes()).hexdigest()
def snap():
    return {o.name:(dg(o.data.vertices,'co',len(o.data.vertices)*3,'f'),dg(o.data.loops,'vertex_index',len(o.data.loops),'i'),dg(o.data.polygons,'material_index',len(o.data.polygons),'i'),tuple((u.name,dg(u.data,'uv',len(u.data)*2,'f')) for u in o.data.uv_layers),tuple(tuple(row) for row in o.matrix_world),tuple(m.name if m else None for m in o.data.materials),o.hide_render) for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.startswith('V7_')}
old=snap();assert len(old)==181
def bbox(o):
    pts=[o.matrix_world@Vector(p) for p in o.bound_box]
    return (min(p.x for p in pts),max(p.x for p in pts),min(p.y for p in pts),max(p.y for p in pts))
def h(x,y):
    ok,p,_,_=ground.ray_cast(Vector((x,y,10)),Vector((0,0,-1)),distance=20)
    assert ok,(x,y)
    return p.z
home=[bbox(o) for o in scene.objects if o.type=='MESH' and o.name.startswith('GEO_') and not o.hide_render]
house=(min(p[0] for p in home)-.5,max(p[1] for p in home)+.5,min(p[2] for p in home)-.5,max(p[3] for p in home)+.5)
limits=bbox(ground)
# Proposed side garden location outside house envelope and route. Size measured in provisional BU.
left=max(house[1]+.35,7.0);right=limits[1]-.65;front=max(house[2]+.7,4.0);back=min(front+4.4,limits[3]-.65)
assert right-left>=1.4 and back-front>=3.0,(limits,house,left,right,front,back)
garden=(left,right,front,back)
def inside(b,rect):
    return b[0]>=rect[0] and b[1]<=rect[1] and b[2]>=rect[2] and b[3]<=rect[3]
def overlap(a,b):
    return not(a[1]<b[0] or a[0]>b[1] or a[3]<b[2] or a[2]>b[3])
rng=random.Random(202611267)
coll=bpy.data.collections.new('V7_GARDEN_SCENIC_ONLY');scene.collection.children.link(coll)
# Explicit LOD3 exact CC0 scan, not the failed bridge abutment or a cuboid generator.
pre_materials=set(bpy.data.materials);pre_images=set(bpy.data.images);pre_meshes=set(bpy.data.meshes)
with bpy.data.libraries.load(str(rock.resolve()),link=False) as (a,b):
    names=[n for n in a.objects if n=='rock_07_LOD3'];assert len(names)==1,a.objects
    b.objects=names
raw=b.objects[0];assert raw.type=='MESH' and len(raw.data.vertices)==929
mesh=raw.data.copy();mesh.name='V7_stone_source';assert len(mesh.uv_layers)>0
# Normalize local scan mesh along principal authored axes; preserve original topology and UV.
v=[p.co.copy() for p in mesh.vertices];mn=[min(p[i] for p in v) for i in range(3)];mx=[max(p[i] for p in v) for i in range(3)]
assert all(mx[i]>mn[i] for i in range(3))
for p in mesh.vertices:
    p.co=Vector(((p.co.x-(mn[0]+mx[0])/2)/(mx[0]-mn[0]),(p.co.y-(mn[1]+mx[1])/2)/(mx[1]-mn[1]),(p.co.z-mn[2])/(mx[2]-mn[2])))
mesh.update();mesh.calc_loop_triangles()
# Scan geometry only: detach imported external-texture dependencies, never existing scene data.
mesh.materials.clear()
source_mesh=raw.data
assert source_mesh not in pre_meshes and not raw.users_collection
bpy.data.objects.remove(raw,do_unlink=True)
assert source_mesh.users==0 or (source_mesh.use_fake_user and source_mesh.users==1)
bpy.data.meshes.remove(source_mesh)
removed_materials=[];removed_images=[]
for item in list(set(bpy.data.materials)-pre_materials):
    assert item.users==0 or (item.use_fake_user and item.users==1),(item.name,item.users)
    removed_materials.append(item.name);bpy.data.materials.remove(item)
for item in list(set(bpy.data.images)-pre_images):
    assert item.users==0 or (item.use_fake_user and item.users==1),(item.name,item.users)
    removed_images.append(item.name);bpy.data.images.remove(item)
print('SCAN_DEPENDENCY_CLEANUP',json.dumps(dict(materials=removed_materials,images=removed_images)),flush=True)
asset=photos/'rock_boulder_dry';rec=json.loads((asset/'manifest.json').read_text());assert rec['license']=='CC0'
mat=bpy.data.materials.new('V7 garden stone PBR');mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links;bs=next(q for q in n if q.type=='BSDF_PRINCIPLED')
texs={}
for role,key in [('basecolor','Base Color'),('roughness','Roughness'),('normal','Normal')]:
    t=rec['textures'][role];p=asset/t['path'];assert sha(p)==t['sha256'];texs[role]=t['sha256']
    img=bpy.data.images.load(str(p.resolve()),check_existing=True);img.colorspace_settings.name=t['color_space'];img.pack();q=n.new('ShaderNodeTexImage');q.image=img
    if role=='normal':
        nm=n.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.5;l.new(q.outputs['Color'],nm.inputs['Color']);l.new(nm.outputs['Normal'],bs.inputs[key])
    else:l.new(q.outputs['Color'],bs.inputs[key])
mesh.materials.clear();mesh.materials.append(mat)
for p in mesh.polygons:p.material_index=0
# Place single-course loose edging: deliberate gaps, not structural masonry.
points=[]
for x in [left+.22,right-.22]:
    y=front+.25
    while y<back-.2:
        points.append((x,y,math.pi/2));y+=rng.uniform(.44,.60)
for y in [front+.20,back-.20]:
    x=left+.6
    while x<right-.5:
        points.append((x,y,0));x+=rng.uniform(.44,.58)
stones=[];roots=[]
for x,y,yaw in points:
    sx,sy,sz=rng.uniform(.38,.53),rng.uniform(.27,.38),rng.uniform(.18,.29)
    lin=Matrix.Rotation(yaw+rng.uniform(-.2,.2),4,'Z')@Matrix.Diagonal((sx,sy,sz,1))
    pts=[lin@p.co for p in mesh.vertices]
    b=(x+min(p.x for p in pts),x+max(p.x for p in pts),y+min(p.y for p in pts),y+max(p.y for p in pts))
    if not inside(b,garden) or overlap(b,house) or any(overlap(b,s['bbox']) for s in stones):continue
    low=[p for p in pts if p.z<=.03];assert low
    residual=[h(x+p.x,y+p.y)-p.z for p in low];z=max(residual)-.02
    rr=[z-a for a in residual]
    if max(rr)>.07:continue
    o=bpy.data.objects.new('V7_stone_%03d'%len(stones),mesh);coll.objects.link(o);o.matrix_world=Matrix.Translation(Vector((x,y,z)))@lin
    stones.append(dict(name=o.name,bbox=b,root_min=min(rr),root_max=max(rr)));roots+=rr
assert len(stones)>=8,stones
# Existing saved V3 flower geometry, no new flora species. Place in natural groups within the edging.
flowers=[]
for kind in ['daisy','spike','grass']:
    templates=sorted([o for o in scene.objects if o.type=='MESH' and o.name.startswith('V3_'+kind+'_')],key=lambda o:o.name)
    assert templates,kind
    t=templates[0];d=t.data;d.calc_loop_triangles();base=t.matrix_world.to_3x3().to_4x4()
    for i in range(100):
        if sum(q['kind']==kind for q in flowers)>=7:break
        x=rng.uniform(left+.55,right-.55);y=rng.uniform(front+.55,back-.55)
        if any(math.hypot(x-q['x'],y-q['y'])<.24 for q in flowers):continue
        lin=Matrix.Rotation(rng.uniform(0,math.tau),4,'Z')@Matrix.Scale(rng.uniform(.55,.82),4)@base
        pts=[lin@v.co for v in d.vertices];mn=min(p.z for p in pts)
        cx=(min(p.x for p in pts)+max(p.x for p in pts))/2;cy=(min(p.y for p in pts)+max(p.y for p in pts))/2
        b=(x+min(p.x for p in pts)-cx,x+max(p.x for p in pts)-cx,y+min(p.y for p in pts)-cy,y+max(p.y for p in pts)-cy)
        if not inside(b,garden) or any(overlap(b,s['bbox']) for s in stones):continue
        low=[p for p in pts if p.z<=mn+.025];rr=[h(x+p.x-cx,y+p.y-cy)-p.z for p in low];z=max(rr)-.006
        res=[z-a for a in rr]
        if max(res)>.05:continue
        o=bpy.data.objects.new('V7_%s_%03d'%(kind,len(flowers)),d);coll.objects.link(o);o.matrix_world=Matrix.Translation(Vector((x-cx,y-cy,z)))@lin
        flowers.append(dict(name=o.name,kind=kind,x=x,y=y,bbox=b,root_max=max(res),triangles=len(d.loop_triangles)));roots+=res
assert len(flowers)>=6,flowers
bpy.context.view_layer.update();assert snap()==old and sha(src)==lock and sha(rock)==rocklock
assert all(inside(q['bbox'],garden) and not overlap(q['bbox'],house) and q['bbox'][2]>2.8 for q in stones+flowers)
# Non-structural scoped metric; no structural or collision PASS implied.
sys.path[:0]=[str(engine/'tools'),str(engine/'tools/production_qa')]
from blueprint_engine.residual import evaluate
actual={'ground_residual_abs_max':max(map(abs,roots)),'protected_mesh_changes':0,'route_overlap_count':0}
metrics=evaluate(dict(values={k:0 for k in actual},tolerances={'ground_residual_abs_max':.07,'protected_mesh_changes':0,'route_overlap_count':0},uncertainty={k:0 for k in actual}),dict(actual=actual,uncertainty={'ground_residual_abs_max':.000001,'protected_mesh_changes':0,'route_overlap_count':0}))
dest=out/'village_garden_v7_UNAPPROVED.blend';assert not dest.exists()
missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()]
assert not missing,missing
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True);bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()),load_ui=False);scene=bpy.context.scene
assert snap()==old and sha(src)==lock and all(bpy.data.objects.get(q['name']) for q in stones+flowers)
q=dict(status='SCENIC_GARDEN_FEASIBILITY',source_sha256=lock,rock_source_sha256=rocklock,rock_source='Poly Haven rock_07 LOD3; CC0; historical source manifest PR363; not Irish provenance',pbr=texs,removed_unused_scan_dependencies=dict(materials=removed_materials,images=removed_images),protected_meshes=len(old),garden=list(garden),house=list(house),stones=stones,flowers=flowers,root_samples=len(roots),actual=actual,engine_metrics=metrics,native_reopen='PASS',limits=['Provisional local scene only; not structural dry-stone wall or approved garden layout.','Existing turf is retained, not collision tested; no GLB bake or runtime.'])
q['added_triangles']=0
for item in stones+flowers:
    m=bpy.data.objects[item['name']].data;m.calc_loop_triangles();q['added_triangles']+=len(m.loop_triangles)
def finish():
    q['outputs']={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.blend','.png')}
    (out/'qa.json').write_text(json.dumps(q,indent=2)+'\n')
finish()
cx=(left+right)/2;cy=(front+back)/2
for name,eye,aim,lens in [('street',(11,-14,6),(0,6,1.8),34),('garden',(cx+3,cy-5,3.3),(cx,cy,.45),35)]:
    d=bpy.data.cameras.new('V7 '+name);o=bpy.data.objects.new('V7 '+name,d);scene.collection.objects.link(o);o.location=eye;o.rotation_euler=(Vector(aim)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=200
    scene.camera=o;scene.render.filepath=str((out/(name+'.png')).resolve());bpy.ops.render.render(write_still=True);finish()

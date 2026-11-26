"""V73 bounded scene material and LOD feasibility, preserve original checkpoint."""
import bpy,sys,math,hashlib,json,random,collections
from pathlib import Path
from array import array
from mathutils import Vector,Matrix
from mathutils.geometry import convex_hull_2d
from mathutils.bvhtree import BVHTree
src,sources,out=map(Path,sys.argv[sys.argv.index('--')+1:])
out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lock='745f3739cf5360b113267003a21b61d0c812abeb7dfb3eecd66a2e558f2bf6bc'
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
old=snap();assert len(old)==691
assert ext.data.color_attributes.get(attr) and terrain.data.color_attributes.get(attr)
def ray(o,x,y):
    inv=o.matrix_world.inverted()
    ok,p,n,i=o.ray_cast(inv@Vector((x,y,100)),inv.to_3x3()@Vector((0,0,-1)),distance=200)
    return float((o.matrix_world@p).z) if ok else None
def ground(x,y):
    if -100<=x<=100 and -100<=y<=0:return ray(terrain,x,y)
    if 60<=x<=135 and -135<=y<=-60:return ray(ext,x,y)
    return None

prior=src.parent/'v71_qa.json';assert sha(prior)=='9aff33210642ddb3acdae13912ad6fe73321382f6073eff8d5b9177d1804013f'
rows=json.loads(prior.read_text())['placed'];assert len(rows)==168
report=sources/'report.json';assert sha(report)=='623601e878a514654e35081796db6ea1b49b46c4ef26bf0f2f549d41e803d00d'
manifest=json.loads(report.read_text());assert len(manifest['files'])==8 and not manifest['errors']
for row in manifest['files']:
    p=sources/row['path'];assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256'] and hashlib.md5(p.read_bytes()).hexdigest()==row['provider_md5']
stumps=[row for row in rows if row['kind']=='stump'];assert len(stumps)==6
template=bpy.data.objects[stumps[0]['source']];original=template.data;original.calc_loop_triangles();assert len(original.loop_triangles)==41046
# One LOD candidate. Evaluate a temporary object and do not change original source.
temp=bpy.data.objects.new('V73_STUMP_LOD_TEMP',original);scene.collection.objects.link(temp)
mod=temp.modifiers.new('V73_LOD','DECIMATE');mod.ratio=.25;mod.use_collapse_triangulate=True
deps=bpy.context.evaluated_depsgraph_get();ev=temp.evaluated_get(deps);lod=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=deps);lod.name='V73_stump_LOD_candidate';lod.calc_loop_triangles()
bpy.data.objects.remove(temp,do_unlink=True)
def bvh(m):
    m.calc_loop_triangles()
    return BVHTree.FromPolygons([v.co for v in m.vertices],[tuple(p.vertices) for p in m.loop_triangles],all_triangles=True)
def distances(a,b):
    t=bvh(b);res=[t.find_nearest(v.co)[3] for v in a.vertices]
    return {'count':len(res),'max_m':max(res),'p95_m':sorted(res)[int(.95*(len(res)-1))]}
def bounds(m):
    return [[min(v.co[i] for v in m.vertices) for i in range(3)],[max(v.co[i] for v in m.vertices) for i in range(3)]]
aa,bb=bounds(original),bounds(lod);max_scale=max(bpy.data.objects[x['name']].scale.x for x in stumps)
dist1,dist2=distances(original,lod),distances(lod,original)
bounds_delta=max(abs(a-b) for x,y in zip(aa,bb) for a,b in zip(x,y))*max_scale
# Sampled surface distance only, not certified Hausdorff bound. Preserve full original projected hull for obstacle protection.
lod_ok=bool(len(lod.uv_layers)==len(original.uv_layers) and len(lod.materials)==len(original.materials) and max(dist1['max_m'],dist2['max_m'])*max_scale<=.025 and bounds_delta<=.015 and len(lod.loop_triangles)<=11000)
lod_result={'original_triangles':41046,'candidate_triangles':len(lod.loop_triangles),'max_instance_scale':max_scale,'sampled_forward':dist1,'sampled_reverse':dist2,'placed_sampled_max_m':max(dist1['max_m'],dist2['max_m'])*max_scale,'bounds_delta_m':bounds_delta,'accepted':False}
if lod_ok:
    checks=[]
    for row in stumps:
        o=bpy.data.objects[row['name']];coords=[o.matrix_world@v.co for v in lod.vertices];bottom=min(v.z for v in coords)
        low=[v for v in coords if v.z<=bottom+.06];res=[v.z-ground(v.x,v.y) for v in low]
        checks.append({'name':o.name,'min':min(res),'max':max(res)})
    lod_ok=all(-.08<=x['min']<=.05 and x['max']<=.22 for x in checks)
    lod_result['root_checks']=checks
if lod_ok:
    for row in stumps:bpy.data.objects[row['name']].data=lod
    lod_result['accepted']=True
saved=(41046-len(lod.loop_triangles))*6 if lod_ok else 0
# Reuse real leaf litter PBR with world-continuous UV and noise; copy only terrain material, preserve original graph.
orig=terrain.data.materials[0];assert ext.data.materials[0]==orig
mat=orig.copy();mat.name='V73_irish_floor_PBR_feasibility';nt=mat.node_tree;n=nt.nodes;l=nt.links
bs=next(x for x in n if x.type=='BSDF_PRINCIPLED');output=next(x for x in n if x.type=='OUTPUT_MATERIAL' and x.is_active_output)
assert output.inputs['Surface'].is_linked and output.inputs['Surface'].links[0].from_node==bs
uv=n.new('ShaderNodeUVMap');uv.uv_map=terrain.data.uv_layers.active.name
assert ext.data.uv_layers.active.name==uv.uv_map
scale=n.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs['Scale'].default_value=2/3;l.new(uv.outputs['UV'],scale.inputs[0])
def tex(suffix,non=False):
    p=sources/'forest_leaves_02'/('forest_leaves_02_'+suffix+'_2k.jpg');im=bpy.data.images.load(str(p),check_existing=False)
    if non:im.colorspace_settings.name='Non-Color'
    im.pack();node=n.new('ShaderNodeTexImage');node.image=im;node.extension='REPEAT';l.new(scale.outputs['Vector'],node.inputs['Vector']);return node
diff=tex('diffuse');normal=tex('nor_gl',True);rough=tex('rough',True)
new=n.new('ShaderNodeBsdfPrincipled');l.new(diff.outputs['Color'],new.inputs['Base Color']);l.new(rough.outputs['Color'],new.inputs['Roughness']);new.inputs['Metallic'].default_value=0
nm=n.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.65;l.new(normal.outputs['Color'],nm.inputs['Color']);l.new(nm.outputs['Normal'],new.inputs['Normal'])
geo=n.new('ShaderNodeNewGeometry');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=.18;noise.inputs['Detail'].default_value=3;l.new(geo.outputs['Position'],noise.inputs['Vector'])
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.25;ramp.color_ramp.elements[0].color=(.15,.15,.15,1);ramp.color_ramp.elements[1].position=.72;ramp.color_ramp.elements[1].color=(.85,.85,.85,1);l.new(noise.outputs['Fac'],ramp.inputs[0])
mix=n.new('ShaderNodeMixShader');l.new(ramp.outputs['Color'],mix.inputs[0]);l.new(bs.outputs['BSDF'],mix.inputs[1]);l.new(new.outputs['BSDF'],mix.inputs[2]);l.new(mix.outputs[0],output.inputs['Surface'])
for o in (terrain,ext):o.data.materials[0]=mat
# One exact imported deadwood asset, only if freed instance triangles permit. Find a non-overlapping footprint in unused patches.
added=[];reject=collections.Counter()
if saved>=101802:
    before=set(bpy.data.objects.keys())
    bpy.ops.import_scene.gltf(filepath=str(sources/'dead_tree_trunk/dead_tree_trunk_1k.gltf'))
    imported=[o for o in bpy.context.scene.objects if o.name not in before and o.type=='MESH'];assert len(imported)==1
    o=imported[0];o.data.calc_loop_triangles();assert len(o.data.loop_triangles)==101802
    # Preserve imported world orientation and scale, apply translation/yaw only.
    M=o.matrix_world.copy();vs=[M@v.co for v in o.data.vertices];mn=Vector(tuple(min(v[i] for v in vs) for i in range(3)));mx=Vector(tuple(max(v[i] for v in vs) for i in range(3)))
    pivot=Vector(((mn.x+mx.x)/2,(mn.y+mx.y)/2,mn.z));xy=[Vector((v.x-pivot.x,v.y-pivot.y)) for v in vs];hh=[xy[i] for i in convex_hull_2d(xy)];low=[v-pivot for v in vs if v.z<=mn.z+.06]
    # Conservative native AABB footprint for existing objects; hero tree trunks only, retain V71 reservations.
    obs=[]
    for name in old:
        if name in (src_name,ext_name):continue
        a=bpy.data.objects[name]
        if name.startswith(('V57_hero_','V58_SCENIC_C_')):
            v=[a.matrix_world@p.co for p in a.data.vertices];bottom=min(p.z for p in v)
            if name.endswith('_leaves') or bottom>32:continue
            pts=[Vector((p.x,p.y)) for p in v if p.z<=bottom+1.2]
        else:
            v=[a.matrix_world@Vector(p) for p in a.bound_box];pts=[Vector((p.x,p.y)) for p in v]
        if len(pts)>=3:
            h=[pts[i] for i in convex_hull_2d(pts)]
            if len(h)>=3:obs.append((name,h,bbox(h)))
    rng=random.Random(2026112673)
    for attempt in range(160):
        cx,cy=rng.choice([(87,-111),(70,-91),(108,-103)])
        x=cx+rng.uniform(-3,3);y=cy+rng.uniform(-3,3);rot=Matrix.Rotation(rng.uniform(0,2*math.pi),3,'Z')
        h=[Vector((q.x+x,q.y+y)) for q in (rot@Vector((p.x,p.y,0)) for p in hh)]
        rg=reserved_gap(h)
        if rg<.10:reject['reserve']+=1;continue
        g=min((poly_gap(h,p) for _,p,b in obs if bboxgap(bbox(h),b)<.15),default=.15)
        if g<.04:reject['obstacle']+=1;continue
        z=ground(x,y)
        if z is None or any(ground(p.x,p.y) is None for p in h):reject['edge']+=1;continue
        rr=[]
        for p in low:
            q=rot@p;gz=ground(x+q.x,y+q.y)
            if gz is None:break
            rr.append(z+q.z-gz)
        if len(rr)!=len(low) or not rr:continue
        off=-min(rr)-.05;res=[v+off for v in rr]
        if max(res)>.22:reject['contact']+=1;continue
        o.parent=None;o.matrix_world=Matrix.Translation((x,y,z+off))@rot.to_4x4()@Matrix.Translation(-pivot)@M;o.name='V73_DEADWOOD_CANDIDATE'
        added.append({'name':o.name,'location':[x,y,z+off],'reserve_gap_m':rg,'obstacle_gap_lower_bound_m':g,'root_residual_range_m':[min(res),max(res)],'triangles':101802});break
    if not added:
        for obj in list(bpy.context.scene.objects):
            if obj.name not in before:bpy.data.objects.remove(obj,do_unlink=True)
bpy.context.view_layer.update()
s=snap()
changed={src_name,ext_name}|({row['name'] for row in stumps} if lod_ok else set())
assert all(s[k]==v for k,v in old.items() if k not in changed)
# Terrain signatures must differ only in material slot list (same geometry, UV and color attributes).
for k in (src_name,ext_name):
    assert s[k][0][:-1]==old[k][0][:-1] and s[k][1:3]==old[k][1:3]
assert sha(src)==lock
bpy.ops.file.pack_all()
dest=out/'v73_irish_material_lod_feasibility.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()))
scene=bpy.context.scene;terrain=bpy.data.objects[src_name];ext=bpy.data.objects[ext_name]
ss=snap();assert all(ss[k]==v for k,v in s.items()) and sha(src)==lock
assert terrain.data.materials[0]==ext.data.materials[0]
q={'status':'BOUNDED_MATERIAL_LOD_FEASIBILITY','source_sha256':lock,'blender':bpy.app.version_string,'prior_meshes':len(old),'unchanged_meshes_exact':len(old)-len(changed),'changed_scoped_names':sorted(changed),'lod':lod_result,'saved_triangles':saved,'deadwood':added,'deadwood_rejections':dict(reject),'net_instance_triangles_delta':sum(a['triangles'] for a in added)-saved,'material':{'source':'forest_leaves_02','repeat_m':3,'method':'shared continuous world-space noise blend of existing shader and photo-derived PBR, no geometry displacement','source_files_verified':8},'native_sha256':sha(dest),'limits':['One isolated feasibility candidate, no D4/G2 acceptance. LOD vertex samples not certified Hausdorff or silhouette/UV error; deadwood conservative AABB and sampled roots only. Material blend provisional; no runtime or formal adoption.']}
(out/'v73_qa.json').write_text(json.dumps(q,indent=2)+'\n')
views={0:((78.17052459716797,-80.77701568603516,29.82533073425293),(93.94316101074219,-93.07432556152344,30.988130569458008),22),2:((71,-73,53),(96,-96,32),32)}
cam=scene.camera
for i,(a,b,lens) in views.items():
    cam.location=a;cam.rotation_euler=(Vector(b)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
    scene.render.filepath=str((out/f'v73_view_{i}.png').resolve());bpy.ops.render.render(write_still=True)
q['outputs']={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.blend','.png')}
(out/'v73_qa.json').write_text(json.dumps(q,indent=2)+'\n');print(q)

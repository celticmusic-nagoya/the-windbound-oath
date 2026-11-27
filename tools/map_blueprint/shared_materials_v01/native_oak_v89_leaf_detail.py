"""V89: retain leaf components and perimeter; simplify interior triangles only.
Native V82D reference is immutable; no forest placement change.
"""
import bpy,bmesh,sys,hashlib,json,math,shutil
from pathlib import Path
from collections import Counter
from mathutils import Vector
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v89_leaf_reduce import reduce_leaf,boundary
src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
LOCK='e2b777f32b17dfa5f1a671b734d5f1f92123a4d93982b5a016d00d8e31629145'
assert sha(src)==LOCK and bpy.app.version[:3]==(5,3,0)
manifest={n.strip().removeprefix('./'):h for h,n in (l.split(None,1) for l in (src.parent/'SHA256SUMS').read_text().splitlines())}
def verify(n):
    f=src.parent/n;assert sha(f)==manifest[n],n;return f
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()))
study=bpy.data.scenes['V82D_OAK_ASSET_STUDY'];reference=study.objects['V82D_oak_reference'];old=study.objects['V82D_oak_candidate'];camera=study.camera
source=reference.data;source.calc_loop_triangles();assert len(source.loop_triangles)==1599403
assert source.materials[1].name=='island_tree_01_leaves'
def protected(m):
    uvs=list(m.uv_layers)
    return Counter((p.material_index,tuple((tuple(m.vertices[m.loops[i].vertex_index].co),tuple(tuple(u.data[i].uv) for u in uvs)) for i in p.loop_indices)) for p in m.polygons if p.material_index!=1)
original=protected(source)
assert sum(original.values())==539371
qa={'candidate_only':True,'source_sha256':LOCK,'source_triangles':1599403,'protected_triangles':539371,'source_leaf_components':44168,'local_sample':{'source_glb_sha256':'fd3a662d02edba211578385edfdef86f30e5489172a8c8a680ef704b51e9a493','sample_count':512,'source_triangles':12288,'candidate_triangles':7760,'max_relative_removed_vertex_residual':.03991265161279157},'limits':['4% relative removed-vertex UV-surface residual is provisional, not continuous Hausdorff error','Perimeter exact; interior normal interpolation may differ','No world placement or Android G4'],'views':[]}
def checkpoint():
    (out/'v89_oak_qa.json').write_text(json.dumps(qa,indent=2));print('V89_CHECKPOINT',json.dumps({k:v for k,v in qa.items() if k!='views'}),flush=True)
copy=source.copy();copy.name='V89_oak_leaf_detail_candidate'
bm=bmesh.new();bm.from_mesh(copy);bm.faces.ensure_lookup_table();bm.verts.ensure_lookup_table()
layers=list(bm.loops.layers.uv.values());active=bm.loops.layers.uv.active;assert layers and active is not None
ai=layers.index(active)
leaf=[f for f in bm.faces if f.material_index==1];wood={v for f in bm.faces if f.material_index!=1 for v in f.verts}
assert len(leaf)==1060032
seen=set();groups=[]
for f in leaf:
    if f in seen:continue
    seen.add(f);todo=[f];group=[]
    while todo:
        cur=todo.pop();group.append(cur)
        for v in cur.verts:
            for n in v.link_faces:
                if n.material_index==1 and n not in seen:seen.add(n);todo.append(n)
    groups.append(group)
assert len(groups)==44168
qa['component_count']=len(groups);checkpoint()
hist=Counter();resmax=0.;changed=0;skipped=0;removed_tri=0
for gi,group in enumerate(groups):
    verts=sorted({v for f in group for v in f.verts},key=lambda v:v.index)
    if len(group)!=24 or len(verts)!=21 or any(v in wood for v in verts) or any(len(f.verts)!=3 for f in group):skipped+=1;hist[len(group)]+=1;continue
    vid={v:i for i,v in enumerate(verts)};faces=[tuple(vid[v] for v in f.verts) for f in group]
    coords=[tuple(v.co) for v in verts];uv={};good=True
    for f in group:
        for l in f.loops:
            values=tuple(tuple(l[layer].uv) for layer in layers);k=vid[l.vert]
            if k in uv and uv[k]!=values:good=False
            uv[k]=values
    if not good or len(uv)!=21:skipped+=1;hist[24]+=1;continue
    new,err=reduce_leaf(coords,[uv[i][ai] for i in range(21)],faces)
    hist[len(new)]+=1
    if len(new)==24:continue
    assert boundary(new)==boundary(faces) and err<=.04
    smooth=all(f.smooth for f in group)
    bmesh.ops.delete(bm,geom=group,context='FACES_ONLY')
    for t in new:
        f=bm.faces.new(tuple(verts[i] for i in t));f.material_index=1;f.smooth=smooth
        for l in f.loops:
            for k,layer in enumerate(layers):l[layer].uv=uv[vid[l.vert]][k]
    changed+=1;removed_tri+=24-len(new);resmax=max(resmax,err)
    if (gi+1)%4000==0:
        qa.update({'processed_components':gi+1,'changed_components':changed,'removed_triangles':removed_tri,'max_relative_residual':resmax});checkpoint()
bmesh.ops.delete(bm,geom=[e for e in bm.edges if not e.link_faces],context='EDGES')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
bm.normal_update();bm.to_mesh(copy);bm.free();copy.update()
assert not copy.validate(verbose=False) and protected(copy)==original
copy.calc_loop_triangles();assert len(copy.loop_triangles)==1599403-removed_tri
qa.update({'changed_components':changed,'skipped_components':skipped,'leaf_triangle_histogram':dict(hist),'triangles_after':len(copy.loop_triangles),'reduction':removed_tri/1599403,'max_relative_residual':resmax,'protected_coordinate_uv_exact':True,'all_leaf_components_retained_by_construction':True});checkpoint()
assert changed>0 and removed_tri>0
ob=bpy.data.objects.new('V89_oak_candidate',copy);study.collection.objects.link(ob)
old.hide_render=True;reference.hide_render=True;ob.hide_render=False
lo=Vector(tuple(min(v.co[i] for v in source.vertices) for i in range(3)));hi=Vector(tuple(max(v.co[i] for v in source.vertices) for i in range(3)));center=(lo+hi)*.5;extent=(hi-lo).length
assert abs(camera.data.ortho_scale-extent*1.05)<1e-5 and study.cycles.samples==24
def alpha(f):
    im=bpy.data.images.load(str(f.resolve()),check_existing=False);a=np.empty(len(im.pixels),dtype=np.float32);im.pixels.foreach_get(a);bpy.data.images.remove(im);return a[3::4]
for angle in (0,90,180,270):
    for elev in (0,35,-35):
        az=math.radians(angle);el=math.radians(elev);direction=Vector((math.cos(el)*math.cos(az),math.cos(el)*math.sin(az),math.sin(el)))
        camera.location=center+direction*(extent*2+1);camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
        name=f'oak_{angle}_{elev}_source.png';shutil.copyfile(verify(name),out/name)
        f=out/f'oak_{angle}_{elev}_v89.png';study.render.filepath=str(f.resolve())
        with bpy.context.temp_override(scene=study):bpy.ops.render.render(write_still=True,scene=study.name)
        a,b=alpha(out/name),alpha(f)
        qa['views'].append({'azimuth':angle,'elevation':elev,'soft_alpha_iou':float(np.minimum(a,b).sum()/np.maximum(a,b).sum()),'coverage_ratio':float(b.sum()/a.sum())});checkpoint()
qa['min_alpha_iou']=min(x['soft_alpha_iou'] for x in qa['views']);qa['max_coverage_deviation']=max(abs(x['coverage_ratio']-1) for x in qa['views'])
qa['screening']='PASS' if qa['min_alpha_iou']>=.92 and qa['max_coverage_deviation']<=.10 else 'HOLD'
bpy.context.window.scene=study;bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
glb=out/'v89_oak_candidate.glb';bpy.ops.export_scene.gltf(filepath=str(glb.resolve()),export_format='GLB',use_selection=True,export_animations=False)
qa['glb_sha256']=sha(glb)
dest=out/'v89_oak_candidate.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True);qa['native_sha256']=sha(dest)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()));assert protected(bpy.data.objects['V89_oak_candidate'].data)==original
qa['reopen_wood_exact']=True;qa['source_unchanged']=sha(src)==LOCK;assert qa['source_unchanged'];checkpoint();print('V89_OAK_DONE',json.dumps(qa))

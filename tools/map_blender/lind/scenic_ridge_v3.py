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

import bmesh
src,out,engine=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
lock='0597cad96ac6507997efe2c2a0ddaf144bf7b9b7e690fd54999ccd643d42d5cd'
assert bpy.app.version[:3]==(5,3,0) and sha(src)==lock
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()))
scene=bpy.context.scene
def digest(data,prop,count,typ):
    a=array(typ,[0])*count
    if count:data.foreach_get(prop,a)
    return hashlib.sha256(a.tobytes()).hexdigest()
def snap():
    return {o.name:(digest(o.data.vertices,'co',len(o.data.vertices)*3,'f'),digest(o.data.loops,'vertex_index',len(o.data.loops),'i'),digest(o.data.polygons,'loop_total',len(o.data.polygons),'i'),tuple((u.name,digest(u.data,'uv',len(u.data)*2,'f')) for u in o.data.uv_layers),tuple(m.name if m else None for m in o.data.materials),tuple(tuple(row) for row in o.matrix_world),o.hide_render) for o in bpy.context.scene.objects if o.type=='MESH'}
old=snap(); assert old
# Dedicated matched diagnostic from the earlier coastal composition review, not a game camera.
native_cam=scene.camera
cam=camera('F01_diagnostic',(30,-1,12),(-26,-63,2.5),36)
render_setup(scene)
render(scene,cam,out/'baseline.png')
# Two independent distant heightfield islands: non-playable, below water at the perimeter.
# Shape dimensions are provisional BU, not surveyed or canonical metres.
coll=bpy.data.collections.new('F01_SCENIC_ONLY_RIDGE_V3');scene.collection.children.link(coll)
rows=[]; made=[]
for k,(cx,cy,rx,ry,peak,col) in enumerate([(-48,-112,58,20,13,(.075,.114,.145)),(-28,-158,86,22,18,(.102,.145,.183))]):
    v=[]; f=[];nx=49;ny=17
    for j in range(ny):
        t=-1+2*j/(ny-1)
        for i in range(nx):
            s=-1+2*i/(nx-1)
            envelope=max(0,1-s*s)**1.4*max(0,1-t*t)**1.7
            variation=.66+.19*math.sin(s*5.8+k)+.10*math.cos(s*12.7+t*3)+.05*math.sin(s*24.5)
            z=-.7+peak*envelope*variation
            v.append((cx+rx*s,cy+ry*t+4*math.sin(s*4+k)*(1-t*t),z))
    for j in range(ny-1):
        for i in range(nx-1):
            a=j*nx+i;f.extend([(a,a+1,a+nx+1),(a,a+nx+1,a+nx)])
    perimeter=list(range(nx))+[j*nx+nx-1 for j in range(1,ny)]+list(range(nx*ny-2,nx*(ny-1)-1,-1))+[j*nx for j in range(ny-2,0,-1)]
    bottom=len(v);v.append((cx,cy,-1.5))
    for a,b in zip(perimeter,perimeter[1:]+perimeter[:1]):f.append((b,a,bottom))
    m=bpy.data.meshes.new('F01_ridge_%d'%k);m.from_pydata(v,[],f);m.update()
    bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    boundary=sum(e.is_boundary for e in bm.edges);nonmanifold=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True)
    assert boundary==nonmanifold==0 and volume>0
    bm.to_mesh(m);bm.free();m.update()
    o=bpy.data.objects.new(m.name,m);coll.objects.link(o);o['scenic_only']=True;o['canonical_transform']='UNDETERMINED'
    mat=simplemat('F01_atmospheric_ridge_%d'%k,col);m.materials.append(mat)
    for face in m.polygons:face.use_smooth=True
    m.calc_loop_triangles();rows.append(dict(name=o.name,vertices=len(m.vertices),triangles=len(m.loop_triangles),boundary=boundary,nonmanifold=nonmanifold,volume_BU3=volume));made.append(o)
bpy.context.view_layer.update()
new=snap();assert all(new[n]==a for n,a in old.items()) and len(new)==len(old)+2 and sha(src)==lock
q=dict(status='ISOLATED_SCENIC_FEASIBILITY',input_sha256=lock,protected_meshes=len(old),ridge=rows,frame='existing composition Z-up provisional BU; not metres',engine_metrics=metrics(engine,{'boundary_edges':0,'nonmanifold_edges':0,'added_triangles':4000},{'boundary_edges':sum(x['boundary'] for x in rows),'nonmanifold_edges':sum(x['nonmanifold'] for x in rows),'added_triangles':sum(x['triangles'] for x in rows)},{'boundary_edges':0,'nonmanifold_edges':0,'added_triangles':4000},{'boundary_edges':0,'nonmanifold_edges':0,'added_triangles':0}),limits=['Diagnostic camera, not game camera. No terrain/collision changes; isolated distant heightfield design, no D4/G1/G2/G4 acceptance.','Blueprint residual evaluation only, no Production OS native correction adapter.'])
# Restore original scene camera in native checkpoint; export only new ridge objects.
scene.camera=native_cam or cam
bpy.ops.object.select_all(action='DESELECT')
for o in made:o.select_set(True)
bpy.context.view_layer.objects.active=made[0]
bpy.ops.export_scene.gltf(filepath=str((out/'ridge.glb').resolve()),use_selection=True,export_extras=True,export_animations=False)
dest=out/'cliff_ridge_v3_UNAPPROVED.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()));scene=bpy.context.scene
assert snap()==new and sha(src)==lock
q['native_reopen']='PASS';finish(out,q)
render(scene,bpy.data.objects['F01_diagnostic'],out/'candidate.png')
cam2=camera('F01_oblique',(-105,-1,37),(-25,-100,5),34);render(scene,cam2,out/'oblique.png')
finish(out,q)

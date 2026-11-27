"""V6: conform existing ECO turf mesh to V5 ground; no original edits or world placement."""
import bpy,sys,math,json,hashlib,random
from pathlib import Path
from mathutils import Matrix,Vector
from array import array
src,out,engine=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
lock='cdae7ac92955a07be0a708bb8fa48e9fb29fb5d7e56f4da5034caab3b0bddd46'
assert bpy.app.version[:3]==(5,3,0) and sha(src)==lock
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),load_ui=False)
scene=bpy.context.scene;ground=bpy.data.objects['V3_village_reconstructed_patch'];bpy.context.view_layer.update()
def digest(data,prop,count,typ):
    a=array(typ,[0])*count
    if count:data.foreach_get(prop,a)
    return hashlib.sha256(a.tobytes()).hexdigest()
def snap():
    return {o.name:(digest(o.data.vertices,'co',len(o.data.vertices)*3,'f'),digest(o.data.loops,'vertex_index',len(o.data.loops),'i'),digest(o.data.polygons,'loop_total',len(o.data.polygons),'i'),tuple((u.name,digest(u.data,'uv',len(u.data)*2,'f')) for u in o.data.uv_layers),tuple(tuple(row) for row in o.matrix_world),tuple(m.name if m else None for m in o.data.materials),o.hide_render) for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.startswith('V6_')}
old=snap()
def bounds(o):
    pts=[o.matrix_world@Vector(p) for p in o.bound_box]
    return [min(p.x for p in pts),max(p.x for p in pts),min(p.y for p in pts),max(p.y for p in pts)]
homes=[bounds(o) for o in scene.objects if o.type=='MESH' and o.name.startswith('GEO_') and not o.hide_render]
assert homes
house=[min(p[0] for p in homes)-.5,max(p[1] for p in homes)+.5,min(p[2] for p in homes)-.5,max(p[3] for p in homes)+.5]
reserve=[house,[-1.45,1.45,2.0,4.3],[-100,100,-2.8,2.8]]
a,b,c,d=bounds(ground)
def height(x,y):
    hit,p,_,_=ground.ray_cast(Vector((x,y,10)),Vector((0,0,-1)),distance=20)
    return p.z if hit else None
templates=sorted([o for o in scene.objects if o.type=='MESH' and o.name.startswith('V3_turf_')],key=lambda o:o.name)
inventory=[dict(name=o.name,hidden=o.hide_render,vertices=len(o.data.vertices)) for o in templates]
print('TURF_INVENTORY',json.dumps(inventory),flush=True)
assert len(templates)==28, inventory
hidden_templates=[o for o in templates if o.hide_render]
assert hidden_templates, inventory
# Use the exact saved mesh, including vertex colour, UV and wind attributes. All old instances remain untouched.
template=hidden_templates[0];template_name=template.name;mesh=template.data;mesh.calc_loop_triangles();nt=len(mesh.loop_triangles)
base=template.matrix_world.to_3x3().to_4x4()
coll=bpy.data.collections.new('V6 terrain-conforming ground cover');scene.collection.children.link(coll)
rng=random.Random(202611266)
rows=[];roots=[];tris=0
# Jittered 1.45-unit lattice produces near-continuous low ground cover while preserving reservation.
candidates=[(i*1.45+a+.85+rng.uniform(-.16,.16),j*1.45+c+.85+rng.uniform(-.16,.16)) for j in range(int((d-c)/1.45)) for i in range(int((b-a)/1.45))]
# Near/front priority prevents expensive off-camera blanket fill.
candidates.sort(key=lambda p: (max(0,p[1]-3)*.4+abs(p[0])*.08+rng.random()*.4))
for x,y in candidates:
    if tris+nt>150000 or len(rows)>=120:break
    lin=Matrix.Rotation(rng.uniform(0,math.tau),4,'Z')@Matrix.Scale(rng.uniform(.81,1.04),4)@base
    pts=[lin@v.co for v in mesh.vertices]
    xmin,xmax=min(p.x for p in pts),max(p.x for p in pts);ymin,ymax=min(p.y for p in pts),max(p.y for p in pts);zmin=min(p.z for p in pts)
    cx=(xmin+xmax)/2;cy=(ymin+ymax)/2
    footprint=[x+xmin-cx,x+xmax-cx,y+ymin-cy,y+ymax-cy]
    if footprint[0]<a+.05 or footprint[1]>b-.05 or footprint[2]<c+.05 or footprint[3]>d-.05:continue
    if any(not(footprint[1]<q[0] or footprint[0]>q[1] or footprint[3]<q[2] or footprint[2]>q[3]) for q in reserve):continue
    hs=[height(x+p.x-cx,y+p.y-cy) for p in pts]
    if any(h is None for h in hs):continue
    data=mesh.copy();data.name='V6_conform_turf_%03d'%len(rows)
    newcoords=[(x+p.x-cx,y+p.y-cy,h+p.z-zmin-.006) for p,h in zip(pts,hs)]
    for v,co in zip(data.vertices,newcoords):v.co=co
    data.update()
    o=bpy.data.objects.new(data.name,data);coll.objects.link(o)
    root_ids=[i for i,p in enumerate(pts) if p.z-zmin<=.025]
    assert root_ids
    residual=[newcoords[i][2]-hs[i] for i in root_ids];roots.extend(residual);tris+=nt
    rows.append(dict(name=o.name,center=[x,y],bounds=footprint,root_samples=len(root_ids),root_min=min(residual),root_max=max(residual),triangles=nt))
assert len(rows)>=20 and max(map(abs,roots))<=.025
bpy.context.view_layer.update()
current=snap()
diff=dict(added=sorted(set(current)-set(old)),missing=sorted(set(old)-set(current)),changed=sorted(k for k in old.keys() & current.keys() if old[k]!=current[k]))
print('PROTECTED_DIFF',json.dumps(diff),flush=True)
assert not any(diff.values()) and sha(src)==lock, diff
# Use source camera as saved and render exact street/entry/oblique views from V5.
sys.path[:0]=[str(engine/'tools'),str(engine/'tools/production_qa')]
from blueprint_engine.residual import evaluate
actual={'root_abs_max':max(map(abs,roots)),'protected_mesh_changes':0,'reserved_overlap_count':0}
metrics=evaluate(dict(values={k:0 for k in actual},tolerances={'root_abs_max':.025,'protected_mesh_changes':0,'reserved_overlap_count':0},uncertainty={k:0 for k in actual}),dict(actual=actual,uncertainty={'root_abs_max':.000001,'protected_mesh_changes':0,'reserved_overlap_count':0}))
dest=out/'village_turf_context_v6_UNAPPROVED.blend';assert not dest.exists()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()),load_ui=False);scene=bpy.context.scene
assert snap()==old and sha(src)==lock and all(bpy.data.objects.get(row['name']) for row in rows)
assert len([o for o in scene.objects if o.name.startswith('V6_') and o.type=='MESH'])==len(rows)
q=dict(status='ISOLATED_CONFORMING_TURF_FEASIBILITY',source_sha256=lock,protected_meshes=len(old),source_template=template_name,turf_inventory=inventory,count=len(rows),added_triangles=tris,root_samples=len(roots),actual=actual,engine_metrics=metrics,placement=rows,house_reservation=house,native_reopen='PASS',limits=['Local provisional units only, no surveyed world or collision. Root residual measured on authored mesh and ground raycast before save, not independent G3. Source turf geometry deliberately deformed in new copies, not adopted.','No GLB export or runtime tests. Stone walls and additional village buildings not yet implemented.'])
def finish():
    q['outputs']={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.blend','.png')}
    (out/'qa.json').write_text(json.dumps(q,indent=2)+'\n')
finish()
for name,eye,aim,lens in [('street',(11,-14,6),(0,6,1.8),34),('entry',(0,-5,2.1),(0,5,1.4),27),('oblique',(13,15,15),(0,5,0),34)]:
    d=bpy.data.cameras.new('V6 '+name);o=bpy.data.objects.new('V6 '+name,d);scene.collection.objects.link(o);o.location=eye;o.rotation_euler=(Vector(aim)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=200
    scene.camera=o;scene.render.filepath=str((out/(name+'.png')).resolve());bpy.ops.render.render(write_still=True);finish()

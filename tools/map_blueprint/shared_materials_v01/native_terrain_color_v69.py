"""V69 isolated repair of missing existing shader input; no new geometry or material design."""
import bpy,sys,math,hashlib,json
from pathlib import Path
from array import array
from mathutils import Vector
src,out=map(Path,sys.argv[sys.argv.index('--')+1:])
out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lock='24bd47906a6ce456441147021929d543ee700624fc6779fc7e251133a196298a'
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
            colors={a.name:(a.domain,a.data_type,digest(a.data,'color',len(a.data)*4,'f')) for a in m.color_attributes if not(o.name==ext_name and a.name==attr)}
            uv={a.name:digest(a.data,'uv',len(a.data)*2,'f') for a in m.uv_layers}
            cache[m.name]=(digest(m.vertices,'co',len(m.vertices)*3,'f'),digest(m.loops,'vertex_index',len(m.loops),'i'),digest(m.polygons,'loop_start',len(m.polygons),'i'),digest(m.polygons,'loop_total',len(m.polygons),'i'),digest(m.polygons,'material_index',len(m.polygons),'i'),uv,colors,tuple(a.name if a else None for a in m.materials))
        result[o.name]=(cache[m.name],tuple(tuple(r) for r in o.matrix_world),o.hide_render,tuple(s.material.name if s.material else None for s in o.material_slots))
    return result
def rgba(x,y):
    a,b=(-205,140),(90,-90);vx,vy=b[0]-a[0],b[1]-a[1]
    t=max(0,min(1,((x-a[0])*vx+(y-a[1])*vy)/(vx*vx+vy*vy)))
    d=math.hypot(x-a[0]-t*vx,y-a[1]-t*vy)
    t=max(0,min(1,(d-1.1)/5.0));t=t*t*(3-2*t)
    patch=.5+.25*math.sin(x*.24+y*.16)+.15*math.cos(y*.37-x*.18)
    green=(.77+.10*patch,.94+.05*patch,.66+.14*patch);road=(.98,.90,.77)
    return tuple((1-t)*a+t*b for a,b in zip(road,green))+(1,)
def key(v):return tuple(round(float(x),5) for x in v[:2])
def vertices(o):return {key(o.matrix_world@v.co):v.index for v in o.data.vertices}
def err(a,b):return max(abs(float(x)-float(y)) for x,y in zip(a,b))
def uv_map(o):
    u=o.data.uv_layers.active;assert u is not None
    q={}
    for l in o.data.loops:
        k=l.vertex_index;v=tuple(u.data[l.index].uv)
        if k in q:assert err(q[k],v)<1e-6
        q[k]=v
    return q
scene=bpy.context.scene;ground=bpy.data.objects[src_name];ext=bpy.data.objects[ext_name]
assert len(ground.data.vertices)==3321 and len(ext.data.vertices)==705 and len(ext.data.polygons)==1288
assert ext.data.users==1
assert ground.data.materials[0]==ext.data.materials[0]
mat=ground.data.materials[0];nt=mat.node_tree
assert any(n.type=='VERTEX_COLOR' and n.layer_name==attr and n.outputs['Color'].is_linked for n in nt.nodes)
a=ground.data.color_attributes.get(attr);assert a and a.domain=='POINT' and a.data_type=='FLOAT_COLOR'
assert ext.data.color_attributes.get(attr) is None,'prior missing attribute no longer reproduced'
old=snap();assert len(old)==523
source_recipe_error=max(err(a.data[v.index].color,rgba(v.co.x,v.co.y)) for v in ground.data.vertices)
assert source_recipe_error<=1e-6,source_recipe_error
g,e=vertices(ground),vertices(ext);seam=sorted(g.keys()&e.keys());assert len(seam)==33
gu,eu=uv_map(ground),uv_map(ext)
uv_residual=max(err(gu[g[k]],eu[e[k]]) for k in seam);assert uv_residual<=1e-6,uv_residual
height_residual=max(abs((ground.matrix_world@ground.data.vertices[g[k]].co).z-(ext.matrix_world@ext.data.vertices[e[k]].co).z) for k in seam);assert height_residual<=1e-6
# The only actual model correction: recreate the already-required shader input.
new=ext.data.color_attributes.new(name=attr,type='FLOAT_COLOR',domain='POINT')
inv=ground.matrix_world.inverted()
for v in ext.data.vertices:
    q=inv@(ext.matrix_world@v.co)
    new.data[v.index].color=rgba(q.x,q.y)
# Copy the exact source values at the known boundary (including float32 rounding).
for k in seam:new.data[e[k]].color=a.data[g[k]].color
ext.data.update()
assert snap()==old
color_residual=max(err(new.data[e[k]].color,a.data[g[k]].color) for k in seam);assert color_residual==0
dest=out/'v69_terrain_color_recovery.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()))
assert snap()==old and sha(src)==lock
scene=bpy.context.scene;ground=bpy.data.objects[src_name];ext=bpy.data.objects[ext_name]
a=ground.data.color_attributes[attr];new=ext.data.color_attributes[attr]
assert new.domain=='POINT' and new.data_type=='FLOAT_COLOR' and len(new.data)==705
assert max(err(new.data[e[k]].color,a.data[g[k]].color) for k in seam)==0
assert ground.data.materials[0]==ext.data.materials[0]
qa={'status':'ATTRIBUTE_REPAIR_NATIVE_REOPEN_PASS_RENDER_PENDING','source_sha256':lock,'blender':bpy.app.version_string,'protected_meshes_exact':len(old),'attribute':attr,'original_attribute_recipe_residual':source_recipe_error,'added_attribute_vertices':len(new.data),'seam_count':len(seam),'seam_rgba_residual':color_residual,'seam_uv_residual':uv_residual,'seam_height_residual_m':height_residual,'native_sha256':sha(dest),'limits':['No new geometry or material graph. Existing scenic extension only; noncanonical terrain. This verifies attribute restoration and native reopen, not independent G2/D4/G4.']}
(out/'v69_qa.json').write_text(json.dumps(qa,indent=2)+'\n')
# Reuse V58 exact saved camera definitions, light setup and render settings.
views=json.loads((src.parent/'v58_qa.json').read_text())['views']
cam=scene.camera
assert scene.render.engine=='CYCLES' and scene.render.resolution_x==960 and scene.render.resolution_y==540
for i in (0,2):
    aa,bb,l=views[i];cam.location=aa;cam.rotation_euler=(Vector(bb)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=l
    scene.render.filepath=str((out/f'v69_after_{i}.png').resolve());bpy.ops.render.render(write_still=True)
assert sha(src)==lock
qa['status']='ATTRIBUTE_REPAIR_NATIVE_REOPEN_AND_MATCHED_RENDER_COMPLETE'
qa['outputs']={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.blend','.png')}
(out/'v69_qa.json').write_text(json.dumps(qa,indent=2)+'\n');print(qa)

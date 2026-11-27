"""V12 CG-led local stone-paved street; irregular individually closed beveled stone meshes."""
import bpy,bmesh,sys,math,hashlib,json,random
from pathlib import Path
from mathutils import Vector
from array import array
src,cg,out,engine=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
lock='6964953322cd2cf53add08011a37c5853ec4b9f49ccffaa11152f3b53317b730'
cghash='c55af0770e0aa7c876575e57e4016df3280816459efd41f7200fa5ed3b51726a'
assert bpy.app.version[:3]==(5,3,0) and sha(src)==lock and sha(cg)==cghash
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),load_ui=False)
scene=bpy.context.scene;bpy.context.view_layer.update()
grounds=[bpy.data.objects[n] for n in ['V3_village_reconstructed_patch','V8_west_grade','V9_east_grade','V10_perimeter_heightfield']]
def dg(data,prop,n,t):
    a=array(t,[0])*n
    if n:data.foreach_get(prop,a)
    return hashlib.sha256(a.tobytes()).hexdigest()
def snap():
    return {o.name:(dg(o.data.vertices,'co',len(o.data.vertices)*3,'f'),dg(o.data.loops,'vertex_index',len(o.data.loops),'i'),dg(o.data.polygons,'material_index',len(o.data.polygons),'i'),tuple((u.name,dg(u.data,'uv',len(u.data)*2,'f')) for u in o.data.uv_layers),tuple(tuple(row) for row in o.matrix_world),tuple(m.name if m else None for m in o.data.materials),o.hide_render) for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.startswith('V12_')}
old=snap();assert len(old)==320
def hit(x,y):
    for g in grounds:
        inv=g.matrix_world.inverted();ok,p,_,_=g.ray_cast(inv@Vector((x,y,30)),inv.to_3x3()@Vector((0,0,-1)),distance=100)
        if ok:return float((g.matrix_world@p).z)
    raise ValueError((x,y))
# Within the already reserved existing straight core route, add a wandering paved inner band.
# CG supplies visible irregular paving, not world scale. All following numbers are proposed local BU.
xmin,xmax=-29.0,35.0;half=1.55
rng=random.Random(26112012)
def center(x):return .27*math.sin(x*.16)+.10*math.sin(x*.36)
seeds=[]
for row in range(7):
    u=-half+(row+.5)*2*half/7
    x=xmin+rng.uniform(.12,.4)
    while x<xmax:
        seeds.append((x,u+rng.uniform(-.13,.13)));x+=rng.uniform(.33,.64)
# Voronoi cells in route coordinates clipped to road band; no grid of identical cuboids.
# Sites separated, exact bisector clipping, then shrink each cell for explicit mortar joints.
def clip(poly,a,b,c):
    if not poly:return []
    result=[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        v=a*p[0]+b*p[1]-c;w=a*q[0]+b*q[1]-c
        if v<=0:result.append(p)
        if (v<=0)!=(w<=0):
            t=v/(v-w);result.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
    return result
def area(p):return .5*sum(x*y2-x2*y for (x,y),(x2,y2) in zip(p,p[1:]+p[:1]))
def contract(poly,margin):
    # inward offset by each convex polygon side, no shared surface crossings
    r=poly[:]
    for (x,y),(X,Y) in zip(poly,poly[1:]+poly[:1]):
        a,b=Y-y,x-X
        r=clip(r,a,b,a*x+b*y-margin*math.hypot(a,b))
    return r
# Use existing V7 CC0 stone PBR; UV-based maps already packed, independently retained.
base=bpy.data.materials.get('V7 garden stone PBR');assert base and base.use_nodes
mats=[]
for k,tint in enumerate([(.88,.82,.72,1),(1,.95,.86,1),(.74,.76,.73,1),(.95,.88,.77,1),(.78,.69,.61,1)]):
    mat=base.copy();mat.name='V12_paving_%02d'%k;ns=mat.node_tree.nodes;ls=mat.node_tree.links
    bs=next(n for n in ns if n.type=='BSDF_PRINCIPLED')
    link=bs.inputs['Base Color'].links[0].from_socket
    mix=ns.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=tint
    ls.new(link,mix.inputs[1]);ls.new(mix.outputs[0],bs.inputs['Base Color'])
    mats.append(mat)
verts=[];faces=[];slots=[];uvs=[];rows=[];topres=[]
for x,u in seeds:
    p=[(xmin,-half),(xmax,-half),(xmax,half),(xmin,half)]
    for X,U in seeds:
        if (X,U)==(x,u) or abs(X-x)>2 or abs(U-u)>1.5:continue
        p=clip(p,2*(X-x),2*(U-u),X*X+U*U-x*x-u*u)
        if not p:break
    if not p or len(p)<3 or area(p)<.025:continue
    p=contract(p,rng.uniform(.009,.017))
    if len(p)<3 or area(p)<.025:continue
    q=contract(p,.022)
    if len(q)!=len(p):continue
    # Every stone has a lower ring, shoulder and inset top. Use equal vertex counts and CCW rings.
    i0=len(verts);N=len(p);zrel=rng.uniform(.035,.065)
    cx=sum(v[0] for v in p)/N;cy=sum(v[1] for v in p)/N
    offset=(rng.random()*.45,rng.random()*.45)
    for ring,rel in [(p,-.055),(p,zrel-.023),(q,zrel)]:
        for px,py in ring:
            wy=py+center(px);z=hit(px,wy);verts.append((px,wy,z+rel));uvs.append(((px-cx)*.65+.5+offset[0],(py-cy)*.65+.5+offset[1]))
            if ring is q:topres.append(rel)
    color=rng.choices(range(5),weights=[2,5,2,3,1])[0]
    def face(ids):faces.append(tuple(i0+j for j in ids));slots.append(color)
    face(list(reversed(range(N))))
    for a in range(N):
        b=(a+1)%N
        face([a,b,b+N,a+N]);face([a+N,b+N,b+2*N,a+2*N])
    face([a+2*N for a in range(N)])
    rows.append(dict(center=[cx,cy+center(cx)],area=area(p),vertices=3*N,top_offset=zrel))
assert len(rows)>=500,len(rows)
mesh=bpy.data.meshes.new('V12 individual rounded paving stones');mesh.from_pydata(verts,[],faces);mesh.update()
for m in mats:mesh.materials.append(m)
uv=mesh.uv_layers.new(name='UVMap')
for p,slot in zip(mesh.polygons,slots):
    p.material_index=slot
    for j in p.loop_indices:uv.data[j].uv=uvs[mesh.loops[j].vertex_index]
o=bpy.data.objects.new('V12_paving_stonework',mesh);scene.collection.objects.link(o)
bm=bmesh.new();bm.from_mesh(mesh)
bad=dict(boundary=sum(e.is_boundary for e in bm.edges),nonmanifold=sum(not e.is_manifold for e in bm.edges),degenerate=sum(f.calc_area()<1e-9 for f in bm.faces))
assert not any(bad.values()),bad
bm.free();mesh.calc_loop_triangles()
# Surface offsets of actual final vertices, no navigation claims.
top_sample=[]
for r in rows:
    assert abs(r['center'][1])<2.0
assert min(topres)>.03 and max(topres)<.066
bpy.context.view_layer.update();assert snap()==old and sha(src)==lock
# Source-grounded D1 relation ledger: observations vs authored coordinates; other modules deferred.
plan=dict(source_sha256=cghash,observed=['irregular stone lane','stone house frontage','large tree','standing stone','river','arched bridge','wood and stone boundaries','training slope','wooded mountain background'],module='paving only',authored={'x_bounds':[xmin,xmax],'width':half*2,'unit':'provisional BU','top_offset':[.035,.065]},unresolved=['physical scale','world transformation','bridge and river alignment','building identities','D4 independent review'])
(out/'composition.json').write_text(json.dumps(plan,indent=2)+'\n')
dest=out/'village_cg_paving_v12_UNAPPROVED.blend';assert not dest.exists()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()),load_ui=False);scene=bpy.context.scene
assert snap()==old and sha(src)==lock
paving=bpy.data.objects['V12_paving_stonework'];paving.data.calc_loop_triangles()
assert len(paving.data.vertices)==len(verts) and len(paving.data.polygons)==len(faces)
assert max((v.co-Vector(p)).length for v,p in zip(paving.data.vertices,verts))<1e-5
q=dict(status='CG_LED_SCENIC_PAVING_CANDIDATE',source_sha256=lock,cg_sha256=cghash,protected_meshes=len(old),stones=len(rows),vertices=len(verts),triangles=len(paving.data.loop_triangles),top_offset_min=min(topres),top_offset_max=max(topres),top_samples=len(topres),mesh_checks=bad,native_reopen='PASS',limits=['Scenic local BU only; authored size not measured from CG. No gameplay collision or world placement. Original V10 unchanged. Stone material copied from V7 approved-for-testing CC0 source, not CG pixel reuse. G2/D4 pending.'])
def finish():
    q['outputs']={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.blend','.png','.json') and p.name!='qa.json'}
    (out/'qa.json').write_text(json.dumps(q,indent=2)+'\n')
finish()
scene.render.resolution_x=1200;scene.render.resolution_y=675;scene.cycles.samples=16
for name,eye,aim,lens in [('street',(-8,-1.6,2.5),(18,2.8,2.3),31),('paving_detail',(12,-3,2.6),(19,.5,.35),40),('overview',(3,-34,48),(3,7,0),28)]:
    d=bpy.data.cameras.new('V12 '+name);o=bpy.data.objects.new('V12 '+name,d);scene.collection.objects.link(o);o.location=eye;o.rotation_euler=(Vector(aim)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=300
    scene.camera=o;scene.render.filepath=str((out/(name+'.png')).resolve());bpy.ops.render.render(write_still=True);finish()

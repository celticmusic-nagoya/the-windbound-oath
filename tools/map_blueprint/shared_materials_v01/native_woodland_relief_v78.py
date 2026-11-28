"""V78 isolated woodland understory feasibility, preserving V77 source."""
import bpy,sys,math,hashlib,json,random,collections
from pathlib import Path
from array import array
from mathutils import Vector,Matrix
from mathutils.geometry import convex_hull_2d
from mathutils.bvhtree import BVHTree
src,out=map(Path,sys.argv[sys.argv.index('--')+1:])
out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lock='1e7e74a3f1d33958eccb7a55e222e586ba6cb018c2ac9585508904985c6cfccf'
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




scene=bpy.context.scene
old=snap();assert len(old)==693
far=bpy.data.objects['V77_SCENIC_ONLY_FAR_RELIEF']
assert len(far.data.vertices)==396 and len(far.data.polygons)==650
original=far.data.materials[0]
mat=original.copy();mat.name='V78_woodland_relief_candidate';far.data.materials[0]=mat
n=mat.node_tree.nodes;l=mat.node_tree.links
# Restrict modifications to the two far PBR branches. Preserve the exact seam shader and factor.
branches=[b for b in n if b.type=='BSDF_PRINCIPLED' and b.inputs['Normal'].is_linked and b.inputs['Normal'].links[0].from_node.type=='NORMAL_MAP' and b.inputs['Normal'].links[0].from_node.uv_map.startswith('V77_far_projection_')]
assert len(branches)==2
geo=n.new('ShaderNodeNewGeometry')
noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=.23;noise.inputs['Detail'].default_value=3;noise.inputs['Roughness'].default_value=.7;l.new(geo.outputs['Position'],noise.inputs['Vector'])
ramp=n.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position=.27;ramp.color_ramp.elements[0].color=(.44,.48,.35,1)
ramp.color_ramp.elements[1].position=.76;ramp.color_ramp.elements[1].color=(.16,.38,.11,1)
ramp.color_ramp.elements.new(.52).color=(.26,.49,.16,1)
l.new(noise.outputs['Fac'],ramp.inputs[0])
for b in branches:
    prev=b.inputs['Base Color'].links[0].from_socket
    q=n.new('ShaderNodeMixRGB');q.blend_type='MULTIPLY';q.inputs[0].default_value=.72
    l.new(prev,q.inputs[1]);l.new(ramp.outputs[0],q.inputs[2]);l.new(q.outputs[0],b.inputs['Base Color'])
# Existing, source-derived meshes only. New scenic instances, no additional cards.
families={'moss':'V21_M_','shrub':'V18_S_','fern':'V18_0_'}
templates={k:next((o for o in sorted(scene.objects,key=lambda x:x.name) if o.type=='MESH' and o.name.startswith(p)),None) for k,p in families.items()}
assert all(templates.values()),[(k,o.name if o else None) for k,o in templates.items()]
coll=bpy.data.collections.new('V78_SCENIC_ONLY_UNDERSTORY');scene.collection.children.link(coll)
rng=random.Random(2026112678)
def ground(x,y):
    ok,p,norm,i=far.ray_cast(Vector((x,y,100)),Vector((0,0,-1)),distance=200)
    return (p.z,norm.z) if ok else None
# Conservative exclusion of existing non-terrain objects with local footprints.
obstacles=[]
for o in scene.objects:
    if o.type!='MESH' or o==far or o.name in (ext_name,src_name):continue
    pts=[o.matrix_world@Vector(p) for p in o.bound_box]
    a,b=min(p.x for p in pts),max(p.x for p in pts);c,d=min(p.y for p in pts),max(p.y for p in pts)
    if b-a<25 and d-c<25:obstacles.append((a,b,c,d))
placed=[];tri=0
for i in range(2400):
    if len(placed)>=60:break
    x=rng.uniform(65,180);y=rng.uniform(-180,-65)
    dist=math.hypot(x-min(x,135),y-max(y,-135))
    if not 5<dist<38:continue
    h=ground(x,y)
    if not h or h[1]<.86:continue
    patch=math.sin(x*.29+y*.16)+math.cos(y*.31-x*.13)
    if patch<.1:continue
    kind=rng.choices(['moss','shrub','fern'],[5,3,2])[0]
    t=templates[kind];t.data.calc_loop_triangles();nt=len(t.data.loop_triangles)
    if tri+nt>60000:continue
    # Use source transform orientation/scale, but replace translation. Normalize to scenic size.
    linear=t.matrix_world.to_3x3().to_4x4()
    pts=[linear@v.co for v in t.data.vertices]
    height=max(p.z for p in pts)-min(p.z for p in pts)
    if height<.0001:continue
    target=rng.uniform(*{'moss':(.22,.45),'shrub':(.7,1.5),'fern':(.45,.9)}[kind])
    fac=target/height
    linear=Matrix.Rotation(rng.uniform(0,math.tau),4,'Z')@Matrix.Scale(fac,4)@linear
    pts=[linear@v.co for v in t.data.vertices]
    mn=Vector(tuple(min(p[j] for p in pts) for j in range(3)));mx=Vector(tuple(max(p[j] for p in pts) for j in range(3)))
    cx=(mn.x+mx.x)/2;cy=(mn.y+mx.y)/2
    radius=max(math.hypot(p.x-cx,p.y-cy) for p in pts)
    if not .05<radius<3:continue
    if any(a-radius-.2<x<b+radius+.2 and c-radius-.2<y<d+radius+.2 for a,b,c,d in obstacles):continue
    if any(math.hypot(x-p['x'],y-p['y'])<radius+p['radius']+.35 for p in placed):continue
    # Ground all lowest mesh vertices against actual triangle surface; bound burial and floating.
    roots=[p for p in pts if p.z<=mn.z+max(.035,target*.08)]
    hits=[(p,ground(x+p.x-cx,y+p.y-cy)) for p in roots]
    if not hits or any(hh is None for p,hh in hits):continue
    offsets=[hh[0]-p.z for p,hh in hits]
    zz=max(offsets)-.015
    residual=[p.z+zz-hh[0] for p,hh in hits]
    if max(residual)>.22:continue
    o=bpy.data.objects.new('V78_'+kind+'_%03d'%len(placed),t.data);coll.objects.link(o)
    o.matrix_world=Matrix.Translation(Vector((x-cx,y-cy,zz)))@linear
    o['scenic_only']=True
    placed.append(dict(name=o.name,source=t.name,x=x,y=y,radius=radius,root_min=min(residual),root_max=max(residual),triangles=nt));tri+=nt
assert len(placed)>=24, len(placed)
bpy.context.view_layer.update();s=snap()
assert len(s)==693+len(placed)
assert all(s[k]==v for k,v in old.items() if k!=far.name)
assert s[far.name][0][:-1]==old[far.name][0][:-1] and s[far.name][1:3]==old[far.name][1:3]
assert sha(src)==lock
dest=out/'v78_woodland_feasibility.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()));scene=bpy.context.scene
assert snap()==s and sha(src)==lock
q=dict(status='SCENIC_UNDERSTORY_FEASIBILITY',source_sha256=lock,native_sha256=sha(dest),blender=bpy.app.version_string,protected_meshes_exact=692,far_geometry_uv_color_exact=True,added_triangles=tri,placements=placed,limits=['Provisional scenic only; no playable terrain or collision edits.','Existing moss/shrub/fern mesh reuse, no new card-count or color-only trial.','Root residual sampled at lowest vertices; not full collision or D4/G2/G4 acceptance.'])
(out/'v78_qa.json').write_text(json.dumps(q,indent=2)+'\n')
eye=Vector((78.17052459716797,-80.77701568603516,29.82533073425293));aim=Vector((93.94316101074219,-93.07432556152344,30.988130569458008));side=Vector((.6148655745981655,.788631932636555,0))
cam=scene.camera
assert scene.render.engine=='CYCLES' and scene.render.resolution_x==960 and scene.render.resolution_y==540
for name,aa in [('v78_matched',eye),('v78_lateral_diagnostic',eye+side*8)]:
    cam.location=aa;cam.rotation_euler=(aim-aa).to_track_quat('-Z','Y').to_euler();cam.data.lens=22
    scene.render.filepath=str((out/(name+'.png')).resolve());bpy.ops.render.render(write_still=True)
q['outputs']={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.blend','.png')};(out/'v78_qa.json').write_text(json.dumps(q,indent=2)+'\n')

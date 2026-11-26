"""V77 bounded scenic relief and lower-background photo PBR, not canonical or playable terrain."""
import bpy,sys,math,hashlib,json,random,collections
from pathlib import Path
from array import array
from mathutils import Vector,Matrix
from mathutils.geometry import convex_hull_2d
from mathutils.bvhtree import BVHTree
src,out=map(Path,sys.argv[sys.argv.index('--')+1:])
out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lock='a0de38b06183e99a7513d04463d7f4ea72113faf6e8dc2316fc98ed3dfb729f9'
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



scene=bpy.context.scene;old=snap();assert len(old)==692
qa=src.parent/'v76_qa.json';assert sha(qa)=='78304d5ac695fe5a2297b7849166f49fb8805f5d79757a37d5c7d2331f9c9210'
terrain=bpy.data.objects[src_name];ext=bpy.data.objects[ext_name]
assert len(ext.data.vertices)==705 and len(ext.data.polygons)==1288
assert ext.data.materials[0]==terrain.data.materials[0]
source={(round(p.x,5),round(p.y,5)):(float(p.z),v.index) for v in ext.data.vertices for p in [ext.matrix_world@v.co]}
assert len(source)==705
xs=[i*2.5 for i in range(24,55)]+[140,147.5,160,175,195]
ys=[-195,-175,-160,-147.5,-140]+[i*2.5 for i in range(-54,-23)]
v=[];f=[];idx={}
def vertex(x,y):
    key=(x,y)
    if key not in idx:
        bx,by=min(x,135),max(y,-135);base=source[(bx,by)][0]
        d=math.hypot(x-bx,y-by);t=min(d/40,1)
        z=base+t*t*(3-2*t)*(12+2.5*math.sin((x+y)*.055)+1.5*math.cos((x-y)*.037))
        idx[key]=len(v);v.append((x,y,z))
    return idx[key]
for x,x1 in zip(xs,xs[1:]):
    for y,y1 in zip(ys,ys[1:]):
        if x<135 and y>=-135:continue
        a,b,c,d=[vertex(*p) for p in ((x,y),(x1,y),(x1,y1),(x,y1))]
        f.extend(((a,b,c),(a,c,d)))
assert len(v)==396 and len(f)==650
seam=sorted(set(idx)&set(source));assert len(seam)==61
assert max(abs(v[idx[k]][2]-source[k][0]) for k in seam)==0
edges=collections.Counter(tuple(sorted((a,b))) for tri in f for a,b in zip(tri,tri[1:]+tri[:1]))
assert max(edges.values())==2
seamedges=[tuple(sorted((idx[k],idx[j]))) for k,j in zip(seam,seam[1:]) if math.dist(k,j)==2.5]
assert len(seamedges)==60 and all(edges[k]==1 for k in seamedges)
me=bpy.data.meshes.new('V77_SCENIC_FAR_RELIEF_MESH');me.from_pydata(v,[],f);me.update()
coll=bpy.data.collections.new('V77_SCENIC_ONLY_FAR_RELIEF');scene.collection.children.link(coll)
o=bpy.data.objects.new('V77_SCENIC_ONLY_FAR_RELIEF',me);coll.objects.link(o)
o['not_canonical']=True;o['scope']='local visual feasibility only, not playable or collision data'
uv=me.uv_layers.new(name=ext.data.uv_layers.active.name);uvname=uv.name
for loop in me.loops:
    x,y,z=v[loop.vertex_index];uv.data[loop.index].uv=(x/2,y/2)
old_uv={}
for loop in ext.data.loops:
    xy=tuple(ext.data.uv_layers.active.data[loop.index].uv)
    if loop.vertex_index in old_uv:assert old_uv[loop.vertex_index]==xy
    old_uv[loop.vertex_index]=xy
assert max(abs(a-b) for k in seam for a,b in zip(old_uv[source[k][1]],(k[0]/2,k[1]/2)))==0
old_color=ext.data.color_attributes[attr];assert old_color.domain=='POINT' and old_color.data_type=='FLOAT_COLOR'
col=me.color_attributes.new(name=attr,type='FLOAT_COLOR',domain='POINT')
for key,i in idx.items():
    x,y=key;bx,by=min(x,135),max(y,-135)
    col.data[i].color=old_color.data[source[(bx,by)][1]].color
for key in seam:assert tuple(col.data[idx[key]].color)==tuple(old_color.data[source[key][1]].color)
assert max(abs(me.vertices[idx[k]].co.z-source[k][0]) for k in seam)==0
for poly in me.polygons:poly.use_smooth=True
# Preserve original shared material and fade only the new far mesh from exact existing shader at seam.
mat=ext.data.materials[0].copy();mat.name='V77_far_photo_relief_candidate';me.materials.append(mat)
nt=mat.node_tree;n=nt.nodes;l=nt.links
output=next(x for x in n if x.type=='OUTPUT_MATERIAL' and x.is_active_output);old_shader=output.inputs['Surface'].links[0].from_socket
locks={'diffuse':'9c38b2b151a0415457a6914966422cfca5a546c94674442e5395e0b1e908a196','nor_gl':'af0346114834c347a8d6a138f6ea16a97b0bec8d6e4db32c24f1c7e482163235','rough':'ed2dd60a10242640b1738760015cfae85c8526a79dbf5da563fdffdf30828eae'}
images={}
for key,expected in locks.items():
    im=next(i for i in bpy.data.images if 'forest_leaves_02_'+key in i.name and i.packed_file)
    assert hashlib.sha256(bytes(im.packed_file.data)).hexdigest()==expected,key
    images[key]=im
geo=n.new('ShaderNodeNewGeometry');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=.09;noise.inputs['Detail'].default_value=2;l.new(geo.outputs['Position'],noise.inputs['Vector'])
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.22;ramp.color_ramp.elements[0].color=(.40,.65,.31,1);ramp.color_ramp.elements[1].position=.78;ramp.color_ramp.elements[1].color=(.75,.92,.55,1);l.new(noise.outputs['Fac'],ramp.inputs[0])
noise2=n.new('ShaderNodeTexNoise');noise2.inputs['Scale'].default_value=.17;noise2.inputs['Detail'].default_value=2;l.new(geo.outputs['Position'],noise2.inputs['Vector'])
# Two independent UV tangents and matching normal maps, not a rotated normal sampled with the wrong tangent frame.
shaders=[]
for i,(angle,rep,off) in enumerate([(0,3,(.11,.24)),(31,4.7,(.61,.39))]):
    un=me.uv_layers.new(name=f'V77_far_projection_{i}')
    ang=math.radians(angle);cs,sn=math.cos(ang),math.sin(ang)
    for loop in me.loops:
        x,y,z=v[loop.vertex_index];un.data[loop.index].uv=((cs*x-sn*y)/rep+off[0],(sn*x+cs*y)/rep+off[1])
    uvnode=n.new('ShaderNodeUVMap');uvnode.uv_map=un.name
    bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Metallic'].default_value=0
    tex={}
    for k,im in images.items():
        t=n.new('ShaderNodeTexImage');t.image=im;t.extension='REPEAT';l.new(uvnode.outputs['UV'],t.inputs['Vector']);tex[k]=t
    tint=n.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1;l.new(tex['diffuse'].outputs['Color'],tint.inputs[1]);l.new(ramp.outputs['Color'],tint.inputs[2]);l.new(tint.outputs[0],bs.inputs['Base Color'])
    nm=n.new('ShaderNodeNormalMap');nm.uv_map=un.name;nm.inputs['Strength'].default_value=.4;l.new(tex['nor_gl'].outputs['Color'],nm.inputs['Color']);l.new(nm.outputs['Normal'],bs.inputs['Normal']);l.new(tex['rough'].outputs['Color'],bs.inputs['Roughness'])
    shaders.append(bs.outputs['BSDF'])
me.uv_layers.active_index=0
m=n.new('ShaderNodeMixShader');l.new(noise2.outputs['Fac'],m.inputs[0]);l.new(shaders[0],m.inputs[1]);l.new(shaders[1],m.inputs[2])
# Seam blending is per-vertex scalar; exact zero at the protected old boundary.
blend=me.attributes.new('V77_far_blend','FLOAT','POINT')
for key,i in idx.items():
    x,y=key;d=math.hypot(x-min(x,135),y-max(y,-135));t=min(d/25,1);blend.data[i].value=t*t*(3-2*t)
assert all(blend.data[idx[k]].value==0 for k in seam)
a=n.new('ShaderNodeAttribute');a.attribute_name=blend.name
m2=n.new('ShaderNodeMixShader');l.new(a.outputs['Fac'],m2.inputs[0]);l.new(old_shader,m2.inputs[1]);l.new(m.outputs[0],m2.inputs[2]);l.new(m2.outputs[0],output.inputs['Surface'])
bpy.context.view_layer.update();s=snap();assert all(s[k]==val for k,val in old.items());assert len(s)==693 and sha(src)==lock
dest=out/'v77_far_relief_feasibility.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()));scene=bpy.context.scene
assert snap()==s and sha(src)==lock
new=bpy.data.objects['V77_SCENIC_ONLY_FAR_RELIEF'];assert len(new.data.vertices)==396 and len(new.data.polygons)==650
assert all(new.data.attributes['V77_far_blend'].data[idx[k]].value==0 for k in seam)
q={'status':'SCENIC_RELIEF_PHOTO_PBR_FEASIBILITY','source_sha256':lock,'native_sha256':sha(dest),'blender':bpy.app.version_string,'protected_meshes_exact':692,'added_vertices':396,'added_triangles':650,'seam_points':61,'seam_edges':60,'seam_height_residual_m':0,'seam_uv_residual':0,'seam_color_residual':0,'source_maps_verified':3,'material_transition':'Existing shader at seam; two rotated PBR projections with broad albedo variation and 25m fade. Different from standalone baked atlas.','limits':['Authored scenic extension, not surveyed terrain or playable collision.','Normal seam and visual transition need actual image inspection. No V75 cards in isolated A/B.','No independent D4/G2 or Android/G4.']}
(out/'v77_qa.json').write_text(json.dumps(q,indent=2)+'\n')
eye=Vector((78.17052459716797,-80.77701568603516,29.82533073425293));aim=Vector((93.94316101074219,-93.07432556152344,30.988130569458008));side=Vector((.6148655745981655,.788631932636555,0))
cam=scene.camera
assert scene.render.engine=='CYCLES' and scene.render.resolution_x==960 and scene.render.resolution_y==540
for name,aa,bb in [('v77_matched',eye,aim),('v77_lateral_diagnostic',eye+side*8,aim)]:
    cam.location=aa;cam.rotation_euler=(bb-aa).to_track_quat('-Z','Y').to_euler();cam.data.lens=22
    scene.render.filepath=str((out/(name+'.png')).resolve());bpy.ops.render.render(write_still=True)
q['outputs']={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.blend','.png')};(out/'v77_qa.json').write_text(json.dumps(q,indent=2)+'\n');print(q)

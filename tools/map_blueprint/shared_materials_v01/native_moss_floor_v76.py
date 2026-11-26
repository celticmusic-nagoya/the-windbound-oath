"""V76 reversible ground-material A/B, separate from fixed-vista candidate; no geometry edits."""
import bpy,sys,math,hashlib,json,random,collections
from pathlib import Path
from array import array
from mathutils import Vector,Matrix
from mathutils.geometry import convex_hull_2d
from mathutils.bvhtree import BVHTree
src,out=map(Path,sys.argv[sys.argv.index('--')+1:])
out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lock='9ae2baa35f9d9d11a17a720f1e8fa1dc7cda90e40275a581b788d118b66bfbf2'
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
qa=src.parent/'v73_qa.json';assert sha(qa)=='f133fec17bf731b35769b37eafb160373c496a5e43fde7a7cb1a51db4a768e65'
terrain=bpy.data.objects[src_name];ext=bpy.data.objects[ext_name];orig=terrain.data.materials[0]
assert ext.data.materials[0]==orig and orig.name=='V73_irish_floor_PBR_feasibility'
mat=orig.copy();mat.name='V76_moss_floor_candidate';nt=mat.node_tree;n=nt.nodes;l=nt.links
assert nt!=orig.node_tree
leaf=next(x for x in n if x.type=='TEX_IMAGE' and x.image and 'forest_leaves_02_diffuse' in x.image.name)
assert leaf.image.packed_file
assert hashlib.sha256(bytes(leaf.image.packed_file.data)).hexdigest()=='9c38b2b151a0415457a6914966422cfca5a546c94674442e5395e0b1e908a196'
bs=next(x for x in n if x.type=='BSDF_PRINCIPLED' and x.inputs['Base Color'].is_linked and x.inputs['Base Color'].links[0].from_node==leaf)
output=next(x for x in n if x.type=='OUTPUT_MATERIAL' and x.is_active_output)
mix=output.inputs['Surface'].links[0].from_node
assert mix.type=='MIX_SHADER' and mix.inputs[0].is_linked and mix.inputs[2].links[0].from_node==bs
old_weight=mix.inputs[0].links[0].from_socket
def setv(sock,x):
    if isinstance(x,(int,float,tuple,list)):sock.default_value=x
    else:l.new(x,sock)
def op(kind,a,b):
    q=n.new('ShaderNodeMath');q.operation=kind;setv(q.inputs[0],a);setv(q.inputs[1],b);return q.outputs[0]
def smooth(a,b,x):
    q=n.new('ShaderNodeMapRange');q.clamp=True;q.interpolation_type='SMOOTHSTEP'
    setv(q.inputs['Value'],x);q.inputs['From Min'].default_value=a;q.inputs['From Max'].default_value=b
    return q.outputs['Result']
def vec(kind,a,b):
    q=n.new('ShaderNodeVectorMath');q.operation=kind;setv(q.inputs[0],a);setv(q.inputs[1],b);return q.outputs['Value'] if kind in ('DOT_PRODUCT','DISTANCE') else q.outputs['Vector']
geo=n.new('ShaderNodeNewGeometry');se=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Position'],se.inputs[0]);xy=n.new('ShaderNodeCombineXYZ');l.new(se.outputs['X'],xy.inputs['X']);l.new(se.outputs['Y'],xy.inputs['Y']);p=xy.outputs[0]
v=vec('SUBTRACT',p,(-205,140,0));dot=vec('DOT_PRODUCT',v,(295,-230,0));t=op('DIVIDE',dot,295**2+230**2);t=op('MINIMUM',op('MAXIMUM',t,0),1)
q=n.new('ShaderNodeVectorMath');q.operation='SCALE';q.inputs[0].default_value=(295,-230,0);l.new(t,q.inputs['Scale'])
dist=vec('DISTANCE',v,q.outputs['Vector']);w=smooth(1.5,4.0,dist)
for cx,cy,rad in [(67.536852,-72.486359,11),(45.876293,-75.886764,8),(49.408698,-58.352544,10),(93.943160,-93.074328,7)]:
    w=op('MULTIPLY',w,smooth(rad,rad+2,vec('DISTANCE',p,(cx,cy,0))))
rgb=n.new('ShaderNodeSeparateColor');rgb.mode='RGB';l.new(leaf.outputs['Color'],rgb.inputs[0]);ratio=op('DIVIDE',rgb.outputs['Green'],op('MAXIMUM',rgb.outputs['Red'],.00001));mask=op('MULTIPLY',smooth(.58,.85,ratio),w)
grade=n.new('ShaderNodeMixRGB');grade.blend_type='MULTIPLY';l.new(mask,grade.inputs[0]);l.new(leaf.outputs['Color'],grade.inputs[1]);grade.inputs[2].default_value=(.48,.92,.68,1)
l.new(grade.outputs[0],bs.inputs['Base Color'])
# Raise leaf-litter blend outside protected core only; retain existing UV and exact maps/normal/roughness.
delta=op('SUBTRACT',op('MAXIMUM',old_weight,.8),old_weight);l.new(op('ADD',old_weight,op('MULTIPLY',w,delta)),mix.inputs[0])
for o in (terrain,ext):o.data.materials[0]=mat
bpy.context.view_layer.update();s=snap();changed={src_name,ext_name}
assert all(s[k]==v for k,v in old.items() if k not in changed)
for k in changed:assert s[k][0][:-1]==old[k][0][:-1] and s[k][1:3]==old[k][1:3]
assert sha(src)==lock
dest=out/'v76_moss_floor_feasibility.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()));scene=bpy.context.scene
assert snap()==s and sha(src)==lock
assert bpy.data.objects[src_name].data.materials[0]==bpy.data.objects[ext_name].data.materials[0]
q={'status':'GROUND_MATERIAL_ONLY_FEASIBILITY','source_sha256':lock,'native_sha256':sha(dest),'blender':bpy.app.version_string,'unchanged_meshes_exact':690,'changed_material_assignments':sorted(changed),'geometry_uv_color_exact':692,'new_triangles':0,'material':'V76_moss_floor_candidate','source_diffuse_sha256':'9c38b2b151a0415457a6914966422cfca5a546c94674442e5395e0b1e908a196','limits':['Heuristic grade based on color, not actual species identification.','Provisional route core 1.5m visual only; all collision/reservations untouched. No runtime, independent D4/G2 or Android assessment.','V75 backdrop deliberately absent; separate matched A/B.']}
(out/'v76_qa.json').write_text(json.dumps(q,indent=2)+'\n')
views={0:((78.17052459716797,-80.77701568603516,29.82533073425293),(93.94316101074219,-93.07432556152344,30.988130569458008),22),2:((71,-73,53),(96,-96,32),32)}
assert scene.render.engine=='CYCLES' and scene.render.resolution_x==960 and scene.render.resolution_y==540
cam=scene.camera
for i,(a,b,lens) in views.items():
    cam.location=a;cam.rotation_euler=(Vector(b)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
    scene.render.filepath=str((out/f'v76_view_{i}.png').resolve());bpy.ops.render.render(write_still=True)
q['outputs']={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.blend','.png')};(out/'v76_qa.json').write_text(json.dumps(q,indent=2)+'\n');print(q)

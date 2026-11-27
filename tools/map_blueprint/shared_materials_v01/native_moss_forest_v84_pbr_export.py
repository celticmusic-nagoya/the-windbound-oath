"""V84 scoped runtime PBR export. V83 exported the untouched castle_wall_slates
diffuse JPEG, losing the layered native color. Bake evaluated color and roughness
only, with a separate UV channel; preserve original UV/normal image.
No direct lighting bake; native material AO remains part of evaluated color.
Candidate, not adopted or runtime performance certified.
"""
import bpy, sys, math, hashlib, json, struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from array import array
import numpy as np
src,out=map(Path,sys.argv[sys.argv.index('--')+1:][:2])
out.mkdir(parents=True,exist_ok=True)
def sha(p):
    with open(p,'rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
LOCK='c45d88985d67018fe3b088eff150272682c0f6726d0e26268a215409d357b52a'
assert sha(src)==LOCK and bpy.app.version[:3]==(5,3,0)
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()))
scene=bpy.context.scene
EYE = Vector((78.17052459716797, -80.77701568603516, 29.82533073425293))
ALTAR = Vector((93.94316101074219, -93.07432556152344, 30.988130569458008))
A_, B_ = Vector((-205, 140)), Vector((90, -90))
RESERVED = [((67.536852, -72.486359), 11), ((45.876293, -75.886764), 8), ((49.408698, -58.352544), 10)]
FWD = (ALTAR - EYE).to_2d().normalized(); PERP = Vector((-FWD.y, FWD.x)); CENTER = (EYE.to_2d() + ALTAR.to_2d()) / 2
SIDE = Vector((.6148655745981655, .788631932636555))
CAM_ZONES = [EYE.to_2d(), EYE.to_2d() + SIDE * 8, EYE.to_2d() - FWD * 12, EYE.to_2d() + FWD * 10, ALTAR.to_2d() + PERP * 14]
C0 = ALTAR.to_2d(); FD = -FWD; FDP = Vector((-FD.y, FD.x))
REVIEW_EYES = [EYE.to_2d(), EYE.to_2d() + SIDE * 8, EYE.to_2d() - FWD * 12, EYE.to_2d() + FWD * 10, C0 + PERP * 14, C0 + FD * 10.5, C0 + FD * 10.5 + FDP * 3.5]
CAM_ZONES = CAM_ZONES + REVIEW_EYES[5:]
VIEW_CONES = [(e, C0) for e in REVIEW_EYES]
terrain = bpy.data.objects['A3 provisional reconstructed terrain']; ext = bpy.data.objects['V58_SCENIC_ONLY_terrain_extension']; far = bpy.data.objects['V77_SCENIC_ONLY_FAR_RELIEF']


def world_bvh(objs):
    verts = []; polys = []
    for o in objs:
        mw = o.matrix_world; base = len(verts)
        verts += [mw @ v.co for v in o.data.vertices]; polys += [[base + i for i in p.vertices] for p in o.data.polygons]
    return BVHTree.FromPolygons(verts, polys)


GROUND = world_bvh([terrain, ext, far])


def ground(x, y):
    hit = GROUND.ray_cast(Vector((x, y, 300)), Vector((0, 0, -1)), 400)
    return hit[0].z if hit[0] else None


# ---------------------------------------------------------------- animal trail (shared by shader + placement)
U = (B_ - A_).normalized(); N_ = Vector((-U.y, U.x)); LEN = (B_ - A_).length


def meander(a):
    fade = max(0., min(1., (LEN - a) / 9.0))
    return (1.1 * math.sin(.23 * a) + .5 * math.sin(.61 * a + 1.3)) * fade


def trail_dist(p):
    w = p - A_; a = w.dot(U)
    if a > LEN:
        return (p - B_).length
    return abs(w.dot(N_) - meander(a))


def seg_dist(p, a, b):
    ab = b - a; t = max(0, min(1, (p - a).dot(ab) / ab.length_squared)); return (a + ab * t - p).length


def gap(p, trail_clear, tall=False):
    """Clearance from trail core, ruin, reserved circles, cameras (+ altar sight ray for tall items)."""
    g = [trail_dist(p) - trail_clear, (p - C0).length - 7.0] + [(p - Vector(c)).length - r for c, r in RESERVED]
    if tall:
        g += [(p - c).length - 3.5 for c in CAM_ZONES] + [seg_dist(p, Vector((65.4663, -80.2138)), C0) - 2.2]
        for c, t in VIEW_CONES:                                  # keep review sightlines readable (half-angle 22 deg)
            v = p - c; L_ = (t - c).length
            if 0 < v.dot((t - c).normalized()) < L_ + 2 and v.angle(t - c) < math.radians(22):
                g.append(-1.0)
    return min(g)





platform=bpy.data.objects['V82_FX_03_floor']
# Recover platform top from the actual emissive inlay, not a guessed world height.
rz=[(platform.matrix_world @ platform.data.vertices[i].co).z for p in platform.data.polygons if p.material_index==0 for i in p.vertices]
assert rz
T=sorted(rz)[len(rz)//2]-.006
def eye_at(p2, h=1.7):
    g = ground(p2.x, p2.y); return Vector((p2.x, p2.y, (g if g is not None else EYE.z - 1.7) + h))


a_tl = LEN - 9; tl = A_ + U * a_tl + N_ * meander(a_tl)
VIEWS = {
    'matched': (EYE, ALTAR, 22), 'lateral': (EYE + SIDE.to_3d() * 8, ALTAR, 22),
    'side': (eye_at(C0 + PERP * 14), ALTAR, 24),
    'player_eye': (eye_at(EYE.to_2d() - FWD * 12), eye_at(EYE.to_2d() + FWD * 14, 1.5), 28),
    'altar_approach': (eye_at(EYE.to_2d() + FWD * 10), ALTAR + Vector((0, 0, -.4)), 28),
    'altar_front': (eye_at(C0 + FD * 10.5, 1.6), Vector((C0.x, C0.y, T + 1.5)), 26),
    'altar_oblique': (Vector((*(C0 + FD * 10.5 + FDP * 3.5), T + 6.2)), Vector((C0.x, C0.y, T + .9)), 24),
    'trail_low': (eye_at(tl, 1.05), eye_at(A_ + U * (LEN - 1) + N_ * meander(LEN - 1), .6), 24),
    'look_up': (EYE, EYE + (FWD.to_3d() * .45 + Vector((0, 0, .9))), 16),
    'oblique_aerial': (CENTER.to_3d() + Vector((-48, 40, EYE.z + 52)), CENTER.to_3d() + Vector((0, 0, EYE.z - 2)), 26),
}



ruin=bpy.data.collections['V81_RUNE_SANCTUARY'];fx=bpy.data.collections['V82_RUNE_VFX_INDEPENDENT']
assert fx.hide_render and fx.hide_viewport
def digest(mesh):
    a=array('f',[0])*(len(mesh.vertices)*3);mesh.vertices.foreach_get('co',a)
    b=array('i',[0])*len(mesh.loops);mesh.loops.foreach_get('vertex_index',b)
    c=array('i',[0])*len(mesh.polygons);mesh.polygons.foreach_get('material_index',c)
    return hashlib.sha256(a.tobytes()+b.tobytes()+c.tobytes()).hexdigest()
def snapshot():
    cache={};result={}
    for o in scene.objects:
        if o.type!='MESH':continue
        if o.data.name not in cache:cache[o.data.name]=digest(o.data)
        result[o.name]=(cache[o.data.name],tuple(tuple(row) for row in o.matrix_world),o.hide_render,o.hide_viewport)
    return result


protected=snapshot()
names=('V81_ruin_platform','V81_ruin_back','V81_ruin_posts','V81_ruin_rubble')
targets=[bpy.data.objects[n] for n in names]
original=bpy.data.materials['V83_weathered_stone_candidate']
# V84-F1 failed here before any bake: raw slot count is not an actual face-material contract.
# Inventory actual used indices, reject non-stone polygons, preserve unused slots.
inventory={o.name:{'mesh_users':o.data.users,'slot_names':[m.name if m else None for m in o.data.materials],'used_indices':sorted({p.material_index for p in o.data.polygons}),'uv_names':[u.name for u in o.data.uv_layers]} for o in targets}
(out/'v84_slot_preflight.json').write_text(json.dumps(inventory,indent=2))
print('V84_SLOT_PREFLIGHT',json.dumps(inventory),flush=True)
used={}
for o in targets:
    indices=inventory[o.name]['used_indices']
    assert len(indices)==1 and all(i<len(o.data.materials) and o.data.materials[i]==original for i in indices),(o.name,inventory[o.name])
    assert 'UVMap' in inventory[o.name]['uv_names'],inventory[o.name]
    used[o.name]=indices[0]
# Every target is assigned its own mesh copy before mutation, even if input has shared users.
normal_node=[n for n in original.node_tree.nodes if n.type=='NORMAL_MAP'];assert len(normal_node)==1
normal_img=normal_node[0].inputs['Color'].links[0].from_node.image
assert normal_img.name.startswith('castle_wall_slates_nor_gl')
normal_strength=normal_node[0].inputs['Strength'].default_value
assert abs(normal_strength-.30)<.001
qa={'candidate_only':True,'source_sha256':LOCK,'reference_glb_sha256':'e74a8ec0110a77b36818328c5d7571269adab24aa8a91c2c85008f28dc7e8c73','bakes':{},'views':{},'limits':['Evaluated native material color includes existing geometry AO; no direct lighting or directional highlight bake','1024px per stone object, provisional texel density; compare seams','Normal map retains original source UV; two UV channels required','No Android G4 or formal adoption']}
def checkpoint():
    (out/'v84_pbr_qa.json').write_text(json.dumps(qa,indent=2))
    print('V84_CHECKPOINT',json.dumps(qa),flush=True)
def uv_sig(m,name):
    a=array('f',[0])*(len(m.loops)*2);m.uv_layers[name].data.foreach_get('uv',a)
    return hashlib.sha256(a.tobytes()).hexdigest()
uv_before={o.name:uv_sig(o.data,'UVMap') for o in targets}
old_slots={o.name:tuple(m.name if m else None for m in o.data.materials) for o in scene.objects if o.type=='MESH'}
cam=scene.camera
camera_state=(cam.matrix_world.copy(),cam.data.type,cam.data.lens,cam.data.clip_start,cam.data.clip_end)
render_state=(scene.render.resolution_percentage,scene.cycles.samples,scene.cycles.use_denoising,scene.render.film_transparent,scene.render.image_settings.file_format,scene.render.image_settings.color_mode,scene.render.filepath)
def select(o):
    bpy.ops.object.select_all(action='DESELECT');o.hide_select=False;o.select_set(True);bpy.context.view_layer.objects.active=o
def uvnode(nt,name):
    n=nt.nodes.new('ShaderNodeUVMap');n.uv_map=name;return n
def texture(nt,img,uv):
    n=nt.nodes.new('ShaderNodeTexImage');n.image=img;nt.links.new(uv.outputs['UV'],n.inputs['Vector']);return n
for o in targets:
    # Work copy of only target mesh; source file unchanged.
    o.data=o.data.copy()
    mesh=o.data;assert 'V84BakeUV' not in mesh.uv_layers
    layer=mesh.uv_layers.new(name='V84BakeUV',do_init=False)
    mesh.uv_layers.active=layer;layer.active_render=True
    select(o)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.008)
    bpy.ops.object.mode_set(mode='OBJECT')
    assert digest(mesh)==protected[o.name][0] and uv_sig(mesh,'UVMap')==uv_before[o.name]
    uv=array('f',[0])*(len(mesh.loops)*2);mesh.uv_layers['V84BakeUV'].data.foreach_get('uv',uv)
    assert min(uv)>=-.001 and max(uv)<=1.001
    work=original.copy();work.name='V84_bake_temp_'+o.name
    o.data.materials[used[o.name]]=work
    assert all(m==original or m==work or i!=used[o.name] for i,m in enumerate(o.data.materials))
    nt=work.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
    for n in nt.nodes:
        if n.type=='NORMAL_MAP':n.uv_map='UVMap'
    output=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
    emit=nt.nodes.new('ShaderNodeEmission')
    nt.links.new(emit.outputs[0],output.inputs['Surface'])
    scene.render.engine='CYCLES';scene.cycles.samples=16
    scene.render.bake.use_selected_to_active=False
    # Bake with explicitly named original shader UV and destination active UV.
    assert mesh.uv_layers.active.name=='V84BakeUV'
    scene.render.bake.target='IMAGE_TEXTURES'
    imgs={}
    for socket,label in (('Base Color','color'),('Roughness','roughness')):
        for l in list(emit.inputs['Color'].links):nt.links.remove(l)
        source=bs.inputs[socket];assert source.is_linked,(o.name,socket)
        nt.links.new(source.links[0].from_socket,emit.inputs['Color'])
        im=bpy.data.images.new('V84_'+o.name+'_'+label,width=1024,height=1024,alpha=False)
        im.colorspace_settings.name='sRGB' if label=='color' else 'Non-Color'
        node=nt.nodes.new('ShaderNodeTexImage');node.image=im
        for n in nt.nodes:n.select=False
        node.select=True;nt.nodes.active=node
        select(o)
        bpy.ops.object.bake(type='EMIT',margin=8,use_clear=True,uv_layer='V84BakeUV')
        pixels=np.empty(len(im.pixels),dtype=np.float32);im.pixels.foreach_get(pixels);rgb=pixels.reshape(-1,4)[:,:3]
        nonzero=float((rgb.max(1)>.005).mean())
        assert nonzero>.10,(o.name,label,nonzero)
        file=out/(im.name+'.png');im.filepath_raw=str(file.resolve());im.file_format='PNG';im.save();im.pack()
        imgs[label]=im
        qa['bakes'].setdefault(o.name,{})[label]={'sha256':sha(file),'size':[1024,1024],'nonblack_fraction_including_empty_uv':nonzero}
        checkpoint();nt.nodes.remove(node)
    mat=bpy.data.materials.new('V84_baked_'+o.name);mat.use_nodes=True
    mt=mat.node_tree;bs=mt.nodes.get('Principled BSDF')
    uv_new=uvnode(mt,'V84BakeUV');uv_old=uvnode(mt,'UVMap')
    col=texture(mt,imgs['color'],uv_new);rr=texture(mt,imgs['roughness'],uv_new);nn=texture(mt,normal_img,uv_old)
    mt.links.new(col.outputs['Color'],bs.inputs['Base Color']);mt.links.new(rr.outputs['Color'],bs.inputs['Roughness'])
    nmap=mt.nodes.new('ShaderNodeNormalMap');nmap.uv_map='UVMap';nmap.inputs['Strength'].default_value=normal_strength
    mt.links.new(nn.outputs['Color'],nmap.inputs['Color']);mt.links.new(nmap.outputs['Normal'],bs.inputs['Normal'])
    bs.inputs['Metallic'].default_value=0;bs.inputs['Specular IOR Level'].default_value=.35
    o.data.materials[used[o.name]]=mat
    assert digest(mesh)==protected[o.name][0] and uv_sig(mesh,'UVMap')==uv_before[o.name]
    assert all((m.name if m else None)==old_slots[o.name][i] for i,m in enumerate(o.data.materials) if i!=used[o.name])
assert snapshot()==protected
for o in scene.objects:
    if o.type=='MESH' and o.name not in names:assert tuple(m.name if m else None for m in o.data.materials)==old_slots[o.name]
cam.matrix_world,cam.data.type,cam.data.lens,cam.data.clip_start,cam.data.clip_end=camera_state
scene.render.resolution_percentage,scene.cycles.samples,scene.cycles.use_denoising,scene.render.film_transparent,scene.render.image_settings.file_format,scene.render.image_settings.color_mode,scene.render.filepath=render_state
assert fx.hide_render and fx.hide_viewport
dest=out/'v84_pbr_export_candidate.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()));scene=bpy.context.scene;cam=scene.camera
ruin=bpy.data.collections['V81_RUNE_SANCTUARY'];fx=bpy.data.collections['V82_RUNE_VFX_INDEPENDENT']
assert snapshot()==protected and fx.hide_render and fx.hide_viewport
assert all(uv_sig(bpy.data.objects[n].data,'UVMap')==uv_before[n] for n in names)
qa['native_sha256']=sha(dest);qa['reopen_geometry_original_uv_exact']=True;checkpoint()
base_objects=sorted([o for o in ruin.objects if o.type=='MESH' and not o.hide_render and not o.hide_viewport],key=lambda o:o.name)
assert len(base_objects)==6
bpy.ops.object.select_all(action='DESELECT')
for o in base_objects:o.hide_select=False;o.select_set(True)
bpy.context.view_layer.objects.active=base_objects[0]
glb=out/'v84_sanctuary_dormant.glb'
bpy.ops.export_scene.gltf(filepath=str(glb.resolve()),export_format='GLB',use_selection=True,export_image_format='AUTO',export_apply=True,export_animations=False)
with glb.open('rb') as f:
    magic,version,length=struct.unpack('<4sII',f.read(12));size,kind=struct.unpack('<II',f.read(8));data=json.loads(f.read(size))
assert magic==b'glTF' and version==2 and length==glb.stat().st_size and kind==0x4e4f534a
assert not any(any(v>0 for v in m.get('emissiveFactor',[])) or 'emissiveTexture' in m for m in data.get('materials',[]))
baked=[m for m in data['materials'] if m.get('name','').startswith('V84_baked_')]
assert len(baked)==4
for m in baked:
    color=m['pbrMetallicRoughness']['baseColorTexture'];rough=m['pbrMetallicRoughness']['metallicRoughnessTexture'];normal=m['normalTexture']
    assert color.get('texCoord',0)==rough.get('texCoord',0) and color.get('texCoord',0)!=normal.get('texCoord',0),m
qa['base_glb']={'sha256':sha(glb),'bytes':length,'meshes':len(data['meshes']),'baked_materials':len(baked),'emissive_materials':0,'dual_uv_exact_contract':True};checkpoint()
def render(name,state):
    p,t,lens=VIEWS[name];cam.data.type='PERSP';cam.location=p;cam.rotation_euler=(t-p).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;cam.data.clip_start=.05;cam.data.clip_end=600
    scene.render.resolution_percentage=50;scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.film_transparent=False;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    file=out/('v84_'+state+'_'+name+'.png');scene.render.filepath=str(file.resolve());bpy.ops.render.render(write_still=True)
    im=bpy.data.images.load(str(file),check_existing=False);a=np.empty(len(im.pixels),dtype=np.float32);im.pixels.foreach_get(a);bpy.data.images.remove(im)
    y=a.reshape(-1,4)[:,:3]@np.array([.2126,.7152,.0722]);qa['views'].setdefault(name,{})[state]={'mean_luma':float(y.mean())};checkpoint()
for view in ('altar_front','altar_oblique'):render(view,'baked_native')
# Reimport GLB into the same environment on an unsaved review copy.
before=set(bpy.data.objects);bounds={o.name:[tuple(o.matrix_world@Vector(c)) for c in o.bound_box] for o in base_objects}
for o in base_objects:o.hide_render=True;o.hide_viewport=True
bpy.ops.import_scene.gltf(filepath=str(glb.resolve()))
loaded=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
assert len(loaded)==6
qa['reimport_meshes']=len(loaded)
for view in ('altar_front','altar_oblique'):render(view,'glb_reimport')
qa['source_unchanged']=sha(src)==LOCK
assert qa['source_unchanged'];checkpoint();print('V84_PBR_EXPORT_DONE',json.dumps(qa))

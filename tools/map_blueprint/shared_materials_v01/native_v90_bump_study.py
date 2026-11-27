"""V90 isolated native pigment/roughness and bump study; no physical displacement."""
import bpy, sys, math, hashlib, json, struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from array import array
import numpy as np
src,maps,out=map(Path,sys.argv[sys.argv.index('--')+1:])
out.mkdir(parents=True,exist_ok=True)
def sha(p):
    with open(p,'rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
LOCK='7f439b39cc8f7ad1c8702b65b55fa268cd74df1a2ad6720c9d3c73dd0b946222'
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



fx=bpy.data.collections['V82_RUNE_VFX_INDEPENDENT'];assert fx.hide_render and fx.hide_viewport
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
slots={o.name:tuple(m.name if m else None for m in o.data.materials) for o in scene.objects if o.type=='MESH'}
bg=scene.world.node_tree.nodes['Background'];vol=scene.world.node_tree.nodes['V79_atmosphere']
strength=bg.inputs['Strength'].default_value;density=vol.inputs['Density'].default_value
assert strength>0 and density>0
exposure=scene.view_settings.exposure
fills=[bpy.data.objects[n] for n in ('V57_cool_ambient','V58_scenic_cool_fill')]
assert all(o.type=='LIGHT' for o in fills)
energies={o.name:o.data.energy for o in fills}
assert all(o.data.users==1 for o in fills)

RECEIPT_SHA='4d0e6c82b553b599ae7cfa51cddf781adac4b8ae20193b904a11b575c5812c89'
assert sha(maps/'native_input_receipt.json')==RECEIPT_SHA
q=json.loads((maps/'native_input_receipt.json').read_text());assert q['source_native_sha256']==LOCK
parts=q['parts'];targets={x['object'] for x in parts.values()}
qa={'candidate_only':True,'source_sha256':LOCK,'receipt_sha256':RECEIPT_SHA,'views':{},'parts':{},'limits':['Native shader bump only; not cut geometry or GLB bump support','Comparison at fixed V86 lighting; provisional depth and strength','No game or Android QA']}
lights={o.name:(o.data.energy,tuple(o.data.color),tuple(tuple(r) for r in o.matrix_world)) for o in scene.objects if o.type=='LIGHT'}
assert lights['V86_trail_soft_00'][0]==lights['V86_trail_soft_01'][0]==220

def uv_sig(o):
    return {u.name:hashlib.sha256(b''.join(struct.pack('<2f',*x.uv) for x in u.data)).hexdigest() for u in o.data.uv_layers}
uvs={name:uv_sig(bpy.data.objects[name]) for name in targets}
def packed_sha(image):
    assert image and image.packed_file
    return hashlib.sha256(bytes(image.packed_file.data)).hexdigest()
def checkpoint():
    (out/'v90_native_qa.json').write_text(json.dumps(qa,indent=2));print('V90_CHECKPOINT',json.dumps(qa),flush=True)
bumps=[]
for part,row in parts.items():
    name=row['object'];ob=bpy.data.objects[name];assert ob.data.users==1 and {p.material_index for p in ob.data.polygons}=={0}
    original=ob.data.materials[0];assert original.name=='V87_dormant_'+name and 'V84BakeUV' in ob.data.uv_layers
    bs=next(n for n in original.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    for sock,key in [('Base Color','source_color_sha256'),('Roughness','source_native_roughness_sha256')]:
        n=bs.inputs[sock].links[0].from_node;assert n.type=='TEX_IMAGE' and packed_sha(n.image)==row[key]
        assert n.inputs['Vector'].links[0].from_node.uv_map=='V84BakeUV'
    norm=bs.inputs['Normal'].links[0].from_node;assert norm.type=='NORMAL_MAP' and norm.uv_map=='UVMap'
    old_normal=packed_sha(norm.inputs['Color'].links[0].from_node.image)
    mat=original.copy();mat.name='V90_engraving_'+name;ob.data.materials[0]=mat;nt=mat.node_tree
    bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');norm=bs.inputs['Normal'].links[0].from_node
    assert packed_sha(norm.inputs['Color'].links[0].from_node.image)==old_normal
    def load(key,cs):
        item=row['maps'][key];f=maps/item['name'];assert sha(f)==item['sha256'];im=bpy.data.images.load(str(f.resolve()),check_existing=False);im.colorspace_settings.name=cs;assert tuple(im.size)==(1024,1024);im.pack();assert packed_sha(im)==item['sha256'];return im
    bs.inputs['Base Color'].links[0].from_node.image=load('color','sRGB')
    bs.inputs['Roughness'].links[0].from_node.image=load('roughness','Non-Color')
    uv=nt.nodes.new('ShaderNodeUVMap');uv.name='V90_Engraving_UV';uv.uv_map='V84BakeUV'
    tex=nt.nodes.new('ShaderNodeTexImage');tex.name='V90_Engraving_Height';tex.image=load('height','Non-Color');tex.extension='EXTEND';nt.links.new(uv.outputs['UV'],tex.inputs['Vector'])
    bump=nt.nodes.new('ShaderNodeBump');bump.name='V90_Engraving_Bump';bump.invert=False;bump.inputs['Distance'].default_value=q['native_bump_distance_local'];bump.inputs['Strength'].default_value=q['native_bump_strength'];nt.links.new(tex.outputs['Color'],bump.inputs['Height']);nt.links.new(norm.outputs['Normal'],bump.inputs['Normal']);nt.links.new(bump.outputs['Normal'],bs.inputs['Normal']);bumps.append(bump)
    assert not bs.inputs['Emission Color'].is_linked and not bs.inputs['Emission Strength'].is_linked and (bs.inputs['Emission Strength'].default_value==0 or max(bs.inputs['Emission Color'].default_value[:3])==0)
    qa['parts'][part]={'old_normal_sha256':old_normal,'maps':row['maps'],'uv_exact':uv_sig(ob)==uvs[name]}
assert snapshot()==protected and all(uv_sig(bpy.data.objects[n])==v for n,v in uvs.items())
assert all(tuple(m.name if m else None for m in o.data.materials)==slots[o.name] for o in scene.objects if o.type=='MESH' and o.name not in targets)
assert fx.hide_render and fx.hide_viewport
# Save a recoverable native checkpoint before rendering; test Bump on/off in memory only.
dest=out/'v90_bump_candidate.blend';assert not dest.exists();bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True);qa['native_sha256']=sha(dest);checkpoint()
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()));scene=bpy.context.scene;fx=bpy.data.collections['V82_RUNE_VFX_INDEPENDENT']
assert snapshot()==protected and fx.hide_render and fx.hide_viewport
assert all(uv_sig(bpy.data.objects[n])==v for n,v in uvs.items())
assert {o.name:(o.data.energy,tuple(o.data.color),tuple(tuple(r) for r in o.matrix_world)) for o in scene.objects if o.type=='LIGHT'}==lights
assert scene.view_settings.exposure==exposure and scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value==strength and scene.world.node_tree.nodes['V79_atmosphere'].inputs['Density'].default_value==density
bumps=[]
for part,row in parts.items():
    nt=bpy.data.objects[row['object']].data.materials[0].node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');bump=nt.nodes['V90_Engraving_Bump'];assert bs.inputs['Normal'].links[0].from_node==bump
    normal=bump.inputs['Normal'].links[0].from_node;assert normal.uv_map=='UVMap' and packed_sha(normal.inputs['Color'].links[0].from_node.image)==qa['parts'][part]['old_normal_sha256']
    for key,node in [('color',bs.inputs['Base Color'].links[0].from_node),('roughness',bs.inputs['Roughness'].links[0].from_node),('height',nt.nodes['V90_Engraving_Height'])]:assert packed_sha(node.image)==row['maps'][key]['sha256']
    bumps.append(bump)
qa['reopen_geometry_uv_lights_and_maps_exact']=True;checkpoint()
cam=scene.camera
def render(view,state):
    p,t,lens=VIEWS[view];cam.data.type='PERSP';cam.location=p;cam.rotation_euler=(t-p).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;cam.data.clip_start=.05;cam.data.clip_end=600
    scene.render.resolution_percentage=50;scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.film_transparent=False;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    f=out/('v90_'+state+'_'+view+'.png');assert not f.exists();scene.render.filepath=str(f.resolve());bpy.ops.render.render(write_still=True);qa['views'][f.name]=sha(f);checkpoint()
for state,value in [('pigment_only',0.),('bump',q['native_bump_strength'])]:
    for b in bumps:b.inputs['Strength'].default_value=value
    for v in ('altar_front','altar_oblique'):render(v,state)
fx.hide_render=False;fx.hide_viewport=False;render('altar_front','active_bump')
assert sha(src)==LOCK and sha(dest)==qa['native_sha256'];qa['source_unchanged']=True;checkpoint();print('V90_NATIVE_DONE',json.dumps(qa),flush=True)

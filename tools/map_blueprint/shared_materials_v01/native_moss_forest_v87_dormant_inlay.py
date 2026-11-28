"""V87 native non-emissive texture inlay, derived from exact V84 baked UVs.
Preserve V86 selected light, geometry, UV, all other material slots and FX.
Candidate only, pigment not physical recess.
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
LOCK='5b665a03c83f20fc3ed193ec029e09181bbb655094c68128b36f4628c7125f48'
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
projection=out/'projection'
q=json.loads((projection/'projection_qa.json').read_text())
targets={'stele':'V81_ruin_back','floor':'V81_ruin_platform','posts':'V81_ruin_posts'}
qa={'candidate_only':True,'source_sha':LOCK,'projection':q,'views':{},'limits':['Texture pigment, not physical recess; no new relief normal','No canonical placement or actual game G4']}
all_lights={o.name:(o.data.energy,tuple(o.data.color),tuple(tuple(r) for r in o.matrix_world)) for o in scene.objects if o.type=='LIGHT'}
assert all_lights['V86_trail_soft_00'][0]==220 and all_lights['V86_trail_soft_01'][0]==220
def uv_sig(o):
    return {u.name:hashlib.sha256(b''.join(struct.pack('<2f',*x.uv) for x in u.data)).hexdigest() for u in o.data.uv_layers}
uvs={name:uv_sig(bpy.data.objects[name]) for name in targets.values()}
for part,name in targets.items():
    ob=bpy.data.objects[name];assert ob.data.users==1
    used={p.material_index for p in ob.data.polygons};assert used=={0}
    original=ob.data.materials[0];assert original.name=='V84_baked_'+name
    assert 'V84BakeUV' in ob.data.uv_layers
    old=next(n for n in original.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    tex=old.inputs['Base Color'].links[0].from_node
    assert tex.type=='TEX_IMAGE' and tex.image.packed_file
    assert hashlib.sha256(bytes(tex.image.packed_file.data)).hexdigest()==q[part]['source_sha']
    f=projection/(part+'_candidate.png');assert sha(f)==q[part]['candidate_sha']
    mat=original.copy();mat.name='V87_dormant_'+name;ob.data.materials[0]=mat
    bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    n=bs.inputs['Base Color'].links[0].from_node
    image=bpy.data.images.load(str(f.resolve()),check_existing=False);image.colorspace_settings.name='sRGB';image.pack();n.image=image
    assert bs.inputs['Emission Strength'].default_value==0 or max(bs.inputs['Emission Color'].default_value[:3])==0
assert snapshot()==protected
assert all(uv_sig(bpy.data.objects[n])==v for n,v in uvs.items())
for o in scene.objects:
    if o.type=='MESH' and o.name not in targets.values():assert tuple(m.name if m else None for m in o.data.materials)==slots[o.name]
dest=out/'v87_dormant_inlay_candidate.blend'
assert not dest.exists() and fx.hide_render and fx.hide_viewport
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()));scene=bpy.context.scene;fx=bpy.data.collections['V82_RUNE_VFX_INDEPENDENT']
assert snapshot()==protected and fx.hide_render and fx.hide_viewport
assert all(uv_sig(bpy.data.objects[n])==v for n,v in uvs.items())
assert all((o.data.energy,tuple(o.data.color),tuple(tuple(r) for r in o.matrix_world))==all_lights[o.name] for o in scene.objects if o.type=='LIGHT')
qa['native_sha']=sha(dest)
def checkpoint():
    (out/'v87_native_qa.json').write_text(json.dumps(qa,indent=2));print('V87_CHECKPOINT',json.dumps(qa),flush=True)
checkpoint()
ruin=bpy.data.collections['V81_RUNE_SANCTUARY']
objs=sorted([o for o in ruin.objects if o.type=='MESH' and not o.hide_render and not o.hide_viewport],key=lambda o:o.name);assert len(objs)==6
bpy.ops.object.select_all(action='DESELECT')
for o in objs:o.hide_select=False;o.select_set(True)
bpy.context.view_layer.objects.active=objs[0]
glb=out/'v87_dormant_inlay.glb';bpy.ops.export_scene.gltf(filepath=str(glb.resolve()),export_format='GLB',use_selection=True,export_image_format='AUTO',export_apply=True,export_animations=False)
with glb.open('rb') as f:
    magic,version,length=struct.unpack('<4sII',f.read(12));n,k=struct.unpack('<II',f.read(8));data=json.loads(f.read(n))
assert magic==b'glTF' and version==2 and length==glb.stat().st_size and k==0x4e4f534a
assert not any(any(v>0 for v in m.get('emissiveFactor',[])) or 'emissiveTexture' in m for m in data['materials'])
qa['glb']={'sha':sha(glb),'meshes':len(data['meshes']),'emissive_materials':0};checkpoint()
cam=scene.camera
def render(view,state):
    p,t,lens=VIEWS[view];cam.data.type='PERSP';cam.location=p;cam.rotation_euler=(t-p).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;cam.data.clip_start=.05;cam.data.clip_end=600
    scene.render.resolution_percentage=50;scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.film_transparent=False;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    file=out/('v87_'+state+'_'+view+'.png');scene.render.filepath=str(file.resolve());bpy.ops.render.render(write_still=True)
    qa['views'][file.name]=sha(file);checkpoint()
for v in ('altar_front','altar_oblique','altar_approach'):render(v,'dormant')
fx.hide_render=False;fx.hide_viewport=False
for v in ('altar_front','altar_oblique'):render(v,'active')
assert sha(src)==LOCK;qa['source_unchanged']=True;checkpoint();print('V87_NATIVE_DONE',json.dumps(qa))

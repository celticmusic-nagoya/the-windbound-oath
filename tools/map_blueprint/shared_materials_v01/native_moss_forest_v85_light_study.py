"""V85 scoped light study. Compare balanced ambient and local fill against V84.
No exposure trick, mesh changes, material changes or asset adoption.
All values and gates provisional; no game lighting performance certification.
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
LOCK='6dcd6508207815d04bb16bb0b05b6cf6014527a9b48c130e5ba440292e215549'
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
qa={'candidate_only':True,'source_sha256':LOCK,'baseline':{'world_strength':strength,'density':density,'exposure':exposure,'fill_energy':energies},'views':{},'limits':['Whole-frame linear luma screening is not G2','Lighting levels provisional, no geometry/texture changes','Native scene lighting does not automatically transfer to game runtime','No Android G4 or formal adoption']}
def checkpoint():
    (out/'v85_light_qa.json').write_text(json.dumps(qa,indent=2))
    print('V85_CHECKPOINT',json.dumps(qa),flush=True)
cam=scene.camera
camera_state=(cam.matrix_world.copy(),cam.data.type,cam.data.lens,cam.data.clip_start,cam.data.clip_end)
render_state=(scene.render.resolution_percentage,scene.cycles.samples,scene.cycles.use_denoising,scene.render.film_transparent,scene.render.image_settings.file_format,scene.render.image_settings.color_mode,scene.render.filepath)
def setlight(factor,fill_factor):
    bg.inputs['Strength'].default_value=strength*factor
    for o in fills:o.data.energy=energies[o.name]*fill_factor
    assert scene.view_settings.exposure==exposure and vol.inputs['Density'].default_value==density
def render(view,state):
    p,t,lens=VIEWS[view];cam.data.type='PERSP';cam.location=p;cam.rotation_euler=(t-p).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;cam.data.clip_start=.05;cam.data.clip_end=600
    scene.render.resolution_percentage=50;scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.film_transparent=False;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    file=out/('v85_'+state+'_'+view+'.png');scene.render.filepath=str(file.resolve());bpy.ops.render.render(write_still=True)
    im=bpy.data.images.load(str(file),check_existing=False);a=np.empty(len(im.pixels),dtype=np.float32);im.pixels.foreach_get(a);bpy.data.images.remove(im)
    y=a.reshape(-1,4)[:,:3]@np.array([.2126,.7152,.0722]);qa['views'].setdefault(view,{})[state]={'mean_luma':float(y.mean()),'p10':float(np.percentile(y,10)),'p95':float(np.percentile(y,95)),'dark_fraction_below_0_02':float((y<.02).mean())};checkpoint()
# Same cameras, sun, volumetrics, exposure, geometry and texture. Two conservative alternatives.
states={'A':(1,1),'B':(1.35,1.2),'C':(1.6,1.4)}
for state,(factor,fill_factor) in states.items():
    setlight(factor,fill_factor)
    for view in ('player_eye','altar_approach','altar_front'):render(view,state)
def acceptable(state):
    a=qa['views']['player_eye']['A'];b=qa['views']['player_eye'][state]
    c=qa['views']['altar_front']['A'];d=qa['views']['altar_front'][state]
    return b['mean_luma']>=a['mean_luma']*1.12 and b['p10']>=a['p10'] and d['p95']<=c['p95']*1.15 and d['mean_luma']<=c['mean_luma']*1.15
winner=next((k for k in ('B','C') if acceptable(k)),None)
qa['screening']={'criteria':'player mean >=1.12x baseline, p10 nondecreasing; front mean/p95 <=1.15x baseline','selected':winner,'provisional':True}
checkpoint()
# Keep baseline if none qualifies; no unreviewed lighting candidate as default.
setlight(*states[winner or 'A'])
assert snapshot()==protected and all(tuple(m.name if m else None for m in o.data.materials)==slots[o.name] for o in scene.objects if o.type=='MESH')
cam.matrix_world,cam.data.type,cam.data.lens,cam.data.clip_start,cam.data.clip_end=camera_state
scene.render.resolution_percentage,scene.cycles.samples,scene.cycles.use_denoising,scene.render.film_transparent,scene.render.image_settings.file_format,scene.render.image_settings.color_mode,scene.render.filepath=render_state
assert fx.hide_render and fx.hide_viewport
dest=out/'v85_light_candidate.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()));scene=bpy.context.scene
assert snapshot()==protected and bpy.data.collections['V82_RUNE_VFX_INDEPENDENT'].hide_render
assert all(tuple(m.name if m else None for m in o.data.materials)==slots[o.name] for o in scene.objects if o.type=='MESH')
qa.update({'native_sha256':sha(dest),'reopen_geometry_exact':True,'source_unchanged':sha(src)==LOCK});checkpoint()
assert qa['source_unchanged'];print('V85_LIGHT_DONE',json.dumps(qa))

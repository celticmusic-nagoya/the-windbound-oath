"""V82-E causal stone atlas correction, separate from geometry repair.
V81 used scan-specific atlas as repeat texture; actual GLB sampling found 34-39%
area-weighted black UV samples. Compare pinned CC0 tileable masonry texture.
No adoption; wall joint pattern may require a single-stone tile in next pass.
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
LOCK='6061d7233cf32b2b1b1e37bfae28a6d15f43eda88c6fd6cf00807eda0c7962a5'
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



ruin=bpy.data.collections['V81_RUNE_SANCTUARY']
fx=bpy.data.collections['V82_RUNE_VFX_INDEPENDENT']
assert fx.hide_render and fx.hide_viewport
original=bpy.data.materials['V82B_pale_weathered_stone_candidate']
targets=[o for o in ruin.objects if o.type=='MESH' and original in list(o.data.materials)]
assert len(targets)==4 and all(o.data.users==1 for o in targets)
def fingerprint():
    result={};cache={}
    for o in scene.objects:
        if o.type=='MESH':
            m=o.data
            if m.name not in cache:
                a=array('f',[0])*(len(m.vertices)*3);m.vertices.foreach_get('co',a)
                b=array('i',[0])*len(m.loops);m.loops.foreach_get('vertex_index',b)
                c=array('i',[0])*len(m.polygons);m.polygons.foreach_get('material_index',c)
                cache[m.name]=hashlib.sha256(a.tobytes()+b.tobytes()+c.tobytes()).hexdigest()
            result[o.name]=[cache[m.name],[list(row) for row in o.matrix_world],o.hide_render,o.hide_viewport]
    return result

protected=fingerprint()
slots={o.name:[m.name if m else None for m in o.data.materials] for o in scene.objects if o.type=='MESH'}
candidate=original.copy();candidate.name='V82E_tileable_stone_candidate'
nt=candidate.node_tree
map_spec=[{"map":"Diffuse","file":"castle_wall_slates_diff_2k.jpg","sha":"89e1dce61cf53decf586bd123b9280365e447019ebedaf3b8e48663ab37eab30"},{"map":"nor_gl","file":"castle_wall_slates_nor_gl_2k.jpg","sha":"ea6042cdb95576d9c2d67c7fa26e3648cca09d8d2fcaf4dfe7d6052a970d7b28"},{"map":"Rough","file":"castle_wall_slates_rough_2k.jpg","sha":"84fe81f77d25e4dc37be41174b0a1fa85e8aece244eabe54ed48c542cb5bed08"}]
node_names={'Diffuse':'rock_moss_set_01_diff','nor_gl':'rock_moss_set_01_nor_gl','Rough':'rock_moss_set_01_rough'}
qa={'candidate_only':True,'source_sha256':LOCK,'texture_source':'Poly Haven castle_wall_slates, catalog CC0; exact SHA locked','texture_checks':[],'views':{},'limits':['Masonry texture includes joints: check duplicate masonry patterns','No floor topology repair in this material-only lane','No adopted material or runtime G4','Whole-frame luma is not art acceptance']}
for spec in map_spec:
    path=out/'source_pbr'/spec['file'];assert sha(path)==spec['sha']
    nodes=[n for n in nt.nodes if n.type=='TEX_IMAGE' and n.image and n.image.name.startswith(node_names[spec['map']])]
    assert len(nodes)==1,(spec['map'],[n.name for n in nodes])
    image=bpy.data.images.load(str(path.resolve()),check_existing=False)
    image.colorspace_settings.name='sRGB' if spec['map']=='Diffuse' else 'Non-Color'
    pixels=np.empty(len(image.pixels),dtype=np.float32);image.pixels.foreach_get(pixels)
    rgb=pixels.reshape(-1,4)[:,:3]
    black=float((rgb.max(1)<.003).mean())
    if spec['map']=='Diffuse':assert black<.01,black
    image.pack();nodes[0].image=image;nodes[0].extension='REPEAT'
    qa['texture_checks'].append({'map':spec['map'],'sha256':spec['sha'],'black_fraction_linear_rgb_max_lt_0_003':black,'size':list(image.size)})
# Replace scan atlas with tileable material while retaining the same UVs, normal/moss mix and lighting.
clay=bpy.data.materials.new('V82E_diagnostic_clay');clay.use_nodes=True;bs=clay.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(.42,.42,.42,1);bs.inputs['Roughness'].default_value=.75
cam=scene.camera
camera_state=(cam.matrix_world.copy(),cam.data.type,cam.data.lens,cam.data.clip_start,cam.data.clip_end)
render_state=(scene.render.resolution_percentage,scene.cycles.samples,scene.cycles.use_denoising,scene.render.film_transparent,scene.render.image_settings.file_format,scene.render.image_settings.color_mode,scene.render.filepath)
def use(m):
    for o in targets:
        for i,name in enumerate(slots[o.name]):
            if name==original.name:o.data.materials[i]=m
def render(name,state):
    p,t,lens=VIEWS[name];cam.data.type='PERSP';cam.location=p;cam.rotation_euler=(t-p).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;cam.data.clip_start=.05;cam.data.clip_end=600
    scene.render.resolution_percentage=50;scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.film_transparent=False;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    file=out/('v82e_'+state+'_'+name+'.png');scene.render.filepath=str(file.resolve());bpy.ops.render.render(write_still=True)
    im=bpy.data.images.load(str(file),check_existing=False);a=np.empty(len(im.pixels),dtype=np.float32);im.pixels.foreach_get(a);bpy.data.images.remove(im)
    y=a.reshape(-1,4)[:,:3]@np.array([.2126,.7152,.0722]);qa['views'].setdefault(name,{})[state]={'mean_luma':float(y.mean()),'p10_luma':float(np.percentile(y,10))}
for m,label in ((original,'atlas'),(clay,'clay'),(candidate,'tileable')):
    use(m)
    for view in ('altar_front','altar_oblique'):render(view,label)
assert fingerprint()==protected and fx.hide_render and fx.hide_viewport
for o in scene.objects:
    if o.type=='MESH' and o not in targets:assert [x.name if x else None for x in o.data.materials]==slots[o.name]
cam.matrix_world,cam.data.type,cam.data.lens,cam.data.clip_start,cam.data.clip_end=camera_state
scene.render.resolution_percentage,scene.cycles.samples,scene.cycles.use_denoising,scene.render.film_transparent,scene.render.image_settings.file_format,scene.render.image_settings.color_mode,scene.render.filepath=render_state
dest=out/'v82e_tileable_stone.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()));scene=bpy.context.scene
assert fingerprint()==protected and bpy.data.collections['V82_RUNE_VFX_INDEPENDENT'].hide_render
assert all(bpy.data.objects[o].data.materials[0].name=='V82E_tileable_stone_candidate' for o in ('V81_ruin_platform','V81_ruin_back','V81_ruin_posts','V81_ruin_rubble'))
qa.update({'source_unchanged':sha(src)==LOCK,'native_sha256':sha(dest),'geometry_reopen_exact':True,'default_vfx_off':True})
(out/'v82e_atlas_fix_qa.json').write_text(json.dumps(qa,indent=2));print('V82E_ATLAS_FIX_DONE',json.dumps(qa))

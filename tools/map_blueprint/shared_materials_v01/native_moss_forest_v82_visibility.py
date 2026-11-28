"""V82-A isolated visibility A/B, no geometry/material edits to source.
Screen transformed sapling bounds, then sample actual triangle intersections.
Hide at most three V81-added saplings in a NEW candidate, no formal adoption.
Ray results ignore alpha and are not rendered-pixel visibility proof.
"""
import bpy, sys, math, json, hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v82_crown_clearance import possible_overlap, bounds, selftest
selftest()
src,out=map(Path,sys.argv[sys.argv.index('--')+1:][:2])
out.mkdir(parents=True,exist_ok=True)
def sha(p):
    with open(p,'rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()
LOCK='59f2d29383872d5f5bdbf4024aa86ca726522b3dfa15c9d32768a50990464b30'
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



platform=bpy.data.objects['V81_ruin_platform']
# Recover platform top from the actual emissive inlay, not a guessed world height.
rz=[(platform.matrix_world @ platform.data.vertices[i].co).z for p in platform.data.polygons if p.material_index==1 for i in p.vertices]
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

selected_views=['matched','lateral','side','player_eye','altar_approach','trail_low']
saplings=sorted((o for o in scene.objects if o.type=='MESH' and o.name.startswith('V81_sapling_') and not o.hide_render),key=lambda o:o.name)
assert len(saplings)==15, len(saplings)
qa={'source_sha256':LOCK,'blender':bpy.app.version_string,'candidate_only':True,'scope':'reversible visibility A/B only','saplings':{},'views':{},'limits':['triangle ray tests ignore leaf alpha','whole-object AABB conservative screen','target widths provisional local units','max 3 hidden trees; not final art','D2 altar geometry open; G2/G3/G4 not certified']}
before={o.name:(tuple(tuple(row) for row in o.matrix_world),o.hide_render,o.hide_viewport) for o in scene.objects}
for o in saplings:
    verts=[o.matrix_world @ v.co for v in o.data.vertices]
    lo,hi=bounds(verts)
    bvh=BVHTree.FromPolygons(verts,[tuple(p.vertices) for p in o.data.polygons])
    counts={}
    for name in selected_views:
        eye,t,lens=VIEWS[name]
        width,height=(2.0,1.2) if name in ('player_eye','trail_low') else (3.4,2.2)
        hit=0
        if possible_overlap(eye,t,lo,hi,width,height):
            f=(t-eye).normalized(); right=f.cross(Vector((0,0,1))).normalized(); up=right.cross(f)
            for i in range(9):
                for j in range(7):
                    target=t+right*((i/8*2-1)*width)+up*((j/6*2-1)*height)
                    d=target-eye
                    if bvh.ray_cast(eye,d.normalized(),d.length)[0] is not None: hit+=1
        counts[name]=hit
    qa['saplings'][o.name]={'world_aabb':[lo,hi],'triangle_hits_of_63':counts,'score':sum(counts.values())}
ranked=sorted(saplings,key=lambda o:(-qa['saplings'][o.name]['score'],o.name))
hide=[o for o in ranked[:3] if qa['saplings'][o.name]['score']>=4]
qa['hidden']=[o.name for o in hide]
for o in hide: o.hide_render=True
# Preserve every object's transform and all non-selected visibility flags.
after={o.name:(tuple(tuple(row) for row in o.matrix_world),o.hide_render,o.hide_viewport) for o in scene.objects}
assert set(before)==set(after)
assert all(before[k][0]==after[k][0] and before[k][2]==after[k][2] and (before[k][1]==after[k][1] or k in qa['hidden']) for k in before)
assert sha(src)==LOCK
dest=out/'v82a_visibility_candidate.blend'
assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()))
scene=bpy.context.scene; cam=scene.camera
assert {o.name:(tuple(tuple(row) for row in o.matrix_world),o.hide_render,o.hide_viewport) for o in scene.objects}==after
qa['native_sha256']=sha(dest);qa['reopen_visibility_transform_exact']=True
(out/'v82a_qa.json').write_text(json.dumps(qa,indent=2))
import numpy as np
def set_view(name):
    p,t,lens=VIEWS[name];cam.data.type='PERSP';cam.location=p;cam.rotation_euler=(t-p).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;cam.data.clip_start=.05;cam.data.clip_end=600
def render(name,file,alpha=False):
    set_view(name);scene.render.resolution_percentage=50;scene.cycles.samples=8 if alpha else 24;scene.cycles.use_denoising=not alpha
    scene.render.film_transparent=alpha;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA' if alpha else 'RGB'
    scene.render.filepath=str((out/file).resolve());bpy.ops.render.render(write_still=True)
    im=bpy.data.images.load(scene.render.filepath);a=np.array(im.pixels[:],dtype=np.float32).reshape(im.size[1],im.size[0],4);bpy.data.images.remove(im);return a
for name in ['matched','lateral','side','player_eye','altar_approach','look_up']:
    a=render(name,'v82a_'+name+'.png');y=a[:,:,:3]@np.array([.2126,.7152,.0722])
    qa['views'][name]={'luma_mean':float(y.mean())}
    vnode=scene.world.node_tree.nodes['V79_atmosphere'];vnode.mute=True
    a=render(name,'v82a_sky_'+name+'.png',True);vnode.mute=False
    qa['views'][name]['sky_exposure']=float((1-a[:,:,3]).mean())
    (out/'v82a_qa.json').write_text(json.dumps(qa,indent=2))
clay=bpy.data.materials.new('V82a_DIAGNOSTIC_ONLY');clay.use_nodes=True
clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.55,.55,.55,1)
scene.view_layers[0].material_override=clay
render('altar_oblique','v82a_clay_altar_oblique.png')
scene.view_layers[0].material_override=None
qa['source_unchanged']=sha(src)==LOCK
(out/'v82a_qa.json').write_text(json.dumps(qa,indent=2))
print('V82A_DONE',json.dumps(qa))

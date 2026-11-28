"""V94 forest-floor lane: 3D leaf litter, sedge tufts across the bare moss lawn, low roots crossing the animal trail.

Director 2026-11-27: keep raising density/quality; animal trail, not a kept road. Built on SHA-locked V90 native
(altar/VFX/LOD/lighting lanes untouched). Deterministic: seeded RNG, sorted iteration only.
Usage: blender -b --factory-startup --python native_forest_floor_v94.py -- V90.blend OUT [--preview] [--no-render]
Isolated candidate: provisional local coordinates, no collision/canonical placement/adoption.
"""
import bpy, bmesh, sys, math, hashlib, json, random, time
from pathlib import Path
from array import array
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
src, out = Path(argv[0]), Path(argv[1])
RENDER = '--no-render' not in argv; PREVIEW = '--preview' in argv
out.mkdir(parents=True, exist_ok=True); T0 = time.time()


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


LOCK = 'bdf76b553f04427eb3408fdee0a0aa1dc32e658b8c53f44eb638a4460823d446'      # V90 artifact 15192905787 native
assert bpy.app.version[:3] == (5, 3, 0)
assert sha(src) == LOCK, 'V90 source SHA mismatch'
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()))
scene = bpy.context.scene; cam = scene.camera
rng = random.Random(20261128094)


def digest(data, prop, count, code):
    a = array(code, [0]) * count
    if count:
        data.foreach_get(prop, a)
    return hashlib.sha256(a.tobytes()).hexdigest()


def snap():
    result = {}; cache = {}
    for o in scene.objects:
        if o.type == 'LIGHT':
            result[o.name] = ('L', o.data.energy, tuple(tuple(r) for r in o.matrix_world)); continue
        if o.type != 'MESH':
            continue
        m = o.data
        if m.name not in cache:
            cache[m.name] = (digest(m.vertices, 'co', len(m.vertices) * 3, 'f'), digest(m.loops, 'vertex_index', len(m.loops), 'i'),
                             digest(m.polygons, 'material_index', len(m.polygons), 'i'), tuple(x.name if x else None for x in m.materials))
        result[o.name] = (cache[m.name], tuple(tuple(r) for r in o.matrix_world), o.hide_render)
    return result


old = snap()
QA = dict(status='V94_FOREST_FLOOR_CANDIDATE', lane='forest floor only (altar, VFX, LOD, lighting lanes untouched)', source='V90 native', source_sha256=LOCK, blender=bpy.app.version_string)

# ---------------------------------------------------------------- anchors (identical to V79-V81)
EYE = Vector((78.17052459716797, -80.77701568603516, 29.82533073425293))
ALTAR = Vector((93.94316101074219, -93.07432556152344, 30.988130569458008))
A_, B_ = Vector((-205, 140)), Vector((90, -90))
FWD = (ALTAR - EYE).to_2d().normalized(); PERP = Vector((-FWD.y, FWD.x)); CENTER = (EYE.to_2d() + ALTAR.to_2d()) / 2
SIDE = Vector((.6148655745981655, .788631932636555)); C0 = ALTAR.to_2d(); FD = -FWD; FDP = Vector((-FD.y, FD.x))
U = (B_ - A_).normalized(); N_ = Vector((-U.y, U.x)); LEN = (B_ - A_).length; Z = Vector((0, 0, 1))
terrain = bpy.data.objects['A3 provisional reconstructed terrain']; ext = bpy.data.objects['V58_SCENIC_ONLY_terrain_extension']; far = bpy.data.objects['V77_SCENIC_ONLY_FAR_RELIEF']


def world_bvh(objs):
    verts = []; polys = []
    for o in objs:
        mw = o.matrix_world; base = len(verts)
        verts += [mw @ v.co for v in o.data.vertices]; polys += [[base + i for i in p.vertices] for p in o.data.polygons]
    return BVHTree.FromPolygons(verts, polys)


GROUND = world_bvh([terrain, ext, far])
RUIN = world_bvh([o for o in sorted(bpy.data.collections['V81_RUNE_SANCTUARY'].objects, key=lambda o: o.name) if o.type == 'MESH'])


def ground(x, y):
    hit = GROUND.ray_cast(Vector((x, y, 300)), Vector((0, 0, -1)), 400)
    return (hit[0].z, hit[1]) if hit[0] else (None, None)


def on_ruin(x, y):
    g = ground(x, y)[0]; h = RUIN.ray_cast(Vector((x, y, 80)), Vector((0, 0, -1)), 120)
    return h[0] is not None and g is not None and h[0].z > g + .03


def meander(a):
    fade = max(0., min(1., (LEN - a) / 9.0)); return (1.1 * math.sin(.23 * a) + .5 * math.sin(.61 * a + 1.3)) * fade


def trail_dist(p):
    w = p - A_; a = w.dot(U)
    return (p - B_).length if a > LEN else abs(w.dot(N_) - meander(a))


A_EYE = (EYE.to_2d() - A_).dot(U)
TRUNKS = sorted([(o.matrix_world.translation.to_2d(), 1.2 if o.data.name == 'island_trees_01_blockout_cleaned' else .45)
                 for o in scene.objects if o.type == 'MESH' and (o.data.name == 'island_trees_01_blockout_cleaned' or o.data.name.startswith('eco_tree'))], key=lambda t: (t[0].x, t[0].y))


def near_trunk(p, extra=0.):
    return any((p - c).length < r + extra for c, r in TRUNKS)


# ================================================================ review views + V90 baseline renders (before any change, identical settings)
import numpy as np


def eye_at(p2, h=1.7):
    g = ground(p2.x, p2.y)[0]; return Vector((p2.x, p2.y, (g if g is not None else EYE.z - 1.7) + h))


gT = max(ground(*(C0 + FD * math.cos(q) * r + FDP * math.sin(q) * r))[0] for r in (0, 2, 4.4) for q in [i * math.tau / 12 for i in range(12)]) + .32
a_tl = LEN - 9; tl = A_ + U * a_tl + N_ * meander(a_tl)
cl = C0 + FD * 9.0 + FDP * 7.5
VIEWS = {
    'matched': (EYE, ALTAR, 22),
    'player_eye': (eye_at(EYE.to_2d() - FWD * 12), eye_at(EYE.to_2d() + FWD * 14, 1.5), 28),
    'trail_low': (eye_at(tl, 1.05), eye_at(A_ + U * (LEN - 1) + N_ * meander(LEN - 1), .6), 24),
    'side': (eye_at(C0 + PERP * 14), ALTAR, 24),
    'altar_oblique': (Vector((*(C0 + FD * 10.5 + FDP * 3.5), gT + 6.2)), Vector((C0.x, C0.y, gT + .9)), 24),
    'clearing_low': (eye_at(cl, .9), eye_at(C0 + FDP * 2.0, .5), 26),
}
RES = 50 if PREVIEW else 100; SPP = 12 if PREVIEW else 64
rd = out / 'renders'; rd.mkdir(exist_ok=True)


def set_view(n):
    p, t, lens = VIEWS[n]; cam.data.type = 'PERSP'; cam.location = p; cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = lens; cam.data.clip_start = .05; cam.data.clip_end = 600


def render(path, spp=None):
    scene.render.resolution_percentage = RES; scene.cycles.samples = spp or SPP; scene.cycles.use_denoising = True; scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGB'
    scene.render.filepath = str(Path(path).resolve()); bpy.ops.render.render(write_still=True); return Path(path)


def load_px(p):
    im = bpy.data.images.load(str(p)); a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4); bpy.data.images.remove(im); return a


def save_px(arr, path):
    h, w = arr.shape[:2]; im = bpy.data.images.new(Path(path).stem, w, h, alpha=True)
    im.pixels.foreach_set(np.ascontiguousarray(arr, dtype=np.float32).ravel()); im.filepath_raw = str(path); im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)


cam_keep = (cam.location.copy(), cam.rotation_euler.copy(), cam.data.lens, cam.data.clip_start, cam.data.clip_end, cam.data.type)
if RENDER:
    for n in VIEWS:
        set_view(n); render(rd / ('v90_base_%s.png' % n))
cam.location, cam.rotation_euler, cam.data.lens, cam.data.clip_start, cam.data.clip_end, cam.data.type = cam_keep
QA['baseline'] = 'V90 native rendered in this run before any change (same camera/res/spp/lighting)'

# ================================================================ materials
def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); b = nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(b.outputs[0], o.inputs[0]); return m, nt, b


def litter_material():
    m, nt, b = node_mat('V94_leaf_litter'); N = nt.nodes; L = nt.links
    att = N.new('ShaderNodeAttribute'); att.attribute_name = 'tone'; att.attribute_type = 'GEOMETRY'
    cr = N.new('ShaderNodeValToRGB'); E = cr.color_ramp.elements
    E[0].position = 0; E[0].color = (.055, .03, .015, 1); E[1].position = 1; E[1].color = (.36, .2, .065, 1)
    e = E.new(.45); e.color = (.16, .095, .035, 1); e = E.new(.75); e.color = (.2, .17, .06, 1)
    L.new(att.outputs['Fac'], cr.inputs['Fac']); L.new(cr.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = .72; b.inputs['Subsurface Weight'].default_value = .08; b.inputs['Specular IOR Level'].default_value = .3
    return m


def sedge_material():
    m, nt, b = node_mat('V94_sedge'); N = nt.nodes; L = nt.links
    att = N.new('ShaderNodeAttribute'); att.attribute_name = 'h'; att.attribute_type = 'GEOMETRY'
    tn = N.new('ShaderNodeAttribute'); tn.attribute_name = 'tone'; tn.attribute_type = 'GEOMETRY'
    cr = N.new('ShaderNodeValToRGB'); E = cr.color_ramp.elements
    E[0].position = 0; E[0].color = (.035, .06, .02, 1); E[1].position = 1; E[1].color = (.34, .38, .11, 1)
    e = E.new(.55); e.color = (.12, .2, .05, 1)
    L.new(att.outputs['Fac'], cr.inputs['Fac'])
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; L.new(tn.outputs['Fac'], mx.inputs['Factor'])
    L.new(cr.outputs['Color'], mx.inputs['A']); mx.inputs['B'].default_value = (.72, .62, .45, 1)
    L.new(mx.outputs['Result'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = .55
    b.inputs['Transmission Weight'].default_value = .18; b.inputs['Subsurface Weight'].default_value = .1
    return m


LITTER = litter_material(); SEDGE = sedge_material(); WOOD = bpy.data.materials['V80_mossy_root_bark']


# ================================================================ procedural meshes
def leaf_patch(i, n=46, radius=.5):
    """Patch of individual curled leaves (lobed outline, folded midrib, lifted tip), per-leaf tone attribute."""
    rr = random.Random(9400 + i); bm = bmesh.new(); tone = bm.faces.layers.float.new('tone'); uvl = bm.loops.layers.uv.new('UVMap')
    for k in range(n):
        r = radius * math.sqrt(rr.random()); a = rr.uniform(0, math.tau); c = Vector((math.cos(a) * r, math.sin(a) * r, 0))
        L = rr.uniform(.045, .095); W = L * rr.uniform(.42, .62); yaw = rr.uniform(0, math.tau); curl = rr.uniform(.004, .016); t = rr.random()
        R = Matrix.Rotation(yaw, 3, 'Z'); z0 = .0015 * (k % 6)                      # slight stacking so leaves overlap without z-fighting
        tip = c + R @ Vector((L / 2, 0, z0 + curl)); base = c + R @ Vector((-L / 2, 0, z0 + curl * .4)); mid = c + R @ Vector((0, 0, z0 + .002))
        ring = [base]
        for s, side in ((1, 1), (-1, -1)):
            pass
        pts = []
        for j in range(1, 6):
            u = j / 6; x = -L / 2 + L * u; w = W / 2 * math.sin(math.pi * u) ** .8 * (1 + .12 * math.sin(u * 18))
            pts.append((x, w, u))
        left = [c + R @ Vector((x, w, z0 + curl * abs(2 * u - 1) ** 2 * (1.2 if u > .5 else .4) + .006 * (w / (W / 2 + 1e-6)))) for x, w, u in pts]
        right = [c + R @ Vector((x, -w, z0 + curl * abs(2 * u - 1) ** 2 * (1.2 if u > .5 else .4) + .006 * (w / (W / 2 + 1e-6)))) for x, w, u in pts]
        vb = bm.verts.new(base); vt = bm.verts.new(tip); vm = [bm.verts.new(c + R @ Vector((x, 0, z0 + .0005 + curl * abs(2 * u - 1) ** 2 * (1.2 if u > .5 else .4)))) for x, w, u in pts]
        vl = [bm.verts.new(p) for p in left]; vr = [bm.verts.new(p) for p in right]
        faces = []
        faces.append(bm.faces.new((vb, vl[0], vm[0]))); faces.append(bm.faces.new((vb, vm[0], vr[0])))
        for j in range(4):
            faces.append(bm.faces.new((vm[j], vl[j], vl[j + 1], vm[j + 1]))); faces.append(bm.faces.new((vm[j], vm[j + 1], vr[j + 1], vr[j])))
        faces.append(bm.faces.new((vm[4], vl[4], vt))); faces.append(bm.faces.new((vm[4], vt, vr[4])))
        for f in faces:
            f[tone] = t
            for lp in f.loops:
                lp[uvl].uv = (lp.vert.co.x + .5, lp.vert.co.y + .5)
    me = bpy.data.meshes.new('V94_leaf_patch_%d' % i); bm.to_mesh(me); bm.free(); me.materials.append(LITTER)
    for p in me.polygons:
        p.use_smooth = True
    return me


def sedge_tuft(i):
    rr = random.Random(9500 + i); bm = bmesh.new(); hl = bm.verts.layers.float.new('h'); tone = bm.faces.layers.float.new('tone'); uvl = bm.loops.layers.uv.new('UVMap')
    nb = rr.randint(14, 26); t = rr.random()
    for k in range(nb):
        a = rr.uniform(0, math.tau); r0 = rr.uniform(0, .05); H = rr.uniform(.22, .58); lean = rr.uniform(.15, .75); w = rr.uniform(.006, .011)
        d = Vector((math.cos(a), math.sin(a), 0)); side = Vector((-d.y, d.x, 0)); prev = None
        for s in range(5):
            u = s / 4; pos = d * (r0 + H * lean * u * u) + Vector((0, 0, H * (u - .45 * lean * u * u)))
            ww = w * (1 - .85 * u)
            pair = (bm.verts.new(pos + side * ww), bm.verts.new(pos - side * ww))
            for v in pair:
                v[hl] = u
            if prev:
                f = bm.faces.new((prev[0], prev[1], pair[1], pair[0])); f[tone] = t
                for lp, uv in zip(f.loops, ((0, u - .25), (1, u - .25), (1, u), (0, u))):
                    lp[uvl].uv = uv
            prev = pair
    me = bpy.data.meshes.new('V94_sedge_%d' % i); bm.to_mesh(me); bm.free(); me.materials.append(SEDGE)
    me.attributes.active = None
    return me


PATCHES = [leaf_patch(i) for i in range(8)]; TUFTS = [sedge_tuft(i) for i in range(6)]
for me in PATCHES + TUFTS:
    me.calc_loop_triangles()
coll = bpy.data.collections.new('V94_FOREST_FLOOR'); scene.collection.children.link(coll)
COUNT = {}; FLO = []


def place(me, kind, x, y, scale=1.0, align=True, sink=.004):
    z, n = ground(x, y)
    if z is None or on_ruin(x, y):
        return None
    n = n if (align and n is not None) else Z
    rot = n.to_track_quat('Z', 'Y').to_matrix().to_4x4() @ Matrix.Rotation(rng.uniform(0, math.tau), 4, 'Z')
    o = bpy.data.objects.new('V94_%s_%05d' % (kind, sum(COUNT.values())), me); coll.objects.link(o)
    o.matrix_world = Matrix.Translation(Vector((x, y, z - sink))) @ rot @ Matrix.Scale(scale, 4)
    o['scenic_only'] = True; COUNT[kind] = COUNT.get(kind, 0) + 1
    return o


# ---- leaf litter: denser on/along the trail and at tree bases, sparser on open moss
for i in range(9000):
    if COUNT.get('litter', 0) >= 2600:
        break
    mode = rng.random()
    if mode < .45:
        a = rng.uniform(A_EYE - 32, LEN - .5); p = A_ + U * a + N_ * (meander(a) + rng.gauss(0, 1.3))
    elif mode < .75:
        c, r = TRUNKS[rng.randrange(len(TRUNKS))]; ang = rng.uniform(0, math.tau); p = c + Vector((math.cos(ang), math.sin(ang))) * (r + abs(rng.gauss(0, 2.2)))
    else:
        p = CENTER + Vector((rng.uniform(-38, 38), rng.uniform(-38, 38)))
    if (p - CENTER).length > 42 or (p - C0).length < 4.9 or near_trunk(p, .1):
        continue
    if mode >= .75 and rng.random() < .5:                                      # open moss stays partly clear
        continue
    place(PATCHES[rng.randrange(len(PATCHES))], 'litter', p.x, p.y, rng.uniform(.75, 1.25))

# ---- sedge tufts in clumps across the bare moss lawn (not on the trail core, not on the ruin)
clumps = 0
for i in range(6000):
    if COUNT.get('sedge', 0) >= 2400:
        break
    p = CENTER + Vector((rng.uniform(-36, 36), rng.uniform(-36, 36)))
    if (p - CENTER).length > 38 or (p - C0).length < 4.7 or trail_dist(p) < 1.0 or near_trunk(p, .3):
        continue
    clumps += 1
    for j in range(rng.randint(4, 14)):
        q = p + Vector((rng.gauss(0, .45), rng.gauss(0, .45)))
        if trail_dist(q) < .8 or (q - C0).length < 4.6 or near_trunk(q, .15):
            continue
        place(TUFTS[rng.randrange(len(TUFTS))], 'sedge', q.x, q.y, rng.uniform(.7, 1.35), align=False, sink=.01)


# ================================================================ low roots crossing the trail (walkable: crest <= 0.12 m above ground)
def tube_mesh(name, rings, sides=8):
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); verts = []; vlen = 0.
    for k, (c, r, vs) in enumerate(rings):
        t = (rings[min(k + 1, len(rings) - 1)][0] - rings[max(k - 1, 0)][0]).normalized(); a = t.cross(Z)
        if a.length < 1e-4:
            a = Vector((1, 0, 0))
        a.normalize(); b = t.cross(a)
        if k:
            vlen += (c - rings[k - 1][0]).length
        verts.append([(bm.verts.new(c + (a * math.cos(q) + b * math.sin(q) * vs) * r), vlen) for q in [i * math.tau / sides for i in range(sides)]])
    for k in range(len(verts) - 1):
        for i in range(sides):
            j = (i + 1) % sides; f = bm.faces.new((verts[k][i][0], verts[k][j][0], verts[k + 1][j][0], verts[k + 1][i][0]))
            for lp, (u, v) in zip(f.loops, ((i / sides, verts[k][i][1]), ((i + 1) / sides, verts[k][j][1]), ((i + 1) / sides, verts[k + 1][j][1]), (i / sides, verts[k + 1][i][1]))):
                lp[uvl].uv = (u, v * .5)
    for ring in (verts[0], verts[-1]):
        bm.faces.new([v for v, _ in ring])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p_ in me.polygons:
        p_.use_smooth = True
    me.materials.append(WOOD); return me


CROSS = []; parts = []
oaks = sorted([c for c, r in TRUNKS], key=lambda c: (c.x, c.y))
for c in oaks:
    w = c - A_; a = w.dot(U)
    if not (A_EYE - 34 < a < LEN - 6):
        continue
    s = w.dot(N_) - meander(a)
    if not (1.8 < abs(s) < 14.0):
        continue
    for k in range(rng.randint(1, 2)):
        # from the trunk towards and across the trail, sinking past it
        a2 = a + rng.uniform(-2.5, 2.5); far_side = A_ + U * a2 + N_ * (meander(a2) - math.copysign(rng.uniform(1.4, 2.6), s))
        st = c + (far_side - c).normalized() * 1.0; n = 16; r0 = rng.uniform(.06, .11); rings = []; ok = True
        side = Vector((-(far_side - st).y, (far_side - st).x)).normalized(); ph = rng.uniform(0, math.tau)
        for i in range(n + 1):
            t = i / n; q = st.lerp(far_side, t) + side * math.sin(ph + t * 6) * .25 * math.sin(math.pi * t)
            g = ground(q.x, q.y)[0]
            if g is None or on_ruin(q.x, q.y) or (q - C0).length < 5.0:
                ok = False; break
            rad = r0 * (1 - .55 * t) + .015
            crest = min(.12, rad * 1.1) * (1 - t ** 3) - .06 * t ** 2               # emerges, crosses, dives
            rings.append((Vector((q.x, q.y, g + crest - rad * .6)), rad, .8))
        if ok and len(rings) > 6:
            parts.append(tube_mesh('cr', rings)); CROSS.append(dict(from_trunk=[round(c.x, 2), round(c.y, 2)], length=round((far_side - st).length, 2), max_crest_m=.12))
if parts:
    bm = bmesh.new()
    for me in parts:
        bm.from_mesh(me); bpy.data.meshes.remove(me)
    rme = bpy.data.meshes.new('V94_trail_roots'); bm.to_mesh(rme); bm.free(); rme.materials.append(WOOD)
    ro = bpy.data.objects.new('V94_trail_roots', rme); coll.objects.link(ro); ro['scenic_only'] = True

# ================================================================ sanctuary dressing (handoff 9-A/B): ground cover ring, enveloping roots, climbing ivy, ledge moss, pebbles
FX = [o for o in scene.objects if o.name.startswith('V82_FX_')]
FX_BVH = world_bvh(FX) if FX else None
RUIN_OBJS = sorted([o for o in bpy.data.collections['V81_RUNE_SANCTUARY'].objects if o.type == 'MESH'], key=lambda o: o.name)


def polar(r, a):
    return C0 + FD * math.cos(a) * r + FDP * math.sin(a) * r


def ang_of(p):
    d = p - C0; return math.atan2(d.dot(FDP), d.dot(FD))


TPL = {}
for o in sorted(scene.objects, key=lambda o: o.name):
    if o.name.startswith('V79_u_'):
        TPL.setdefault(o.name.split('_')[2], {}).setdefault(o.data.name, o)
TPL = {k: [v[n] for n in sorted(v)] for k, v in TPL.items()}


def place_tpl(kind, x, y, hrange, align=False):
    src_kind = kind.replace('ring_', ''); t = TPL[src_kind][rng.randrange(len(TPL[src_kind]))]; m = t.data; lin3 = t.matrix_world.to_3x3()
    pts = [lin3 @ m.vertices[i].co for i in range(0, len(m.vertices), max(1, len(m.vertices) // 200))]
    h = max(p.z for p in pts) - min(p.z for p in pts); fac = rng.uniform(*hrange) / max(h, 1e-4)
    lin = Matrix.Rotation(rng.uniform(0, math.tau), 4, 'Z') @ Matrix.Scale(fac, 4) @ lin3.to_4x4()
    pts = [lin @ m.vertices[i].co for i in range(0, len(m.vertices), max(1, len(m.vertices) // 200))]
    cx = sum(p.x for p in pts) / len(pts); cy = sum(p.y for p in pts) / len(pts); zmin = min(p.z for p in pts)
    g = ground(x, y)[0]
    if g is None or on_ruin(x, y):
        return None
    o = bpy.data.objects.new('V94_%s_%05d' % (kind, sum(COUNT.values())), m); coll.objects.link(o)
    o.matrix_world = Matrix.Translation(Vector((x - cx, y - cy, g - zmin - .015))) @ lin; o['scenic_only'] = True; COUNT[kind] = COUNT.get(kind, 0) + 1
    return o


STEP_HALF = math.radians(40)
for i in range(7000):
    if COUNT.get('ring_fern', 0) >= 260 and COUNT.get('ring_sedge', 0) >= 1500:
        break
    r = 4.7 + abs(rng.gauss(0, 3.4)); a = rng.uniform(-math.pi, math.pi)
    if r > 14 or abs(a) < STEP_HALF and r < 9:
        continue
    p = polar(r, a)
    if trail_dist(p) < .9 or near_trunk(p, .2):
        continue
    if rng.random() < .3 and COUNT.get('ring_fern', 0) < 260:
        place_tpl('ring_fern', p.x, p.y, (.55, 1.15))
    else:
        for j in range(rng.randint(3, 9)):
            q = p + Vector((rng.gauss(0, .3), rng.gauss(0, .3)))
            if (q - C0).length > 4.6 and trail_dist(q) > .8 and place(TUFTS[rng.randrange(len(TUFTS))], 'ring_sedge', q.x, q.y, rng.uniform(.9, 1.5), align=False, sink=.01):
                pass
for i in range(400):
    if COUNT.get('ring_moss', 0) >= 150:
        break
    r = 4.6 + abs(rng.gauss(0, 2.2)); a = rng.uniform(-math.pi, math.pi); p = polar(r, a)
    if trail_dist(p) > .9 and not near_trunk(p, .1):
        place_tpl('ring_moss', p.x, p.y, (.12, .3))


# ---- pebbles (deformed icospheres, stone photo material), at ruin base, step foot and along the trail
def pebble(i):
    rr = random.Random(9600 + i); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    sx, sy, sz = rr.uniform(.8, 1.3), rr.uniform(.6, 1.0), rr.uniform(.35, .6)
    for v in bm.verts:
        n = v.co.normalized(); d = 1 + .18 * math.sin(n.x * 5.1 + i) * math.cos(n.y * 4.3 - i) + .08 * math.sin(n.z * 9.7)
        v.co = Vector((n.x * sx * d, n.y * sy * d, n.z * sz * d))
    uvl = bm.loops.layers.uv.new('UVMap')
    for f in bm.faces:
        for lp in f.loops:
            lp[uvl].uv = (lp.vert.co.x * .5 + .5 + i * .13, lp.vert.co.y * .5 + .5 + lp.vert.co.z * .3)
    me = bpy.data.meshes.new('V94_pebble_%d' % i); bm.to_mesh(me); bm.free()
    for p_ in me.polygons:
        p_.use_smooth = True
    me.materials.append(PEB_M); me.calc_loop_triangles(); return me


def pebble_material():
    m, nt, b = node_mat('V94_pebble'); N = nt.nodes; L = nt.links
    img = sorted([i for i in bpy.data.images if i.name.startswith('rock_moss_set_01_diff')], key=lambda i: i.name)[0]
    t = N.new('ShaderNodeTexImage'); t.image = img
    hs = N.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = .35; hs.inputs['Value'].default_value = 1.7
    L.new(t.outputs['Color'], hs.inputs['Color']); L.new(hs.outputs[0], b.inputs['Base Color']); b.inputs['Roughness'].default_value = .82
    return m


PEB_M = pebble_material()
PEB = [pebble(i) for i in range(6)]
for i in range(3000):
    if COUNT.get('pebble', 0) >= 600:
        break
    if rng.random() < .55:
        r = 4.5 + abs(rng.gauss(0, 1.6)); p = polar(r, rng.uniform(-math.pi, math.pi))
    else:
        a = rng.uniform(A_EYE - 30, LEN - .5); p = A_ + U * a + N_ * (meander(a) + rng.gauss(0, 1.0))
    if near_trunk(p, .05):
        continue
    sc_ = rng.uniform(.03, .11)
    o = place(PEB[rng.randrange(6)], 'pebble', p.x, p.y, sc_, align=False, sink=sc_ * .3)


# ---- thick roots enveloping the ruin: from nearby oaks to the curb, hugging masonry, wrapping along the ring, diving
def surface_z(x, y):
    g = ground(x, y)[0]; h = RUIN.ray_cast(Vector((x, y, 80)), Vector((0, 0, -1)), 120)
    return max(g if g is not None else -1e9, h[0].z if h[0] else -1e9)


ENV = []; eparts = []
near_oaks = sorted([c for c, r in TRUNKS if r > 1 and 6 < (c - C0).length < 19], key=lambda c: (c - C0).length)[:6]
for c in near_oaks:
    for k in range(rng.randint(2, 3)):
        a_end = ang_of(c) + rng.uniform(-.5, .5); wrap = rng.choice((-1, 1)) * rng.uniform(.35, .9)
        if abs(((a_end + math.pi) % math.tau) - math.pi) < STEP_HALF:                    # keep the step approach readable
            continue
        st = c + (polar(4.6, a_end) - c).normalized() * 1.2; r0 = rng.uniform(.17, .3); pts = []
        n1 = 14
        for i in range(n1 + 1):
            t = i / n1; q = st.lerp(polar(4.75, a_end), t); q += Vector((-(polar(4.75, a_end) - st).y, (polar(4.75, a_end) - st).x)).normalized() * math.sin(t * 5 + k) * .3 * math.sin(math.pi * t); pts.append(q)
        for i in range(1, 11):
            pts.append(polar(4.72 - .02 * i, a_end + wrap * i / 10))
        rings = []
        for i, q in enumerate(pts):
            t = i / (len(pts) - 1); rad = r0 * (1 - .75 * t) + .03
            dive = -.25 * max(0, (t - .88) / .12)
            rings.append((Vector((q.x, q.y, surface_z(q.x, q.y) + rad * .55 + dive)), rad, 1.15 - .35 * t))
        eparts.append(tube_mesh('env', rings, 10)); ENV.append(dict(from_oak=[round(c.x, 2), round(c.y, 2)], end_angle_deg=round(math.degrees(a_end), 1), wrap_deg=round(math.degrees(wrap), 1)))
if eparts:
    bm = bmesh.new()
    for me in eparts:
        bm.from_mesh(me); bpy.data.meshes.remove(me)
    eme = bpy.data.meshes.new('V94_enveloping_roots'); bm.to_mesh(eme); bm.free(); eme.materials.append(WOOD)
    eo = bpy.data.objects.new('V94_enveloping_roots', eme); coll.objects.link(eo); eo['scenic_only'] = True


# ---- climbing ivy: continuous stems found by ray-casting the actual masonry; 3D lobed leaves with petioles
def ivy_leaf_material():
    m, nt, b = node_mat('V94_ivy_leaf'); N = nt.nodes; L = nt.links
    tn = N.new('ShaderNodeAttribute'); tn.attribute_name = 'tone'; tn.attribute_type = 'GEOMETRY'
    cr = N.new('ShaderNodeValToRGB'); E = cr.color_ramp.elements
    E[0].color = (.02, .045, .015, 1); E[1].color = (.13, .2, .05, 1); e = E.new(.6); e.color = (.05, .1, .025, 1)
    L.new(tn.outputs['Fac'], cr.inputs['Fac']); L.new(cr.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = .38; b.inputs['Transmission Weight'].default_value = .12; b.inputs['Specular IOR Level'].default_value = .55
    return m


IVY_M = ivy_leaf_material(); ivb = bmesh.new(); ivt = ivb.faces.layers.float.new('tone'); ivuv = ivb.loops.layers.uv.new('UVMap'); STEMS = []; NLEAF = [0]


def add_leaf(at, normal, up, size):
    side = up.cross(normal).normalized(); ang = rng.uniform(-.9, .9)
    ax = (up * math.cos(ang) + side * math.sin(ang)).normalized(); ay = normal.cross(ax).normalized()
    nrm = (normal + ax * rng.uniform(-.25, .1)).normalized(); tone = rng.random()
    base = at + nrm * rng.uniform(.015, .05) + ax * .02
    outline = [(0, 0), (.25, .32), (.5, .48), (.62, .3), (1.0, 0), (.62, -.3), (.5, -.48), (.25, -.32)]   # ivy-like lobes
    cen = ivb.verts.new(base + ax * size * .42 + nrm * size * .06)
    vs = [ivb.verts.new(base + (ax * u + ay * w) * size + nrm * (size * .05 * (1 - abs(w) * 2))) for u, w in outline]
    for j in range(len(vs)):
        f = ivb.faces.new((cen, vs[j], vs[(j + 1) % len(vs)])); f[ivt] = tone
        for lp in f.loops:
            lp[ivuv].uv = (.5, .5)
    NLEAF[0] += 1


def climb(struct_c, face_dir, x_off, h_max, festoon=False):
    """Stem from ground up a face: horizontal ray towards the structure each 6 cm finds the real surface."""
    side = Vector((-face_dir.y, face_dir.x, 0)); g = ground(struct_c.x, struct_c.y)[0]
    pts = []; z = g + .02; x = x_off; sway = rng.uniform(0, math.tau)
    while z < g + h_max:
        o_ = struct_c.to_3d() + face_dir * 3.0 + side * (x + math.sin(sway + z * 2.3) * .06); o_.z = z
        hit = RUIN.ray_cast(o_, -face_dir, 3.5)
        if hit[0] is None:
            break
        pts.append((hit[0] + hit[1] * .018, hit[1])); z += .06
    if len(pts) < 6:
        return 0
    if festoon:                                                          # hang back down from the top a little
        top, n = pts[-1]
        for k in range(1, rng.randint(4, 10)):
            pts.append((top + n * (.04 + .015 * k) + Vector((0, 0, -.07 * k)), n))
    rings = [(p, .009, 1.0) for p, n in pts]
    STEMS.append(tube_mesh('stem', rings, 5))
    for k, (p, n) in enumerate(pts):
        if k % 2 == 0 or rng.random() < .3:
            for j in range(rng.randint(1, 3)):
                add_leaf(p, n, Vector((0, 0, 1)), rng.uniform(.06, .12))
    return len(pts)


STRUCT_ANGLES = {'stele': (180, 5.5, .5, 4.6), 'pillar': ((156, -156), 5.85, .4, 3.3), 'niche': ((128, -128), 5.85, 1.35, 3.5), 'wall': ((104, -104), 5.85, 1.0, 1.9)}
for kind, (angs, rr_, half, hmax) in STRUCT_ANGLES.items():
    for deg in (angs if isinstance(angs, tuple) else (angs,)):
        c = polar(rr_, math.radians(deg)); inward = (C0 - c).normalized().to_3d(); tang = Vector((-inward.y, inward.x, 0))
        for face, offs in ((inward, [-half * .8, half * .8] if kind == 'stele' else [rng.uniform(-half, half) for _ in range(3)]),
                           (-inward, [rng.uniform(-half, half) for _ in range(2)]), (tang, [0]), (-tang, [0])):
            for xo in offs:
                climb(c, face, xo, hmax * rng.uniform(.6, 1.0), festoon=kind in ('niche', 'stele'))
if STEMS:
    bm = bmesh.new()
    for me in STEMS:
        bm.from_mesh(me); bpy.data.meshes.remove(me)
    sme = bpy.data.meshes.new('V94_ivy_stems'); bm.to_mesh(sme); bm.free(); sme.materials.append(WOOD)
    so = bpy.data.objects.new('V94_ivy_stems', sme); coll.objects.link(so); so['scenic_only'] = True
# rune clearance: drop any leaf face within 6 cm of an independent rune FX mesh (stele glyph, post strips, floor)
removed = 0
if FX_BVH:
    kill = [f for f in ivb.faces if FX_BVH.find_nearest(f.calc_center_median(), .06)[0] is not None]
    removed = len(kill); bmesh.ops.delete(ivb, geom=kill, context='FACES')
lme = bpy.data.meshes.new('V94_ivy_leaves'); ivb.to_mesh(lme); ivb.free(); lme.materials.append(IVY_M)
lo = bpy.data.objects.new('V94_ivy_leaves', lme); coll.objects.link(lo); lo['scenic_only'] = True


# ---- 3D moss cushions on masonry ledges (post caps, wall tops, step edges), not on the rune disc
LEDGE = 0
for i in range(5000):
    if LEDGE >= 120:
        break
    r = rng.uniform(3.9, 6.6); aa = rng.uniform(-math.pi, math.pi); p = polar(r, aa)
    h = RUIN.ray_cast(Vector((p.x, p.y, 80)), Vector((0, 0, -1)), 120); g = ground(p.x, p.y)[0]
    if h[0] is None or g is None or h[1].z < .8:
        continue
    curb = 4.22 < r < 4.75 and abs(aa) > STEP_HALF and abs(h[0].z - gT) < .25       # raised curb ring
    high = h[0].z > gT + .35                                                          # post caps, wall/pillar tops
    if not (curb or high):
        continue                                                                       # never on the platform treads or steps
    if FX_BVH and FX_BVH.find_nearest(h[0], .12)[0] is not None:
        continue
    t = TPL['moss'][rng.randrange(len(TPL['moss']))]; m = t.data; lin3 = t.matrix_world.to_3x3()
    pts = [lin3 @ m.vertices[j].co for j in range(0, len(m.vertices), max(1, len(m.vertices) // 120))]
    hh = max(q.z for q in pts) - min(q.z for q in pts); fac = rng.uniform(.04, .1) / max(hh, 1e-4)
    lin = Matrix.Rotation(rng.uniform(0, math.tau), 4, 'Z') @ Matrix.Scale(fac, 4) @ lin3.to_4x4()
    pts = [lin @ m.vertices[j].co for j in range(0, len(m.vertices), max(1, len(m.vertices) // 120))]
    cx = sum(q.x for q in pts) / len(pts); cy = sum(q.y for q in pts) / len(pts); zmin = min(q.z for q in pts)
    o = bpy.data.objects.new('V94_ledge_moss_%04d' % LEDGE, m); coll.objects.link(o)
    o.matrix_world = Matrix.Translation(Vector((p.x - cx, p.y - cy, h[0].z - zmin - .01))) @ lin; o['scenic_only'] = True; LEDGE += 1
COUNT['ledge_moss'] = LEDGE
lme.calc_loop_triangles()
QA['sanctuary_dressing'] = dict(enveloping_roots=len(ENV), roots=ENV, ivy_stems=len(STEMS), ivy_leaves_built=NLEAF[0], ivy_leaf_faces_removed_for_rune_clearance=removed,
                                ivy_leaf_triangles=len(lme.loop_triangles), ledge_moss=LEDGE,
                                rule='stone geometry/UV untouched; ivy stems from actual masonry ray hits; leaves within 6 cm of V82_FX meshes removed; moss not within 12 cm of FX; step approach (+-40 deg) kept open for roots')
print('V94_SANCTUARY', json.dumps({k: v for k, v in QA['sanctuary_dressing'].items() if k != 'roots'}))

# ---- contact check on placed instances (lowest-vertex samples vs ground under them)
bpy.context.view_layer.update(); fl = []
for o in sorted(coll.objects, key=lambda o: o.name)[::7]:
    if o.name.startswith(('V94_trail_roots', 'V94_enveloping', 'V94_ivy', 'V94_ledge')):
        continue
    mw = o.matrix_world; vs = [mw @ o.data.vertices[i].co for i in range(0, len(o.data.vertices), max(1, len(o.data.vertices) // 40))]
    low = sorted(vs, key=lambda v: v.z)[:6]; fl += [v.z - ground(v.x, v.y)[0] for v in low if ground(v.x, v.y)[0] is not None]
tri = 0
for o in coll.objects:
    o.data.calc_loop_triangles(); tri += len(o.data.loop_triangles)
QA['floor_added'] = dict(by_kind=COUNT, sedge_clumps=clumps, trail_root_crossings=len(CROSS), instances=len(coll.objects), triangles_instanced=tri,
                         leaves_per_patch=46, leaf_patch_variants=len(PATCHES), sedge_variants=len(TUFTS),
                         sampled_lowest_vertex_offset_m=dict(min=round(min(fl), 3), max=round(max(fl), 3), n=len(fl)),
                         rules='litter allowed on the trail (walkable, flat); sedge >=0.8 m from trail core; roots crest <=0.12 m; nothing on ruin footprint or within 4.6-5 m of the altar centre')
print('V94_FLOOR', json.dumps(QA['floor_added']))

# ================================================================ protection
bpy.context.view_layer.update(); now = snap()
bad = [k for k, v in old.items() if now.get(k) != v]
assert not bad, bad[:8]
QA['protected_objects_exact'] = len(old); assert sha(src) == LOCK

# ================================================================ save / reopen
dest = out / 'v94_forest_floor.blend'; assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()), compress=True); before = snap()
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve())); scene = bpy.context.scene; cam = scene.camera
assert snap() == before
QA['native_sha256'] = sha(dest); QA['native_bytes'] = dest.stat().st_size; QA['reopen_digest_exact'] = True
print('V94_SAVED', QA['native_sha256'])
LUM = np.array([.2126, .7152, .0722], np.float32)
if RENDER:
    QA['luminance'] = {}
    for n in VIEWS:
        set_view(n); b_ = load_px(rd / ('v90_base_%s.png' % n))[..., :3] @ LUM; a_ = load_px(render(rd / ('v94_%s.png' % n)))[..., :3] @ LUM
        QA['luminance'][n] = dict(v90_mean=round(float(b_.mean()), 4), v94_mean=round(float(a_.mean()), 4), v94_p10=round(float(np.percentile(a_, 10)), 4))
    print('V94_LUM', json.dumps(QA['luminance']))

    def tile(p, w=640, h=360):
        a = load_px(p); ys = np.linspace(0, a.shape[0] - 1, h).astype(int); xs = np.linspace(0, a.shape[1] - 1, w).astype(int); t = a[ys][:, xs].copy(); t[..., 3] = 1; return t
    white = np.ones((360, 8, 4), np.float32)
    rows = [np.concatenate([tile(rd / ('v90_base_%s.png' % v)), white, tile(rd / ('v94_%s.png' % v))], 1) for v in reversed(list(VIEWS))]
    sheet = np.concatenate([x for r in rows for x in (r, np.ones((8, r.shape[1], 4), np.float32))][:-1], 0)
    save_px(sheet, out / 'v94_before_after_sheet.png')
    # small review-only set for Studio handoff (existing renders reused, no extra render)
    rv = out / 'review_only'; rv.mkdir(exist_ok=True)
    for n in VIEWS:
        for tag in ('v90_base', 'v94'):
            a = tile(rd / ('%s_%s.png' % (tag, n)), 960, 540); save_px(a, rv / ('%s_%s.png' % (tag, n)))
QA['limits'] = ['Provisional local coordinates; no collision or traversal test.', 'Leaf litter/sedge are procedural (geometry + attribute colour), not photo-scanned.',
                'Game budget: added instances are native-only; no game LOD/GLB for this lane yet.', 'G2 producer self-review only; G4 NOT_RUN.']
QA['outputs'] = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.suffix in ('.blend', '.png')}
QA['secs'] = round(time.time() - T0, 1)
(out / 'v94_qa.json').write_text(json.dumps(QA, indent=1) + '\n')
print('V94_DONE', QA['secs'])

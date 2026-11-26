"""V79 enclosed moss-forest canopy candidate (canopy-first), preserving V78 source.

Director direction 2026-11-26: enclosed dim woodland, near-zero sky from normal cameras.
Usage: blender -b --factory-startup --python native_enclosed_canopy_v79.py -- V78.blend OUT_DIR [--stage canopy|full] [--no-render]
Isolated candidate only: no playable collision, canonical placement or adoption.
"""
import bpy, sys, math, hashlib, json, random, time
from pathlib import Path
from array import array
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
src, out = Path(argv[0]), Path(argv[1])
STAGE = argv[argv.index('--stage') + 1] if '--stage' in argv else 'full'
RENDER = '--no-render' not in argv
out.mkdir(parents=True, exist_ok=True)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


LOCK = '9bba74441e5430551fa97cabfd49641d9338c4e10a9c54c325d4b2d0bf349357'
assert bpy.app.version[:3] == (5, 3, 0), bpy.app.version
assert sha(src) == LOCK, 'V78 source SHA mismatch'
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()))
scene = bpy.context.scene
T0 = time.time()


# ---------------------------------------------------------------- protection snapshot (same scheme as V78)
def digest(data, prop, count, code):
    a = array(code, [0]) * count
    if count:
        data.foreach_get(prop, a)
    return hashlib.sha256(a.tobytes()).hexdigest()


def snap():
    result = {}; cache = {}
    for o in scene.objects:
        if o.type != 'MESH':
            continue
        m = o.data
        if m.name not in cache:
            uv = {a.name: digest(a.data, 'uv', len(a.data) * 2, 'f') for a in m.uv_layers}
            cache[m.name] = (digest(m.vertices, 'co', len(m.vertices) * 3, 'f'), digest(m.loops, 'vertex_index', len(m.loops), 'i'),
                             digest(m.polygons, 'material_index', len(m.polygons), 'i'), uv)
        result[o.name] = (cache[m.name], tuple(tuple(r) for r in o.matrix_world), o.hide_render)
    return result


old = snap()
assert len(old) == 728, len(old)
import numpy as np


def hemisphere_openness(pos, path):
    """Upward equisolid 180-deg fisheye, film-transparent alpha; returns sky fraction inside the image circle."""
    c = scene.camera; keep = (c.location.copy(), c.rotation_euler.copy(), c.data.type, scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage, scene.render.film_transparent)
    c.location = pos; c.rotation_euler = (math.pi, 0, 0); c.data.type = 'PANO'; c.data.panorama_type = 'FISHEYE_EQUISOLID'; c.data.fisheye_fov = math.pi; c.data.fisheye_lens = 10.5
    scene.render.resolution_x = scene.render.resolution_y = 360; scene.render.resolution_percentage = 100; scene.render.film_transparent = True; scene.cycles.samples = 8; scene.cycles.use_denoising = False
    scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGBA'
    vol = scene.world.node_tree.nodes.get('V79_atmosphere'); vm = vol.mute if vol else None
    if vol: vol.mute = True
    scene.render.filepath = str(Path(path).resolve()); bpy.ops.render.render(write_still=True)
    if vol: vol.mute = vm
    im = bpy.data.images.load(str(path)); a = np.array(im.pixels[:], dtype=np.float32).reshape(360, 360, 4)[..., 3]; bpy.data.images.remove(im)
    yy, xx = np.mgrid[0:360, 0:360]; inside = ((xx - 179.5) ** 2 + (yy - 179.5) ** 2) < 178 ** 2
    c.location, c.rotation_euler, c.data.type, scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage, scene.render.film_transparent = keep
    return round(float((1 - a)[inside].mean()), 4)


HEMI = {}
if RENDER and STAGE == 'full':
    (out / 'renders').mkdir(exist_ok=True)
    HEMI['v78_eye'] = hemisphere_openness(Vector((78.17052459716797, -80.77701568603516, 29.82533073425293)), out / 'renders' / 'diag_hemi_v78_eye_alpha.png')
    HEMI['v78_altar'] = hemisphere_openness(Vector((93.94316101074219, -93.07432556152344, 30.988130569458008 + 1.0)), out / 'renders' / 'diag_hemi_v78_altar_alpha.png')
    # V78 baseline with identical camera/lens/resolution/samples/exposure, before any V79 change
    _eye = Vector((78.17052459716797, -80.77701568603516, 29.82533073425293)); _aim = Vector((93.94316101074219, -93.07432556152344, 30.988130569458008))
    _c = scene.camera; scene.render.resolution_percentage = 50 if '--preview' in argv else 100; scene.cycles.samples = 12
    for _n, _p in (('matched', _eye), ('lateral', _eye + Vector((.6148655745981655, .788631932636555, 0)) * 8)):
        _c.location = _p; _c.rotation_euler = (_aim - _p).to_track_quat('-Z', 'Y').to_euler(); _c.data.lens = 22
        scene.render.filepath = str((out / ('v78_baseline_%s.png' % _n)).resolve()); bpy.ops.render.render(write_still=True)

# ---------------------------------------------------------------- measured anchors (from V57/V58/V71/V78 sources)
EYE = Vector((78.17052459716797, -80.77701568603516, 29.82533073425293))
ALTAR = Vector((93.94316101074219, -93.07432556152344, 30.988130569458008))
ROUTE = (Vector((-205, 140)), Vector((90, -90)))          # V57/V58/V71 provisional route, 5 m half clearance
RESERVED = [((67.536852, -72.486359), 11), ((45.876293, -75.886764), 8), ((49.408698, -58.352544), 10), ((93.943160, -93.074328), 7)]
RAYS = [((65.4663, -80.2138), (45.876293, -75.886764), 4), ((65.4663, -80.2138), (93.943160, -93.074328), 3)]
FWD = (ALTAR - EYE).to_2d().normalized(); PERP = Vector((-FWD.y, FWD.x))
CENTER = (EYE.to_2d() + ALTAR.to_2d()) / 2
SIDE = Vector((.6148655745981655, .788631932636555))
CAM_ZONES = [EYE.to_2d(), EYE.to_2d() + SIDE * 8, EYE.to_2d() - FWD * 12, EYE.to_2d() + FWD * 10, ALTAR.to_2d() + PERP * 14]

terrain = bpy.data.objects['A3 provisional reconstructed terrain']
ext = bpy.data.objects['V58_SCENIC_ONLY_terrain_extension']
far = bpy.data.objects['V77_SCENIC_ONLY_FAR_RELIEF']


def world_bvh(objs):
    verts = []; polys = []
    for o in objs:
        mw = o.matrix_world; base = len(verts)
        verts += [mw @ v.co for v in o.data.vertices]
        polys += [[base + i for i in p.vertices] for p in o.data.polygons]
    return BVHTree.FromPolygons(verts, polys)


GROUND = world_bvh([terrain, ext, far])


def ground(x, y):
    hit = GROUND.ray_cast(Vector((x, y, 300)), Vector((0, 0, -1)), 400)
    return (hit[0].z, hit[1].z) if hit[0] else None


def seg_dist(p, a, b):
    ab = b - a; t = max(0, min(1, (p - a).dot(ab) / ab.length_squared)); return (a + ab * t - p).length


def interface_gap(p):
    """Clearance (m) from protected route/reserved/sight interfaces; positive = outside."""
    g = [seg_dist(p, *ROUTE) - 5]
    g += [(p - Vector(c)).length - r for c, r in RESERVED]
    g += [seg_dist(p, Vector(a), Vector(b)) - r for a, b, r in RAYS]
    g += [(p - c).length - 3.5 for c in CAM_ZONES]
    return min(g)


# existing trunk footprints (protected trees) for spacing
existing_trunks = []
for o in scene.objects:
    if o.type == 'MESH' and o.data.name in ('island_trees_01_blockout_cleaned', 'eco_tree_forest_tall_a_LOD1_mesh', 'eco_tree_deciduous_a_LOD1_mesh'):
        existing_trunks.append((o.matrix_world.translation.to_2d(), 1.2))

# ---------------------------------------------------------------- source tree families (existing in-scene, CC0 / prior-recorded)
ISL = bpy.data.meshes['island_trees_01_blockout_cleaned']      # Poly Haven island_tree_01 (CC0), via V55 intake
TALL = bpy.data.meshes['eco_tree_forest_tall_a_LOD1_mesh']
DEC = bpy.data.meshes['eco_tree_deciduous_a_LOD1_mesh']


def trunk_profile(mesh, bark_index=0, zfrac=.06):
    zs = [v.co.z for v in mesh.vertices]; z0, z1 = min(zs), max(zs)
    pts = [v.co for p in mesh.polygons if p.material_index == bark_index for v in (mesh.vertices[i] for i in p.vertices) if v.co.z < z0 + (z1 - z0) * zfrac]
    cx = sum(p.x for p in pts) / len(pts); cy = sum(p.y for p in pts) / len(pts)
    r = max(math.hypot(p.x - cx, p.y - cy) for p in pts)
    stem = [v.co for p in mesh.polygons if p.material_index == bark_index for v in (mesh.vertices[i] for i in p.vertices) if z0 + (z1 - z0) * .14 < v.co.z < z0 + (z1 - z0) * .2]
    rs = 0.
    if len(stem) > 8:
        sx = sum(p.x for p in stem) / len(stem); sy = sum(p.y for p in stem) / len(stem)
        rs = sorted(math.hypot(p.x - sx, p.y - sy) for p in stem)[int(len(stem) * .9)]
    rs = max(rs, r * .45)
    return dict(c=Vector((cx, cy)), r=r, stem=rs, h=z1 - z0, z0=z0, roots=[Vector((p.x, p.y, p.z)) for p in pts[::max(1, len(pts) // 48)]])


PROF = {ISL.name: trunk_profile(ISL), TALL.name: trunk_profile(TALL), DEC.name: trunk_profile(DEC)}
for k, v in PROF.items():
    print('V79_TRUNK', k, 'flare=%.2f stem=%.2f h=%.2f roots=%d' % (v['r'], v['stem'], v['h'], len(v['roots'])))
TRI = {}
for m in (ISL, TALL, DEC):
    m.calc_loop_triangles(); TRI[m.name] = len(m.loop_triangles)

coll = bpy.data.collections.new('V79_ENCLOSED_CANOPY'); scene.collection.children.link(coll)
placed = []
FAIL = {}


def fail(k):
    FAIL[k] = FAIL.get(k, 0) + 1
    return None


def try_place(kind, mesh, x, y, height, yaw, lean=0.0, lean_dir=0.0, tag='', clearance=.6, min_space=1.2):
    pr = PROF[mesh.name]; s = height / pr['h']; tr = pr['stem'] * s; fr = pr['r'] * s
    p = Vector((x, y))
    if interface_gap(p) < fr + clearance:
        return fail('interface')
    for q, r in existing_trunks + [(Vector((d['x'], d['y'])), d['trunk_r']) for d in placed]:
        if (p - q).length < tr + r + min_space:
            return fail('spacing')
    rot = Matrix.Rotation(lean, 4, Vector((math.cos(lean_dir + math.pi / 2), math.sin(lean_dir + math.pi / 2), 0))) @ Matrix.Rotation(yaw, 4, 'Z')
    lin = rot @ Matrix.Scale(s, 4)
    centre = lin @ Vector((pr['c'].x, pr['c'].y, pr['z0']))
    samples = []
    for rp in pr['roots']:
        w = lin @ rp
        g = ground(x + w.x - centre.x, y + w.y - centre.y)
        if g is None:
            return fail('no_ground')
        if g[1] < .55:
            return fail('slope')
        samples.append((w.z, g[0]))
    # sink so the highest-floating root sample touches ground; burial bounded
    zz = max(gz - wz for wz, gz in samples) - .05 * s
    res = [wz + zz - gz for wz, gz in samples]
    if min(res) < -1.2 * max(1, s / 3):
        return fail('bury')
    o = bpy.data.objects.new('V79_%s_%03d' % (kind, len(placed)), mesh); coll.objects.link(o)
    o.matrix_world = Matrix.Translation(Vector((x - centre.x, y - centre.y, zz))) @ lin
    o['scenic_only'] = True; o['v79_layer'] = tag
    d = dict(name=o.name, kind=kind, layer=tag, x=round(x, 3), y=round(y, 3), height=round(height, 2), scale=round(s, 3), trunk_r=round(tr, 2),
             lean_deg=round(math.degrees(lean), 1), root_float_max=round(max(res), 3), root_bury_min=round(min(res), 3), triangles=TRI[mesh.name],
             flare_r=round(fr, 2), interface_gap=round(interface_gap(p) - fr, 2))
    placed.append(d)
    return d


rng = random.Random(20261126079)


def place_near(kind, mesh, x, y, hrange, lean=0., lean_dir=None, tag='', tries=40, jitter=2.5, **kw):
    for i in range(tries):
        jx = x + (rng.uniform(-jitter, jitter) if i else 0); jy = y + (rng.uniform(-jitter, jitter) if i else 0)
        ld = lean_dir if lean_dir is not None else math.atan2(CENTER.y - jy, CENTER.x - jx)
        d = try_place(kind, mesh, jx, jy, rng.uniform(*hrange), rng.uniform(0, math.tau), lean, ld, tag, **kw)
        if d:
            return d
        jitter = min(jitter * 1.08, 3.5)
    return None


# ---- A. canopy key trees: art-directed overhang across the route/sight corridor and over the altar clearing
key_specs = [
    # (along FWD from eye, across PERP, height range, lean deg) -- trunks flank the corridor, crowns lean in over it
    (1.0, 8.5, (22, 25), 9), (5.5, -8.0, (21, 24), 10), (-4.0, -8.5, (20, 23), 7), (-5.0, 8.0, (21, 24), 8),
    (11.0, 9.0, (22, 26), 11), (12.0, -9.5, (21, 25), 10), (-11.0, 1.5, (23, 26), 5),
]
for a, c, hr, ld in key_specs:
    q = EYE.to_2d() + FWD * a + PERP * c
    d = None
    for da in (0, 2.5, -2.5, 5):
        q = EYE.to_2d() + FWD * (a + da) + PERP * c
        d = place_near('oak_key', ISL, q.x, q.y, hr, math.radians(ld), math.atan2(-c * PERP.y, -c * PERP.x) if c else None, 'A_key_overhang', tries=15, jitter=1.5)
        if d:
            break
    print('V79_KEY', a, c, d and (d['name'], d['x'], d['y'], d['interface_gap']))
# ring round the altar clearing (narrows the open stage ~35-40%)
ring_targets = [(70, 15.5), (120, 15), (160, 17), (185, 15.5), (210, 18), (250, 15), (300, 16.5), (180, 25), (160, 28), (205, 29)]
for ang, dist in ring_targets:
    t = math.radians(ang); dirv = Vector((-FWD.x, -FWD.y)); dirv.rotate(Matrix.Rotation(t, 2))
    d = None
    for dd in (dist, dist + 2.5, dist - 1.5, dist + 5):
        q = ALTAR.to_2d() + dirv * dd
        d = place_near('oak_ring', ISL, q.x, q.y, (20, 25), math.radians(rng.uniform(6, 12)), math.atan2(ALTAR.y - q.y, ALTAR.x - q.x), 'A_altar_ring', tries=15, jitter=1.5)
        if d:
            break
    print('V79_RING', ang, dist, d and (d['name'], d['x'], d['y'], round((Vector((d['x'], d['y'])) - ALTAR.to_2d()).length, 1)))

# ---- B. midground clustered groves (natural density variance, no grid)
centres = []
for i in range(4000):
    if len(centres) >= 26:
        break
    r = math.sqrt(rng.uniform(20 ** 2, 52 ** 2)); t = rng.uniform(0, math.tau)
    q = CENTER + Vector((math.cos(t), math.sin(t))) * r
    if all((q - c).length > 13 for c in centres):
        centres.append(q)
for c in centres:
    n = rng.choices([2, 3, 4, 5], [2, 4, 3, 1])[0]
    for j in range(n):
        q = c + Vector((rng.gauss(0, 4.5), rng.gauss(0, 4.5)))
        fam = rng.choices([('oak_mid', ISL, (16, 24)), ('tall_mid', TALL, (17, 23)), ('dec_mid', DEC, (13, 18))], [5, 3, 2])[0]
        place_near(fam[0], fam[1], q.x, q.y, fam[2], math.radians(rng.uniform(0, 8)), rng.uniform(0, math.tau), 'B_mid_grove', tries=8, jitter=2)

# ---- C. far enclosure ring, cheaper LOD meshes, overlapping crowns to stop distant sightlines
for i in range(2600):
    r = math.sqrt(rng.uniform(50 ** 2, 92 ** 2)); t = rng.uniform(0, math.tau)
    q = CENTER + Vector((math.cos(t), math.sin(t))) * r
    fam = rng.choices([('oak_far', ISL, (18, 25)), ('tall_far', TALL, (19, 26)), ('dec_far', DEC, (14, 19))], [2, 5, 3])[0]
    try_place(fam[0], fam[1], q.x, q.y, rng.uniform(*fam[2]), rng.uniform(0, math.tau), math.radians(rng.uniform(0, 7)), rng.uniform(0, math.tau), 'C_far_enclosure', min_space=3.5)
    if sum(1 for d in placed if d['layer'] == 'C_far_enclosure') >= 120:
        break

def free_area(trunks, origin, cap=40.0, n=144):
    acc = 0.
    for i in range(n):
        t = math.tau * i / n; dvec = Vector((math.cos(t), math.sin(t))); best = cap
        for q, r in trunks:
            w = q - origin; along = w.dot(dvec)
            if 0 < along < best and abs(w.x * dvec.y - w.y * dvec.x) < r + .6:
                best = along
        acc += best * best
    return .5 * acc * math.tau / n


a78 = free_area(existing_trunks, ALTAR.to_2d()); a79 = free_area(existing_trunks + [(Vector((d['x'], d['y'])), d['flare_r']) for d in placed], ALTAR.to_2d())
ALTAR_OPEN = dict(method='trunk-free star area from altar, 144 rays, cap 40 m, trunk radius +0.6 m', v78_m2=round(a78, 1), v79_m2=round(a79, 1), reduction=round(1 - a79 / a78, 3))
print('V79_ALTAR_OPEN', ALTAR_OPEN)
layers = {}
for d in placed:
    L = layers.setdefault(d['layer'], dict(count=0, triangles=0)); L['count'] += 1; L['triangles'] += d['triangles']
print('V79_FAIL', FAIL)
print('V79_CANOPY', json.dumps(layers), 'secs', round(time.time() - T0, 1))
QA = dict(status='V79_ENCLOSED_CANOPY_CANDIDATE', source_sha256=LOCK, blender=bpy.app.version_string, stage=STAGE, canopy_layers=layers, altar_openness=ALTAR_OPEN, canopy=placed, placement_rejections=FAIL)


# ================================================================ D. layered forest-floor material (photo-derived CC0 maps already packed)
def img(name):
    return bpy.data.images[name]


def build_floor_material():
    m = bpy.data.materials.new('V79_forest_floor_layered'); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links; N.clear()
    outn = N.new('ShaderNodeOutputMaterial'); bsdf = N.new('ShaderNodeBsdfPrincipled'); L.new(bsdf.outputs[0], outn.inputs[0])
    geo = N.new('ShaderNodeNewGeometry')

    def coords(scale, angle):
        r = N.new('ShaderNodeVectorRotate'); r.rotation_type = 'Z_AXIS'; r.inputs['Angle'].default_value = math.radians(angle)
        L.new(geo.outputs['Position'], r.inputs['Vector'])
        s = N.new('ShaderNodeVectorMath'); s.operation = 'SCALE'; s.inputs['Scale'].default_value = 1.0 / scale
        L.new(r.outputs[0], s.inputs[0]); return s.outputs[0]

    def noise(scale, detail=4, rough=.6, w=None):
        n = N.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = detail; n.inputs['Roughness'].default_value = rough
        L.new(geo.outputs['Position'], n.inputs['Vector']); return n.outputs['Fac']

    def ramp(fac, a, b):
        r = N.new('ShaderNodeMapRange'); r.inputs['From Min'].default_value = a; r.inputs['From Max'].default_value = b; L.new(fac, r.inputs['Value']); return r.outputs[0]

    breakup = ramp(noise(.11, 3), .38, .62)

    def tex(name, vec, non_color=False):
        t = N.new('ShaderNodeTexImage'); t.image = img(name); t.interpolation = 'Linear'
        if non_color:
            t.image.colorspace_settings.name = 'Non-Color'
        L.new(vec, t.inputs['Vector']); return t.outputs['Color']

    def mixc(f, a, b):
        x = N.new('ShaderNodeMix'); x.data_type = 'RGBA'; x.clamp_factor = True
        if isinstance(f, float):
            x.inputs['Factor'].default_value = f
        else:
            L.new(f, x.inputs['Factor'])
        L.new(a, x.inputs['A']); L.new(b, x.inputs['B']); return x.outputs['Result']

    def layer(prefix_d, prefix_n, prefix_r, scale, r_channel):
        c1, c2 = coords(scale, 0), coords(scale * .73, 37)
        col = mixc(breakup, tex(prefix_d, c1), tex(prefix_d, c2))
        nor = mixc(breakup, tex(prefix_n, c1, True), tex(prefix_n, c2, True))
        rr = mixc(breakup, tex(prefix_r, c1, True), tex(prefix_r, c2, True))
        sep = N.new('ShaderNodeSeparateColor'); L.new(rr, sep.inputs[0])
        return col, nor, sep.outputs[r_channel]

    litter = layer('forest_leaves_02_diffuse_2k.jpg', 'forest_leaves_02_nor_gl_2k.jpg', 'forest_leaves_02_rough_2k.jpg', 2.4, 'Red')
    soil = layer('forrest_ground_01_diff_2k.jpg', 'forrest_ground_01_nor_gl_2k.jpg', 'forrest_ground_01_arm_2k.jpg', 3.2, 'Green')
    moss = layer('moss_tile_basecolor', 'moss_tile_normal', 'moss_tile_orm', 1.3, 'Green')
    # tone: damp, shaded woodland (no baked light; only albedo calibration)
    def hsv(c, h, s, v):
        x = N.new('ShaderNodeHueSaturation'); x.inputs['Hue'].default_value = h; x.inputs['Saturation'].default_value = s; x.inputs['Value'].default_value = v
        L.new(c, x.inputs['Color']); return x.outputs[0]
    litter_c = hsv(litter[0], .5, .85, .78); soil_c = hsv(soil[0], .5, .78, .48); moss_c = hsv(moss[0], .5, 1.05, .8)
    # distance to protected route segment (xy) -> trodden path; edges get moss carpets
    A, B = ROUTE
    sep = N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Position'], sep.inputs[0])
    cmb = N.new('ShaderNodeCombineXYZ'); L.new(sep.outputs[0], cmb.inputs[0]); L.new(sep.outputs[1], cmb.inputs[1])
    pa = N.new('ShaderNodeVectorMath'); pa.operation = 'SUBTRACT'; L.new(cmb.outputs[0], pa.inputs[0]); pa.inputs[1].default_value = (A.x, A.y, 0)
    ab = (B - A); proj = N.new('ShaderNodeVectorMath'); proj.operation = 'DOT_PRODUCT'; L.new(pa.outputs[0], proj.inputs[0]); proj.inputs[1].default_value = (ab.x / ab.length_squared, ab.y / ab.length_squared, 0)
    cl = N.new('ShaderNodeClamp'); L.new(proj.outputs['Value'], cl.inputs[0])
    sc = N.new('ShaderNodeVectorMath'); sc.operation = 'SCALE'; sc.inputs[0].default_value = (ab.x, ab.y, 0); L.new(cl.outputs[0], sc.inputs['Scale'])
    dv = N.new('ShaderNodeVectorMath'); dv.operation = 'DISTANCE'; L.new(pa.outputs[0], dv.inputs[0]); L.new(sc.outputs[0], dv.inputs[1])
    alt = N.new('ShaderNodeVectorMath'); alt.operation = 'DISTANCE'; L.new(cmb.outputs[0], alt.inputs[0]); alt.inputs[1].default_value = (ALTAR.x, ALTAR.y, 0)
    altd = N.new('ShaderNodeMath'); altd.operation = 'SUBTRACT'; L.new(alt.outputs['Value'], altd.inputs[0]); altd.inputs[1].default_value = 2.5
    dmin = N.new('ShaderNodeMath'); dmin.operation = 'MINIMUM'; L.new(dv.outputs['Value'], dmin.inputs[0]); L.new(altd.outputs[0], dmin.inputs[1])
    wob = N.new('ShaderNodeMath'); wob.operation = 'MULTIPLY_ADD'; L.new(noise(.35, 3), wob.inputs[0]); wob.inputs[1].default_value = 2.4; L.new(dmin.outputs[0], wob.inputs[2])
    path = N.new('ShaderNodeMapRange'); path.inputs['From Min'].default_value = 4.2; path.inputs['From Max'].default_value = 2.2; L.new(wob.outputs[0], path.inputs['Value'])
    edge = N.new('ShaderNodeMapRange'); edge.inputs['From Min'].default_value = 3.6; edge.inputs['From Max'].default_value = 6.5; L.new(wob.outputs[0], edge.inputs['Value'])
    mraw = N.new('ShaderNodeMath'); mraw.operation = 'MULTIPLY_ADD'; L.new(edge.outputs[0], mraw.inputs[0]); mraw.inputs[1].default_value = .09; L.new(noise(.075, 6, .62), mraw.inputs[2])
    moss_mask = ramp(mraw.outputs[0], .5, .58)                    # moss carpets, denser off-path
    damp_mask = ramp(noise(.16, 5, .55), .55, .66)               # wet dark soil hollows
    dm = N.new('ShaderNodeMath'); dm.operation = 'MAXIMUM'; L.new(damp_mask, dm.inputs[0])
    pth = N.new('ShaderNodeMath'); pth.operation = 'MULTIPLY'; L.new(path.outputs[0], pth.inputs[0]); pth.inputs[1].default_value = .55; L.new(pth.outputs[0], dm.inputs[1])
    damp_mask = dm.outputs[0]
    mm = N.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; L.new(moss_mask, mm.inputs[0])
    inv = N.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1; L.new(path.outputs[0], inv.inputs[1]); L.new(inv.outputs[0], mm.inputs[1])
    moss_mask = mm.outputs[0]
    col = mixc(damp_mask, litter_c, soil_c); col = mixc(moss_mask, col, moss_c)
    nor = mixc(damp_mask, litter[1], soil[1]); nor = mixc(moss_mask, nor, moss[1])
    rough = N.new('ShaderNodeMix'); rough.data_type = 'FLOAT'; L.new(damp_mask, rough.inputs['Factor']); L.new(litter[2], rough.inputs['A'])
    wet = N.new('ShaderNodeMath'); wet.operation = 'MULTIPLY'; wet.inputs[1].default_value = .62; L.new(soil[2], wet.inputs[0]); L.new(wet.outputs[0], rough.inputs['B'])
    rough2 = N.new('ShaderNodeMix'); rough2.data_type = 'FLOAT'; L.new(moss_mask, rough2.inputs['Factor']); L.new(rough.outputs['Result'], rough2.inputs['A']); rough2.inputs['B'].default_value = .9
    nm = N.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 1.2; L.new(nor, nm.inputs['Color'])
    bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .25; bump.inputs['Distance'].default_value = .05
    L.new(noise(2.7, 8, .7), bump.inputs['Height']); L.new(nm.outputs[0], bump.inputs['Normal'])
    L.new(col, bsdf.inputs['Base Color']); L.new(rough2.outputs['Result'], bsdf.inputs['Roughness']); L.new(bump.outputs[0], bsdf.inputs['Normal'])
    bsdf.inputs['Specular IOR Level'].default_value = .35
    return m


def tone_leafcards():
    changed = []
    for name in ('GM_eco_leafcard_beech', 'GM_eco_leafcard_oak', 'GM_eco_leafcard_beech.001'):
        m = bpy.data.materials.get(name)
        if not m:
            continue
        nt = m.node_tree; b = [x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED'][0]
        src_sock = b.inputs['Base Color'].links[0].from_socket
        h = nt.nodes.new('ShaderNodeHueSaturation'); h.name = 'V79_shade_tone'
        h.inputs['Hue'].default_value = .505; h.inputs['Saturation'].default_value = .62; h.inputs['Value'].default_value = .5
        nt.links.new(src_sock, h.inputs['Color']); nt.links.new(h.outputs[0], b.inputs['Base Color'])
        changed.append(name)
    return changed


if STAGE == 'full':
    floor = build_floor_material()
    for o in (terrain, ext):
        o.data.materials[0] = floor
    QA['material_changes'] = dict(floor='V79_forest_floor_layered on terrain+extension (forest_leaves_02, forrest_ground_01, moss_tile)', leafcards_toned=tone_leafcards())

# ================================================================ C. understory colonies (tree-base / corridor-edge, raycast grounded)
FAM = {'fern': ['V18_0_', 'V18_1_', 'V18_2_', 'V18_3_'], 'moss': ['V21_M_'], 'shrub': ['V18_S_'], 'rock': ['V21_R_'], 'stump': ['V21_U_']}
templates = {}
for k, prefixes in FAM.items():
    seen = {}
    for o in sorted(scene.objects, key=lambda x: x.name):
        if o.type == 'MESH' and any(o.name.startswith(p) for p in prefixes) and o.data.name not in seen:
            seen[o.data.name] = o
    templates[k] = list(seen.values())
HT = {'fern': (.45, 1.05), 'moss': (.1, .26), 'shrub': (.75, 1.5), 'rock': (.35, 1.1), 'stump': (.45, .8)}
under = []; utri = 0
ucoll = bpy.data.collections.new('V79_UNDERSTORY_COLONIES'); scene.collection.children.link(ucoll)
trunks_all = existing_trunks + [(Vector((d['x'], d['y'])), d['trunk_r']) for d in placed]


def place_item(kind, x, y, near_trunk=True):
    global utri
    t = rng.choice(templates[kind]); m = t.data
    if m.name not in TRI:
        m.calc_loop_triangles(); TRI[m.name] = len(m.loop_triangles)
    lin = t.matrix_world.to_3x3().to_4x4()
    pts = [lin @ m.vertices[i].co for i in range(0, len(m.vertices), max(1, len(m.vertices) // 400))]
    hgt = max(p.z for p in pts) - min(p.z for p in pts)
    if hgt < 1e-4:
        return None
    fac = rng.uniform(*HT[kind]) / hgt
    if kind == 'moss':
        fac *= rng.uniform(1.4, 2.6)
    lin = Matrix.Rotation(rng.uniform(0, math.tau), 4, 'Z') @ Matrix.Scale(fac, 4) @ lin
    pts = [lin @ m.vertices[i].co for i in range(0, len(m.vertices), max(1, len(m.vertices) // 400))]
    mn = Vector([min(p[j] for p in pts) for j in range(3)]); mx = Vector([max(p[j] for p in pts) for j in range(3)])
    cx, cy = (mn.x + mx.x) / 2, (mn.y + mx.y) / 2
    rad = max(math.hypot(p.x - cx, p.y - cy) for p in pts)
    pp = Vector((x, y))
    if interface_gap(pp) < rad + .25:
        return None
    if any((pp - q).length < r + rad * .35 for q, r in trunks_all):
        return None
    if any((pp - Vector((u['x'], u['y']))).length < (rad + u['radius']) * .55 for u in under[-60:]):
        return None
    roots = [p for p in pts if p.z <= mn.z + max(.03, (mx.z - mn.z) * .1)]
    hits = []
    for p in roots[::max(1, len(roots) // 24)]:
        g = ground(x + p.x - cx, y + p.y - cy)
        if g is None:
            return None
        hits.append((p.z, g[0]))
    zz = max(gz - pz for pz, gz in hits) - (.02 if kind != 'rock' else (mx.z - mn.z) * .25)
    res = [pz + zz - gz for pz, gz in hits]
    if max(res) > .2:
        return None
    o = bpy.data.objects.new('V79_u_%s_%04d' % (kind, len(under)), m); ucoll.objects.link(o)
    o.matrix_world = Matrix.Translation(Vector((x - cx, y - cy, zz))) @ lin
    o['scenic_only'] = True
    under.append(dict(name=o.name, kind=kind, source=t.name, x=round(x, 3), y=round(y, 3), radius=round(rad, 3), root_float_max=round(max(res), 3), root_bury_min=round(min(res), 3), triangles=TRI[m.name]))
    utri += TRI[m.name]
    return o


if STAGE == 'full':
    # 1) colonies hugging tree bases (new + existing trunks within 60 m of the clearing)
    for q, r in trunks_all:
        dist = (q - CENTER).length
        if dist > 60:
            continue
        n = int(rng.uniform(6, 13) * (1.5 if dist < 30 else 1.0))
        a0 = rng.uniform(0, math.tau)
        for i in range(n * 3):
            if n <= 0:
                break
            ang = a0 + rng.gauss(0, 1.1)                       # one-sided colony, not a ring
            kind = rng.choices(['moss', 'fern', 'shrub', 'rock', 'stump'], [5, 6, 1.5, 1, .3 if dist < 35 else 0])[0]
            rr = r + (rng.uniform(.15, 1.4) if kind == 'moss' else rng.uniform(.6, 4.5))
            if place_item(kind, q.x + math.cos(ang) * rr, q.y + math.sin(ang) * rr):
                n -= 1
    # 2) corridor-edge drifts: clustered ferns/moss just outside the protected route and altar
    for i in range(1400):
        tpar = rng.uniform(-38, 4)
        side = rng.choice((-1, 1))
        off = 5.0 + abs(rng.gauss(0, 3.2)) + .4
        q = EYE.to_2d() + FWD * tpar + PERP * side * off
        if (q - ALTAR.to_2d()).length < 7.6:
            continue
        patch = math.sin(q.x * .37 + q.y * .21) + math.cos(q.y * .29 - q.x * .17)
        if patch < -.35:
            continue
        place_item(rng.choices(['fern', 'moss', 'shrub', 'rock'], [6, 5, 1, .6])[0], q.x, q.y, False)
    QA['understory'] = dict(count=len(under), triangles=utri, by_kind={k: sum(1 for u in under if u['kind'] == k) for k in FAM},
                            root_float_max=max(u['root_float_max'] for u in under), root_bury_min=min(u['root_bury_min'] for u in under))
    print('V79_UNDER', json.dumps(QA['understory']))

# ================================================================ protection check (all 728 V78 objects: geometry/UV/transform exact)
bpy.context.view_layer.update()
now = snap()
changed = [k for k, v in old.items() if now.get(k) != v]
assert not changed, changed[:10]
QA['protected_objects_exact'] = len(old)
assert sha(src) == LOCK
if STAGE != 'full':
    print('V79_STAGE_ONLY', STAGE); raise SystemExit(0)

# ================================================================ review cameras (provisional local coordinates)
PREVIEW = '--preview' in argv
RES = 50 if PREVIEW else 100
SPP_A = 12                                    # identical to V78 scene samples
SPP_B = 12 if PREVIEW else 64
cam = scene.camera
up = Vector((0, 0, 1))


def eye_at(p2, h=1.7):
    g = ground(p2.x, p2.y); return Vector((p2.x, p2.y, (g[0] if g else EYE.z - 1.7) + h))


VIEWS = {
    'matched': (EYE, ALTAR, 22, 'persp'),
    'lateral': (EYE + SIDE.to_3d() * 8, ALTAR, 22, 'persp'),
    'side': (eye_at(ALTAR.to_2d() + PERP * 14), ALTAR, 24, 'persp'),
    'player_eye': (eye_at(EYE.to_2d() - FWD * 12), eye_at(EYE.to_2d() + FWD * 14, 1.5), 28, 'persp'),
    'altar_approach': (eye_at(EYE.to_2d() + FWD * 10), ALTAR + Vector((0, 0, -.4)), 28, 'persp'),
    'look_up': (EYE, EYE + (FWD.to_3d() * .45 + up * .9), 16, 'persp'),
    'oblique_aerial': (CENTER.to_3d() + Vector((-48, 40, 0)) + Vector((0, 0, EYE.z + 52)), CENTER.to_3d() + Vector((0, 0, EYE.z - 2)), 26, 'persp'),
}
ORDINARY = ['matched', 'lateral', 'side', 'player_eye', 'altar_approach']
# floor close-up at the densest near tree-base colony
def _fc_score(u):
    w = Vector((u['x'], u['y'])) - EYE.to_2d(); along = w.dot(FWD)
    return abs(along - 9) + abs(abs(w.dot(PERP)) - 6.5) + (0 if u['kind'] == 'fern' else 4) + (0 if w.dot(PERP) < 0 else 2)   # lit right-hand corridor edge
near = sorted(under, key=_fc_score)
fc = Vector((near[0]['x'], near[0]['y'])) if near else EYE.to_2d() + PERP * 7
fdir = (fc - EYE.to_2d()).normalized()
VIEWS['floor_close'] = (eye_at(fc - fdir * 2.2, .75), eye_at(fc + fdir * .8, 0.1), 30, 'persp')


def set_view(name):
    p, t, lens, kind = VIEWS[name]
    cam.data.type = 'PERSP'; cam.location = p; cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = lens
    cam.data.clip_start = .05; cam.data.clip_end = 600


def render(path, spp, transparent=False, pct=RES):
    scene.render.resolution_percentage = pct; scene.cycles.samples = spp; scene.cycles.use_denoising = not transparent
    scene.render.film_transparent = transparent
    scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGBA' if transparent else 'RGB'
    scene.render.filepath = str(Path(path).resolve()); bpy.ops.render.render(write_still=True)
    return Path(path)


import numpy as np


def load_px(path):
    im = bpy.data.images.load(str(path)); a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)
    bpy.data.images.remove(im); return a


def sky_stats(path):
    a = load_px(path)[..., 3]; s = 1 - a; h = s.shape[0]
    return dict(sky_mean=round(float(s.mean()), 4), sky_hard=round(float((a < .5).mean()), 4), sky_top_third=round(float(s[2 * h // 3:].mean()), 4))


def save_px(arr, path):
    h, w = arr.shape[:2]; im = bpy.data.images.new(Path(path).stem, w, h, alpha=True)
    im.pixels.foreach_set(np.ascontiguousarray(arr, dtype=np.float32).ravel()); im.filepath_raw = str(path); im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)


V78_LIGHT = dict(world=tuple(scene.world.node_tree.nodes['Background'].inputs['Color'].default_value), world_strength=scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value,
                 lights={o.name: o.data.energy for o in scene.objects if o.type == 'LIGHT'})


def apply_v79_lighting():
    bg = scene.world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (.42, .52, .47, 1); bg.inputs['Strength'].default_value = .75
    sun = bpy.data.objects['Sun']; sun.data.energy = 7.0; sun.data.angle = math.radians(1.0); sun.data.color = (1, .9, .74)
    for nme, f in (('V57_cool_ambient', .7), ('V57_warm_canopy_opening', .85), ('V58_scenic_cool_fill', .55), ('V58_scenic_warm_key', .7)):
        o = bpy.data.objects.get(nme)
        if o:
            o.data.energy *= f
    # light, homogeneous atmospheric scatter for depth falloff and occasional shafts (not a blanket fog)
    nt = scene.world.node_tree
    vol = nt.nodes.new('ShaderNodeVolumePrincipled'); vol.name = 'V79_atmosphere'
    vol.inputs['Density'].default_value = .0012; vol.inputs['Color'].default_value = (.82, .82, .7, 1); vol.inputs['Anisotropy'].default_value = .5
    nt.links.new(vol.outputs[0], [n for n in nt.nodes if n.type == 'OUTPUT_WORLD'][0].inputs['Volume'])
    scene.view_settings.exposure = .45
    return dict(world_color=(.42, .52, .47), world_strength=.75, sun_energy=7.0, sun_angle_deg=1.0, fills_scaled={'V57_cool_ambient': .7, 'V57_warm_canopy_opening': .85, 'V58_scenic_cool_fill': .55, 'V58_scenic_warm_key': .7},
                atmosphere_density=.0012, exposure=.45, calibration='L2: matched mean linear luminance 0.143 vs 0.156 V78-light state at 50%/12spp; 10th pct 0.022')


def set_atmosphere(on):
    nt = scene.world.node_tree; v = nt.nodes.get('V79_atmosphere')
    if v:
        v.mute = not on


renders = {}
r_dir = out / 'renders'; r_dir.mkdir(exist_ok=True)
QA['metrics_scene'] = dict(canopy_instances=len(placed), understory_instances=len(under),
                           canopy_triangles_instanced=sum(d['triangles'] for d in placed), understory_triangles_instanced=utri,
                           unique_meshes_added=len({o.data.name for o in list(coll.objects) + list(ucoll.objects)}),
                           materials_total=len(bpy.data.materials), images_total=len(bpy.data.images),
                           image_bytes_uncompressed=int(sum(i.size[0] * i.size[1] * 4 for i in bpy.data.images)))

# ---- A. comparison with V78 lighting/exposure (geometry + materials changed only)
if RENDER:
    for name in ('matched', 'lateral'):
        set_view(name); renders['v79A_' + name] = render(r_dir / ('v79_A_v78light_%s.png' % name), SPP_A)
    # sky occlusion masks (geometry only, alpha; no colour substitution)
    QA['sky_exposure'] = {}
    for name in ORDINARY + ['look_up']:
        set_view(name); pth = render(r_dir / ('mask_%s_alpha.png' % name), 8, True, 50)
        QA['sky_exposure'][name] = sky_stats(pth)
        print('V79_SKY', name, QA['sky_exposure'][name])
    HEMI['v79_eye'] = hemisphere_openness(EYE, r_dir / 'diag_hemi_v79_eye_alpha.png')
    HEMI['v79_altar'] = hemisphere_openness(ALTAR + Vector((0, 0, 1.0)), r_dir / 'diag_hemi_v79_altar_alpha.png')
    QA['hemisphere_sky_openness'] = HEMI
    # side-by-side occlusion diagnostic: magenta = sky, green = canopy/geometry
    tiles = []
    for k in ('v78_eye', 'v79_eye', 'v78_altar', 'v79_altar'):
        pth = (out / 'renders' if k.startswith('v78') else r_dir) / ('diag_hemi_%s_alpha.png' % k)
        a = load_px(pth)[..., 3]; t = np.zeros((360, 360, 4), np.float32); t[..., 3] = 1
        t[..., 0] = 1 - a; t[..., 2] = (1 - a) * .7; t[..., 1] = a * .5
        tiles.append(t)
    save_px(np.concatenate([np.concatenate(tiles[2:], 1), np.concatenate(tiles[:2], 1)], 0), r_dir / 'diag_canopy_occlusion_hemispheres.png')
    print('V79_HEMI', HEMI)

QA['lighting_v79'] = apply_v79_lighting()

# ================================================================ save / reopen / SHA
dest = out / 'v79_enclosed_canopy.blend'; assert not dest.exists()
scene.camera = cam; set_view('matched')
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()), compress=True)
digest_before = snap()
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve())); scene = bpy.context.scene; cam = scene.camera
assert snap() == digest_before, 'reopen digest mismatch'
assert sha(src) == LOCK
QA['native_sha256'] = sha(dest); QA['reopen_digest_exact'] = True; QA['native_bytes'] = dest.stat().st_size
print('V79_SAVED', QA['native_sha256'])

# ---- B. final V79 lighting set
if RENDER:
    for name in VIEWS:
        set_view(name); renders['v79B_' + name] = render(r_dir / ('v79_B_%s.png' % name), SPP_B)
    # wireframe diagnostic (Cycles material override, aerial + matched)
    wm = bpy.data.materials.new('V79_diag_wire'); wm.use_nodes = True; n = wm.node_tree.nodes; l = wm.node_tree.links
    b = n['Principled BSDF']; b.inputs['Base Color'].default_value = (.03, .035, .04, 1)
    wf = n.new('ShaderNodeWireframe'); wf.use_pixel_size = True; wf.inputs['Size'].default_value = .3
    em = n.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (.55, .9, .6, 1); em.inputs['Strength'].default_value = 1.5
    mx = n.new('ShaderNodeMixShader'); l.new(wf.outputs[0], mx.inputs[0]); l.new(b.outputs[0], mx.inputs[1]); l.new(em.outputs[0], mx.inputs[2])
    l.new(mx.outputs[0], n['Material Output'].inputs[0])
    set_atmosphere(False); scene.view_layers[0].material_override = wm
    for name in ('oblique_aerial', 'matched'):
        set_view(name); render(r_dir / ('diag_wireframe_%s.png' % name), 4)
    scene.view_layers[0].material_override = None; set_atmosphere(True)
    # matched sky-mask overlay on the final image
    m = load_px(r_dir / 'mask_matched_alpha.png'); f = load_px(r_dir / 'v79_B_matched.png')
    if m.shape[:2] != f.shape[:2]:
        m = np.repeat(np.repeat(m, f.shape[0] // m.shape[0], 0), f.shape[1] // m.shape[1], 1)
    sky = (1 - m[..., 3])[..., None]; ov = f.copy(); ov[..., :3] = f[..., :3] * (1 - sky * .85) + np.array([1, .1, .6]) * sky * .85
    save_px(ov, r_dir / 'diag_matched_sky_overlay.png')

# ================================================================ game-LOD GLB candidate (separate from native art source)
def oak_lod(src_mesh, keep_every, card_scale, wood_ratio, name):
    import bmesh
    bm = bmesh.new(); bm.from_mesh(src_mesh); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
    runs = []; cur = []; cur_v = set()
    for f in bm.faces:
        if f.material_index != 1:
            continue
        vs = {v.index for v in f.verts}
        if cur and not (vs & cur_v):
            runs.append(cur); cur = []; cur_v = set()
        cur.append(f); cur_v |= vs
    if cur:
        runs.append(cur)
    kill = []
    for i, r in enumerate(runs):
        if i % keep_every:
            kill += r
        else:
            vs = {v for f in r for v in f.verts}; c = sum((v.co for v in vs), Vector()) / len(vs)
            for v in vs:
                v.co = c + (v.co - c) * card_scale
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for i, mt in enumerate(src_mesh.materials):
        me.materials.append(mt)
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    vg = o.vertex_groups.new(name='wood'); wood_v = {i for p in me.polygons if p.material_index != 1 for i in p.vertices}
    vg.add(list(wood_v), 1.0, 'REPLACE')
    md = o.modifiers.new('dec', 'DECIMATE'); md.ratio = wood_ratio; md.vertex_group = 'wood'; md.vertex_group_factor = 1.0
    bpy.context.view_layer.objects.active = o
    with bpy.context.temp_override(object=o, active_object=o):
        bpy.ops.object.modifier_apply(modifier='dec')
    me = o.data; me.calc_loop_triangles(); bpy.data.objects.remove(o)
    return me, len(runs)


if '--no-glb' not in argv:
    try:
        lod_near, nruns = oak_lod(bpy.data.meshes['island_trees_01_blockout_cleaned'], 40, 2.9, .03, 'V79_GAME_oak_LOD1')
        lod_far, _ = oak_lod(bpy.data.meshes['island_trees_01_blockout_cleaned'], 140, 4.6, .012, 'V79_GAME_oak_LOD2')
        gcoll = bpy.data.collections.new('V79_GAME_EXPORT'); scene.collection.children.link(gcoll)
        gt = 0; per_mesh = {}
        for o in bpy.data.collections['V79_ENCLOSED_CANOPY'].objects:
            me = o.data
            if me.name == 'island_trees_01_blockout_cleaned':
                me = lod_near if o['v79_layer'].startswith('A') else lod_far
            g = bpy.data.objects.new('G_' + o.name, me); g.matrix_world = o.matrix_world.copy(); gcoll.objects.link(g)
            me.calc_loop_triangles(); gt += len(me.loop_triangles); per_mesh[me.name] = per_mesh.get(me.name, 0) + 1
        for o in bpy.data.collections['V79_UNDERSTORY_COLONIES'].objects:
            if o.data.name.startswith(('modelShape', 'tt_01', 'medium')):
                continue                              # heavy scan rocks/stumps stay native-only in this candidate
            g = bpy.data.objects.new('G_' + o.name, o.data); g.matrix_world = o.matrix_world.copy(); gcoll.objects.link(g)
            o.data.calc_loop_triangles(); gt += len(o.data.loop_triangles); per_mesh[o.data.name] = per_mesh.get(o.data.name, 0) + 1
        bpy.ops.object.select_all(action='DESELECT')
        for o in gcoll.objects:
            o.select_set(True)
        glb = out / 'v79_enclosed_canopy_game_lod_candidate.glb'
        bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB', use_selection=True, export_gpu_instances=True, export_apply=False,
                                  export_image_format='JPEG', export_jpeg_quality=80)
        mats = {m.name for o in gcoll.objects for m in o.data.materials if m}
        QA['glb_candidate'] = dict(path=glb.name, sha256=sha(glb), bytes=glb.stat().st_size, instances=len(gcoll.objects), unique_meshes=len(per_mesh), instances_per_mesh=per_mesh,
                                   triangles_instanced=gt, materials=len(mats), est_draw_calls_instanced=sum(len(bpy.data.meshes[k].materials) for k in per_mesh),
                                   oak_leaf_clusters_src=nruns, oak_LOD1_tris=len(lod_near.loop_triangles), oak_LOD2_tris=len(lod_far.loop_triangles),
                                   note='GPU-instanced layout LOD; heavy scan rocks/stumps omitted; G4 runtime NOT_RUN')
        print('V79_GLB', json.dumps({k: v for k, v in QA['glb_candidate'].items() if k != 'instances_per_mesh'}))
    except Exception as e:                            # recorded, never hidden
        QA['glb_candidate'] = dict(status='FAILED', error=repr(e)); print('V79_GLB_FAIL', repr(e))

# ================================================================ before/after sheet + QA
if RENDER and (out / 'v78_baseline_matched.png').exists():
    def tile(p, w=480, h=270):
        a = load_px(p); ys = np.linspace(0, a.shape[0] - 1, h).astype(int); xs = np.linspace(0, a.shape[1] - 1, w).astype(int); return a[ys][:, xs]
    rows = []
    for v in ('matched', 'lateral'):
        rows.append(np.concatenate([tile(out / ('v78_baseline_%s.png' % v)), np.ones((270, 6, 4), np.float32), tile(r_dir / ('v79_A_v78light_%s.png' % v)), np.ones((270, 6, 4), np.float32), tile(r_dir / ('v79_B_%s.png' % v))], 1))
    sheet = np.concatenate([rows[1], np.ones((6, rows[0].shape[1], 4), np.float32), rows[0]], 0)   # image origin bottom-left
    save_px(sheet, out / 'v79_before_after_sheet.png')
QA['limits'] = ['Provisional local coordinates; no canonical world placement or collision authored.',
                'Protected route/altar/sight/camera zones from V57/V58/V71 provisional data; trunks and understory excluded, crowns may overhang.',
                'Sky exposure is geometry-only alpha occlusion at 50% res, 8 spp; atmosphere disabled for masks.',
                'G4 (WebGL/Android/runtime) NOT_RUN; GLB is a layout LOD candidate only.']
QA['outputs'] = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.suffix in ('.blend', '.png', '.glb')}
QA['secs'] = round(time.time() - T0, 1)
(out / 'v79_qa.json').write_text(json.dumps(QA, indent=1) + '\n')
print('V79_DONE', QA['secs'])

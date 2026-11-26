"""V80 moss-forest root support, floor detail and game LOD budget, on SHA-locked V79 candidate.

Addresses V79 independent QA (PR #482 comment 7185097913): root float, projected-error LOD/visible
budget, homogeneous floor patches, lateral foreground trunk.
Usage: blender -b --factory-startup --python native_moss_forest_v80.py -- V79.blend OUT_DIR [--v79-renders DIR] [--preview] [--no-render] [--stage ground|full]
Isolated candidate only: provisional local coordinates, no collision/canonical placement/adoption.
"""
import bpy, sys, math, hashlib, json, random, time
from pathlib import Path
from array import array
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
src, out = Path(argv[0]), Path(argv[1])
OPT = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
STAGE = OPT('--stage', 'full'); RENDER = '--no-render' not in argv; PREVIEW = '--preview' in argv
V79R = Path(OPT('--v79-renders')) if OPT('--v79-renders') else None
out.mkdir(parents=True, exist_ok=True)
T0 = time.time()


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


LOCK = '08675798620fd43d08bc68cb674d32659cf4b7ed5c724622f99a2cce8aaf9288'   # V79 artifact 15092623768 native
assert bpy.app.version[:3] == (5, 3, 0)
assert sha(src) == LOCK, 'V79 source SHA mismatch'
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()))
scene = bpy.context.scene
rng = random.Random(20261126080)


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
            cache[m.name] = (digest(m.vertices, 'co', len(m.vertices) * 3, 'f'), digest(m.loops, 'vertex_index', len(m.loops), 'i'),
                             digest(m.polygons, 'material_index', len(m.polygons), 'i'), {a.name: digest(a.data, 'uv', len(a.data) * 2, 'f') for a in m.uv_layers})
        result[o.name] = (cache[m.name], tuple(tuple(r) for r in o.matrix_world), o.hide_render)
    return result


old = snap()
V78_NAMES = [k for k in old if not k.startswith('V79_')]
assert len(V78_NAMES) == 728 and len(old) == 728 + 185 + 1268, (len(V78_NAMES), len(old))
QA = dict(status='V80_MOSS_FOREST_CANDIDATE', source='V79 native', source_sha256=LOCK, blender=bpy.app.version_string)

# ---------------------------------------------------------------- anchors (identical to V79)
EYE = Vector((78.17052459716797, -80.77701568603516, 29.82533073425293))
ALTAR = Vector((93.94316101074219, -93.07432556152344, 30.988130569458008))
ROUTE = (Vector((-205, 140)), Vector((90, -90)))
RESERVED = [((67.536852, -72.486359), 11), ((45.876293, -75.886764), 8), ((49.408698, -58.352544), 10), ((93.943160, -93.074328), 7)]
RAYS = [((65.4663, -80.2138), (45.876293, -75.886764), 4), ((65.4663, -80.2138), (93.943160, -93.074328), 3)]
FWD = (ALTAR - EYE).to_2d().normalized(); PERP = Vector((-FWD.y, FWD.x)); CENTER = (EYE.to_2d() + ALTAR.to_2d()) / 2
SIDE = Vector((.6148655745981655, .788631932636555))
CAM_ZONES = [EYE.to_2d(), EYE.to_2d() + SIDE * 8, EYE.to_2d() - FWD * 12, EYE.to_2d() + FWD * 10, ALTAR.to_2d() + PERP * 14]
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
    return (hit[0].z, hit[1]) if hit[0] else None


def seg_dist(p, a, b):
    ab = b - a; t = max(0, min(1, (p - a).dot(ab) / ab.length_squared)); return (a + ab * t - p).length


def interface_gap(p):
    g = [seg_dist(p, *ROUTE) - 5] + [(p - Vector(c)).length - r for c, r in RESERVED]
    g += [seg_dist(p, Vector(a), Vector(b)) - r for a, b, r in RAYS] + [(p - c).length - 3.5 for c in CAM_ZONES]
    return min(g)


canopy = sorted([o for o in scene.objects if o.name.startswith('V79_') and not o.name.startswith('V79_u_') and o.type == 'MESH'], key=lambda o: o.name)
under = sorted([o for o in scene.objects if o.name.startswith('V79_u_')], key=lambda o: o.name)
assert len(canopy) == 185 and len(under) == 1268


# ================================================================ 1. sector contact metric + re-grounding
BAND_CACHE = {}


def base_band(mesh, wood_only):
    """Local-space vertices in the lowest 18% of the mesh (bark/wood materials only for trees)."""
    key = (mesh.name, wood_only)
    if key not in BAND_CACHE:
        zs = [v.co.z for v in mesh.vertices]; z0, z1 = min(zs), max(zs)
        if wood_only:
            leaf = {i for i, m in enumerate(mesh.materials) if m and ('leaf' in m.name.lower() or 'leaves' in m.name.lower() or 'branches' in m.name.lower())}
            ids = {i for p in mesh.polygons if p.material_index not in leaf for i in p.vertices}
        else:
            ids = range(len(mesh.vertices))
        BAND_CACHE[key] = [mesh.vertices[i].co.copy() for i in ids if mesh.vertices[i].co.z < z0 + (z1 - z0) * .18]
    return BAND_CACHE[key]


def contact(o, wood_only, sectors):
    """Per angular sector around the base centroid: lowest world vertex minus ground directly beneath it."""
    mw = o.matrix_world; pts = [mw @ c for c in base_band(o.data, wood_only)]
    zmin = min(p.z for p in pts); low = [p for p in pts if p.z < zmin + (1.2 if wood_only else .12)]
    cx = sum(p.x for p in low) / len(low); cy = sum(p.y for p in low) / len(low)
    best = {}
    for p in low:
        s = int((math.atan2(p.y - cy, p.x - cx) + math.pi) / math.tau * sectors) % sectors
        if s not in best or p.z < best[s].z:
            best[s] = p
    res = []
    for s, p in best.items():
        g = ground(p.x, p.y)
        if g:
            res.append(p.z - g[0])
    return dict(centre=Vector((cx, cy)), floats=res, n=len(res))


def reground(objs, wood_only, sectors, sink, max_bury):
    rows = []
    for o in objs:
        c0 = contact(o, wood_only, sectors)
        dz = -(max(c0['floats']) + sink)
        if min(c0['floats']) + dz < -max_bury:          # steep side: cap burial, keep the record honest
            dz = -max_bury - min(c0['floats'])
        o.matrix_world = Matrix.Translation(Vector((0, 0, dz))) @ o.matrix_world
        c1 = contact(o, wood_only, sectors)
        rows.append(dict(name=o.name, sectors=c1['n'], float_max_before=round(max(c0['floats']), 3), float_max_after=round(max(c1['floats']), 3),
                         bury_min_after=round(min(c1['floats']), 3), dz=round(dz, 3)))
    return rows


bpy.context.view_layer.update()
GROUND_ROWS = reground(canopy, True, 16, .04, 3.0)
bpy.context.view_layer.update()
U_ROWS = reground(under, False, 8, .015, .35)


def summary(rows):
    fb = [r['float_max_before'] for r in rows]; fa = [r['float_max_after'] for r in rows]
    return dict(count=len(rows), float_max_before=max(fb), float_max_after=max(fa), over_5cm_after=sum(f > .05 for f in fa),
                over_15cm_after=sum(f > .15 for f in fa), bury_min_after=min(r['bury_min_after'] for r in rows))


QA['root_support'] = dict(method='16 angular sectors (trees, wood materials, lowest 1.2 m band) / 8 sectors (understory); lowest world vertex per sector minus raycast ground',
                          canopy=summary(GROUND_ROWS), understory=summary(U_ROWS))
print('V80_ROOT', json.dumps(QA['root_support']))

# ---- lateral foreground trunk: measure which object fills the lateral view within 10 m, move it clear
lat3 = EYE + SIDE.to_3d() * 8


def near_coverage(cam_pos, target, lens=22, nx=64, ny=36, near=10.0):
    fwd = (target - cam_pos).normalized(); right = fwd.cross(Vector((0, 0, 1))).normalized(); upv = right.cross(fwd)
    hx = 18 / lens; hy = hx * 9 / 16; dg = bpy.context.evaluated_depsgraph_get(); cnt = {}
    for j in range(ny):
        for i in range(nx):
            dvec = (fwd + right * ((i + .5) / nx * 2 - 1) * hx + upv * ((j + .5) / ny * 2 - 1) * hy).normalized()
            ok, loc, nrm, idx, ob, mtx = scene.ray_cast(dg, cam_pos, dvec, distance=near)
            if ok and ob.name.startswith('V79_') and not ob.name.startswith('V79_u_'):
                cnt[ob.name] = cnt.get(ob.name, 0) + 1
    return {k: round(v / (nx * ny), 4) for k, v in sorted(cnt.items(), key=lambda kv: -kv[1])}


cov0 = near_coverage(lat3, ALTAR)
lat_rec = dict(coverage_before=cov0)
UP_T0 = EYE + (FWD.to_3d() * .45 + Vector((0, 0, .9)))
if cov0 and next(iter(cov0.values())) > .12:
    ob = bpy.data.objects[next(iter(cov0))]; M0 = ob.matrix_world.copy()
    c = contact(ob, True, 8)['centre']; away = (c - lat3.to_2d()); away.normalize()
    lat_rec['up_coverage_before'] = round(sum(near_coverage(EYE, UP_T0, 16, 40, 24, 45).values()), 4)
    best = None
    for step in (0, 1.0, 2.0, 3.0, 4.0, 5.5):
        p = c + away * step
        if step and interface_gap(p) < 3.0:
            continue
        for yaw in range(0, 360, 45):
            R = Matrix.Translation(p.to_3d()) @ Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Translation(-c.to_3d())
            ob.matrix_world = R @ M0; bpy.context.view_layer.update()
            cv = near_coverage(lat3, ALTAR).get(ob.name, 0)
            if cv > .08:
                continue
            up = sum(near_coverage(EYE, UP_T0, 16, 40, 24, 45).values())
            if best is None or up > best[0] + 1e-6 or (abs(up - best[0]) < 1e-6 and step < best[1]):
                best = (up, step, yaw, cv, R @ M0)
    if best:
        ob.matrix_world = best[4]; bpy.context.view_layer.update(); r = reground([ob], True, 16, .04, 3.0)[0]
        lat_rec.update(name=ob.name, shift_m=best[1], yaw_deg=best[2], coverage_after=round(best[3], 4), up_coverage_after=round(best[0], 4), float_max_after=r['float_max_after'])
    else:
        ob.matrix_world = M0
QA['lateral_trunk'] = lat_rec
print('V80_LATERAL', json.dumps(lat_rec))

# ---- overhead compensation: one added oak chosen by measured upward coverage, rejected if it blocks matched/lateral within 20 m
def total_cov(cam_pos, target, lens, near):
    return sum(near_coverage(cam_pos, target, lens, 40, 24, near).values())


UP_T = EYE + (FWD.to_3d() * .45 + Vector((0, 0, .9)))
up0 = total_cov(EYE, UP_T, 16, 45)
ISL_M = bpy.data.meshes['island_trees_01_blockout_cleaned']
best = None; tried = 0
trunk_c = [contact(o, True, 4)['centre'] for o in canopy]
for dist in (8.5, 10.5, 12.5, 14.5):
    for k in range(16):
        ang = math.tau * k / 16; q = EYE.to_2d() + Vector((math.cos(ang), math.sin(ang))) * dist
        if interface_gap(q) < 3.2 or any((q - t).length < 4.0 for t in trunk_c):
            continue
        tried += 1
        o = bpy.data.objects.new('V80_oak_overhead', ISL_M); scene.collection.objects.link(o)
        s_ = 23.0 / 5.03; lean_axis = Vector((-(EYE.y - q.y), EYE.x - q.x, 0)).normalized()
        o.matrix_world = Matrix.Translation(q.to_3d()) @ Matrix.Rotation(math.radians(9), 4, lean_axis) @ Matrix.Rotation(ang * 1.7, 4, 'Z') @ Matrix.Scale(s_, 4)
        bpy.context.view_layer.update(); reground([o], True, 16, .04, 3.0); bpy.context.view_layer.update()
        up = total_cov(EYE, UP_T, 16, 45) - up0
        blk = max(near_coverage(EYE, ALTAR, 22, 40, 24, 20).get(o.name, 0), near_coverage(lat3, ALTAR, 22, 40, 24, 20).get(o.name, 0))
        if blk <= .06 and (best is None or up > best[0]):
            best = (up, q.copy(), o.matrix_world.copy(), blk)
        bpy.data.objects.remove(o)
OVER = dict(candidates_tried=tried, up_coverage_before=round(up0, 4))
if best and best[0] > .03:
    o = bpy.data.objects.new('V80_oak_overhead', ISL_M); bpy.data.collections.new('V80_CANOPY_COMPENSATION')
    cc = bpy.data.collections['V80_CANOPY_COMPENSATION']; scene.collection.children.link(cc); cc.objects.link(o); o.matrix_world = best[2]; o['scenic_only'] = True
    bpy.context.view_layer.update(); r = reground([o], True, 16, .04, 3.0)[0]
    OVER.update(placed=True, x=round(best[1].x, 2), y=round(best[1].y, 2), up_coverage_gain=round(best[0], 4), near_block_max=round(best[3], 4), float_max_after=r['float_max_after'], interface_gap=round(interface_gap(best[1]), 2))
    canopy.append(o)
QA['overhead_compensation'] = OVER
print('V80_OVERHEAD', json.dumps(OVER))
if STAGE == 'ground':
    raise SystemExit(0)


# ================================================================ 2. mossy wood material (box-projected photo bark + moss on up-facing surfaces)
def mossy_wood_material():
    m = bpy.data.materials.new('V80_mossy_root_bark'); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links; N.clear()
    o = N.new('ShaderNodeOutputMaterial'); b = N.new('ShaderNodeBsdfPrincipled'); L.new(b.outputs[0], o.inputs[0])
    tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1.6, 1.6, 1.6); L.new(tc.outputs['Object'], mp.inputs['Vector'])

    def tex(name, nc=False):
        t = N.new('ShaderNodeTexImage'); t.image = bpy.data.images[name]; t.projection = 'BOX'; t.projection_blend = .35
        if nc:
            t.image.colorspace_settings.name = 'Non-Color'
        L.new(mp.outputs[0], t.inputs['Vector']); return t
    bark = tex('island_tree_01_diff'); nor = tex('island_tree_01_nor_gl', True); arm = tex('island_tree_01_rough', True)
    mc = N.new('ShaderNodeTexImage'); mc.image = bpy.data.images['moss_tile_basecolor']; mc.projection = 'BOX'; mc.projection_blend = .3
    m2 = N.new('ShaderNodeMapping'); m2.inputs['Scale'].default_value = (2.4, 2.4, 2.4); L.new(tc.outputs['Object'], m2.inputs['Vector']); L.new(m2.outputs[0], mc.inputs['Vector'])
    geo = N.new('ShaderNodeNewGeometry'); sep = N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Normal'], sep.inputs[0])
    up = N.new('ShaderNodeMapRange'); up.inputs['From Min'].default_value = .2; up.inputs['From Max'].default_value = .75; L.new(sep.outputs['Z'], up.inputs['Value'])
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 5; L.new(geo.outputs['Position'], nz.inputs['Vector'])
    nm = N.new('ShaderNodeMapRange'); nm.inputs['From Min'].default_value = .38; nm.inputs['From Max'].default_value = .6; L.new(nz.outputs['Fac'], nm.inputs['Value'])
    f = N.new('ShaderNodeMath'); f.operation = 'MULTIPLY'; L.new(up.outputs[0], f.inputs[0]); L.new(nm.outputs[0], f.inputs[1])
    dark = N.new('ShaderNodeHueSaturation'); dark.inputs['Value'].default_value = .62; dark.inputs['Saturation'].default_value = .8; L.new(bark.outputs['Color'], dark.inputs['Color'])
    moss = N.new('ShaderNodeHueSaturation'); moss.inputs['Value'].default_value = .75; L.new(mc.outputs['Color'], moss.inputs['Color'])
    mix = N.new('ShaderNodeMix'); mix.data_type = 'RGBA'; L.new(f.outputs[0], mix.inputs['Factor']); L.new(dark.outputs[0], mix.inputs['A']); L.new(moss.outputs[0], mix.inputs['B'])
    L.new(mix.outputs['Result'], b.inputs['Base Color'])
    sp = N.new('ShaderNodeSeparateColor'); L.new(arm.outputs['Color'], sp.inputs[0])
    rr = N.new('ShaderNodeMix'); rr.data_type = 'FLOAT'; L.new(f.outputs[0], rr.inputs['Factor']); L.new(sp.outputs['Green'], rr.inputs['A']); rr.inputs['B'].default_value = .92
    L.new(rr.outputs['Result'], b.inputs['Roughness'])
    nmap = N.new('ShaderNodeNormalMap'); L.new(nor.outputs['Color'], nmap.inputs['Color']); L.new(nmap.outputs[0], b.inputs['Normal'])
    b.inputs['Specular IOR Level'].default_value = .3
    return m


WOOD = mossy_wood_material()
rcoll = bpy.data.collections.new('V80_ROOTS_AND_DEADWOOD'); scene.collection.children.link(rcoll)


# ================================================================ 3. exposed buttress roots (tapered swept tubes, follow measured ground, dive in)
def tube_mesh(name, rings, sides=7, rings_v=None):
    """rings: list of (centre Vector, radius). Builds a closed-ish tapered tube with cylindrical UVs."""
    import bmesh
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); verts = []; vlen = 0.
    for k, (c, r) in enumerate(rings):
        t = (rings[min(k + 1, len(rings) - 1)][0] - rings[max(k - 1, 0)][0]).normalized()
        a = t.cross(Vector((0, 0, 1)))
        if a.length < 1e-4:
            a = Vector((1, 0, 0))
        a.normalize(); bvec = t.cross(a)
        if k:
            vlen += (c - rings[k - 1][0]).length
        ring = []
        for i in range(sides):
            ang = math.tau * i / sides
            vs = rings_v[k] if rings_v else .82
            ring.append((bm.verts.new(c + (a * math.cos(ang) + bvec * math.sin(ang) * vs) * r), vlen))
        verts.append(ring)
    for k in range(len(verts) - 1):
        for i in range(sides):
            j = (i + 1) % sides
            f = bm.faces.new((verts[k][i][0], verts[k][j][0], verts[k + 1][j][0], verts[k + 1][i][0]))
            for lp, (u, v) in zip(f.loops, ((i / sides, verts[k][i][1]), ((i + 1) / sides, verts[k][j][1]), ((i + 1) / sides, verts[k + 1][j][1]), (i / sides, verts[k + 1][i][1]))):
                lp[uvl].uv = (u, v * .5)
    for ring in (verts[0], verts[-1]):                     # caps: no open tube ends
        try:
            bm.faces.new([v for v, _ in ring])
        except ValueError:
            pass
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    return me


def join_meshes(name, meshes):
    import bmesh
    bm = bmesh.new()
    for me in meshes:
        bm.from_mesh(me); bpy.data.meshes.remove(me)
    out_me = bpy.data.meshes.new(name); bm.to_mesh(out_me); bm.free(); out_me.materials.append(WOOD); return out_me


ROOT_ROWS = []
oak_targets = [o for o in canopy if o.data.name == 'island_trees_01_blockout_cleaned']
for o in oak_targets:
    con = contact(o, True, 16); c = con['centre']
    if (c - CENTER).length > 34:
        continue
    s = o.matrix_world.to_scale().x
    band = [o.matrix_world @ v for v in base_band(o.data, True)]
    g0 = ground(c.x, c.y)[0]
    collar = [p for p in band if g0 + .2 < p.z < g0 + .9] or band
    nroot = rng.randint(5, 8); a0 = rng.uniform(0, math.tau); parts = []; clipped = 0
    for k in range(nroot):
        ang = a0 + math.tau * k / nroot + rng.uniform(-.3, .3); dvec = Vector((math.cos(ang), math.sin(ang)))
        sect = [p for p in collar if abs(((math.atan2(p.y - c.y, p.x - c.x) - ang + math.pi) % math.tau) - math.pi) < .35]
        r_in = max(((p.to_2d() - c).length for p in sect), default=.6 * s / 4.6)
        L = rng.uniform(1.8, 4.6) * s / 4.6; r0 = rng.uniform(.2, .36) * s / 4.6; h0 = rng.uniform(.35, .75) * s / 4.6
        wander = rng.uniform(-.3, .3); ph = rng.uniform(0, math.tau); rings = []; vsc = []
        for i in range(13):
            t = i / 12; side = Vector((-dvec.y, dvec.x))
            q = c + dvec * (r_in * .4 + L * t) + side * (wander * L * t * t + math.sin(ph + t * 7) * .12 * L * t)
            g = ground(q.x, q.y)
            if g is None or interface_gap(q) < .25 + r0 * (1 - .8 * t):
                clipped += 1; break
            rings.append((Vector((q.x, q.y, g[0] + h0 * (1 - t) ** 2.1 - .2 * t)), r0 * (1 - .86 * t) + .018)); vsc.append(1.9 - 1.1 * min(1, t * 2.2))   # buttress: tall/flat near trunk
        if len(rings) >= 5:
            parts.append(tube_mesh('root', rings, 8, vsc))
            if rng.random() < .65 and len(rings) >= 8:                     # side root off the main root
                k0 = rng.randint(3, min(6, len(rings) - 3)); base_c, base_r = rings[k0]; sd = rng.choice((-1, 1))
                d2 = (dvec + Vector((-dvec.y, dvec.x)) * sd * rng.uniform(.6, 1.1)).normalized(); sub = []
                for i in range(7):
                    t = i / 6; q = base_c.to_2d() + d2 * L * .45 * t; g = ground(q.x, q.y)
                    if g is None or interface_gap(q) < .2:
                        break
                    sub.append((Vector((q.x, q.y, g[0] + (base_c.z - g[0]) * (1 - t) ** 1.5 - .12 * t)), base_r * .6 * (1 - .8 * t) + .012))
                if len(sub) >= 4:
                    parts.append(tube_mesh('sroot', sub, 6))
    if parts:
        me = join_meshes('V80_roots_' + o.name[4:], parts); ro = bpy.data.objects.new('V80_roots_' + o.name[4:], me); rcoll.objects.link(ro)
        ro['scenic_only'] = True; me.calc_loop_triangles()
        ROOT_ROWS.append(dict(tree=o.name, roots=len(parts), clipped_by_interface=clipped, triangles=len(me.loop_triangles)))
QA['exposed_roots'] = dict(trees=len(ROOT_ROWS), roots=sum(r['roots'] for r in ROOT_ROWS), triangles=sum(r['triangles'] for r in ROOT_ROWS), rows=ROOT_ROWS)
print('V80_ROOTS', QA['exposed_roots']['trees'], QA['exposed_roots']['roots'], QA['exposed_roots']['triangles'])


# ================================================================ 4. fallen twigs / branches (procedural, 6 variants, instanced) + logs
def twig_variant(i):
    rr = random.Random(9100 + i); Ln = rr.uniform(.6, 1.7); r = rr.uniform(.018, .05); parts = []

    def stick(p0, d, length, rad, n=5):
        rings = []
        bend = Vector((rr.uniform(-.1, .1), rr.uniform(-.1, .1), 0))
        for k in range(n):
            t = k / (n - 1); rings.append((p0 + d * length * t + bend * length * t * t, rad * (1 - .55 * t) + .004))
        return rings
    parts.append(tube_mesh('tw', stick(Vector((0, 0, 0)), Vector((1, 0, 0)), Ln, r), 6))
    for b in range(rr.randint(1, 3)):
        t = rr.uniform(.25, .75); side = rr.choice((-1, 1)); ang = side * rr.uniform(.45, .9)
        d = Vector((math.cos(ang), math.sin(ang), 0)); parts.append(tube_mesh('tb', stick(Vector((Ln * t, 0, 0)), d, Ln * rr.uniform(.2, .45), r * .55, 4), 5))
    me = join_meshes('V80_twig_v%d' % i, parts); me.calc_loop_triangles(); return me


TWIGS = [twig_variant(i) for i in range(6)]
trunks_xy = [contact(o, True, 4)['centre'] for o in canopy]
TW = []
for i in range(6000):
    if len(TW) >= 900:
        break
    if rng.random() < .7:
        q = rng.choice(trunks_xy) + Vector((rng.gauss(0, 3.5), rng.gauss(0, 3.5)))
    else:
        q = CENTER + Vector((rng.uniform(-36, 36), rng.uniform(-36, 36)))
    if (q - CENTER).length > 42 or interface_gap(q) < .9:
        continue
    me = rng.choice(TWIGS); yaw = rng.uniform(0, math.tau); g = ground(q.x, q.y)
    if not g:
        continue
    span = max(v.co.x for v in me.vertices)
    ends = [q, q + Vector((math.cos(yaw), math.sin(yaw))) * span]
    ge = [ground(e.x, e.y) for e in ends]
    if any(x is None for x in ge) or any(interface_gap(e) < .5 for e in ends):
        continue
    dz = ge[1][0] - ge[0][0]; pitch = math.atan2(dz, span)
    mtx = Matrix.Translation(Vector((q.x, q.y, ge[0][0] - .012))) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(-pitch, 4, 'Y') @ Matrix.Rotation(rng.uniform(0, math.tau), 4, 'X')
    ob = bpy.data.objects.new('V80_twig_%04d' % len(TW), me); ob.matrix_world = mtx; rcoll.objects.link(ob); ob['scenic_only'] = True
    TW.append(me)
dead_src = bpy.data.meshes['dead_tree']
LOGS = []
for ang, dist in ((40, 11), (115, 9), (200, 13), (300, 10), (160, 22)):
    t = math.radians(ang); q = ALTAR.to_2d() + Vector((math.cos(t), math.sin(t))) * dist
    for tries in range(12):
        qq = q + Vector((rng.uniform(-2, 2), rng.uniform(-2, 2)))
        lo = bpy.data.objects.new('V80_log_%d' % len(LOGS), dead_src); rcoll.objects.link(lo)
        lo.matrix_world = Matrix.Translation(Vector((qq.x, qq.y, 0))) @ Matrix.Rotation(rng.uniform(0, math.tau), 4, 'Z') @ Matrix.Scale(rng.uniform(1.3, 2.1), 4)
        bpy.context.view_layer.update()
        pts = [lo.matrix_world @ Vector(b) for b in lo.bound_box]
        if all(interface_gap(p.to_2d()) > .4 for p in pts):
            con = reground([lo], False, 8, .03, .4)[0]; LOGS.append(dict(name=lo.name, float_max_after=con['float_max_after'])); break
        bpy.data.objects.remove(lo)
dead_src.calc_loop_triangles()
QA['deadwood'] = dict(twig_instances=len(TW), twig_variants=len(TWIGS), twig_triangles_instanced=sum(len(m.loop_triangles) for m in TW), logs=LOGS,
                      log_triangles_instanced=len(LOGS) * len(dead_src.loop_triangles))
print('V80_DEADWOOD', len(TW), len(LOGS))


# ================================================================ 5. floor patch breakup (mid-scale value + moss islands, path-aware) and depth lift
def floor_breakup():
    src_m = terrain.data.materials[0]; assert src_m.name == 'V79_forest_floor_layered'
    m = src_m.copy(); m.name = 'V80_forest_floor_layered'; nt = m.node_tree; N = nt.nodes; L = nt.links
    b = [n for n in N if n.type == 'BSDF_PRINCIPLED'][0]; col_sock = b.inputs['Base Color'].links[0].from_socket
    path = [n for n in N if n.type == 'MAP_RANGE' and abs(n.inputs['From Min'].default_value - 4.2) < 1e-4][0]
    geo = N.new('ShaderNodeNewGeometry')

    def noise(scale, detail, rough=.6):
        n = N.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = detail; n.inputs['Roughness'].default_value = rough
        L.new(geo.outputs['Position'], n.inputs['Vector']); return n.outputs['Fac']
    val = N.new('ShaderNodeMapRange'); val.inputs['From Min'].default_value = .3; val.inputs['From Max'].default_value = .7; val.inputs['To Min'].default_value = .7; val.inputs['To Max'].default_value = 1.12
    L.new(noise(.42, 4), val.inputs['Value'])
    mul = N.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1
    cmb = N.new('ShaderNodeCombineColor'); L.new(val.outputs[0], cmb.inputs[0]); L.new(val.outputs[0], cmb.inputs[1]); L.new(val.outputs[0], cmb.inputs[2])
    L.new(col_sock, mul.inputs['A']); L.new(cmb.outputs[0], mul.inputs['B'])
    mt = N.new('ShaderNodeTexImage'); mt.image = bpy.data.images['moss_tile_basecolor']
    sc = N.new('ShaderNodeVectorMath'); sc.operation = 'SCALE'; sc.inputs['Scale'].default_value = 1 / .9; L.new(geo.outputs['Position'], sc.inputs[0]); L.new(sc.outputs[0], mt.inputs['Vector'])
    hs = N.new('ShaderNodeHueSaturation'); hs.inputs['Value'].default_value = .68; hs.inputs['Hue'].default_value = .49; L.new(mt.outputs['Color'], hs.inputs['Color'])
    isl = N.new('ShaderNodeMapRange'); isl.inputs['From Min'].default_value = .6; isl.inputs['From Max'].default_value = .67; L.new(noise(.33, 5, .65), isl.inputs['Value'])
    inv = N.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1; L.new(path.outputs[0], inv.inputs[1])
    msk = N.new('ShaderNodeMath'); msk.operation = 'MULTIPLY'; L.new(isl.outputs[0], msk.inputs[0]); L.new(inv.outputs[0], msk.inputs[1])
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; L.new(msk.outputs[0], mx.inputs['Factor']); L.new(mul.outputs['Result'], mx.inputs['A']); L.new(hs.outputs[0], mx.inputs['B'])
    L.new(mx.outputs['Result'], b.inputs['Base Color'])
    for o in (terrain, ext):
        o.data.materials[0] = m
    return m.name


QA['floor'] = dict(material=floor_breakup(), added='mid-scale value variation (0.7-1.12, ~2.4 m features) + off-path moss islands (~3 m), photo moss albedo')
vol = scene.world.node_tree.nodes['V79_atmosphere']; vol.inputs['Density'].default_value = .0018
vol.inputs['Emission Strength'].default_value = .00008; vol.inputs['Emission Color'].default_value = (.52, .62, .56, 1)
QA['lighting_delta'] = dict(atmosphere='density 0.0012 -> 0.0018 + emission 0.00008 (ambient in-scatter approximation; density alone darkened the band under closed canopy: 0.211 -> 0.195 measured)',
                            calibration='matched 50%/12spp: band 0.185 (d.0012) / 0.192 (d.0022) / 0.2105 (e.0003: full-scene mean .192 p10 .075 milky; e.00015: .175/.057; chosen e.00008 interpolated to V79 mean .143) / 0.231 (e.0006 rejected)', other='V79 L2 unchanged')

# ================================================================ protection
bpy.context.view_layer.update(); now = snap()
assert all(now[k] == old[k] for k in V78_NAMES), 'V78 protected object changed'
QA['protected_v78_objects_exact'] = len(V78_NAMES)
QA['v79_objects_transform_only'] = sum(1 for k in old if k.startswith('V79_') and now[k][0] == old[k][0] and now[k][1] != old[k][1])
assert all(now[k][0] == old[k][0] for k in old), 'V79 mesh data changed'
assert all(k in now for k in old), 'object removed'
assert sha(src) == LOCK

# ================================================================ save / reopen
dest = out / 'v80_moss_forest.blend'; assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()), compress=True); before = snap()
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve())); scene = bpy.context.scene
assert snap() == before
QA['native_sha256'] = sha(dest); QA['native_bytes'] = dest.stat().st_size; QA['reopen_digest_exact'] = True
print('V80_SAVED', QA['native_sha256'])
terrain = bpy.data.objects['A3 provisional reconstructed terrain']; ext = bpy.data.objects['V58_SCENIC_ONLY_terrain_extension']; far = bpy.data.objects['V77_SCENIC_ONLY_FAR_RELIEF']
canopy = sorted([o for o in scene.objects if (o.name.startswith('V79_') and not o.name.startswith('V79_u_') or o.name == 'V80_oak_overhead') and o.type == 'MESH'], key=lambda o: o.name)
cam = scene.camera
import numpy as np


def eye_at(p2, h=1.7):
    g = ground(p2.x, p2.y); return Vector((p2.x, p2.y, (g[0] if g else EYE.z - 1.7) + h))


ring_oak = min([o for o in canopy if o.data.name == 'island_trees_01_blockout_cleaned'], key=lambda o: abs((contact(o, True, 4)['centre'] - EYE.to_2d()).length - 11))
rc = contact(ring_oak, True, 8)['centre']; rdir = (rc - EYE.to_2d()).normalized()
VIEWS = {
    'matched': (EYE, ALTAR, 22), 'lateral': (EYE + SIDE.to_3d() * 8, ALTAR, 22),
    'side': (eye_at(ALTAR.to_2d() + PERP * 14), ALTAR, 24),
    'player_eye': (eye_at(EYE.to_2d() - FWD * 12), eye_at(EYE.to_2d() + FWD * 14, 1.5), 28),
    'altar_approach': (eye_at(EYE.to_2d() + FWD * 10), ALTAR + Vector((0, 0, -.4)), 28),
    'look_up': (EYE, EYE + (FWD.to_3d() * .45 + Vector((0, 0, .9))), 16),
    'oblique_aerial': (CENTER.to_3d() + Vector((-48, 40, EYE.z + 52)), CENTER.to_3d() + Vector((0, 0, EYE.z - 2)), 26),
    'root_close': (eye_at(rc - rdir * 5.5, 1.3), eye_at(rc, .3), 30),
}
ORDINARY = ['matched', 'lateral', 'side', 'player_eye', 'altar_approach']
RES = 50 if PREVIEW else 100; SPP = 12 if PREVIEW else 64


def set_view(n):
    p, t, lens = VIEWS[n]; cam.data.type = 'PERSP'; cam.location = p; cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = lens; cam.data.clip_start = .05; cam.data.clip_end = 600


def render(path, spp, transparent=False, pct=None):
    scene.render.resolution_percentage = pct or RES; scene.cycles.samples = spp; scene.cycles.use_denoising = not transparent; scene.render.film_transparent = transparent
    scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGBA' if transparent else 'RGB'
    scene.render.filepath = str(Path(path).resolve()); bpy.ops.render.render(write_still=True); return Path(path)


def load_px(p):
    im = bpy.data.images.load(str(p)); a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4); bpy.data.images.remove(im); return a


def save_px(arr, path):
    h, w = arr.shape[:2]; im = bpy.data.images.new(Path(path).stem, w, h, alpha=True)
    im.pixels.foreach_set(np.ascontiguousarray(arr, dtype=np.float32).ravel()); im.filepath_raw = str(path); im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)


rd = out / 'renders'; rd.mkdir(exist_ok=True)
LUM = np.array([.2126, .7152, .0722], np.float32)
if RENDER:
    vnode = scene.world.node_tree.nodes['V79_atmosphere']
    QA['sky_exposure'] = {}
    vnode.mute = True
    for n in ORDINARY + ['look_up']:
        set_view(n); a = load_px(render(rd / ('mask_%s_alpha.png' % n), 8, True, 50))[..., 3]
        QA['sky_exposure'][n] = dict(sky_mean=round(float((1 - a).mean()), 4), sky_top_third=round(float((1 - a)[2 * a.shape[0] // 3:].mean()), 4))
    vnode.mute = False
    print('V80_SKY', json.dumps(QA['sky_exposure']))
    QA['luminance'] = {}
    for n in VIEWS:
        set_view(n); px = load_px(render(rd / ('v80_%s.png' % n), SPP))
        y = px[..., :3] @ LUM; h, w = y.shape
        QA['luminance'][n] = dict(mean=round(float(y.mean()), 4), p10=round(float(np.percentile(y, 10)), 4))
        if n == 'matched':
            QA['luminance']['matched_far_band'] = round(float(y[int(h * .52):int(h * .66), int(w * .2):int(w * .42)].mean()), 4)   # image rows bottom-up
    print('V80_LUM', json.dumps(QA['luminance']))
    # wireframe of root/deadwood detail
    wm = bpy.data.materials.new('V80_diag_wire'); wm.use_nodes = True; n_ = wm.node_tree.nodes; l_ = wm.node_tree.links
    b_ = n_['Principled BSDF']; b_.inputs['Base Color'].default_value = (.03, .035, .04, 1)
    wf = n_.new('ShaderNodeWireframe'); wf.use_pixel_size = True; wf.inputs['Size'].default_value = .4
    em = n_.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (.55, .9, .6, 1); mx = n_.new('ShaderNodeMixShader')
    l_.new(wf.outputs[0], mx.inputs[0]); l_.new(b_.outputs[0], mx.inputs[1]); l_.new(em.outputs[0], mx.inputs[2]); l_.new(mx.outputs[0], n_['Material Output'].inputs[0])
    vnode.mute = True; scene.view_layers[0].material_override = wm; set_view('root_close'); render(rd / 'diag_wireframe_root_close.png', 4)
    scene.view_layers[0].material_override = None; vnode.mute = False
    # before/after: V79 artifact renders were produced at identical camera/res/spp/lighting (except atmosphere density)
    if V79R and (V79R / 'v79_B_matched.png').exists():
        def tile(p, w=640, h=360):
            a = load_px(p); ys = np.linspace(0, a.shape[0] - 1, h).astype(int); xs = np.linspace(0, a.shape[1] - 1, w).astype(int); return a[ys][:, xs]
        rows = []
        for v in ('floor_close', 'side', 'lateral', 'matched'):
            vv = 'floor_close' if v == 'floor_close' else v
            rows.append(np.concatenate([tile(V79R / ('v79_B_%s.png' % vv)), np.ones((360, 8, 4), np.float32), tile(rd / ('v80_%s.png' % (v if v != 'floor_close' else 'root_close')))], 1))
        sheet = np.concatenate([x for r in rows for x in (r, np.ones((8, r.shape[1], 4), np.float32))][:-1], 0)
        save_px(sheet, out / 'v80_before_after_sheet.png')


# ================================================================ 6. game LOD: projected-error assignment, impostors, visible budget, GLB
def decimated(mesh, ratio, name, protect_leaf=False):
    o = bpy.data.objects.new('tmp_' + name, mesh.copy()); scene.collection.objects.link(o)
    md = o.modifiers.new('d', 'DECIMATE'); md.ratio = ratio
    with bpy.context.temp_override(object=o, active_object=o):
        bpy.ops.object.modifier_apply(modifier='d')
    me = o.data; me.name = name; bpy.data.objects.remove(o); me.calc_loop_triangles(); return me


def oak_lod(src_mesh, keep_every, card_scale, wood_ratio, name):
    import bmesh
    bm = bmesh.new(); bm.from_mesh(src_mesh); runs = []; cur = []; cur_v = set()
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
    for mt in src_mesh.materials:
        me.materials.append(mt)
    o = bpy.data.objects.new(name, me); scene.collection.objects.link(o)
    vg = o.vertex_groups.new(name='wood'); vg.add(list({i for p in me.polygons if p.material_index != 1 for i in p.vertices}), 1.0, 'REPLACE')
    md = o.modifiers.new('dec', 'DECIMATE'); md.ratio = wood_ratio; md.vertex_group = 'wood'
    with bpy.context.temp_override(object=o, active_object=o):
        bpy.ops.object.modifier_apply(modifier='dec')
    me = o.data; bpy.data.objects.remove(o); me.calc_loop_triangles(); return me


def bake_impostor(mesh, name, res=512):
    """Two orthographic views under uniform white sky (ambient-lit albedo approximation, no directional highlight) -> 2-card cross."""
    sc = bpy.data.scenes.new('bake_' + name); sc.render.engine = 'CYCLES'; sc.cycles.samples = 32; sc.cycles.use_denoising = True
    sc.render.resolution_x = sc.render.resolution_y = res; sc.render.film_transparent = True; sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('bake_w'); w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (1, 1, 1, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0; sc.world = w
    ob = bpy.data.objects.new('bake_obj', mesh); sc.collection.objects.link(ob)
    xs = [v.co.x for v in mesh.vertices]; ys = [v.co.y for v in mesh.vertices]; zs = [v.co.z for v in mesh.vertices]
    cx, cy, cz = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2
    S = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)) * 1.02
    cd = bpy.data.cameras.new('bake_cam'); cd.type = 'ORTHO'; cd.ortho_scale = S; cm = bpy.data.objects.new('bake_cam', cd); sc.collection.objects.link(cm); sc.camera = cm
    halves = []
    for k, (pos, rot) in enumerate((((cx, cy - 50, cz), (math.pi / 2, 0, 0)), ((cx - 50, cy, cz), (math.pi / 2, 0, -math.pi / 2)))):
        cm.location = pos; cm.rotation_euler = rot; p = out / 'impostors' / ('%s_v%d.png' % (name, k)); p.parent.mkdir(exist_ok=True)
        sc.render.filepath = str(p.resolve()); sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
        with bpy.context.temp_override(scene=sc):
            bpy.ops.render.render(write_still=True, scene=sc.name)
        halves.append(load_px(p))
    atlas = np.concatenate(halves, 1); ap = out / 'impostors' / ('%s_atlas.png' % name); save_px(atlas, ap)
    img = bpy.data.images.load(str(ap)); img.pack()
    bpy.data.objects.remove(ob); bpy.data.objects.remove(cm); bpy.data.scenes.remove(sc)
    mt = bpy.data.materials.new('V80_imp_' + name); mt.use_nodes = True; N = mt.node_tree.nodes; b = N['Principled BSDF']
    t = N.new('ShaderNodeTexImage'); t.image = img; mt.node_tree.links.new(t.outputs['Color'], b.inputs['Base Color']); mt.node_tree.links.new(t.outputs['Alpha'], b.inputs['Alpha']); b.inputs['Roughness'].default_value = .9
    h = S / 2
    v = [(cx - h, cy, cz - h), (cx + h, cy, cz - h), (cx + h, cy, cz + h), (cx - h, cy, cz + h),
         (cx, cy + h, cz - h), (cx, cy - h, cz - h), (cx, cy - h, cz + h), (cx, cy + h, cz + h)]
    me = bpy.data.meshes.new('V80_GAME_%s_impostor' % name); me.from_pydata(v, [], [(0, 1, 2, 3), (4, 5, 6, 7)]); me.materials.append(mt)
    uv = me.uv_layers.new(name='UVMap'); coords = [(0, 0), (.5, 0), (.5, 1), (0, 1), (.5, 0), (1, 0), (1, 1), (.5, 1)]
    for p_ in me.polygons:
        for li in p_.loop_indices:
            uv.data[li].uv = coords[me.loops[li].vertex_index]
    me.calc_loop_triangles(); return me, ap


GLB_QA = {}
if '--no-glb' not in argv:
    ISL = bpy.data.meshes['island_trees_01_blockout_cleaned']; TALL = bpy.data.meshes['eco_tree_forest_tall_a_LOD1_mesh']; DEC = bpy.data.meshes['eco_tree_deciduous_a_LOD1_mesh']
    CULL = ('CULL', None)
    # ladders: (label, mesh|None, estimated geometric error m); coarsest option whose projected error <= tolerance is chosen
    LAD = {ISL.name: [('oak_LOD1', oak_lod(ISL, 40, 2.9, .03, 'V80_GAME_oak_LOD1'), .08), ('oak_LOD2', oak_lod(ISL, 80, 3.6, .02, 'V80_GAME_oak_LOD2'), .16),
                      ('oak_LOD3', oak_lod(ISL, 200, 5.4, .008, 'V80_GAME_oak_LOD3'), .4)],
           TALL.name: [('tall_src', TALL, 0.), ('tall_dec', decimated(TALL, .35, 'V80_GAME_tall_dec'), .25)],
           DEC.name: [('dec_src', DEC, 0.), ('dec_dec', decimated(DEC, .35, 'V80_GAME_dec_dec'), .25)]}
    imp_paths = {}
    for k, nm, err in ((ISL.name, 'oak', 1.6), (TALL.name, 'tall', 1.0), (DEC.name, 'dec', .9)):
        me, ap = bake_impostor(bpy.data.meshes[k], nm); LAD[k].append((nm + '_IMP', me, err)); imp_paths[nm] = sha(ap)
    log_lod = decimated(bpy.data.meshes['dead_tree'], .03, 'V80_GAME_log_lod')
    for o in scene.objects:
        if not o.name.startswith('V79_u_') or o.data.name in LAD:
            continue
        me = o.data; n = me.name
        if n.startswith(('modelShape', 'medium', 'tt_01')):
            LAD[n] = [('rock_dec', decimated(me, .05, 'V80_GAME_%s_lod' % n), .03), ('cull', None, .5)]
        elif n.startswith('Plane'):
            LAD[n] = [('fern_src', me, 0.), ('fern_d30', decimated(me, .3, 'V80_GAME_%s_d30' % n), .05), ('fern_d10', decimated(me, .1, 'V80_GAME_%s_d10' % n), .15), ('cull', None, .8)]
        elif 'moss' in n:
            LAD[n] = [('moss_src', me, 0.), ('cull', None, .25)]
        else:
            LAD[n] = [('shrub_src', me, 0.), ('cull', None, 1.2)]
    for me in {o.data for o in scene.objects if o.name.startswith('V80_twig')}:
        LAD[me.name] = [('twig_src', me, 0.), ('cull', None, .06)]
    for me in {o.data for o in scene.objects if o.name.startswith('V80_roots')}:
        LAD[me.name] = [('root_src', me, 0.), ('cull', None, .5)]
    LAD['dead_tree'] = [('log_dec', log_lod, .04), ('cull', None, .7)]
    for lad in LAD.values():
        for e in lad:
            if e[1] is not None:
                e[1].calc_loop_triangles()
    samples = [eye_at(EYE.to_2d() + FWD * t) for t in range(-36, 21, 3)] + [eye_at(ALTAR.to_2d() + Vector((math.cos(a), math.sin(a))) * 5) for a in (0, 1.57, 3.14, 4.71)]
    F_PX = 960 * 22 / 36

    def bsphere(o):
        cs = [o.matrix_world @ Vector(b) for b in o.bound_box]; c = sum(cs, Vector()) / 8; return c, max((x - c).length for x in cs)
    INST = [o for o in scene.objects if o.type == 'MESH' and (o.name.startswith(('V79_', 'V80_oak', 'V80_twig', 'V80_roots', 'V80_log'))) and o.data.name in LAD]
    DIST = {}
    for o in INST:
        c, r = bsphere(o); DIST[o.name] = (c, r, max(.5, min((s_ - c).length for s_ in samples) - r))

    def assign(tau):
        ch = {}
        for o in INST:
            d = DIST[o.name][2]; lad = LAD[o.data.name]; pick = lad[0]
            for cand in lad:
                if cand[2] * F_PX / d <= tau:
                    pick = cand
            ch[o.name] = pick
        return ch

    def frustum(view, ch):
        p, t, lens = VIEWS[view]; fwd = (t - p).normalized(); right = fwd.cross(Vector((0, 0, 1))).normalized(); upv = right.cross(fwd)
        hx = 18 / lens; hy = hx * 9 / 16
        planes = [(fwd * hx - right).normalized(), (fwd * hx + right).normalized(), (fwd * hy - upv).normalized(), (fwd * hy + upv).normalized()]
        tris = 0; pairs = set(); inst = 0; cat = {}
        for name, pick in ch.items():
            if pick[1] is None:
                continue
            c, r, _ = DIST[name]; v = c - p
            if v.dot(fwd) < -r or any(v.dot(n) < -r for n in planes):
                continue
            nt_ = len(pick[1].loop_triangles); tris += nt_; inst += 1; k = pick[0].split('_')[0]; cat[k] = cat.get(k, 0) + nt_
            for mt in pick[1].materials:
                pairs.add((pick[1].name, mt.name if mt else None))
        # occlusion estimate: instances actually hit by a 160x90 primary-ray grid against the native scene
        dg = bpy.context.evaluated_depsgraph_get(); seen = set()
        for j in range(90):
            for i in range(160):
                dv = (fwd + right * ((i + .5) / 160 * 2 - 1) * hx + upv * ((j + .5) / 90 * 2 - 1) * hy).normalized()
                ok, loc, nrm, idx, ob, mtx = scene.ray_cast(dg, p, dv, distance=600)
                if ok and ob.name in ch:
                    seen.add(ob.name)
        otris = 0; opairs = set()
        for name in seen:
            pick = ch[name]
            if pick[1] is None:
                continue
            otris += len(pick[1].loop_triangles)
            for mt in pick[1].materials:
                opairs.add((pick[1].name, mt.name if mt else None))
        return dict(visible_instances=inst, visible_triangles=tris, draw_calls_instanced=len(pairs), triangles_by_category=dict(sorted(cat.items(), key=lambda kv: -kv[1])),
                    occlusion_est_instances=len(seen), occlusion_est_triangles=otris, occlusion_est_draw_calls=len(opairs))
    BUDGET = dict(triangles=600000, draw_calls=150, scope='V79/V80 added forest layers only; V78 base scene content excluded', basis='provisional Android/WebGL mid-tier planning target, not a measured device limit')
    PROF = {}
    for name, tau in (('desktop_4px', 4.0), ('mobile_8px', 8.0)):
        ch = assign(tau); vis = {v: frustum(v, ch) for v in ORDINARY}; cnt = {}
        for pk in ch.values():
            cnt[pk[0]] = cnt.get(pk[0], 0) + 1
        worst = max(vis.values(), key=lambda x: x['visible_triangles'])
        PROF[name] = dict(tolerance_px=tau, lod_counts=cnt, visible=vis, worst_visible_triangles=worst['visible_triangles'],
                          max_draw_calls=max(v['draw_calls_instanced'] for v in vis.values()),
                          result='PASS' if worst['visible_triangles'] <= BUDGET['triangles'] and max(v['draw_calls_instanced'] for v in vis.values()) <= BUDGET['draw_calls'] else 'OVER',
                          worst_occlusion_est_triangles=max(v['occlusion_est_triangles'] for v in vis.values()),
                          result_with_occlusion_culling='PASS' if max(v['occlusion_est_triangles'] for v in vis.values()) <= BUDGET['triangles'] else 'OVER')
        PROF[name]['_choice'] = ch
        print('V80_BUDGET', name, PROF[name]['worst_visible_triangles'], PROF[name]['max_draw_calls'], PROF[name]['result'], 'occl', PROF[name]['worst_occlusion_est_triangles'], PROF[name]['result_with_occlusion_culling'], json.dumps(worst['triangles_by_category']))
    ch = PROF['mobile_8px'].pop('_choice'); PROF['desktop_4px'].pop('_choice')
    gcoll = bpy.data.collections.new('V80_GAME_EXPORT'); scene.collection.children.link(gcoll); total = 0; meshes = set()
    for name, pick in ch.items():
        if pick[1] is None:
            continue
        g = bpy.data.objects.new('G_' + name, pick[1]); g.matrix_world = bpy.data.objects[name].matrix_world.copy(); gcoll.objects.link(g); total += len(pick[1].loop_triangles); meshes.add(pick[1].name)
    bpy.ops.object.select_all(action='DESELECT')
    for o in gcoll.objects:
        o.select_set(True)
    glb = out / 'v80_moss_forest_game_lod_mobile8px.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB', use_selection=True, export_gpu_instances=True, export_image_format='JPEG', export_jpeg_quality=80)
    GLB_QA = dict(path=glb.name, sha256=sha(glb), bytes=glb.stat().st_size, profile='mobile_8px', instances=len(gcoll.objects), unique_meshes=len(meshes), triangles_instanced_total=total,
                  impostor_atlas_sha256=imp_paths, f_px=round(F_PX, 1), gameplay_samples=len(samples), lod_tris={e[0]: len(e[1].loop_triangles) for k in (ISL.name, TALL.name, DEC.name) for e in LAD[k]},
                  error_note='geometric errors are per-LOD estimates, not measured Hausdorff; impostors ambient-lit albedo approximation', profiles=PROF, budget=BUDGET,
                  note='static LOD by nearest gameplay sample (conservative); G4 WebGL/Android runtime NOT_RUN')
QA['glb_candidate'] = GLB_QA

QA['limits'] = ['Provisional local coordinates; no collision or canonical placement.', 'Roots/twigs procedural (swept tubes) with photo bark + moss box projection; scenic, not physics.',
                'Sky metrics geometry-only alpha at 50%/8 spp, atmosphere off.', 'Impostors ambient-lit albedo approximation; LOD error values estimated.', 'G4 NOT_RUN.']
QA['outputs'] = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.suffix in ('.blend', '.png', '.glb')}
QA['secs'] = round(time.time() - T0, 1)
(out / 'v80_qa.json').write_text(json.dumps(QA, indent=1) + '\n')
print('V80_DONE', QA['secs'])

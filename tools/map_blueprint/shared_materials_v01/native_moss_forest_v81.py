"""V81 moss forest: rune sanctuary ruin after the official 2D design, animal trail, denser understory.

Director 2026-11-27: keep raising density/quality; the way is rarely travelled -> animal trail, not a kept road;
ruins follow the 2D official design (assets/images/environments/moss_ancient_altar_idle_v1.png, ruin kit in
docs/art/reference/moss/05_asset_sheets.png). Built on SHA-locked V80 native.
Usage: blender -b --factory-startup --python native_moss_forest_v81.py -- V80.blend OUT [--v80-renders DIR] [--ref PNG] [--preview] [--no-render] [--stage build|full]
Isolated candidate: provisional local coordinates, no collision/canonical placement/adoption.
"""
import bpy, bmesh, sys, math, hashlib, json, random, time
from pathlib import Path
from array import array
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
src, out = Path(argv[0]), Path(argv[1])
OPT = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
STAGE = OPT('--stage', 'full'); RENDER = '--no-render' not in argv; PREVIEW = '--preview' in argv
V80R = Path(OPT('--v80-renders')) if OPT('--v80-renders') else None
REF = Path(OPT('--ref')) if OPT('--ref') else None
out.mkdir(parents=True, exist_ok=True); T0 = time.time()


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


LOCK = 'af0f7d08af9ca52eefb5e3538d5ad79e71f915070ceb488ecfb9a62de6a4a155'      # V80 artifact 15101780672 native
REF_SHA = None
assert bpy.app.version[:3] == (5, 3, 0)
assert sha(src) == LOCK, 'V80 source SHA mismatch'
if REF:
    REF_SHA = sha(REF)
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()))
scene = bpy.context.scene
rng = random.Random(20261127081)


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
                             digest(m.polygons, 'material_index', len(m.polygons), 'i'))
        result[o.name] = (cache[m.name], tuple(tuple(r) for r in o.matrix_world), o.hide_render)
    return result


old = snap()
QA = dict(status='V81_MOSS_FOREST_CANDIDATE', source='V80 native', source_sha256=LOCK, blender=bpy.app.version_string,
          design_reference=dict(path='assets/images/environments/moss_ancient_altar_idle_v1.png', sha256=REF_SHA, kit='docs/art/reference/moss/05_asset_sheets.png'))

# ---------------------------------------------------------------- anchors (identical to V79/V80)
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


# ================================================================ materials
def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); b = nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(b.outputs[0], o.inputs[0]); return m, nt, b


def ruin_stone_material():
    m, nt, b = node_mat('V81_ruin_stone'); N = nt.nodes; L = nt.links
    uv = N.new('ShaderNodeUVMap'); uv.uv_map = 'UVMap'

    def tex(name, nc=False):
        t = N.new('ShaderNodeTexImage'); t.image = bpy.data.images[name]
        if nc:
            t.image.colorspace_settings.name = 'Non-Color'
        L.new(uv.outputs[0], t.inputs['Vector']); return t
    d = tex('rock_moss_set_01_diff.001'); n = tex('rock_moss_set_01_nor_gl.001', True); r = tex('rock_moss_set_01_rough.001', True)
    grey = N.new('ShaderNodeHueSaturation'); grey.inputs['Saturation'].default_value = .3; grey.inputs['Value'].default_value = 2.0; L.new(d.outputs['Color'], grey.inputs['Color'])
    att = N.new('ShaderNodeAttribute'); att.attribute_name = 'blk'; att.attribute_type = 'GEOMETRY'
    var = N.new('ShaderNodeMapRange'); var.inputs['To Min'].default_value = .86; var.inputs['To Max'].default_value = 1.08; L.new(att.outputs['Fac'], var.inputs['Value'])
    tint = N.new('ShaderNodeMix'); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'; tint.inputs['Factor'].default_value = 1
    cc = N.new('ShaderNodeCombineColor'); [L.new(var.outputs[0], cc.inputs[i]) for i in range(3)]
    L.new(grey.outputs[0], tint.inputs['A']); L.new(cc.outputs[0], tint.inputs['B'])
    ao = N.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value = .18; ao.samples = 8
    aom = N.new('ShaderNodeMapRange'); aom.inputs['To Min'].default_value = .8; L.new(ao.outputs['AO'], aom.inputs['Value'])
    cav = N.new('ShaderNodeMix'); cav.data_type = 'RGBA'; cav.blend_type = 'MULTIPLY'; cav.inputs['Factor'].default_value = 1
    cc2 = N.new('ShaderNodeCombineColor'); [L.new(aom.outputs[0], cc2.inputs[i]) for i in range(3)]
    L.new(tint.outputs['Result'], cav.inputs['A']); L.new(cc2.outputs[0], cav.inputs['B'])
    geo = N.new('ShaderNodeNewGeometry'); sp = N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Normal'], sp.inputs[0])
    up = N.new('ShaderNodeMapRange'); up.inputs['From Min'].default_value = .5; up.inputs['From Max'].default_value = .85; L.new(sp.outputs['Z'], up.inputs['Value'])
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.2; nz.inputs['Detail'].default_value = 6; L.new(geo.outputs['Position'], nz.inputs['Vector'])
    nm = N.new('ShaderNodeMapRange'); nm.inputs['From Min'].default_value = .42; nm.inputs['From Max'].default_value = .58; L.new(nz.outputs['Fac'], nm.inputs['Value'])
    low = N.new('ShaderNodeMapRange'); low.inputs['From Min'].default_value = .62; low.inputs['From Max'].default_value = .3; L.new(geo.outputs['Position'], low.inputs['Value'])
    hz = N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Position'], hz.inputs[0])
    mo = N.new('ShaderNodeMath'); mo.operation = 'MULTIPLY'; L.new(up.outputs[0], mo.inputs[0]); L.new(nm.outputs[0], mo.inputs[1])
    side = N.new('ShaderNodeMapRange'); side.inputs['From Min'].default_value = .6; side.inputs['From Max'].default_value = .75
    nz2 = N.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = 1.1; nz2.inputs['Detail'].default_value = 4; L.new(geo.outputs['Position'], nz2.inputs['Vector']); L.new(nz2.outputs['Fac'], side.inputs['Value'])
    mx = N.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'; L.new(mo.outputs[0], mx.inputs[0]); L.new(side.outputs[0], mx.inputs[1])
    mt = N.new('ShaderNodeTexImage'); mt.image = bpy.data.images['moss_tile_basecolor']; L.new(uv.outputs[0], mt.inputs['Vector'])
    mhs = N.new('ShaderNodeHueSaturation'); mhs.inputs['Value'].default_value = .78; L.new(mt.outputs['Color'], mhs.inputs['Color'])
    fin = N.new('ShaderNodeMix'); fin.data_type = 'RGBA'; L.new(mx.outputs[0], fin.inputs['Factor']); L.new(cav.outputs['Result'], fin.inputs['A']); L.new(mhs.outputs[0], fin.inputs['B'])
    L.new(fin.outputs['Result'], b.inputs['Base Color'])
    sr = N.new('ShaderNodeSeparateColor'); L.new(r.outputs['Color'], sr.inputs[0])
    rr = N.new('ShaderNodeMix'); rr.data_type = 'FLOAT'; L.new(mx.outputs[0], rr.inputs['Factor']); L.new(sr.outputs['Red'], rr.inputs['A']); rr.inputs['B'].default_value = .92; L.new(rr.outputs['Result'], b.inputs['Roughness'])
    nmap = N.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = 1.3; L.new(n.outputs['Color'], nmap.inputs['Color']); L.new(nmap.outputs[0], b.inputs['Normal'])
    b.inputs['Specular IOR Level'].default_value = .35
    return m


def rune_material():
    m, nt, b = node_mat('V81_rune_glow')
    b.inputs['Base Color'].default_value = (.55, .75, .85, 1); b.inputs['Roughness'].default_value = .4
    b.inputs['Emission Color'].default_value = (.38, .74, 1.0, 1); b.inputs['Emission Strength'].default_value = .9
    return m


def flower_material():
    m, nt, b = node_mat('V81_white_flower'); N = nt.nodes; L = nt.links
    att = N.new('ShaderNodeAttribute'); att.attribute_name = 'part'; att.attribute_type = 'GEOMETRY'
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; L.new(att.outputs['Fac'], mx.inputs['Factor'])
    mx.inputs['A'].default_value = (.86, .88, .84, 1); mx.inputs['B'].default_value = (.85, .66, .18, 1)
    L.new(mx.outputs['Result'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = .6
    b.inputs['Subsurface Weight'].default_value = .2; b.inputs['Transmission Weight'].default_value = .15
    return m


def mushroom_material():
    m, nt, b = node_mat('V81_mushroom'); N = nt.nodes; L = nt.links
    att = N.new('ShaderNodeAttribute'); att.attribute_name = 'part'; att.attribute_type = 'GEOMETRY'
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; L.new(att.outputs['Fac'], mx.inputs['Factor'])
    mx.inputs['A'].default_value = (.78, .72, .6, 1); mx.inputs['B'].default_value = (.42, .22, .1, 1)
    L.new(mx.outputs['Result'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = .55; b.inputs['Subsurface Weight'].default_value = .15
    return m


STONE = ruin_stone_material(); RUNE = rune_material(); FLOWER = flower_material(); MUSH = mushroom_material()
WOOD = bpy.data.materials['V80_mossy_root_bark']


# ================================================================ masonry builder (bmesh, chamfered blocks, per-block random attribute, cube UVs)
class Mason:
    def __init__(self):
        self.bm = bmesh.new(); self.blk = self.bm.faces.layers.float.new('blk'); self.n = 0; self.glow = []

    def _tag(self, faces, mat=0):
        r = rng.random()
        for f in faces:
            f[self.blk] = r; f.material_index = mat
        self.n += 1

    def box(self, centre, w, d, h, yaw=0., tilt=(0., 0.), bevel=.035, mat=0):
        before = set(self.bm.faces)
        M = Matrix.Translation(centre) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(tilt[0], 4, 'X') @ Matrix.Rotation(tilt[1], 4, 'Y') @ Matrix.Diagonal((w, d, h, 1))
        res = bmesh.ops.create_cube(self.bm, size=1.0, matrix=M)
        vs = res['verts']; es = list({e for v in vs for e in v.link_edges})
        if bevel > 0:
            bmesh.ops.bevel(self.bm, geom=vs + es, offset=min(bevel, w * .3, d * .3, h * .3), offset_type='OFFSET', segments=2, profile=.5, affect='EDGES', clamp_overlap=True)
        self._tag([f for f in self.bm.faces if f not in before], mat)

    def sector(self, r0, r1, a0, a1, z0, z1, mat=0, seg=6):
        """Annular sector block in the ruin frame (angles from the front direction)."""
        before = set(self.bm.faces); ring = []
        for zz in (z0, z1):
            for rr in (r0, r1):
                row = []
                for i in range(seg + 1):
                    a = a0 + (a1 - a0) * i / seg; p = C0 + FD * math.cos(a) * rr + FDP * math.sin(a) * rr
                    row.append(self.bm.verts.new((p.x, p.y, zz)))
                ring.append(row)
        bi, bo, ti, to = ring
        F = self.bm.faces.new
        for i in range(seg):
            F((ti[i], to[i], to[i + 1], ti[i + 1])); F((bi[i + 1], bo[i + 1], bo[i], bi[i]))
            F((bo[i], bo[i + 1], to[i + 1], to[i])); F((bi[i + 1], bi[i], ti[i], ti[i + 1]))
        F((bi[0], bo[0], to[0], ti[0])); F((bo[-1], bi[-1], ti[-1], to[-1]))
        new = [f for f in self.bm.faces if f not in before]
        es = list({e for f in new for e in f.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > .6})
        try:
            bmesh.ops.bevel(self.bm, geom=es, offset=.025, offset_type='OFFSET', segments=2, profile=.5, affect='EDGES', clamp_overlap=True)
        except Exception:
            pass
        self._tag([f for f in self.bm.faces if f not in before], mat)

    def ribbon(self, pts, width, normal, lift=.004):
        """Flat emissive strip following pts, lying on the plane with the given normal."""
        before = set(self.bm.faces); prev = None
        for k, p in enumerate(pts):
            t = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]).normalized(); s = t.cross(normal).normalized() * width / 2
            a = self.bm.verts.new(p + s + normal * lift); b = self.bm.verts.new(p - s + normal * lift)
            if prev:
                self.bm.faces.new((prev[0], prev[1], b, a))
            prev = (a, b)
        self._tag([f for f in self.bm.faces if f not in before], 1)

    def mesh(self, name):
        bm = self.bm; uvl = bm.loops.layers.uv.new('UVMap')
        for f in bm.faces:
            n = f.normal; ax = max(range(3), key=lambda i: abs(n[i])); o = f[self.blk] * 7.0
            for lp in f.loops:
                c = lp.vert.co
                u, v = ((c.y, c.z), (c.x, c.z), (c.x, c.y))[ax]
                lp[uvl].uv = (u / 1.6 + o, v / 1.6 + o * .37)
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        me.materials.append(STONE); me.materials.append(RUNE)
        for p in me.polygons:
            p.use_smooth = False
        return me


def polar(r, a):
    return C0 + FD * math.cos(a) * r + FDP * math.sin(a) * r


def circle_pts(r, z, n=96, a0=0., a1=math.tau):
    return [(lambda p: Vector((p.x, p.y, z)))(polar(r, a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


ruin = bpy.data.collections.new('V81_RUNE_SANCTUARY'); scene.collection.children.link(ruin)
R_PLAT, R_RIM = 4.25, 4.55
gz = [ground(*polar(r, a)) for r in (0, 1.5, 3, 4.6) for a in [i * math.tau / 16 for i in range(16)]]
gz = [g for g in gz if g is not None]
T = max(gz) + .32; BASE = min(gz) - .45
QA['ruin_frame'] = dict(centre=[round(C0.x, 3), round(C0.y, 3)], front_dir=[round(FD.x, 4), round(FD.y, 4)], platform_top=round(T, 3), ground_min=round(min(gz), 3), ground_max=round(max(gz), 3),
                        note='dimensions authored from 2D proportions (estimate): rune disc r2.45, platform r4.25, 3 front steps, 12 posts, stele 4.3 m')

# ---- platform: substrate, radial flagstones, raised curb, rune inlay
P = Mason()
P.sector(0, R_PLAT - .02, -math.pi, math.pi, BASE, T - .035, seg=48)          # top face = mossy grout between slabs
P.box(Vector((C0.x, C0.y, T - .07)), 1.3, 1.3, .16, yaw=math.radians(45), bevel=.03)       # centre stone
for (r0, r1, n) in ((.72, 1.62, 8), (1.62, 2.6, 14), (2.6, 3.45, 20), (3.45, R_PLAT, 26)):
    off = rng.uniform(0, math.tau)
    for i in range(n):
        a0 = off + math.tau * i / n + .006; a1 = off + math.tau * (i + 1) / n - .006
        if r0 >= 2.6 and rng.random() < .03:
            continue                                                                       # missing slab (moss shows)
        dz = rng.uniform(-.015, .008) if r0 < 2.6 else rng.uniform(-.035, .012)
        P.sector(r0 + .015, r1 - .015, a0, a1, T - .2 + dz, T + dz, seg=4)
STEP_SPAN = math.radians(34)
for i in range(30):
    a0 = -math.pi + math.tau * i / 30 + .01; a1 = -math.pi + math.tau * (i + 1) / 30 - .01
    am = (a0 + a1) / 2
    if abs(am) < STEP_SPAN or rng.random() < .1:
        continue
    P.sector(R_PLAT, R_RIM, a0, a1, T - .25, T + .1 + rng.uniform(-.03, .03), seg=3)
for k in range(3):                                                                         # front steps (curved, masonry)
    r0 = R_PLAT + .42 * k; r1 = r0 + .44; top = T - .17 * (k + 1)
    nb = 5 + k
    for i in range(nb):
        a0 = -STEP_SPAN + 2 * STEP_SPAN * i / nb + .008; a1 = -STEP_SPAN + 2 * STEP_SPAN * (i + 1) / nb - .008
        P.sector(r0, r1, a0, a1, min(gz) - .4, top + rng.uniform(-.02, .01), seg=3)
Z = Vector((0, 0, 1)); RZ = T + .002
for rr in (2.45, 2.22, 1.36, .58):
    P.ribbon(circle_pts(rr, RZ), .05 if rr > 2 else .04, Z)
for k in range(4):
    a = k * math.pi / 2
    P.ribbon([Vector((*polar(.58, a), RZ)), Vector((*polar(2.45, a), RZ))], .045, Z)
    tip = polar(2.05, a); l = polar(1.85, a + .1); rr_ = polar(1.85, a - .1)
    P.ribbon([Vector((*l, RZ)), Vector((*tip, RZ)), Vector((*rr_, RZ))], .04, Z)             # arrowheads
for k in range(4):                                                                         # four-point star
    a = k * math.pi / 2 + math.pi / 4
    P.ribbon([Vector((*polar(.0, 0), RZ)), Vector((*polar(1.05, a), RZ))], .03, Z)
for k in range(32):                                                                        # glyph dashes between rings
    a = math.tau * k / 32
    P.ribbon([Vector((*polar(2.27, a), RZ)), Vector((*polar(2.4, a + .03 * (1 if k % 2 else -1)), RZ))], .03, Z)
plat_me = P.mesh('V81_ruin_platform'); plat = bpy.data.objects.new('V81_ruin_platform', plat_me); ruin.objects.link(plat)

# ---- ring posts with rune slots
S = Mason(); POSTS = []
for deg in (42, 66, 90, 114, 138, 162):
    for sgn in (1, -1):
        a = math.radians(deg) * sgn; p = polar(4.02, a); h = rng.uniform(1.05, 1.32); broken = rng.random() < .22
        if broken:
            h = rng.uniform(.5, .75)
        tilt = (math.radians(rng.uniform(-6, 6)), math.radians(rng.uniform(-6, 6))) if rng.random() < .25 else (0, 0)
        yaw = math.atan2((C0 - p).y, (C0 - p).x)
        S.box(Vector((p.x, p.y, T - .05 + h / 2)), .44, .48, h + .1, yaw, tilt, .04)
        if not broken:
            S.box(Vector((p.x, p.y, T + h + .02)), .52, .56, .1, yaw, tilt, .025)                       # cap stone
            inward = (C0 - p).normalized().to_3d()
            for face in (inward, -inward):
                base = Vector((p.x, p.y, 0)) + face * .245
                S.ribbon([Vector((base.x, base.y, T + .25)), Vector((base.x, base.y, T + h - .18))], .055, face, .006)
                S.ribbon([Vector((base.x, base.y, T + h - .48)) + Vector((-face.y, face.x, 0)) * .09, Vector((base.x, base.y, T + h - .38)), Vector((base.x, base.y, T + h - .48)) - Vector((-face.y, face.x, 0)) * .09], .035, face, .006)
        POSTS.append(dict(angle_deg=round(math.degrees(a), 1), height=round(h, 2), broken=broken))
posts = bpy.data.objects.new('V81_ruin_posts', S.mesh('V81_ruin_posts')); ruin.objects.link(posts)

# ---- back crescent: central rune stele, tall pillars, arched niches, broken walls (stacked ashlar)
W = Mason()


def course_wall(centre2, tangent, width, depth, height, gz0, ragged=.6, opening=None):
    """Ashlar courses along the tangent; opening=(width, spring) leaves an arch void handled by arch()."""
    z = gz0; course = 0
    while z < gz0 + height - .05:
        hh = rng.uniform(.3, .42); x = -width / 2 + (.25 if course % 2 else 0) - .25
        top_limit = gz0 + height - (rng.uniform(0, ragged * 1.6) if z > gz0 + height - ragged * 2 else 0)
        while x < width / 2:
            ln = rng.uniform(.45, .8); x0 = max(x, -width / 2); x1 = min(x + ln, width / 2); x = x + ln + .02
            if x1 - x0 < .18:
                continue
            xm = (x0 + x1) / 2
            if opening and abs(xm) < opening[0] / 2 + .05 and z < gz0 + opening[1] + opening[0] / 2:
                continue
            if z + hh > top_limit and rng.random() < .55:
                continue
            c = centre2 + tangent * xm
            W.box(Vector((c.x, c.y, z + hh / 2)), x1 - x0 - .02, depth * rng.uniform(.94, 1.0), hh - .02, math.atan2(tangent.y, tangent.x), bevel=.04)
        z += hh; course += 1


def arch(centre2, tangent, span, spring, depth, gz0, n=9):
    r_in = span / 2; r_out = r_in + .42
    for i in range(n):
        a0 = math.pi * i / n + .02; a1 = math.pi * (i + 1) / n - .02; am = (a0 + a1) / 2
        rm = (r_in + r_out) / 2; c = centre2 + tangent * (math.cos(am) * rm)
        W.box(Vector((c.x, c.y, gz0 + spring + math.sin(am) * rm)), .4, depth, (r_out - r_in) * .98, math.atan2(tangent.y, tangent.x), (0., -(am - math.pi / 2)), .035)


STRUCT = []
for deg, kind in ((180, 'stele'), (156, 'pillar'), (-156, 'pillar'), (128, 'niche'), (-128, 'niche'), (104, 'wall'), (-104, 'wall')):
    a = math.radians(deg); p = polar(5.85 if kind != 'stele' else 5.5, a); g = ground(p.x, p.y); g0 = min(g, T) - .25
    tangent = Vector((-(C0 - p).y, (C0 - p).x)).normalized(); inward = (C0 - p).normalized().to_3d()
    if kind == 'stele':
        W.box(Vector((p.x, p.y, g0 + .22)), 1.55, 1.0, .5, math.atan2(tangent.y, tangent.x), bevel=.05)
        W.box(Vector((p.x, p.y, g0 + .45 + 2.15)), 1.0, .56, 4.3, math.atan2(tangent.y, tangent.x), (math.radians(-2), 0), .07)
        f = Vector((p.x, p.y, 0)) + inward * .29; zc = g0 + .45 + 3.0; t3 = tangent.to_3d()
        W.ribbon([Vector((f.x, f.y, g0 + 1.1)), Vector((f.x, f.y, g0 + 4.1))], .07, inward, .008)
        W.ribbon([Vector((f.x, f.y, zc)) + (t3 * math.cos(q) + Z * math.sin(q)) * .34 for q in [i * math.tau / 40 for i in range(41)]], .055, inward, .008)
        W.ribbon([Vector((f.x, f.y, g0 + 1.55)) + t3 * .26, Vector((f.x, f.y, g0 + 1.15)), Vector((f.x, f.y, g0 + 1.55)) - t3 * .26], .055, inward, .008)
        W.ribbon([Vector((f.x, f.y, zc + .62)) + t3 * .2, Vector((f.x, f.y, zc + .62)) - t3 * .2], .05, inward, .008)
        STRUCT.append(dict(kind=kind, angle_deg=deg, height=4.75))
    elif kind == 'pillar':
        h = rng.uniform(3.0, 3.5); z = g0
        while z < g0 + h:
            hh = rng.uniform(.45, .6); yaw = math.atan2(tangent.y, tangent.x) + rng.uniform(-.05, .05)
            if z + hh > g0 + h:
                W.box(Vector((p.x, p.y, z + hh / 2)), .74, .74, hh, yaw + .3, (rng.uniform(-.2, .2), rng.uniform(-.15, .15)), .05); break
            W.box(Vector((p.x, p.y, z + hh / 2)), .8, .8, hh - .02, yaw, bevel=.05); z += hh
        f = Vector((p.x, p.y, 0)) + inward * .41
        W.ribbon([Vector((f.x, f.y, g0 + 1.0)), Vector((f.x, f.y, g0 + 2.4))], .06, inward, .008)
        STRUCT.append(dict(kind=kind, angle_deg=deg, height=round(h, 2)))
    elif kind == 'niche':
        course_wall(p, tangent, 2.7, .7, 3.6, g0, .5, opening=(1.3, 1.9)); arch(p, tangent, 1.3, 1.9, .72, g0)
        STRUCT.append(dict(kind=kind, angle_deg=deg, height=3.6, opening='1.3 x 2.55 m round arch'))
    else:
        h = rng.uniform(1.3, 2.1); course_wall(p, tangent, 2.0, .62, h, g0, .7)
        STRUCT.append(dict(kind=kind, angle_deg=deg, height=round(h, 2)))
backs = bpy.data.objects.new('V81_ruin_back', W.mesh('V81_ruin_back')); ruin.objects.link(backs)

# ---- rubble and fallen carved blocks
Rb = Mason(); rub = 0
for i in range(300):
    if rub >= 34:
        break
    a = rng.uniform(-math.pi, math.pi)
    if abs(a) < STEP_SPAN + .25:
        continue
    r = rng.uniform(4.7, 7.4); p = polar(r, a); g = ground(p.x, p.y)
    if g is None:
        continue
    s = rng.uniform(.32, .72); h = s * rng.uniform(.5, .8)
    Rb.box(Vector((p.x, p.y, g + h * rng.uniform(.05, .35))), s, s * rng.uniform(.6, 1.0), h, rng.uniform(0, math.tau), (rng.uniform(-.3, .3), rng.uniform(-.3, .3)), .05); rub += 1
rubble = bpy.data.objects.new('V81_ruin_rubble', Rb.mesh('V81_ruin_rubble')); ruin.objects.link(rubble)
for o in ruin.objects:
    o['scenic_only'] = True

# ---- ivy strands draped from the tops of the stele, pillars, niche walls and some posts (alpha leaf cards)
def ivy_material():
    m, nt, b = node_mat('V81_ivy'); N = nt.nodes; L = nt.links
    t = N.new('ShaderNodeTexImage'); t.image = bpy.data.images['leaf_cluster_beech_basecolor']
    hs = N.new('ShaderNodeHueSaturation'); hs.inputs['Hue'].default_value = .52; hs.inputs['Value'].default_value = .62; hs.inputs['Saturation'].default_value = 1.1
    L.new(t.outputs['Color'], hs.inputs['Color']); L.new(hs.outputs[0], b.inputs['Base Color']); L.new(t.outputs['Alpha'], b.inputs['Alpha'])
    nm = N.new('ShaderNodeTexImage'); nm.image = bpy.data.images['leaf_cluster_beech_normal']; nn = N.new('ShaderNodeNormalMap'); L.new(nm.outputs['Color'], nn.inputs['Color']); L.new(nn.outputs[0], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = .55; b.inputs['Transmission Weight'].default_value = .1
    return m


IVY = ivy_material(); ib = bmesh.new(); iuv = ib.loops.layers.uv.new('UVMap'); IVY_N = 0


def ivy_strand(top, normal, tangent, length):
    global IVY_N
    pos = top.copy(); sway = rng.uniform(0, math.tau)
    while (top - pos).length < length:
        sz = rng.uniform(.2, .34); ang = rng.uniform(-.8, .8)
        ax = (tangent * math.cos(ang) + Z * math.sin(ang)).normalized(); ay = normal.cross(ax).normalized()
        c = pos + normal * rng.uniform(.03, .09) + tangent * math.sin(sway) * .08
        out_t = normal * rng.uniform(.0, .12)
        vs = [ib.verts.new(c + (-ax - ay) * sz / 2), ib.verts.new(c + (ax - ay) * sz / 2 + out_t), ib.verts.new(c + (ax + ay) * sz / 2 + out_t), ib.verts.new(c + (-ax + ay) * sz / 2)]
        f = ib.faces.new(vs)
        for lp, uv_ in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            lp[iuv].uv = uv_
        pos += Vector((0, 0, -rng.uniform(.11, .18))) + tangent * rng.uniform(-.05, .05); sway += .7; IVY_N += 1


for st in [x for x in STRUCT]:
    a = math.radians(st['angle_deg']); p = polar(5.85 if st['kind'] != 'stele' else 5.5, a); g0 = min(ground(p.x, p.y), T) - .25
    inward = (C0 - p).normalized().to_3d(); tangent = Vector((-inward.y, inward.x, 0))
    half = {'stele': .5, 'pillar': .4, 'niche': 1.35, 'wall': 1.0}[st['kind']]; depth = {'stele': .28, 'pillar': .4, 'niche': .36, 'wall': .31}[st['kind']]
    top = g0 + (st['height'] + (.45 if st['kind'] == 'stele' else 0) if st['kind'] != 'niche' else 3.3)
    for k in range(rng.randint(3, 6) if st['kind'] != 'wall' else rng.randint(1, 3)):
        side_ = rng.uniform(-half, half); face = rng.choice((inward, inward, -inward, tangent if side_ > 0 else -tangent))
        o_ = Vector((p.x, p.y, top)) + face * depth + tangent * (side_ if abs(face.dot(tangent)) < .5 else 0) + (tangent * half if face.dot(tangent) > .5 else (-tangent * half if face.dot(tangent) < -.5 else Vector()))
        ivy_strand(o_, face, Vector((-face.y, face.x, 0)).normalized() if face.to_2d().length > .1 else tangent, rng.uniform(.8, min(2.8, st['height'] * .8)))
for pst in POSTS:
    if pst['broken'] or rng.random() < .55:
        continue
    a = math.radians(pst['angle_deg']); p = polar(4.02, a); face = (p - C0).normalized().to_3d() if rng.random() < .5 else (C0 - p).normalized().to_3d()
    ivy_strand(Vector((p.x, p.y, T + pst['height'])) + face * .25, face, Vector((-face.y, face.x, 0)), rng.uniform(.4, .9))
ime = bpy.data.meshes.new('V81_ruin_ivy'); ib.to_mesh(ime); ib.free(); ime.materials.append(IVY)
ivy = bpy.data.objects.new('V81_ruin_ivy', ime); ruin.objects.link(ivy); ivy['scenic_only'] = True
QA['ruin_ivy_cards'] = IVY_N

# ---- hide the V57 proxy altar/arch (geometry untouched; reversible flag)
PROXY = [o for o in scene.objects if o.name.startswith(('V57_ALTAR_PROXY', 'V57_ARCH_PROXY'))]
for o in PROXY:
    o.hide_render = True; o.hide_viewport = True
QA['v57_proxy_hidden'] = sorted(o.name for o in PROXY)
bpy.context.view_layer.update()
RUIN_BVH = world_bvh([plat, posts, backs])
ruin_tris = 0
for o in ruin.objects:
    o.data.calc_loop_triangles(); ruin_tris += len(o.data.loop_triangles)
QA['ruin'] = dict(objects=len(ruin.objects), triangles=ruin_tris, posts=POSTS, back_structures=STRUCT, rubble_blocks=rub,
                  blocks=dict(platform=P.n, posts=S.n, back=W.n, rubble=Rb.n), materials=['V81_ruin_stone (rock_moss_set_01 photo maps, desaturated + per-block variation + AO cavity + moss)', 'V81_rune_glow'])
print('V81_RUIN', json.dumps({k: v for k, v in QA['ruin'].items() if k in ('objects', 'triangles', 'blocks', 'rubble_blocks')}))


# ================================================================ roots weaving through the ruin (from the nearest oaks behind it)
def tube_mesh(name, rings, sides=8, vsc=None):
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); verts = []; vlen = 0.
    for k, (c, r) in enumerate(rings):
        t = (rings[min(k + 1, len(rings) - 1)][0] - rings[max(k - 1, 0)][0]).normalized(); a = t.cross(Z)
        if a.length < 1e-4:
            a = Vector((1, 0, 0))
        a.normalize(); b = t.cross(a); vs = vsc[k] if vsc else .85
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
    return me


def surface_z(x, y):
    g = ground(x, y) or T
    hit = RUIN_BVH.ray_cast(Vector((x, y, T + 12)), Vector((0, 0, -1)), 30)
    return max(g, hit[0].z) if hit[0] else g


oaks = [o for o in scene.objects if o.type == 'MESH' and o.data.name == 'island_trees_01_blockout_cleaned' and o.visible_get()]
behind = sorted(oaks, key=lambda o: (o.matrix_world.translation.to_2d() - C0).length)
ROOTS = []; rparts = []
for o in behind[:6]:
    b2 = o.matrix_world.translation.to_2d(); dist = (b2 - C0).length
    if dist > 17 or dist < 7:
        continue
    for k in range(rng.randint(1, 2)):
        tgt_a = math.atan2(*reversed(tuple(b2 - C0))) + rng.uniform(-.35, .35)
        end = C0 + Vector((math.cos(tgt_a), math.sin(tgt_a))) * rng.uniform(3.3, 4.4)
        st = b2 + (C0 - b2).normalized() * 1.6; rings = []; n = 18; r0 = rng.uniform(.18, .27)
        side = Vector((-(end - st).y, (end - st).x)).normalized(); ph = rng.uniform(0, math.tau)
        for i in range(n + 1):
            t = i / n; q = st.lerp(end, t) + side * math.sin(ph + t * 5) * .5 * math.sin(math.pi * t)
            rad = r0 * (1 - .7 * t) + .03
            rings.append((Vector((q.x, q.y, surface_z(q.x, q.y) + rad * .55 - (.25 if t > .93 else 0))), rad))
        rparts.append(tube_mesh('rr', rings, 8, [1.25 - .4 * (i / n) for i in range(n + 1)])); ROOTS.append(dict(tree=o.name, length=round((end - st).length, 2)))
if rparts:
    bm = bmesh.new()
    for me in rparts:
        bm.from_mesh(me); bpy.data.meshes.remove(me)
    rme = bpy.data.meshes.new('V81_ruin_roots'); bm.to_mesh(rme); bm.free(); rme.materials.append(WOOD)
    ro = bpy.data.objects.new('V81_ruin_roots', rme); ruin.objects.link(ro); ro['scenic_only'] = True
QA['ruin']['weaving_roots'] = ROOTS


# ================================================================ small procedural flora: white star flowers, mushrooms
def flower_mesh():
    bm = bmesh.new(); part = bm.faces.layers.float.new('part'); uvl = bm.loops.layers.uv.new('UVMap')
    for k in range(5):
        a = k * math.tau / 5; d = Vector((math.cos(a), math.sin(a), 0))
        s_ = Vector((-d.y, d.x, 0)); h = .095
        vs = [bm.verts.new(Vector((0, 0, h)) + s_ * .004), bm.verts.new(Vector((0, 0, h)) + d * .022 + s_ * .009 + Vector((0, 0, .004))),
              bm.verts.new(Vector((0, 0, h)) + d * .03 + Vector((0, 0, .002))), bm.verts.new(Vector((0, 0, h)) + d * .022 - s_ * .009 + Vector((0, 0, .004))), bm.verts.new(Vector((0, 0, h)) - s_ * .004)]
        f = bm.faces.new(vs); f[part] = 0.
    c = [bm.verts.new(Vector((math.cos(q) * .006, math.sin(q) * .006, .1))) for q in [i * math.tau / 6 for i in range(6)]]
    f = bm.faces.new(c); f[part] = 1.
    st = [bm.verts.new(Vector((.0015, 0, 0))), bm.verts.new(Vector((-.0015, 0, 0))), bm.verts.new(Vector((-.0015, 0, .095))), bm.verts.new(Vector((.0015, 0, .095)))]
    f = bm.faces.new(st); f[part] = .55
    for f in bm.faces:
        for lp in f.loops:
            lp[uvl].uv = (lp.vert.co.x * 10 + .5, lp.vert.co.y * 10 + .5)
    me = bpy.data.meshes.new('V81_white_flower'); bm.to_mesh(me); bm.free(); me.materials.append(FLOWER); return me


def mushroom_mesh(i):
    rr = random.Random(700 + i); bm = bmesh.new(); part = bm.faces.layers.float.new('part'); uvl = bm.loops.layers.uv.new('UVMap')
    for k in range(rr.randint(3, 6)):
        off = Vector((rr.uniform(-.07, .07), rr.uniform(-.07, .07), 0)); h = rr.uniform(.04, .11); cr = rr.uniform(.018, .042)
        before = set(bm.faces)
        bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=cr * .28, radius2=cr * .22, depth=h, matrix=Matrix.Translation(off + Vector((0, 0, h / 2))))
        for f in set(bm.faces) - before:
            f[part] = 0.
        before = set(bm.faces)
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=5, radius=cr, matrix=Matrix.Translation(off + Vector((0, 0, h))) @ Matrix.Diagonal((1, 1, .55, 1)))
        for f in set(bm.faces) - before:
            f[part] = 1. if f.calc_center_median().z > off.z + h - cr * .05 else 0.
    for f in bm.faces:
        for lp in f.loops:
            lp[uvl].uv = (lp.vert.co.x * 6 + .5, lp.vert.co.z * 6)
    me = bpy.data.meshes.new('V81_mushroom_%d' % i); bm.to_mesh(me); bm.free(); me.materials.append(MUSH); return me


FLOWER_ME = flower_mesh(); MUSH_ME = [mushroom_mesh(i) for i in range(4)]
fcoll = bpy.data.collections.new('V81_TRAIL_AND_UNDERSTORY'); scene.collection.children.link(fcoll)
ADD = {}


def put(me, x, y, yaw, scale, kind, sink=.01):
    z = ground(x, y)
    hit = RUIN_BVH.ray_cast(Vector((x, y, T + 12)), Vector((0, 0, -1)), 30)
    if hit[0] and hit[0].z > (z or -1e9):
        z = hit[0].z
    if z is None:
        return None
    o = bpy.data.objects.new('V81_%s_%05d' % (kind, sum(ADD.values())), me); fcoll.objects.link(o)
    o.matrix_world = Matrix.Translation(Vector((x, y, z - sink))) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Scale(scale, 4)
    o['scenic_only'] = True; ADD[kind] = ADD.get(kind, 0) + 1; return o


# flowers: clusters at post bases, step cheeks, ruin rim, trail edges
for i in range(240):
    a = rng.uniform(-math.pi, math.pi); r = rng.choice((rng.uniform(4.4, 5.4), rng.uniform(3.7, 4.3), rng.uniform(5.4, 8.5)))
    c = polar(r, a)
    for j in range(rng.randint(4, 11)):
        q = c + Vector((rng.gauss(0, .18), rng.gauss(0, .18)))
        if abs(math.atan2(*reversed(tuple(q - C0)))) < 0 and False:
            continue
        if (q - C0).length < 2.7:
            continue
        put(FLOWER_ME, q.x, q.y, rng.uniform(0, math.tau), rng.uniform(.8, 1.35), 'flower')


# ================================================================ animal trail in the floor shader (replaces the wide worn road)
def trail_floor():
    m = terrain.data.materials[0].copy(); m.name = 'V81_forest_floor_trail'; nt = m.node_tree; N = nt.nodes; L = nt.links
    path = [n for n in N if n.type == 'MAP_RANGE' and abs(n.inputs['From Min'].default_value - 4.2) < 1e-4][0]
    edge = [n for n in N if n.type == 'MAP_RANGE' and abs(n.inputs['From Min'].default_value - 3.6) < 1e-4][0]
    geo = N.new('ShaderNodeNewGeometry')

    def M(op, a, b=None, c=None):
        n = N.new('ShaderNodeMath'); n.operation = op
        for i, x in enumerate((a, b, c)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                L.new(x, n.inputs[i])
        return n.outputs[0]
    sep = N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Position'], sep.inputs[0])
    px = M('SUBTRACT', sep.outputs[0], A_.x); py = M('SUBTRACT', sep.outputs[1], A_.y)
    a = M('ADD', M('MULTIPLY', px, U.x), M('MULTIPLY', py, U.y)); s_ = M('ADD', M('MULTIPLY', px, N_.x), M('MULTIPLY', py, N_.y))
    fade = M('MINIMUM', M('MAXIMUM', M('DIVIDE', M('SUBTRACT', LEN, a), 9.0), 0.0), 1.0)
    mea = M('MULTIPLY', M('ADD', M('MULTIPLY', M('SINE', M('MULTIPLY', a, .23)), 1.1), M('MULTIPLY', M('SINE', M('ADD', M('MULTIPLY', a, .61), 1.3)), .5)), fade)
    d = M('ABSOLUTE', M('SUBTRACT', s_, mea))
    db = M('SQRT', M('ADD', M('POWER', M('SUBTRACT', sep.outputs[0], B_.x), 2), M('POWER', M('SUBTRACT', sep.outputs[1], B_.y), 2)))
    past = M('GREATER_THAN', a, LEN)
    dfin = M('ADD', M('MULTIPLY', d, M('SUBTRACT', 1.0, past)), M('MULTIPLY', db, past))
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = .6; nz.inputs['Detail'].default_value = 3; L.new(geo.outputs['Position'], nz.inputs['Vector'])
    dw = M('ADD', dfin, M('MULTIPLY', M('SUBTRACT', nz.outputs['Fac'], .5), .55))
    nb = N.new('ShaderNodeTexNoise'); nb.inputs['Scale'].default_value = .09; nb.inputs['Detail'].default_value = 2; L.new(geo.outputs['Position'], nb.inputs['Vector'])
    brk = N.new('ShaderNodeMapRange'); brk.inputs['From Min'].default_value = .36; brk.inputs['From Max'].default_value = .46; L.new(nb.outputs['Fac'], brk.inputs['Value'])
    core = N.new('ShaderNodeMapRange'); core.inputs['From Min'].default_value = .95; core.inputs['From Max'].default_value = .3; L.new(dw, core.inputs['Value'])
    trail = M('MULTIPLY', core.outputs[0], brk.outputs[0])
    for link in list(path.outputs[0].links):
        L.new(trail, link.to_socket)
    L.new(dw, edge.inputs['Value']); edge.inputs['From Min'].default_value = .9; edge.inputs['From Max'].default_value = 2.6
    for o in (terrain, ext):
        o.data.materials[0] = m
    return m.name


QA['trail'] = dict(material=trail_floor(), model='meander 1.1 sin(.23a)+.5 sin(.61a+1.3) about the provisional route line, fades to the ruin steps; core 0.3-0.95 m (+-0.27 m noise), ~25% overgrown breaks',
                   walkable_clear_core_m=.75, replaced='V79/V80 5 m worn road mask')

# ================================================================ density: encroaching understory, saplings, twigs, flowers, mushrooms
TPL = {}
for o in scene.objects:
    if o.name.startswith('V79_u_'):
        k = o.name.split('_')[2]; TPL.setdefault(k, {})[o.data.name] = o
TPL = {k: list(v.values()) for k, v in TPL.items()}
HT = {'fern': (.45, 1.1), 'moss': (.1, .26), 'shrub': (.7, 1.4), 'rock': (.3, .9)}
trunks = [(o.matrix_world.translation.to_2d(), 1.3) for o in oaks] + [(o.matrix_world.translation.to_2d(), .6) for o in scene.objects if o.type == 'MESH' and o.data.name.startswith('eco_tree')]


def place_tpl(kind, x, y, trail_clear, tall=False):
    t = rng.choice(TPL[kind]); m = t.data; lin3 = t.matrix_world.to_3x3()
    pts = [lin3 @ m.vertices[i].co for i in range(0, len(m.vertices), max(1, len(m.vertices) // 300))]
    h = max(p.z for p in pts) - min(p.z for p in pts)
    fac = rng.uniform(*HT[kind]) / max(h, 1e-4) * (rng.uniform(1.4, 2.4) if kind == 'moss' else 1)
    lin = Matrix.Rotation(rng.uniform(0, math.tau), 4, 'Z') @ Matrix.Scale(fac, 4) @ lin3.to_4x4()
    pts = [lin @ m.vertices[i].co for i in range(0, len(m.vertices), max(1, len(m.vertices) // 300))]
    cx = sum(p.x for p in pts) / len(pts); cy = sum(p.y for p in pts) / len(pts); rad = max(math.hypot(p.x - cx, p.y - cy) for p in pts)
    q = Vector((x, y))
    if gap(q, trail_clear + rad * .3, tall) < 0 or any((q - c).length < r + rad * .3 for c, r in trunks):
        return None
    zmin = min(p.z for p in pts); low = [p for p in pts if p.z < zmin + .05 * max(h * fac, .2)]
    gs = [ground(x + p.x - cx, y + p.y - cy) for p in low[:12]]
    if any(g is None for g in gs):
        return None
    zz = min(g - p.z for g, p in zip(gs, low[:12])) - .01
    o = bpy.data.objects.new('V81_%s_%05d' % (kind, sum(ADD.values())), m); fcoll.objects.link(o)
    o.matrix_world = Matrix.Translation(Vector((x - cx, y - cy, zz))) @ lin; o['scenic_only'] = True; ADD[kind] = ADD.get(kind, 0) + 1
    return max(p.z + zz - g for g, p in zip(gs, low[:12]))


A_EYE = (EYE.to_2d() - A_).dot(U)
_tl = A_ + U * (LEN - 9) + N_ * meander(LEN - 9); CAM_ZONES.append(_tl); VIEW_CONES.append((_tl, C0))
FLOATS = []
TARGET = {'fern': 950, 'moss': 380, 'shrub': 90, 'rock': 45}
for i in range(16000):
    a = rng.uniform(A_EYE - 30, LEN - .5); side = rng.choice((-1, 1)); off = .8 + abs(rng.gauss(0, 1.9))
    if off > 7.5:
        continue
    p = A_ + U * a + N_ * (meander(a) + side * off)
    clump = math.sin(p.x * .9) * math.cos(p.y * .7) + math.sin((p.x + p.y) * .31)
    if clump < -.6:
        continue
    kind = rng.choices(['fern', 'moss', 'shrub', 'rock'], [7, 4, 1 if off > 1.8 else 0, .6 if off > 1.4 else 0])[0]
    if ADD.get(kind, 0) >= TARGET[kind]:
        continue
    f = place_tpl(kind, p.x, p.y, .75 if kind in ('moss', 'fern') else 1.4, tall=kind == 'shrub')
    if f is not None:
        FLOATS.append(f)
DEC = bpy.data.meshes['eco_tree_deciduous_a_LOD1_mesh']; dz = [v.co.z for v in DEC.vertices]; DEC_H = max(dz) - min(dz); sap = 0
for i in range(4000):
    if sap >= 34:
        break
    a = rng.uniform(A_EYE - 28, LEN - 4); side = rng.choice((-1, 1)); off = rng.uniform(2.3, 7.0)
    p = A_ + U * a + N_ * (meander(a) + side * off)
    if gap(p, 2.2, True) < 0 or any((p - c).length < r + 1.2 for c, r in trunks):
        continue
    h = rng.uniform(8.0, 11.0); s_ = h / DEC_H; g = ground(p.x, p.y)
    o = bpy.data.objects.new('V81_sapling_%02d' % sap, DEC); fcoll.objects.link(o)
    o.matrix_world = Matrix.Translation(Vector((p.x, p.y, g - min(dz) * s_ - .12))) @ Matrix.Rotation(rng.uniform(0, math.tau), 4, 'Z') @ Matrix.Rotation(math.radians(rng.uniform(0, 6)), 4, 'X') @ Matrix.Scale(s_, 4)
    o['scenic_only'] = True; trunks.append((p, .5)); sap += 1
ADD['sapling'] = sap
TW = [m for m in bpy.data.meshes if m.name.startswith('V80_twig_v')]
for i in range(340):
    a = rng.uniform(A_EYE - 30, LEN - 1); p = A_ + U * a + N_ * (meander(a) + rng.gauss(0, 1.4))
    if (p - C0).length < 6.5:
        continue
    put(rng.choice(TW), p.x, p.y, rng.uniform(0, math.tau), rng.uniform(.6, 1.1), 'twig', .012)
for i in range(150):
    a = rng.uniform(A_EYE - 30, LEN - 1); side = rng.choice((-1, 1)); c = A_ + U * a + N_ * (meander(a) + side * rng.uniform(.6, 2.0))
    if (c - C0).length < 6.5:
        continue
    for j in range(rng.randint(3, 9)):
        q = c + Vector((rng.gauss(0, .2), rng.gauss(0, .2)))
        if trail_dist(q) > .45:
            put(FLOWER_ME, q.x, q.y, rng.uniform(0, math.tau), rng.uniform(.8, 1.3), 'flower')
mus = 0
for c, r in trunks[:200]:
    if (c - CENTER).length > 30 or rng.random() < .45:
        continue
    a = rng.uniform(0, math.tau); q = c + Vector((math.cos(a), math.sin(a))) * (r + rng.uniform(.3, 1.4))
    if gap(q, .5) > 0 and put(rng.choice(MUSH_ME), q.x, q.y, rng.uniform(0, math.tau), rng.uniform(.8, 1.6), 'mushroom', .015):
        mus += 1
for lg in [o for o in scene.objects if o.name.startswith('V80_log')]:
    for k in range(4):
        q = lg.matrix_world.translation.to_2d() + Vector((rng.uniform(-1.5, 1.5), rng.uniform(-1.5, 1.5)))
        put(rng.choice(MUSH_ME), q.x, q.y, rng.uniform(0, math.tau), rng.uniform(.8, 1.4), 'mushroom', .015)
tri_add = 0
for o in fcoll.objects:
    o.data.calc_loop_triangles(); tri_add += len(o.data.loop_triangles)
QA['density_added'] = dict(by_kind=ADD, instances=len(fcoll.objects), triangles_instanced=tri_add, understory_float_max=round(max(FLOATS), 3) if FLOATS else None,
                           rule='trail core >=0.75 m clear for ferns/moss, >=1.4 m rocks/shrubs, >=2.2 m saplings; ruin r>=7; tall items clear of review cameras and altar sight line')
print('V81_DENSITY', json.dumps(QA['density_added']))

# ================================================================ protection: every pre-existing object exact; only V57 proxy hide flags changed
bpy.context.view_layer.update(); now = snap()
proxy_names = set(QA['v57_proxy_hidden'])
bad = [k for k, v in old.items() if (now[k][:2] != v[:2]) or (k not in proxy_names and now[k][2] != v[2])]
assert not bad, bad[:8]
QA['protected_objects_exact'] = len(old); assert sha(src) == LOCK
if STAGE == 'build':
    raise SystemExit(0)
dest = out / 'v81_moss_forest.blend'; assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()), compress=True); before = snap()
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve())); scene = bpy.context.scene; cam = scene.camera
assert snap() == before
QA['native_sha256'] = sha(dest); QA['native_bytes'] = dest.stat().st_size; QA['reopen_digest_exact'] = True
print('V81_SAVED', QA['native_sha256'])

import numpy as np


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


def tile(a, w=640, h=360):
    if a.shape[1] / a.shape[0] > w / h:                     # centre-crop to 16:9 then sample
        nw = int(a.shape[0] * w / h); x0 = (a.shape[1] - nw) // 2; a = a[:, x0:x0 + nw]
    else:
        nh = int(a.shape[1] * h / w); y0 = (a.shape[0] - nh) // 2; a = a[y0:y0 + nh]
    ys = np.linspace(0, a.shape[0] - 1, h).astype(int); xs = np.linspace(0, a.shape[1] - 1, w).astype(int); t = a[ys][:, xs].copy(); t[..., 3] = 1; return t


rd = out / 'renders'; rd.mkdir(exist_ok=True); LUM = np.array([.2126, .7152, .0722], np.float32)
if RENDER:
    vnode = scene.world.node_tree.nodes['V79_atmosphere']; vnode.mute = True; QA['sky_exposure'] = {}
    for n in ORDINARY + ['look_up']:
        set_view(n); a = load_px(render(rd / ('mask_%s_alpha.png' % n), 8, True, 50))[..., 3]
        QA['sky_exposure'][n] = dict(sky_mean=round(float((1 - a).mean()), 4), sky_top_third=round(float((1 - a)[2 * a.shape[0] // 3:].mean()), 4))
    vnode.mute = False; print('V81_SKY', json.dumps(QA['sky_exposure']))
    QA['luminance'] = {}
    for n in VIEWS:
        set_view(n); px = load_px(render(rd / ('v81_%s.png' % n), SPP)); y = px[..., :3] @ LUM
        QA['luminance'][n] = dict(mean=round(float(y.mean()), 4), p10=round(float(np.percentile(y, 10)), 4))
    print('V81_LUM', json.dumps(QA['luminance']))
    wm = bpy.data.materials.new('V81_diag_wire'); wm.use_nodes = True; n_ = wm.node_tree.nodes; l_ = wm.node_tree.links
    b_ = n_['Principled BSDF']; b_.inputs['Base Color'].default_value = (.03, .035, .04, 1)
    wf = n_.new('ShaderNodeWireframe'); wf.use_pixel_size = True; wf.inputs['Size'].default_value = .5
    em = n_.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (.55, .9, .6, 1); mx = n_.new('ShaderNodeMixShader')
    l_.new(wf.outputs[0], mx.inputs[0]); l_.new(b_.outputs[0], mx.inputs[1]); l_.new(em.outputs[0], mx.inputs[2]); l_.new(mx.outputs[0], n_['Material Output'].inputs[0])
    vnode.mute = True; scene.view_layers[0].material_override = wm; set_view('altar_front'); render(rd / 'diag_wireframe_altar_front.png', 4)
    scene.view_layers[0].material_override = None; vnode.mute = False
    white = np.ones((360, 8, 4), np.float32); hgap = lambda w: np.ones((8, w, 4), np.float32)
    if REF and REF.exists():
        row = np.concatenate([tile(load_px(REF)), white, tile(load_px(rd / 'v81_altar_front.png')), white, tile(load_px(rd / 'v81_altar_oblique.png'))], 1)
        save_px(row, out / 'v81_design_reference_vs_3d.png')
    if V80R and (V80R / 'v80_matched.png').exists():
        rows = [np.concatenate([tile(load_px(V80R / ('v80_%s.png' % v))), white, tile(load_px(rd / ('v81_%s.png' % v)))], 1) for v in ('player_eye', 'altar_approach', 'lateral', 'matched')]
        sheet = np.concatenate([x for r in rows for x in (r, hgap(r.shape[1]))][:-1], 0); save_px(sheet, out / 'v81_before_after_sheet.png')

# ================================================================ ruin game GLB candidate
ruin_objs = [o for o in bpy.data.collections['V81_RUNE_SANCTUARY'].objects]
bpy.ops.object.select_all(action='DESELECT')
for o in ruin_objs:
    o.hide_select = False; o.select_set(True)
glb = out / 'v81_rune_sanctuary_ruin.glb'
bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB', use_selection=True, export_image_format='JPEG', export_jpeg_quality=85, export_apply=True)
QA['ruin_glb'] = dict(path=glb.name, sha256=sha(glb), bytes=glb.stat().st_size, objects=len(ruin_objs), triangles=sum(len(o.data.loop_triangles) for o in ruin_objs if o.data.loop_triangles or o.data.calc_loop_triangles() is None),
                      materials=sorted({m.name for o in ruin_objs for m in o.data.materials}), note='native shader layering (moss/AO) simplifies on glTF export; collision not authored; G4 NOT_RUN')
QA['limits'] = ['Provisional local coordinates; no collision, canonical placement or gameplay interaction.',
                'Ruin proportions authored from the 2D design by estimate; no orthographic design drawings exist (D2 open).',
                'Stone microstructure from in-file CC0 rock_moss_set_01; a clean pinned ashlar PBR (catalog ph_castle_wall_slates, HISTORICAL_LOCK_NOT_LOCAL) is a follow-up.',
                'Trail clearance is a visual/provisional walk core (0.75 m); collision and traversal tests NOT_RUN.',
                'Forest game LOD budget unchanged from V80 (OVER); added density raises native triangle count.']
QA['outputs'] = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.suffix in ('.blend', '.png', '.glb')}
QA['secs'] = round(time.time() - T0, 1)
(out / 'v81_qa.json').write_text(json.dumps(QA, indent=1) + '\n')
print('V81_DONE', QA['secs'])

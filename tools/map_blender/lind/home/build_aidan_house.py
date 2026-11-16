"""LIND-HOME-01 — Aidan's house (エイダンの家) modular master builder.

Deterministic Blender build. Runs both as
    python3 tools/map_blender/lind/home/build_aidan_house.py --out <dir> [--render all|none|<view,...>]
and
    blender -b --python tools/map_blender/lind/home/build_aidan_house.py -- --out <dir> ...

Masonry method family: F9 "layout-outline pillowed rubble" (see docs/qa/lind/home/attempt-ledger.json).
  * a wall-plane snecked-rubble layout produces disjoint cells (shared course grid near corners and
    openings, free stone lengths, jumpers spanning two courses, pinning snecks);
  * every cell is inset by a per-edge half joint, then turned into a rounded irregular outline;
  * the outline is extruded perpendicular to the wall (beds/perpends stay shared planes) and the exposed
    face gets an asymmetric crown (pillowed rubble face) plus low-frequency relief;
  * mortar = recessed wall core built as prisms around real apertures.
Stopped families F1-F5, F7 (and legacy H-A/H-B, roof V1-V3, arch v3) are NOT used.

Contract: docs/production/lind/home/arch-kit-contract.v1.json. Status: CANDIDATE, not art-approved.
"""
import argparse
import hashlib
import json
import math
import os
import random
import sys

import bpy
from mathutils import Vector, Matrix

SEED = 20261116
SCRIPT_VERSION = "lind-home-01/build_aidan_house.py v1.0"
HERE = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------------------------------------------
# Dimensions (contract v1 defaults; CANDIDATE values, not canon)
# ----------------------------------------------------------------------------------------------
L = 9.0            # exterior length (X, ridge axis)
D = 6.6            # exterior depth (Y); front facade at -Y
T = 0.55           # wall thickness
FOUND_TOP = 0.06   # foundation slab top above grade
FFL = 0.25         # finished floor level
WALL_TOP = 3.30    # long-wall masonry top
CEIL = 2.80        # underside of loft joists
PITCH = math.radians(42.0)
EAVE_OH = 0.40
VERGE_OH = 0.30
DECK_Z_AT_WALL = 3.50   # deck top at exterior wall line
DECK_T = 0.025
RIDGE_SAG = 0.035
MORTAR_RECESS = 0.025
STONE_BACK = 0.05
TAN = math.tan(PITCH)
COS = math.cos(PITCH)
SIN = math.sin(PITCH)
S_RIDGE = (D / 2 + EAVE_OH) / COS            # slope length from eave edge to ridge
Z_EAVE = DECK_Z_AT_WALL - EAVE_OH * TAN       # deck top at eave edge
Z_RIDGE = DECK_Z_AT_WALL + (D / 2) * TAN
CHIM_X = (L / 2 - 0.75, L / 2 + 0.02)
CHIM_Y = (-0.38, 0.37)
CHIM_TOP = Z_RIDGE + 0.85

def _tex_dir():
    for d in (os.environ.get("LIND_TEX_CACHE", ""), "/home/claude/.cache/lind_home_tex", os.path.expanduser("~/.cache/lind_home_tex")):
        if d and os.path.isdir(d):
            return d
    return os.path.expanduser("~/.cache/lind_home_tex")


TEX_DIR = _tex_dir()


def srgb(c):
    """sRGB 0-1 -> linear."""
    def f(x):
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    return tuple(f(x) for x in c[:3]) + ((c[3],) if len(c) > 3 else (1.0,))


def hsv_srgb(h, s, v):
    import colorsys
    return colorsys.hsv_to_rgb(h / 360.0, s, v)


def noise3(x, y, z, seed=0.0):
    """Smooth deterministic pseudo-noise in [-1,1] (sum of incommensurate sines)."""
    a = math.sin(1.73 * x + 2.31 * y + 0.71 * z + seed) * math.sin(0.93 * y - 1.37 * z + 1.9 + seed * 0.7)
    b = math.sin(2.91 * x - 1.13 * y + 1.57 * z + 0.4 + seed * 1.3) * 0.6
    c = math.sin(5.3 * x + 4.7 * z - 3.1 * y + seed * 2.1) * 0.25
    return (a + b + c) / 1.85


# ----------------------------------------------------------------------------------------------
# Mesh builder (vertex/face lists -> one bpy object; UVs, per-face material + attributes)
# ----------------------------------------------------------------------------------------------
class MB:
    def __init__(self, name):
        self.name = name
        self.v = []
        self.f = []
        self.uv = []
        self.mat = []
        self.rand = []
        self.kind = []
        self.mats = []

    def mi(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def vert(self, p):
        self.v.append((float(p[0]), float(p[1]), float(p[2])))
        return len(self.v) - 1

    def poly(self, idx, uvs, mat, rand=0.0, kind=0):
        self.f.append(list(idx))
        self.uv.append([tuple(u) for u in uvs])
        self.mat.append(self.mi(mat))
        self.rand.append(rand)
        self.kind.append(kind)

    # oriented box: origin corner o, edge vectors a,b,c (right-handed)
    def box(self, o, a, b, c, mat, tile=1.0, rand=None, kind=0, rng=None):
        o, a, b, c = Vector(o), Vector(a), Vector(b), Vector(c)
        if a.cross(b).dot(c) < 0:
            b, a = a, b
            o = o
        P = [o, o + a, o + a + b, o + b, o + c, o + a + c, o + a + b + c, o + b + c]
        ids = [self.vert(p) for p in P]
        r = rand if rand is not None else (rng.random() if rng else 0.0)
        off = (r * 7.3 % 1.0, r * 3.1 % 1.0)
        faces = [((0, 3, 2, 1), a, b, 0), ((4, 5, 6, 7), a, b, 0), ((0, 1, 5, 4), a, c, 0),
                 ((2, 3, 7, 6), a, c, 0), ((1, 2, 6, 5), b, c, 0), ((3, 0, 4, 7), b, c, 0)]
        for fi, e1, e2, _ in faces:
            # project corners on the two edge directions; long axis first so grain follows the member
            l1, l2 = e1.length, e2.length
            if l2 > l1:
                e1, e2 = e2, e1
            n1, n2 = e1.normalized(), e2.normalized()
            uvs = [(off[0] + (P[i] - o).dot(n1) / tile, off[1] + (P[i] - o).dot(n2) / tile) for i in fi]
            self.poly([ids[i] for i in fi], uvs, mat, r, kind)

    def aabb(self, lo, hi, mat, tile=1.0, rand=None, kind=0, rng=None):
        lo, hi = Vector(lo), Vector(hi)
        d = hi - lo
        self.box(lo, (d.x, 0, 0), (0, d.y, 0), (0, 0, d.z), mat, tile, rand, kind, rng)

    def cylinder(self, base, axis, radius, height, seg, mat, tile=1.0, rand=0.0, rfun=None, rings=1, cap=True, kind=0):
        base, axis = Vector(base), Vector(axis).normalized()
        t1 = axis.orthogonal().normalized()
        t2 = axis.cross(t1)
        grid = []
        for j in range(rings + 1):
            h = height * j / rings
            row = []
            for i in range(seg):
                a = 2 * math.pi * i / seg
                r = radius * (rfun(j / rings, a) if rfun else 1.0)
                row.append(self.vert(base + axis * h + (t1 * math.cos(a) + t2 * math.sin(a)) * r))
            grid.append(row)
        circ = 2 * math.pi * radius
        for j in range(rings):
            for i in range(seg):
                i2 = (i + 1) % seg
                u0, u1 = circ * i / seg / tile, circ * (i + 1) / seg / tile
                v0, v1 = height * j / rings / tile, height * (j + 1) / rings / tile
                self.poly([grid[j][i], grid[j][i2], grid[j + 1][i2], grid[j + 1][i]],
                          [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], mat, rand, kind)
        if cap:
            for j, rev in ((0, True), (rings, False)):
                ring = grid[j][::-1] if rev else grid[j]
                uvs = [(0.5 + 0.5 * math.cos(2 * math.pi * i / seg) * radius / tile,
                        0.5 + 0.5 * math.sin(2 * math.pi * i / seg) * radius / tile) for i in range(seg)]
                self.poly(ring, uvs[::-1] if rev else uvs, mat, rand, kind)

    def superq(self, c, half, e=0.25, nu=14, nv=8, mat=None, tile=1.0, rand=0.0, disp=None, kind=0):
        """Rounded box / pillow (superquadric). e small -> boxy, 1 -> ellipsoid."""
        c = Vector(c)

        def sp(w, m):
            s = math.copysign(abs(w) ** m, w)
            return s
        rows = []
        for j in range(nv + 1):
            th = -math.pi / 2 + math.pi * j / nv
            row = []
            for i in range(nu):
                ph = -math.pi + 2 * math.pi * i / nu
                x = sp(math.cos(th), e) * sp(math.cos(ph), e)
                y = sp(math.cos(th), e) * sp(math.sin(ph), e)
                z = sp(math.sin(th), e)
                p = Vector((x * half[0], y * half[1], z * half[2]))
                if disp:
                    p = disp(p)
                row.append(p)
            rows.append(row)
        top = self.vert(c + rows[nv][0])
        bot = self.vert(c + rows[0][0])
        ids = [None] + [[self.vert(c + p) for p in rows[j]] for j in range(1, nv)] + [None]
        for j in range(nv):
            for i in range(nu):
                i2 = (i + 1) % nu
                uv = [(i / nu * 4 / tile, j / nv * 2 / tile), ((i + 1) / nu * 4 / tile, j / nv * 2 / tile),
                      ((i + 1) / nu * 4 / tile, (j + 1) / nv * 2 / tile), (i / nu * 4 / tile, (j + 1) / nv * 2 / tile)]
                if j == 0:
                    self.poly([bot, ids[1][i2], ids[1][i]], [uv[0], uv[2], uv[3]], mat, rand, kind)
                elif j == nv - 1:
                    self.poly([ids[j][i], ids[j][i2], top], [uv[0], uv[1], uv[2]], mat, rand, kind)
                else:
                    self.poly([ids[j][i], ids[j][i2], ids[j + 1][i2], ids[j + 1][i]], uv, mat, rand, kind)

    def prism(self, poly2d, frame, d0, d1, mat, tile=1.0, rand=0.0, kind=0):
        """Extrude a CCW (u,z) polygon between depths d0>d1 in a face frame."""
        o, tu, n = frame
        def P(u, z, d):
            return Vector((o[0] + tu[0] * u + n[0] * d, o[1] + tu[1] * u + n[1] * d, z + o[2] + n[2] * d))
        k = len(poly2d)
        fr = [self.vert(P(u, z, d0)) for u, z in poly2d]
        bk = [self.vert(P(u, z, d1)) for u, z in poly2d]
        uv = [(u / tile, z / tile) for u, z in poly2d]
        self.poly(fr, uv, mat, rand, kind)
        self.poly(bk[::-1], uv[::-1], mat, rand, kind)
        for i in range(k):
            j = (i + 1) % k
            lu = math.hypot(poly2d[j][0] - poly2d[i][0], poly2d[j][1] - poly2d[i][1])
            self.poly([fr[i], bk[i], bk[j], fr[j]], [(0, 0), (abs(d1 - d0) / tile, 0), (abs(d1 - d0) / tile, lu / tile), (0, lu / tile)], mat, rand, kind)

    def build(self, matlib, collection):
        me = bpy.data.meshes.new(self.name)
        me.from_pydata(self.v, [], self.f)
        me.validate(clean_customdata=False)
        for m in self.mats:
            me.materials.append(matlib[m])
        n = len(me.polygons)
        assert n == len(self.f), (self.name, n, len(self.f))
        me.polygons.foreach_set("material_index", self.mat)
        uvl = me.uv_layers.new(name="UVMap")
        flat = []
        for poly in self.uv:
            for u in poly:
                flat.extend(u)
        uvl.data.foreach_set("uv", flat)
        a = me.attributes.new("part_rand", "FLOAT", "FACE")
        a.data.foreach_set("value", self.rand)
        k = me.attributes.new("part_kind", "INT", "FACE")
        k.data.foreach_set("value", self.kind)
        me.polygons.foreach_set("use_smooth", [True] * n)
        try:
            me.set_sharp_from_angle(angle=math.radians(38))
        except Exception:
            pass
        me.update()
        ob = bpy.data.objects.new(self.name, me)
        collection.objects.link(ob)
        return ob


# ----------------------------------------------------------------------------------------------
# 2D polygon helpers
# ----------------------------------------------------------------------------------------------
def poly_area(P):
    a = 0.0
    for i in range(len(P)):
        x0, y0 = P[i]
        x1, y1 = P[(i + 1) % len(P)]
        a += x0 * y1 - x1 * y0
    return a / 2


def clip_half(P, a, b, c):
    """Keep points with a*u + b*z <= c."""
    out = []
    n = len(P)
    for i in range(n):
        p, q = P[i], P[(i + 1) % n]
        fp = a * p[0] + b * p[1] - c
        fq = a * q[0] + b * q[1] - c
        if fp <= 0:
            out.append(p)
        if (fp < 0 < fq) or (fq < 0 < fp):
            t = fp / (fp - fq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def clip_rect(P, u0, u1, z0, z1):
    for a, b, c in ((-1, 0, -u0), (1, 0, u1), (0, -1, -z0), (0, 1, z1)):
        P = clip_half(P, a, b, c)
        if len(P) < 3:
            return []
    return P


def inset_poly(P, ds):
    """Inset convex CCW polygon; edge i (P[i]->P[i+1]) moved inward by ds[i]."""
    n = len(P)
    lines = []
    for i in range(n):
        p, q = Vector((*P[i], 0)), Vector((*P[(i + 1) % n], 0))
        e = (q - p)
        if e.length < 1e-6:
            return []
        e.normalize()
        inward = Vector((-e.y, e.x, 0))
        lines.append((p + inward * ds[i], e))
    out = []
    for i in range(n):
        p1, e1 = lines[i - 1]
        p2, e2 = lines[i]
        den = e1.x * e2.y - e1.y * e2.x
        if abs(den) < 1e-9:
            out.append((p2.x, p2.y))
            continue
        t = ((p2.x - p1.x) * e2.y - (p2.y - p1.y) * e2.x) / den
        out.append((p1.x + e1.x * t, p1.y + e1.y * t))
    if poly_area(out) <= 0:
        return []
    return out


def round_outline(P, rng, rmin, rmax, jitter=0.010, fixed_edges=()):
    """Replace corners by 3-point rounded arcs, add inward mid-edge irregularity."""
    n = len(P)
    V = [Vector(p) for p in P]
    out = []
    for i in range(n):
        a, p, b = V[i - 1], V[i], V[(i + 1) % n]
        la, lb = (a - p).length, (b - p).length
        r = min(rng.uniform(rmin, rmax), 0.42 * la, 0.42 * lb)
        pa = p + (a - p).normalized() * r
        pb = p + (b - p).normalized() * r * rng.uniform(0.75, 1.25) if lb > 0 else p
        mid = 0.25 * pa + 0.5 * p + 0.25 * pb
        mid = mid + (mid - p) * rng.uniform(0.0, 0.35)
        out += [pa, mid, pb]
        # mid-edge irregularity on edge p->b
        if lb > 0.20 and i not in fixed_edges:
            e = (b - p)
            inward = Vector((-e.y, e.x)).normalized()
            for t in sorted(rng.uniform(0.3, 0.7) for _ in range(1 if lb < 0.45 else 2)):
                out.append(p + e * t + inward * rng.uniform(0.0, jitter))
    # drop near-duplicates
    clean = []
    for q in out:
        if not clean or (q - clean[-1]).length > 0.004:
            clean.append(q)
    if (clean[0] - clean[-1]).length <= 0.004:
        clean.pop()
    return [(q.x, q.y) for q in clean]


# ----------------------------------------------------------------------------------------------
# F9 stone generator
# ----------------------------------------------------------------------------------------------
class Face:
    def __init__(self, name, origin, tu, n, length):
        self.name, self.o, self.tu, self.n, self.len = name, Vector(origin), Vector(tu), Vector(n), length

    def P(self, u, z, d):
        return self.o + self.tu * u + Vector((0, 0, z)) + self.n * d

    @property
    def frame(self):
        return (self.o, self.tu, self.n)


def add_stone(mb, face, outline, rng, mat, kind, depth=STONE_BACK, crown=(0.012, 0.035), proud=0.0,
              tex_tile=1.8, seed_off=0.0):
    """Extrude an outline (CCW in face u,z) into a pillowed stone shell (closed manifold)."""
    n = len(outline)
    if n < 3:
        return 0
    us = [p[0] for p in outline]
    zs = [p[1] for p in outline]
    w, h = max(us) - min(us), max(zs) - min(zs)
    cx = sum(us) / n
    cz = sum(zs) / n
    cx += rng.uniform(-0.14, 0.14) * w * 0.5
    cz += rng.uniform(-0.14, 0.14) * h * 0.5
    H = max(crown[0], min(crown[1], 0.17 * min(w, h))) * rng.uniform(0.7, 1.2)
    tilt_u = rng.uniform(-0.035, 0.035)
    tilt_z = rng.uniform(-0.035, 0.035)
    r = rng.random()
    uo, vo = rng.random(), rng.random()

    def dd(u, z, base):
        dn = noise3(face.o.x + u * 2.7, z * 2.9, face.o.y * 0.7, seed_off) * 0.006
        return base + proud + tilt_u * (u - cx) + tilt_z * (z - cz) + dn

    def uv(u, z):
        return ((u - min(us)) / tex_tile + uo, (z - min(zs)) / tex_tile + vo)

    edge = [(u, z, max(-MORTAR_RECESS + 0.006, dd(u, z, 0.0))) for u, z in outline]
    f1 = [rng.uniform(0.70, 0.86) for _ in range(n)]
    f2 = [rng.uniform(0.36, 0.50) for _ in range(n)]
    ring1 = [(cx + f1[i] * (outline[i][0] - cx), cz + f1[i] * (outline[i][1] - cz)) for i in range(n)]
    ring2 = [(cx + f2[i] * (outline[i][0] - cx), cz + f2[i] * (outline[i][1] - cz)) for i in range(n)]
    perim = [0.0]
    for i in range(n - 1):
        perim.append(perim[-1] + math.hypot(outline[i + 1][0] - outline[i][0], outline[i + 1][1] - outline[i][1]))
    e_ids = [mb.vert(face.P(u, z, d)) for u, z, d in edge]
    r1 = [mb.vert(face.P(u, z, dd(u, z, H * rng.uniform(0.52, 0.70)))) for u, z in ring1]
    r2 = [mb.vert(face.P(u, z, dd(u, z, H * rng.uniform(0.86, 0.98)))) for u, z in ring2]
    c_id = mb.vert(face.P(cx, cz, dd(cx, cz, H)))
    b_ids = [mb.vert(face.P(u, z, -depth)) for u, z in outline]
    for i in range(n):
        j = (i + 1) % n
        mb.poly([e_ids[i], e_ids[j], r1[j], r1[i]], [uv(*outline[i]), uv(*outline[j]), uv(*ring1[j]), uv(*ring1[i])], mat, r, kind)
        mb.poly([r1[i], r1[j], r2[j], r2[i]], [uv(*ring1[i]), uv(*ring1[j]), uv(*ring2[j]), uv(*ring2[i])], mat, r, kind)
        mb.poly([r2[i], r2[j], c_id], [uv(*ring2[i]), uv(*ring2[j]), uv(cx, cz)], mat, r, kind)
        lu = math.hypot(outline[j][0] - outline[i][0], outline[j][1] - outline[i][1])
        s0 = perim[i] / tex_tile + uo
        s1 = s0 + lu / tex_tile
        mb.poly([e_ids[i], b_ids[i], b_ids[j], e_ids[j]],
                [(s0, vo), (s0, vo - depth / tex_tile), (s1, vo - depth / tex_tile), (s1, vo)], mat, r, kind)
    mb.poly(b_ids[::-1], [uv(*p) for p in outline[::-1]], mat, r, kind)
    return 1


def course_grid(rng, z0, z1, first=None, hmin=0.18, hmax=0.30):
    zs = [z0]
    if first:
        zs.append(z0 + first)
    while zs[-1] < z1 - 1e-6:
        h = rng.uniform(hmin, hmax)
        if z1 - (zs[-1] + h) < hmin * 0.75:
            h = z1 - zs[-1]
        zs.append(min(z1, zs[-1] + h))
    if zs[-1] - zs[-2] < hmin * 0.6 and len(zs) > 2:
        zs.pop(-2)
    return zs


def snap(zs, z):
    return min(range(len(zs)), key=lambda i: abs(zs[i] - z))


def subtract(intervals, a, b):
    out = []
    for x0, x1 in intervals:
        if b <= x0 or a >= x1:
            out.append((x0, x1))
        else:
            if a > x0:
                out.append((x0, a))
            if b < x1:
                out.append((b, x1))
    return [(x0, x1) for x0, x1 in out if x1 - x0 > 1e-4]


def build_wall_masonry(mb, mb_timber, face, rng, zs, top_clip, openings, quoin_ends, cells_log,
                       lmin=0.24, lmax=0.60, plinth_len=(0.40, 0.75), field_mat="MAT_STONE_RUBBLE_LIMESTONE_A",
                       quoin_mat="MAT_STONE_QUOIN_DRESSED_A", stats=None, crown=(0.012, 0.035), jumpers=True,
                       u_range=None):
    """Layout + stones for one wall face.

    zs: course boundaries; top_clip(u)-> max z (gable rake) or None.
    openings: list of dict(u0,u1,i0,i1,kind) with i0/i1 = course indices of bottom/top of masonry opening.
    quoin_ends: dict 'start'/'end' -> list per course of (reserve_on_this_face, quoin_here(bool), depth)
    """
    ua, ub = u_range if u_range else (0.0, face.len)
    ncourse = len(zs) - 1
    blocked = [[] for _ in range(ncourse)]
    special = []  # (kind, u0, u1, k0, k1, depth, proud)
    # quoins
    for end in ("start", "end"):
        for k, q in enumerate(quoin_ends.get(end, [])):
            if q is None or k >= ncourse:
                continue
            reserve, here, depth = q
            if end == "start":
                blocked[k].append((ua - 0.05, ua + reserve))
                if here:
                    special.append(("quoin", ua - 0.02, ua + reserve, k, k + 1, depth, 0.0))
            else:
                blocked[k].append((ub - reserve, ub + 0.05))
                if here:
                    special.append(("quoin", ub - reserve, ub + 0.02, k, k + 1, depth, 0.0))
    # openings: jambs, lintels (timber), sills
    for op in openings:
        u0, u1, i0, i1 = op["u0"], op["u1"], op["i0"], op["i1"]
        for k in range(i0, i1):
            jl = 0.24 if (k + int(u0 * 10)) % 2 == 0 else 0.38
            jr = 0.38 if (k + int(u0 * 10)) % 2 == 0 else 0.24
            blocked[k].append((u0 - jl, u1 + jr))
            special.append(("jamb", u0 - jl, u0, k, k + 1, 0.14, 0.0))
            special.append(("jamb", u1, u1 + jr, k, k + 1, 0.14, 0.0))
        # lintel course
        if i1 < ncourse:
            blocked[i1].append((u0 - 0.24, u1 + 0.24))
            z0, z1 = zs[i1], zs[i1 + 1]
            mb_timber.box(face.P(u0 - 0.22, z0 + 0.006, 0.012), face.tu * (u1 - u0 + 0.44), Vector((0, 0, z1 - z0 - 0.012)),
                          -face.n * 0.32, "MAT_TIMBER_OAK_WEATHERED_A", tile=1.0, rng=rng, kind=7)
        if op["kind"] == "window" and i0 > 0:
            blocked[i0 - 1].append((u0 - 0.10, u1 + 0.10))
            special.append(("sill", u0 - 0.09, u1 + 0.09, i0 - 1, i0, 0.16, 0.035))
    # specials -> stones
    nst = 0
    for kind, u0, u1, k0, k1, depth, proud in special:
        cell = [(u0, zs[k0]), (u1, zs[k0]), (u1, zs[k1]), (u0, zs[k1])]
        if top_clip:
            cell = clip_top(cell, top_clip)
            if not cell or abs(poly_area(cell)) < 0.01:
                continue
        ins = inset_poly(cell, [rng.uniform(0.004, 0.010) for _ in cell])
        if not ins:
            continue
        out = round_outline(ins, rng, 0.015, 0.04, jitter=0.006)
        kcode = {"quoin": 1, "jamb": 2, "sill": 3}[kind]
        nst += add_stone(mb, face, out, rng, quoin_mat, kcode, depth=depth, crown=(0.006, 0.016), proud=proud,
                         seed_off=rng.random() * 10)
        cells_log.append((face.name, kind, round(u0, 3), round(u1, 3), round(zs[k0], 3), round(zs[k1], 3)))
    # field
    reserved_next = [[] for _ in range(ncourse + 1)]
    prev_joints = []
    for k in range(ncourse):
        z0, z1 = zs[k], zs[k + 1]
        free = [(ua, ub)]
        for a, b in blocked[k] + reserved_next[k]:
            free = subtract(free, a, b)
        joints = []
        plinth = (k == 0)
        for a, b in free:
            if b - a < 0.10:
                continue
            u = a
            while u < b - 1e-4:
                lo, hi = plinth_len if plinth else (lmin, lmax)
                ln = rng.uniform(lo, hi)
                if b - (u + ln) < 0.16:
                    ln = b - u
                # perpend avoidance vs course below
                cut = u + ln
                for pj in prev_joints:
                    if abs(pj - cut) < 0.07 and cut < b - 0.2:
                        cut = pj + 0.09 if cut + 0.09 - u < hi * 1.25 else pj - 0.09
                if cut <= u + 0.12:
                    cut = min(b, u + lo)
                cut = min(cut, b)
                # jumper (spans two courses) if next course free there
                span2 = False
                if jumpers and not plinth and k + 1 < ncourse and rng.random() < 0.13 and (cut - u) < 0.55:
                    nb = blocked[k + 1] + reserved_next[k + 1]
                    if all(cut <= x0 or u >= x1 for x0, x1 in nb):
                        span2 = True
                        reserved_next[k + 1].append((u, cut))
                ztop = zs[k + 2] if span2 else z1
                cells = []
                if (not span2) and (not plinth) and (cut - u) > 0.36 and (z1 - z0) > 0.20 and rng.random() < 0.24:
                    # pinning sneck: main stone + two small stones stacked at one end
                    ls = rng.uniform(0.12, 0.18)
                    if rng.random() < 0.5:
                        cells.append((u, cut - ls, z0, z1))
                        zm = z0 + (z1 - z0) * rng.uniform(0.4, 0.6)
                        cells += [(cut - ls, cut, z0, zm), (cut - ls, cut, zm, z1)]
                    else:
                        cells.append((u + ls, cut, z0, z1))
                        zm = z0 + (z1 - z0) * rng.uniform(0.4, 0.6)
                        cells += [(u, u + ls, z0, zm), (u, u + ls, zm, z1)]
                elif (not span2) and (not plinth) and (z1 - z0) > 0.19 and (cut - u) > 0.30 and rng.random() < 0.38:
                    # brought-to-course: lower main stone + a row of 1-3 small levelling stones above it
                    zm = z0 + (z1 - z0) * rng.uniform(0.58, 0.74)
                    if rng.random() < 0.5:
                        cells.append((u, cut, z0, zm))
                        top0, top1 = zm, z1
                    else:
                        cells.append((u, cut, z1 - (zm - z0), z1))
                        top0, top1 = z0, z1 - (zm - z0)
                    npc = 1 if (cut - u) < 0.4 else rng.choice((2, 2, 3))
                    xs = sorted([u, cut] + [u + (cut - u) * (i + rng.uniform(0.3, 0.7)) / npc for i in range(npc - 1)])
                    for x0_, x1_ in zip(xs[:-1], xs[1:]):
                        cells.append((x0_, x1_, top0, top1))
                else:
                    cells.append((u, cut, z0, ztop))
                for c0, c1, cz0, cz1 in cells:
                    poly = [(c0, cz0), (c1, cz0), (c1, cz1), (c0, cz1)]
                    if top_clip:
                        poly = clip_top(poly, top_clip)
                        if not poly or abs(poly_area(poly)) < 0.012:
                            continue
                    ins = inset_poly(poly, [rng.uniform(0.004, 0.011) for _ in poly])
                    if not ins or abs(poly_area(ins)) < 0.008:
                        continue
                    big = min(c1 - c0, cz1 - cz0)
                    out = round_outline(ins, rng, 0.05 * (big / 0.25) ** 0.5, 0.13 * (big / 0.25) ** 0.5, jitter=0.018)
                    nst += add_stone(mb, face, out, rng, field_mat, 4 if plinth else 0,
                                     depth=STONE_BACK + (0.04 if plinth else 0.0), crown=crown,
                                     proud=0.012 if plinth else rng.uniform(-0.004, 0.006), seed_off=rng.random() * 10)
                    cells_log.append((face.name, "plinth" if plinth else "field", round(c0, 3), round(c1, 3), round(cz0, 3), round(cz1, 3)))
                joints.append(cut)
                u = cut
        prev_joints = joints
    if stats is not None:
        stats[face.name] = nst
    return nst


def clip_top(poly, top_clip):
    """top_clip is a list of half-planes (a,b,c) meaning a*u + b*z <= c."""
    for a, b, c in top_clip:
        poly = clip_half(poly, a, b, c)
        if len(poly) < 3:
            return []
    return poly


# ----------------------------------------------------------------------------------------------
# Materials
# ----------------------------------------------------------------------------------------------
TEX_STATUS = {}


def tex_path(name):
    p = os.path.join(TEX_DIR, name)
    if not os.path.isfile(p):
        TEX_STATUS[name] = "MISSING"
        return None
    try:
        src = json.load(open(os.path.join(HERE, "texture_sources.json")))["files"][name]
        sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if sha != src["sha256"]:
            TEX_STATUS[name] = "SHA_MISMATCH"
            return None
        TEX_STATUS[name] = "OK sha256=" + sha
    except Exception as e:  # noqa
        TEX_STATUS[name] = "UNVERIFIED " + str(e)
        return None
    return p


def sock(node, ident, out=False):
    coll = node.outputs if out else node.inputs
    if isinstance(ident, int):
        return coll[ident]
    for s in coll:
        if s.identifier == ident or s.name == ident:
            if s.enabled if hasattr(s, "enabled") else True:
                return s
    for s in coll:
        if s.identifier == ident or s.name == ident:
            return s
    raise KeyError(ident)


class NT:
    def __init__(self, mat):
        mat.use_nodes = True
        self.nt = mat.node_tree
        self.nt.nodes.clear()
        self.out = self.nt.nodes.new("ShaderNodeOutputMaterial")
        self.bsdf = self.nt.nodes.new("ShaderNodeBsdfPrincipled")
        self.link(self.bsdf, "BSDF", self.out, "Surface")

    def n(self, t, **kw):
        nd = self.nt.nodes.new(t)
        for k, v in kw.items():
            setattr(nd, k, v)
        return nd

    def link(self, a, ao, b, bi):
        self.nt.links.new(sock(a, ao, True), sock(b, bi))

    def val(self, node, ident, v):
        sock(node, ident).default_value = v

    def img(self, path, noncolor=False, uvnode=None):
        nd = self.n("ShaderNodeTexImage")
        im = bpy.data.images.load(path, check_existing=True)
        if noncolor:
            im.colorspace_settings.name = "Non-Color"
        nd.image = im
        nd.interpolation = "Linear"
        if uvnode is not None:
            self.link(uvnode, "Vector", nd, "Vector")
        return nd

    def attr(self, name):
        return self.n("ShaderNodeAttribute", attribute_name=name)

    def ramp(self, src, src_out, stops):
        r = self.n("ShaderNodeValToRGB")
        cr = r.color_ramp
        while len(cr.elements) > 1:
            cr.elements.remove(cr.elements[-1])
        cr.elements[0].position = stops[0][0]
        cr.elements[0].color = srgb(stops[0][1])
        for pos, col in stops[1:]:
            e = cr.elements.new(pos)
            e.color = srgb(col)
        self.link(src, src_out, r, "Fac")
        return r

    def mix(self, blend, fac_node, fac_out, a, aout, b, bout, fac_val=None):
        m = self.n("ShaderNodeMix")
        m.data_type = "RGBA"
        m.blend_type = blend
        if fac_node is not None:
            self.link(fac_node, fac_out, m, "Factor_Float")
        else:
            sock(m, "Factor_Float").default_value = fac_val
        if a is not None:
            self.link(a, aout, m, "A_Color")
        if b is not None:
            self.link(b, bout, m, "B_Color")
        return m

    def noise(self, scale, detail=3.0, rough=0.55, vec=None):
        nd = self.n("ShaderNodeTexNoise")
        self.val(nd, "Scale", scale)
        self.val(nd, "Detail", detail)
        self.val(nd, "Roughness", rough)
        if vec is not None:
            self.link(vec[0], vec[1], nd, "Vector")
        return nd

    def maprange(self, src, out, a, b, c, d):
        m = self.n("ShaderNodeMapRange")
        self.link(src, out, m, "Value")
        self.val(m, "From Min", a)
        self.val(m, "From Max", b)
        self.val(m, "To Min", c)
        self.val(m, "To Max", d)
        return m


def make_materials():
    M = {}

    def new(name):
        m = bpy.data.materials.new(name)
        M[name] = m
        return m, NT(m)

    texco_cache = {}

    def uvmap(nt, scale=1.0):
        tc = nt.n("ShaderNodeTexCoord")
        mp = nt.n("ShaderNodeMapping")
        nt.link(tc, "UV", mp, "Vector")
        mp.inputs["Scale"].default_value = (scale, scale, scale)
        return mp

    # --- stone rubble (CC0 rock_boulder_dry, tinted toward approved CG cream/greige) ---
    for name, stops, sat, valmul in (
        ("MAT_STONE_RUBBLE_LIMESTONE_A", [(0.0, (0.86, 0.77, 0.62)), (0.3, (0.92, 0.84, 0.70)), (0.55, (0.80, 0.74, 0.64)),
                                          (0.8, (0.94, 0.87, 0.74)), (1.0, (0.78, 0.68, 0.52))], 0.22, 1.0),
        ("MAT_STONE_QUOIN_DRESSED_A", [(0.0, (0.92, 0.85, 0.72)), (0.5, (0.88, 0.80, 0.68)), (1.0, (0.95, 0.89, 0.77))], 0.2, 1.0)):
        m, nt = new(name)
        mp = uvmap(nt)
        pd = tex_path("rock_boulder_dry_diff_1k.jpg")
        pn = tex_path("rock_boulder_dry_nor_gl_1k.jpg")
        pr = tex_path("rock_boulder_dry_rough_1k.jpg")
        at = nt.attr("part_rand")
        tint = nt.ramp(at, "Fac", stops)
        if pd:
            di = nt.img(pd, uvnode=mp)
            hs = nt.n("ShaderNodeHueSaturation")
            nt.val(hs, "Saturation", sat)
            nt.val(hs, "Value", 1.55)
            nt.link(di, "Color", hs, "Color")
            mixc = nt.mix("MULTIPLY", None, None, hs, "Color", tint, "Color", fac_val=1.0)
        else:
            nz = nt.noise(6.0, 6.0, 0.6, vec=(mp, "Vector"))
            mixc = nt.mix("MULTIPLY", None, None, nz, "Fac", tint, "Color", fac_val=0.25)
        # weathering: darker, slightly greenish toward ground (object z) — not a uniform band (noise-modulated)
        geo = nt.n("ShaderNodeNewGeometry")
        sep = nt.n("ShaderNodeSeparateXYZ")
        nt.link(geo, "Position", sep, "Vector")
        nzw = nt.noise(1.3, 4.0, 0.6, vec=(geo, "Position"))
        ground = nt.maprange(sep, "Z", 0.0, 0.8, 0.75, 0.0)
        mulw = nt.n("ShaderNodeMath", operation="MULTIPLY")
        nt.link(ground, "Result", mulw, 0)
        nt.link(nzw, "Fac", mulw, 1)
        grime = nt.mix("MIX", mulw, "Value", mixc, "Result_Color", None, None)
        sock(grime, "B_Color").default_value = srgb((0.46, 0.44, 0.34))
        nt.link(grime, "Result_Color", nt.bsdf, "Base Color")
        if pr:
            ri = nt.img(pr, True, mp)
            rr = nt.maprange(ri, "Color", 0.0, 1.0, 0.72, 0.95)
            nt.link(rr, "Result", nt.bsdf, "Roughness")
        else:
            nt.val(nt.bsdf, "Roughness", 0.86)
        if pn:
            ni = nt.img(pn, True, mp)
            nm = nt.n("ShaderNodeNormalMap")
            nt.val(nm, "Strength", 0.9)
            nt.link(ni, "Color", nm, "Color")
            nt.link(nm, "Normal", nt.bsdf, "Normal")

    # --- mortar ---
    m, nt = new("MAT_MORTAR_LIME_A")
    geo = nt.n("ShaderNodeNewGeometry")
    nz = nt.noise(14.0, 5.0, 0.7, vec=(geo, "Position"))
    rp = nt.ramp(nz, "Fac", [(0.3, (0.40, 0.38, 0.33)), (0.7, (0.55, 0.52, 0.46))])
    nt.link(rp, "Color", nt.bsdf, "Base Color")
    nt.val(nt.bsdf, "Roughness", 0.95)
    bump = nt.n("ShaderNodeBump")
    nt.val(bump, "Strength", 0.4)
    nt.link(nz, "Fac", bump, "Height")
    nt.link(bump, "Normal", nt.bsdf, "Normal")

    # --- slate (procedural PBR, blue-gray canon) ---
    for name, base_v, lich in (("MAT_SLATE_BLUEGRAY_A", (0.32, 0.45), True), ("MAT_SLATE_RIDGE_A", (0.28, 0.36), False)):
        m, nt = new(name)
        at = nt.attr("part_rand")
        stops = []
        for i, (h, s, v) in enumerate(((203, 0.12, base_v[0] + 0.03), (208, 0.10, base_v[0] + 0.07), (212, 0.14, base_v[1] - 0.04),
                                       (200, 0.09, base_v[1]), (215, 0.13, base_v[0]))):
            stops.append((i / 4, hsv_srgb(h, s, v)))
        tint = nt.ramp(at, "Fac", stops)
        tc = nt.n("ShaderNodeTexCoord")
        grain = nt.noise(38.0, 6.0, 0.62, vec=(tc, "UV"))
        gr = nt.maprange(grain, "Fac", 0.3, 0.7, 0.86, 1.10)
        col = nt.n("ShaderNodeVectorMath", operation="SCALE")
        nt.link(tint, "Color", col, 0)
        nt.link(gr, "Result", col, "Scale")
        last = (col, "Vector")
        if lich:
            # lichen / moss: patchy, biased to lower courses (part_kind encodes course 0..100) and north slope
            kd = nt.attr("slate_low")
            pos = nt.n("ShaderNodeNewGeometry")
            pn = nt.noise(3.2, 5.0, 0.7, vec=(pos, "Position"))
            pm = nt.maprange(pn, "Fac", 0.52, 0.68, 0.0, 1.0)
            mul = nt.n("ShaderNodeMath", operation="MULTIPLY")
            nt.link(pm, "Result", mul, 0)
            nt.link(kd, "Fac", mul, 1)
            lc = nt.mix("MIX", mul, "Value", None, None, None, None)
            nt.link(col, "Vector", lc, "A_Color")
            sock(lc, "B_Color").default_value = srgb((0.50, 0.50, 0.34))
            last = (lc, "Result_Color")
        nt.link(last[0], last[1], nt.bsdf, "Base Color")
        rgh = nt.maprange(grain, "Fac", 0.3, 0.7, 0.55, 0.78)
        nt.link(rgh, "Result", nt.bsdf, "Roughness")
        bump = nt.n("ShaderNodeBump")
        nt.val(bump, "Strength", 0.25)
        nt.val(bump, "Distance", 0.003)
        wav = nt.n("ShaderNodeTexWave")
        nt.val(wav, "Scale", 6.0)
        nt.val(wav, "Distortion", 6.0)
        nt.link(tc, "UV", wav, "Vector")
        nt.link(wav, "Fac", bump, "Height")
        nt.link(bump, "Normal", nt.bsdf, "Normal")

    # --- timber / planks (CC0) ---
    for name, prefix, tint_col, rmin, rmax in (
        ("MAT_TIMBER_OAK_WEATHERED_A", "rough_wood", (0.78, 0.70, 0.62), 0.62, 0.85),
        ("MAT_PLANK_FLOOR_A", "weathered_brown_planks", (0.95, 0.88, 0.80), 0.55, 0.78),
        ("MAT_DOOR_PLANK_A", "weathered_brown_planks", (0.85, 0.74, 0.62), 0.55, 0.80)):
        m, nt = new(name)
        mp = uvmap(nt, 0.5 if prefix == "rough_wood" else 0.4)
        at = nt.attr("part_rand")
        var = nt.ramp(at, "Fac", [(0.0, tuple(c * 0.85 for c in tint_col)), (1.0, tint_col)])
        pd = tex_path(prefix + "_diff_1k.jpg")
        pn = tex_path(prefix + "_nor_gl_1k.jpg")
        pr = tex_path(prefix + "_rough_1k.jpg")
        if pd:
            di = nt.img(pd, uvnode=mp)
            mc = nt.mix("MULTIPLY", None, None, di, "Color", var, "Color", fac_val=1.0)
            nt.link(mc, "Result_Color", nt.bsdf, "Base Color")
        else:
            wv = nt.n("ShaderNodeTexWave")
            nt.link(mp, "Vector", wv, "Vector")
            rp = nt.ramp(wv, "Fac", [(0.0, (0.25, 0.18, 0.12)), (1.0, (0.40, 0.30, 0.20))])
            nt.link(rp, "Color", nt.bsdf, "Base Color")
        if pr:
            ri = nt.img(pr, True, mp)
            rr = nt.maprange(ri, "Color", 0, 1, rmin, rmax)
            nt.link(rr, "Result", nt.bsdf, "Roughness")
        if pn:
            ni = nt.img(pn, True, mp)
            nm = nt.n("ShaderNodeNormalMap")
            nt.link(ni, "Color", nm, "Color")
            nt.link(nm, "Normal", nt.bsdf, "Normal")

    # --- plaster interior ---
    m, nt = new("MAT_PLASTER_LIME_INT_A")
    geo = nt.n("ShaderNodeNewGeometry")
    nz = nt.noise(2.5, 6.0, 0.65, vec=(geo, "Position"))
    rp = nt.ramp(nz, "Fac", [(0.35, (0.74, 0.70, 0.62)), (0.65, (0.86, 0.83, 0.76))])
    sep = nt.n("ShaderNodeSeparateXYZ")
    nt.link(geo, "Position", sep, "Vector")
    low = nt.maprange(sep, "Z", 0.25, 0.9, 0.35, 0.0)
    dm = nt.mix("MULTIPLY", low, "Result", rp, "Color", None, None)
    sock(dm, "B_Color").default_value = srgb((0.55, 0.50, 0.42))
    nt.link(dm, "Result_Color", nt.bsdf, "Base Color")
    nt.val(nt.bsdf, "Roughness", 0.92)
    bump = nt.n("ShaderNodeBump")
    nt.val(bump, "Strength", 0.12)
    nt.link(nz, "Fac", bump, "Height")
    nt.link(bump, "Normal", nt.bsdf, "Normal")

    # --- glass ---
    m, nt = new("MAT_GLASS_CROWN_A")
    nt.val(nt.bsdf, "Base Color", srgb((0.86, 0.92, 0.86)))
    nt.val(nt.bsdf, "Roughness", 0.06)
    nt.val(nt.bsdf, "IOR", 1.5)
    nt.val(nt.bsdf, "Transmission Weight", 1.0)

    # --- simple PBR sets ---
    simple = {
        "MAT_IRON_WROUGHT_A": ((0.12, 0.11, 0.10), 0.6, 1.0),
        "MAT_TERRACOTTA_A": ((0.56, 0.33, 0.22), 0.82, 0.0),
        "MAT_LEAD_FLASHING_A": ((0.36, 0.38, 0.40), 0.6, 0.6),
        "MAT_FABRIC_WOOL_GREEN_A": ((0.20, 0.32, 0.20), 0.95, 0.0),
        "MAT_LINEN_A": ((0.82, 0.79, 0.70), 0.9, 0.0),
        "MAT_SOOT_A": ((0.05, 0.045, 0.04), 0.95, 0.0),
    }
    for name, (c, r, met) in simple.items():
        m, nt = new(name)
        geo = nt.n("ShaderNodeNewGeometry")
        nz = nt.noise(9.0, 4.0, 0.6, vec=(geo, "Position"))
        rp = nt.ramp(nz, "Fac", [(0.3, tuple(x * 0.82 for x in c)), (0.7, c)])
        nt.link(rp, "Color", nt.bsdf, "Base Color")
        nt.val(nt.bsdf, "Roughness", r)
        nt.val(nt.bsdf, "Metallic", met)

    # --- fire ---
    m, nt = new("MAT_FIRE_EMIT_A")
    nt.val(nt.bsdf, "Base Color", (0, 0, 0, 1))
    nt.val(nt.bsdf, "Emission Color", srgb((1.0, 0.55, 0.18)))
    nt.val(nt.bsdf, "Emission Strength", 18.0)

    # --- staging ground / foliage / flowers (STG, never exported) ---
    m, nt = new("STG_MAT_GRASS")
    geo = nt.n("ShaderNodeNewGeometry")
    nz = nt.noise(0.8, 6.0, 0.6, vec=(geo, "Position"))
    rp = nt.ramp(nz, "Fac", [(0.3, (0.27, 0.38, 0.15)), (0.55, (0.38, 0.47, 0.20)), (0.75, (0.45, 0.42, 0.25))])
    nt.link(rp, "Color", nt.bsdf, "Base Color")
    nt.val(nt.bsdf, "Roughness", 0.95)
    nz2 = nt.noise(60.0, 2.0, 0.5, vec=(geo, "Position"))
    bump = nt.n("ShaderNodeBump")
    nt.val(bump, "Strength", 0.5)
    nt.link(nz2, "Fac", bump, "Height")
    nt.link(bump, "Normal", nt.bsdf, "Normal")
    for name, c in (("MAT_FOLIAGE_A", (0.22, 0.36, 0.14)), ("MAT_FLOWER_RED_A", (0.75, 0.14, 0.12)),
                    ("MAT_FLOWER_CREAM_A", (0.92, 0.88, 0.72))):
        m, nt = new(name)
        at = nt.attr("part_rand")
        rp = nt.ramp(at, "Fac", [(0.0, tuple(x * 0.8 for x in c)), (1.0, c)])
        nt.link(rp, "Color", nt.bsdf, "Base Color")
        nt.val(nt.bsdf, "Roughness", 0.7)
    return M


# ----------------------------------------------------------------------------------------------
# Building
# ----------------------------------------------------------------------------------------------
def faces_house():
    return [
        Face("front", (-L / 2, -D / 2, 0), (1, 0, 0), (0, -1, 0), L),
        Face("east", (L / 2, -D / 2, 0), (0, 1, 0), (1, 0, 0), D),
        Face("rear", (L / 2, D / 2, 0), (-1, 0, 0), (0, 1, 0), L),
        Face("west", (-L / 2, D / 2, 0), (0, -1, 0), (-1, 0, 0), D),
    ]


def deck_top_z(y):
    return DECK_Z_AT_WALL + (D / 2 - abs(y)) * TAN


def gable_clip(face):
    """Half-planes (u,z) for gable faces: below deck underside minus margin."""
    # u maps to y: east u = y + D/2 ; west u = D/2 - y. For both, rake rises toward u = D/2.
    m = 0.03 + DECK_T
    z_w = DECK_Z_AT_WALL - m
    # left rake: z <= z_w + u*TAN ; right rake: z <= z_w + (D-u)*TAN
    return [(-TAN, 1.0, z_w), (TAN, 1.0, z_w + D * TAN)]


def opening_plan(zs):
    """Openings per face (masonry opening, course-snapped). CANDIDATE layout."""
    door_top = snap(zs, FFL + 2.05 + 0.08)
    w_bot = snap(zs, FFL + 0.95)
    w_top = max(w_bot + 3, snap(zs, FFL + 0.95 + 1.05 + 0.16))
    ops = {
        "front": [dict(id="DOOR_MAIN", kind="door", u0=L / 2 - 0.58, u1=L / 2 + 0.58, i0=0, i1=door_top),
                  dict(id="W_FRONT_W", kind="window", u0=2.0 - 0.48, u1=2.0 + 0.48, i0=w_bot, i1=w_top, panes=(2, 3)),
                  dict(id="W_FRONT_E", kind="window", u0=7.0 - 0.48, u1=7.0 + 0.48, i0=w_bot, i1=w_top, panes=(2, 3))],
        "rear": [dict(id="W_REAR", kind="window", u0=(L / 2 - 0.2) - 0.48, u1=(L / 2 - 0.2) + 0.48, i0=w_bot, i1=w_top, panes=(2, 3))],
        "west": [dict(id="W_WEST_BED", kind="window", u0=(D / 2 + 0.5) - 0.44, u1=(D / 2 + 0.5) + 0.44, i0=w_bot, i1=w_top, panes=(2, 3))],
        "east": [dict(id="W_EAST_SMALL", kind="window", u0=1.5 - 0.30, u1=1.5 + 0.30, i0=snap(zs, 1.35), i1=snap(zs, 1.35) + 2, panes=(1, 2))],
    }
    return ops


def build(out_dir):
    rng_master = random.Random(SEED)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    M = make_materials()
    root = bpy.data.collections.new("AIDAN_HOUSE")
    scene.collection.children.link(root)
    C = {}
    for nme in ["FOUNDATION", "WALL_SHELL", "MASONRY", "TIMBER", "ROOF_STRUCT", "ROOF_SLATE", "OPENINGS", "CHIMNEY",
                "PORCH", "INTERIOR", "PROPS_EXT", "COLLISION", "ANCHORS", "STAGING"]:
        c = bpy.data.collections.new(nme)
        root.children.link(c)
        C[nme] = c

    def R(i):
        return random.Random(SEED * 31 + i)

    cells_log = []
    stats = {}
    faces = faces_house()
    # ------------------------------------------------------------------ course grid (shared at corners)
    zs_main = course_grid(R(1), FOUND_TOP, WALL_TOP, first=0.34, hmin=0.17, hmax=0.34)
    zs_gable_up = course_grid(R(2), WALL_TOP, Z_RIDGE, hmin=0.17, hmax=0.27)
    zs_gable = zs_main + zs_gable_up[1:]
    ops = opening_plan(zs_main)

    # gable loft window (west only; east gable carries the chimney)
    k_loft0 = len(zs_main) - 1 + snap(zs_gable_up, 3.95)
    ops["west"].append(dict(id="W_WEST_LOFT", kind="window", u0=D / 2 - 0.36, u1=D / 2 + 0.36,
                            i0=k_loft0, i1=k_loft0 + 3, panes=(2, 2)))

    # ------------------------------------------------------------------ quoins
    rq = R(3)
    ncm = len(zs_main) - 1
    quoin_plan = {f.name: {"start": [None] * ncm, "end": [None] * ncm} for f in faces}
    for k in range(ncm):
        for c in range(4):
            f = faces[c]
            fp = faces[(c - 1) % 4]
            Ll, Ls = rq.uniform(0.50, 0.60), rq.uniform(0.29, 0.35)
            if k == 0:
                Ll, Ls = rq.uniform(0.55, 0.65), rq.uniform(0.40, 0.48)
            if (k + c) % 2 == 0:
                quoin_plan[f.name]["start"][k] = (Ll, True, Ls)
                quoin_plan[fp.name]["end"][k] = (Ls, False, 0)
            else:
                quoin_plan[fp.name]["end"][k] = (Ll, True, Ls)
                quoin_plan[f.name]["start"][k] = (Ls, False, 0)

    # ------------------------------------------------------------------ masonry (F9)
    timber = MB("GEO_AIDANHOUSE_TIMBER")
    for i, f in enumerate(faces):
        mb = MB("GEO_AIDANHOUSE_MASONRY_" + f.name.upper())
        gable = f.name in ("east", "west")
        zs = zs_gable if gable else zs_main
        build_wall_masonry(mb, timber, f, R(10 + i), zs, gable_clip(f) if gable else None, ops[f.name],
                           quoin_plan[f.name], cells_log, stats=stats)
        mb.build(M, C["MASONRY"])

    # ------------------------------------------------------------------ wall core (mortar) + plaster, real apertures
    core = MB("GEO_AIDANHOUSE_WALLCORE")
    plaster = MB("GEO_AIDANHOUSE_PLASTER_INT")
    for f in faces:
        gable = f.name in ("east", "west")
        zs = zs_gable if gable else zs_main
        holes = [(op["u0"], op["u1"], zs[op["i0"]], zs[op["i1"]]) for op in ops[f.name]]
        if gable:
            regions = [[(T, FOUND_TOP), (D - T, FOUND_TOP), (D - T, WALL_TOP), (T, WALL_TOP)],
                       clip_top([(0.02, WALL_TOP), (D - 0.02, WALL_TOP), (D - 0.02, Z_RIDGE), (0.02, Z_RIDGE)], gable_clip(f))]
        else:
            regions = [[(0.02, FOUND_TOP), (L - 0.02, FOUND_TOP), (L - 0.02, WALL_TOP), (0.02, WALL_TOP)]]
        for reg in regions:
            prisms_with_holes(core, reg, holes, f.frame, -MORTAR_RECESS, -T, "MAT_MORTAR_LIME_A", 1.5)
        lo, hi = (T, (D if gable else L) - T)
        prisms_with_holes(plaster, [(lo, FFL), (hi, FFL), (hi, CEIL), (lo, CEIL)], holes, f.frame, -T, -T - 0.02,
                          "MAT_PLASTER_LIME_INT_A", 2.0)
    core.build(M, C["WALL_SHELL"])
    plaster.build(M, C["WALL_SHELL"])

    # ------------------------------------------------------------------ foundation
    fnd = MB("GEO_AIDANHOUSE_FOUNDATION")
    fnd.aabb((-L / 2 - 0.09, -D / 2 - 0.09, -0.25), (L / 2 + 0.09, D / 2 + 0.09, FOUND_TOP), "MAT_STONE_QUOIN_DRESSED_A", 1.8, rand=0.4)
    fnd.aabb((-L / 2 + T, -D / 2 + T, FOUND_TOP), (L / 2 - T, D / 2 - T, FFL - 0.05), "MAT_MORTAR_LIME_A", 2.0, rand=0.2)
    fnd.build(M, C["FOUNDATION"])

    # ------------------------------------------------------------------ openings: frames, glass, door, threshold
    build_openings(M, C, faces, ops, zs_main, zs_gable, R(40))

    # ------------------------------------------------------------------ roof structure + slates + ridge
    build_roof(M, C, timber, R(50))
    timber.build(M, C["TIMBER"])

    # ------------------------------------------------------------------ chimney
    build_chimney(M, C, R(60), cells_log, stats)

    # ------------------------------------------------------------------ porch
    build_porch(M, C, R(70))

    # ------------------------------------------------------------------ interior
    build_interior(M, C, R(80))

    # ------------------------------------------------------------------ exterior props + staging
    build_props(M, C, R(90))
    build_staging(M, C, R(100))

    # ------------------------------------------------------------------ collision + anchors
    build_collision_anchors(C)

    # ------------------------------------------------------------------ lights / world
    setup_world_lights(scene, C)

    # manifest
    man = manifest(scene, C, cells_log, stats, zs_main, zs_gable, ops)
    os.makedirs(out_dir, exist_ok=True)
    return man


def prisms_with_holes(mb, region, holes, frame, d0, d1, mat, tile):
    us = sorted(set([min(p[0] for p in region), max(p[0] for p in region)] +
                    [h[0] for h in holes] + [h[1] for h in holes]))
    zmin, zmax = min(p[1] for p in region), max(p[1] for p in region)
    for a, b in zip(us[:-1], us[1:]):
        if b - a < 1e-4:
            continue
        zint = [(zmin, zmax)]
        for h in holes:
            if h[0] < b - 1e-4 and h[1] > a + 1e-4:
                zint = subtract(zint, h[2], h[3])
        for z0, z1 in zint:
            P = clip_rect(region, a, b, z0, z1)
            if P and abs(poly_area(P)) > 1e-4:
                if poly_area(P) < 0:
                    P = P[::-1]
                mb.prism(P, frame, d0, d1, mat, tile)


def build_openings(M, C, faces, ops, zs_main, zs_gable, rng):
    mb = MB("GEO_AIDANHOUSE_OPENINGS")
    glass = MB("GEO_AIDANHOUSE_GLASS")
    fr_t, setback, depth = 0.08, 0.14, 0.09
    fmap = {f.name: f for f in faces}
    for fname, lst in ops.items():
        f = fmap[fname]
        zs = zs_gable if fname in ("east", "west") else zs_main
        for op in lst:
            u0, u1, z0, z1 = op["u0"], op["u1"], zs[op["i0"]], zs[op["i1"]]
            n, tu = f.n, f.tu
            d_out = -setback
            op["clear"] = (round(u1 - u0 - 2 * fr_t, 3), round(z1 - z0 - (fr_t if op["kind"] == "door" else 2 * fr_t), 3))
            op["z"] = (round(z0, 3), round(z1, 3))
            if op["kind"] == "door":
                zb = FFL
                # threshold stone inside opening + outside step
                mb.box(f.P(u0, FOUND_TOP, 0.10), tu * (u1 - u0), Vector((0, 0, FFL - FOUND_TOP)), -n * (T + 0.10),
                       "MAT_STONE_QUOIN_DRESSED_A", 1.8, rand=0.6)
                # frame: two jambs + head
                for uu in (u0, u1 - fr_t):
                    mb.box(f.P(uu, zb, d_out), tu * fr_t, Vector((0, 0, z1 - zb)), -n * depth, "MAT_TIMBER_OAK_WEATHERED_A", 1.0, rng=rng)
                mb.box(f.P(u0, z1 - fr_t, d_out), tu * (u1 - u0), Vector((0, 0, fr_t)), -n * depth, "MAT_TIMBER_OAK_WEATHERED_A", 1.0, rng=rng)
                # door leaf: vertical planks of varying width with small gaps
                du0, du1, dz0, dz1 = u0 + fr_t + 0.004, u1 - fr_t - 0.004, zb + 0.01, z1 - fr_t - 0.004
                u = du0
                while u < du1 - 0.01:
                    w = min(rng.uniform(0.13, 0.19), du1 - u)
                    if du1 - (u + w) < 0.07:
                        w = du1 - u
                    mb.box(f.P(u, dz0, d_out - 0.02), tu * (w - 0.004), Vector((0, 0, dz1 - dz0 - rng.uniform(0, 0.01))),
                           -n * 0.045, "MAT_DOOR_PLANK_A", 0.8, rng=rng)
                    u += w
                # strap hinges, ring handle, latch plate
                for zh in (dz0 + 0.35, dz1 - 0.35):
                    mb.box(f.P(du0 - 0.01, zh, d_out - 0.012), tu * 0.62, Vector((0, 0, 0.045)), -n * 0.012, "MAT_IRON_WROUGHT_A", 0.5, rand=0.3)
                    mb.cylinder(f.P(du0 + 0.62, zh + 0.022, d_out - 0.006), -n, 0.014, 0.012, 8, "MAT_IRON_WROUGHT_A", 0.2)
                mb.box(f.P(du1 - 0.20, FFL + 0.95, d_out - 0.012), tu * 0.07, Vector((0, 0, 0.16)), -n * 0.01, "MAT_IRON_WROUGHT_A", 0.5)
                mb.cylinder(f.P(du1 - 0.165, FFL + 0.96, d_out + 0.005), tu, 0.05, 0.012, 12, "MAT_IRON_WROUGHT_A", 0.2, cap=True)
            else:
                cols, rows = op.get("panes", (2, 3))
                # outer frame
                for uu in (u0, u1 - fr_t):
                    mb.box(f.P(uu, z0, d_out), tu * fr_t, Vector((0, 0, z1 - z0)), -n * depth, "MAT_TIMBER_OAK_WEATHERED_A", 1.0, rng=rng)
                for zz in (z0, z1 - fr_t):
                    mb.box(f.P(u0, zz, d_out), tu * (u1 - u0), Vector((0, 0, fr_t)), -n * depth, "MAT_TIMBER_OAK_WEATHERED_A", 1.0, rng=rng)
                # glazing bars
                gu0, gu1, gz0, gz1 = u0 + fr_t, u1 - fr_t, z0 + fr_t, z1 - fr_t
                bar = 0.032
                for i in range(1, cols):
                    uu = gu0 + (gu1 - gu0) * i / cols - bar / 2
                    mb.box(f.P(uu, gz0, d_out - 0.02), tu * bar, Vector((0, 0, gz1 - gz0)), -n * 0.045, "MAT_TIMBER_OAK_WEATHERED_A", 0.6, rng=rng)
                for j in range(1, rows):
                    zz = gz0 + (gz1 - gz0) * j / rows - bar / 2
                    mb.box(f.P(gu0, zz, d_out - 0.02), tu * (gu1 - gu0), Vector((0, 0, bar)), -n * 0.045, "MAT_TIMBER_OAK_WEATHERED_A", 0.6, rng=rng)
                glass.box(f.P(gu0, gz0, d_out - 0.04), tu * (gu1 - gu0), Vector((0, 0, gz1 - gz0)), -n * 0.006, "MAT_GLASS_CROWN_A", 1.0, rand=0.5)
                # interior sill board
                if z0 < CEIL:
                    mb.box(f.P(u0 - 0.05, z0 - 0.03, -setback - depth), tu * (u1 - u0 + 0.10), Vector((0, 0, 0.035)),
                           -n * (T - setback - depth + 0.06), "MAT_TIMBER_OAK_WEATHERED_A", 1.0, rng=rng)
                # front windows: open plank shutters hung on the wall face
                if fname == "front":
                    sw = (u1 - u0) / 2 + 0.02
                    for side in (-1, 1):
                        us = u0 - sw - 0.06 if side < 0 else u1 + 0.06
                        rot = rng.uniform(-0.02, 0.02)
                        for p in range(3):
                            pw = sw / 3
                            mb.box(f.P(us + p * pw, z0 + 0.02 + rot, 0.05), tu * (pw - 0.006), Vector((0, 0, z1 - z0 - 0.04)),
                                   -n * 0.03, "MAT_DOOR_PLANK_A", 0.8, rng=rng)
                        for zz in (z0 + 0.15, z1 - 0.2):
                            mb.box(f.P(us, zz, 0.08), tu * sw, Vector((0, 0, 0.07)), -n * 0.03, "MAT_DOOR_PLANK_A", 0.8, rng=rng)
    mb.build(M, C["OPENINGS"])
    glass.build(M, C["OPENINGS"])


def roof_point(slope, x, s, h):
    """slope=-1 front (-Y), +1 rear. s along slope from eave edge; h along roof normal above deck top."""
    sag = RIDGE_SAG * max(0.0, 1 - (x / (L / 2 + VERGE_OH)) ** 2) * min(1.0, s / S_RIDGE)
    y = slope * (D / 2 + EAVE_OH) - slope * s * COS
    z = Z_EAVE + s * SIN - sag
    ny, nz = slope * SIN, COS
    return Vector((x, y + ny * h, z + nz * h))


def s_of_y(y):
    return (D / 2 + EAVE_OH - abs(y)) / COS


def build_roof(M, C, timber, rng):
    xl, xr = -L / 2 - VERGE_OH, L / 2 + VERGE_OH
    # deck (boards) — gridded so it follows the ridge sag
    deck = MB("GEO_AIDANHOUSE_ROOFDECK")
    nx, ns = 24, 10
    for slope in (-1, 1):
        top = [[deck.vert(roof_point(slope, xl + (xr - xl) * i / nx, S_RIDGE * j / ns, 0.0)) for i in range(nx + 1)] for j in range(ns + 1)]
        bot = [[deck.vert(roof_point(slope, xl + (xr - xl) * i / nx, S_RIDGE * j / ns, -DECK_T)) for i in range(nx + 1)] for j in range(ns + 1)]
        for j in range(ns):
            for i in range(nx):
                uv = [(i / nx * 9.6, j / ns * 5), ((i + 1) / nx * 9.6, j / ns * 5), ((i + 1) / nx * 9.6, (j + 1) / ns * 5), (i / nx * 9.6, (j + 1) / ns * 5)]
                q = [top[j][i], top[j][i + 1], top[j + 1][i + 1], top[j + 1][i]]
                b = [bot[j][i], bot[j][i + 1], bot[j + 1][i + 1], bot[j + 1][i]]
                if slope < 0:
                    deck.poly(q, uv, "MAT_TIMBER_OAK_WEATHERED_A", 0.3)
                    deck.poly(b[::-1], uv[::-1], "MAT_TIMBER_OAK_WEATHERED_A", 0.3)
                else:
                    deck.poly(q[::-1], uv[::-1], "MAT_TIMBER_OAK_WEATHERED_A", 0.3)
                    deck.poly(b, uv, "MAT_TIMBER_OAK_WEATHERED_A", 0.3)
        # perimeter (eave edge j=0, verge edges)
        for i in range(nx):
            q = [top[0][i], bot[0][i], bot[0][i + 1], top[0][i + 1]]
            deck.poly(q if slope < 0 else q[::-1], [(0, 0), (0, 0.03), (0.4, 0.03), (0.4, 0)], "MAT_TIMBER_OAK_WEATHERED_A", 0.3)
        for i_edge, rev in ((0, False), (nx, True)):
            for j in range(ns):
                q = [top[j][i_edge], top[j + 1][i_edge], bot[j + 1][i_edge], bot[j][i_edge]]
                if (slope < 0) == rev:
                    q = q[::-1]
                deck.poly(q, [(0, 0), (0.5, 0), (0.5, 0.03), (0, 0.03)], "MAT_TIMBER_OAK_WEATHERED_A", 0.3)
    deck.build(M, C["ROOF_STRUCT"])

    # rafters (straight; tails exposed at eaves), fly rafters + bargeboards at verges, ridge board, wall plates, frieze
    for slope in (-1, 1):
        nrm = Vector((0, slope * SIN, COS))
        up = Vector((0, -slope * COS, SIN))
        xs = [-L / 2 + 0.12 + 0.6 * i for i in range(int((L - 0.24) / 0.6) + 1)] + [L / 2 - 0.2]
        for x in xs:
            o = roof_point(slope, x - 0.04, 0.0, -DECK_T) - nrm * 0.15
            o = Vector((o.x, o.y, o.z + RIDGE_SAG * 0))
            timber.box(o, Vector((0.08, 0, 0)), up * (S_RIDGE - 0.04), nrm * 0.15, "MAT_TIMBER_OAK_WEATHERED_A", 1.0, rng=rng, kind=8)
        for x in (xl, xr - 0.06):
            o = roof_point(slope, x, 0.0, -DECK_T) - nrm * 0.15
            timber.box(o, Vector((0.06, 0, 0)), up * (S_RIDGE - 0.02), nrm * 0.15, "MAT_TIMBER_OAK_WEATHERED_A", 1.0, rng=rng, kind=8)
            # bargeboard: outside the fly rafter, up to slate level
            bx = x - 0.05 if x == xl else x + 0.06
            ob = roof_point(slope, bx, -0.02, 0.03) - nrm * 0.22
            timber.box(ob, Vector((0.05, 0, 0)), up * (S_RIDGE + 0.02), nrm * 0.24, "MAT_TIMBER_OAK_WEATHERED_A", 1.0, rng=rng, kind=9)
        # fascia board along eave
        o = roof_point(slope, xl, -0.03, 0.02) - nrm * 0.18
        timber.box(o, Vector((xr - xl, 0, 0)), up * 0.03, nrm * 0.18, "MAT_TIMBER_OAK_WEATHERED_A", 1.0, rng=rng, kind=9)
        # wall plate + frieze blocking between rafters at the wall line
        yw = slope * (D / 2 - 0.05)
        timber.aabb((-L / 2 + 0.05, min(yw, yw - slope * 0.22), WALL_TOP), (L / 2 - 0.05, max(yw, yw - slope * 0.22), WALL_TOP + 0.15),
                    "MAT_TIMBER_OAK_WEATHERED_A", 1.0, rng=rng, kind=7)
        yf = slope * (D / 2 + 0.005)
        zf = deck_top_z(D / 2) - DECK_T
        timber.aabb((-L / 2, min(yf, yf - slope * 0.04), WALL_TOP - 0.01), (L / 2, max(yf, yf - slope * 0.04), zf + 0.01),
                    "MAT_TIMBER_OAK_WEATHERED_A", 1.0, rng=rng, kind=7)
    timber.aabb((-L / 2 - VERGE_OH, -0.04, Z_RIDGE - DECK_T - 0.22), (L / 2 + VERGE_OH, 0.04, Z_RIDGE - DECK_T - 0.02),
                "MAT_TIMBER_OAK_WEATHERED_A", 1.0, rng=rng, kind=8)

    # slates
    build_slates(M, C, rng, xl, xr)


def build_slates(M, C, rng, xl, xr):
    s_chim = s_of_y(CHIM_Y[0]) - 0.02  # chimney lowest slope position (front); rear symmetric enough (0.37)
    total = 0
    for slope in (-1, 1):
        mb = MB("GEO_AIDANHOUSE_SLATES_" + ("FRONT" if slope < 0 else "REAR"))
        s_ch = s_of_y(CHIM_Y[0] if slope < 0 else CHIM_Y[1]) - 0.03
        s = 0.0
        k = 0
        prev_joints = []
        courses = []
        g = rng.uniform(0.16, 0.19)
        # under-eave course (short slates) then regular courses
        while s < S_RIDGE - 0.08:
            courses.append((k, s, g))
            k += 1
            s += g
            g = rng.uniform(0.155, 0.195)
        ncourse = len(courses)
        for (k, s0, g) in [(-1, 0.0, 0.10)] + courses:
            ln = 2 * g + rng.uniform(0.06, 0.08) if k >= 0 else 0.22
            ln = min(ln, S_RIDGE - s0 + 0.02)
            if ln < 0.06:
                continue
            spans = [(xl - 0.04, xr + 0.04)]
            if s0 + ln > s_ch:
                spans = [(xl - 0.04, CHIM_X[0] - 0.012), (CHIM_X[1] + 0.012, xr + 0.04)]
            joints = []
            low = max(0.0, 1.0 - (k + 1) / (ncourse * 0.55)) * (1.0 if slope > 0 else 0.55)
            for a, b in spans:
                x = a
                if k % 2 == 1 and a < 0:
                    first = rng.uniform(0.10, 0.16)
                else:
                    first = None
                while x < b - 0.01:
                    w = first if first else rng.uniform(0.18, 0.32)
                    first = None
                    if b - (x + w) < 0.12:
                        w = b - x
                    cut = x + w
                    for pj in prev_joints:
                        if abs(pj - cut) < 0.06 and b - cut > 0.2:
                            cut = pj + 0.075
                    w = cut - x
                    add_slate(mb, rng, slope, x, w, s0, ln, k, low)
                    joints.append(cut)
                    total += 1
                    x = cut
            prev_joints = joints
        ob = mb.build(M, C["ROOF_SLATE"])
        lo = ob.data.attributes.new("slate_low", "FLOAT", "FACE")
        lo.data.foreach_set("value", mb.low)
    # ridge saddles
    rmb = MB("GEO_AIDANHOUSE_RIDGE")
    x = xl - 0.03
    while x < xr + 0.03:
        ln = rng.uniform(0.30, 0.38)
        if CHIM_X[0] - 0.02 < x + ln and x < CHIM_X[1] + 0.02:
            x = CHIM_X[1] + 0.02
            continue
        ln = min(ln, xr + 0.04 - x)
        if ln < 0.08:
            break
        th = rng.uniform(0.018, 0.026)
        for slope in (-1, 1):
            p0 = roof_point(slope, x, S_RIDGE - 0.17, 0.045)
            p1 = roof_point(slope, x, S_RIDGE + 0.012, 0.045)
            up = p1 - p0
            nrm = Vector((0, slope * SIN, COS))
            yaw = rng.uniform(-0.01, 0.01)
            rmb.box(p0 + Vector((0, 0, yaw)), Vector((ln, 0, 0)), up, nrm * th, "MAT_SLATE_RIDGE_A", 0.5, rand=rng.random(), kind=6)
        x += ln - 0.035
    rmb.build(M, C["ROOF_SLATE"])
    C["_slate_count"] = total


def add_slate(mb, rng, slope, x, w, s0, ln, k, low):
    if not hasattr(mb, "low"):
        mb.low = []
    t = rng.uniform(0.010, 0.018)
    hb = 0.008 + 2.5 * t + rng.uniform(-0.002, 0.004)
    ht = 0.004 + 0.5 * t
    gap = rng.uniform(0.002, 0.006)
    a0, a1 = x + gap / 2, x + w - gap / 2
    # outline (a along x, b along slope from bottom edge), chipped bottom corners and ragged bottom edge
    cl = rng.uniform(0.0, 0.035) if rng.random() < 0.65 else 0.0
    cr = rng.uniform(0.0, 0.035) if rng.random() < 0.65 else 0.0
    bmid = [rng.uniform(-0.006, 0.006) for _ in range(2)]
    eave = rng.uniform(-0.012, 0.010)
    out = [(a0, cl * 0.8), (a0 + cl, 0.0), (a0 + (a1 - a0) * 0.35, bmid[0]), (a0 + (a1 - a0) * 0.68, bmid[1]),
           (a1 - cr, 0.0), (a1, cr * 0.8), (a1 - rng.uniform(0, 0.008), ln), (a0 + rng.uniform(0, 0.008), ln)]
    out = [(p[0], p[1] + eave) for p in out]
    # dedupe (no chip -> coincident points)
    ded = []
    for p in out:
        if not ded or abs(p[0] - ded[-1][0]) + abs(p[1] - ded[-1][1]) > 1e-4:
            ded.append(p)
    if abs(ded[0][0] - ded[-1][0]) + abs(ded[0][1] - ded[-1][1]) < 1e-4:
        ded.pop()
    out = ded
    yaw = rng.uniform(-0.018, 0.018)
    cxm = (a0 + a1) / 2
    r = rng.random()
    tp, bt = [], []
    for a, b in out:
        aa = cxm + (a - cxm) * math.cos(yaw) - b * math.sin(yaw)
        bb = (a - cxm) * math.sin(yaw) + b * math.cos(yaw)
        h = hb + (ht - hb) * max(0.0, min(1.0, bb / ln))
        tp.append(mb.vert(roof_point(slope, aa, s0 + bb, h)))
        bt.append(mb.vert(roof_point(slope, aa, s0 + bb, h - t)))
    uvs = [((a - x) / 0.5 + r * 3, b / 0.5 + r * 5) for a, b in out]
    n = len(out)
    top_order = list(range(n)) if slope < 0 else list(range(n))[::-1]
    mb.poly([tp[i] for i in top_order], [uvs[i] for i in top_order], "MAT_SLATE_BLUEGRAY_A", r, 5)
    mb.poly([bt[i] for i in top_order[::-1]], [uvs[i] for i in top_order[::-1]], "MAT_SLATE_BLUEGRAY_A", r, 5)
    mb.low += [low, low]
    for i in range(n):
        j = (i + 1) % n
        q = [tp[i], bt[i], bt[j], tp[j]] if slope < 0 else [tp[j], bt[j], bt[i], tp[i]]
        mb.poly(q, [uvs[i], uvs[i], uvs[j], uvs[j]], "MAT_SLATE_BLUEGRAY_A", r, 5)
        mb.low.append(low)


def build_chimney(M, C, rng, cells_log, stats):
    x0, x1 = CHIM_X
    y0, y1 = CHIM_Y
    zb = deck_top_z(max(abs(y0), abs(y1))) - 0.12
    ztop = CHIM_TOP
    zs = course_grid(rng, zb, ztop - 0.12, hmin=0.15, hmax=0.23)
    faces = [
        Face("chim_front", (x0, y0, 0), (1, 0, 0), (0, -1, 0), x1 - x0),
        Face("chim_east", (x1, y0, 0), (0, 1, 0), (1, 0, 0), y1 - y0),
        Face("chim_rear", (x1, y1, 0), (-1, 0, 0), (0, 1, 0), x1 - x0),
        Face("chim_west", (x0, y1, 0), (0, -1, 0), (-1, 0, 0), y1 - y0),
    ]
    nc = len(zs) - 1
    qp = {f.name: {"start": [None] * nc, "end": [None] * nc} for f in faces}
    for k in range(nc):
        for c in range(4):
            f, fp = faces[c], faces[(c - 1) % 4]
            half_f = f.len / 2 - 0.004
            half_p = fp.len / 2 - 0.004
            jitter = rng.uniform(-0.06, 0.06)
            if (k + c) % 2 == 0:
                qp[f.name]["start"][k] = (half_f + (jitter if c % 2 == 0 else -jitter), True, min(0.30, half_p))
                qp[fp.name]["end"][k] = (min(0.30, half_p), False, 0)
            else:
                qp[fp.name]["end"][k] = (half_p + (jitter if c % 2 == 0 else -jitter), True, min(0.30, half_f))
                qp[f.name]["start"][k] = (min(0.30, half_f), False, 0)
    mb = MB("GEO_AIDANHOUSE_CHIMNEY")
    dummy = MB("_unused")
    for i, f in enumerate(faces):
        build_wall_masonry(mb, dummy, f, random.Random(SEED + 600 + i), zs, None, [], qp[f.name], cells_log,
                           lmin=0.16, lmax=0.36, plinth_len=(0.16, 0.36), stats=stats, crown=(0.008, 0.02), jumpers=False)
    # core, cap slab, pots, flashing
    mb.aabb((x0 + MORTAR_RECESS, y0 + MORTAR_RECESS, zb), (x1 - MORTAR_RECESS, y1 - MORTAR_RECESS, ztop - 0.12), "MAT_MORTAR_LIME_A", 1.5, rand=0.5)
    mb.aabb((x0 - 0.07, y0 - 0.07, ztop - 0.12), (x1 + 0.07, y1 + 0.07, ztop), "MAT_STONE_QUOIN_DRESSED_A", 1.8, rand=0.7)
    for i, (px, py) in enumerate(((x0 + 0.22, (y0 + y1) / 2), (x1 - 0.22, (y0 + y1) / 2 + 0.02))):
        hgt = 0.42 if i == 0 else 0.36
        mb.cylinder((px, py, ztop), (0, 0, 1), 0.12, hgt, 14, "MAT_TERRACOTTA_A", 0.5, rand=0.4 + i * 0.3,
                    rfun=lambda t, a: 1.0 + 0.18 * max(0, (t - 0.8) / 0.2) - 0.08 * math.sin(t * math.pi), rings=5)
    fl = MB("GEO_AIDANHOUSE_FLASHING")
    for slope, yy in ((-1, y0), (1, y1)):
        nrm = Vector((0, slope * SIN, COS))
        up = Vector((0, -slope * COS, SIN))
        s_c = s_of_y(yy)
        o = roof_point(slope, x0 - 0.08, s_c - 0.20, 0.03)
        fl.box(o, Vector((x1 - x0 + 0.16, 0, 0)), up * 0.22, nrm * 0.006, "MAT_LEAD_FLASHING_A", 0.5, rand=0.2)
        # apron upstand against chimney face
        fl.aabb((x0 - 0.08, yy - 0.004 if slope < 0 else yy - 0.002, roof_point(slope, x0, s_c, 0.0).z),
                (x1 + 0.08, yy + 0.002 if slope < 0 else yy + 0.004, roof_point(slope, x0, s_c, 0.0).z + 0.16), "MAT_LEAD_FLASHING_A", 0.5, rand=0.2)
        for xx in (x0 - 0.08, x1 + 0.02):
            o = roof_point(slope, xx, s_c - 0.02, 0.035)
            fl.box(o, Vector((0.06, 0, 0)), up * (S_RIDGE - s_c + 0.02), nrm * 0.006, "MAT_LEAD_FLASHING_A", 0.5, rand=0.2)
    mb.build(M, C["CHIMNEY"])
    fl.build(M, C["CHIMNEY"])


def build_porch(M, C, rng):
    mb = MB("GEO_AIDANHOUSE_PORCH")
    yw = -D / 2
    proj, half = 1.30, 1.05
    z_wall, z_beam = 3.02, 2.40
    pitch = math.atan2(z_wall - z_beam, proj)
    for sx in (-1, 1):
        x = sx * (half - 0.06)
        mb.superq((x, yw - proj + 0.05, 0.10), (0.16, 0.16, 0.10), e=0.35, nu=10, nv=6, mat="MAT_STONE_QUOIN_DRESSED_A", tile=1.8, rand=rng.random())
        mb.aabb((x - 0.065, yw - proj - 0.015, 0.20), (x + 0.065, yw - proj + 0.115, z_beam), "MAT_TIMBER_OAK_WEATHERED_A", 1.0, rng=rng)
        # knee braces
        mb.box(Vector((x - 0.035, yw - proj + 0.1, z_beam - 0.45)), Vector((0.07, 0, 0)), Vector((0, 0.45, 0.42)), Vector((0, -0.05, 0.05)),
               "MAT_TIMBER_OAK_WEATHERED_A", 1.0, rng=rng)
    mb.aabb((-half - 0.1, yw - proj - 0.03, z_beam), (half + 0.1, yw - proj + 0.13, z_beam + 0.16), "MAT_TIMBER_OAK_WEATHERED_A", 1.0, rng=rng)
    mb.aabb((-half - 0.1, yw - 0.02, z_wall - 0.16), (half + 0.1, yw + 0.02, z_wall), "MAT_TIMBER_OAK_WEATHERED_A", 1.0, rng=rng)
    up = Vector((0, math.cos(pitch), math.sin(pitch)))
    nrm = Vector((0, -math.sin(pitch), math.cos(pitch)))
    s_len = (proj + 0.25) / math.cos(pitch)
    o_e = Vector((0, yw - proj - 0.25, z_beam + 0.16 - 0.25 * math.tan(pitch)))
    for x in [-half - 0.05 + i * (2 * half + 0.1 - 0.07) / 4 for i in range(5)]:
        mb.box(o_e + Vector((x, 0, 0)), Vector((0.07, 0, 0)), up * (s_len), nrm * 0.11, "MAT_TIMBER_OAK_WEATHERED_A", 1.0, rng=rng)
    o_d = o_e + nrm * 0.11
    mb.box(o_d + Vector((-half - 0.12, 0, 0)), Vector((2 * half + 0.24, 0, 0)), up * s_len, nrm * 0.02, "MAT_TIMBER_OAK_WEATHERED_A", 1.0, rng=rng)
    mb.build(M, C["PORCH"])
    # slates on porch (same slate rules, local plane)
    sl = MB("GEO_AIDANHOUSE_PORCH_SLATES")
    sl.low = []
    base = o_d + nrm * 0.02
    s0 = 0.0
    prev = []
    k = 0
    while s0 < s_len - 0.08:
        g = rng.uniform(0.15, 0.18)
        ln = min(2 * g + 0.07, s_len - s0 + 0.02)
        x = -half - 0.16
        joints = []
        first = rng.uniform(0.1, 0.16) if k % 2 else None
        while x < half + 0.16 - 0.01:
            w = first or rng.uniform(0.18, 0.30)
            first = None
            if half + 0.16 - (x + w) < 0.12:
                w = half + 0.16 - x
            for pj in prev:
                if abs(pj - (x + w)) < 0.06:
                    w += 0.075
            t = rng.uniform(0.010, 0.016)
            hb, ht = 0.008 + 2.5 * t, 0.004 + 0.5 * t
            r = rng.random()
            cl = rng.uniform(0, 0.03) if rng.random() < 0.6 else 0.0
            pts = [(x + 0.003, cl), (x + 0.003 + cl, 0), (x + w - 0.003, 0), (x + w - 0.003, ln), (x + 0.003, ln)]
            if cl < 1e-3:
                pts = pts[1:]
            tp = [sl.vert(base + Vector((a, 0, 0)) + up * (s0 + b) + nrm * (hb + (ht - hb) * b / ln)) for a, b in pts]
            bt = [sl.vert(base + Vector((a, 0, 0)) + up * (s0 + b) + nrm * (hb + (ht - hb) * b / ln - t)) for a, b in pts]
            uvs = [(a * 2 + r * 3, b * 2) for a, b in pts]
            sl.poly(tp, uvs, "MAT_SLATE_BLUEGRAY_A", r, 5)
            sl.poly(bt[::-1], uvs[::-1], "MAT_SLATE_BLUEGRAY_A", r, 5)
            sl.low += [0.6, 0.6]
            n = len(pts)
            for i in range(n):
                j = (i + 1) % n
                sl.poly([tp[i], bt[i], bt[j], tp[j]], [uvs[i], uvs[i], uvs[j], uvs[j]], "MAT_SLATE_BLUEGRAY_A", r, 5)
                sl.low.append(0.6)
            joints.append(x + w)
            x += w
        prev = joints
        s0 += g
        k += 1
    ob = sl.build(M, C["PORCH"])
    a = ob.data.attributes.new("slate_low", "FLOAT", "FACE")
    a.data.foreach_set("value", sl.low)
    # lead flashing against wall
    fl = MB("GEO_AIDANHOUSE_PORCH_FLASHING")
    fl.aabb((-half - 0.14, yw - 0.12, z_wall + 0.02), (half + 0.14, yw + 0.005, z_wall + 0.20), "MAT_LEAD_FLASHING_A", 0.5, rand=0.3)
    fl.build(M, C["PORCH"])


def build_interior(M, C, rng):
    xi0, xi1, yi0, yi1 = -L / 2 + T, L / 2 - T, -D / 2 + T, D / 2 - T
    fl = MB("GEO_AIDANHOUSE_INT_FLOOR")
    # floor boards along X, staggered
    y = yi0
    while y < yi1 - 0.01:
        w = min(rng.uniform(0.17, 0.24), yi1 - y)
        x = xi0
        while x < xi1 - 0.01:
            ln = min(rng.uniform(1.6, 3.2), xi1 - x)
            fl.aabb((x + 0.002, y + 0.002, FFL - 0.03 - rng.uniform(0, 0.004)), (x + ln - 0.002, y + w - 0.002, FFL),
                    "MAT_PLANK_FLOOR_A", 1.2, rng=rng)
            x += ln
        y += w
    fl.build(M, C["INTERIOR"])
    ce = MB("GEO_AIDANHOUSE_INT_CEILING")
    x = xi0 + 0.25
    while x < xi1 - 0.1:
        ce.aabb((x, yi0 - 0.1, CEIL), (x + 0.12, yi1 + 0.1, CEIL + 0.16), "MAT_TIMBER_OAK_WEATHERED_A", 1.0, rng=rng)
        x += rng.uniform(0.55, 0.65)
    ce.aabb((xi0 - 0.05, yi0 - 0.05, CEIL + 0.16), (xi1 + 0.05, yi1 + 0.05, CEIL + 0.20), "MAT_PLANK_FLOOR_A", 1.2, rand=0.5)
    # spine beam
    ce.aabb((xi0 - 0.1, -0.12, CEIL - 0.18), (xi1 + 0.1, 0.12, CEIL), "MAT_TIMBER_OAK_WEATHERED_A", 1.0, rng=rng)
    ce.build(M, C["INTERIOR"])

    fu = MB("GEO_AIDANHOUSE_INT_FURNITURE")
    W = "MAT_TIMBER_OAK_WEATHERED_A"
    # bed in NW corner, headboard on west wall
    bx0, bx1, by0, by1 = xi0 + 0.02, xi0 + 2.02, yi1 - 1.06, yi1 - 0.04
    for px, py, ph in ((bx0, by0, 1.05), (bx0, by1 - 0.08, 1.05), (bx1 - 0.08, by0, 0.70), (bx1 - 0.08, by1 - 0.08, 0.70)):
        fu.aabb((px, py, FFL), (px + 0.08, py + 0.08, FFL + ph), W, 1.0, rng=rng)
    for yy in (by0, by1 - 0.06):
        fu.aabb((bx0 + 0.08, yy, FFL + 0.22), (bx1 - 0.08, yy + 0.06, FFL + 0.40), W, 1.0, rng=rng)
    for i in range(4):
        fu.aabb((bx0 + 0.01, by0 + 0.08 + i * 0.215, FFL + 0.45), (bx0 + 0.07, by0 + 0.08 + i * 0.215 + 0.2, FFL + 0.98), W, 0.8, rng=rng)
    fu.aabb((bx1 - 0.075, by0 + 0.08, FFL + 0.40), (bx1 - 0.015, by1 - 0.08, FFL + 0.62), W, 0.8, rng=rng)
    fu.aabb((bx0 + 0.08, by0 + 0.06, FFL + 0.36), (bx1 - 0.08, by1 - 0.06, FFL + 0.40), W, 0.8, rng=rng)
    soft = MB("GEO_AIDANHOUSE_INT_SOFT")
    soft.superq(((bx0 + bx1) / 2, (by0 + by1) / 2, FFL + 0.50), ((bx1 - bx0) / 2 - 0.08, (by1 - by0) / 2 - 0.07, 0.10), e=0.18,
                nu=20, nv=8, mat="MAT_LINEN_A", tile=1.0, rand=0.3)
    # blanket: draped over lower 70% with soft folds
    def blanket_disp(p):
        return Vector((p.x, p.y, p.z + 0.012 * math.sin(p.x * 11) * math.cos(p.y * 7)))
    soft.superq(((bx0 + bx1) / 2 + 0.28, (by0 + by1) / 2, FFL + 0.555), ((bx1 - bx0) / 2 - 0.30, (by1 - by0) / 2 - 0.03, 0.075), e=0.15,
                nu=24, nv=8, mat="MAT_FABRIC_WOOL_GREEN_A", tile=1.0, rand=0.5, disp=blanket_disp)
    soft.superq((bx0 + 0.36, (by0 + by1) / 2 + 0.04, FFL + 0.66), (0.17, 0.32, 0.07), e=0.45, nu=16, nv=8, mat="MAT_LINEN_A", rand=0.7)
    # rug beside bed (opening spawn spot) and under table
    soft.superq((bx0 + 1.1, by0 - 0.55, FFL + 0.006), (0.75, 0.45, 0.006), e=0.1, nu=16, nv=4, mat="MAT_FABRIC_WOOL_GREEN_A", rand=0.9)
    # chest at bed foot
    cx0 = bx1 + 0.08
    fu.aabb((cx0, by1 - 0.55, FFL), (cx0 + 0.70, by1 - 0.05, FFL + 0.48), W, 0.8, rng=rng)
    fu.aabb((cx0 - 0.01, by1 - 0.56, FFL + 0.48), (cx0 + 0.71, by1 - 0.04, FFL + 0.53), W, 0.8, rng=rng)
    for xx in (cx0 + 0.08, cx0 + 0.58):
        fu.aabb((xx, by1 - 0.565, FFL + 0.05), (xx + 0.04, by1 - 0.555, FFL + 0.50), "MAT_IRON_WROUGHT_A", 0.5, rand=0.2)
    # candle on chest
    fu.cylinder((cx0 + 0.35, by1 - 0.30, FFL + 0.53), (0, 0, 1), 0.05, 0.015, 10, "MAT_IRON_WROUGHT_A", 0.3)
    fu.cylinder((cx0 + 0.35, by1 - 0.30, FFL + 0.545), (0, 0, 1), 0.018, 0.10, 8, "MAT_LINEN_A", 0.3)
    # cupboard on rear wall (west of rear window)
    fu.aabb((-1.55, yi1 - 0.45, FFL), (-0.70, yi1 - 0.02, FFL + 1.75), W, 0.8, rng=rng)
    fu.aabb((-1.56, yi1 - 0.47, FFL + 1.75), (-0.69, yi1, FFL + 1.82), W, 0.8, rng=rng)
    fu.aabb((-1.13, yi1 - 0.462, FFL + 0.25), (-1.12, yi1 - 0.45, FFL + 1.60), W, 0.8, rng=rng)
    # shelf with books on rear wall (east)
    for zz in (FFL + 0.9, FFL + 1.35, FFL + 1.8):
        fu.aabb((2.4, yi1 - 0.32, zz), (3.6, yi1 - 0.02, zz + 0.035), W, 0.8, rng=rng)
        x = 2.45
        while x < 3.45:
            bw = rng.uniform(0.035, 0.07)
            bh = rng.uniform(0.20, 0.30)
            lean = 0 if rng.random() < 0.85 else 0.03
            fu.aabb((x, yi1 - 0.27, zz + 0.035), (x + bw, yi1 - 0.07, zz + 0.035 + bh), "MAT_FABRIC_WOOL_GREEN_A" if rng.random() < 0.4 else "MAT_DOOR_PLANK_A", 0.3, rand=rng.random())
            x += bw + 0.004 + lean
    for xx in (2.42, 3.55):
        fu.aabb((xx, yi1 - 0.32, FFL), (xx + 0.05, yi1 - 0.02, FFL + 1.88), W, 0.8, rng=rng)
    # table, stools, bench
    tx, ty = 0.4, -0.2
    fu.cylinder((tx, ty, FFL + 0.72), (0, 0, 1), 0.55, 0.05, 24, W, 0.8, rand=0.4)
    for a in range(3):
        ang = a * 2 * math.pi / 3 + 0.3
        fu.aabb((tx + 0.3 * math.cos(ang) - 0.03, ty + 0.3 * math.sin(ang) - 0.03, FFL), (tx + 0.3 * math.cos(ang) + 0.03, ty + 0.3 * math.sin(ang) + 0.03, FFL + 0.72), W, 0.8, rng=rng)
    for sx, sy in ((tx - 0.85, ty + 0.1), (tx + 0.85, ty - 0.15)):
        fu.cylinder((sx, sy, FFL + 0.42), (0, 0, 1), 0.17, 0.04, 14, W, 0.8, rand=0.3)
        for a in range(3):
            ang = a * 2 * math.pi / 3
            fu.aabb((sx + 0.1 * math.cos(ang) - 0.02, sy + 0.1 * math.sin(ang) - 0.02, FFL), (sx + 0.1 * math.cos(ang) + 0.02, sy + 0.1 * math.sin(ang) + 0.02, FFL + 0.42), W, 0.8, rng=rng)
    # bowl + bread on table
    soft.superq((tx + 0.1, ty, FFL + 0.80), (0.12, 0.12, 0.04), e=0.6, nu=14, nv=6, mat="MAT_TERRACOTTA_A", rand=0.3)
    soft.superq((tx - 0.2, ty + 0.15, FFL + 0.80), (0.10, 0.07, 0.05), e=0.6, nu=12, nv=6, mat="MAT_DOOR_PLANK_A", rand=0.9)
    # fireplace on east wall (chimney breast inside), firebox, hearth, mantel, logs, fire
    fx = xi1
    fb = "MAT_STONE_QUOIN_DRESSED_A"
    fu.aabb((fx - 0.42, -0.75, FFL), (fx, -0.42, CEIL), fb, 1.8, rand=0.3)
    fu.aabb((fx - 0.42, 0.42, FFL), (fx, 0.75, CEIL), fb, 1.8, rand=0.5)
    fu.aabb((fx - 0.42, -0.42, FFL + 1.05), (fx, 0.42, CEIL), fb, 1.8, rand=0.7)
    fu.aabb((fx - 0.08, -0.42, FFL), (fx, 0.42, FFL + 1.05), "MAT_SOOT_A", 1.0, rand=0.1)
    fu.aabb((fx - 0.95, -0.9, FFL), (fx, 0.9, FFL + 0.05), fb, 1.8, rand=0.2)
    fu.aabb((fx - 0.52, -0.92, FFL + 1.05), (fx - 0.40, 0.92, FFL + 1.20), W, 1.0, rng=rng)
    for i in range(3):
        fu.cylinder((fx - 0.35, -0.28 + i * 0.1, FFL + 0.10 + (i % 2) * 0.08), (0.2, 1, 0.05 * (i - 1)), 0.055, 0.42, 8, W, 0.5, rand=0.2 + i * 0.1)
    fu.superq((fx - 0.32, -0.02, FFL + 0.22), (0.16, 0.16, 0.12), e=0.9, nu=10, nv=6, mat="MAT_FIRE_EMIT_A", rand=0.5)
    # pot on hook
    fu.superq((fx - 0.32, 0.0, FFL + 0.62), (0.13, 0.13, 0.12), e=0.8, nu=14, nv=6, mat="MAT_IRON_WROUGHT_A", rand=0.5)
    # barrel / basket / bucket / jar by the door (runtime prototype positions)
    add_barrel(fu, (xi0 + 0.45, yi0 + 0.45, FFL), 0.27, 0.7, rng)
    add_barrel(fu, (xi1 - 0.5, yi0 + 0.35, FFL), 0.16, 0.30, rng)
    soft.superq((xi1 - 1.1, yi0 + 0.35, FFL + 0.14), (0.22, 0.17, 0.14), e=0.5, nu=14, nv=6, mat="MAT_DOOR_PLANK_A", rand=0.2)
    soft.superq((xi1 - 0.35, yi0 + 0.95, FFL + 0.25), (0.15, 0.15, 0.25), e=0.85, nu=14, nv=8, mat="MAT_TERRACOTTA_A", rand=0.6)
    # wall pegs with cloak (west wall, beside bed window)
    fu.aabb((xi0, -0.35, FFL + 1.65), (xi0 + 0.04, 0.55, FFL + 1.73), W, 0.8, rng=rng)
    soft.superq((xi0 + 0.10, 0.25, FFL + 1.20), (0.06, 0.24, 0.48), e=0.7, nu=12, nv=8, mat="MAT_FABRIC_WOOL_GREEN_A", rand=0.1,
                disp=lambda p: Vector((p.x + 0.04 * (p.z / 0.48 + 1) * 0.5, p.y * (1.0 - 0.25 * (p.z / 0.48)), p.z)))
    fu.build(M, C["INTERIOR"])
    soft.build(M, C["INTERIOR"])


def add_barrel(mb, base, r, h, rng, mat="MAT_DOOR_PLANK_A"):
    mb.cylinder(base, (0, 0, 1), r, h, 16, mat, 0.6, rand=rng.random(),
                rfun=lambda t, a: 1.0 + 0.10 * math.sin(t * math.pi) + 0.006 * math.sin(a * 16), rings=6)
    for t in (0.12, 0.88):
        rr = r * (1.0 + 0.10 * math.sin(t * math.pi)) + 0.004
        mb.cylinder((base[0], base[1], base[2] + h * t - 0.02), (0, 0, 1), rr, 0.04, 16, "MAT_IRON_WROUGHT_A", 0.3, cap=True)


def build_props(M, C, rng):
    mb = MB("GEO_AIDANHOUSE_PROPS_EXT")
    W = "MAT_TIMBER_OAK_WEATHERED_A"
    # woodpile against east gable wall (south of chimney), small slate-topped lean-to
    x0 = L / 2 + 0.08
    for row in range(5):
        z = 0.04 + row * 0.15
        y = -2.65 + (row % 2) * 0.07
        while y < -1.05 - (row * 0.05):
            r = rng.uniform(0.055, 0.085)
            ln = rng.uniform(0.42, 0.52)
            seg = 7
            mb.cylinder((x0 + rng.uniform(0, 0.04), y + r, z + r), (1, rng.uniform(-0.05, 0.05), rng.uniform(-0.03, 0.03)), r, ln, seg, W, 0.5,
                        rand=rng.random(), rfun=lambda t, a, rr=rng.random(): 1.0 + 0.12 * math.sin(a * 3 + rr * 6))
            y += 2 * r + 0.01
    for yy in (-2.75, -0.95):
        mb.aabb((x0 + 0.52, yy, 0.0), (x0 + 0.60, yy + 0.08, 1.15), W, 1.0, rng=rng)
    # water barrel at front-west corner, flower box under front-west window, bench under front-east window
    add_barrel(mb, (-L / 2 - 0.42, -D / 2 - 0.40, 0.0), 0.32, 0.86, rng)
    mb.cylinder((-L / 2 - 0.42, -D / 2 - 0.40, 0.80), (0, 0, 1), 0.31, 0.01, 16, "MAT_GLASS_CROWN_A", 1.0, rand=0.1)
    fbx0, fbx1 = -L / 2 + 2.0 - 0.6, -L / 2 + 2.0 + 0.6
    zf = 1.08
    mb.aabb((fbx0, -D / 2 - 0.30, zf), (fbx1, -D / 2 - 0.03, zf + 0.20), "MAT_DOOR_PLANK_A", 0.8, rand=0.4)
    for xx in (fbx0 + 0.1, fbx1 - 0.14):
        mb.box(Vector((xx, -D / 2 - 0.03, zf - 0.22)), Vector((0.04, 0, 0)), Vector((0, -0.24, 0.22)), Vector((0, -0.0, 0.0)) + Vector((0, 0.0, 0.04)), W, 1.0, rng=rng)
    fl = MB("GEO_AIDANHOUSE_PROPS_PLANTS")
    for i in range(22):
        px = rng.uniform(fbx0 + 0.06, fbx1 - 0.06)
        py = rng.uniform(-D / 2 - 0.26, -D / 2 - 0.07)
        fl.superq((px, py, zf + 0.24), (0.06, 0.06, 0.05), e=1.0, nu=6, nv=4, mat="MAT_FOLIAGE_A", rand=rng.random())
        if rng.random() < 0.7:
            fl.superq((px + rng.uniform(-0.03, 0.03), py, zf + 0.30 + rng.uniform(0, 0.05)), (0.025, 0.025, 0.02), e=1.0, nu=6, nv=4,
                      mat="MAT_FLOWER_RED_A", rand=rng.random())
    # bench
    bx = L / 2 - 2.55
    mb.aabb((bx, -D / 2 - 0.48, 0.42), (bx + 1.1, -D / 2 - 0.12, 0.47), W, 1.0, rng=rng)
    for xx in (bx + 0.08, bx + 0.94):
        mb.aabb((xx, -D / 2 - 0.42, 0.0), (xx + 0.08, -D / 2 - 0.18, 0.42), W, 1.0, rng=rng)
    # chopping block + split log
    mb.cylinder((L / 2 + 1.3, -2.1, 0.0), (0, 0, 1), 0.26, 0.42, 12, W, 0.6, rand=0.3)
    mb.cylinder((L / 2 + 1.25, -2.12, 0.42), (0, 0, 1), 0.09, 0.30, 7, W, 0.5, rand=0.7)
    # washing line on the west side (wind motif): posts, line, three cloths with wind sag
    for yy in (-2.2, 2.2):
        mb.aabb((-L / 2 - 1.75, yy - 0.05, 0.0), (-L / 2 - 1.65, yy + 0.05, 2.05), W, 1.0, rng=rng)
    mb.cylinder((-L / 2 - 1.70, -2.2, 1.95), (0, 1, 0), 0.006, 4.4, 6, "MAT_LINEN_A", 0.3, cap=True)
    cl = MB("GEO_AIDANHOUSE_PROPS_LAUNDRY")
    for i, (yc, wdt, hgt, mat) in enumerate(((-1.2, 0.8, 0.9, "MAT_LINEN_A"), (0.05, 0.6, 0.55, "MAT_FABRIC_WOOL_GREEN_A"), (1.05, 0.9, 1.0, "MAT_LINEN_A"))):
        nu, nv = 8, 6
        grid = []
        for j in range(nv + 1):
            row = []
            for k in range(nu + 1):
                v = j / nv
                u = k / nu
                x = -L / 2 - 1.70 + 0.10 * v * v + 0.025 * math.sin(u * 6.2 + i) * v
                y = yc - wdt / 2 + wdt * u
                z = 1.95 - hgt * v + 0.02 * math.sin(u * 3.1) * (1 - v)
                row.append(cl.vert((x, y, z)))
            grid.append(row)
        for j in range(nv):
            for k in range(nu):
                q = [grid[j][k], grid[j + 1][k], grid[j + 1][k + 1], grid[j][k + 1]]
                cl.poly(q, [(k / nu, j / nv), (k / nu, (j + 1) / nv), ((k + 1) / nu, (j + 1) / nv), ((k + 1) / nu, j / nv)], mat, 0.5)
    # low shrubs at foundation corners
    for (px, py) in ((-L / 2 - 0.3, D / 2 - 0.6), (L / 2 + 0.35, D / 2 - 0.4), (-L / 2 + 0.8, -D / 2 - 0.35), (L / 2 - 0.7, D / 2 + 0.35)):
        for i in range(5):
            s = rng.uniform(0.18, 0.32)
            fl.superq((px + rng.uniform(-0.3, 0.3), py + rng.uniform(-0.2, 0.2), s * 0.7), (s, s, s * 0.8), e=1.0, nu=8, nv=6,
                      mat="MAT_FOLIAGE_A", rand=rng.random(),
                      disp=lambda p, sd=rng.random(): p * (1 + 0.25 * noise3(p.x * 9, p.y * 9, p.z * 9, sd * 9)))
    mb.build(M, C["PROPS_EXT"])
    fl.build(M, C["PROPS_EXT"])
    cl.build(M, C["PROPS_EXT"])


def build_staging(M, C, rng):
    """STG_ objects: ground and path for presentation only; footprint is NOT locked and terrain is WORLD's job."""
    mb = MB("STG_AIDANHOUSE_GROUND")
    n = 40
    S = 30.0
    g = [[mb.vert((-S / 2 + S * i / n, -S / 2 + S * j / n, -0.01 + 0.03 * noise3(i * 0.4, j * 0.4, 0))) for i in range(n + 1)] for j in range(n + 1)]
    for j in range(n):
        for i in range(n):
            mb.poly([g[j][i], g[j][i + 1], g[j + 1][i + 1], g[j + 1][i]], [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)], "STG_MAT_GRASS", 0.5)
    mb.build(M, C["STAGING"])
    ps = MB("STG_AIDANHOUSE_PATH")
    y = -D / 2 - 1.55
    while y > -12:
        for k in range(2):
            sx = rng.uniform(-0.45, 0.45)
            s = rng.uniform(0.22, 0.34)
            ps.superq((sx, y + rng.uniform(-0.08, 0.08), 0.015), (s, s * rng.uniform(0.7, 1.0), 0.04), e=0.45, nu=10, nv=4,
                      mat="MAT_STONE_QUOIN_DRESSED_A", tile=1.8, rand=rng.random())
        y -= rng.uniform(0.55, 0.7)
    # outside step
    ps.aabb((-0.75, -D / 2 - 0.55, 0.0), (0.75, -D / 2 - 0.06, 0.13), "MAT_STONE_QUOIN_DRESSED_A", 1.8, rand=0.55)
    ps.build(M, C["STAGING"])


def build_collision_anchors(C):
    def col(name, lo, hi):
        me = bpy.data.meshes.new(name)
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)]
        me.from_pydata(v, [], f)
        ob = bpy.data.objects.new(name, me)
        ob.display_type = "WIRE"
        ob.hide_render = True
        ob["collision"] = "box"
        C["COLLISION"].objects.link(ob)
    h = 2.5
    col("COL_AIDANHOUSE_wall_front_w", (-L / 2, -D / 2, 0), (-0.58, -D / 2 + T, h))
    col("COL_AIDANHOUSE_wall_front_e", (0.58, -D / 2, 0), (L / 2, -D / 2 + T, h))
    col("COL_AIDANHOUSE_wall_rear", (-L / 2, D / 2 - T, 0), (L / 2, D / 2, h))
    col("COL_AIDANHOUSE_wall_west", (-L / 2, -D / 2, 0), (-L / 2 + T, D / 2, h))
    col("COL_AIDANHOUSE_wall_east", (L / 2 - T, -D / 2, 0), (L / 2, D / 2, h))
    xi0, xi1, yi1 = -L / 2 + T, L / 2 - T, D / 2 - T
    col("COL_AIDANHOUSE_bed", (xi0, yi1 - 1.06, FFL), (xi0 + 2.02, yi1, FFL + 1.0))
    col("COL_AIDANHOUSE_chest", (xi0 + 2.1, yi1 - 0.56, FFL), (xi0 + 2.8, yi1, FFL + 0.55))
    col("COL_AIDANHOUSE_cupboard", (-1.56, yi1 - 0.47, FFL), (-0.69, yi1, FFL + 1.8))
    col("COL_AIDANHOUSE_shelf", (2.4, yi1 - 0.32, FFL), (3.6, yi1, FFL + 1.9))
    col("COL_AIDANHOUSE_table", (-0.15, -0.75, FFL), (0.95, 0.35, FFL + 0.8))
    col("COL_AIDANHOUSE_fireplace", (xi1 - 0.95, -0.9, FFL), (xi1, 0.9, FFL + 1.2))
    col("COL_AIDANHOUSE_porch_posts", (-1.15, -D / 2 - 1.36, 0), (1.15, -D / 2 - 1.20, h))
    col("COL_AIDANHOUSE_woodpile", (L / 2, -2.8, 0), (L / 2 + 0.7, -0.9, 1.2))
    col("COL_AIDANHOUSE_barrel_ext", (-L / 2 - 0.78, -D / 2 - 0.76, 0), (-L / 2 - 0.06, -D / 2 - 0.04, 0.9))

    def anc(name, loc, rot_z, kind, runtime_id, links_to=""):
        e = bpy.data.objects.new(name, None)
        e.empty_display_type = "PLAIN_AXES"
        e.empty_display_size = 0.3
        e.location = loc
        e.rotation_euler = (0, 0, rot_z)
        e["anchor_kind"] = kind
        e["links_to"] = links_to
        e["runtime_map"] = "rilde_in_aidan" if not name.endswith("_EXT") else "rilde_village"
        e["runtime_id"] = runtime_id
        e["status"] = "CANDIDATE_G4_NOT_RUN"
        C["ANCHORS"].objects.link(e)
    anc("ANC_AIDANHOUSE_DOOR_MAIN_EXT", (0, -D / 2 - 0.6 - 0.1, 0.0), math.pi, "door", "from_aidan", "ANC_AIDANHOUSE_DOOR_MAIN_INT")
    anc("ANC_AIDANHOUSE_DOOR_MAIN_INT", (0, -D / 2 + T + 0.6, FFL), 0.0, "door", "tr_exit/from_village", "ANC_AIDANHOUSE_DOOR_MAIN_EXT")
    anc("ANC_AIDANHOUSE_SPAWN_BEDSIDE", (-L / 2 + T + 1.1, D / 2 - T - 1.6, FFL), math.pi, "spawn", "from_bed")
    anc("ANC_AIDANHOUSE_EVENT_BED", (-L / 2 + T + 1.0, D / 2 - T - 0.55, FFL), math.pi, "event", "ev_bed_04")
    anc("ANC_AIDANHOUSE_SAVE_BED", (-L / 2 + T + 1.0, D / 2 - T - 0.55, FFL), math.pi, "save", "candidate_save_bed")
    anc("ANC_AIDANHOUSE_EVENT_FIREPLACE", (L / 2 - T - 1.1, 0.0, FFL), -math.pi / 2, "event", "ev_fireplace_08")
    anc("ANC_AIDANHOUSE_EVENT_SHELF", (3.0, D / 2 - T - 0.8, FFL), 0.0, "event", "ev_shelf_books_10")
    anc("ANC_AIDANHOUSE_EVENT_CUPBOARD", (-1.12, D / 2 - T - 0.9, FFL), 0.0, "event", "ev_cupboard_06")
    anc("ANC_AIDANHOUSE_EVENT_TABLE", (0.4, -0.95, FFL), 0.0, "event", "ev_table_round_13")
    anc("ANC_AIDANHOUSE_EVENT_JAR", (L / 2 - T - 0.35, -D / 2 + T + 1.45, FFL), 0.0, "event", "ev_jar_19")


def setup_world_lights(scene, C):
    w = bpy.data.worlds.new("STG_WORLD")
    scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background") or w.node_tree.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = srgb((0.64, 0.74, 0.88))
    bg.inputs["Strength"].default_value = 0.85
    sun = bpy.data.lights.new("LGT_SUN", "SUN")
    sun.energy = 3.6
    sun.angle = math.radians(1.5)
    sun.color = (1.0, 0.92, 0.80)
    so = bpy.data.objects.new("LGT_SUN", sun)
    d = Vector((0.55, 0.72, -0.62)).normalized()
    so.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    C["STAGING"].objects.link(so)
    fire = bpy.data.lights.new("LGT_FIRE", "POINT")
    fire.energy = 90
    fire.color = (1.0, 0.55, 0.22)
    fire.shadow_soft_size = 0.15
    fo = bpy.data.objects.new("LGT_FIRE", fire)
    fo.location = (L / 2 - T - 0.45, 0.0, FFL + 0.35)
    C["INTERIOR"].objects.link(fo)
    amb = bpy.data.lights.new("LGT_INT_FILL", "AREA")
    amb.energy = 60
    amb.size = 3.0
    amb.color = (1.0, 0.86, 0.68)
    ao = bpy.data.objects.new("LGT_INT_FILL", amb)
    ao.location = (-0.5, 0.0, CEIL - 0.25)
    C["INTERIOR"].objects.link(ao)
    cand = bpy.data.lights.new("LGT_CANDLE", "POINT")
    cand.energy = 6
    cand.color = (1.0, 0.65, 0.3)
    cand.shadow_soft_size = 0.02
    co = bpy.data.objects.new("LGT_CANDLE", cand)
    co.location = (-L / 2 + T + 2.45, D / 2 - T - 0.30, FFL + 0.70)
    C["INTERIOR"].objects.link(co)


# ----------------------------------------------------------------------------------------------
# Manifest / geometry hash
# ----------------------------------------------------------------------------------------------
def tri_count(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def geo_hash():
    h = hashlib.sha256()
    for ob in sorted(bpy.data.objects, key=lambda o: o.name):
        h.update(ob.name.encode())
        if ob.type == "MESH":
            me = ob.data
            co = [0.0] * (len(me.vertices) * 3)
            me.vertices.foreach_get("co", co)
            h.update(",".join("%.5f" % c for c in co).encode())
            h.update(str(len(me.polygons)).encode())
    return h.hexdigest()


def manifest(scene, C, cells_log, stats, zs_main, zs_gable, ops):
    cols = {}
    for name, c in C.items():
        if name.startswith("_"):
            continue
        t = sum(tri_count(o.data) for o in c.objects if o.type == "MESH")
        cols[name] = {"objects": sorted(o.name for o in c.objects), "tris": t}
    kinds = {}
    for _, k, *_ in cells_log:
        kinds[k] = kinds.get(k, 0) + 1
    mats = sorted({m.name for m in bpy.data.materials if m.users})
    return {
        "task_id": "LIND-HOME-01",
        "script": SCRIPT_VERSION,
        "blender": bpy.app.version_string,
        "seed": SEED,
        "status": "CANDIDATE_NOT_ART_APPROVED",
        "masonry_family": "F9 layout-outline pillowed rubble",
        "dimensions_m": {"L": L, "D": D, "T": T, "FFL": FFL, "wall_top": WALL_TOP, "pitch_deg": round(math.degrees(PITCH), 2),
                         "eave_oh": EAVE_OH, "verge_oh": VERGE_OH, "ridge_z": round(Z_RIDGE, 3), "chimney_top": round(CHIM_TOP, 3)},
        "course_grid_main": [round(z, 3) for z in zs_main],
        "course_grid_gable": [round(z, 3) for z in zs_gable],
        "openings": {f: [{k: v for k, v in op.items() if k in ("id", "kind", "u0", "u1", "clear", "z")} for op in lst] for f, lst in ops.items()},
        "stone_counts_by_face": stats,
        "stone_cells_by_kind": kinds,
        "slate_count": C.get("_slate_count"),
        "collections": cols,
        "materials": mats,
        "textures": TEX_STATUS,
        "geometry_sha256": geo_hash(),
    }


# ----------------------------------------------------------------------------------------------
# Cameras / rendering
# ----------------------------------------------------------------------------------------------
VIEWS = {
    "front_three_quarter": dict(loc=(-11.5, -15.5, 5.2), tgt=(0.3, 0, 2.9), lens=40, res=(1280, 800)),
    "rear_three_quarter": dict(loc=(12.5, 15.0, 6.0), tgt=(0.0, 0, 3.0), lens=40, res=(1280, 800)),
    "closeup_masonry_roof": dict(loc=(7.6, -6.6, 2.3), tgt=(4.0, -3.2, 3.2), lens=42, res=(1280, 800)),
    "interior_bedside": dict(loc=(1.6, -2.15, 1.65), tgt=(-3.0, 1.9, 0.75), lens=17, res=(1280, 800), interior=True),
    "game_27deg": dict(ortho=True, elev=27, azim=-45, scale=17.0, res=(768, 768)),
}


def set_camera(scene, view):
    cam = bpy.data.objects.get("CAM_VIEW")
    if cam is None:
        cd = bpy.data.cameras.new("CAM_VIEW")
        cam = bpy.data.objects.new("CAM_VIEW", cd)
        scene.collection.objects.link(cam)
    scene.camera = cam
    v = VIEWS[view]
    cd = cam.data
    if v.get("ortho"):
        cd.type = "ORTHO"
        cd.ortho_scale = v["scale"]
        el, az = math.radians(v["elev"]), math.radians(v["azim"])
        tgt = Vector((0, 0, 2.6))
        # azimuth -45 deg: camera on the front-left (-X,-Y) side
        dirv = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
        cam.location = tgt + dirv * 40
        cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
        cd.clip_end = 200
    else:
        cd.type = "PERSP"
        cd.lens = v["lens"]
        cd.clip_start = 0.05
        cam.location = v["loc"]
        cam.rotation_euler = (Vector(v["tgt"]) - Vector(v["loc"])).to_track_quat("-Z", "Y").to_euler()
    scene.render.resolution_x, scene.render.resolution_y = v["res"]
    scene.render.resolution_percentage = 100
    return cam


def render(out_dir, views, samples=48, pct=100):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.seed = 0
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    scene.cycles.max_bounces = 6
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 2
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 0.0
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    out = {}
    for v in views:
        set_camera(scene, v)
        scene.render.resolution_percentage = pct
        interior = VIEWS[v].get("interior", False)
        scene.cycles.samples = 64 if interior else samples
        scene.view_settings.exposure = 0.6 if interior else 0.0
        if v == "game_27deg":
            # in-game scale is checked on the asset alone: hide staging ground, keep transparent film
            for o in bpy.data.collections["STAGING"].objects:
                o.hide_render = o.type == "MESH"
            scene.render.film_transparent = True
            scene.render.image_settings.color_mode = "RGBA"
        else:
            for o in bpy.data.collections["STAGING"].objects:
                o.hide_render = False
            scene.render.film_transparent = False
            scene.render.image_settings.color_mode = "RGB"
        path = os.path.join(out_dir, v + ".png")
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        out[v] = path
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--render", default="none", help="none | all | comma list of " + ",".join(VIEWS))
    ap.add_argument("--samples", type=int, default=48)
    ap.add_argument("--pct", type=int, default=100, help="resolution percentage (previews)")
    ap.add_argument("--blend", default="", help="optional path to save the .blend")
    a = ap.parse_args(argv)
    man = build(a.out)
    if a.blend:
        os.makedirs(os.path.dirname(os.path.abspath(a.blend)), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.blend), compress=True)
        man["blend_path_uncommitted"] = os.path.abspath(a.blend)
    views = [] if a.render == "none" else (list(VIEWS) if a.render == "all" else a.render.split(","))
    if views:
        r = render(a.out, views, a.samples, a.pct)
        man["renders"] = {k: {"path": os.path.relpath(p, a.out), "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest()} for k, p in r.items()}
        man["render_settings"] = {"engine": "CYCLES", "samples_ext": a.samples, "samples_int": 64, "denoise": "OIDN", "view_transform": "AgX",
                                  "cameras": VIEWS}
    with open(os.path.join(a.out, "build_manifest.json"), "w") as fh:
        json.dump(man, fh, indent=1, sort_keys=True, default=str)
    print("BUILD_OK", json.dumps({k: man[k] for k in ("geometry_sha256", "slate_count", "stone_cells_by_kind")}))
    print("TRIS", {k: v["tris"] for k, v in man["collections"].items()})


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(argv)

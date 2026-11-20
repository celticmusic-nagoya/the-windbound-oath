"""C11 Method E: individually sculpted polyhedral rock masses inside the repair islands.

Independent G2 on D4 (PR #421): FAIL. Vertical grooves read artificial, and rock-mass
structure and hardness are insufficient. UV improvement to be kept. Director: switch
to per-block sculpting of the main rock masses and joints; reproduce the official
CG's irregular polygonal blocks, fracture faces and asymmetric ridgelines; no
straight grooves, no uniform columnar division, no over-smoothing.

Structural difference from D4 (method-family switch, recorded):
  D4 = one plane per uniform columnar Voronoi cell, boundaries height-AVERAGED (no
  true ridges/valleys), plus one long straight constrained riser.
  E  = union of individually authored convex rock blocks. Each block is the min()
  of its own planes: a tilted front plane, an optional fracture fold plane, a steep
  asymmetric side plane per joint edge, and corner chip planes. The surface is
  max(blocks, joint floor). Ridges and valleys are therefore EXACT plane-plane
  intersections. They are extracted from a label map, snapped analytically and
  inserted as constrained edges, so creases are crisp and mesh-aligned. Block
  footprints come from a power diagram with variable spacing and weights
  (irregular sizes and polygons). The main fracture is a zig-zag of short
  non-collinear block joints with varying depth.
UV: unchanged D4 method (exact-boundary 3D mean-value harmonic map + untangle).

  blender -b --factory-startup --python c11_method_e_block_sculpt.py -- D4.blend METHOD_C.blend OUT_DIR
Inputs are SHA-pinned and never modified. Output: CANDIDATE ONLY.
"""
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c11_method_d4_joint_facets as d4  # noqa: E402  (helpers only; D4 main not run)
from c11_uv_qa import island_uv_report  # noqa: E402

D4_SHA = "0e560afc031f2356ade277e7b4f89eb01a2e62acdcda780c1c366112b90d99ff"
D4_GEOMETRY_SHA = "ec2af2d59f922157de5a6f336c5c99208102e648a67b140a2f8eb994c42e0274"
METHOD_C_SHA = d4.METHOD_C_SHA
TARGET = d4.TARGET
RAILS = (
    {"name": "west_fracture", "pts": ((-7.35, 0.95), (-7.47, 2.35), (-7.98, 4.80), (-8.24, 6.95)), "seed": 11},
    {"name": "central_fracture", "pts": ((-5.42, 2.30), (-5.72, 3.62), (-5.97, 5.05), (-5.67, 6.80)), "seed": 23},
)
GRID = 0.008          # label-map resolution (domain units)
FILL = 0.06           # interior sample spacing
EDGE_MARGIN = 0.06    # creases stop this far inside the locked perimeter
FADE = 0.12           # block relief -> locked perimeter blend band
FLOOR_DEPTH = 0.26    # deepest joint floor below the mass form
SHARP_DEG = 12.0
PROTRUDE_MAX = 0.12   # block face above the mass form
RECESS_MAX = 0.20     # block face below the mass form
MIN_COMPONENT_FACES = 50
hash01 = d4.hash01
smoothstep = d4.smoothstep


def inside_mask(P, poly):
    """Vectorised even-odd point-in-polygon for (n,2) points."""
    x, y = P[:, 0], P[:, 1]
    inside = np.zeros(len(P), bool)
    n = len(poly)
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[i - 1]
        cond = (yi > y) != (yj > y)
        xint = (xj - xi) * (y - yi) / (yj - yi + 1e-30) + xi
        inside ^= cond & (x < xint)
    return inside


def dist_to_poly_vec(P, poly):
    d = np.full(len(P), np.inf)
    n = len(poly)
    for i in range(n):
        a = np.array(poly[i])
        b = np.array(poly[(i + 1) % n])
        ab = b - a
        t = np.clip(((P - a) @ ab) / (ab @ ab + 1e-30), 0, 1)
        d = np.minimum(d, np.linalg.norm(P - (a + t[:, None] * ab), axis=1))
    return d


class MassForm:
    """Harmonic mass form T on a grid (Dirichlet from the locked perimeter)."""

    def __init__(self, poly, heights, pad=0.5, res=0.02):
        P = np.array(poly)
        self.x0, self.y0 = P.min(0) - pad
        x1, y1 = P.max(0) + pad
        self.res = res
        nx = int((x1 - self.x0) / res) + 2
        ny = int((y1 - self.y0) / res) + 2
        gx, gy = np.meshgrid(self.x0 + res * np.arange(nx), self.y0 + res * np.arange(ny))
        G = np.c_[gx.ravel(), gy.ravel()]
        ins = inside_mask(G, poly)
        H = np.array(heights)
        # IDW from perimeter for outside cells (fixed) and initial guess
        Z = np.zeros(len(G))
        for k in range(0, len(G), 4096):
            d2 = ((G[k:k + 4096, None, :] - P[None, :, :]) ** 2).sum(2) + 1e-6
            w = 1.0 / d2 ** 1.5
            Z[k:k + 4096] = (w * H).sum(1) / w.sum(1)
        Z = Z.reshape(ny, nx)
        ins = ins.reshape(ny, nx)
        for _ in range(6000):
            avg = 0.25 * (np.roll(Z, 1, 0) + np.roll(Z, -1, 0) + np.roll(Z, 1, 1) + np.roll(Z, -1, 1))
            delta = np.abs(avg - Z)[ins].max() if ins.any() else 0
            Z = np.where(ins, avg, Z)
            if delta < 1e-7:
                break
        self.Z = Z
        self.nx, self.ny = nx, ny

    def __call__(self, P):
        P = np.atleast_2d(P)
        fx = np.clip((P[:, 0] - self.x0) / self.res, 0, self.nx - 1.001)
        fy = np.clip((P[:, 1] - self.y0) / self.res, 0, self.ny - 1.001)
        ix, iy = fx.astype(int), fy.astype(int)
        tx, ty = fx - ix, fy - iy
        Z = self.Z
        return ((1 - tx) * (1 - ty) * Z[iy, ix] + tx * (1 - ty) * Z[iy, ix + 1] +
                (1 - tx) * ty * Z[iy + 1, ix] + tx * ty * Z[iy + 1, ix + 1])

    def grad(self, p, e=0.03):
        p = np.asarray(p, float)
        gx = (self(p + [e, 0])[0] - self(p - [e, 0])[0]) / (2 * e)
        gy = (self(p + [0, e])[0] - self(p - [0, e])[0]) / (2 * e)
        return np.array([gx, gy])


def plane_through(a, ha, b, hb, inward, slope):
    """Plane h = g.p + c containing the 3D line (a,ha)-(b,hb), rising along
    `inward` (unit, perpendicular to a-b) with gradient `slope`."""
    t = b - a
    L = np.linalg.norm(t)
    t = t / L
    g = t * (hb - ha) / L + inward * slope
    return g, ha - g @ a


def power_cells(seeds, weights, box):
    cells = []
    S = np.array(seeds)
    W = np.array(weights)
    for i, si in enumerate(seeds):
        cell = list(box)
        d2 = ((S - S[i]) ** 2).sum(1)
        for j in np.argsort(d2)[1:40]:
            sj = S[j]
            nrm = sj - si
            # power bisector: 2 x.(sj-si) <= |sj|^2 - |si|^2 - wj + wi
            rhs = (sj @ sj - si @ si - W[j] + W[i]) / 2.0
            m = nrm * (rhs / (nrm @ nrm))
            cell = d4.clip_halfplane(cell, tuple(m), tuple(nrm))
            if len(cell) < 3:
                break
        cells.append(cell if len(cell) >= 3 else None)
    return cells


def build_blocks(poly, T, rail2d, seed):
    """Author the rock blocks for one island. Returns list of blocks; each block
    = list of (g(2,), c) planes, plus metadata."""
    P = np.array(poly)
    lo, hi = P.min(0) - 0.35, P.max(0) + 0.35
    seeds, wts, tags = [], [], []
    # main fracture: zig-zag seed pairs straddling the rail (short, non-collinear joints)
    if rail2d is not None:
        Lr = sum(np.linalg.norm(np.array(b) - np.array(a)) for a, b in zip(rail2d, rail2d[1:]))
        s = 0.06 + 0.04 * hash01(seed, 1)
        k = 0
        while s < 0.9:
            p, t = d4.poly_point(rail2d, s)
            p = np.array(p)
            nrm = np.array([t[1], -t[0]])
            off = 0.24 + 0.14 * hash01(seed, k, 2)
            shift = (hash01(seed, k, 3) - 0.5) * 0.30
            for sg in (1, -1):
                q = p + sg * off * nrm + np.array(t) * (shift * sg)
                seeds.append(q)
                wts.append((0.05 + 0.12 * hash01(seed, k, sg)) ** 2)
                tags.append(1)
            s += (0.60 + 0.45 * hash01(seed, k, 4)) / Lr
            k += 1
    # variable-radius dart throwing (deterministic) for the remaining masses
    tries = 0
    while tries < 6000:
        tries += 1
        q = lo + (hi - lo) * np.array([hash01(seed, tries, 7), hash01(seed, tries, 8)])
        r = 0.45 + 0.45 * hash01(seed, tries, 9)
        if seeds and min(np.linalg.norm(q - s_) for s_ in seeds) < r:
            continue
        seeds.append(q)
        wts.append((0.05 + 0.22 * hash01(seed, tries, 10)) ** 2)
        tags.append(0)
    box = [tuple(lo - 1), (hi[0] + 1, lo[1] - 1), tuple(hi + 1), (lo[0] - 1, hi[1] + 1)]
    cells = power_cells(seeds, wts, box)
    # joint depth per footprint vertex (shared by neighbouring blocks -> consistent joints)
    def vdepth(v, main):
        base = 0.035 + 0.085 * hash01(round(v[0], 4), round(v[1], 4), seed)
        return base * (1.6 if main else 1.0)
    blocks = []
    for bi, cell in enumerate(cells):
        if cell is None:
            continue
        C = np.array(cell)
        cen = C.mean(0)
        if not (inside_mask(C, poly).any() or inside_mask(cen[None], poly)[0]):
            if d4.dist_to_poly(tuple(cen), poly) > 0.4:
                continue
        # front plane: least-squares fit of the mass form over the block's own
        # footprint (no pyramid apex on convex flanks) + offset + asymmetric tilt
        lo_c, hi_c = C.min(0), C.max(0)
        gx_, gy_ = np.meshgrid(np.linspace(lo_c[0], hi_c[0], 12), np.linspace(lo_c[1], hi_c[1], 12))
        S_ = np.c_[gx_.ravel(), gy_.ravel()]
        S_ = S_[inside_mask(S_, [tuple(p) for p in C])]
        if len(S_) < 6:
            S_ = np.vstack([C, cen[None]])
        A_ = np.c_[S_, np.ones(len(S_))]
        coef, *_ = np.linalg.lstsq(A_, T(S_), rcond=None)
        gT = coef[:2]
        Tc = float(coef[:2] @ cen + coef[2])
        planes, kinds = [], []
        o = 0.01 + 0.04 * hash01(seed, bi, 11)
        tilt = math.radians(5 + 8 * hash01(seed, bi, 12))
        az = 2 * math.pi * hash01(seed, bi, 13)
        g = gT + math.tan(tilt) * np.array([math.cos(az), math.sin(az)])
        c = Tc + o - g @ cen
        # protrusion limit: the block face may stand at most PROTRUDE_MAX above
        # and RECESS_MAX below the mass form anywhere on its footprint (no spikes)
        dev_ = S_ @ g + c - T(S_)
        if dev_.max() > PROTRUDE_MAX:
            c -= dev_.max() - PROTRUDE_MAX
        dev_ = S_ @ g + c - T(S_)
        if dev_.min() < -RECESS_MAX:
            # too tilted for this footprint: reduce the tilt to the fitted plane
            g = gT.copy()
            c = Tc + o - g @ cen
            c -= max(0.0, (S_ @ g + c - T(S_)).max() - PROTRUDE_MAX)
        front = (g.copy(), c)
        planes.append((g, c))
        kinds.append("front")
        # fracture fold (broken face, convex ridge) on ~half of the blocks
        if hash01(seed, bi, 14) < 0.5:
            ang = math.pi * hash01(seed, bi, 15)
            d = np.array([math.cos(ang), math.sin(ang)])
            q = cen + (hash01(seed, bi, 16) - 0.5) * 0.5 * np.array([-d[1], d[0]])
            nperp = np.array([-d[1], d[0]])
            fold = math.radians(8 + 10 * hash01(seed, bi, 17))
            g2 = g + math.tan(fold) * nperp * (1 if hash01(seed, bi, 18) < 0.5 else -1)
            c2 = (g @ q + c) - g2 @ q
            planes.append((g2, c2))
            kinds.append("fold")
        # steep asymmetric side planes, one per joint edge
        n = len(C)
        area2 = sum(C[i, 0] * C[(i + 1) % n, 1] - C[(i + 1) % n, 0] * C[i, 1] for i in range(n))
        for i in range(n):
            a, b = C[i], C[(i + 1) % n]
            if np.linalg.norm(b - a) < 1e-4:
                continue
            t = (b - a) / np.linalg.norm(b - a)
            inward = np.array([-t[1], t[0]]) if area2 > 0 else np.array([t[1], -t[0]])
            main = tags[bi] == 1
            # side planes start below this block's own front plane (offset joints)
            ha = float(front[0] @ a + front[1]) - o - vdepth(a, main)
            hb = float(front[0] @ b + front[1]) - o - vdepth(b, main)
            alpha = math.radians(38 + 26 * hash01(seed, bi, i, 19))
            planes.append(plane_through(a, ha, b, hb, inward, math.tan(alpha)))
            kinds.append("side")
        # corner chips: break 1-2 block corners with a plane descending to the corner
        for k in range(2):
            if hash01(seed, bi, k, 20) < 0.35:
                i = int(hash01(seed, bi, k, 21) * n) % n
                v = C[i]
                e1 = C[(i + 1) % n] - v
                e0 = C[i - 1] - v
                l1, l0 = np.linalg.norm(e1), np.linalg.norm(e0)
                if min(l1, l0) < 0.30:
                    continue
                r1 = 0.10 + 0.12 * hash01(seed, bi, k, 22)
                r0 = 0.10 + 0.12 * hash01(seed, bi, k, 23)
                p1, p0 = v + e1 / l1 * r1, v + e0 / l0 * r0
                hp = lambda p: min(gg @ p + cc for gg, cc in planes)
                t = p1 - p0
                inward = np.array([-t[1], t[0]])
                if inward @ (cen - (p0 + p1) / 2) < 0:
                    inward = -inward
                inward /= np.linalg.norm(inward)
                # chip rises inward from the cut line, i.e. descends toward the corner
                gch, cch = plane_through(p0, hp(p0) - 0.01, p1, hp(p1) - 0.01, inward,
                                         math.tan(math.radians(30 + 20 * hash01(seed, bi, k, 24))))
                planes.append((gch, cch))
                kinds.append("chip")
        blocks.append({"id": bi, "planes": planes, "kinds": kinds, "main": tags[bi] == 1, "footprint": C})
    return blocks


def evaluate(P, blocks, T):
    """Height and (block, plane) label of the block envelope; label -1 = joint floor."""
    P = np.atleast_2d(P)
    best = np.full(len(P), -np.inf)
    lab = np.full(len(P), -1, int)
    for bk in blocks:
        G = np.array([g for g, _ in bk["planes"]])
        Cc = np.array([c for _, c in bk["planes"]])
        vals = P @ G.T + Cc
        k = vals.argmin(1)
        cap = vals[np.arange(len(P)), k]
        upd = cap > best
        best = np.where(upd, cap, best)
        lab = np.where(upd, bk["id"] * 64 + k, lab)
    floor = T(P) - FLOOR_DEPTH
    fl = floor > best
    return np.where(fl, floor, best), np.where(fl, -1, lab)


def plane_of(label, blocks_by_id):
    if label < 0:
        return None
    return blocks_by_id[label // 64]["planes"][label % 64]


def extract_creases(poly, blocks, T):
    """Crease polylines = boundaries between labels of the envelope, crossing
    points solved exactly on plane pairs; chained and simplified."""
    P = np.array(poly)
    lo, hi = P.min(0), P.max(0)
    nx = int((hi[0] - lo[0]) / GRID) + 2
    ny = int((hi[1] - lo[1]) / GRID) + 2
    gx, gy = np.meshgrid(lo[0] + GRID * np.arange(nx), lo[1] + GRID * np.arange(ny))
    G = np.c_[gx.ravel(), gy.ravel()]
    _, L = evaluate(G, blocks, T)
    L = L.reshape(ny, nx)
    byid = {b["id"]: b for b in blocks}

    def cross(p, q, la, lb):
        pa, pb = plane_of(la, byid), plane_of(lb, byid)
        if pa is None or pb is None:
            return (p + q) / 2
        dg = pa[0] - pb[0]
        dc = pa[1] - pb[1]
        fp, fq = dg @ p + dc, dg @ q + dc
        if fp == fq:
            return (p + q) / 2
        t = min(1.0, max(0.0, fp / (fp - fq)))
        return p + t * (q - p)
    pts = {}

    def key(p):
        return (round(p[0], 6), round(p[1], 6))
    edges = set()
    for j in range(ny - 1):
        for i in range(nx - 1):
            c = [L[j, i], L[j, i + 1], L[j + 1, i + 1], L[j + 1, i]]
            if c[0] == c[1] == c[2] == c[3]:
                continue
            q = [G[j * nx + i], G[j * nx + i + 1], G[(j + 1) * nx + i + 1], G[(j + 1) * nx + i]]
            xs = []
            for k in range(4):
                a, b = k, (k + 1) % 4
                if c[a] != c[b]:
                    xs.append((cross(q[a], q[b], c[a], c[b]), frozenset((c[a], c[b]))))
            if len(xs) == 2:
                ka, kb = key(xs[0][0]), key(xs[1][0])
                pts[ka], pts[kb] = xs[0][0], xs[1][0]
                if ka != kb:
                    edges.add(tuple(sorted((ka, kb))))
            elif len(xs) > 2:
                m = sum(x[0] for x in xs) / len(xs)
                km = key(m)
                pts[km] = m
                for x in xs:
                    kx = key(x[0])
                    pts[kx] = x[0]
                    if kx != km:
                        edges.add(tuple(sorted((kx, km))))
    adj = {}
    for a, b in edges:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    # chain between breakpoints (deg != 2) and Douglas-Peucker simplify
    seen = set()
    chains = []
    for s in adj:
        if len(adj[s]) == 2:
            continue
        for nb in adj[s]:
            e = tuple(sorted((s, nb)))
            if e in seen:
                continue
            chain = [s, nb]
            seen.add(e)
            prev, cur = s, nb
            while len(adj[cur]) == 2:
                nxt = [x for x in adj[cur] if x != prev][0]
                e2 = tuple(sorted((cur, nxt)))
                if e2 in seen:
                    break
                seen.add(e2)
                chain.append(nxt)
                prev, cur = cur, nxt
            chains.append(chain)
    for s in adj:   # closed loops
        for nb in adj[s]:
            e = tuple(sorted((s, nb)))
            if e not in seen:
                chain = [s, nb]
                seen.add(e)
                prev, cur = s, nb
                while True:
                    nxt = [x for x in adj[cur] if x != prev]
                    if not nxt:
                        break
                    e2 = tuple(sorted((cur, nxt[0])))
                    if e2 in seen:
                        break
                    seen.add(e2)
                    chain.append(nxt[0])
                    prev, cur = cur, nxt[0]
                chains.append(chain)

    def dp(pl, tol):
        if len(pl) < 3:
            return pl
        a, b = np.array(pl[0]), np.array(pl[-1])
        dmax, idx = 0.0, 0
        for i in range(1, len(pl) - 1):
            d = d4.seg_dist(pl[i], a, b)
            if d > dmax:
                dmax, idx = d, i
        if dmax > tol:
            return dp(pl[:idx + 1], tol)[:-1] + dp(pl[idx:], tol)
        return [pl[0], pl[-1]]
    polylines = [dp([tuple(pts[k]) for k in ch], 0.0035) for ch in chains]
    return polylines


def build_component(bm, region, rail, comp_name, report):
    loop = d4.perimeter_loop(region, comp_name)
    squeeze, N, U, V, poly = d4.choose_basis(region, loop)
    n = len(loop)
    inner_old = {v for f in region for v in f.verts} - set(loop)
    island_pts = [v.co for f in region for v in f.verts]
    rail2d = []
    for x, z in rail["pts"]:
        near = min(island_pts, key=lambda c: (c.x - x) ** 2 + (c.z - z) ** 2)
        p = Vector((x, near.y, z))
        rail2d.append((p.dot(U), p.dot(V)))
    inside_pts = [s for s in np.linspace(0, 1, 100) if d4.point_in_poly(d4.poly_point(rail2d, s)[0], poly)]
    use_rail = rail2d if len(inside_pts) >= 10 else None
    T = MassForm(poly, [v.co.dot(N) for v in loop])
    blocks = build_blocks(poly, T, use_rail, rail["seed"])
    polylines = extract_creases(poly, blocks, T)
    # constraints: crease polylines subdivided, clipped to EDGE_MARGIN inside
    cpts, cedges, pidx = [], [], {}

    def add_pt(p):
        k = (round(p[0] / 0.01), round(p[1] / 0.01))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                j = pidx.get((k[0] + dx, k[1] + dy))
                if j is not None and math.dist(cpts[j], p) < 0.01:
                    return j
        pidx[k] = len(cpts)
        cpts.append(p)
        return pidx[k]
    longest_straight = 0.0
    for pl in polylines:
        for a_, b_ in zip(pl, pl[1:]):
            L = math.dist(a_, b_)
            m = max(1, int(math.ceil(L / 0.05)))
            prev = None
            run = 0.0
            for t in range(m + 1):
                p = (a_[0] + (b_[0] - a_[0]) * t / m, a_[1] + (b_[1] - a_[1]) * t / m)
                ok = d4.point_in_poly(p, poly) and d4.dist_to_poly(p, poly) > EDGE_MARGIN
                if ok:
                    cur = add_pt(p)
                    if prev is not None and prev != cur:
                        cedges.append((prev, cur))
                        run += L / m
                    prev = cur
                else:
                    prev = None
            longest_straight = max(longest_straight, run)
    cedges = list({tuple(sorted(e)) for e in cedges if e[0] != e[1]})
    # fill points away from constraints and perimeter
    C = np.array(cpts) if cpts else np.zeros((0, 2))
    fill = []
    us = [p[0] for p in poly]
    vs = [p[1] for p in poly]
    j = 0
    z = min(vs) + FILL * 0.5
    while z < max(vs):
        x = min(us) + FILL * (0.5 + 0.5 * (j % 2))
        while x < max(us):
            p = (x + 0.2 * FILL * (hash01(x, z, 5) - 0.5), z + 0.2 * FILL * (hash01(z, x, 6) - 0.5))
            if d4.point_in_poly(p, poly) and d4.dist_to_poly(p, poly) > 0.6 * FILL:
                if not len(C) or np.min(np.hypot(C[:, 0] - p[0], C[:, 1] - p[1])) > 0.45 * FILL:
                    fill.append(p)
            x += FILL
        z += FILL * 0.866
        j += 1
    coords = [Vector(p) for p in poly] + [Vector(p) for p in cpts] + [Vector(p) for p in fill]
    edges_in = [(i, (i + 1) % n) for i in range(n)] + [(n + a, n + b) for a, b in cedges]
    out = delaunay_2d_cdt(coords, edges_in, [list(range(n))], 1, 1e-5)
    o_verts, o_faces, o_orig = out[0], out[2], out[3]
    bmesh.ops.delete(bm, geom=sorted(region, key=lambda f: f.index), context="FACES_ONLY")
    for v in sorted((v for v in inner_old if not v.link_faces), key=lambda v: d4.rkey(v.co)):
        bm.verts.remove(v)
    for e in sorted({e for v in loop for e in v.link_edges if not e.link_faces},
                    key=lambda e: sorted(d4.rkey(v.co) for v in e.verts)):
        bm.edges.remove(e)
    bmv, uv2 = [], []
    for oi, ov in enumerate(o_verts):
        origs = o_orig[oi]
        if origs and origs[0] < n:
            if any(o >= n for o in origs[1:]):
                raise RuntimeError(f"{comp_name}: interior point merged into perimeter; STOP")
            bmv.append(loop[origs[0]])
        else:
            bmv.append(None)
        uv2.append((ov.x, ov.y))
    if sum(b is not None for b in bmv) != n:
        raise RuntimeError(f"{comp_name}: perimeter vertex count changed by CDT; STOP")
    tris = [tuple(t) for t in o_faces if len(set(t)) == 3]
    P2 = np.array(uv2)
    perim = {i for i in range(len(uv2)) if bmv[i] is not None}
    free = [i for i in range(len(uv2)) if i not in perim]
    nbr = [set() for _ in uv2]
    for t in tris:
        for a_ in t:
            nbr[a_] |= set(t) - {a_}
    # mesh-harmonic mass form for the perimeter fade (exact at the locked loop)
    hm = np.array([bmv[i].co.dot(N) if i in perim else float(T(P2[i])[0]) for i in range(len(uv2))])
    for _ in range(3000):
        delta = 0.0
        for i in free:
            val = sum(hm[k] for k in nbr[i]) / len(nbr[i])
            delta = max(delta, abs(val - hm[i]))
            hm[i] = val
        if delta < 1e-7:
            break
    henv, lab = evaluate(P2, blocks, T)
    dper = dist_to_poly_vec(P2, poly)
    w = np.array([smoothstep(0.0, FADE, d) for d in dper])
    hf = (1 - w) * hm + w * henv
    tri_lab = evaluate(np.array([P2[list(t)].mean(0) for t in tris]), blocks, T)[1]
    lay = bm.verts.layers.int["orig_id"]
    for i in free:
        bv = bm.verts.new(U * P2[i][0] + V * P2[i][1] + N * hf[i])
        bv[lay] = -1
        bmv[i] = bv
    faces, flab = [], []
    for t, lb in zip(tris, tri_lab):
        vs3 = [bmv[i] for i in t]
        if len(set(vs3)) == 3:
            faces.append(bm.faces.new(vs3))
            flab.append(int(lb))
    newv = [bmv[i] for i in free]
    newset_v = set(newv)
    state = {bmv[i]: (P2[i], hm[i], hf[i]) for i in free}
    relax_passes = 0
    for relax_passes in range(1, 9):
        bm.verts.index_update()
        tri_old = [tuple(l.vert for l in lt) for lt in bm.calc_loop_triangles()
                   if not any(l.vert in newset_v for l in lt) and any(-9.6 < l.vert.co.x < -4.0 for l in lt)]
        co = [tuple(u.co) for u in bm.verts]
        bn = BVHTree.FromPolygons(co, [[u.index for u in f.verts] for f in faces], all_triangles=True)
        bo = BVHTree.FromPolygons(co, [[u.index for u in t] for t in tri_old], all_triangles=True)
        bad = set()
        for a_, b_ in bn.overlap(bo):
            if not set(faces[a_].verts) & set(tri_old[b_]):
                bad |= {u for u in faces[a_].verts if u in newset_v}
        if not bad:
            break
        for u in bad:
            p2, h0, h1 = state[u]
            h1 = 0.5 * (h0 + h1)
            state[u] = (p2, h0, h1)
            u.co = U * p2[0] + V * p2[1] + N * h1
    # winding from the perimeter
    newset = set(faces)

    def opposite_ok(f, e):
        other = [l for l in e.link_loops if l.face is not f]
        mine = [l for l in e.link_loops if l.face is f]
        return not other or not mine or other[0].vert is not mine[0].vert
    done, queue, flipped = set(), [], 0
    for f in faces:
        for e in f.edges:
            if any(l.face not in newset for l in e.link_loops) and f not in done:
                if not opposite_ok(f, e):
                    f.normal_flip()
                    flipped += 1
                done.add(f)
                queue.append(f)
    while queue:
        f = queue.pop()
        for e in f.edges:
            for g_ in e.link_faces:
                if g_ in newset and g_ not in done:
                    if not opposite_ok(g_, e):
                        g_.normal_flip()
                        flipped += 1
                    done.add(g_)
                    queue.append(g_)
    for f in faces:
        f.smooth = True
        f.normal_update()
    lab_of = dict(zip(faces, flab))
    sharp_n = crease_edges = 0
    dihedrals = []
    for f in faces:
        for e in f.edges:
            lf = e.link_faces
            if len(lf) == 2 and all(x in lab_of for x in lf) and lf[0] is f:
                if lab_of[lf[0]] != lab_of[lf[1]]:
                    crease_edges += 1
                    ang = math.degrees(e.calc_face_angle(0.0))
                    dihedrals.append(ang)
                    e.smooth = ang < SHARP_DEG
                    sharp_n += ang >= SHARP_DEG
                else:
                    e.smooth = True
    # label-region statistics (irregular polygonal masses, not uniform columns)
    areas = {}
    for f, lb in lab_of.items():
        areas[lb] = areas.get(lb, 0.0) + f.calc_area()
    reg = np.array([a for lb, a in areas.items() if lb >= 0])
    fp_area = [abs(sum(b["footprint"][i, 0] * b["footprint"][i - 1, 1] - b["footprint"][i - 1, 0] * b["footprint"][i, 1]
                       for i in range(len(b["footprint"])))) / 2 for b in blocks]
    report[comp_name] = {
        "rail": rail["name"], "main_fracture_from_rail": use_rail is not None,
        "projection_normal": [round(c, 5) for c in N], "perimeter_squeeze_fraction": round(squeeze, 4),
        "perimeter_vertices_locked": n, "old_faces_removed": len(region),
        "old_interior_vertices_removed": len(inner_old),
        "blocks": len(blocks), "block_planes": sum(len(b["planes"]) for b in blocks),
        "fold_planes": sum(b["kinds"].count("fold") for b in blocks),
        "chip_planes": sum(b["kinds"].count("chip") for b in blocks),
        "block_footprint_area_min_med_max": [round(float(np.min(fp_area)), 4), round(float(np.median(fp_area)), 4),
                                             round(float(np.max(fp_area)), 4)],
        "block_footprint_sides_hist": {str(k): int(v) for k, v in zip(*np.unique([len(b["footprint"]) for b in blocks], return_counts=True))},
        "crease_polylines": len(polylines), "crease_constraint_edges": len(cedges),
        "longest_straight_crease_run": round(longest_straight, 4),
        "new_vertices": len(newv), "new_faces": len(faces), "faces_flipped_by_winding": flipped,
        "crease_edges": crease_edges, "sharp_crease_edges": sharp_n,
        "crease_dihedral_median_p90": [round(float(np.median(dihedrals)), 2), round(float(np.percentile(dihedrals, 90)), 2)] if dihedrals else None,
        "visible_facet_regions": int(len(reg)), "facet_region_area_median": round(float(np.median(reg)), 5) if len(reg) else None,
        "floor_face_fraction": round(sum(1 for lb in flab if lb < 0) / max(1, len(flab)), 4),
        "relief_vs_massform_min_max": [round(float((hf - hm).min()), 4), round(float((hf - hm).max()), 4)],
        "contact_relax_passes": relax_passes,
    }
    dom = {bmv[i]: (float(P2[i][0]), float(P2[i][1])) for i in range(len(uv2)) if bmv[i] is not None and bmv[i].is_valid}
    return faces, loop, dom


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    src, mc, output = (Path(a).resolve() for a in argv)
    if tuple(bpy.app.version) != (5, 3, 0):
        raise RuntimeError("Requires Blender 5.3.0")
    if d4.sha(src) != D4_SHA or d4.sha(mc) != METHOD_C_SHA:
        raise RuntimeError("input SHA mismatch; STOP")
    for s_ in (src, mc):
        if output == s_.parent or s_.parent in [output, *output.parents]:
            raise RuntimeError("Output must not overwrite or nest a source directory")
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(mc))
    mo = bpy.data.objects[TARGET]
    c_faces = {d4.fkey([mo.data.vertices[i].co for i in p.vertices]) for p in mo.data.polygons}
    bpy.ops.wm.open_mainfile(filepath=str(src))
    obj = bpy.data.objects[TARGET]
    if obj.matrix_world != obj.matrix_world.Identity(4):
        raise RuntimeError("Carrier transform changed; STOP")
    if d4.geometry_sha256(obj) != D4_GEOMETRY_SHA:
        raise RuntimeError("D4 geometry SHA mismatch; STOP")
    me = obj.data
    before = d4.topology(obj)
    contacts_before = d4.local_self_contacts(obj, -9.6, -4.0)
    cn = me.corner_normals
    old_normal_of = {}
    for p in me.polygons:
        k = d4.fkey([me.vertices[i].co for i in p.vertices])
        for li in p.loop_indices:
            old_normal_of[(k, d4.rkey(me.vertices[me.loops[li].vertex_index].co))] = tuple(cn[li].vector)
    bm = bmesh.new()
    bm.from_mesh(me)
    lay = bm.verts.layers.int.new("orig_id")
    for v in bm.verts:
        v[lay] = v.index
    refill = {f for f in bm.faces if d4.fkey([v.co for v in f.verts]) not in c_faces}
    pend, comps = set(refill), []
    while pend:
        st = [pend.pop()]
        comp = set(st)
        while st:
            f = st.pop()
            for e in f.edges:
                for g in e.link_faces:
                    if g in pend:
                        pend.discard(g)
                        comp.add(g)
                        st.append(g)
        comps.append(comp)
    comps.sort(key=lambda c: (-len(c), min(d4.rkey(v.co) for f in c for v in f.verts)))
    protected = {d4.rkey(v.co) for v in bm.verts if any(f not in refill for f in v.link_faces)}
    report, skipped, all_new = {}, [], []
    for ci, comp in enumerate(comps):
        if len(comp) < MIN_COMPONENT_FACES:
            skipped.append(len(comp))
            continue
        cen = sum((v.co for f in comp for v in f.verts), Vector()) / sum(len(f.verts) for f in comp)
        rail = min(RAILS, key=lambda r: min(math.hypot(cen.x - x, cen.z - z) for x, z in r["pts"]))
        name = f"island_{ci}_{rail['name']}"
        faces, loop, dom = build_component(bm, comp, rail, name, report)
        faces, report[name]["uv"] = d4.assign_uvs(bm, faces, loop, dom)
        all_new += faces
    bm.normal_update()
    newset = {f for f in all_new if f.is_valid}
    new_loop_normal = {}
    for f in newset:
        k = d4.fkey([v.co for v in f.verts])
        for l in f.loops:
            v = l.vert
            fan, st = {f}, [f]
            while st:
                g = st.pop()
                for e in g.edges:
                    if v in e.verts and e.smooth:
                        for h_ in e.link_faces:
                            if h_ not in fan:
                                fan.add(h_)
                                st.append(h_)
            old = [old_normal_of.get((d4.fkey([u.co for u in g.verts]), d4.rkey(v.co))) for g in fan if g not in newset]
            old = [o for o in old if o]
            if old:
                nv = sum((Vector(o) for o in old), Vector()).normalized()
            else:
                nv = Vector()
                for g in fan:
                    for gl in g.loops:
                        if gl.vert is v:
                            nv += g.normal * gl.calc_angle()
                nv.normalize()
            new_loop_normal[(k, d4.rkey(v.co))] = tuple(nv)
    bm.verts.layers.int.remove(lay)
    bm.to_mesh(me)
    bm.free()
    me.update()
    loop_normals, missing_norm = [], 0
    for p in me.polygons:
        k = d4.fkey([me.vertices[i].co for i in p.vertices])
        for li in p.loop_indices:
            vk = d4.rkey(me.vertices[me.loops[li].vertex_index].co)
            nv = new_loop_normal.get((k, vk)) or old_normal_of.get((k, vk))
            if nv is None:
                missing_norm += 1
                nv = (0.0, 0.0, 0.0)
            loop_normals.append(nv)
    me.normals_split_custom_set(loop_normals)
    me.update()
    uvl = me.uv_layers.active
    co = np.array([v.co[:] for v in me.vertices])
    newp = [p for p in me.polygons if d4.fkey([me.vertices[i].co for i in p.vertices]) not in c_faces]
    newv_ids = {i for p in newp for i in p.vertices}
    newp_ids = {p.index for p in newp}
    ringp = [p for p in me.polygons if p.index not in newp_ids and set(p.vertices) & newv_ids]

    def tri_arrays(polys):
        t3, tuv = [], []
        for p in polys:
            li, vi = list(p.loop_indices), list(p.vertices)
            for k in range(1, len(vi) - 1):
                idx = [0, k, k + 1]
                t3.append(co[[vi[i] for i in idx]])
                tuv.append(np.array([uvl.data[li[i]].uv[:] for i in idx]))
        return np.array(t3).reshape(-1, 3, 3), np.array(tuv).reshape(-1, 3, 2)
    uv_report = island_uv_report(*tri_arrays(newp), *tri_arrays(ringp))
    after = d4.topology(obj)
    contacts_after = d4.local_self_contacts(obj, -9.6, -4.0)
    final = {d4.rkey(v.co) for v in me.vertices}
    missing_protected = len(protected - final)
    cn2 = me.corner_normals
    dev = []
    for p in me.polygons:
        k = d4.fkey([me.vertices[i].co for i in p.vertices])
        for li in p.loop_indices:
            vk = d4.rkey(me.vertices[me.loops[li].vertex_index].co)
            o = old_normal_of.get((k, vk))
            if o is not None and (k, vk) not in new_loop_normal:
                dev.append(math.degrees(Vector(o).angle(cn2[li].vector, 0.0)))
    scene = bpy.context.scene
    scene["candidate"] = "C11_METHOD_E_BLOCK_SCULPT_UNAPPROVED"
    scene["c11_method_e_source_sha256"] = D4_SHA
    dest = output / "c11_method_e_block_sculpt_UNAPPROVED.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(dest), compress=True, copy=True)
    bmw = bmesh.new()
    bmw.from_mesh(me)
    winding = all(e.link_loops[0].vert is not e.link_loops[1].vert for e in bmw.edges if len(e.link_loops) == 2)
    bmw.free()
    checks = {
        "closed_manifold": after["boundary_edges"] == 0 and after["nonmanifold_edges"] == 0,
        "no_degenerate_faces": after["degenerate_faces"] == 0,
        "no_new_local_self_contacts": contacts_after <= contacts_before,
        "protected_vertices_unchanged": missing_protected == 0,
        "consistent_winding": winding,
        "old_loop_normals_preserved_deg_lt_0.5": (max(dev) if dev else 0.0) < 0.5,
        "every_loop_has_normal": missing_norm == 0,
        "no_straight_crease_longer_than_0.9": all(r["longest_straight_crease_run"] <= 0.9 for r in report.values()),
        "sources_sha_intact": d4.sha(src) == D4_SHA and d4.sha(mc) == METHOD_C_SHA,
        "uv_no_flipped_triangles": uv_report["flipped_uv"] == 0,
        "uv_no_zero_area_triangles": uv_report["zero_area_uv"] == 0,
        "uv_no_overlaps_repair_and_ring": uv_report["overlap_pairs"] == 0,
        "uv_perimeter_continuous": all(r["uv"]["perimeter_uv_mismatch_max"] < 1e-5 for r in report.values()),
    }
    result = {
        "status": "CANDIDATE_ONLY", "method": "E_individual_polyhedral_block_sculpt",
        "d4_source_sha256": D4_SHA, "d4_geometry_sha256": D4_GEOMETRY_SHA, "method_c_sha256": METHOD_C_SHA,
        "candidate_sha256": d4.sha(dest), "carrier_geometry_sha256": d4.geometry_sha256(obj),
        "before": before, "after": after,
        "local_self_contacts": {"before": contacts_before, "after": contacts_after},
        "protected_vertices": len(protected), "protected_vertices_missing": missing_protected,
        "old_loop_normal_max_dev_deg": round(max(dev), 4) if dev else 0.0,
        "skipped_small_components_faces": skipped,
        "islands": report, "uv_audit": uv_report, "checks": checks,
        "G1": "BLOCKED", "G2": "NOT_RUN", "G3": "PARTIAL_LOCAL" if all(checks.values()) else "FAIL", "G4": "NOT_RUN",
    }
    (output / "c11_method_e_report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("METHOD_E", json.dumps({k: result[k] for k in ("checks", "before", "after", "local_self_contacts")}), flush=True)
    if not all(checks.values()):
        raise RuntimeError("Method E stop condition; candidate retained for diagnosis only")


if __name__ == "__main__":
    main()

"""C11 Method D4: coherent planar joint facets inside the existing Method D repair islands.

Independent art QA (PR #421 comment 7034151523) on D3: blade removal PASS, G2 FAIL —
west refill soft/mottled and crest interrupted, central fracture discontinuous with
small dark cavities. Measured cause (Claude, 2026-11-20):
  * D3 surface = smooth harmonic membrane + rounded channel + 2-octave noise + ledge
    ripple, all smooth-shaded with auto normals on a 0.055 mesh. Neighbouring rock is
    faceted (dihedral p90 29-43 deg, edge ~0.11-0.14). Result reads soft/lumpy.
  * Central rail used depth_scale 0.5 and contact relaxation halved carve locally ->
    depth varies vertex-by-vertex -> isolated dark pits instead of one joint line.
  * Channel taper (0.55 at s=1) left a notch under the west crest.

D4 is structurally different from D1/D2/D3 (no membrane-as-final-surface, no noise,
no bedding ripple, no channel profile): each island is re-tessellated with
constrained edges along an anisotropic (columnar) Voronoi joint network; every
joint cell is ONE plane (tilted on a two-set columnar joint model); the fracture
is a single continuous constrained riser line with monotone depth, so it cannot
fragment into pits; creases >= SHARP_DEG are marked sharp, smaller ones stay
smooth (restrained rounding). Perimeter vertices, everything outside the islands
and the old loops' shading normals are preserved.

Run with Blender 5.3.0:
  blender -b --factory-startup --python c11_method_d4_joint_facets.py -- \
      D3B.blend METHOD_C.blend OUT_DIR
Inputs are SHA-pinned and never modified. Output: CANDIDATE ONLY.
"""
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c11_uv_qa import island_uv_report  # noqa: E402

D3B_SHA = "a6813fe0d65874b04c46106c49dfdbac67b980ff90e67128375ebcad911484ce"
D3B_GEOMETRY_SHA = "b3d289124c8a8fb724de4ca30d25e57ea1e7a90f620ccee2640c5c91a2a7c934"
METHOD_C_SHA = "d0e91ae7543f2995b70c2a3f2d59e625d7cc828e6328ccc90c9224d060b0b545"
TARGET = "Cliff C8 B | joinable coastal segment"

# Measured junction rails (unchanged from Method D), x/z bottom -> top.
# recess_side +1: low side toward +x, so the riser faces +x, away from the review
# key light (-x) -> reads as one continuous shadowed joint, ramp catches light.
RAILS = (
    {"name": "west_fracture", "pts": ((-7.35, 0.95), (-7.47, 2.35), (-7.98, 4.80), (-8.24, 6.95)),
     "depth": 0.26, "ramp": 0.34, "riser": 0.055, "s_range": (0.04, 0.80), "tilt": (17.0, -10.0), "seed": 11},
    {"name": "central_fracture", "pts": ((-5.42, 2.30), (-5.72, 3.62), (-5.97, 5.05), (-5.67, 6.80)),
     "depth": 0.24, "ramp": 0.24, "riser": 0.045, "s_range": (0.05, 0.86), "tilt": (-15.0, 11.0), "seed": 23},
)
COL_W = 0.20          # joint column width (across)
COL_L = 0.55          # joint column length (along the column axis)
FILL = 0.07           # interior sample spacing
SUBDIV = 0.06         # constraint subdivision
EDGE_MARGIN = 0.07    # joints terminate this far inside the locked perimeter
FADE = 0.08           # facet -> perimeter blend band
MAX_DEV = 0.07        # max facet deviation from the mass-form target at a cell vertex
SHARP_DEG = 20.0
MIN_COMPONENT_FACES = 50


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def geometry_sha256(obj):
    h = hashlib.sha256()
    for v in obj.data.vertices:
        h.update(struct.pack("<3f", *v.co))
    for f in obj.data.polygons:
        h.update(struct.pack(f"<{len(f.vertices)}i", *f.vertices))
    return h.hexdigest()


def rkey(co):
    return (round(co[0], 6), round(co[1], 6), round(co[2], 6))


def fkey(coords):
    return tuple(sorted(rkey(c) for c in coords))


def smoothstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def hash01(*k):
    x = math.sin(sum((i + 1) * 12.9898 * v for i, v in enumerate(k)) + 78.233) * 43758.5453
    return x - math.floor(x)


def poly_query(pts, p):
    """Closest point on 2D polyline: distance, side (+1 right of direction), s 0..1, tangent."""
    lens = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    total = sum(lens)
    best, acc = None, 0.0
    for (a, b), L in zip(zip(pts, pts[1:]), lens):
        dx, dy = b[0] - a[0], b[1] - a[1]
        t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (L * L)))
        qx, qy = a[0] + t * dx, a[1] + t * dy
        d = math.hypot(p[0] - qx, p[1] - qy)
        cross = dx * (p[1] - a[1]) - dy * (p[0] - a[0])
        side = -1.0 if cross > 0 else 1.0
        if best is None or d < best[0]:
            best = (d, side, (acc + t * L) / total, (dx / L, dy / L))
        acc += L
    return best


def poly_point(pts, s):
    lens = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    target, acc = s * sum(lens), 0.0
    for (a, b), L in zip(zip(pts, pts[1:]), lens):
        if acc + L >= target or b is pts[-1]:
            t = (target - acc) / L
            return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])), ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        acc += L
    return pts[-1], (0.0, 1.0)


def point_in_poly(p, poly):
    x, z = p
    inside, j = False, len(poly) - 1
    for i in range(len(poly)):
        xi, zi = poly[i]
        xj, zj = poly[j]
        if (zi > z) != (zj > z) and x < (xj - xi) * (z - zi) / (zj - zi + 1e-30) + xi:
            inside = not inside
        j = i
    return inside


def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def dist_to_poly(p, poly):
    n = len(poly)
    return min(seg_dist(p, poly[i], poly[(i + 1) % n]) for i in range(n))


def segs_intersect(p1, p2, p3, p4, eps=1e-5):
    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def on_seg(a, b, c):
        return (min(a[0], b[0]) - eps <= c[0] <= max(a[0], b[0]) + eps and
                min(a[1], b[1]) - eps <= c[1] <= max(a[1], b[1]) + eps)
    d1, d2 = orient(p3, p4, p1), orient(p3, p4, p2)
    d3, d4 = orient(p1, p2, p3), orient(p1, p2, p4)
    if ((d1 > eps and d2 < -eps) or (d1 < -eps and d2 > eps)) and \
            ((d3 > eps and d4 < -eps) or (d3 < -eps and d4 > eps)):
        return True
    return ((abs(d1) <= eps and on_seg(p3, p4, p1)) or (abs(d2) <= eps and on_seg(p3, p4, p2)) or
            (abs(d3) <= eps and on_seg(p1, p2, p3)) or (abs(d4) <= eps and on_seg(p1, p2, p4)))


def clip_halfplane(poly, m, nrm):
    """Keep (x - m) . nrm <= 0 (Sutherland-Hodgman)."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        da = (a[0] - m[0]) * nrm[0] + (a[1] - m[1]) * nrm[1]
        db = (b[0] - m[0]) * nrm[0] + (b[1] - m[1]) * nrm[1]
        if da <= 0:
            out.append(a)
        if (da <= 0) != (db <= 0):
            t = da / (da - db)
            out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
    return out


def local_self_contacts(obj, xmin, xmax):
    mesh = obj.data
    mesh.calc_loop_triangles()
    co = [v.co.copy() for v in mesh.vertices]
    tris = [tuple(t.vertices) for t in mesh.loop_triangles
            if xmin < min(co[i].x for i in t.vertices) and max(co[i].x for i in t.vertices) < xmax]
    bvh = BVHTree.FromPolygons(co, tris, all_triangles=True)
    return sum(a < b and not set(tris[a]) & set(tris[b]) for a, b in bvh.overlap(bvh))


def topology(obj):
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        return {"vertices": len(bm.verts), "faces": len(bm.faces),
                "boundary_edges": sum(e.is_boundary for e in bm.edges),
                "nonmanifold_edges": sum(not e.is_manifold for e in bm.edges),
                "degenerate_faces": sum(f.calc_area() <= 1e-10 for f in bm.faces)}
    finally:
        bm.free()


def perimeter_loop(region, name):
    border = {e for f in region for e in f.edges if sum(l in region for l in e.link_faces) == 1}
    adj = {}
    for e in border:
        a, b = e.verts
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    if any(len(n) != 2 for n in adj.values()):
        raise RuntimeError(f"{name}: perimeter not a simple loop; STOP")
    key = lambda v: rkey(v.co)
    for v in adj:
        adj[v].sort(key=key)
    start = min(adj, key=key)
    loop, prev, cur = [start], None, start
    while True:
        nxt = adj[cur][0] if adj[cur][0] is not prev else adj[cur][1]
        if nxt is start:
            break
        loop.append(nxt)
        prev, cur = cur, nxt
    if len(loop) != len(adj):
        raise RuntimeError(f"{name}: multiple perimeter loops; STOP")
    return loop


def choose_basis(region, loop):
    avg = Vector()
    for f in region:
        avg += f.normal * f.calc_area()
    avg.normalize()
    if avg.y > 0:
        avg = -avg

    def axis(az, el):
        az, el = math.radians(az), math.radians(el)
        return Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    grid = sorted(((az, el) for az in (0, -12, 12, -25, 25, -40, 40) for el in (0, 20, 35, 50)),
                  key=lambda p: abs(p[0]) + p[1])
    cands = [axis(az, el) for az, el in grid]
    cands += [(avg * (1 - m) + Vector((0, -1, 0)) * m).normalized() for m in (0.35, 0.0)]
    best = None
    n = len(loop)
    for N in cands:
        U = Vector((0, 0, 1)).cross(N).normalized()
        V = N.cross(U).normalized()
        poly = [(v.co.dot(U), v.co.dot(V)) for v in loop]
        simple = not any(segs_intersect(poly[i], poly[(i + 1) % n], poly[j], poly[(j + 1) % n])
                         for i in range(n) for j in range(i + 2, n) if not (i == 0 and j == n - 1))
        if not simple:
            continue
        plen = sq = 0.0
        for i in range(n):
            a3 = (loop[i].co - loop[(i + 1) % n].co).length
            a2 = math.dist(poly[i], poly[(i + 1) % n])
            plen += a3
            sq += a3 if a2 < 0.35 * a3 else 0.0
        g = sq / (plen or 1.0)
        if best is None or g < best[0] - 1e-9:
            best = (g, N, U, V, poly)
    if best is None:
        raise RuntimeError("no simple projection; STOP (D4 has no disk fallback by design)")
    return best


def build_component(bm, region, rail, comp_name, old_normal_of, report):
    loop = perimeter_loop(region, comp_name)
    squeeze, N, U, V, poly = choose_basis(region, loop)
    n = len(loop)
    loopset = set(loop)
    inner_old = {v for f in region for v in f.verts} - loopset
    # ---- mass-form target: height of the existing D3b surface along N is NOT used
    #      (it carries the soft carve); target = harmonic interpolation of the locked
    #      perimeter + authored planar fracture wedge.
    # rail in this domain: lift (x, z) onto the island using nearest island vertex y
    island_pts = [v.co for f in region for v in f.verts]
    rail2d = []
    for x, z in rail["pts"]:
        near = min(island_pts, key=lambda c: (c.x - x) ** 2 + (c.z - z) ** 2)
        p = Vector((x, near.y, z))
        rail2d.append((p.dot(U), p.dot(V)))
    # column frame: axis a along the mean rail direction, b across
    ax = Vector((rail2d[-1][0] - rail2d[0][0], rail2d[-1][1] - rail2d[0][1])).normalized()
    a_vec, b_vec = (ax.x, ax.y), (ax.y, -ax.x)

    def to_s(p):   # domain -> scaled isotropic column space
        return ((p[0] * b_vec[0] + p[1] * b_vec[1]) / COL_W, (p[0] * a_vec[0] + p[1] * a_vec[1]) / COL_L)

    def from_s(q):
        x, y = q[0] * COL_W, q[1] * COL_L
        return (x * b_vec[0] + y * a_vec[0], x * b_vec[1] + y * a_vec[1])

    us = [p[0] for p in poly]
    vs = [p[1] for p in poly]
    s0, s1 = rail["s_range"]
    rail_inside = [s for s in np.linspace(s0, s1, 200)
                   if point_in_poly(poly_point(rail2d, s)[0], poly) and
                   dist_to_poly(poly_point(rail2d, s)[0], poly) > EDGE_MARGIN]
    has_rail = len(rail_inside) >= 8
    if has_rail:
        rs0, rs1 = min(rail_inside), max(rail_inside)
    # ---- seeds in scaled space
    corners = [to_s((u, v)) for u in (min(us), max(us)) for v in (min(vs), max(vs))]
    qx = [c[0] for c in corners]
    qy = [c[1] for c in corners]
    rail_s = [to_s(p) for p in rail2d]
    seeds, tags = [], []
    j = 0
    y = min(qy) - 1.0
    while y < max(qy) + 1.0:
        x = min(qx) - 1.0 + 0.5 * (j % 2)
        while x < max(qx) + 1.0:
            q = (x + 0.28 * (hash01(x, y, rail["seed"]) - 0.5), y + 0.28 * (hash01(y, x, rail["seed"] + 1) - 0.5))
            dq = poly_query(rail_s, q)
            if not (has_rail and dq[0] < 0.75 and rs0 - 0.05 < dq[2] < rs1 + 0.05):
                seeds.append(q)
                tags.append(0)
            x += 1.0
        y += 0.866
        j += 1
    if has_rail:
        # mirrored seed pairs straddling the rail: their bisector IS the rail
        Ls = sum(math.dist(a, b) for a, b in zip(rail_s, rail_s[1:]))
        k = 0
        s = rs0
        while s <= rs1 + 1e-9:
            # rail point/tangent in scaled space
            p_dom, _ = poly_point(rail2d, s)
            ps = to_s(p_dom)
            pd2, _ = poly_point(rail2d, min(1.0, s + 0.002))
            ps2 = to_s(pd2)
            t = Vector((ps2[0] - ps[0], ps2[1] - ps[1])).normalized()
            nrm = (t.y, -t.x)
            off = 0.5 + 0.1 * (hash01(s, rail["seed"]) - 0.5)
            for sg in (1, -1):
                seeds.append((ps[0] + sg * off * nrm[0], ps[1] + sg * off * nrm[1]))
                side = poly_query(rail2d, from_s(seeds[-1]))[1]
                tags.append(int(side))
            s += 0.9 / Ls
            k += 1
    S = np.array(seeds)
    # ---- Voronoi edges (scaled space) by half-plane clipping
    box = [(min(qx) - 2, min(qy) - 2), (max(qx) + 2, min(qy) - 2), (max(qx) + 2, max(qy) + 2), (min(qx) - 2, max(qy) + 2)]
    edges = {}
    for i, si in enumerate(seeds):
        d2 = ((S - S[i]) ** 2).sum(1)
        cell = list(box)
        for jj in np.argsort(d2)[1:40]:
            sj = seeds[jj]
            m = ((si[0] + sj[0]) / 2, (si[1] + sj[1]) / 2)
            cell = clip_halfplane(cell, m, (sj[0] - si[0], sj[1] - si[1]))
            if len(cell) < 3:
                break
        for a_, b_ in zip(cell, cell[1:] + cell[:1]):
            if math.dist(a_, b_) < 1e-6:
                continue
            key = tuple(sorted((tuple(round(c, 5) for c in a_), tuple(round(c, 5) for c in b_))))
            edges[key] = (a_, b_)

    def seed_pair(mid):
        d2 = ((S - np.array(mid)) ** 2).sum(1)
        o = np.argsort(d2)[:2]
        return int(o[0]), int(o[1])
    joint_segs = []
    for a_, b_ in edges.values():
        i1, i2 = seed_pair(((a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2))
        if tags[i1] and tags[i2] and tags[i1] != tags[i2]:
            continue   # replaced by the explicit rail constraint
        joint_segs.append((from_s(a_), from_s(b_)))
    if has_rail:
        rp = [poly_point(rail2d, s)[0] for s in np.linspace(rs0, rs1, 60)]
        joint_segs += list(zip(rp, rp[1:]))
        # riser foot line, offset to the recess (+side) by the riser width
        foot = []
        for s in np.linspace(rs0, rs1, 60):
            p, t = poly_point(rail2d, s)
            nr = (t[1], -t[0])   # +1 side (right of upward direction)
            if poly_query(rail2d, (p[0] + 0.01 * nr[0], p[1] + 0.01 * nr[1]))[1] < 0:
                nr = (-nr[0], -nr[1])
            foot.append((p[0] + rail["riser"] * nr[0], p[1] + rail["riser"] * nr[1]))
        joint_segs += list(zip(foot, foot[1:]))
    # ---- clip / subdivide constraints, keep EDGE_MARGIN from the locked perimeter
    cpts, cedges = [], []
    pidx = {}

    def add_pt(p):
        k = (round(p[0] / 0.012), round(p[1] / 0.012))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                j = pidx.get((k[0] + dx, k[1] + dy))
                if j is not None and math.dist(cpts[j], p) < 0.012:
                    return j
        pidx[k] = len(cpts)
        cpts.append(p)
        return pidx[k]
    for a_, b_ in joint_segs:
        L = math.dist(a_, b_)
        m = max(1, int(math.ceil(L / SUBDIV)))
        prev = None
        for t in range(m + 1):
            p = (a_[0] + (b_[0] - a_[0]) * t / m, a_[1] + (b_[1] - a_[1]) * t / m)
            ok = point_in_poly(p, poly) and dist_to_poly(p, poly) > EDGE_MARGIN
            if ok:
                cur = add_pt(p)
                if prev is not None and prev != cur:
                    cedges.append((prev, cur))
                prev = cur
            else:
                prev = None
    # fill points
    fill = []
    jrow = 0
    z = min(vs) + FILL * 0.5
    while z < max(vs):
        x = min(us) + FILL * (0.5 + 0.5 * (jrow % 2))
        while x < max(us):
            p = (x + 0.2 * FILL * (hash01(x, z, 5) - 0.5), z + 0.2 * FILL * (hash01(z, x, 6) - 0.5))
            if point_in_poly(p, poly) and dist_to_poly(p, poly) > 0.6 * FILL:
                if not cpts or min(math.dist(p, c) for c in cpts) > 0.5 * FILL:
                    if all(seg_dist(p, cpts[e0], cpts[e1]) > 0.4 * FILL for e0, e1 in cedges
                           if abs(cpts[e0][0] - p[0]) < 0.2 and abs(cpts[e0][1] - p[1]) < 0.2):
                        fill.append(p)
            x += FILL
        z += FILL * 0.866
        jrow += 1
    coords = [Vector(p) for p in poly] + [Vector(p) for p in cpts] + [Vector(p) for p in fill]
    edges_in = [(i, (i + 1) % n) for i in range(n)] + [(n + a, n + b) for a, b in cedges]
    out = delaunay_2d_cdt(coords, edges_in, [list(range(n))], 1, 1e-5)
    o_verts, o_faces, o_orig = out[0], out[2], out[3]
    # ---- delete old island, keep perimeter
    bmesh.ops.delete(bm, geom=sorted(region, key=lambda f: f.index), context="FACES_ONLY")
    for v in sorted((v for v in inner_old if not v.link_faces), key=lambda v: rkey(v.co)):
        bm.verts.remove(v)
    for e in sorted({e for v in loop for e in v.link_edges if not e.link_faces},
                    key=lambda e: sorted(rkey(v.co) for v in e.verts)):
        bm.edges.remove(e)
    # ---- vertices
    uv2 = []          # per output vertex 2D coords
    bmv = []
    for oi, ov in enumerate(o_verts):
        origs = o_orig[oi]
        if origs and origs[0] < n:
            if any(o >= n for o in origs[1:]):
                raise RuntimeError(f"{comp_name}: interior point merged into perimeter; STOP")
            bmv.append(loop[origs[0]])
        else:
            bmv.append(None)
        uv2.append((ov.x, ov.y))
    perim_mask = np.array([b is not None for b in bmv])
    if perim_mask.sum() != n:
        raise RuntimeError(f"{comp_name}: perimeter vertex count changed by CDT; STOP")
    tris = [tuple(t) for t in o_faces if len(set(t)) == 3]
    P2 = np.array(uv2)
    # adjacency
    nbr = [set() for _ in uv2]
    for t in tris:
        for a_ in t:
            nbr[a_] |= set(t) - {a_}
    # harmonic membrane along N from the locked perimeter
    h = np.zeros(len(uv2))
    perim_h = {i: bmv[i].co.dot(N) for i in range(len(uv2)) if bmv[i] is not None}
    PP = np.array([P2[i] for i in perim_h])
    PH = np.array(list(perim_h.values()))
    for i in range(len(uv2)):
        if i in perim_h:
            h[i] = perim_h[i]
        else:
            w = 1.0 / (((PP - P2[i]) ** 2).sum(1) + 1e-6)
            h[i] = (w * PH).sum() / w.sum()
    free = [i for i in range(len(uv2)) if i not in perim_h]
    for _ in range(3000):
        delta = 0.0
        for i in free:
            val = sum(h[k] for k in nbr[i]) / len(nbr[i])
            delta = max(delta, abs(val - h[i]))
            h[i] = val
        if delta < 1e-6:
            break
    hm = h.copy()
    # authored planar fracture wedge (monotone, no noise)
    rail_info = [poly_query(rail2d, tuple(p)) for p in P2]

    def wedge(i):
        if not has_rail:
            return 0.0
        d, side, s, _ = rail_info[i]
        if side < 0 or not (rs0 - 0.02 <= s <= rs1 + 0.02):
            return 0.0
        taper = smoothstep(rs0, rs0 + 0.12, s) * (1.0 - smoothstep(rs1 - 0.14, rs1, s))
        D = rail["depth"] * taper * (1.0 + 0.12 * math.sin(2 * math.pi * 1.3 * s + rail["seed"]))
        if d <= rail["riser"]:
            return -D * d / rail["riser"]
        return -D * max(0.0, 1.0 - (d - rail["riser"]) / rail["ramp"])
    R = np.array([wedge(i) for i in range(len(uv2))])
    T = hm + R
    # ---- classify triangles: riser strip or nearest seed cell (side-consistent)
    tri_cls = []
    for t in tris:
        c = P2[list(t)].mean(0)
        if has_rail:
            d, side, s, _ = poly_query(rail2d, tuple(c))
            if side > 0 and d < rail["riser"] * 1.02 and rs0 <= s <= rs1:
                tri_cls.append(-1)
                continue
        cs = np.array(to_s(tuple(c)))
        d2 = ((S - cs) ** 2).sum(1)
        order = np.argsort(d2)
        pick = int(order[0])
        if has_rail:
            d, side, s, _ = poly_query(rail2d, tuple(c))
            if d < 0.5 and rs0 - 0.02 <= s <= rs1 + 0.02:
                for o in order[:12]:
                    if tags[o] == int(side):
                        pick = int(o)
                        break
        tri_cls.append(pick)
    cells = {}
    for t, c in zip(tris, tri_cls):
        if c >= 0:
            cells.setdefault(c, set()).update(t)
    # ---- one plane per joint cell, tilted on a two-set columnar joint model
    planes = {}
    tilt_scale_min = 1.0
    tilt_scales = []
    for c, vids in cells.items():
        ids = sorted(vids)
        A = np.c_[P2[ids], np.ones(len(ids))]
        wts = np.array([3.0 if i in perim_h else 1.0 for i in ids])
        coef, *_ = np.linalg.lstsq(A * wts[:, None], T[ids] * wts, rcond=None)
        col = int(math.floor(S[c][0] + 0.5))   # column index in scaled space
        sgn = 1 if (col % 2 == 0) else -1
        th = math.radians(rail["tilt"][0] if sgn > 0 else rail["tilt"][1]) * (0.75 + 0.5 * hash01(c, 3))
        ps = math.radians(4.0) * (2 * hash01(c, 4) - 1)
        g = np.array([coef[0], coef[1]]) + math.tan(th) * np.array(b_vec) + math.tan(ps) * np.array(a_vec)
        cen = P2[ids].mean(0)
        c0 = float((T[ids]).mean() - g @ cen)
        dev = np.abs(A[:, :2] @ g + c0 - T[ids]).max()
        k = 1.0
        if dev > MAX_DEV:
            # scale only the authored tilt back toward the fitted plane
            gf = np.array([coef[0], coef[1]])
            lo, hi = 0.0, 1.0
            for _ in range(20):
                mid = (lo + hi) / 2
                gm = gf + mid * (g - gf)
                cm = float(T[ids].mean() - gm @ cen)
                if np.abs(A[:, :2] @ gm + cm - T[ids]).max() > MAX_DEV:
                    hi = mid
                else:
                    lo = mid
            k = lo
            g = gf + k * (g - gf)
            c0 = float(T[ids].mean() - g @ cen)
        tilt_scale_min = min(tilt_scale_min, k)
        tilt_scales.append(k)
        planes[c] = (g, c0)
    # ---- vertex heights
    vcells = [set() for _ in uv2]
    for t, c in zip(tris, tri_cls):
        for i in t:
            if c >= 0:
                vcells[i].add(c)
    dperim = np.array([dist_to_poly(tuple(p), poly) for p in P2])
    hf = T.copy()
    for i in free:
        cs = vcells[i]
        if cs:
            hf[i] = float(np.mean([planes[c][0] @ P2[i] + planes[c][1] for c in cs]))
        w = smoothstep(0.0, FADE, dperim[i])
        hf[i] = (1 - w) * T[i] + w * hf[i]
    # ---- continuous fracture riser: rail-top heights smoothed along s (no
    #      per-cell notches), riser foot forced to top - D(s) (cannot fragment)
    riser_fix = 0
    if has_rail:
        def depth_at(s):
            taper = smoothstep(rs0, rs0 + 0.12, s) * (1.0 - smoothstep(rs1 - 0.14, rs1, s))
            return rail["depth"] * taper * (1.0 + 0.12 * math.sin(2 * math.pi * 1.3 * s + rail["seed"]))
        top = sorted((rail_info[i][2], i) for i in free if rail_info[i][0] < 2e-3)
        if top:
            vals = np.array([hf[i] for _, i in top])
            sm = np.array([vals[max(0, k - 3):k + 4].mean() for k in range(len(vals))])
            for (s, i), hv in zip(top, sm):
                hf[i] = hv
            ts = np.array([s for s, _ in top])
            for i in free:
                d, side, s, _ = rail_info[i]
                if side > 0 and abs(d - rail["riser"]) < 2e-3 and rs0 <= s <= rs1:
                    hf[i] = float(np.interp(s, ts, sm)) - depth_at(s)
                    riser_fix += 1
    import os
    if os.environ.get("C11_D4_DUMP"):
        np.savez(os.path.join(os.environ["C11_D4_DUMP"], f"{comp_name}.npz"), P2=P2, hf=hf, hm=hm, T=T,
                 tris=np.array(tris), cls=np.array(tri_cls), rail=np.array(rail2d), poly=np.array(poly))
    # ---- create geometry
    lay = bm.verts.layers.int["orig_id"]
    for i in free:
        p = U * P2[i][0] + V * P2[i][1] + N * hf[i]
        bv = bm.verts.new(p)
        bv[lay] = -1
        bmv[i] = bv
    faces, face_cls = [], []
    for t, c in zip(tris, tri_cls):
        vs3 = [bmv[i] for i in t]
        if len(set(vs3)) == 3:
            faces.append(bm.faces.new(vs3))
            face_cls.append(c)
    newv = [bmv[i] for i in free]
    # ---- contact relaxation toward the membrane (8 passes max)
    hm_of = {bmv[i]: (P2[i], hm[i], hf[i]) for i in free}
    relax_passes = 0
    newset_v = set(newv)
    for relax_passes in range(1, 9):
        bm.verts.index_update()
        tri_old = [tuple(l.vert for l in lt) for lt in bm.calc_loop_triangles()
                   if not any(l.vert in newset_v for l in lt)
                   and any(-9.6 < l.vert.co.x < -4.0 for l in lt)]
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
            p2, h0, h1 = hm_of[u]
            h1 = 0.5 * (h0 + h1)
            hm_of[u] = (p2, h0, h1)
            u.co = U * p2[0] + V * p2[1] + N * h1
    # ---- winding from the perimeter
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
    # ---- crease marking: joint boundaries with dihedral >= SHARP_DEG
    cls_of = dict(zip(faces, face_cls))
    sharp_n = joint_edges = 0
    for f in faces:
        for e in f.edges:
            lf = e.link_faces
            if len(lf) == 2 and all(x in cls_of for x in lf) and cls_of[lf[0]] != cls_of[lf[1]]:
                if lf[0] is f:
                    joint_edges += 1
                    if math.degrees(e.calc_face_angle(0.0)) >= SHARP_DEG:
                        e.smooth = False
                        sharp_n += 1
                    else:
                        e.smooth = True
            elif len(lf) == 2 and all(x in cls_of for x in lf):
                e.smooth = True
    # metrics: continuity of the joint, planarity
    cont = None
    if has_rail:
        samples = []
        for s in np.linspace(rs0 + 0.12, rs1 - 0.14, 40):
            p, t = poly_point(rail2d, s)
            nr = (t[1], -t[0])
            if poly_query(rail2d, (p[0] + 0.01 * nr[0], p[1] + 0.01 * nr[1]))[1] < 0:
                nr = (-nr[0], -nr[1])
            top = np.array(p) - 0.012 * np.array(nr)
            bot = np.array(p) + (rail["riser"] + 0.012) * np.array(nr)
            def h_at(q):
                # barycentric interpolation on the final triangulation
                for t in tris:
                    a_, b_, c_ = P2[list(t)]
                    det = (b_[1] - c_[1]) * (a_[0] - c_[0]) + (c_[0] - b_[0]) * (a_[1] - c_[1])
                    if abs(det) < 1e-14:
                        continue
                    l1 = ((b_[1] - c_[1]) * (q[0] - c_[0]) + (c_[0] - b_[0]) * (q[1] - c_[1])) / det
                    l2 = ((c_[1] - a_[1]) * (q[0] - c_[0]) + (a_[0] - c_[0]) * (q[1] - c_[1])) / det
                    l3 = 1 - l1 - l2
                    if min(l1, l2, l3) >= -1e-9:
                        return float(l1 * hf[t[0]] + l2 * hf[t[1]] + l3 * hf[t[2]])
                return float('nan')
            samples.append(h_at(top) - h_at(bot))
        samples = [x for x in samples if x == x]
        cont = {"riser_drop_min": round(min(samples), 4), "riser_drop_max": round(max(samples), 4),
                "riser_drop_samples": len(samples),
                "riser_continuous": bool(min(samples) > 0.35 * rail["depth"])}
    rms = []
    for c, vids in cells.items():
        ids = [i for i in vids if i not in perim_h and dperim[i] > FADE]
        if len(ids) >= 3:
            g, c0 = planes[c]
            rms.append(float(np.sqrt(np.mean((P2[ids] @ g + c0 - hf[ids]) ** 2))))
    report[comp_name] = {
        "rail": rail["name"], "rail_in_island": has_rail,
        "projection_normal": [round(c, 5) for c in N], "perimeter_squeeze_fraction": round(squeeze, 4),
        "perimeter_vertices_locked": n, "old_faces_removed": len(region),
        "old_interior_vertices_removed": len(inner_old),
        "seeds": len(seeds), "joint_cells": len(cells), "joint_constraint_edges": len(cedges),
        "new_vertices": len(newv), "new_faces": len(faces), "faces_flipped_by_winding": flipped,
        "joint_boundary_edges": joint_edges, "sharp_joint_edges": sharp_n,
        "authored_tilt_min_scale": round(tilt_scale_min, 3), "authored_tilt_mean_scale": round(float(np.mean(tilt_scales)), 3), "contact_relax_passes": relax_passes,
        "facet_plane_rms_median": round(float(np.median(rms)), 6) if rms else None,
        "facet_plane_rms_max": round(float(np.max(rms)), 6) if rms else None,
        "joint_continuity": cont, "riser_foot_vertices": riser_fix,
    }
    dom = {bmv[i]: (float(P2[i][0]), float(P2[i][1])) for i in range(len(uv2)) if bmv[i] is not None and bmv[i].is_valid}
    return faces, loop, dom


def assign_uvs(bm, faces, loop, dom):
    """Fold-free UVs from the island's planar CDT domain (D3/D3b used a 3D affine
    fit, which folds wherever the surface turns against the fitted plane -> the
    flipped/overlapping UV triangles found by Codex QA). UV = A(u, v) + f * r(u, v):
    A = least-squares affine map domain -> perimeter UVs (bijective on the
    fold-free CDT), r = harmonic interpolation of the perimeter residual so the
    perimeter matches the untouched neighbours exactly (f = 1). f is reduced only
    if a fold would appear; the chosen f is reported."""
    uvl = bm.loops.layers.uv.active
    newset = set(faces)
    old_uv, spread = {}, 0.0
    for v in loop:
        pts = [tuple(l[uvl].uv) for l in v.link_loops if l.face not in newset]
        arr = np.array(pts)
        sp = float(np.ptp(arr, 0).max()) if len(arr) > 1 else 0.0
        if sp > 1e-3:   # seam through a perimeter vertex: use edge-adjacent old faces
            adj = [tuple(l[uvl].uv) for e in v.link_edges if any(f in newset for f in e.link_faces)
                   for f in e.link_faces if f not in newset for l in f.loops if l.vert is v]
            arr = np.array(adj)
            sp = float(np.ptp(arr, 0).max()) if len(arr) > 1 else 0.0
        spread = max(spread, sp)
        old_uv[v] = arr.mean(0)
    A = np.array([[dom[v][0], dom[v][1], 1.0] for v in loop])
    Y = np.array([old_uv[v] for v in loop])
    M, *_ = np.linalg.lstsq(A, Y, rcond=None)
    detA = float(np.linalg.det(M[:2, :2]))
    resid = {v: Y[k] - A[k] @ M for k, v in enumerate(loop)}
    # diagnostic: perimeter edges whose old UV direction disagrees with the affine map
    nL = len(loop)
    rev = []
    for k in range(nL):
        a_, b_ = loop[k], loop[(k + 1) % nL]
        du = Y[(k + 1) % nL] - Y[k]
        dd = (A[(k + 1) % nL] - A[k]) @ M
        c = float(du @ dd / (np.linalg.norm(du) * np.linalg.norm(dd) + 1e-30))
        rev.append(c)
    rev = np.array(rev)
    inner = sorted({v for f in faces for v in f.verts} - set(loop), key=lambda v: dom[v])
    r = {v: resid[v] for v in loop}
    for v in inner:
        r[v] = np.zeros(2)
    nb = {v: [e.other_vert(v) for e in v.link_edges if e.other_vert(v) in r] for v in inner}
    for _ in range(4000):
        delta = 0.0
        for v in inner:
            val = sum(r[u] for u in nb[v]) / len(nb[v])
            delta = max(delta, float(np.abs(val - r[v]).max()))
            r[v] = val
        if delta < 1e-9:
            break

    # Ears made only of locked perimeter vertices cannot be unfolded if the old
    # UVs turn back there: rotate their interior edge (domain-convex quads only)
    # so the perimeter vertex connects to a free interior vertex.
    loopset_ = set(loop)
    ears_rotated = 0

    def dom_area(vs3):
        return sum(dom[vs3[i]][0] * dom[vs3[(i + 1) % 3]][1] - dom[vs3[(i + 1) % 3]][0] * dom[vs3[i]][1] for i in range(3))

    def uv_area(vs3):
        return sum(old_uv[vs3[i]][0] * old_uv[vs3[(i + 1) % 3]][1] - old_uv[vs3[(i + 1) % 3]][0] * old_uv[vs3[i]][1] for i in range(3))
    for f in list(faces):
        if not f.is_valid:
            continue
        vs3 = [l.vert for l in f.loops]
        if not all(v in loopset_ for v in vs3):
            continue
        if np.sign(uv_area(vs3)) == np.sign(dom_area(vs3)) * np.sign(detA):
            continue
        for e in f.edges:
            other = [g for g in e.link_faces if g is not f]
            if len(other) != 1 or other[0] not in newset:
                continue
            y = [v for v in other[0].verts if v not in e.verts][0]
            if y in loopset_:
                continue
            a_, c_ = e.verts
            b_ = [v for v in vs3 if v not in e.verts][0]
            # convex quad test in the domain: segments b-y and a-c must cross
            if not segs_intersect(dom[b_], dom[y], dom[a_], dom[c_]):
                continue
            ne = bmesh.utils.edge_rotate(e, True)
            if ne is None:
                continue
            newset.discard(f)
            newset.discard(other[0])
            for g in ne.link_faces:
                newset.add(g)
                g.smooth = True
            ears_rotated += 1
            break
    faces = [f for f in faces if f.is_valid] + [f for f in newset if f.is_valid and f not in set(faces)]
    newset = set(faces)
    for f in faces:
        f.normal_update()
    # Exact-boundary harmonic map (Floater mean-value weights from the 3D
    # surface, all positive), initialised from A + harmonic residual, then local
    # untangling of any fold near reflex perimeter corners.
    allv = list(loop) + inner
    pos = {v: np.array([dom[v][0], dom[v][1]]) for v in allv}
    U2 = {v: np.array(old_uv[v], float) for v in loop}
    for v in inner:
        U2[v] = np.array([dom[v][0], dom[v][1], 1.0]) @ M + r[v]
    ring_of = {}
    for v in inner:
        # ordered one-ring (faces of the island only) for mean-value weights
        fs = [f for f in v.link_faces if f in newset]
        w = {}
        for f in fs:
            vs3 = [l.vert for l in f.loops]
            i = vs3.index(v)
            a_, b_ = vs3[(i + 1) % 3], vs3[(i + 2) % 3]
            # 3D mean-value weights (true surface metric, still all positive)
            ea = np.array((a_.co - v.co)[:])
            eb = np.array((b_.co - v.co)[:])
            la, lb = np.linalg.norm(ea), np.linalg.norm(eb)
            ang = math.acos(max(-1.0, min(1.0, float(ea @ eb) / (la * lb + 1e-30))))
            t = math.tan(ang / 2)
            w[a_] = w.get(a_, 0.0) + t / (la + 1e-30)
            w[b_] = w.get(b_, 0.0) + t / (lb + 1e-30)
        ring_of[v] = w
    for _ in range(6000):
        delta = 0.0
        for v in inner:
            w = ring_of[v]
            tot = sum(w.values())
            val = sum(U2[u] * wt for u, wt in w.items()) / tot
            delta = max(delta, float(np.abs(val - U2[v]).max()))
            U2[v] = val
        if delta < 1e-10:
            break
    sgn_ref = np.sign(detA)

    def face_ok(f):
        vs3 = [l.vert for l in f.loops]
        d = sum(pos[vs3[i]][0] * pos[vs3[(i + 1) % 3]][1] - pos[vs3[(i + 1) % 3]][0] * pos[vs3[i]][1] for i in range(3))
        u = sum(U2[vs3[i]][0] * U2[vs3[(i + 1) % 3]][1] - U2[vs3[(i + 1) % 3]][0] * U2[vs3[i]][1] for i in range(3))
        return u != 0 and np.sign(u) == np.sign(d) * sgn_ref

    def nflips():
        return sum(not face_ok(f) for f in faces)
    flips0 = nflips()
    untangle_passes = 0
    for untangle_passes in range(1, 401):
        bad = [f for f in faces if not face_ok(f)]
        if not bad:
            break
        movers = {v for f in bad for v in (l.vert for l in f.loops) if v in ring_of}
        if not movers:
            break
        for v in sorted(movers, key=lambda v: dom[v]):
            local = [f for f in v.link_faces if f in newset]
            nbrs = list(ring_of[v])
            cen = sum(U2[u] for u in nbrs) / len(nbrs)
            best, best_bad = U2[v].copy(), sum(not face_ok(f) for f in local)
            # candidates: blends toward the 1-ring centroid plus a 9x9 grid over
            # the 1-ring UV bounding box (searches the 1-ring kernel)
            nb_uv = np.array([U2[u] for u in nbrs])
            lo_, hi_ = nb_uv.min(0), nb_uv.max(0)
            cands = [U2[v] * (1 - t) + cen * t for t in (0.25, 0.5, 0.75, 1.0)]
            cands += [lo_ + (hi_ - lo_) * np.array([i / 8, j / 8]) for i in range(1, 8) for j in range(1, 8)]
            old = U2[v].copy()
            best_d = 0.0
            for cnd in cands:
                U2[v] = cnd
                nb_ = sum(not face_ok(f) for f in local)
                dd = float(np.linalg.norm(cnd - old))
                if nb_ < best_bad or (nb_ == best_bad and nb_ > 0 and dd < best_d):
                    best, best_bad, best_d = cnd.copy(), nb_, dd
            U2[v] = best
    flips1 = nflips()
    if flips1:
        info = [[(round(dom[l.vert][0], 3), round(dom[l.vert][1], 3), l.vert in ring_of) for l in f.loops]
                for f in faces if not face_ok(f)]
        raise RuntimeError(f"UV: {flips1} folds remain after untangling: {info}; STOP")
    for f in faces:
        for l in f.loops:
            l[uvl].uv = (float(U2[l.vert][0]), float(U2[l.vert][1]))
    chosen = 1.0
    rms = float(np.sqrt(np.mean([float(r_ @ r_) for r_ in resid.values()])))
    return faces, {"uv_method": "exact_boundary_mean_value_harmonic_map_with_untangle",
            "residual_weight": chosen, "affine_det": detA, "perimeter_affine_residual_rms": rms,
            "perimeter_uv_mismatch_max": float(max(np.abs(U2[v] - old_uv[v]).max() for v in loop)),
            "harmonic_flips_before_untangle": flips0, "untangle_passes": untangle_passes,
            "perimeter_ears_rotated": ears_rotated,
            "perimeter_old_uv_spread_max": spread,
            "perimeter_edges_reversed_vs_affine": int((rev < 0).sum()),
            "perimeter_edges_angle_gt45_vs_affine": int((rev < 0.7071).sum()), "perimeter_edges": nL}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    d3b, mc, output = (Path(a).resolve() for a in argv)
    if tuple(bpy.app.version) != (5, 3, 0):
        raise RuntimeError("Requires Blender 5.3.0")
    if sha(d3b) != D3B_SHA or sha(mc) != METHOD_C_SHA:
        raise RuntimeError("input SHA mismatch; STOP")
    for src in (d3b, mc):
        if output == src.parent or src.parent in [output, *output.parents]:
            raise RuntimeError("Output must not overwrite or nest a source directory")
    output.mkdir(parents=True, exist_ok=True)
    # Method C face keys identify which D3b faces are the Method D refill
    bpy.ops.wm.open_mainfile(filepath=str(mc))
    mo = bpy.data.objects[TARGET]
    c_faces = {fkey([mo.data.vertices[i].co for i in p.vertices]) for p in mo.data.polygons}
    bpy.ops.wm.open_mainfile(filepath=str(d3b))
    obj = bpy.data.objects[TARGET]
    if obj.matrix_world != obj.matrix_world.Identity(4):
        raise RuntimeError("Carrier transform changed; STOP")
    if geometry_sha256(obj) != D3B_GEOMETRY_SHA:
        raise RuntimeError("D3b geometry SHA mismatch; STOP")
    me = obj.data
    before = topology(obj)
    contacts_before = local_self_contacts(obj, -9.6, -4.0)
    # record shading normals of every loop (old loops must keep them)
    cn = me.corner_normals
    old_normal_of = {}
    for p in me.polygons:
        k = fkey([me.vertices[i].co for i in p.vertices])
        for li in p.loop_indices:
            vi = me.loops[li].vertex_index
            old_normal_of[(k, rkey(me.vertices[vi].co))] = tuple(cn[li].vector)
    bm = bmesh.new()
    bm.from_mesh(me)
    lay = bm.verts.layers.int.new("orig_id")
    for v in bm.verts:
        v[lay] = v.index
    refill = {f for f in bm.faces if fkey([v.co for v in f.verts]) not in c_faces}
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
    comps.sort(key=lambda c: (-len(c), min(rkey(v.co) for f in c for v in f.verts)))
    protected = {rkey(v.co) for v in bm.verts
                 if not any(f in refill for f in v.link_faces) or
                 any(f not in refill for f in v.link_faces)}
    report, skipped = {}, []
    all_new_faces = []
    for ci, comp in enumerate(comps):
        if len(comp) < MIN_COMPONENT_FACES:
            skipped.append(len(comp))
            continue
        cen = sum((v.co for f in comp for v in f.verts), Vector()) / sum(len(f.verts) for f in comp)
        rail = min(RAILS, key=lambda r: min(math.hypot(cen.x - x, cen.z - z) for x, z in r["pts"]))
        name = f"island_{ci}_{rail['name']}"
        faces, loop, dom = build_component(bm, comp, rail, name, old_normal_of, report)
        faces, report[name]["uv"] = assign_uvs(bm, faces, loop, dom)
        all_new_faces += faces
    bm.normal_update()
    # new-loop shading normals: per smooth fan; fans touching old faces keep old normal
    newset = set(f for f in all_new_faces if f.is_valid)
    new_loop_normal = {}
    for f in newset:
        k = fkey([v.co for v in f.verts])
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
            old = [old_normal_of.get((fkey([u.co for u in g.verts]), rkey(v.co))) for g in fan if g not in newset]
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
            new_loop_normal[(k, rkey(v.co))] = tuple(nv)
    bm.verts.layers.int.remove(lay)
    bm.to_mesh(me)
    bm.free()
    me.update()
    loop_normals = []
    missing_norm = 0
    for p in me.polygons:
        k = fkey([me.vertices[i].co for i in p.vertices])
        for li in p.loop_indices:
            vk = rkey(me.vertices[me.loops[li].vertex_index].co)
            nv = new_loop_normal.get((k, vk)) or old_normal_of.get((k, vk))
            if nv is None:
                missing_norm += 1
                nv = (0.0, 0.0, 0.0)
            loop_normals.append(nv)
    me.normals_split_custom_set(loop_normals)
    me.update()
    # UV audit of every face that differs from Method C (incl. untouched D3b fragments)
    uvl = me.uv_layers.active
    co = np.array([v.co[:] for v in me.vertices])
    newp = [p for p in me.polygons if fkey([me.vertices[i].co for i in p.vertices]) not in c_faces]
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
    after = topology(obj)
    contacts_after = local_self_contacts(obj, -9.6, -4.0)
    final = {rkey(v.co) for v in me.vertices}
    missing_protected = len(protected - final)
    # old-loop normal preservation
    cn2 = me.corner_normals
    dev = []
    for p in me.polygons:
        k = fkey([me.vertices[i].co for i in p.vertices])
        for li in p.loop_indices:
            vk = rkey(me.vertices[me.loops[li].vertex_index].co)
            o = old_normal_of.get((k, vk))
            if o is not None and (k, vk) not in new_loop_normal:
                dev.append(math.degrees(Vector(o).angle(cn2[li].vector, 0.0)))
    scene = bpy.context.scene
    scene["candidate"] = "C11_METHOD_D4_JOINT_FACETS_UNAPPROVED"
    scene["c11_method_d4_source_sha256"] = D3B_SHA
    dest = output / "c11_method_d4_joint_facets_UNAPPROVED.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(dest), compress=True, copy=True)
    winding = True
    bmw = bmesh.new()
    bmw.from_mesh(me)
    winding = all(e.link_loops[0].vert is not e.link_loops[1].vert for e in bmw.edges if len(e.link_loops) == 2)
    bmw.free()
    conts = [r["joint_continuity"] for r in report.values() if r.get("joint_continuity")]
    checks = {
        "closed_manifold": after["boundary_edges"] == 0 and after["nonmanifold_edges"] == 0,
        "no_degenerate_faces": after["degenerate_faces"] == 0,
        "no_new_local_self_contacts": contacts_after <= contacts_before,
        "protected_vertices_unchanged": missing_protected == 0,
        "consistent_winding": winding,
        "old_loop_normals_preserved_deg_lt_0.5": (max(dev) if dev else 0.0) < 0.5,
        "every_loop_has_normal": missing_norm == 0,
        "fracture_riser_continuous": all(c["riser_continuous"] for c in conts) and len(conts) >= 2,
        "sources_sha_intact": sha(d3b) == D3B_SHA and sha(mc) == METHOD_C_SHA,
        "uv_no_flipped_triangles": uv_report["flipped_uv"] == 0,
        "uv_no_zero_area_triangles": uv_report["zero_area_uv"] == 0,
        "uv_no_overlaps_repair_and_ring": uv_report["overlap_pairs"] == 0,
        "uv_perimeter_continuous": all(r["uv"]["perimeter_uv_mismatch_max"] < 1e-5 for r in report.values()),
    }
    result = {
        "status": "CANDIDATE_ONLY", "method": "D4_constrained_voronoi_planar_joint_facets",
        "d3b_source_sha256": D3B_SHA, "d3b_geometry_sha256": D3B_GEOMETRY_SHA,
        "method_c_sha256": METHOD_C_SHA, "candidate_sha256": sha(dest),
        "carrier_geometry_sha256": geometry_sha256(obj),
        "before": before, "after": after,
        "local_self_contacts": {"before": contacts_before, "after": contacts_after},
        "protected_vertices": len(protected), "protected_vertices_missing": missing_protected,
        "old_loop_normal_max_dev_deg": round(max(dev), 4) if dev else 0.0,
        "skipped_small_components_faces": skipped,
        "islands": report, "uv_audit": uv_report, "checks": checks,
        "G1": "BLOCKED", "G2": "NOT_RUN", "G3": "PARTIAL_LOCAL" if all(checks.values()) else "FAIL",
        "G4": "NOT_RUN",
    }
    (output / "c11_method_d4_report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("METHOD_D4", json.dumps({k: result[k] for k in ("checks", "before", "after", "local_self_contacts")}), flush=True)
    if not all(checks.values()):
        raise RuntimeError("Method D4 stop condition; candidate retained for diagnosis only")


if __name__ == "__main__":
    main()

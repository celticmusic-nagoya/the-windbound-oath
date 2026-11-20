"""C11 Method D: replace junction boolean slits with authored fracture channels.

Root cause (measured 2026-11-20, Claude): the persistent thin "blades" in C11
Method B/C come from the two EXACT-boolean V-notch slits added by
sculpt_junction.py (C10 -> junction stage), not from the C11 recess patch.
Each slit is 0.18-0.72 wide but 0.30-0.87 deep with ruled planar walls up to
2.4 units tall and an unbevelled lip; under the review light the lit wall
reads as a raised plate. Methods B/C displaced a different face island, so the
slit geometry survived unchanged.

Method D (structurally different from B/C): delete each slit plus a collar as
one closed face island, keep every perimeter vertex bit-for-bit, refill the
hole with a constrained-Delaunay triangulation over the asset-local XZ plane,
solve a harmonic membrane from the fixed perimeter (continuity with the
existing bedrock/hero sculpt), then carve a broad asymmetric fracture channel
with width/depth > 1.5, rounded lips, dipping bedding ledges and low-amplitude
noise. No new sheet, no duplicate wall, no boolean.

Run with Blender 5.3.0:
  blender -b --factory-startup --python c11_method_d_channel.py -- \
      INPUT.blend SLIT_IDS.json OUT_DIR
Never modifies INPUT. Output is CANDIDATE ONLY (G1 BLOCKED, G2 NOT_RUN).
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector, noise
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt

SOURCE_SHA = "d0e91ae7543f2995b70c2a3f2d59e625d7cc828e6328ccc90c9224d060b0b545"
TARGET = "Cliff C8 B | joinable coastal segment"
# Rails = measured junction fracture centrelines (sculpt_junction.RAILS),
# bottom -> top: x, z, original cutter half-width. Same asset-local frame.
RAILS = (
    {"name": "west_fracture", "rings": 2, "fade": 0.22, "depth_scale": 1.0, "seed": 11,
     "pts": ((-7.35, 0.95, .09), (-7.47, 2.35, .19), (-7.98, 4.80, .28), (-8.24, 6.95, .36)),
     # side +1 means the steep (light-catching) joint face is on +x side
     "steep_side": +1},
    {"name": "central_fracture", "rings": 1, "fade": 0.18, "depth_scale": 0.5, "seed": 23,
     "pts": ((-5.42, 2.30, .10), (-5.72, 3.62, .18), (-5.97, 5.05, .27), (-5.67, 6.80, .21)),
     "steep_side": -1},
)
COLLAR = 0.45          # region half-width = cutter half + collar
FRONT_Y = -1.0         # only seaward wall faces
MIN_Z = 0.3
SPACING = 0.055        # interior sample spacing of the refill (asset units)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def smoothstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def rail_query(pts, x, z):
    """Closest point on polyline in XZ: distance, signed side, s (0..1), half."""
    seg_len = [math.dist((a[0], a[1]), (b[0], b[1])) for a, b in zip(pts, pts[1:])]
    total = sum(seg_len)
    best = None
    acc = 0.0
    for (a, b), L in zip(zip(pts, pts[1:]), seg_len):
        dx, dz = b[0] - a[0], b[1] - a[1]
        t = max(0.0, min(1.0, ((x - a[0]) * dx + (z - a[1]) * dz) / (L * L)))
        px, pz = a[0] + t * dx, a[1] + t * dz
        d = math.hypot(x - px, z - pz)
        cross = dx * (z - a[1]) - dz * (x - a[0])
        side = -1.0 if cross > 0 else 1.0   # +1 = toward +x for an upward rail
        if best is None or d < best[0]:
            best = (d, side, (acc + t * L) / total, a[2] + t * (b[2] - a[2]))
        acc += L
    return best


def in_region(rail, co):
    d, _, _, half = rail_query(rail["pts"], co.x, co.z)
    return d < half + COLLAR and co.y < FRONT_Y and MIN_Z < co.z <= rail["zcap"]


def point_in_poly(x, z, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, zi = poly[i]
        xj, zj = poly[j]
        if (zi > z) != (zj > z) and x < (xj - xi) * (z - zi) / (zj - zi + 1e-30) + xi:
            inside = not inside
        j = i
    return inside


def segs_intersect(p1, p2, p3, p4, eps=1e-5):
    """Proper crossing, touching or collinear overlap of non-adjacent segments."""
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


def channel_offset(rail, x, z):
    """+y (inland) carve depth for the authored fracture channel at (x, z)."""
    d, side, s, half = rail_query(rail["pts"], x, z)
    seed = rail["seed"]
    # irregular width / depth along the rail (two octaves, deterministic)
    n1 = noise.noise(Vector((s * 3.1, seed, 0.3)))
    n2 = noise.noise(Vector((s * 9.7, seed * 0.5, 1.7)))
    width = 0.30 + 0.85 * half + 0.10 * n1 + 0.04 * n2          # 0.33 .. 0.69
    depth = 0.22 + 0.45 * half + 0.06 * n1 - 0.03 * n2          # ~0.24 .. 0.40
    # taper both ends so the channel dies into the wall / crest naturally
    taper = smoothstep(0.0, 0.12, s) * (1.0 - 0.55 * smoothstep(0.80, 1.0, s))
    t = d / width
    steep = side == rail["steep_side"]
    floor = 0.16
    if t <= floor:
        g = 1.0
    else:
        u = (t - floor) / (1.0 - floor)
        if u >= 1.0:
            g = 0.0
        elif steep:   # joint face: holds depth, then breaks over a rounded lip
            g = 1.0 - smoothstep(0.0, 1.0, u) ** 0.55
        else:         # weathered slope side
            g = (1.0 - u) ** 1.8
    depth *= rail.get("depth_scale", 1.0)
    carve = depth * taper * g
    # rounded, slightly chipped lip on the steep side (outward = -y)
    if steep:
        lip = 0.035 * math.exp(-((t - 1.05) / 0.16) ** 2)
        lip *= 0.6 + 0.4 * noise.noise(Vector((x * 4.0, z * 4.0, seed)))
        carve -= lip * taper
    # bedding ledges: dipping layers ~0.5 apart, only inside the channel walls
    if t < 1.35:
        layer_coord = (z + 0.18 * x) / 0.52 + 0.15 * n1
        frac = layer_coord - math.floor(layer_coord)
        ledge = smoothstep(0.78, 0.96, frac) - 0.5
        carve += 0.03 * rail.get("depth_scale", 1.0) * ledge * smoothstep(1.35, 0.6, t) * taper
    # low-amplitude rock grain everywhere in the refill
    carve += 0.012 * noise.noise(Vector((x * 3.5, z * 3.5, seed + 0.5)))
    return carve


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


def geometry_sha256(obj):
    import struct
    h = hashlib.sha256()
    for v in obj.data.vertices:
        h.update(struct.pack("<3f", *v.co))
    for f in obj.data.polygons:
        h.update(struct.pack(f"<{len(f.vertices)}i", *f.vertices))
    return h.hexdigest()


def winding_ok(obj):
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        return all(e.link_loops[0].vert is not e.link_loops[1].vert
                   for e in bm.edges if len(e.link_loops) == 2)
    finally:
        bm.free()


def local_self_contacts(obj, xmin, xmax):
    mesh = obj.data
    mesh.calc_loop_triangles()
    co = [v.co.copy() for v in mesh.vertices]
    tris = [tuple(t.vertices) for t in mesh.loop_triangles
            if xmin < min(co[i].x for i in t.vertices) and max(co[i].x for i in t.vertices) < xmax]
    bvh = BVHTree.FromPolygons(co, tris, all_triangles=True)
    return sum(a < b and not set(tris[a]) & set(tris[b]) for a, b in bvh.overlap(bvh))


def ring_region(bm, seed_faces, rings, min_z):
    region = set(seed_faces)
    frontier = set(seed_faces)
    for _ in range(rings):
        nxt = set()
        for f in frontier:
            for e in f.edges:
                for g in e.link_faces:
                    if g not in region and all(v.co.z > min_z for v in g.verts):
                        nxt.add(g)
        region |= nxt
        frontier = nxt
    return region


def enclose_holes(region):
    """Add unselected face islands fully enclosed by the region (hole closure)."""
    border_faces = set()
    for f in region:
        for e in f.edges:
            for g in e.link_faces:
                if g not in region:
                    border_faces.add(g)
    seen = set()
    for start in border_faces:
        if start in seen:
            continue
        comp, stack, escaped = set(), [start], False
        while stack and not escaped:
            f = stack.pop()
            if f in comp:
                continue
            comp.add(f)
            if len(comp) > 400:
                escaped = True
                break
            for e in f.edges:
                for g in e.link_faces:
                    if g not in region and g not in comp:
                        stack.append(g)
        seen |= comp
        if not escaped:
            region |= comp
    return region


def rebuild_rail(bm, rail, slit_ids, report):
    lay = bm.verts.layers.int["orig_id"]
    slit_set = set(slit_ids)
    window = [v for v in bm.verts if v[lay] in slit_set
              and rail_query(rail["pts"], v.co.x, v.co.z)[0] < 0.6]
    seed_faces = {f for v in window for f in v.link_faces}
    region = enclose_holes(ring_region(bm, seed_faces, rail["rings"], MIN_Z))
    comps, pending = [], set(region)
    while pending:
        st = [pending.pop()]
        comp = set(st)
        while st:
            f = st.pop()
            for e in f.edges:
                for g in e.link_faces:
                    if g in pending:
                        pending.discard(g); comp.add(g); st.append(g)
        comps.append(comp)
    comps.sort(key=lambda c: (-len(c), min(f.index for f in c)))
    all_inner = {v for f in region for v in f.verts}
    window_ids = {v[lay] for v in window}
    results = []
    for ci, comp in enumerate(comps):
        if not all(f.is_valid for f in comp):
            raise RuntimeError(f"{rail['name']}: component {ci} invalidated by previous fill; STOP")
        results.append(fill_component(bm, rail, comp, lay))
    present = {v[lay] for v in bm.verts}
    remaining = sorted(window_ids & present)
    report[rail["name"]] = {
        "region_rings": rail["rings"], "components": [r[2] for r in results],
        "slit_vertices_in_window": len(window_ids),
        "slit_vertices_remaining": remaining,
    }
    return results


def fill_component(bm, rail, region, lay):
    border = {e for f in region for e in f.edges if sum(l in region for l in e.link_faces) == 1}
    adj = {}
    for e in border:
        a, b = e.verts
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    if any(len(n) != 2 for n in adj.values()):
        raise RuntimeError(f"{rail['name']}: perimeter not a simple loop; STOP")
    key = lambda v: (v[lay], tuple(round(c, 7) for c in v.co))
    for v in adj:
        adj[v].sort(key=key)   # deterministic traversal (set order is id-based)
    start = min(adj, key=key)
    loop, prev, cur = [start], None, start
    while True:
        nxt = adj[cur][0] if adj[cur][0] is not prev else adj[cur][1]
        if nxt is start:
            break
        loop.append(nxt)
        prev, cur = cur, nxt
    if len(loop) != len(adj):
        rest = set(adj) - set(loop)
        info = []
        while rest:
            st = [rest.pop()]
            comp = set(st)
            while st:
                x = st.pop()
                for y in adj[x]:
                    if y in rest:
                        rest.discard(y); comp.add(y); st.append(y)
            info.append((len(comp), [round(c, 2) for c in sum((v.co for v in comp), Vector()) / len(comp)]))
        raise RuntimeError(f"{rail['name']}: multiple perimeter loops main={len(loop)} others={info}; STOP")
    loopset = set(loop)
    inner_old = {v for f in region for v in f.verts} - loopset
    avg = Vector()
    for f in region:
        avg += f.normal * f.calc_area()
    avg.normalize()
    if avg.y > 0:
        avg = -avg
    # 2) projected constrained-Delaunay refill (uniform triangles), choosing
    #    the first projection axis under which the perimeter is a simple polygon
    def axis(az, el):
        az, el = math.radians(az), math.radians(el)
        return Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    grid = sorted(((az, el) for az in (0, -12, 12, -25, 25, -40, 40) for el in (0, 20, 35, 50)),
                  key=lambda p: abs(p[0]) + p[1])
    cands = [axis(az, el) for az, el in grid]
    cands += [(avg * (1 - m) + Vector((0, -1, 0)) * m).normalized() for m in (0.35, 0.0)]
    tried, basis = [], None
    for N in cands:
        U = Vector((0, 0, 1)).cross(N).normalized()
        V = N.cross(U).normalized()
        poly = [(v.co.dot(U), v.co.dot(V)) for v in loop]
        n = len(poly)
        simple = not any(segs_intersect(poly[i], poly[(i + 1) % n], poly[j], poly[(j + 1) % n])
                         for i in range(n) for j in range(i + 2, n) if not (i == 0 and j == n - 1))
        tried.append({"normal": [round(c, 4) for c in N], "simple": simple})
        if simple:
            basis = (N, U, V)
            break
    if basis is None:
        return fill_component_disk(bm, rail, region, lay, loop, inner_old, tried)
    N, U, V = basis
    # 1) remove the slit island, keeping the perimeter loop bit-for-bit
    bmesh.ops.delete(bm, geom=sorted(region, key=lambda f: f.index), context="FACES_ONLY")
    for v in sorted((v for v in inner_old if not v.link_faces), key=lambda v: (v[lay], tuple(v.co))):
        bm.verts.remove(v)
    wires = {e for v in loop for e in v.link_edges if not e.link_faces}
    for e in sorted(wires, key=lambda e: sorted((v[lay], tuple(v.co)) for v in e.verts)):
        bm.edges.remove(e)   # edge only; never its (locked) vertices
    xs = [p[0] for p in poly]
    zs = [p[1] for p in poly]
    pts = []
    kx = 0
    z = min(zs) + SPACING * 0.5
    while z < max(zs):
        x = min(xs) + SPACING * (0.5 + 0.5 * (kx % 2))
        while x < max(xs):
            jx = 0.28 * SPACING * noise.noise(Vector((x * 37.1, z * 37.1, 3.3)))
            jz = 0.28 * SPACING * noise.noise(Vector((x * 37.1, z * 37.1, 7.7)))
            px, pz = x + jx, z + jz
            if point_in_poly(px, pz, poly) and \
                    min(math.hypot(px - bx, pz - bz) for bx, bz in poly) > SPACING * 0.6:
                pts.append((px, pz))
            x += SPACING
        z += SPACING * 0.866
        kx += 1
    coords = [Vector(p) for p in poly] + [Vector(p) for p in pts]
    out = delaunay_2d_cdt(coords, [(i, (i + 1) % n) for i in range(n)], [list(range(n))], 1, 1e-7)
    o_verts, o_faces, o_orig = out[0], out[2], out[3]
    out_to_in = {oi: origs[0] for oi, origs in enumerate(o_orig) if origs}
    if len(out_to_in) != len(o_verts):
        raise RuntimeError(f"{rail['name']}: CDT created unexpected vertices; STOP")
    new_verts = [bm.verts.new(U * px + V * pz) for px, pz in pts]
    for v in new_verts:
        v[lay] = -1
    in_to_bm = {i: loop[i] for i in range(n)}
    in_to_bm.update({n + i: v for i, v in enumerate(new_verts)})
    faces = []
    for t in o_faces:
        vs = [in_to_bm[out_to_in[i]] for i in t]
        if len(set(vs)) == 3:
            faces.append(bm.faces.new(vs))
    for v in [v for v in new_verts if not v.link_faces]:
        new_verts.remove(v)
        bm.verts.remove(v)
    # 3) harmonic membrane of the height along N, perimeter fixed
    h = {b: b.co.dot(N) for b in loop}
    nbr = {v: [e.other_vert(v) for e in v.link_edges] for v in new_verts}
    for v in new_verts:
        pu, pv = v.co.dot(U), v.co.dot(V)
        wsum = hsum = 0.0
        for b in loop:
            w = 1.0 / (math.hypot(pu - b.co.dot(U), pv - b.co.dot(V)) ** 2 + 1e-6)
            wsum += w
            hsum += w * h[b]
        h[v] = hsum / wsum
    delta = 0.0
    for _ in range(800):
        delta = 0.0
        for v in new_verts:
            val = sum(h[u] for u in nbr[v]) / len(nbr[v])
            delta = max(delta, abs(val - h[v]))
            h[v] = val
        if delta < 1e-6:
            break
    membrane_residual = delta
    # 4) authored channel carve along +Y, faded to zero at the locked perimeter
    for v in new_verts:
        v.co = v.co + N * h[v]
    bm.normal_update()
    clear_bvh = BVHTree.FromBMesh(bm)
    clamped = 0
    carve_of = {}
    for v in new_verts:
        base = v.co.copy()
        dmin = min(math.hypot(base.dot(U) - bx, base.dot(V) - bz) for bx, bz in poly)
        carve = smoothstep(0.0, rail["fade"], dmin) * channel_offset(rail, base.x, base.z)
        if carve > 0:
            # clearance-limited: never carve deeper than 45% of the free
            # distance to the next surface behind (prevents self-contact)
            hit = clear_bvh.ray_cast(base + Vector((0, 2e-3, 0)), Vector((0, 1, 0)), 2.0)
            if hit[0] is not None and carve > 0.45 * (hit[2] + 2e-3):
                carve = 0.45 * (hit[2] + 2e-3)
                clamped += 1
        v.co = base + Vector((0, 1, 0)) * carve
        carve_of[v] = (base, carve)
    # contact relaxation: halve the carve of refill vertices whose triangles
    # touch untouched geometry, until no new/old contacts remain (max 8 passes)
    relax_passes = 0
    for relax_passes in range(1, 9):
        bm.verts.index_update()
        newv = set(new_verts)
        tri_new = [f for f in faces if f.is_valid]
        tri_old = [tuple(l.vert for l in lt) for lt in bm.calc_loop_triangles()
                   if not any(l.vert in newv for l in lt)
                   and any(-9.6 < l.vert.co.x < -4.0 for l in lt)]
        bn = BVHTree.FromPolygons([tuple(u.co) for u in bm.verts], [[u.index for u in f.verts] for f in tri_new], all_triangles=True)
        bo = BVHTree.FromPolygons([tuple(u.co) for u in bm.verts], [[u.index for u in t] for t in tri_old], all_triangles=True)
        bad = set()
        for i, j in bn.overlap(bo):
            if not set(tri_new[i].verts) & set(tri_old[j]):
                bad |= {u for u in tri_new[i].verts if u in newv}
        if not bad:
            break
        grow = set(bad)
        for u in bad:
            grow |= {e.other_vert(u) for e in u.link_edges if e.other_vert(u) in newv}
        for u in grow:
            b0, c0 = carve_of[u]
            carve_of[u] = (b0, c0 * 0.5)
            u.co = b0 + Vector((0, 1, 0)) * c0 * 0.5
    # 5) winding consistency from the perimeter (no guessed flips)
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
            for g in e.link_faces:
                if g in newset and g not in done:
                    if not opposite_ok(g, e):
                        g.normal_flip()
                        flipped += 1
                    done.add(g)
                    queue.append(g)
    for f in faces:
        f.smooth = True
        f.normal_update()
    return faces, loop, {
        "fill_path": "projected_cdt_height_membrane", "carve_clearance_clamped": clamped, "contact_relax_passes": relax_passes,
        "projection_normal": [round(c, 5) for c in N], "projection_attempts": tried,
        "region_faces_removed": len(region), "perimeter_vertices_locked": len(loop),
        "old_interior_vertices_removed": len(inner_old),
        "new_vertices": len(new_verts), "new_faces": len(faces),
        "faces_flipped_by_winding": flipped, "membrane_max_residual": membrane_residual}


def fill_component_disk(bm, rail, region, lay, loop, inner_old, tried):
    """Fallback when no planar projection is simple (crest-wrapping strips):
    map the perimeter to an ellipse sized by its 3D principal extents (convex,
    therefore always simple), triangulate uniformly there, then solve a 3D
    harmonic membrane with the perimeter fixed. No projection folding is
    possible because the parameter domain is convex by construction."""
    import numpy as np
    n = len(loop)
    P = np.array([tuple(v.co) for v in loop])
    c = P.mean(0)
    _, sv, vt = np.linalg.svd(P - c, full_matrices=False)
    proj = (P - c) @ vt[:2].T
    a = max(proj[:, 0].max() - proj[:, 0].min(), 1e-3) / 2
    b = max(proj[:, 1].max() - proj[:, 1].min(), 1e-3) / 2
    # match the parameter-domain area to the true removed surface area so the
    # sample spacing is close to SPACING on the rebuilt surface
    true_area = sum(f.calc_area() for f in region)
    k_area = math.sqrt(true_area / (math.pi * a * b))
    a, b = a * k_area, b * k_area
    proj = proj * k_area
    seg = np.linalg.norm(np.roll(P, -1, 0) - P, axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)[:-1]]) / seg.sum()
    # orient the ellipse parameter with the loop's own winding in PCA space
    area = 0.5 * np.sum(proj[:, 0] * np.roll(proj[:, 1], -1) - np.roll(proj[:, 0], -1) * proj[:, 1])
    sign = 1.0 if area >= 0 else -1.0
    ang0 = math.atan2(proj[0, 1] / b, proj[0, 0] / a)
    poly = [(a * math.cos(ang0 + sign * 2 * math.pi * t), b * math.sin(ang0 + sign * 2 * math.pi * t)) for t in cum]
    pts = []
    k = 0
    z = -b + SPACING * 0.5
    while z < b:
        x = -a + SPACING * (0.5 + 0.5 * (k % 2))
        while x < a:
            if (x / a) ** 2 + (z / b) ** 2 < 1 and \
                    min(math.hypot(x - px, z - pz) for px, pz in poly) > SPACING * 0.6:
                pts.append((x, z))
            x += SPACING
        z += SPACING * 0.866
        k += 1
    coords = [Vector(p) for p in poly] + [Vector(p) for p in pts]
    out = delaunay_2d_cdt(coords, [(i, (i + 1) % n) for i in range(n)], [list(range(n))], 1, 1e-7)
    o_verts, o_faces, o_orig = out[0], out[2], out[3]
    out_to_in = {oi: origs[0] for oi, origs in enumerate(o_orig) if origs}
    if len(out_to_in) != len(o_verts):
        raise RuntimeError(f"{rail['name']}: disk CDT created unexpected vertices; STOP")
    # remove old island (same rules as the projected path)
    bmesh.ops.delete(bm, geom=sorted(region, key=lambda f: f.index), context="FACES_ONLY")
    for v in sorted((v for v in inner_old if not v.link_faces), key=lambda v: (v[lay], tuple(v.co))):
        bm.verts.remove(v)
    for e in sorted({e for v in loop for e in v.link_edges if not e.link_faces},
                    key=lambda e: sorted((v[lay], tuple(v.co)) for v in e.verts)):
        bm.edges.remove(e)
    new_verts = []
    for px, pz in pts:
        wsum, acc = 0.0, Vector()
        for (bx, bz), bv in zip(poly, loop):
            w = 1.0 / (math.hypot(px - bx, pz - bz) ** 2 + 1e-6)
            wsum += w
            acc += bv.co * w
        v = bm.verts.new(acc / wsum)
        v[lay] = -1
        new_verts.append(v)
    in_to_bm = {i: loop[i] for i in range(n)}
    in_to_bm.update({n + i: v for i, v in enumerate(new_verts)})
    faces = []
    for t in o_faces:
        vs = [in_to_bm[out_to_in[i]] for i in t]
        if len(set(vs)) == 3:
            faces.append(bm.faces.new(vs))
    for v in [v for v in new_verts if not v.link_faces]:
        new_verts.remove(v)
        bm.verts.remove(v)
    # vectorised Jacobi relaxation of the 3D membrane (perimeter fixed)
    index = {v: i for i, v in enumerate(new_verts)}
    fixed = {v: j for j, v in enumerate(loop)}
    X = np.array([tuple(v.co) for v in new_verts])
    B = np.array([tuple(v.co) for v in loop])
    rows_n, cols_n, rows_b, cols_b, deg = [], [], [], [], np.zeros(len(new_verts))
    for v in new_verts:
        i = index[v]
        for e in v.link_edges:
            u = e.other_vert(v)
            deg[i] += 1
            if u in index:
                rows_n.append(i); cols_n.append(index[u])
            else:
                rows_b.append(i); cols_b.append(fixed[u])
    rows_n, cols_n = np.array(rows_n, int), np.array(cols_n, int)
    rows_b, cols_b = np.array(rows_b, int), np.array(cols_b, int)
    bsum = np.zeros_like(X)
    np.add.at(bsum, rows_b, B[cols_b])
    delta = 0.0
    for _ in range(6000):
        acc = bsum.copy()
        np.add.at(acc, rows_n, X[cols_n])
        Xn = acc / deg[:, None]
        delta = float(np.abs(Xn - X).max())
        X = 0.3 * X + 0.7 * Xn
        if delta < 1e-6:
            break
    for v in new_verts:
        v.co = Vector(X[index[v]])
    for v in new_verts:
        dmin = min((v.co - b_.co).length for b_ in loop)
        v.co.y += smoothstep(0.0, rail["fade"], dmin) * channel_offset(rail, v.co.x, v.co.z)
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
                    f.normal_flip(); flipped += 1
                done.add(f); queue.append(f)
    while queue:
        f = queue.pop()
        for e in f.edges:
            for g in e.link_faces:
                if g in newset and g not in done:
                    if not opposite_ok(g, e):
                        g.normal_flip(); flipped += 1
                    done.add(g); queue.append(g)
    for f in faces:
        f.smooth = True
        f.normal_update()
    return faces, loop, {
        "fill_path": "convex_disk_parameterisation_3d_membrane",
        "projection_attempts_failed": len(tried),
        "region_faces_removed": len(region), "perimeter_vertices_locked": n,
        "old_interior_vertices_removed": len(inner_old),
        "new_vertices": len(new_verts), "new_faces": len(faces),
        "faces_flipped_by_winding": flipped, "membrane_max_residual": delta}


def assign_uvs(bm, faces, loop):
    """Least-squares affine UV fit from the perimeter's existing UVs."""
    uvl = bm.loops.layers.uv.active
    if uvl is None:
        return None
    newset = set(faces)
    rows, us, vs = [], [], []
    for v in loop:
        for l in v.link_loops:
            if l.face not in newset:
                rows.append((v.co.x, v.co.y, v.co.z, 1.0))
                us.append(l[uvl].uv.x)
                vs.append(l[uvl].uv.y)
    import numpy as np
    A = np.array(rows)
    cu, ru, *_ = np.linalg.lstsq(A, np.array(us), rcond=None)
    cv, rv, *_ = np.linalg.lstsq(A, np.array(vs), rcond=None)
    pu = A @ cu
    pv = A @ cv
    rms = float(np.sqrt(np.mean((pu - us) ** 2 + (pv - vs) ** 2)))
    for f in faces:
        for l in f.loops:
            c = l.vert.co
            l[uvl].uv = (float(cu @ (c.x, c.y, c.z, 1)), float(cv @ (c.x, c.y, c.z, 1)))
    return rms


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    source, ids_path, output = (Path(a).resolve() for a in argv)
    if tuple(bpy.app.version) != (5, 3, 0):
        raise RuntimeError("Requires Blender 5.3.0")
    if sha(source) != SOURCE_SHA:
        raise RuntimeError("C11 Method C input SHA mismatch; STOP")
    if output == source.parent or source.parent in [output, *output.parents]:
        raise RuntimeError("Output must not overwrite or nest the source directory")
    output.mkdir(parents=True, exist_ok=True)
    slit_ids = json.loads(ids_path.read_text())["vertex_ids"]
    bpy.ops.wm.open_mainfile(filepath=str(source))
    obj = bpy.data.objects[TARGET]
    if obj.matrix_world != obj.matrix_world.Identity(4):
        raise RuntimeError("Carrier transform changed; STOP")
    before = topology(obj)
    contacts_before = local_self_contacts(obj, -9.6, -4.0)
    # protect everything outside both regions bit-for-bit
    original = {i: tuple(v.co) for i, v in enumerate(obj.data.vertices)}
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    report = {}
    lay = bm.verts.layers.int.new("orig_id")
    for v in bm.verts:
        v[lay] = v.index
    # vertices created later get -1 via layer default; verify
    removed_orig = set()
    for rail in RAILS:
        bm.verts.ensure_lookup_table()
        before_ids = {v[lay] for v in bm.verts if v[lay] >= 0}
        results = rebuild_rail(bm, rail, slit_ids, report)
        after_ids = {v[lay] for v in bm.verts if v[lay] >= 0}
        removed_orig |= before_ids - after_ids
        for (faces, loop, rec) in results:
            rec["uv_fit_rms"] = assign_uvs(bm, faces, loop)
        for v in bm.verts:
            pass
    bm.verts.layers.int.remove(lay)
    bm.normal_update()
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    after = topology(obj)
    contacts_after = local_self_contacts(obj, -9.6, -4.0)
    # every original coordinate that was not inside a rebuilt region must survive
    final = {tuple(v.co) for v in obj.data.vertices}
    final = {}
    for v in obj.data.vertices:
        final.setdefault(tuple(v.co), 0)
    missing_outside = [i for i, c in original.items() if i not in removed_orig and c not in final]
    scene = bpy.context.scene
    scene["candidate"] = "C11_METHOD_D_FRACTURE_CHANNEL_UNAPPROVED"
    scene["c11_method_d_source_sha256"] = SOURCE_SHA
    dest = output / "c11_method_d_channel_UNAPPROVED.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(dest), compress=True, copy=True)
    checks = {
        "closed_manifold": after["boundary_edges"] == 0 and after["nonmanifold_edges"] == 0,
        "no_degenerate_faces": after["degenerate_faces"] == 0,
        "no_new_local_self_contacts": contacts_after <= contacts_before,
        "outside_vertices_unchanged": not missing_outside,
        "consistent_winding": winding_ok(obj),
        "all_slit_vertices_removed": all(not r["slit_vertices_remaining"] for r in report.values()),
        "source_sha_intact": sha(source) == SOURCE_SHA,
    }
    result = {
        "status": "CANDIDATE_ONLY", "method": "D_slit_removal_cdt_membrane_channel",
        "source_sha256": SOURCE_SHA, "candidate_sha256": sha(dest),
        "slit_ids_file_sha256": sha(ids_path),
        "carrier_geometry_sha256": geometry_sha256(obj),
        "before": before, "after": after,
        "local_self_contacts": {"before": contacts_before, "after": contacts_after},
        "missing_outside_vertices": len(missing_outside),
        "removed_original_vertices": len(removed_orig),
        "rails": report, "checks": checks,
        "G1": "BLOCKED", "G2": "NOT_RUN", "G3": "PARTIAL_LOCAL" if all(checks.values()) else "FAIL",
        "G4": "NOT_RUN",
    }
    (output / "c11_method_d_report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("METHOD_D", json.dumps({k: result[k] for k in ("checks", "before", "after", "local_self_contacts")}), flush=True)
    if not all(checks.values()):
        raise RuntimeError("Method D stop condition; candidate retained for diagnosis only")


if __name__ == "__main__":
    main()

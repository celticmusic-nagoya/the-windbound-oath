"""MORWEN-LOCAL-RETOPO-03: one local-retopology candidate for the nose bridge/tip (in-memory build).

Non-destructive: the pinned VRM is imported, edited in memory and never written back. The
candidate can be saved to $MORWEN_OUT as a derived .blend for review (artifact only).

Construction (all deterministic):
1. Region: Face-skin triangles whose vertices all lie inside a teardrop around the measured nose
   tip (front x/z plane). Their boundary vertices stay untouched, so everything outside the
   region (and the Face/Body seam) is bit-identical.
2. Rings: the boundary loop is resampled by angle in normalised teardrop space; rings are
   scaled copies toward the tip (16 vertices, then 8 around the tip, then a centre vertex).
   Loops of different vertex counts are joined by a monotone zipper triangulation.
3. Height: y = thin-plate fill of the boundary + outer one-ring (slope continuity)
          + A * smoothstep(s)^p     (zero value and zero slope at the boundary)
   A keeps the measured baseline nose-tip projection in the Basis shape.
4. Transfer: every new vertex is projected (front ray) onto the ORIGINAL surface; UV, vertex
   weights and all 56 shape-key offsets are interpolated barycentrically from that triangle.
5. Custom split normals of untouched corners are restored exactly; patch corners are set to
   zero (= auto normal, so shading follows the design key and expressions); boundary corners
   on patch faces use the original normal.
6. Design range: shape key MORWEN_DESIGN_NoseDepth adds extra tip projection with the same
   profile. Nose depth stays an art decision.
"""
import hashlib
import importlib.util
import json
import math
import os
import sys
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

HERE = Path(__file__).resolve().parent
LM_DIR = HERE.parent / "head_landmark"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


M3 = _load(LM_DIR / "measure_head_landmarks_3d.py", "morwen_m3")
PARAMS_PATH = Path(os.environ.get("MORWEN_NOSE_PARAMS", HERE / "nose_params_03.json"))


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def smoothstep(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


class Teardrop:
    def __init__(self, tip, nasion, p):
        self.cx, self.cz = tip.x, tip.z
        self.up = (nasion.z + p["z_above_tip_to_top_m_from_nasion"]) - tip.z
        self.down = p["z_below_tip_m"]
        self.ax = p["x_half_m"]
        self.taper = p["x_taper_toward_nasion"]

    def ax_at(self, dz):
        return self.ax * (1 - self.taper * min(1.0, max(0.0, dz / self.up)))

    def rho_theta(self, x, z):
        dz = z - self.cz
        az = self.up if dz > 0 else self.down
        u = (x - self.cx) / self.ax_at(dz)
        v = dz / az
        return math.hypot(u, v), math.atan2(v, u)


def tps_fit(P, y):
    """2D thin-plate spline y(x,z) through points P (n,2)."""
    P = np.asarray(P, float)
    n = len(P)
    r = np.linalg.norm(P[:, None] - P[None], axis=-1)
    with np.errstate(divide="ignore", invalid="ignore"):
        K = np.where(r > 0, r * r * np.log(r), 0.0)
    A = np.zeros((n + 3, n + 3))
    A[:n, :n] = K + 1e-12 * np.eye(n)
    A[:n, n] = 1
    A[:n, n + 1:] = P
    A[n, :n] = 1
    A[n + 1:, :n] = P.T
    sol = np.linalg.solve(A, np.concatenate([y, np.zeros(3)]))

    def f(Q):
        Q = np.atleast_2d(np.asarray(Q, float))
        rr = np.linalg.norm(Q[:, None] - P[None], axis=-1)
        with np.errstate(divide="ignore", invalid="ignore"):
            KK = np.where(rr > 0, rr * rr * np.log(rr), 0.0)
        return KK @ sol[:n] + sol[n] + Q @ sol[n + 1:]
    return f


def zipper(outer_t, inner_t):
    """Triangles joining two closed loops ordered in the same angular direction.
    outer_t / inner_t: angular fraction in [0,1) of every vertex (first vertex near 0).
    Returns triangles of tagged indices (('o', i) / ('i', j)); advances whichever side is
    angularly behind, so non-uniform loops never fold."""
    no, ni = len(outer_t), len(inner_t)
    nxt_o = lambda i: outer_t[(i + 1) % no] + (1.0 if i + 1 >= no else 0.0)  # noqa: E731
    nxt_i = lambda j: inner_t[(j + 1) % ni] + (1.0 if j + 1 >= ni else 0.0)  # noqa: E731
    tris, i, j = [], 0, 0
    while i < no or j < ni:
        if j >= ni or (i < no and nxt_o(i) <= nxt_i(j)):
            tris.append((("o", i % no), ("o", (i + 1) % no), ("i", j % ni)))
            i += 1
        else:
            tris.append((("o", i % no), ("i", (j + 1) % ni), ("i", j % ni)))
            j += 1
    return tris


def ordered_boundary(me, region):
    """Boundary vertex loop of a face set (mesh indices), in edge order; asserts a single loop."""
    count = {}
    for i in region:
        for ek in me.polygons[i].edge_keys:
            count[ek] = count.get(ek, 0) + 1
    edges = [ek for ek, c in count.items() if c == 1]
    adj = {}
    for a, b in edges:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    assert all(len(v) == 2 for v in adj.values()), "region boundary is not a simple loop"
    start = min(adj)
    loop, prev = [start], None
    while True:
        cur = loop[-1]
        nxt = adj[cur][0] if adj[cur][0] != prev else adj[cur][1]
        if nxt == start:
            break
        prev = cur
        loop.append(nxt)
    assert len(loop) == len(adj), "region boundary must be one loop"
    return loop


def select_region(face, td, p, si, co_w):
    """Face-skin triangles inside the teardrop, grown until the boundary has no notches."""
    me = face.data
    region = set()
    for poly in me.polygons:
        if poly.material_index != si:
            continue
        pts = [co_w[v] for v in poly.vertices]
        if all(td.rho_theta(q.x, q.z)[0] < 1.0 and q.y > p["region"]["min_y_m"] for q in pts):
            region.add(poly.index)

    # grow the region until its boundary is star-shaped around the tip without notches:
    # a boundary vertex closer to the tip (normalised rho) than NOTCH x the mean of its two
    # neighbours becomes interior. Deterministic; iteration count recorded.
    notch = p["region"]["notch_ratio"]
    grow_iter = 0
    for grow_iter in range(1, 21):
        order = ordered_boundary(me, region)
        rho = [td.rho_theta(co_w[v].x, co_w[v].z)[0] for v in order]
        bad = [order[i] for i in range(len(order))
               if rho[i] < notch * 0.5 * (rho[i - 1] + rho[(i + 1) % len(order)])]
        if not bad:
            break
        bad = set(bad)
        for poly in me.polygons:
            if poly.material_index == si and bad & set(poly.vertices):
                region.add(poly.index)
    else:
        raise AssertionError("region did not become notch-free in 20 iterations")

    return region, grow_iter


def build(params):
    """Run on the scene already holding the imported source. Returns a build record."""
    p = params
    np.random.seed(p["seed"])
    base = M3.measure()
    L = base["landmarks"]
    tip = Vector(L["pronasale"]["position"])
    nasion = Vector(L["nasion"]["position"])
    td = Teardrop(tip, nasion, p["region"])
    face = bpy.data.objects["Face"]
    me = face.data
    mw = face.matrix_world
    mwi = mw.inverted()
    si = M3.slot_index(face, "Face_00_SKIN")

    # ---- original data for transfer --------------------------------------------------------
    me.calc_loop_triangles()
    co_w = [mw @ v.co for v in me.vertices]
    uv_layer = me.uv_layers.active
    tris0 = [t for t in me.loop_triangles if t.material_index == si]
    bvh0 = BVHTree.FromPolygons(co_w, [t.vertices[:] for t in tris0])
    keys = me.shape_keys.key_blocks
    basis = np.array([v.co[:] for v in keys[0].data])
    key_off = {kb.name: np.array([v.co[:] for v in kb.data]) - basis for kb in keys[1:]}
    groups = {g.index: g.name for g in face.vertex_groups}
    weights = [{groups[g.group]: g.weight for g in v.groups} for v in me.vertices]
    corner_n0 = [tuple(c.vector) for c in me.corner_normals]
    poly_corner_key = {}
    for poly in me.polygons:
        ck = tuple(sorted(tuple(round(c, 7) for c in me.vertices[v].co) for v in poly.vertices))
        poly_corner_key[ck] = {tuple(round(c, 7) for c in me.vertices[v].co): corner_n0[li]
                               for v, li in zip(poly.vertices, poly.loop_indices)}

    def transfer(x, z):
        hit, _, idx, _ = bvh0.ray_cast(Vector((x, 1.0, z)), Vector((0, -1, 0)))
        assert hit is not None, f"no original surface under ({x:.4f},{z:.4f})"
        t = tris0[idx]
        vs = t.vertices[:]
        w = barycentric_transform(hit, *(co_w[i] for i in vs), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)))
        w = np.array([w.x, w.y, w.z])
        uv = sum((Vector(uv_layer.data[li].uv) * w[k] for k, li in enumerate(t.loops)), Vector((0, 0)))
        wt = {}
        for k, i in enumerate(vs):
            for g, val in weights[i].items():
                wt[g] = wt.get(g, 0.0) + val * w[k]
        offs = {name: (off[list(vs)] * w[:, None]).sum(0) for name, off in key_off.items()}
        return hit, uv, wt, offs

    region, grow_iter = select_region(face, td, p, si, co_w)

    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    region_faces = [bm.faces[i] for i in region]
    region_verts = {v for f in region_faces for v in f.verts}
    interior = {v for v in region_verts if all(f.index in region for f in v.link_faces)}
    boundary_edges = [e for f in region_faces for e in f.edges
                      if sum(1 for lf in e.link_faces if lf.index in region) == 1]
    # orient the hole loop: the KEPT face traverses a->b
    nxt = {}
    for e in boundary_edges:
        kept = next(lf for lf in e.link_faces if lf.index not in region)
        vs = list(kept.verts)
        a, b = e.verts
        i = vs.index(a)
        if vs[(i + 1) % len(vs)] is b:
            nxt[a] = b
        else:
            nxt[b] = a
    start = next(iter(nxt))
    loop = [start]
    while True:
        n = nxt[loop[-1]]
        if n is start:
            break
        loop.append(n)
    assert len(loop) == len(nxt), "region boundary must be one simple loop"
    loop_co = [(mw @ v.co) for v in loop]
    loop_uv = []
    uvl = bm.loops.layers.uv.active
    for v in loop:
        lp = next(lp for lp in v.link_loops if lp.face.index not in region)
        loop_uv.append(Vector(lp[uvl].uv))
    outer_ring = {o for v in loop for e in v.link_edges for o in [e.other_vert(v)]
                  if o not in region_verts and any(f.material_index == si for f in o.link_faces)}
    fill_pts = [(mw @ v.co) for v in loop] + [(mw @ v.co) for v in outer_ring]

    bmesh.ops.delete(bm, geom=region_faces, context="FACES_ONLY")
    bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces and all(v in interior for v in e.verts)], context="EDGES")
    bmesh.ops.delete(bm, geom=[v for v in interior if v.is_valid], context="VERTS")

    # ---- rings in (x,z) --------------------------------------------------------------------
    ang = [td.rho_theta(q.x, q.z)[1] for q in loop_co]
    loop_dir = 1 if sum(((ang[(i + 1) % len(ang)] - ang[i] + math.pi) % (2 * math.pi) - math.pi)
                        for i in range(len(ang))) > 0 else -1

    def boundary_at(theta):
        # point on the boundary polyline at teardrop angle theta (ray from tip)
        for i in range(len(loop_co)):
            a, b = ang[i], ang[(i + 1) % len(ang)]
            d = ((b - a + math.pi) % (2 * math.pi)) - math.pi
            t = ((theta - a + math.pi) % (2 * math.pi) - math.pi) / d if abs(d) > 1e-12 else -1
            if 0 <= t <= 1:
                q = loop_co[i].lerp(loop_co[(i + 1) % len(loop_co)], t)
                return Vector((q.x, q.z))
        raise AssertionError("angle not covered by boundary")
    theta0 = ang[0]
    rho_ref = p["rings"]["smooth_rho_ref"]

    def teardrop_point(rho, th):
        v = rho * math.sin(th)
        dz = v * (td.up if v > 0 else td.down)
        return Vector((td.cx + rho * math.cos(th) * td.ax_at(dz), td.cz + dz))
    rings = []
    for s, m, beta in zip(p["rings"]["s"], p["rings"]["vertices_per_ring"], p["rings"]["smooth_blend"]):
        ring = []
        for j in range(m):
            th = theta0 + loop_dir * 2 * math.pi * j / m
            b = boundary_at(th)
            scaled = Vector((tip.x + (b.x - tip.x) * (1 - s), tip.z + (b.y - tip.z) * (1 - s)))
            smooth = teardrop_point(rho_ref * (1 - s), th)
            q = scaled.lerp(smooth, beta)
            t2 = Vector((tip.x, tip.z))
            lim = (scaled - t2).length
            if (q - t2).length > lim:  # never outside the scaled boundary: prevents folds
                q = t2 + (q - t2).normalized() * lim
            ring.append((q.x, q.y, s))
        rings.append(ring)
    # angular fractions for the zipper (same direction and origin as the rings)
    loop_t = [((loop_dir * (a_ - theta0)) % (2 * math.pi)) / (2 * math.pi) for a_ in ang]

    fill = tps_fit([(q.x, q.z) for q in fill_pts], np.array([q.y for q in fill_pts]))
    power = p["shape"]["profile_power"]
    A = tip.y - float(fill([(tip.x, tip.z)])[0])

    def height(x, z, s):
        return float(fill([(x, z)])[0]) + A * smoothstep(s) ** power

    # ---- create vertices with transferred attributes ---------------------------------------
    shape_layers = {kb.name: bm.verts.layers.shape.get(kb.name) for kb in keys}
    dl = bm.verts.layers.deform.active
    gidx = {g.name: g.index for g in face.vertex_groups}
    new_meta = []

    def make_vert(x, z, s):
        y = height(x, z, s)
        _, uv, wt, offs = transfer(x, z)
        v = bm.verts.new(mwi @ Vector((x, y, z)))
        for name, layer in shape_layers.items():
            if name == keys[0].name:
                v[layer] = v.co
            else:
                v[layer] = v.co + mwi.to_3x3() @ Vector(offs[name])
        tot = sum(wt.values())
        for g, val in wt.items():
            if val / tot > 1e-4:
                v[dl][gidx[g]] = val / tot
        new_meta.append((v, uv, s))
        return v
    s0 = p["rings"]["boundary_copy_s"]
    ring0 = [make_vert(tip.x + (q.x - tip.x) * (1 - s0), tip.z + (q.z - tip.z) * (1 - s0), s0) for q in loop_co]
    ring_verts = [[make_vert(x, z, s) for x, z, s in ring] for ring in rings]
    centre = make_vert(tip.x, tip.z, 1.0)
    uv_of = {v: uv for v, uv, _ in new_meta}
    uv_of.update({v: uv for v, uv in zip(loop, loop_uv)})

    # ---- faces -------------------------------------------------------------------------------
    new_faces = []

    def add_face(vs):
        f = bm.faces.new(vs)
        f.material_index = si
        f.smooth = True
        new_faces.append(f)

    chain = [loop, ring0] + ring_verts
    fracs = [loop_t, loop_t] + [[j / len(r) for j in range(len(r))] for r in ring_verts]
    for (outer, ot), (inner, it) in zip(zip(chain[:-1], fracs[:-1]), zip(chain[1:], fracs[1:])):
        if len(outer) == len(inner):
            for k in range(len(outer)):
                add_face([outer[k], outer[(k + 1) % len(outer)], inner[(k + 1) % len(inner)], inner[k]])
        else:
            if outer is ring0:  # rotate so the first vertex is angularly first
                k0 = min(range(len(ot)), key=lambda k: ot[k])
                outer = outer[k0:] + outer[:k0]
                ot = ot[k0:] + ot[:k0]
            for tri in zipper(ot, it):
                add_face([outer[i] if tag == "o" else inner[i] for tag, i in tri])
    last = ring_verts[-1]
    for k in range(len(last)):
        add_face([last[k], last[(k + 1) % len(last)], centre])
    # winding must oppose the kept neighbour on the hole loop
    a, b = loop[0], loop[1]
    f0 = next(f for f in new_faces if a in f.verts and b in f.verts)
    vs = list(f0.verts)
    if vs[(vs.index(a) + 1) % len(vs)] is b:
        bmesh.ops.reverse_faces(bm, faces=new_faces)
    for f in new_faces:
        for lp in f.loops:
            lp[uvl].uv = uv_of[lp.vert]

    bm.verts.index_update()
    patch_idx = sorted({v.index for f in new_faces for v in f.verts})
    s_of = {v.index: s for v, _, s in new_meta}
    loop_idx = [v.index for v in loop]
    bm.to_mesh(me)
    bm.free()
    me.update()

    # ---- custom normals ----------------------------------------------------------------------
    me.calc_loop_triangles()
    smooth = {}
    for poly in me.polygons:
        for v in poly.vertices:
            smooth.setdefault(v, Vector())
            smooth[v] += poly.normal * poly.area
    loop_set = set(loop_idx)
    orig_at = {}
    for poly_map in poly_corner_key.values():
        for k, n in poly_map.items():
            orig_at.setdefault(k, []).append(Vector(n))
    corner = [None] * len(me.loops)
    restored = 0
    for poly in me.polygons:
        ck = tuple(sorted(tuple(round(c, 7) for c in me.vertices[v].co) for v in poly.vertices))
        old = poly_corner_key.get(ck)
        for v, li in zip(poly.vertices, poly.loop_indices):
            key = tuple(round(c, 7) for c in me.vertices[v].co)
            if old is not None:
                corner[li] = old[key]
                restored += 1
            elif v in loop_set:
                corner[li] = tuple(sum(orig_at[key], Vector()).normalized())
            else:
                # zero = "auto normal": patch shading follows the geometry under shape keys
                corner[li] = (0.0, 0.0, 0.0)
    me.normals_split_custom_set(corner)

    # ---- design key ------------------------------------------------------------------------
    dk = face.shape_key_add(name=p["design_range"]["shape_key_name"], from_mix=False)
    extra = p["design_range"]["full_key_extra_projection_U"] * base["normalisation"]["unit_U_m"]
    rot = mwi.to_3x3()
    for i in patch_idx:
        s = s_of.get(i, 0.0)
        dk.data[i].co = me.vertices[i].co + rot @ Vector((0, extra * smoothstep(s) ** power, 0))
    dk.value = 0.0
    return {"baseline": base, "region_faces": len(region), "deleted_vertices": len(interior),
            "boundary_vertices": len(loop_idx), "new_vertices": len(new_meta), "new_faces": len(new_faces),
            "patch_vertex_indices": patch_idx, "boundary_vertex_indices": loop_idx,
            "ring_s": {i: s_of[i] for i in s_of}, "amplitude_m": round(A, 9), "extra_full_m": round(extra, 9),
            "restored_corner_normals": restored, "teardrop": {k: round(v, 9) for k, v in vars(td).items()},
            "region_growth_iterations": grow_iter}

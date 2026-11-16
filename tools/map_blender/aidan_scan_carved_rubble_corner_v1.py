"""AIDAN-MASONRY-ART-02 — scan-carved coursed-rubble corner (method family F8).

Noncanonical candidate study. Never writes to approved/canonical asset paths.

Method (causal difference from stopped families F1-F7):
  * Stone *shape* comes from real CC0 photogrammetry (Poly Haven rock_moss_set_01),
    not from perturbed cubes / rings / noise.
  * A coursed-rubble layout solver (alternating long/short quoins, staggered
    perpends) defines disjoint masonry cells separated by a measured mortar joint.
  * For each cell, candidate scan orientations/scales are scored by ray-cast
    coverage of the exposed face and by point-inside tests on every hidden face,
    then the chosen rock is cut by an exact Boolean INTERSECT with the cell.
    => exposed face = natural scan surface; beds/perpends = exact shared planes.
  * Mortar = wall envelope minus all cells (exact Boolean), so every stone is
    bedded on a mortar slab of measured thickness (JOINT_RANGE): no floating, no interpenetration.

Usage:
  blender -b --python aidan_scan_carved_rubble_corner_v1.py -- \
      --src rock_moss_set_01_8k.blend --tex <dir with rock_boulder_dry_*_2k.jpg> \
      --out <outdir> [--seed 20261116] [--samples 96] [--no-render]
"""
import argparse
import hashlib
import json
import math
import os
import random
import sys
import time

import bmesh
import bpy
from mathutils import Matrix, Vector, Quaternion
from mathutils.bvhtree import BVHTree

# ----------------------------------------------------------------- parameters
LA, LB = 1.55, 1.25          # wall lengths from the corner arris (m)
T = 0.50                     # wall thickness (m)
H_TARGET = 1.70              # module height (m)
JOINT_RANGE = (0.012, 0.032)  # mortar joint thickness range (m), varied per bed and per perpend
SKEW = 0.025                 # perpend skew half-offset (m): joint leans +-2.5 cm over a course
POINT_RECESS = 0.024         # mortar pointing recess behind face plane (m)
COURSE_H = (0.15, 0.27)
STONE_L = (0.20, 0.50)
QUOIN_LONG = (0.44, 0.58)
QUOIN_SHORT = (0.26, 0.34)
STONE_D = (0.30, 0.48)
MIN_STAGGER = 0.075
ROCKS = ["rock01", "rock02", "rock03", "rock05", "rock06"]  # rock04 excluded: 18 boundary edges
N_CAND = 120
FAR = 0.30
FRONT_CAP = 0.032             # max allowed stone protrusion in front of the face plane (m)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--src", required=True)
    p.add_argument("--tex", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--seed", type=int, default=20261116)
    p.add_argument("--samples", type=int, default=96)
    p.add_argument("--res", type=int, default=1200)
    p.add_argument("--no-render", action="store_true")
    p.add_argument("--reuse", action="store_true", help="look-dev: re-render saved geometry with rebuilt materials")
    return p.parse_args(argv)


# ------------------------------------------------------------------- layout
def prism(along, a_b0, a_b1, a_t0, a_t1, d0, d1, z0, z1):
    """8 vertices of a cell whose two end faces may be slanted (perpend skew).
    along='x' -> stone runs along X (wall A), depth along Y; along='y' swaps."""
    pts = []
    for zz, a0, a1 in ((z0, a_b0, a_b1), (z1, a_t0, a_t1)):
        for (a, d) in ((a0, d0), (a1, d0), (a1, d1), (a0, d1)):
            pts.append((a, d, zz) if along == "x" else (d, a, zz))
    return pts


def bbox(pts):
    return (min(p[0] for p in pts), max(p[0] for p in pts), min(p[1] for p in pts),
            max(p[1] for p in pts), min(p[2] for p in pts), max(p[2] for p in pts))


def solve_layout(rng):
    """Coursed rubble grammar v2: alternating quoins, staggered *skewed* perpends,
    per-bed and per-perpend joint thickness variation. Beds stay level (load path)."""
    courses = []
    z = 0.0
    while True:
        h = rng.uniform(*COURSE_H)
        if z + h > H_TARGET - COURSE_H[0] * 0.6:
            courses.append((z, H_TARGET))
            break
        courses.append((z, z + h))
        z += h
    beds = [rng.uniform(*JOINT_RANGE) for _ in range(len(courses) + 1)]
    cells = []
    prev = {"A": [], "B": []}
    for i, (c0, c1) in enumerate(courses):
        z0, z1 = c0 + beds[i] / 2, c1 - beds[i + 1] / 2
        ql, qs = rng.uniform(*QUOIN_LONG), rng.uniform(*QUOIN_SHORT)
        qa, qb = (ql, qs) if i % 2 == 0 else (qs, ql)
        ska, skb = rng.uniform(-SKEW, SKEW), rng.uniform(-SKEW, SKEW)
        ga, gb = rng.uniform(*JOINT_RANGE) / 2, rng.uniform(*JOINT_RANGE) / 2
        qa_b, qa_t = qa - ska - ga, qa + ska - ga
        qb_b, qb_t = qb - skb - gb, qb + skb - gb
        pts = [(-FAR, -FAR, z0), (qa_b, -FAR, z0), (qa_b, qb_b, z0), (-FAR, qb_b, z0),
               (-FAR, -FAR, z1), (qa_t, -FAR, z1), (qa_t, qb_t, z1), (-FAR, qb_t, z1)]
        cells.append(dict(kind="quoin", wall="corner", course=i, pts=pts, box=bbox(pts), ext=["-x", "-y"],
                          face_len=(qa, qb)))
        for wall, start, sk0, g0, length in (("A", qa, ska, ga, LA), ("B", qb, skb, gb, LB)):
            joints = []
            pos, skw, gl = start, sk0, g0 * 2
            while length - pos > 1e-6:
                for _ in range(80):
                    L = rng.uniform(*STONE_L)
                    end = pos + L
                    if length - end < STONE_L[0] * 0.7:
                        end = length
                    if end - pos > STONE_L[1] * 1.35:
                        continue
                    if end < length and any(abs(end - pj) < MIN_STAGGER for pj in prev[wall]):
                        continue
                    break
                last = end >= length - 1e-6
                sk2 = 0.0 if last else rng.uniform(-SKEW, SKEW)
                g2 = 0.0 if last else rng.uniform(*JOINT_RANGE)
                d = T if i == len(courses) - 1 else rng.uniform(*STONE_D)
                if wall == "A" and pos < T:  # behind-quoin conflict with first wall-B stone
                    d = min(d, min(qb_b, qb_t) - JOINT_RANGE[1])
                a_b0, a_t0 = pos - skw + gl / 2, pos + skw + gl / 2
                a_b1, a_t1 = end - sk2 - g2 / 2, end + sk2 - g2 / 2
                pts = prism("x" if wall == "A" else "y", a_b0, a_b1, a_t0, a_t1, -FAR, d, z0, z1)
                cells.append(dict(kind="wall", wall=wall, course=i, pts=pts, box=bbox(pts),
                                  ext=["-y"] if wall == "A" else ["-x"], d_target=d))
                if not last:
                    joints.append(end)
                pos, skw, gl = end, sk2, g2
            prev[wall] = joints + [start]
    return courses, cells


# ------------------------------------------------------------- rock fitting
def load_rocks(src):
    with bpy.data.libraries.load(src, link=False) as (data_from, data_to):
        data_to.objects = [n for n in data_from.objects if any(n.endswith(r) for r in ROCKS)]
    rocks = {}
    for ob in data_to.objects:
        key = ob.name.split("_")[-1]
        me = ob.data
        verts = [Vector(v.co) for v in me.vertices]
        c = sum(verts, Vector()) / len(verts)
        tmp = bpy.data.objects.new("tmp_" + key, me)
        bpy.context.scene.collection.objects.link(tmp)
        sub = tmp.modifiers.new("sub", "SUBSURF")
        sub.levels = 1
        sub.render_levels = 1
        dg = bpy.context.evaluated_depsgraph_get()
        hi = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
        hi.name = "hi_" + key
        for v in hi.vertices:
            v.co = v.co - c
        bpy.data.objects.remove(tmp)
        rocks[key] = dict(verts=[v - c for v in verts], polys=[tuple(p.vertices) for p in me.polygons],
                          mesh=me, hi=hi, src_obj=ob.name)
    return rocks


def transform_verts(verts, R, S, t):
    out = []
    for v in verts:
        w = R @ v
        out.append(Vector((w.x * S[0] + t[0], w.y * S[1] + t[1], w.z * S[2] + t[2])))
    return out


def grid(a0, a1, b0, b1, na, nb):
    return [(a0 + (a1 - a0) * (i + 0.5) / na, b0 + (b1 - b0) * (j + 0.5) / nb) for i in range(na) for j in range(nb)]


def inside(bvh, p):
    loc, nrm, idx, dist = bvh.find_nearest(p)
    if loc is None:
        return False
    return (p - loc).dot(nrm) < 0


def evaluate(cell, verts, polys):
    """Score a transformed rock for a cell. Returns (score, metrics) or (None, reason)."""
    x0, x1, y0, y1, z0, z1 = cell["box"]
    bvh = BVHTree.FromPolygons(verts, polys)
    depths, edge = [], []
    faces = []
    if "-y" in cell["ext"]:
        xa = 0.0 if cell["kind"] == "quoin" else x0
        faces.append(("y", xa, x1))
    if "-x" in cell["ext"]:
        ya = 0.0 if cell["kind"] == "quoin" else y0
        faces.append(("x", ya, y1))
    for axis, a0, a1 in faces:
        for (a, zz) in grid(a0, a1, z0, z1, 12, 8):
            if axis == "y":
                o, dvec = Vector((a, -1.0, zz)), Vector((0, 1, 0))
            else:
                o, dvec = Vector((-1.0, a, zz)), Vector((1, 0, 0))
            hit = bvh.ray_cast(o, dvec, 3.0)
            t = (hit[0].y if axis == "y" else hit[0].x) if hit[0] is not None else 9.0
            depths.append(t)
            ua = (a - a0) / (a1 - a0)
            uz = (zz - z0) / (z1 - z0)
            if min(ua, 1 - ua, uz, 1 - uz) < 0.13:
                edge.append(t)
    cov = sum(1 for t in depths if t <= POINT_RECESS) / len(depths)
    cov_e = sum(1 for t in edge if t <= POINT_RECESS) / max(1, len(edge))
    hits = [t for t in depths if t < 1]
    if len(hits) < 0.8 * len(depths):
        return None, "missing_face"
    mean = sum(hits) / len(hits)
    std = math.sqrt(sum((t - mean) ** 2 for t in hits) / len(hits))
    # hidden-face solidity: every hidden cell face (beyond 4 cm from the exterior) must lie inside the rock
    pts = []
    keep = 0.06
    xa = max(x0, keep) if "-x" in cell["ext"] else x0
    ya = max(y0, keep) if "-y" in cell["ext"] else y0
    for (a, b) in grid(xa, x1, ya, y1, 6, 5):
        pts += [Vector((a, b, z0 + 1e-4)), Vector((a, b, z1 - 1e-4))]
    for (a, zz) in grid(xa, x1, z0, z1, 6, 4):
        pts.append(Vector((a, y1 - 1e-4, zz)))
        if "-y" not in cell["ext"]:
            pts.append(Vector((a, y0 + 1e-4, zz)))
    for (b, zz) in grid(ya, y1, z0, z1, 6, 4):
        pts.append(Vector((x1 - 1e-4, b, zz)))
        if "-x" not in cell["ext"]:
            pts.append(Vector((x0 + 1e-4, b, zz)))
    solid = sum(1 for p in pts if inside(bvh, p)) / len(pts)
    m = dict(coverage=round(cov, 3), edge_coverage=round(cov_e, 3), relief_std_m=round(std, 4),
             hidden_solidity=round(solid, 3))
    if solid < 0.97:
        return None, m
    if cov < 0.66 or std > 0.03:
        return None, m
    relief_pen = 0.0 if 0.004 <= std <= 0.018 else min(abs(std - 0.004), abs(std - 0.018)) * 40
    edge_pen = 0.0 if 0.40 <= cov_e <= 0.78 else min(abs(cov_e - 0.40), abs(cov_e - 0.78)) * 2
    score = cov - edge_pen - relief_pen
    return score, m


def window_depths(bvh, axis, a0, a1, z0, z1, n=7):
    out = []
    for (a, zz) in grid(a0, a1, z0, z1, n, 5):
        if axis == "y":
            hit = bvh.ray_cast(Vector((a, -3.0, zz)), Vector((0, 1, 0)), 6.0)
            out.append(hit[0].y if hit[0] is not None else None)
        else:
            hit = bvh.ray_cast(Vector((-3.0, a, zz)), Vector((1, 0, 0)), 6.0)
            out.append(hit[0].x if hit[0] is not None else None)
    return out


def fit_cell(cell, rocks, rng):
    """Quarry the stone from a window of a large scan surface (cover 2.5-5x the cell)."""
    x0, x1, y0, y1, z0, z1 = cell["box"]
    h = z1 - z0
    best = None
    tries = []
    for k in range(N_CAND):
        rk = rng.choice(ROCKS)
        R = Quaternion((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))).normalized().to_matrix()
        rv = [R @ v for v in rocks[rk]["verts"]]
        ext = [max(v[i] for v in rv) - min(v[i] for v in rv) for i in range(3)]
        cover = rng.uniform(2.5, 5.0)
        kd = rng.uniform(0.55, 1.0)
        bulge = rng.uniform(0.006, 0.022)
        if cell["kind"] == "quoin":
            qa, qb = cell["face_len"]
            base = cover * max(qa, qb, h)
            S = [base / ext[0], base / ext[1], base * rng.uniform(0.8, 1.0) / ext[2]]
        elif cell["wall"] == "A":
            base = cover * max(x1 - x0, h)
            S = [base / ext[0], kd * base / ext[1], base * rng.uniform(0.75, 1.0) / ext[2]]
        else:
            base = cover * max(y1 - y0, h)
            S = [kd * base / ext[0], base / ext[1], base * rng.uniform(0.75, 1.0) / ext[2]]
        sv = [Vector((v.x * S[0], v.y * S[1], v.z * S[2])) for v in rv]
        mn = [min(v[i] for v in sv) for i in range(3)]
        mx = [max(v[i] for v in sv) for i in range(3)]
        cen = [(mn[i] + mx[i]) / 2 for i in range(3)]
        half = [(mx[i] - mn[i]) / 2 for i in range(3)]
        # pick a random window on the front side of the boulder
        t = [0.0, 0.0, 0.0]
        t[2] = (z0 + z1) / 2 - cen[2] + rng.uniform(-0.45, 0.45) * max(0.0, half[2] - h)
        if cell["kind"] == "quoin":
            t[0] = -mn[0] - rng.uniform(0.0, 0.25) * half[0]
            t[1] = -mn[1] - rng.uniform(0.0, 0.25) * half[1]
        elif cell["wall"] == "A":
            t[0] = (x0 + x1) / 2 - cen[0] + rng.uniform(-0.45, 0.45) * max(0.0, half[0] - (x1 - x0))
            t[1] = -mn[1]
        else:
            t[1] = (y0 + y1) / 2 - cen[1] + rng.uniform(-0.45, 0.45) * max(0.0, half[1] - (y1 - y0))
            t[0] = -mn[0]
        verts = [v + Vector(t) for v in sv]
        # shift along each exterior normal so the frontmost point inside the window sits at -bulge
        ok = True
        for _ in range(2):
            bvh = BVHTree.FromPolygons(verts, rocks[rk]["polys"])
            shift = Vector()
            if "-y" in cell["ext"]:
                d = window_depths(bvh, "y", max(x0, 0.0), x1, z0, z1)
                if any(v is None for v in d):
                    ok = False
                    break
                shift.y = -bulge - min(d)
            if "-x" in cell["ext"]:
                d = window_depths(bvh, "x", max(y0, 0.0), y1, z0, z1)
                if any(v is None for v in d):
                    ok = False
                    break
                shift.x = -bulge - min(d)
            if shift.length < 1e-5:
                break
            verts = [v + shift for v in verts]
        if not ok:
            tries.append({"reject": "window_miss"})
            continue
        sc, m = evaluate(cell, verts, rocks[rk]["polys"])
        tries.append(m if isinstance(m, dict) else {"reject": m})
        if sc is not None and (best is None or sc > best[0]):
            offset = verts[0] - Vector((rv[0].x * S[0], rv[0].y * S[1], rv[0].z * S[2]))
            best = (sc, dict(rock=rk, R=[list(r) for r in R], S=S, t=list(offset), cover=cover, kd=kd, bulge=bulge,
                             metrics=m), verts)
    if os.environ.get("AIDAN_DEBUG"):
        print("FITDBG", cell["kind"], cell["wall"], tries[:6])
    return best, len(tries)


# ------------------------------------------------------------------ geometry
def box_object(name, box):
    x0, x1, y0, y1, z0, z1 = box
    pts = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    return prism_object(name, pts)


def prism_object(name, pts):
    me = bpy.data.meshes.new(name)
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me.from_pydata([Vector(p) for p in pts], [], faces)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def mesh_from_fit(name, rock, info):
    me = rock["hi"].copy()
    me.name = name
    R = Matrix(info["R"])
    S, t = info["S"], info["t"]
    for v in me.vertices:
        w = R @ v.co
        v.co = Vector((w.x * S[0] + t[0], w.y * S[1] + t[1], w.z * S[2] + t[2]))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def clip_convex(ob, planes):
    """Clip a convex cell mesh by half-spaces (keep side where (p-co).no <= 0) and re-cap."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    for co, no in planes:
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no, clear_outer=True)
        cut_edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        if cut_edges:
            bmesh.ops.contextual_create(bm, geom=cut_edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def face_plane(pts, idx, outward_hint):
    a, b, c = (Vector(pts[i]) for i in idx[:3])
    n = (b - a).cross(c - a).normalized()
    if n.dot(outward_hint) < 0:
        n = -n
    centre = sum((Vector(pts[i]) for i in idx), Vector()) / len(idx)
    return centre, n


def pitch_planes(cell, rng):
    """D-F8-2 fix: mason's pitched arrises. For every exposed front edge (beds, perpends and
    the quoin arris) add a shallow and a steep chamfer plane whose set-back behind the face
    plane, angle and yaw vary per edge, so the proud scan surface rolls into the joint
    instead of ending on a flat sawn shelf. Planes only remove material in front of the
    mortar recess; beds/perpends behind it stay exact and shared."""
    planes = []
    x0, x1, y0, y1, z0, z1 = cell["box"]
    pts = cell["pts"]
    quoin = cell["kind"] == "quoin"
    for ext in cell["ext"]:
        o = Vector((0, -1, 0)) if ext == "-y" else Vector((-1, 0, 0))
        t = Vector((1, 0, 0)) if ext == "-y" else Vector((0, 1, 0))
        mid = Vector(((x0 + x1) / 2 if ext == "-y" else 0.0, (y0 + y1) / 2 if ext == "-x" else 0.0, 0.0))
        edges = [(Vector((0, 0, 1)), Vector((0, 0, z1))), (Vector((0, 0, -1)), Vector((0, 0, z0)))]
        if quoin:
            end_idx = [(1, 2, 6, 5)] if ext == "-y" else [(2, 3, 7, 6)]
        else:
            end_idx = [(1, 2, 6, 5), (0, 3, 7, 4)]
        for k, idx in enumerate(end_idx):
            hint = t if k == 0 else -t
            centre, ne = face_plane(pts, idx, hint)
            edges.append((ne, centre))
        for u, anchor in edges:
            for phi_rng, c_rng in (((24, 40), (0.006, 0.016)), ((55, 70), (0.000, 0.008))):
                phi = math.radians(rng.uniform(*phi_rng))
                c = rng.uniform(*c_rng)
                n = (o * math.cos(phi) + u * math.sin(phi)).normalized()
                n = Matrix.Rotation(math.radians(rng.uniform(-4, 4)), 3, u) @ n
                if abs(u.z) > 0.9:   # bed edge: anchor on the bed plane, centred along the face
                    P = Vector((mid.x, mid.y, anchor.z))
                else:                # perpend edge: anchor on the (slanted) end face
                    P = Vector(anchor)
                    P = P - o * P.dot(o)            # move anchor onto the face plane (o-coordinate 0)
                P = P - o * c                        # set back c behind the face plane
                planes.append((P, n))
    if quoin:  # vertical arris between the two exterior faces
        phi = math.radians(rng.uniform(35, 55))
        n = Vector((-math.cos(phi), -math.sin(phi), 0.0))
        c = rng.uniform(0.0, 0.012)
        planes.append((n * (-c), n))
    return planes


def apply_boolean(ob, operand, op, collection=None):
    mod = ob.modifiers.new("bool", "BOOLEAN")
    mod.operation = op
    mod.solver = "EXACT"
    if collection is not None:
        mod.operand_type = "COLLECTION"
        mod.collection = collection
    else:
        mod.object = operand
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)


def topology(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.edges.ensure_lookup_table()
    boundary = sum(1 for e in bm.edges if e.is_boundary)
    nonman = sum(1 for e in bm.edges if not e.is_manifold)
    degenerate = sum(1 for f in bm.faces if f.calc_area() < 1e-10)
    vol = bm.calc_volume(signed=True)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    tris = len(bm.faces)
    comps = 0
    seen = set()
    for f in bm.faces:
        if f.index in seen:
            continue
        comps += 1
        stack = [f]
        seen.add(f.index)
        while stack:
            c = stack.pop()
            for e in c.edges:
                for lf in e.link_faces:
                    if lf.index not in seen:
                        seen.add(lf.index)
                        stack.append(lf)
    bm.free()
    return dict(boundary_edges=boundary, nonmanifold_edges=nonman, degenerate_faces=degenerate,
                signed_volume_m3=round(vol, 6), triangles=tris, components=comps)


def plane_area(ob, axis, value, tol=5e-5, outward=None):
    total = 0.0
    for p in ob.data.polygons:
        if all(abs(ob.data.vertices[v].co[axis] - value) < tol for v in p.vertices):
            total += p.area
    return total


# ---------------------------------------------------------------- materials
def img(tex, name, colorspace):
    im = bpy.data.images.load(os.path.abspath(os.path.join(tex, name)), check_existing=True)
    im.colorspace_settings.name = colorspace
    return im


def stone_material(tex):
    m = bpy.data.materials.new("M_stone_scan_limestone")
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    bsdf = N.new("ShaderNodeBsdfPrincipled")
    L.new(bsdf.outputs[0], out.inputs[0])
    tc = N.new("ShaderNodeTexCoord")
    oi = N.new("ShaderNodeObjectInfo")
    rnd3 = N.new("ShaderNodeCombineXYZ")
    mul = [N.new("ShaderNodeMath") for _ in range(3)]
    for i, mm in enumerate(mul):
        mm.operation = "MULTIPLY"
        mm.inputs[1].default_value = 37.0 * (i + 1)
        L.new(oi.outputs["Random"], mm.inputs[0])
        L.new(mm.outputs[0], rnd3.inputs[i])
    scale = N.new("ShaderNodeVectorMath")
    scale.operation = "SCALE"
    scale.inputs[3].default_value = 1.15  # 2k map covers ~0.87 m
    L.new(tc.outputs["Object"], scale.inputs[0])
    add = N.new("ShaderNodeVectorMath")
    add.operation = "ADD"
    L.new(scale.outputs[0], add.inputs[0])
    L.new(rnd3.outputs[0], add.inputs[1])

    def tex_node(fname, cs):
        t = N.new("ShaderNodeTexImage")
        t.image = img(tex, fname, cs)
        t.projection = "BOX"
        t.projection_blend = 0.25
        L.new(add.outputs[0], t.inputs[0])
        return t

    diff = tex_node("rock_boulder_dry_diff_2k.jpg", "sRGB")
    rough = tex_node("rock_boulder_dry_rough_2k.jpg", "Non-Color")
    disp = tex_node("rock_boulder_dry_disp_2k.jpg", "Non-Color")
    # per-stone tint (grey / warm beige / ochre limestone variation seen in V11)
    ramp = N.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.interpolation = "CONSTANT"
    cr.elements[0].color = (0.50, 0.50, 0.48, 1)
    cr.elements[1].color = (0.90, 0.78, 0.60, 1)
    for pos, col in ((0.18, (0.66, 0.65, 0.62, 1)), (0.40, (0.80, 0.76, 0.68, 1)), (0.62, (0.72, 0.70, 0.66, 1)),
                     (0.80, (0.84, 0.72, 0.55, 1)), (0.93, (0.58, 0.56, 0.52, 1))):
        e = cr.elements.new(pos)
        e.color = col
    L.new(oi.outputs["Random"], ramp.inputs[0])
    tint = N.new("ShaderNodeMix")
    tint.data_type = "RGBA"
    tint.blend_type = "MULTIPLY"
    tint.inputs[0].default_value = 1.0
    L.new(diff.outputs[0], tint.inputs[6])
    L.new(ramp.outputs[0], tint.inputs[7])
    # crevice darkening (AO) — dirt in pits and along mortar
    ao = N.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.05
    aor = N.new("ShaderNodeMapRange")
    aor.inputs[1].default_value = 0.0
    aor.inputs[2].default_value = 1.0
    aor.inputs[3].default_value = 0.45
    aor.inputs[4].default_value = 1.0
    L.new(ao.outputs["AO"], aor.inputs[0])
    dirt = N.new("ShaderNodeMix")
    dirt.data_type = "RGBA"
    dirt.blend_type = "MULTIPLY"
    dirt.inputs[0].default_value = 1.0
    L.new(tint.outputs[2], dirt.inputs[6])
    L.new(aor.outputs[0], dirt.inputs[7])
    # moss mask: low on the wall, upward-facing, crevices, broken by noise
    geo = N.new("ShaderNodeNewGeometry")
    sep_p = N.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Position"], sep_p.inputs[0])
    low = N.new("ShaderNodeMapRange")
    low.inputs[1].default_value = 0.0
    low.inputs[2].default_value = 0.55
    low.inputs[3].default_value = 1.0
    low.inputs[4].default_value = 0.0
    L.new(sep_p.outputs[2], low.inputs[0])
    sep_n = N.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Normal"], sep_n.inputs[0])
    up = N.new("ShaderNodeMapRange")
    up.inputs[1].default_value = -0.2
    up.inputs[2].default_value = 0.8
    up.inputs[3].default_value = 0.75
    up.inputs[4].default_value = 0.95
    L.new(sep_n.outputs[2], up.inputs[0])
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 5.5
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.65
    L.new(tc.outputs["Object"], noise.inputs[0])
    m1 = N.new("ShaderNodeMath")
    m1.operation = "MULTIPLY"
    L.new(low.outputs[0], m1.inputs[0])
    L.new(up.outputs[0], m1.inputs[1])
    crev = N.new("ShaderNodeMapRange")  # 1 - AO -> 0.6..1.4
    crev.inputs[1].default_value = 1.0
    crev.inputs[2].default_value = 0.0
    crev.inputs[3].default_value = 0.6
    crev.inputs[4].default_value = 1.4
    L.new(ao.outputs["AO"], crev.inputs[0])
    m2 = N.new("ShaderNodeMath")
    m2.operation = "MULTIPLY"
    L.new(m1.outputs[0], m2.inputs[0])
    L.new(crev.outputs[0], m2.inputs[1])
    m3 = N.new("ShaderNodeMath")
    m3.operation = "MULTIPLY"
    L.new(m2.outputs[0], m3.inputs[0])
    L.new(noise.outputs["Fac"], m3.inputs[1])
    moss_k = N.new("ShaderNodeMapRange")
    moss_k.inputs[1].default_value = 0.25
    moss_k.inputs[2].default_value = 0.36
    L.new(m3.outputs[0], moss_k.inputs[0])
    moss_col = N.new("ShaderNodeMix")
    moss_col.data_type = "RGBA"
    moss_col.inputs[6].default_value = (0.045, 0.07, 0.02, 1)
    moss_col.inputs[7].default_value = (0.12, 0.15, 0.04, 1)
    L.new(noise.outputs["Fac"], moss_col.inputs[0])
    # lichen: sparse irregular crust blotches (multi-octave noise threshold, no cellular dots)
    n2 = N.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = 14.0
    n2.inputs["Detail"].default_value = 14.0
    n2.inputs["Roughness"].default_value = 0.72
    n2.inputs["Distortion"].default_value = 0.6
    L.new(add.outputs[0], n2.inputs[0])
    lich_k = N.new("ShaderNodeMapRange")
    lich_k.inputs[1].default_value = 0.64
    lich_k.inputs[2].default_value = 0.70
    lich_k.inputs[4].default_value = 0.65
    L.new(n2.outputs["Fac"], lich_k.inputs[0])
    lich_col = N.new("ShaderNodeMix")
    lich_col.data_type = "RGBA"
    lich_col.inputs[6].default_value = (0.58, 0.60, 0.50, 1)
    lich_col.inputs[7].default_value = (0.62, 0.48, 0.18, 1)
    L.new(oi.outputs["Random"], lich_col.inputs[0])
    lich_mix = N.new("ShaderNodeMix")
    lich_mix.data_type = "RGBA"
    L.new(lich_k.outputs[0], lich_mix.inputs[0])
    L.new(dirt.outputs[2], lich_mix.inputs[6])
    L.new(lich_col.outputs[2], lich_mix.inputs[7])
    final = N.new("ShaderNodeMix")
    final.data_type = "RGBA"
    L.new(moss_k.outputs[0], final.inputs[0])
    L.new(lich_mix.outputs[2], final.inputs[6])
    L.new(moss_col.outputs[2], final.inputs[7])
    hsv = N.new("ShaderNodeHueSaturation")
    hsv.inputs["Saturation"].default_value = 0.78
    L.new(final.outputs[2], hsv.inputs["Color"])
    L.new(hsv.outputs[0], bsdf.inputs["Base Color"])
    rmix = N.new("ShaderNodeMix")
    L.new(moss_k.outputs[0], rmix.inputs[0])
    L.new(rough.outputs[0], rmix.inputs[2])
    rmix.inputs[3].default_value = 0.95
    L.new(rmix.outputs[0], bsdf.inputs["Roughness"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.9
    bump.inputs["Distance"].default_value = 0.006
    L.new(disp.outputs[0], bump.inputs["Height"])
    L.new(bump.outputs[0], bsdf.inputs["Normal"])
    return m


def mortar_material():
    m = bpy.data.materials.new("M_lime_mortar_authored")
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    bsdf = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    n = N.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 60.0
    n.inputs["Detail"].default_value = 10.0
    L.new(tc.outputs["Object"], n.inputs[0])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.13, 0.12, 0.10, 1)
    ramp.color_ramp.elements[1].color = (0.30, 0.28, 0.24, 1)
    L.new(n.outputs["Fac"], ramp.inputs[0])
    ao = N.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.04
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 1.0
    L.new(ramp.outputs[0], mix.inputs[6])
    L.new(ao.outputs["AO"], mix.inputs[7])
    L.new(mix.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.97
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.6
    bump.inputs["Distance"].default_value = 0.003
    L.new(n.outputs["Fac"], bump.inputs["Height"])
    L.new(bump.outputs[0], bsdf.inputs["Normal"])
    return m


def wood_material(tex):
    m = bpy.data.materials.new("M_oak_wallplate_rough_wood")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    bsdf = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.9, 0.9, 2.2)
    L.new(tc.outputs["Object"], mp.inputs[0])
    ims = {}
    for key, cs in (("diff", "sRGB"), ("rough", "Non-Color"), ("disp", "Non-Color")):
        t = N.new("ShaderNodeTexImage")
        t.image = img(tex, "rough_wood_%s_2k.jpg" % key, cs)
        t.projection = "BOX"
        t.projection_blend = 0.2
        L.new(mp.outputs[0], t.inputs[0])
        ims[key] = t
    warm = N.new("ShaderNodeMix")
    warm.data_type = "RGBA"
    warm.blend_type = "MULTIPLY"
    warm.inputs[0].default_value = 1.0
    warm.inputs[7].default_value = (0.60, 0.50, 0.41, 1)
    L.new(ims["diff"].outputs[0], warm.inputs[6])
    L.new(warm.outputs[2], bsdf.inputs["Base Color"])
    L.new(ims["rough"].outputs[0], bsdf.inputs["Roughness"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.8
    bump.inputs["Distance"].default_value = 0.004
    L.new(ims["disp"].outputs[0], bump.inputs["Height"])
    L.new(bump.outputs[0], bsdf.inputs["Normal"])
    return m


def wall_plate(H, tex):
    """Oak wall plate on the wall top (V11: timber over stone). Context prop, not stone geometry."""
    a = box_object("oak_wallplate", (0.03, LA, 0.03, T, H, H + 0.17))
    b = box_object("oak_wallplate_b", (0.03, T, 0.03, LB, H, H + 0.17))
    apply_boolean(a, b, "UNION")
    bpy.data.objects.remove(b)
    bev = a.modifiers.new("bevel", "BEVEL")
    bev.width = 0.012
    bev.segments = 2
    a.data.materials.append(wood_material(tex))
    return a


# -------------------------------------------------------------------- scene
def setup_render(args):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = args.samples
    sc.cycles.use_denoising = True
    sc.cycles.seed = args.seed
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = -0.55
    world = bpy.data.worlds.new("W")
    sc.world = world
    world.use_nodes = True
    sky = world.node_tree.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    sky.sun_elevation = math.radians(32)
    sky.sun_rotation = math.radians(215)
    sky.sun_intensity = 0.25
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Strength"].default_value = 0.35
    world.node_tree.links.new(sky.outputs[0], bg.inputs[0])
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 3.4
    sun.angle = math.radians(1.5)
    sun.color = (1.0, 0.86, 0.68)
    so = bpy.data.objects.new("Sun", sun)
    to_sun = Vector((-0.80, -0.42, 0.52)).normalized()  # low raking light from camera-left (V11 afternoon key)
    so.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()
    sc.collection.objects.link(so)
    # ground = shadow catcher (keeps RGBA sprite-ready output, still grounds the wall)
    g = box_object("ground_shadow_catcher", (-2.5, 3.5, -2.5, 3.5, -0.02, 0.0))
    g.is_shadow_catcher = True


def camera(name, loc, target, lens=50):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    ob = bpy.data.objects.new(name, cam)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return ob


# --------------------------------------------------------------------- main
def lookdev(args):
    blend = os.path.join(args.out, "aidan_scan_carved_corner_v1.blend")
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
    mpath = os.path.join(args.out, "aidan_scan_carved_corner_v1_manifest.json")
    manifest = json.load(open(mpath))
    smat, mmat = stone_material(args.tex), mortar_material()
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        if ob.name.startswith("stone_"):
            ob.data.materials.clear()
            ob.data.materials.append(smat)
        elif ob.name == "mortar_matrix":
            ob.data.materials.clear()
            ob.data.materials.append(mmat)
    render_all(args, manifest, manifest["params"]["H"])
    with open(mpath, "w") as f:
        json.dump(manifest, f, indent=1)


def render_all(args, manifest, H):
    plate = wall_plate(H, args.tex)
    manifest["context_props"] = dict(oak_wallplate=dict(texture="rough_wood 2k (Poly Haven, CC0)",
                                                      url="https://polyhaven.com/a/rough_wood",
                                                      files={f: sha256(os.path.join(args.tex, f)) for f in
                                                             sorted(os.listdir(args.tex)) if f.startswith("rough_wood_")}))
    setup_render(args)
    sc = bpy.context.scene
    views = {
        "three_quarter": ((-3.1, -3.0, 2.35), (0.42, 0.40, 0.72), 50),
        "front_A": ((0.80, -4.1, 1.10), (0.80, 0.0, 0.85), 50),
        "top_oblique": ((-1.55, -1.5, 3.6), (0.45, 0.45, 0.6), 40),
    }
    renders = {}
    for vname, (loc, tgt, lens) in views.items():
        cam = camera("CAM_" + vname, loc, tgt, lens)
        sc.camera = cam
        sc.render.resolution_x = args.res
        sc.render.resolution_y = int(args.res * 0.75)
        p = os.path.join(args.out, "corner_%s.png" % vname)
        sc.render.filepath = os.path.abspath(p)
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        renders[vname] = dict(file=os.path.basename(p), seconds=round(time.time() - t0, 1), sha256=sha256(p))
    cam = camera("CAM_game", (-3.3, -3.2, 2.15), (0.42, 0.42, 0.8), 55)
    sc.camera = cam
    sc.render.resolution_x = sc.render.resolution_y = 768
    p = os.path.join(args.out, "corner_game_src_768.png")
    sc.render.filepath = os.path.abspath(p)
    bpy.ops.render.render(write_still=True)
    renders["game_src"] = dict(file=os.path.basename(p), sha256=sha256(p))
    manifest["renders"] = renders
    manifest["render_settings"] = dict(engine="CYCLES CPU", samples=args.samples, denoise="OpenImageDenoise",
                                       view="AgX Medium High Contrast", exposure=sc.view_settings.exposure)


def main():
    args = parse()
    t_start = time.time()
    os.makedirs(args.out, exist_ok=True)
    if args.reuse:
        return lookdev(args)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rng = random.Random(args.seed)
    src_sha = sha256(args.src)
    tex_files = sorted(f for f in os.listdir(args.tex) if f.startswith("rock_boulder_dry_"))
    tex_sha = {f: sha256(os.path.join(args.tex, f)) for f in tex_files}
    rocks = load_rocks(args.src)
    courses, cells = solve_layout(rng)

    stones_col = bpy.data.collections.new("stones")
    bpy.context.scene.collection.children.link(stones_col)
    cells_col = bpy.data.collections.new("cells_operand")
    bpy.context.scene.collection.children.link(cells_col)
    smat = stone_material(args.tex)
    mmat = mortar_material()
    records = []
    for i, cell in enumerate(cells):
        name = "stone_%02d_%s_c%d" % (i, cell["wall"], cell["course"])
        fits = []
        ntry = 0
        if cell["kind"] == "quoin":
            x0, x1, y0, y1, z0, z1 = cell["box"]
            x1 = min(p[0] for p in cell["pts"] if p[0] > 0)
            y1 = min(p[1] for p in cell["pts"] if p[1] > 0)
            pa = dict(kind="wall", wall="A", course=cell["course"], box=(0.0, x1, -FAR, y1, z0, z1), ext=["-y"], d_target=y1)
            pb = dict(kind="wall", wall="B", course=cell["course"], box=(-FAR, x1, 0.0, y1, z0, z1), ext=["-x"], d_target=x1)
            for pc in (pa, pb):
                for _round in range(5):
                    b, n = fit_cell(pc, rocks, rng)
                    ntry += n
                    if b is not None:
                        break
                fits.append(b)
        else:
            b, ntry = fit_cell(cell, rocks, rng)
            for _round in range(4):
                if b is not None:
                    break
                b, n2 = fit_cell(cell, rocks, rng)
                ntry += n2
            fits.append(b)
        if any(f is None for f in fits):
            records.append(dict(name=name, status="UNFILLED", cell=cell["box"]))
            continue
        cpts = [(max(p[0], -FRONT_CAP), max(p[1], -FRONT_CAP), p[2]) for p in cell["pts"]]
        cut = prism_object(name + "_cell", cpts)
        clip_convex(cut, pitch_planes(cell, rng))
        rock_ob = None
        for f in fits:
            ob = mesh_from_fit(name if rock_ob is None else name + "_b", rocks[f[1]["rock"]], f[1])
            if rock_ob is None:
                rock_ob = ob
                apply_boolean(rock_ob, cut, "INTERSECT")
            else:
                apply_boolean(rock_ob, ob, "INTERSECT")
                bpy.data.objects.remove(ob)
        bpy.data.objects.remove(cut)
        info = fits[0][1]
        rock_ob.data.materials.clear()
        rock_ob.data.materials.append(smat)
        for c in rock_ob.users_collection:
            c.objects.unlink(rock_ob)
        stones_col.objects.link(rock_ob)
        # operand for mortar subtraction (cell boxes)
        cb = prism_object(name + "_mcell", cell["pts"])
        for c in cb.users_collection:
            c.objects.unlink(cb)
        cells_col.objects.link(cb)
        records.append(dict(name=name, kind=cell["kind"], wall=cell["wall"], course=cell["course"],
                            cell=list(cell["box"]), pts=[list(p) for p in cell["pts"]], exterior=cell["ext"],
                            candidates=ntry,
                            source_rocks=[rocks[f[1]["rock"]]["src_obj"] for f in fits],
                            cover=[round(f[1]["cover"], 3) for f in fits],
                            relief_k=[round(f[1]["kd"], 3) for f in fits],
                            bulge_m=[round(f[1]["bulge"], 4) for f in fits],
                            fit=[f[1]["metrics"] for f in fits]))
    # mortar matrix
    H = courses[-1][1]
    env = box_object("mortar_matrix", (POINT_RECESS, LA, POINT_RECESS, T, 0.0, H))
    env2 = box_object("mortar_env_b", (POINT_RECESS, T, POINT_RECESS, LB, 0.0, H))
    apply_boolean(env, env2, "UNION")
    bpy.data.objects.remove(env2)
    cells_col.hide_render = True
    apply_boolean(env, None, "DIFFERENCE", collection=cells_col)
    env.data.materials.append(mmat)
    for ob in list(cells_col.objects):
        bpy.data.objects.remove(ob)
    bpy.data.collections.remove(cells_col)
    for ob in list(bpy.data.objects):
        if ob.name.startswith("rock_moss_set_01"):
            bpy.data.objects.remove(ob)
    for ob in stones_col.objects:
        ob.data.polygons.foreach_set("use_smooth", [True] * len(ob.data.polygons))

    # ------------------------------------------------------------ technical QA
    stones = list(stones_col.objects)
    qa = dict(stones=[], pairs_bvh_overlap=0, mortar=None)
    bvhs = {}
    for ob in stones:
        topo = topology(ob)
        rec = next(r for r in records if r["name"] == ob.name)
        x0, x1, y0, y1, z0, z1 = rec["cell"]
        xs = [v.co.x for v in ob.data.vertices]
        ys = [v.co.y for v in ob.data.vertices]
        zs = [v.co.z for v in ob.data.vertices]
        eps = 2e-4
        cobj = prism_object("_qa_cell", rec["pts"])
        cb = bmesh.new()
        cb.from_mesh(cobj.data)
        planes = [(f.calc_center_median().copy(), f.normal.copy()) for f in cb.faces]
        cb.free()
        bpy.data.objects.remove(cobj)
        in_cell = all(all((v.co - c).dot(n) <= eps for c, n in planes) for v in ob.data.vertices)
        bot = [p for p in rec["pts"] if abs(p[2] - z0) < 1e-9]
        xb0, xb1 = max(min(p[0] for p in bot), 0.0), max(p[0] for p in bot)
        yb0, yb1 = max(min(p[1] for p in bot), 0.0), max(p[1] for p in bot)
        foot = (xb1 - xb0) * (yb1 - yb0)
        bed = plane_area(ob, 2, z0)
        top = plane_area(ob, 2, z1)
        protrusion = -min(min(ys) if "-y" in rec["exterior"] else 0, min(xs) if "-x" in rec["exterior"] else 0)
        rec["qa"] = dict(topo, inside_cell=in_cell, bed_area_m2=round(bed, 5), top_area_m2=round(top, 5),
                         bed_support_ratio=round(bed / foot, 3) if foot > 0 else None,
                         max_protrusion_m=round(protrusion, 4))
        bvhs[ob.name] = BVHTree.FromObject(ob, bpy.context.evaluated_depsgraph_get())
    names = list(bvhs)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            if bvhs[names[i]].overlap(bvhs[names[j]]):
                qa["pairs_bvh_overlap"] += 1
    mt = topology(env)
    mb = BVHTree.FromObject(env, bpy.context.evaluated_depsgraph_get())
    mortar_overlaps = sum(1 for n in names if mb.overlap(bvhs[n]))
    qa["mortar"] = dict(mt, stone_triangle_contacts=mortar_overlaps,
                        note="coplanar touching faces register as BVH triangle contacts; interpenetration is "
                             "excluded by construction (stone subset of cell, mortar = envelope minus cells)")
    # visible-void test: rays through both exterior faces must hit stone or mortar before passing the wall
    allb = stones + [env]
    trees = [bvhs[o.name] for o in stones] + [mb]
    holes, rays = 0, 0
    miss_pts = []
    for face, length in (("y", LA), ("x", LB)):
        for k in range(160):
            a = 0.005 + (length - 0.01) * (k + 0.5) / 160
            for m in range(120):
                zz = 0.005 + (H - 0.01) * (m + 0.5) / 120
                if face == "y":
                    o, d = Vector((a, -0.5, zz)), Vector((0, 1, 0))
                else:
                    o, d = Vector((-0.5, a, zz)), Vector((1, 0, 0))
                rays += 1
                hit = any(t.ray_cast(o, d, 0.5 + T - 0.02)[0] is not None for t in trees)
                if not hit:
                    holes += 1
                    miss_pts.append([face, round(a, 4), round(zz, 4)])
    band = POINT_RECESS + 0.005  # rays this close to the arris run parallel to the other face inside its pointing recess
    through = [q for q in miss_pts if q[1] > band]
    qa["see_through_rays"] = dict(rays=rays, misses=holes, through_wall_misses=len(through),
                                  arris_grazing_misses=holes - len(through), arris_band_m=band,
                                  miss_points=miss_pts[:400])
    unfilled = [r for r in records if r.get("status") == "UNFILLED"]
    st_ok = all(r["qa"]["boundary_edges"] == 0 and r["qa"]["nonmanifold_edges"] == 0 and r["qa"]["inside_cell"]
                and r["qa"]["signed_volume_m3"] > 0 and r["qa"]["components"] == 1
                for r in records if "qa" in r)
    support = [r["qa"]["bed_support_ratio"] for r in records if "qa" in r]
    max_prot = max(r["qa"]["max_protrusion_m"] for r in records if "qa" in r)
    qa["summary"] = dict(max_protrusion_m=max_prot, stone_count=len(stones), unfilled=len(unfilled), stones_watertight_single_component=st_ok,
                         min_bed_support_ratio=min(support), mean_bed_support_ratio=round(sum(support) / len(support), 3),
                         stone_stone_bvh_overlaps=qa["pairs_bvh_overlap"],
                         mortar_watertight=mt["boundary_edges"] == 0 and mt["nonmanifold_edges"] == 0,
                         see_through_misses=holes, through_wall_misses=len(through),
                         total_triangles=sum(r["qa"]["triangles"] for r in records if "qa" in r) + mt["triangles"])
    qa["pass"] = bool(st_ok and not unfilled and qa["pairs_bvh_overlap"] == 0 and len(through) == 0
                      and qa["summary"]["mortar_watertight"] and min(support) >= 0.5)

    manifest = dict(task="AIDAN-MASONRY-ART-02", method_family="F8 scan-carved coursed rubble",
                    canonical=False, blender=bpy.app.version_string, seed=args.seed,
                    params=dict(LA=LA, LB=LB, T=T, H=H, joint_range=JOINT_RANGE, skew=SKEW, point_recess=POINT_RECESS,
                                course_h=COURSE_H, stone_l=STONE_L, quoin_long=QUOIN_LONG,
                                quoin_short=QUOIN_SHORT, stone_d=STONE_D, n_candidates=N_CAND),
                    sources=dict(scan=dict(file=os.path.basename(args.src), sha256=src_sha,
                                           url="https://polyhaven.com/a/rock_moss_set_01", license="CC0 1.0",
                                           used="geometry only (rock01/02/03/05/06); scan textures NOT used"),
                                 texture=dict(asset="rock_boulder_dry 2k", url="https://polyhaven.com/a/rock_boulder_dry",
                                              license="CC0 1.0", files=tex_sha,
                                              used="diffuse/roughness/displacement via box projection; "
                                                   "normal and AO maps downloaded but not wired")),
                    courses=[[round(a, 4), round(b, 4)] for a, b in courses], stones=records, qa=qa)
    blend_path = os.path.join(args.out, "aidan_scan_carved_corner_v1.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path, compress=True)
    try:
        for o in bpy.context.selected_objects:
            o.select_set(False)
        for o in stones + [env]:
            o.select_set(True)
        bpy.ops.export_scene.gltf(filepath=os.path.join(args.out, "aidan_scan_carved_corner_v1.glb"),
                                  use_selection=True, export_apply=True, export_materials="NONE")
    except Exception as e:  # recorded, not masked
        manifest["glb_export_error"] = repr(e)

    if not args.no_render:
        render_all(args, manifest, H)
    manifest["seconds_total"] = round(time.time() - t_start, 1)
    with open(os.path.join(args.out, "aidan_scan_carved_corner_v1_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    print("QA_PASS", qa["pass"], json.dumps(qa["summary"]))


main()

"""MORWEN-EYES-LIDS-MOUTH-04: build ONE candidate on top of the locked #312 nose (depth 0.5).

In-memory only; the pinned VRM is never written. Steps (deterministic):
  0. Rebuild #312 nose, assert its Face geometry hash, set MORWEN_DESIGN_NoseDepth = 0.5.
  1. Eyelids (R, L): annulus local retopology between the rim junction loop (skin vertices
     coincident with EyeWhite) and a notch-free outer loop; 3 concentric loops with the rim's
     vertex count (quads), zipper to the outer loop. New vertices are shrink-wrapped onto the
     ORIGINAL skin (closest point of the 3D rim->outer interpolation, so rings follow the lid/lip
     roll; shape unchanged); UV, weights and every shape key transferred barycentrically.
  2. Mouth: same annulus construction around the lip seam (skin/FaceMouth junction), 4 loops.
  3. Eyes: old EyeWhite/EyeIris/EyeHighlight plates removed from Face; a new independent eye
     surface per side (spherical cap behind the rim, polar topology) with a procedural violet
     material (no texture stretching). Iris width and in-opening position from Layer 0
     measurements, per side. Rigged to J_Adj_{L,R}_FaceEye.
  4. Cards (eyeline, eyelash): per state, opaque texels behind the skin are lifted along the
     skin normal (least-norm per triangle), keeping each key's own card motion.
  5. Custom normals: untouched corners restored; patch corners automatic.
Patch membership is stored in the integer vertex attribute `elm_patch`
(1 lid R, 2 lid L, 3 mouth, 4 nose) for QA.
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
MP = HERE.parent


def _load(path, name):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


NB = _load(MP / "nose_retopo" / "build_nose_retopo_03.py", "morwen_nose_build")
M3 = NB.M3
X = _load(HERE / "measure_eye_mouth_intersections_04.py", "morwen_elm_ix")
PARAMS_PATH = Path(os.environ.get("MORWEN_ELM_PARAMS", HERE / "elm_params_04.json"))
PATCH_ATTR = "elm_patch"


def pkey(co):
    return tuple(round(c * 1e6) for c in co)


def face_hash(me):
    h = hashlib.sha256()
    for kb in me.shape_keys.key_blocks:
        h.update(kb.name.encode())
        h.update(np.round(np.array([v.co[:] for v in kb.data]), 7).astype(np.float64).tobytes())
    h.update(np.array([v for p in me.polygons for v in p.vertices], dtype=np.int32).tobytes())
    h.update(np.round(np.array([lp.uv[:] for lp in me.uv_layers.active.data]), 7).tobytes())
    return h.hexdigest()


class Transfer:
    """Projection onto the CURRENT skin (front ray, nearest fallback) with attribute interpolation."""

    def __init__(self, face, si):
        me = face.data
        me.calc_loop_triangles()
        self.mw = face.matrix_world
        self.co = [self.mw @ v.co for v in me.vertices]
        self.tris = [t for t in me.loop_triangles if t.material_index == si]
        self.bvh = BVHTree.FromPolygons(self.co, [t.vertices[:] for t in self.tris])
        self.uv = me.uv_layers.active
        keys = me.shape_keys.key_blocks
        base = np.array([v.co[:] for v in keys[0].data])
        self.off = {kb.name: np.array([v.co[:] for v in kb.data]) - base for kb in keys[1:]}
        groups = {g.index: g.name for g in face.vertex_groups}
        self.w = [{groups[g.group]: g.weight for g in v.groups} for v in me.vertices]

    def project(self, x, z, near=None):
        """Front ray onto the skin; with `near` (3D point) use the closest skin point instead."""
        if near is not None:
            hit, _, idx, _ = self.bvh.find_nearest(near)
        else:
            hit, _, idx, _ = self.bvh.ray_cast(Vector((x, 1.0, z)), Vector((0, -1, 0)))
            if hit is None:
                hit, _, idx, _ = self.bvh.find_nearest(Vector((x, 0.2, z)))
        t = self.tris[idx]
        vs = t.vertices[:]
        b = barycentric_transform(hit, *(self.co[i] for i in vs), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)))
        b = np.array([b.x, b.y, b.z])
        uv = sum((Vector(self.uv.data[li].uv) * b[k] for k, li in enumerate(t.loops)), Vector((0, 0)))
        wt = {}
        for k, i in enumerate(vs):
            for g, val in self.w[i].items():
                wt[g] = wt.get(g, 0.0) + val * b[k]
        offs = {name: (o[list(vs)] * b[:, None]).sum(0) for name, o in self.off.items()}
        return hit, uv, wt, offs


def boundary_loops(me, region):
    count = {}
    for i in region:
        for ek in me.polygons[i].edge_keys:
            count[ek] = count.get(ek, 0) + 1
    adj = {}
    for (a, b), c in count.items():
        if c == 1:
            adj.setdefault(a, []).append(b)
            adj.setdefault(b, []).append(a)
    assert all(len(v) == 2 for v in adj.values()), "region boundary is not a set of simple loops"
    loops, seen = [], set()
    for s in sorted(adj):
        if s in seen:
            continue
        loop, prev = [s], None
        seen.add(s)
        while True:
            cur = loop[-1]
            nxt = adj[cur][0] if adj[cur][0] != prev else adj[cur][1]
            if nxt == s:
                break
            prev = cur
            loop.append(nxt)
            seen.add(nxt)
        loops.append(loop)
    return loops


class Ellipse:
    def __init__(self, cx, cz, ax, up, down):
        self.cx, self.cz, self.ax, self.up, self.down = cx, cz, ax, up, down

    def rho_theta(self, x, z):
        dz = z - self.cz
        u = (x - self.cx) / self.ax
        v = dz / (self.up if dz > 0 else self.down)
        return math.hypot(u, v), math.atan2(v, u)


def rim_notches(co, outer, inner, notch):
    """Outer-loop vertices nearer to the rim than `notch` x the mean of their two neighbours
    (distance to the nearest rim vertex in the x/z plane); such dents make the last ring cross."""
    rim = [Vector((co[v].x, co[v].z)) for v in inner]
    d = [min((Vector((co[v].x, co[v].z)) - r).length for r in rim) for v in outer]
    n = len(outer)
    return {outer[i] for i in range(n) if d[i] < notch * 0.5 * (d[i - 1] + d[(i + 1) % n])}


def buffered(me, exclude, rings=1):
    """Excluded vertices plus `rings` one-rings around them: a band of untouched original faces
    stays between a new patch and any locked patch (e.g. the #312 nose)."""
    out = set(exclude)
    for _ in range(rings):
        add = set()
        for p in me.polygons:
            if out & set(p.vertices):
                add |= set(p.vertices)
        out |= add
    return out


def select_annulus(face, si, junction, ell, exclude, notch, membership="all_vertices"):
    """Skin faces inside the ellipse (not touching other patches). The OUTER loop must be
    angularly monotonic around the ellipse centre (star-shaped) and free of dents toward the rim
    (rim_notches); offending vertices' faces are absorbed."""
    me = face.data
    co = [face.matrix_world @ v.co for v in me.vertices]
    region = set()
    for p in me.polygons:
        if p.material_index != si or any(v in exclude for v in p.vertices):
            continue
        if membership == "centroid":
            c = sum((co[v] for v in p.vertices), Vector()) / len(p.vertices)
            inside = ell.rho_theta(c.x, c.z)[0] < 1.0
        else:
            inside = all(ell.rho_theta(co[v].x, co[v].z)[0] < 1.0 for v in p.vertices)
        if inside:
            region.add(p.index)
    for it in range(1, 41):
        loops = boundary_loops(me, region)
        assert len(loops) == 2, f"annulus must have 2 boundary loops, got {len(loops)}"
        outer = next(lp for lp in loops if not all(v in junction for v in lp))
        ang = [ell.rho_theta(co[v].x, co[v].z)[1] for v in outer]
        steps = [((ang[(i + 1) % len(ang)] - ang[i] + math.pi) % (2 * math.pi)) - math.pi for i in range(len(ang))]
        direction = 1 if sum(steps) > 0 else -1
        bad = {outer[(i + 1) % len(outer)] for i, st in enumerate(steps) if st * direction <= 0}
        rim_stage = not bad
        if rim_stage and notch > 0:
            bad = rim_notches(co, outer, next(lp for lp in loops if lp is not outer), notch)
        if not bad:
            return region, it, co
        grown = False
        for p in me.polygons:
            if p.material_index == si and p.index not in region and bad & set(p.vertices) \
                    and not any(v in exclude for v in p.vertices):
                c = sum((co[v] for v in p.vertices), Vector()) / len(p.vertices)
                if ell.rho_theta(c.x, c.z)[0] < 1.6:  # never grow far beyond the ellipse
                    region.add(p.index)
                    grown = True
        if not grown:
            assert rim_stage, "outer loop not star-shaped and cannot grow (next to a locked patch)"
            return region, it, co  # rim dent next to a locked patch / limit: accepted and recorded
    raise AssertionError("annulus outer loop not star-shaped")


def skin_boundary_vertices(me, si):
    """Vertices on skin edges used by exactly one skin face (the rim/seam where the skin is split
    from the eye or mouth part, plus the outer face-mask border)."""
    cnt = {}
    for p in me.polygons:
        if p.material_index == si:
            for ek in p.edge_keys:
                cnt[ek] = cnt.get(ek, 0) + 1
    return {v for ek, c in cnt.items() if c == 1 for v in ek}


def build_annulus(face, si, junction_mat_key, ell, ring_t, notch, patch_id, membership="all_vertices", relax_iters=5):
    """Replace the skin annulus around a junction loop by concentric rings (shape preserved)."""
    me = face.data
    attr = me.attributes[PATCH_ATTR].data
    exclude = {i for i, a in enumerate(attr) if a.value != 0}
    jm = [i for i, s in enumerate(face.material_slots) if s.material and junction_mat_key in s.material.name][0]
    jpos = {pkey(me.vertices[v].co) for p in me.polygons if p.material_index == jm for v in p.vertices}
    co_all = [face.matrix_world @ v.co for v in me.vertices]
    sb = skin_boundary_vertices(me, si)
    junction = {v.index for v in me.vertices if v.index in sb and pkey(v.co) in jpos
                and ell.rho_theta(co_all[v.index].x, co_all[v.index].z)[0] < 1.0}
    region, grow, co = select_annulus(face, si, junction, ell, exclude, notch, membership)
    loops = boundary_loops(me, region)
    inner = next(lp for lp in loops if all(v in junction for v in lp))
    outer = next(lp for lp in loops if lp is not inner)
    tr = Transfer(face, si)

    def ccw(loop):
        ang = [ell.rho_theta(co[v].x, co[v].z)[1] for v in loop]
        tot = sum(((ang[(i + 1) % len(ang)] - ang[i] + math.pi) % (2 * math.pi)) - math.pi for i in range(len(ang)))
        return (loop if tot > 0 else list(reversed(loop)))
    inner, outer = ccw(inner), ccw(outer)
    # polar construction in ellipse-normalised coordinates (as the #312 nose): rings are sampled at
    # uniform angles between the radial intersections with the inner and outer loops, so rings at
    # the same angle are radially ordered and cannot cross. Loops are joined by angle zippers.
    def ang(v):
        return ell.rho_theta(co[v].x, co[v].z)[1] % (2 * math.pi)

    def loop_at(loop, fr, f):
        """Point on a closed polyline at parameter f (fractions fr ascending from ~0)."""
        n = len(loop)
        for i in range(n):
            a_, b_ = fr[i], (fr[i + 1] if i + 1 < n else fr[0] + 1.0)
            ff = f if f >= a_ else f + 1.0
            if a_ <= ff <= b_:
                t = 0.0 if b_ == a_ else (ff - a_) / (b_ - a_)
                return co[loop[i]].lerp(co[loop[(i + 1) % n]], t)
        return co[loop[0]]

    def star(lp_):
        st = [((ang(lp_[(i + 1) % len(lp_)]) - ang(lp_[i]) + math.pi) % (2 * math.pi)) - math.pi for i in range(len(lp_))]
        return all(x > 0 for x in st)
    if not star(outer):
        st = [((ang(outer[(i + 1) % len(outer)]) - ang(outer[i]) + math.pi) % (2 * math.pi)) - math.pi for i in range(len(outer))]
        raise AssertionError(f"outer loop not star-shaped around ({ell.cx:.4f},{ell.cz:.4f}): "
                             f"{[(i, round(math.degrees(x), 3), [round(c, 4) for c in co[outer[i]]]) for i, x in enumerate(st) if x <= 0][:5]}")
    outer = outer[min(range(len(outer)), key=lambda k: ang(outer[k])):] + outer[:min(range(len(outer)), key=lambda k: ang(outer[k]))]
    out_f = [ang(v) / (2 * math.pi) for v in outer]
    inner_star = star(inner)
    if inner_star:
        inner = inner[min(range(len(inner)), key=lambda k: ang(inner[k])):] + inner[:min(range(len(inner)), key=lambda k: ang(inner[k]))]
        in_f = [ang(v) / (2 * math.pi) for v in inner]

        def inner_ref(f):
            return loop_at(inner, in_f, f)
    else:
        # slit-like seam (lips): rings start from an ellipse that wraps the seam with a margin;
        # the seam joins the first ring by corner-pinned arc length (right corner 0, left 0.5)
        zs = [co[v].z for v in inner]
        cz2 = sum(zs) / len(zs)
        ax2 = max(abs(co[v].x - ell.cx) for v in inner)
        az2 = max(abs(z - cz2) for z in zs) + 0.0008
        i0 = max(range(len(inner)), key=lambda k: co[inner[k]].x)
        inner = inner[i0:] + inner[:i0]
        # CCW in x/z: after the right corner the loop must go up (upper lip first)
        if co[inner[1]].z < co[inner[-1]].z:
            inner = [inner[0]] + list(reversed(inner[1:]))
        pts = [Vector((co[v].x, co[v].z)) for v in inner]
        kl = min(range(len(inner)), key=lambda k: pts[k].x)
        seg = [(pts[(i + 1) % len(pts)] - pts[i]).length for i in range(len(pts))]
        first, second = sum(seg[:kl]), sum(seg[kl:])
        in_f, acc = [], 0.0
        for i, s_ in enumerate(seg):
            in_f.append(0.5 * acc / first if i < kl else 0.5 + 0.5 * (acc - first) / second)
            acc += s_
        def inner_ref(f):
            th = 2 * math.pi * f
            x, z = ell.cx + ax2 * math.cos(th), cz2 + az2 * math.sin(th)
            near = loop_at(inner, in_f, f)
            return Vector((x, near.y, z))

    # direction of the first inner edge in the old region face, to orient the patch
    a0, b0 = inner[0], inner[1]
    old_dir = None
    for i in region:
        vs = list(me.polygons[i].vertices)
        if a0 in vs and b0 in vs:
            old_dir = vs[(vs.index(a0) + 1) % len(vs)] == b0
    assert old_dir is not None, "inner edge not found in the old region"
    n_ring = len(inner) if inner_star else 2 * (len(inner) // 2)
    ring_f = [j / n_ring for j in range(n_ring)]

    interior = {v for i in region for v in me.polygons[i].vertices} - set(inner) - set(outer)
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    pl = bm.verts.layers.int.get(PATCH_ATTR)
    uvl = bm.loops.layers.uv.active
    dl = bm.verts.layers.deform.verify()
    keys = me.shape_keys.key_blocks
    shape_layers = {kb.name: bm.verts.layers.shape.get(kb.name) for kb in keys}
    gidx = {g.name: g.index for g in face.vertex_groups}
    mwi = face.matrix_world.inverted()
    rot = mwi.to_3x3()
    inner_bv = [bm.verts[i] for i in inner]
    outer_bv = [bm.verts[i] for i in outer]
    uv_bound = {}
    for v in inner_bv + outer_bv:
        lp = next((lp for lp in v.link_loops if lp.face.index not in region and lp.face.material_index == si), None)
        if lp is None:
            lp = next(lp for lp in v.link_loops if lp.face.index in region)
        uv_bound[v] = Vector(lp[uvl].uv)
        v[pl] = patch_id
    interior_bv = [bm.verts[i] for i in interior]
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in region], context="FACES_ONLY")
    # only interior vertices go; the rim/seam loop is split from the eye/mouth part and must survive
    bmesh.ops.delete(bm, geom=[v for v in interior_bv if v.is_valid], context="VERTS")
    uv_of = dict(uv_bound)

    def new_vert(x, z, near=None):
        hit = tr.project(x, z, near)[0]
        v = bm.verts.new(mwi @ hit)
        v[pl] = patch_id
        return v

    def finish_vert(v):
        """Attributes at the FINAL (relaxed) position: UV, weights, every shape key."""
        hit, uv, wt, offs = tr.project(0, 0, face.matrix_world @ v.co)
        v.co = mwi @ hit
        for name, layer in shape_layers.items():
            v[layer] = v.co if name == keys[0].name else v.co + rot @ Vector(offs[name])
        tot = sum(wt.values())
        for g, val in wt.items():
            if val / tot > 1e-4:
                v[dl][gidx[g]] = val / tot
        uv_of[v] = uv
    rings = []
    for t in ring_t:
        ring = []
        for f in ring_f:
            q = inner_ref(f).lerp(loop_at(outer, out_f, f), t)  # radial, same angle
            ring.append(new_vert(q.x, q.z, near=q))   # closest skin point follows the lid/lip roll
        rings.append(ring)
    faces = []

    def add(vs):
        f = bm.faces.new(vs)
        f.material_index = si
        f.smooth = True
        faces.append(f)
    for tri in NB.zipper(in_f, ring_f):           # rim/seam loop -> first ring
        add([inner_bv[i] if tag == "o" else rings[0][i] for tag, i in tri])
    n = n_ring
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(n):
            add([a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]])
    for tri in NB.zipper(ring_f, out_f):           # last ring -> outer loop
        add([rings[-1][i] if tag == "o" else outer_bv[i] for tag, i in tri])
    # relax: neighbour average, re-projected to the original skin; loops' boundary vertices fixed
    new_vs = [v for r in rings for v in r]
    mw = face.matrix_world
    for _ in range(relax_iters):
        target = {}
        for v in new_vs:
            nb = [e.other_vert(v) for e in v.link_edges]
            target[v] = sum(((mw @ w.co) for w in nb), Vector()) / len(nb)
        for v, q in target.items():
            v.co = mwi @ tr.project(0, 0, q)[0]
    for v in new_vs:
        finish_vert(v)
    a, b = inner_bv[0], inner_bv[1]
    f0 = next(f for f in faces if a in f.verts and b in f.verts)
    vs = list(f0.verts)
    if (vs[(vs.index(a) + 1) % len(vs)] is b) != old_dir:
        bmesh.ops.reverse_faces(bm, faces=faces)
    for f in faces:
        for lp in f.loops:
            lp[uvl].uv = uv_of[lp.vert]
    bm.to_mesh(me)
    bm.free()
    me.update()
    return {"region_faces": len(region), "removed_vertices": len(interior), "inner_loop": len(inner),
            "outer_loop": len(outer), "rings": len(ring_t), "ring_vertices": n_ring,
            "new_vertices": len(ring_t) * n_ring, "new_faces": len(faces),
            "growth_iterations": grow, "relax_iterations": relax_iters}


def eye_material(c):
    m = bpy.data.materials.new("MORWEN_EYE_PROCEDURAL")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N = nt.nodes.new
    L = nt.links.new
    uv = N("ShaderNodeUVMap")
    sep = N("ShaderNodeSeparateXYZ")
    L(uv.outputs[0], sep.inputs[0])

    def math(op, a, b=None, val=None):
        n = N("ShaderNodeMath")
        n.operation = op
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                L(x, n.inputs[i])
        return n.outputs[0]
    # UV: iris unit circle mapped to radius 0.25 around (0.5, 0.5)
    qx = math("MULTIPLY", math("SUBTRACT", sep.outputs[0], 0.5), 4.0)
    qy = math("MULTIPLY", math("SUBTRACT", sep.outputs[1], 0.5), 4.0)
    d = math("SQRT", math("ADD", math("MULTIPLY", qx, qx), math("MULTIPLY", qy, qy)))

    def rgb(col):
        n = N("ShaderNodeRGB")
        n.outputs[0].default_value = (*col, 1)
        return n.outputs[0]

    def mix(fac, a, b):
        n = N("ShaderNodeMixRGB")
        L(fac, n.inputs[0])
        L(a, n.inputs[1])
        L(b, n.inputs[2])
        return n.outputs[0]

    def step(x, edge, soft=0.04):  # smooth step 0->1 around edge
        return math("MAXIMUM", 0.0, math("MINIMUM", 1.0, math("DIVIDE", math("SUBTRACT", x, edge - soft), 2 * soft)))
    vgrad = math("MAXIMUM", 0.0, math("MINIMUM", 1.0, math("MULTIPLY", math("ADD", qy, 1.0), 0.5)))  # 0 bottom .. 1 top
    iris = mix(vgrad, rgb(c["iris_bottom"]), rgb(c["iris_top"]))
    iris = mix(step(d, 0.88, 0.06), iris, rgb(c["limbal"]))
    iris = mix(math("SUBTRACT", 1.0, step(d, 0.40, 0.05)), iris, rgb(c["pupil"]))
    sclera = mix(step(qy, 0.55, 0.45), rgb(c["sclera"]), rgb(c["sclera_shadow"]))
    col = mix(step(d, 1.0, 0.03), iris, sclera)
    h1 = math("SUBTRACT", 1.0, step(math("SQRT", math("ADD", math("POWER", math("ADD", qx, 0.32), 2.0),
                                                     math("POWER", math("SUBTRACT", qy, 0.38), 2.0))), 0.20, 0.03))
    h2 = math("SUBTRACT", 1.0, step(math("SQRT", math("ADD", math("POWER", math("SUBTRACT", qx, 0.30), 2.0),
                                                     math("POWER", math("ADD", qy, 0.36), 2.0))), 0.09, 0.02))
    col = mix(math("MAXIMUM", h1, h2), col, rgb(c["highlight"]))
    em = N("ShaderNodeEmission")
    L(col, em.inputs["Color"])
    em.inputs["Strength"].default_value = 1.0
    out = N("ShaderNodeOutputMaterial")
    L(em.outputs[0], out.inputs["Surface"])
    return m


def build_eyes(face, arm, ep, rims, opening, U):
    """One spherical-cap eye surface per side behind the rim loop; returns the new object."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    verts, faces, uvs, side_of = [], [], [], []
    # front cover: opaque Face polygons (cards / brow / EyeExtra are alpha overlays)
    dg = bpy.context.evaluated_depsgraph_get()
    fe = face.evaluated_get(dg)
    fme = fe.data
    overlay = {i for i, sl in enumerate(face.material_slots)
               if sl.material and any(k in sl.material.name for k in ("Eyeline", "Eyelash", "Brow", "EyeExtra"))}
    fv = [fe.matrix_world @ v.co for v in fme.vertices]
    fp = [tuple(pp.vertices) for pp in fme.polygons if pp.material_index not in overlay]
    cover = BVHTree.FromPolygons(fv, fp)
    up = Vector((0, 1, 0))
    clip_cell = [0]

    def covered(x, y, z):
        hit = cover.ray_cast(Vector((x, y + 1e-5, z)), up)
        return hit[0] is not None
    for side in ("R", "L"):
        rim = rims[side]
        x0, x1, z0, z1 = opening[side]
        inner_x, outer_x = (x0, x1) if side == "R" else (x1, x0)
        px = inner_x + ep["pupil_frac_from_inner_corner"][side] * (outer_x - inner_x)
        pz = z1 - ep["pupil_frac_from_top"][side] * (z1 - z0)
        r_iris = ep["canonical_iris_width_U"] * U / 2
        R = ep["surface_radius_m"]
        d2 = [(q.x - px) ** 2 + (q.z - pz) ** 2 for q in rim]
        assert max(d2) < R * R, "rim exceeds eye surface radius"
        cy = min(q.y - ep["gap_behind_rim_m"] - math.sqrt(R * R - dd) for q, dd in zip(rim, d2))
        # oblique cover: where the rim sits far in front of the eye surface the
        # surface must reach further out, or a +/-45 deg view looks past its edge
        # into the head interior (MORWEN-ELM-04 socket show-through finding)
        tan_cov = math.tan(math.radians(ep["oblique_cover_deg"]))
        ang_r = [(math.atan2(q.z - pz, q.x - px), math.hypot(q.x - px, q.z - pz),
                  q.y - (cy + math.sqrt(R * R - dd))) for q, dd in zip(rim, d2)]

        def rmax(th):
            near = [a for a in ang_r if math.cos(a[0] - th) > math.cos(math.radians(25))] or \
                [max(ang_r, key=lambda a: math.cos(a[0] - th))]
            want = max(a[1] + ep["margin_m"] + a[2] * tan_cov for a in near)
            # never let the edge leave the head: stop where the front skin no longer covers it
            cone = [a for a in ang_r if math.cos(a[0] - th) > math.cos(math.radians(10))] or near
            r = max(a[1] for a in cone) + 5e-4
            while r < want:
                rn = min(r + 5e-4, want)
                x, z = px + rn * math.cos(th), pz + rn * math.sin(th)
                if not covered(x, cy + math.sqrt(max(R * R - rn * rn, 0)), z):
                    clipped[0] += 1
                    return r
                r = rn
            return want
        clipped = clip_cell
        base = len(verts)
        verts.append((px, cy + R, pz))
        uvs.append((0.5, 0.5))
        side_of.append(side)
        S, Rn = ep["segments"], ep["rings"]
        sx = 1 if side == "R" else -1
        for i in range(1, Rn + 1):
            for j in range(S):
                th = 2 * math.pi * j / S
                r = rmax(th) * i / Rn
                x, z = px + r * math.cos(th), pz + r * math.sin(th)
                y = cy + math.sqrt(max(R * R - (x - px) ** 2 - (z - pz) ** 2, 0))
                verts.append((x, y, z))
                uvs.append((0.5 + 0.25 * sx * (x - px) / r_iris, 0.5 + 0.25 * (z - pz) / r_iris))
                side_of.append(side)
        for j in range(S):
            faces.append((base, base + 1 + (j + 1) % S, base + 1 + j))
        for i in range(1, Rn):
            a0, b0 = base + 1 + (i - 1) * S, base + 1 + i * S
            for j in range(S):
                faces.append((a0 + j, a0 + (j + 1) % S, b0 + (j + 1) % S, b0 + j))
    clip_total = clip_cell[0]
    me = bpy.data.meshes.new("MORWEN_Eyes")
    me.from_pydata(verts, [], faces)
    me.update()
    for p in me.polygons:
        p.use_smooth = True
        if p.normal.y < 0:
            p.flip()
    me.update()
    uvl = me.uv_layers.new(name="UVMap")
    for p in me.polygons:
        for v, li in zip(p.vertices, p.loop_indices):
            uvl.data[li].uv = uvs[v]
    ob = bpy.data.objects.new("MORWEN_Eyes", me)
    ob["edge_clipped_samples"] = clip_total
    bpy.context.scene.collection.objects.link(ob)
    ob.parent = arm
    for side in ("R", "L"):
        g = ob.vertex_groups.new(name=f"J_Adj_{side}_FaceEye")
        g.add([i for i, s in enumerate(side_of) if s == side], 1.0, "REPLACE")
    mod = ob.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    me.materials.append(eye_material(ep["colours"]))
    return ob


def remove_face_materials(face, keys):
    me = face.data
    slots = [i for i, s in enumerate(face.material_slots) if s.material and any(k in s.material.name for k in keys)]
    bm = bmesh.new()
    bm.from_mesh(me)
    dead = [f for f in bm.faces if f.material_index in slots]
    n = len(dead)
    bmesh.ops.delete(bm, geom=dead, context="FACES")
    bm.to_mesh(me)
    bm.free()
    me.update()
    return n


def rebind_cards(face, cp, slots):
    """Skin-relative clearance projection of eyeline/eyelash cards in Basis and every key."""
    me = face.data
    keys = me.shape_keys.key_blocks
    base0 = np.array([v.co[:] for v in keys[0].data])
    abs0 = {kb.name: np.array([v.co[:] for v in kb.data]) for kb in keys[1:]}
    mw = np.array(face.matrix_world)
    mwi = np.linalg.inv(mw)
    card_slots = {i for i, s in enumerate(face.material_slots) if s.material and any(k in s.material.name for k in cp["materials"])}
    me.calc_loop_triangles()
    ctris = [(t.vertices[:], t.loops[:], t.material_index) for t in me.loop_triangles if t.material_index in card_slots]
    stris = [t.vertices[:] for t in me.loop_triangles if t.material_index == slots["skin"]]
    alpha = {i: X.image_alpha(face.material_slots[i].material) for i in card_slots}
    uv = me.uv_layers.active.data
    bary = [(i / X.GRID, j / X.GRID) for i in range(X.GRID + 1) for j in range(X.GRID + 1 - i)]
    samples = []  # (tri index, barycentric) of opaque texels
    for ti, (vs, loops, mi) in enumerate(ctris):
        arr, w, h = alpha[mi]
        U = [uv[li].uv for li in loops]
        for s, t in bary:
            r = 1 - s - t
            u = U[0] * s + U[1] * t + U[2] * r
            if arr[min(h - 1, max(0, int(u.y * h))), min(w - 1, max(0, int(u.x * w)))] >= X.ALPHA_MIN:
                samples.append((ti, np.array([s, t, r])))
    card_verts = sorted({v for vs, _, _ in ctris for v in vs})
    log = {}

    def to_world(c):
        return (np.hstack([c, np.ones((len(c), 1))]) @ mw.T)[:, :3]

    def fix(local):
        W = to_world(local)
        moved_total = 0.0
        for _ in range(cp["iterations"]):
            bvh = BVHTree.FromPolygons([Vector(p) for p in W], stris)
            lift = {}
            for ti, b in samples:
                vs = ctris[ti][0]
                p = Vector((W[vs[0]] * b[0] + W[vs[1]] * b[1] + W[vs[2]] * b[2]).tolist())
                cov = X.covered(bvh, p)
                if cov is None:
                    continue
                need = cov[0] + cp["min_clearance_m"]
                nrm = cov[1]
                s2 = float((b * b).sum())
                for k, v in enumerate(vs):
                    amt = need * b[k] / s2
                    if v not in lift or amt > lift[v][0]:
                        lift[v] = (amt, np.array(nrm[:]))
            if not lift:
                break
            for v, (amt, n) in lift.items():
                W[v] += n * amt
                moved_total = max(moved_total, amt)
        return (np.hstack([W, np.ones((len(W), 1))]) @ mwi.T)[:, :3], moved_total
    new_base, m0 = fix(base0.copy())
    keys[0].data.foreach_set("co", new_base.ravel())
    me.vertices.foreach_set("co", new_base.ravel())
    log["Basis"] = round(m0 * 1000, 3)
    for kb in keys[1:]:
        k_abs = new_base + (abs0[kb.name] - base0)
        if np.abs(abs0[kb.name] - base0)[card_verts].max() < 1e-9 and m0 == 0:
            kb.data.foreach_set("co", k_abs.ravel())
            continue
        k_new, mk = fix(k_abs)
        kb.data.foreach_set("co", k_new.ravel())
        if mk > 0:
            log[kb.name] = round(mk * 1000, 3)
    me.update()
    return {"card_vertices": len(card_verts), "opaque_samples": len(samples), "max_lift_mm_by_state": log}


def ellipses(p, L):
    out = {}
    lp = p["lids"]
    for side in ("R", "L"):
        cx = (L[f"eye_inner_{side}"]["position"][0] + L[f"eye_outer_{side}"]["position"][0]) / 2
        cz = (L[f"eye_top_{side}"]["position"][2] + L[f"eye_bottom_{side}"]["position"][2]) / 2
        hw = abs(L[f"eye_outer_{side}"]["position"][0] - L[f"eye_inner_{side}"]["position"][0]) / 2
        hh = (L[f"eye_top_{side}"]["position"][2] - L[f"eye_bottom_{side}"]["position"][2]) / 2
        out[f"lid_{side}"] = ("EyeWhite", Ellipse(cx, cz, hw * lp["ellipse_scale_x"], hh * lp["ellipse_scale_z_up"],
                                                  hh * lp["ellipse_scale_z_down"]), lp)
    mp = p["mouth"]
    mR, mL = L["mouth_corner_R"]["position"], L["mouth_corner_L"]["position"]
    st = L["stomion"]["position"]
    out["mouth"] = ("FaceMouth", Ellipse((mR[0] + mL[0]) / 2, st[2], abs(mR[0] - mL[0]) / 2 * mp["half_width_scale"],
                                         mp["z_up_m"], mp["z_down_m"]), mp)
    return out


def region_vertices(face, name, spec):
    """Dry run of the annulus selection on the CURRENT mesh (baseline QA)."""
    key, ell, sp = spec
    me = face.data
    si = M3.slot_index(face, "Face_00_SKIN")
    exclude = {i for i, a in enumerate(me.attributes[PATCH_ATTR].data) if a.value != 0} if PATCH_ATTR in me.attributes else set()
    jm = M3.slot_index(face, key)
    jpos = {pkey(me.vertices[v].co) for p in me.polygons if p.material_index == jm for v in p.vertices}
    co = [face.matrix_world @ v.co for v in me.vertices]
    sb = skin_boundary_vertices(me, si)
    junction = {v.index for v in me.vertices if v.index in sb and pkey(v.co) in jpos
                and ell.rho_theta(co[v.index].x, co[v.index].z)[0] < 1.0}
    region, _, _ = select_annulus(face, si, junction, ell, exclude, sp["notch_ratio"], sp.get("membership", "all_vertices"))
    return {v for i in region for v in me.polygons[i].vertices}


def build_base(params):
    """Import must already be in the scene. Rebuild #312 and lock the nose at 0.5."""
    p = params
    np.random.seed(p["seed"])
    nrec = NB.build(json.loads(NB.PARAMS_PATH.read_text()))
    face = bpy.data.objects["Face"]
    me = face.data
    assert face_hash(me) == p["locked_nose"]["face_geometry_hash"], "locked #312 nose geometry mismatch"
    me.shape_keys.key_blocks[p["locked_nose"]["design_key"]].value = p["locked_nose"]["design_value"]
    attr = me.attributes.new(PATCH_ATTR, "INT", "POINT")
    nose_set = set(nrec["patch_vertex_indices"])
    attr.data.foreach_set("value", [4 if i in nose_set else 0 for i in range(len(me.vertices))])
    return nrec


def build(params, nrec, baseline_open):
    """Candidate on top of build_base(). Returns (record, eyes object)."""
    p = params
    face = bpy.data.objects["Face"]
    me = face.data
    nose_set = {i for i, a in enumerate(me.attributes[PATCH_ATTR].data) if a.value == 4}
    si = M3.slot_index(face, "Face_00_SKIN")
    # corner normals of the current (nose) mesh, keyed by face position, for final restore
    poly_n = {}
    for poly in me.polygons:
        ck = tuple(sorted(pkey(me.vertices[v].co) for v in poly.vertices))
        poly_n[ck] = {pkey(me.vertices[v].co): tuple(me.corner_normals[li].vector) for v, li in zip(poly.vertices, poly.loop_indices)}
    nose_pos = {pkey(me.vertices[i].co) for i in nose_set}
    base = nrec["baseline"]
    L = base["landmarks"]
    U = base["normalisation"]["unit_U_m"]
    rec = {"nose": {"hash_verified": True, "design_value": p["locked_nose"]["design_value"]}}
    for (name, (key, ell, sp)), pid in zip(ellipses(p, L).items(), (1, 2, 3)):
        if not sp.get("enabled", True):
            rec[name] = {"built": False, "status": p.get("retopo_status", {}).get("status", "DISABLED")}
            continue
        rec[name] = build_annulus(face, si, key, ell, sp["ring_t"], sp["notch_ratio"], pid,
                                  sp.get("membership", "all_vertices"), sp.get("relax_iterations", 5))
    # eyes: rims and the measured opening (baseline neutral) per side
    ew = M3.slot_index(face, "EyeWhite")
    rimpos = {pkey(me.vertices[v].co) for pp in me.polygons if pp.material_index == ew for v in pp.vertices}
    rims = {"R": [], "L": []}
    skin_v = {v for pp in me.polygons if pp.material_index == si for v in pp.vertices}
    for v in skin_v:
        if pkey(me.vertices[v].co) in rimpos:
            w = face.matrix_world @ me.vertices[v].co
            rims["R" if w.x > M3.MID_X else "L"].append(w)
    ep = p["eyes"]
    rec["removed_eye_plate_faces"] = remove_face_materials(face, ep["remove_face_materials"])
    arm = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
    eyes = build_eyes(face, arm, ep, rims, baseline_open, U)
    rec["eyes"] = {"object": eyes.name, "vertices": len(eyes.data.vertices), "faces": len(eyes.data.polygons),
                   "iris_radius_m": round(ep["canonical_iris_width_U"] * U / 2, 6)}
    # custom normals: untouched corners restored, patch corners automatic (incl. nose)
    attr = me.attributes[PATCH_ATTR].data
    patch = {i for i, a in enumerate(attr) if a.value != 0}
    corner = [None] * len(me.loops)
    for poly in me.polygons:
        ck = tuple(sorted(pkey(me.vertices[v].co) for v in poly.vertices))
        old = poly_n.get(ck)
        in_patch = all(v in patch for v in poly.vertices) or any(pkey(me.vertices[v].co) in nose_pos for v in poly.vertices)
        for v, li in zip(poly.vertices, poly.loop_indices):
            if old is not None and not in_patch:
                corner[li] = old[pkey(me.vertices[v].co)]
            else:
                corner[li] = (0.0, 0.0, 0.0)
    me.normals_split_custom_set(corner)
    rec["cards"] = rebind_cards(face, p["cards"], X.face_slots(face))
    return rec, eyes

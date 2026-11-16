"""LIND-BUILD-01 shared modular kit: mesh builder and architectural primitives.

Method family (see attempt-ledger): BUILD-KIT-A "solid wall shell with grid-decomposed real
apertures + irregular planar-outline dressed stones + per-slate varied roof on modelled
rafters/battens". Structurally different from stopped families H-A (identical slate cubes),
H-E (bevel/displaced cube quoins) and H-F (per-row masonry stones).

All geometry is emitted directly in metres into MeshBuilder buffers; every face receives UVs
(box-projected in world metres unless explicit UVs are given) and a per-piece random value
(face attribute `piece_rand`) used by shaders for per-stone/per-slate/per-plank variation.
"""
from __future__ import annotations

import math
import random

import bpy  # noqa: I001 (bpy before bmesh in module mode)
import bmesh
from mathutils import Matrix, Vector

Z = Vector((0.0, 0.0, 1.0))


# --------------------------------------------------------------------------- builder
class MeshBuilder:
    def __init__(self, name, uv_scale=1.0):
        self.name = name
        self.verts = []
        self.faces = []
        self.face_mat = []
        self.face_uv = []
        self.face_rand = []
        self.mats = []
        self.M = Matrix.Identity(4)
        self.uv_scale = uv_scale
        self.seg = 0
        self.vert_seg = []

    def new_segment(self):
        """Start a new weld island (vertices are only merged within one segment)."""
        self.seg += 1

    def _mat_index(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def poly(self, pts, mat, uvs=None, rand=0.0, uv_scale=None):
        """pts: building-space points (Vector/tuple); transformed by self.M."""
        wp = [self.M @ Vector(p) for p in pts]
        if len(wp) < 3:
            return
        base = len(self.verts)
        self.verts.extend(wp)
        self.vert_seg.extend([self.seg] * len(wp))
        self.faces.append(tuple(range(base, base + len(wp))))
        self.face_mat.append(self._mat_index(mat))
        if uvs is None:
            uvs = box_uv(wp, uv_scale or self.uv_scale)
        self.face_uv.append(uvs)
        self.face_rand.append(rand)

    def to_object(self, coll, merge=False, smooth=False):
        if not self.faces:
            return None
        me = bpy.data.meshes.new(self.name)
        verts, faces = self.verts, self.faces
        if merge:
            key_to_new, remap, nv = {}, [], []
            for i, v in enumerate(self.verts):
                key = (self.vert_seg[i], round(v.x, 5), round(v.y, 5), round(v.z, 5))
                if key not in key_to_new:
                    key_to_new[key] = len(nv)
                    nv.append(v)
                remap.append(key_to_new[key])
            verts = nv
            faces = [tuple(remap[i] for i in f) for f in self.faces]
        me.from_pydata([tuple(v) for v in verts], [], faces)
        uv = me.uv_layers.new(name="UVMap")
        li = 0
        for fi, poly in enumerate(me.polygons):
            for k, loop_index in enumerate(poly.loop_indices):
                uv.data[loop_index].uv = self.face_uv[fi][k]
            poly.material_index = self.face_mat[fi]
        attr = me.attributes.new("piece_rand", "FLOAT", "FACE")
        attr.data.foreach_set("value", self.face_rand)
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = smooth
        ob = bpy.data.objects.new(self.name, me)
        for m in self.mats:
            ob.data.materials.append(m)
        coll.objects.link(ob)
        return ob


def box_uv(pts, scale):
    n = poly_normal(pts)
    ax = max(range(3), key=lambda i: abs(n[i]))
    if ax == 0:
        return [(p.y / scale, p.z / scale) for p in pts]
    if ax == 1:
        return [(p.x / scale, p.z / scale) for p in pts]
    return [(p.x / scale, p.y / scale) for p in pts]


def poly_normal(pts):
    n = Vector((0.0, 0.0, 0.0))
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        n.x += (a.y - b.y) * (a.z + b.z)
        n.y += (a.z - b.z) * (a.x + b.x)
        n.z += (a.x - b.x) * (a.y + b.y)
    return n.normalized() if n.length > 1e-12 else Vector((0, 0, 1))


# --------------------------------------------------------------------------- primitives
def box(mb, center, size, mat, axes=None, rand=0.0, uv_scale=None, ML=None):
    """Oriented box. axes = (X, Y, Z) unit vectors; ML optional local->building matrix."""
    c = Vector(center)
    ax = axes or (Vector((1, 0, 0)), Vector((0, 1, 0)), Z)
    hx, hy, hz = (ax[0] * size[0] / 2, ax[1] * size[1] / 2, ax[2] * size[2] / 2)
    p = [c - hx - hy - hz, c + hx - hy - hz, c + hx + hy - hz, c - hx + hy - hz,
         c - hx - hy + hz, c + hx - hy + hz, c + hx + hy + hz, c - hx + hy + hz]
    if ML is not None:
        p = [ML @ q for q in p]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        mb.poly([p[i] for i in f], mat, rand=rand, uv_scale=uv_scale)


def flat_prism(mb, outline, frame_fn, d0, d1, mat, rand=0.0):
    """Extrude a (possibly concave) outline; caps are n-gons (Blender tessellates concave n-gons)."""
    back = [frame_fn(u, v, d0) for (u, v) in outline]
    front = [frame_fn(u, v, d1) for (u, v) in outline]
    mb.poly(front, mat, rand=rand)
    mb.poly(list(reversed(back)), mat, rand=rand)
    n = len(outline)
    for i in range(n):
        j = (i + 1) % n
        mb.poly([back[i], back[j], front[j], front[i]], mat, rand=rand)


def prism(mb, outline, frame_fn, d0, d1, mat, rand=0.0, bulge=0.0, front_jitter=None, uvs_scale=None):
    """Extrude a 2D outline [(u,v)...] from depth d0 (back) to d1 (front).
    frame_fn(u, v, d) -> building-space Vector. Front face is fanned from the centroid so a
    bulge / per-vertex depth jitter produces planar facets (hand-dressed face)."""
    n = len(outline)
    fj = front_jitter or [0.0] * n
    back = [frame_fn(u, v, d0) for (u, v) in outline]
    front = [frame_fn(u, v, d1 + fj[i]) for i, (u, v) in enumerate(outline)]
    cu = sum(u for u, _ in outline) / n
    cv = sum(v for _, v in outline) / n
    cen = frame_fn(cu, cv, d1 + bulge + (sum(fj) / n))
    mb.poly(list(reversed(back)), mat, rand=rand, uv_scale=uvs_scale)
    for i in range(n):
        j = (i + 1) % n
        mb.poly([back[i], back[j], front[j], front[i]], mat, rand=rand, uv_scale=uvs_scale)
        mb.poly([front[i], front[j], cen], mat, rand=rand, uv_scale=uvs_scale)


def lathe(mb, profile, center, mat, segments=16, rand=0.0, cap_bottom=True, cap_top=True, axis_M=None, uv_rows=None):
    """Revolve profile [(r, z)...] around local Z. axis_M optional 3x3 rotation."""
    c = Vector(center)
    R = axis_M or Matrix.Identity(3)
    rings = []
    for (r, zz) in profile:
        ring = []
        for s in range(segments):
            a = 2 * math.pi * s / segments
            ring.append(c + R @ Vector((r * math.cos(a), r * math.sin(a), zz)))
        rings.append(ring)
    height = max(1e-6, profile[-1][1] - profile[0][1])
    for k in range(len(rings) - 1):
        for s in range(segments):
            t = (s + 1) % segments
            u0, u1 = s / segments, (s + 1) / segments
            v0 = (profile[k][1] - profile[0][1]) / height
            v1 = (profile[k + 1][1] - profile[0][1]) / height
            mb.poly([rings[k][s], rings[k][t], rings[k + 1][t], rings[k + 1][s]], mat,
                    uvs=[(u0, v0), (u1, v0), (u1, v1), (u0, v1)], rand=rand)
    if cap_bottom and profile[0][0] > 1e-5:
        mb.poly(list(reversed(rings[0])), mat, rand=rand)
    if cap_top and profile[-1][0] > 1e-5:
        mb.poly(rings[-1], mat, rand=rand)


# --------------------------------------------------------------------------- frames
class WallFrame:
    """Outer face of a wall. u along wall (left->right seen from outside), z up, d outward."""

    def __init__(self, origin, U, N):
        self.O = Vector(origin)
        self.U = Vector(U).normalized()
        self.N = Vector(N).normalized()

    def p(self, u, z, d=0.0):
        return self.O + self.U * u + Z * z + self.N * d

    def fn(self):
        return lambda u, v, d: self.p(u, v, d)


def clip_convex(poly, clip):
    """Sutherland-Hodgman: clip polygon (list of (x,y)) against convex CCW polygon."""
    out = poly
    for i in range(len(clip)):
        a, b = clip[i], clip[(i + 1) % len(clip)]
        inp, out = out, []
        if not inp:
            break

        def inside(p):
            return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= -1e-9

        def inter(p, q):
            x1, y1, x2, y2 = p[0], p[1], q[0], q[1]
            x3, y3, x4, y4 = a[0], a[1], b[0], b[1]
            den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
            t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
            return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

        for j in range(len(inp)):
            cur, prev = inp[j], inp[j - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(inter(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(inter(prev, cur))
    # drop near-duplicate points
    res = []
    for p in out:
        if not res or abs(p[0] - res[-1][0]) > 1e-7 or abs(p[1] - res[-1][1]) > 1e-7:
            res.append(p)
    if len(res) > 1 and abs(res[0][0] - res[-1][0]) < 1e-7 and abs(res[0][1] - res[-1][1]) < 1e-7:
        res.pop()
    return res


def wall_with_openings(mb, frame, length, profile, thickness, openings, mat, mat_reveal=None):
    """Watertight wall solid with real rectangular apertures.

    profile: convex CCW outline [(u,z)...] in the wall plane (rectangle or gable pentagon).
    openings: list of (u0, u1, z0, z1) rectangles fully inside profile.
    Grid decomposition keeps every edge shared, so merging vertices yields a closed mesh.
    """
    mat_reveal = mat_reveal or mat
    mb.new_segment()
    us = sorted({round(p[0], 6) for p in profile} | {round(o[k], 6) for o in openings for k in (0, 1)})
    zs = sorted({round(p[1], 6) for p in profile} | {round(o[k], 6) for o in openings for k in (2, 3)})
    cells = []
    for i in range(len(us) - 1):
        for j in range(len(zs) - 1):
            cu, cz = (us[i] + us[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
            if any(o[0] < cu < o[1] and o[2] < cz < o[3] for o in openings):
                continue
            rect = [(us[i], zs[j]), (us[i + 1], zs[j]), (us[i + 1], zs[j + 1]), (us[i], zs[j + 1])]
            c = clip_convex(rect, profile)
            if len(c) >= 3:
                cells.append(c)
    # snap shared points to identical floats (tolerance hash), then emit caps
    table = {}

    def snap(p):
        kx, ky = int(math.floor(p[0] / 1e-4)), int(math.floor(p[1] / 1e-4))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for q in table.get((kx + dx, ky + dy), ()):
                    if abs(q[0] - p[0]) < 2e-5 and abs(q[1] - p[1]) < 2e-5:
                        return q
        q = (p[0], p[1])
        table.setdefault((kx, ky), []).append(q)
        return q

    snapped = []
    for c in cells:
        sc = []
        for p in c:
            q = snap(p)
            if not sc or sc[-1] != q:
                sc.append(q)
        if len(sc) > 1 and sc[0] == sc[-1]:
            sc.pop()
        if len(sc) >= 3:
            snapped.append(sc)
    # T-junction removal: insert any snapped vertex lying on a cell edge into that edge
    allpts = list({q for c in snapped for q in c})
    fixed = []
    for c in snapped:
        out = []
        for i in range(len(c)):
            a, b = c[i], c[(i + 1) % len(c)]
            out.append(a)
            ex, ey = b[0] - a[0], b[1] - a[1]
            L2 = ex * ex + ey * ey
            if L2 < 1e-12:
                continue
            mids = []
            for q in allpts:
                if q == a or q == b:
                    continue
                t = ((q[0] - a[0]) * ex + (q[1] - a[1]) * ey) / L2
                if 1e-6 < t < 1 - 1e-6:
                    cr = abs(ex * (q[1] - a[1]) - ey * (q[0] - a[0])) / math.sqrt(L2)
                    if cr < 2e-5:
                        mids.append((t, q))
            out.extend(q for _, q in sorted(mids))
        fixed.append(out)
    edge_use = {}
    for c in fixed:
        mb.poly([frame.p(u, z, 0.0) for (u, z) in c], mat)
        mb.poly([frame.p(u, z, -thickness) for (u, z) in reversed(c)], mat)
        for i in range(len(c)):
            a, b = c[i], c[(i + 1) % len(c)]
            k = (a, b) if a < b else (b, a)
            edge_use.setdefault(k, []).append((a, b))
    for k, uses in edge_use.items():
        if len(uses) != 1:
            continue
        a, b = uses[0]
        on_open = any(abs(a[0] - b[0]) < 1e-9 and o[0] - 1e-6 <= a[0] <= o[1] + 1e-6 and o[2] - 1e-6 <= min(a[1], b[1])
                      and max(a[1], b[1]) <= o[3] + 1e-6 or abs(a[1] - b[1]) < 1e-9 and o[2] - 1e-6 <= a[1] <= o[3] + 1e-6
                      and o[0] - 1e-6 <= min(a[0], b[0]) and max(a[0], b[0]) <= o[1] + 1e-6 for o in openings)
        mb.poly([frame.p(a[0], a[1], 0), frame.p(a[0], a[1], -thickness), frame.p(b[0], b[1], -thickness),
                 frame.p(b[0], b[1], 0)], mat_reveal if on_open else mat)


def irregular_outline(u0, u1, z0, z1, rng, chip=0.04, wobble=0.012):
    """Rectangle with randomly chipped corners and wobbling edges (hand-dressed stone face)."""
    pts = []
    corners = [(u0, z0), (u1, z0), (u1, z1), (u0, z1)]
    lim = 0.3 * min(u1 - u0, z1 - z0)
    for i, (cu, cz) in enumerate(corners):
        nu, nz = corners[(i + 1) % 4]
        pu_, pz_ = corners[i - 1]
        du = 1 if nu > cu else (-1 if nu < cu else 0)
        dz = 1 if nz > cz else (-1 if nz < cz else 0)
        iu = 1 if cu > pu_ else (-1 if cu < pu_ else 0)
        iz = 1 if cz > pz_ else (-1 if cz < pz_ else 0)
        c1 = min(rng.uniform(0.0, chip), lim)
        if c1 > chip * 0.35:
            c0 = c1 * rng.uniform(0.5, 1.0)
            pts.append((cu - iu * c0, cz - iz * c0))
            pts.append((cu + du * c1, cz + dz * c1))
        else:
            pts.append((cu, cz))
        # mid-edge wobble points
        segs = 2 if abs(nu - cu) + abs(nz - cz) > 0.5 else 1
        for s in range(1, segs + 1):
            t = s / (segs + 1)
            mu, mz = cu + (nu - cu) * t, cz + (nz - cz) * t
            w = rng.uniform(-wobble, wobble)
            mu += -dz * w
            mz += du * w
            pts.append((mu, mz))
    # fix order: corners were inserted with chip points possibly reversed; ensure CCW in (u,z)
    area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts)))
    if area < 0:
        pts.reverse()
    return pts


def dressed_stone(mb, frame, u0, u1, z0, z1, proud, mat, rng, embed=0.06, chip=0.045):
    outline = irregular_outline(u0, u1, z0, z1, rng, chip=chip)
    fj = [rng.uniform(-0.008, 0.010) for _ in outline]
    prism(mb, outline, frame.fn(), -embed, proud, mat, rand=rng.random(),
          bulge=rng.uniform(0.004, 0.016), front_jitter=fj)

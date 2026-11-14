"""MORWEN-EYELID-RETOPO-05: canthus-anchored, curve-constrained local quad retopology of the lids.

Base = PR #316 candidate (locked #312 nose @0.5, procedural violet eye, card rebind). The eye
opening is redesigned to the Layer 0 targets (measure_eye_targets_05.py). Per eye:

1. lid region = ELM-04 lid selection (original skin faces only; its outer loop is kept).
2. the outer loop is split into an upper and a lower arc on the canthal axis of the NEW canthi.
3. each arc becomes a structured quad strip: one column per existing outer vertex (no zipper),
   rows t = rows_t from the new margin curve (t = 0) to the outer vertex (t = 1); the two strips
   share the canthus columns, so the canthi are single fixed vertices.
4. depth, UV, weights and every shape key come from the OLD lid at the same (u, t): a point
   between the old rim and the same outer vertex. Lid keys are retargeted per column: the old
   margin motion as a fraction of the old upper-lower gap is applied to the NEW gap.
5. eyeliner / eyelash / EyeExtra cards follow the margin displacement; the eye surface is rebuilt
   behind the new rim with the unchanged #316 material; cards are re-lifted per state (#316).

The mouth is out of scope and untouched. The polar annulus family (stopped) is not used.
"""
import importlib.util
import json
import math
import os
import sys
from pathlib import Path

import bpy
import bmesh  # noqa: E402  (needs bpy first)
import numpy as np
from mathutils import Vector

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


E = _load(MP / "eyes_lids_mouth" / "build_eyes_lids_mouth_04.py", "morwen_elm_build")
MT = _load(HERE / "measure_eye_targets_05.py", "morwen_eye_targets_05")
M3, X = E.M3, E.X
PARAMS_PATH = HERE / "eyelid_params_05.json"
SIDES = {"R": 1, "L": 2}  # elm_patch ids (3 = mouth, unused here; 4 = locked nose)
WALL_OFFSET = 10          # lid-thickness wall vertices: 11 (R) / 12 (L)


def xz(v):
    return np.array([v[0], v[2]])


def arc_param(pts):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.asarray(pts)[:, [0, 2]] if np.asarray(pts).shape[1] == 3
                                                  else np.asarray(pts), axis=0), axis=1))]
    return d / d[-1]


def sample(pts, u_of, u):
    """Piecewise-linear point at parameter u (pts: N x D, u_of: N increasing 0..1)."""
    pts = np.asarray(pts, float)
    return np.array([np.interp(u, u_of, pts[:, k]) for k in range(pts.shape[1])])


def nearest_param(pts, u_of, q):
    """Parameter and distance of the closest point of polyline pts (x/z plane) to q (x, z)."""
    P = np.asarray(pts, float)[:, [0, 2]]
    best = (1e9, 0.0)
    for i in range(len(P) - 1):
        a, b = P[i], P[i + 1]
        ab = b - a
        t = float(np.clip(np.dot(q - a, ab) / max(np.dot(ab, ab), 1e-18), 0, 1))
        d = float(np.linalg.norm(a + t * ab - q))
        if d < best[0]:
            best = (d, u_of[i] + t * (u_of[i + 1] - u_of[i]))
    return best[1], best[0]


def ccw(loop, co):
    """Order a loop counter-clockwise in the x/z plane (front view: +x = character R)."""
    P = np.array([xz(co[v]) for v in loop])
    area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    return loop if area > 0 else loop[::-1]


def split_arcs(loop, co, c_in, c_out, pick):
    """Split a closed loop into (upper, lower) arcs ordered inner -> outer canthus.
    pick='axis': split vertices are the loop vertices nearest the canthal axis beyond each canthus
    (outer loop); pick='extreme': split vertices are the loop vertices extreme along the axis (old rim)."""
    a = (c_out - c_in) / np.linalg.norm(c_out - c_in)
    n = np.array([-a[1], a[0]])
    if n[1] < 0:
        n = -n  # n points up (+z)
    mid = (c_in + c_out) / 2
    P = {v: xz(co[v]) - mid for v in loop}
    if pick == "axis":
        i_in = min((v for v in loop if np.dot(P[v], a) < 0), key=lambda v: abs(np.dot(P[v], n)))
        i_out = min((v for v in loop if np.dot(P[v], a) > 0), key=lambda v: abs(np.dot(P[v], n)))
    else:
        i_in = min(loop, key=lambda v: np.dot(P[v], a))
        i_out = max(loop, key=lambda v: np.dot(P[v], a))
    k_in, k_out = loop.index(i_in), loop.index(i_out)
    n_ = len(loop)
    fwd = [loop[(k_in + i) % n_] for i in range((k_out - k_in) % n_ + 1)]
    bwd = [loop[(k_in - i) % n_] for i in range((k_in - k_out) % n_ + 1)]
    up_fwd = np.mean([np.dot(P[v], n) for v in fwd[1:-1]]) if len(fwd) > 2 else 0
    up_bwd = np.mean([np.dot(P[v], n) for v in bwd[1:-1]]) if len(bwd) > 2 else 0
    return (fwd, bwd) if up_fwd > up_bwd else (bwd, fwd)


def lid_region(face, spec):
    key, ell, sp = spec
    me = face.data
    si = M3.slot_index(face, "Face_00_SKIN")
    exclude = {i for i, a in enumerate(me.attributes[E.PATCH_ATTR].data) if a.value != 0}
    jm = M3.slot_index(face, key)
    jpos = {E.pkey(me.vertices[v].co) for p in me.polygons if p.material_index == jm for v in p.vertices}
    co = [face.matrix_world @ v.co for v in me.vertices]
    sb = E.skin_boundary_vertices(me, si)
    junction = {v.index for v in me.vertices if v.index in sb and E.pkey(v.co) in jpos
                and ell.rho_theta(co[v.index].x, co[v.index].z)[0] < 1.0}
    region, _, _ = E.select_annulus(face, si, junction, ell, exclude, sp["notch_ratio"], sp.get("membership", "all_vertices"))
    loops = E.boundary_loops(me, region)
    assert len(loops) == 2
    inner = next(lp for lp in loops if all(v in junction for v in lp))
    outer = next(lp for lp in loops if lp is not inner)
    return region, ccw(inner, co), ccw(outer, co)


def build_lid(face, side, spec, tgt, P, tr):
    """Replace one lid region by two canthus-anchored quad strips. Returns (record, margin data)."""
    me = face.data
    si = M3.slot_index(face, "Face_00_SKIN")
    mw, mwi = face.matrix_world, face.matrix_world.inverted()
    region, inner, outer = lid_region(face, spec)
    co = [mw @ v.co for v in me.vertices]
    c_in, c_out = np.array(tgt["canthus_inner_xz"]), np.array(tgt["canthus_outer_xz"])
    o_up, o_lo = split_arcs(outer, co, c_in, c_out, "axis")
    r_up, r_lo = split_arcs(inner, co, c_in, c_out, "extreme")
    # new margin curves (x, z), inner -> outer
    m_up, m_lo = np.array(tgt["upper_xz"]), np.array(tgt["lower_xz"])
    keys = me.shape_keys.key_blocks
    base = np.array([v.co[:] for v in keys[0].data])
    off = {kb.name: np.array([v.co[:] for v in kb.data]) - base for kb in keys[1:]}
    # closing / opening keys are retargeted per column by the old motion expressed as a fraction
    # alpha of the old upper-lower gap plus the motion perpendicular to it (attempt 2)
    u_up = arc_param(np.array([co[v][:] for v in r_up])); u_lo = arc_param(np.array([co[v][:] for v in r_lo]))
    oU, oL = base[r_up], base[r_lo]
    offU = {k: o[r_up] for k, o in off.items()}; offL = {k: o[r_lo] for k, o in off.items()}
    ur = P["closure"]["u_range"]
    new_margin_local = {}

    def margin_motion(name, k, u):
        """(new margin offset, old margin offset) in local coordinates for strip `name` at u."""
        uc = min(max(u, ur[0]), ur[1])
        gc = sample(oL, u_lo, uc) - sample(oU, u_up, uc)
        gg = max(float(np.dot(gc, gc)), 1e-12)
        g = sample(oL, u_lo, u) - sample(oU, u_up, u)
        nU, nL = sample(new_margin_local["upper"], np.array(new_margin_local["u_upper"]), u), \
            sample(new_margin_local["lower"], np.array(new_margin_local["u_lower"]), u)
        gn = nL - nU
        if name == "upper":
            o = sample(offU[k], u_up, u)
            a = float(np.clip(np.dot(sample(offU[k], u_up, uc), gc) / gg, -0.5, 1.5))
            return a * gn + (o - a * g), o
        o = sample(offL[k], u_lo, u)
        a = float(np.clip(np.dot(sample(offL[k], u_lo, uc), -gc) / gg, -0.5, 1.5))
        return a * -gn + (o + a * g), o
    rows = P["rows_t"]
    t_coarse, t_last_fine = rows[-2], rows[-3]
    t_mid = (t_coarse + t_last_fine) / 2
    fine_rows = rows[:-2]

    def point(marg, u_m, opoly, u_o, r_pts, u_r, u, t):
        M = sample(marg, u_m, u)
        O3 = sample(opoly, u_o, u)
        R_old = sample(r_pts, u_r, u)
        x, z = M[0] + (O3[0] - M[0]) * t, M[1] + (O3[2] - M[1]) * t
        q = R_old + (O3 - R_old) * t
        # depth by correspondence: the old lid's depth at the same (u, t) (smooth along the column;
        # attempt 1 mixed skin hits and rim depths, which made the canthus spike / lower-lid shelf)
        y = q[1] if t == 0 else tr.project(0, 0, Vector(q.tolist()))[0].y
        return {"x": x, "y": y, "z": z, "q": q, "t": t, "u": float(u)}
    strips = {}
    for name, oarc, rarc, marg in (("upper", o_up, r_up, m_up), ("lower", o_lo, r_lo, m_lo)):
        opoly = np.array([co[v][:] for v in oarc]); u_o = arc_param(opoly)
        r_pts = np.array([co[v][:] for v in rarc]); u_r = arc_param(r_pts)
        u_m = arc_param(marg)
        segs = len(oarc) - 1
        F = 3 if segs < P["min_margin_segments"] else 1
        fine_u = [u_o[j] + (u_o[j + 1] - u_o[j]) * i / F for j in range(segs) for i in range(F)] + [1.0]
        pt = lambda u, t: point(marg, u_m, opoly, u_o, r_pts, u_r, u, t)  # noqa: E731
        strips[name] = {"F": F, "outer": oarc, "u_o": list(u_o), "fine_u": fine_u,
                        "fine": [[pt(u, t) for t in fine_rows] for u in fine_u],
                        "coarse": [pt(u, t_coarse) for u in u_o],
                        "mid": {(j, i): pt(fine_u[F * j + i], t_mid) for j in range(segs) for i in range(1, F)}}
    a_grid = np.linspace(0, 1, 21)

    def alphas(k, u):
        uc = min(max(u, ur[0]), ur[1])
        gc = sample(oL, u_lo, uc) - sample(oU, u_up, uc)
        gg = max(float(np.dot(gc, gc)), 1e-12)
        return (float(np.clip(np.dot(sample(offU[k], u_up, uc), gc) / gg, -0.5, 1.5)),
                float(np.clip(np.dot(sample(offL[k], u_lo, uc), -gc) / gg, -0.5, 1.5)))
    alpha_tab = {k: np.array([alphas(k, u) for u in a_grid]) for k in off}
    for name in ("upper", "lower"):
        st = strips[name]
        new_margin_local[name] = np.array([np.array(mwi @ Vector((c[0]["x"], c[0]["y"], c[0]["z"]))) for c in st["fine"]])
        new_margin_local[f"u_{name}"] = st["fine_u"]
    # --- topology --------------------------------------------------------------------------------
    old_dir = None
    a0, b0 = outer[0], outer[1]
    for i in region:
        vs = list(me.polygons[i].vertices)
        if a0 in vs and b0 in vs:
            old_dir = vs[(vs.index(a0) + 1) % len(vs)] == b0
    interior = {v for i in region for v in me.polygons[i].vertices} - set(outer)
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    pl = bm.verts.layers.int.get(E.PATCH_ATTR)
    uvl = bm.loops.layers.uv.active
    dl = bm.verts.layers.deform.verify()
    shape_layers = {kb.name: bm.verts.layers.shape.get(kb.name) for kb in keys}
    gidx = {g.name: g.index for g in face.vertex_groups}
    rot = mwi.to_3x3()
    outer_bv = {v: bm.verts[v] for v in outer}
    uv_of = {}
    for v, bv in outer_bv.items():
        lp = next((lp for lp in bv.link_loops if lp.face.index not in region and lp.face.material_index == si), None)
        lp = lp or next(lp for lp in bv.link_loops if lp.face.index in region)
        uv_of[bv] = Vector(lp[uvl].uv)
        bv[pl] = SIDES[side]
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in region], context="FACES_ONLY")
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in interior if bm.verts[i].is_valid], context="VERTS")

    def make_vert(c, name):
        p = Vector((c["x"], c["y"], c["z"]))
        bv = bm.verts.new(mwi @ p)
        bv[pl] = SIDES[side]
        hit, uv, wt, offs = tr.project(0, 0, Vector(c["q"].tolist()))
        w = 1.0 - (3 * c["t"] ** 2 - 2 * c["t"] ** 3)  # smoothstep falloff: margin 1 -> outer row 0
        for kname, layer in shape_layers.items():
            if kname == keys[0].name:
                bv[layer] = bv.co
                continue
            new_o, old_o = margin_motion(name, kname, c["u"])
            bv[layer] = bv.co + rot @ Vector(offs[kname]) + Vector((w * (new_o - old_o)).tolist())
        tot = sum(wt.values())
        for g, val in wt.items():
            if val / tot > 1e-4:
                bv[dl][gidx[g]] = val / tot
        uv_of[bv] = uv
        return bv
    # canthus columns (first / last) are shared by both strips: key = (outer vertex, t)
    shared = {}

    def get(c, ov_end, name):
        if ov_end is None:
            return make_vert(c, name)
        key = (ov_end, round(c["t"], 6))
        if key not in shared:
            shared[key] = make_vert(c, name)
        return shared[key]
    faces = []

    def quad(name, vs):
        f = bm.faces.new(vs)
        f.material_index = si
        f.smooth = True
        faces.append((name, f))
    grids = {}
    for name, st in strips.items():
        oarc, F = st["outer"], st["F"]
        nf = len(st["fine_u"])
        fine = [[get(c, oarc[0] if i == 0 else (oarc[-1] if i == nf - 1 else None), name) for c in col]
                for i, col in enumerate(st["fine"])]
        coarse = [get(c, oarc[j] if j in (0, len(oarc) - 1) else None, name) for j, c in enumerate(st["coarse"])]
        mid = {k: make_vert(c, name) for k, c in st["mid"].items()}
        for i in range(nf - 1):  # fine rows
            for k in range(len(fine_rows) - 1):
                quad(name, [fine[i][k], fine[i + 1][k], fine[i + 1][k + 1], fine[i][k + 1]])
        last = len(fine_rows) - 1
        for j in range(len(oarc) - 1):  # transition fine -> coarse (3:1 all-quad, or 1:1)
            a = [fine[F * j + i][last] for i in range(F + 1)]
            b0, b1 = coarse[j], coarse[j + 1]
            if F == 1:
                quad(name, [a[0], a[1], b1, b0])
            else:
                m1, m2 = mid[(j, 1)], mid[(j, 2)]
                quad(name, [a[0], a[1], m1, b0])
                quad(name, [a[1], a[2], m2, m1])
                quad(name, [a[2], a[3], b1, m2])
                quad(name, [m1, m2, b1, b0])
            quad(name, [b0, b1, outer_bv[oarc[j + 1]], outer_bv[oarc[j]]])
        grids[name] = fine
    # lid thickness: a wall continues each strip inward/backward from the margin (t < 0), so oblique
    # views into the opening meet the inside of the lid instead of the head interior (method 3)
    wall_of = {}
    back = rot @ Vector((0.0, -P["wall"]["depth_m"], 0.0))
    for name, fine in grids.items():
        ring = []
        for i, col in enumerate(fine):
            m = col[0]
            if m not in wall_of:
                wv = bm.verts.new(m.co + back)
                wv[pl] = SIDES[side] + WALL_OFFSET
                for kname, layer in shape_layers.items():
                    wv[layer] = m[layer] + back
                for g_, val in m[dl].items():
                    wv[dl][g_] = val
                uv_of[wv] = uv_of[m] + (uv_of[m] - uv_of[col[1]]) * P["wall"]["uv_extrapolation"]
                wall_of[m] = wv
            ring.append(wall_of[m])
        for i in range(len(fine) - 1):
            quad(name, [ring[i], ring[i + 1], fine[i + 1][0], fine[i][0]])
    # orientation: each strip separately must agree with the old winding on the shared outer edges
    for name in grids:
        fs = [f for n_, f in faces if n_ == name]
        outer_set = set(outer_bv.values())
        fset = set(fs)
        e0 = next(e for f in fs for e in f.edges if len(e.link_faces) == 2 and all(v in outer_set for v in e.verts)
                  and any(lf not in fset for lf in e.link_faces))
        f0 = next(lf for lf in e0.link_faces if lf in fset)
        other = next(f for f in e0.link_faces if f is not f0)
        va, vb = e0.verts

        def forward(f):
            vs = list(f.verts)
            return vs[(vs.index(va) + 1) % len(vs)] is vb
        if forward(f0) == forward(other):
            bmesh.ops.reverse_faces(bm, faces=fs)
    for _, f in faces:
        for lp in f.loops:
            lp[uvl].uv = uv_of[lp.vert]
    canthus_pos = {"inner": tuple(mw @ grids["upper"][0][0].co), "outer": tuple(mw @ grids["upper"][-1][0].co)}
    margin = {}
    for name in ("upper", "lower"):
        margin[name] = {"new": [tuple(mw @ col[0].co) for col in grids[name]],
                        "old": [tuple(col[0]["q"]) for col in strips[name]["fine"]],
                        "u": strips[name]["fine_u"],
                        "delta": {k: np.array([(lambda m: m[0] - m[1])(margin_motion(name, k, u)) for u in strips[name]["fine_u"]])
                                  for k in off}}
    new_vs = {f_.verts[i] for _, f_ in faces for i in range(4)} - set(outer_bv.values())
    n_new = len(new_vs)
    bm.to_mesh(me)
    bm.free()
    me.update()
    rec = {"region_faces": len(region), "removed_vertices": len(interior), "outer_loop": len(outer),
           "old_rim_loop": len(inner), "outer_columns": {k: len(st["outer"]) for k, st in strips.items()},
           "margin_columns": {k: len(v) for k, v in grids.items()}, "reduction": {k: f"{st['F']}:1" for k, st in strips.items()},
           "rows": len(rows),
           "new_vertices": n_new, "new_faces": len(faces), "old_winding_forward": bool(old_dir),
           "canthus_vertex_world": {k: [round(c, 6) for c in v] for k, v in canthus_pos.items()},
           "canthus_target_xz": {"inner": tgt["canthus_inner_xz"], "outer": tgt["canthus_outer_xz"]}}
    rec["wall_vertices"] = len(wall_of)
    return rec, {"margin": margin, "alpha_grid": a_grid, "alpha": alpha_tab}


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def rotate(p, a0, axis, phi):
    v = p - a0
    c, s_ = math.cos(phi), math.sin(phi)
    return a0 + v * c + np.cross(axis, v) * s_ + axis * np.dot(axis, v) * (1 - c)


def author_lid_keys(face, data, P):
    """Method 3: lid-closing / -opening keys re-authored as a rotation about the canthal axis.
    The canthi lie on the axis and stay fixed. Per key and column the upper (lower) margin turns
    by alpha_U(u) (alpha_L(u)) of the angle between the new upper and lower margin; the angle
    falls off smoothly with distance from the margin (F) and replaces the old motion inside D1
    (blend to the old motion between D1 and D2)."""
    me = face.data
    keys = me.shape_keys.key_blocks
    mw = np.array(face.matrix_world)
    rot_l = np.linalg.inv(mw[:3, :3])
    base = np.array([v.co[:] for v in keys[0].data])
    W = base @ mw[:3, :3].T + mw[:3, 3]
    absk = {kb.name: np.array([v.co[:] for v in kb.data]) for kb in keys[1:]}
    attr = me.attributes["elm_patch"].data
    skip_slots = {i for i, s in enumerate(face.material_slots) if s.material and any(k in s.material.name for k in P["closure"]["skip_materials"])}
    vslot = {}
    for poly in me.polygons:
        for v in poly.vertices:
            vslot.setdefault(v, set()).add(poly.material_index)
    rec = {}
    for side in ("R", "L"):
        d = data[side]
        up = np.array(d["margin"]["upper"]["new"]); lo = np.array(d["margin"]["lower"]["new"])
        c0, c1 = up[0], up[-1]
        axis = (c1 - c0) / np.linalg.norm(c1 - c0)
        span = float(np.linalg.norm(c1 - c0))
        # pivot axis through the eyeball centre: the canthal axis moved straight back (attempt B2;
        # B1 pivoted on the surface line -> 166 deg sweeps and folds)
        a0 = c0 + np.array([0.0, -P["closure"]["pivot_back_m"], 0.0])
        uu, ul = arc_param(up), arc_param(lo)
        grid = d["alpha_grid"]

        def foot(p):
            return a0 + axis * np.dot(p - a0, axis)
        theta = []
        for g in grid:
            U, L = sample(up, uu, g), sample(lo, ul, g)
            v1, v2 = U - foot(U), L - foot(L)
            v1 = v1 - axis * np.dot(v1, axis); v2 = v2 - axis * np.dot(v2, axis)
            theta.append(math.atan2(float(np.dot(axis, np.cross(v1, v2))), float(np.dot(v1, v2))) if np.linalg.norm(v1) > 1e-7 and np.linalg.norm(v2) > 1e-7 else 0.0)
        theta = np.array(theta)
        mid = (grid > 0.3) & (grid < 0.7)
        close_keys = [k for k, tab in d["alpha"].items() if float(np.abs(tab[mid]).sum(1).max()) > P["closure"]["key_alpha_threshold"]]
        patch_id = SIDES[side]
        pv = [i for i, a_ in enumerate(attr) if a_.value == patch_id]
        polys = {nm: (np.array(d["margin"][nm]["new"]), np.array(d["margin"][nm]["u"])) for nm in ("upper", "lower")}

        def near(p):
            best = None
            for nm, (pts, u_of) in polys.items():
                u, dist = nearest_param(pts, u_of, np.array([p[0], p[2]]))
                if best is None or dist < best[1]:
                    best = (nm, dist)
            return best
        D1 = P["closure"]["D1_m"]  # bounded (B1 used the patch extent, 30.7 mm, and reached the mouth)
        D2 = D1 + P["closure"]["blend_width_m"]
        z_guard = float(lo[:, 2].min()) - P["closure"]["mouth_guard_m"]
        cand = [i for i in range(len(W)) if (W[i][0] > M3.MID_X) == (side == "R") and attr[i].value in (0, patch_id, patch_id + WALL_OFFSET)
                and not (vslot.get(i, set()) & skip_slots)]
        verts, info = [], []
        for i in cand:
            nm, dist = near(W[i])
            if dist >= D2 or W[i][2] < z_guard:
                continue
            u = float(np.clip(np.dot(W[i] - c0, axis) / span, 0, 1))
            verts.append(i)
            info.append((nm, dist, u))
        for k in close_keys:
            tab = d["alpha"][k]
            aU = np.interp(np.array([x[2] for x in info]), grid, tab[:, 0])
            aL = np.interp(np.array([x[2] for x in info]), grid, tab[:, 1])
            ssum = aU + aL
            sc = np.where(ssum > 0.9, P["closure"]["closed_sum"] / np.maximum(ssum, 1e-9), 1.0)  # closed -> slight overlap
            new = absk[k].copy()
            for j, i in enumerate(verts):
                nm, dist, u = info[j]
                th = float(np.interp(u, grid, theta))
                phi = (aU[j] * sc[j] * th) if nm == "upper" else (-aL[j] * sc[j] * th)
                F = 1 - float(smoothstep(0, D2, dist))
                B = 1 - float(smoothstep(D1, D2, dist))
                off_w = rotate(W[i], a0, axis, phi * F) - W[i]
                new[i] = base[i] + rot_l @ off_w + (1 - B) * (absk[k][i] - base[i])
            absk[k] = new
        rec[side] = {"close_keys": close_keys, "D1_mm": round(D1 * 1000, 3), "D2_mm": round(D2 * 1000, 3),
                     "vertices": len(verts), "theta_full_deg_max": round(float(np.degrees(np.abs(theta).max())), 3)}
    for kb in keys[1:]:
        kb.data.foreach_set("co", absk[kb.name].ravel())
    me.update()
    return rec


def retarget_cards(face, data, materials):
    """Move eyeliner / eyelash / EyeExtra vertices with the margin displacement (per key faded by 1 - c_k)."""
    me = face.data
    mw = face.matrix_world
    mwi = mw.inverted()
    slots = {i for i, s in enumerate(face.material_slots) if s.material and any(k in s.material.name for k in materials)}
    verts = sorted({v for p in me.polygons if p.material_index in slots for v in p.vertices})
    keys = me.shape_keys.key_blocks
    base = np.array([v.co[:] for v in keys[0].data])
    absk = {kb.name: np.array([v.co[:] for v in kb.data]) for kb in keys[1:]}
    rot = np.array(mwi.to_3x3())
    moved = 0.0
    new_base = base.copy()
    new_k = {k: a.copy() for k, a in absk.items()}
    for v in verts:
        w = np.array(mw @ Vector(base[v]))
        side = "R" if w[0] > M3.MID_X else "L"
        d_ = data[side]
        best = None
        for name in ("upper", "lower"):
            m = d_["margin"][name]
            old = np.array(m["old"]); u_of = np.array(m["u"])
            u, dist = nearest_param(old, u_of, np.array([w[0], w[2]]))
            if best is None or dist < best[1]:
                best = (name, dist, u)
        name, _, u = best
        m = d_["margin"][name]
        disp = sample(np.array(m["new"]) - np.array(m["old"]), np.array(m["u"]), u)
        dl = rot @ disp
        new_base[v] = base[v] + dl
        moved = max(moved, float(np.linalg.norm(disp)))
        for k in new_k:
            new_k[k][v] = absk[k][v] + dl + sample(m["delta"][k], np.array(m["u"]), u)
    keys[0].data.foreach_set("co", new_base.ravel())
    me.vertices.foreach_set("co", new_base.ravel())
    for kb in keys[1:]:
        kb.data.foreach_set("co", new_k[kb.name].ravel())
    me.update()
    return {"card_vertices": len(verts), "max_displacement_mm": round(moved * 1000, 3)}


def build(P05, P04, nrec, targets):
    """On top of E.build_base(P04). Returns (record, eyes object, per-side margin data)."""
    face = bpy.data.objects["Face"]
    me = face.data
    si = M3.slot_index(face, "Face_00_SKIN")
    nose_pos = {E.pkey(me.vertices[i].co) for i, a in enumerate(me.attributes[E.PATCH_ATTR].data) if a.value == 4}
    poly_n = {}
    for poly in me.polygons:
        ck = tuple(sorted(E.pkey(me.vertices[v].co) for v in poly.vertices))
        poly_n[ck] = {E.pkey(me.vertices[v].co): tuple(me.corner_normals[li].vector) for v, li in zip(poly.vertices, poly.loop_indices)}
    L = nrec["baseline"]["landmarks"]
    U = nrec["baseline"]["normalisation"]["unit_U_m"]
    specs = E.ellipses(P04, L)
    rec, data = {"nose": {"hash_verified": True, "design_value": P04["locked_nose"]["design_value"]}}, {}
    for side in ("R", "L"):
        tr = E.Transfer(face, si)  # old surface incl. previous edits of the other side (disjoint regions)
        rec[f"lid_{side}"], data[side] = build_lid(face, side, specs[f"lid_{side}"], targets[side], P05, tr)
    rec["mouth"] = {"built": False, "status": "OUT_OF_SCOPE (separate task)"}
    rec["cards_retarget"] = retarget_cards(face, data, P05["cards"]["materials"])
    rec["lid_keys"] = author_lid_keys(face, data, P05)
    # eyes: unchanged #316 material, surface behind the NEW rim, pupil at the Layer 0 target
    ep = dict(P04["eyes"])
    ep["surface_radius_m"] = P05["eyes"]["surface_radius_m"]
    rec["removed_eye_plate_faces"] = E.remove_face_materials(face, ep["remove_face_materials"])
    rims, opening = {}, {}
    for side in ("R", "L"):
        pts = [Vector(p) for nm in ("upper", "lower") for p in data[side]["margin"][nm]["new"]]
        rims[side] = pts
        xs, zs = [p.x for p in pts], [p.z for p in pts]
        opening[side] = (min(xs), max(xs), min(zs), max(zs))
    fr_in, fr_top = {}, {}
    for side in ("R", "L"):
        x0, x1, z0, z1 = opening[side]
        inner_x, outer_x = (x0, x1) if side == "R" else (x1, x0)
        px, pz = targets[side]["pupil_xz"]
        fr_in[side] = (px - inner_x) / (outer_x - inner_x)
        fr_top[side] = (z1 - pz) / (z1 - z0)
    ep["pupil_frac_from_inner_corner"], ep["pupil_frac_from_top"] = fr_in, fr_top
    arm = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
    eyes = E.build_eyes(face, arm, ep, rims, opening, U)
    rec["eyes"] = {"object": eyes.name, "vertices": len(eyes.data.vertices), "faces": len(eyes.data.polygons),
                   "material": eyes.data.materials[0].name, "edge_clipped_samples": int(eyes["edge_clipped_samples"]),
                   "pupil_target_xz": {s: targets[s]["pupil_xz"] for s in ("R", "L")}}
    # custom normals: untouched corners restored; lid strips, nose and changed faces automatic
    attr = me.attributes[E.PATCH_ATTR].data
    patch = {i for i, a in enumerate(attr) if a.value != 0}
    corner = [None] * len(me.loops)
    for poly in me.polygons:
        ck = tuple(sorted(E.pkey(me.vertices[v].co) for v in poly.vertices))
        old = poly_n.get(ck)
        in_patch = all(v in patch for v in poly.vertices) or any(E.pkey(me.vertices[v].co) in nose_pos for v in poly.vertices)
        for v, li in zip(poly.vertices, poly.loop_indices):
            corner[li] = old[E.pkey(me.vertices[v].co)] if old is not None and not in_patch else (0.0, 0.0, 0.0)
    me.normals_split_custom_set(corner)
    rec["cards"] = E.rebind_cards(face, dict(P04["cards"], iterations=P05["cards"]["rebind_iterations"]), X.face_slots(face))
    return rec, eyes, data

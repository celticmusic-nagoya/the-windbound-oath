"""LIND-BUILD-01 roof module: rafters + battens + individually varied blue-gray slates + ridge.

Roof-local frame: ridge along +X at y=0; side sigma=-1 slopes down toward -Y, +1 toward +Y.
`s` = horizontal distance ridge -> outer wall face, `he` = height where the rafter underside
meets the outer wall face. ML maps roof-local -> building space.

Every slate gets its own width/length/thickness/tilt/rotation/chipped corners/colour value
(piece_rand) — the causal fix for stopped family H-A (672 identical slates).
"""
from __future__ import annotations

import math

from mathutils import Matrix, Vector

from kit_geometry import box


def _hash01(*vals):
    h = 0
    for v in vals:
        h = (h * 1000003) ^ int(v * 1000.0 + 7919)
        h &= 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 0x5BD1E995) & 0xFFFFFFFF
    h ^= h >> 15
    return (h & 0xFFFF) / 65535.0


def gable_roof(parts, ML, x0, x1, s, he, pitch_deg, eave, verge, cfg, rng, mats,
               sides=(-1, 1), skip=None, state="peaceful", ridge=True, rafters=True,
               stats=None, burn_keep=0.28):
    """parts: dict with MeshBuilders 'slates', 'roof_timber', 'ridge'.
    x0/x1: wall-plate extent of the roof (rafters inside, slates extend by `verge`).
    skip(p_building)->bool removes pieces (chimneys, dormers, valleys, intersecting roofs)."""
    rc = cfg["roof"]
    p = math.radians(pitch_deg)
    rw, rh = rc["rafter_section"]
    bw, bh = rc["batten_section"]
    burning = state in ("burning", "ruin")
    stats = stats if stats is not None else {}
    X = Vector((1, 0, 0))
    for sig in sides:
        up = Vector((0, -sig * math.cos(p), math.sin(p)))     # up-slope
        nrm = Vector((0, sig * math.sin(p), math.cos(p)))      # outward roof normal
        B0 = Vector((0, sig * (s + eave * math.cos(p)), he - eave * math.sin(p)))  # rafter underside at eave end
        L = eave + s / math.cos(p)                              # slope length eave end -> ridge line
        # ---------------------------------------------------------- rafters
        if rafters:
            n_r = max(2, int(round((x1 - x0) / rc["rafter_spacing"])) + 1)
            for i in range(n_r):
                x = x0 + rw / 2 + (x1 - x0 - rw) * i / (n_r - 1)
                length = L
                mat = mats["timber"]
                if burning:
                    mat = mats["charred"]
                    hb = _hash01(x, sig, 3)
                    if hb < 0.30:
                        length = L * (0.35 + 0.5 * hb / 0.30)   # broken rafter
                c = B0 + up * (length / 2) + nrm * (rh / 2) + X * x
                if skip and skip(ML @ c):
                    continue
                box(parts["roof_timber"], c, (rw, length, rh), mat, axes=(X, up, nrm),
                    rand=rng.random(), ML=ML, uv_scale=1.2)
                stats["rafters"] = stats.get("rafters", 0) + 1
        # ---------------------------------------------------------- battens
        a = 0.12
        while a < L - 0.05:
            if not (burning and _hash01(a, sig, 5) < 0.55):
                c = B0 + up * a + nrm * (rh + bh / 2) + X * ((x0 + x1) / 2)
                box(parts["roof_timber"], c, (x1 - x0 + 2 * verge, bw, bh),
                    mats["charred"] if burning else mats["timber"], axes=(X, up, nrm),
                    rand=rng.random(), ML=ML, uv_scale=1.2)
                stats["battens"] = stats.get("battens", 0) + 1
            a += rc["slate_gauge"]
        # ---------------------------------------------------------- slates
        base_off = rh + bh
        gauge = rc["slate_gauge"]
        k = 0
        a_low = -0.02
        xa, xb = x0 - verge, x1 + verge
        while a_low < L - 0.06:
            x = xa - (rng.uniform(0.0, rc["slate_width"][1]) if k % 2 else 0.0)
            while x < xb - 0.02:
                w = rng.uniform(*rc["slate_width"])
                gap = rng.uniform(0.004, 0.012)
                sx0, sx1 = max(x, xa), min(x + w, xb)
                x += w + gap
                if sx1 - sx0 < 0.06:
                    continue
                ln = rng.uniform(*rc["slate_length"])
                a0 = a_low + rng.uniform(-0.012, 0.012)
                a1 = min(a0 + ln, L + 0.03)
                t = rng.uniform(*rc["slate_thickness"])
                lift_lo = (0.9 if k == 0 else 2.0) * 0.017
                rot = math.radians(rng.uniform(-1.2, 1.2))
                pr = rng.random()
                cx, ca = (sx0 + sx1) / 2, (a0 + a1) / 2
                # burning: keep only scattered clusters, mostly low on the slope
                if burning:
                    keep = _hash01(round(cx * 1.3), round(ca * 2.2), sig) < burn_keep * (1.4 - ca / L)
                    if not keep:
                        continue
                cen_b = ML @ (B0 + up * ca + nrm * (base_off + lift_lo / 2) + X * cx)
                if skip and skip(cen_b):
                    continue
                c1 = rng.uniform(0.0, 0.035) if rng.random() < 0.6 else 0.0
                c2 = rng.uniform(0.0, 0.035) if rng.random() < 0.6 else 0.0
                outline = [(sx0 + c1, a0), (sx1 - c2, a0), (sx1, a0 + c2 * 0.8), (sx1, a1), (sx0, a1), (sx0, a0 + c1 * 0.8)]
                cr, sr = math.cos(rot), math.sin(rot)
                pts_lo, pts_hi = [], []
                for (u, v) in outline:
                    du, dv = u - cx, v - ca
                    u2, v2 = cx + du * cr - dv * sr, ca + du * sr + dv * cr
                    f = min(1.0, max(0.0, (v2 - a0) / max(1e-3, (a1 - a0))))
                    lift = lift_lo * (1 - f) + rng.uniform(-0.002, 0.002)
                    q = B0 + up * v2 + nrm * (base_off + lift) + X * u2
                    pts_lo.append(ML @ q)
                    pts_hi.append(ML @ (q + nrm * t))
                uvo = (pr * 13.7 % 1.0, pr * 7.3 % 1.0)
                uv = [((u - sx0) * 2.0 + uvo[0], (v - a0) * 2.0 + uvo[1]) for (u, v) in outline]
                mb = parts["slates"]
                mb.poly(pts_hi, mats["slate"], uvs=uv, rand=pr)
                mb.poly(list(reversed(pts_lo)), mats["slate"], uvs=list(reversed(uv)), rand=pr)
                n = len(outline)
                for i in range(n):
                    j = (i + 1) % n
                    mb.poly([pts_lo[i], pts_lo[j], pts_hi[j], pts_hi[i]], mats["slate"],
                            uvs=[uv[i], uv[j], (uv[j][0], uv[j][1] + 0.02), (uv[i][0], uv[i][1] + 0.02)], rand=pr)
                stats["slates"] = stats.get("slates", 0) + 1
                stats.setdefault("_slate_dims", set()).add((round(sx1 - sx0, 3), round(a1 - a0, 3), round(t, 4)))
            k += 1
            a_low = k * gauge - 0.02
        # ---------------------------------------------------------- verge boards
        if not burning:
            for xv in (xa + 0.05, xb - 0.05):  # slates project ~0.03-0.06 past bargeboard (contract)
                c = B0 + up * (L / 2) + nrm * (rh + bh - rc["bargeboard"][1] / 2 + 0.01) + X * xv
                if skip and skip(ML @ c):
                    continue
                bgw, bgh = rc["bargeboard"]
                box(parts["roof_timber"], c, (bgw, L + 0.02, bgh), mats["timber"], axes=(X, up, nrm),
                    rand=rng.random(), ML=ML, uv_scale=1.2)
    # -------------------------------------------------------------- ridge
    top = rh + bh + 0.04
    ridge_z = he + s * math.tan(p) + top / math.cos(p)
    if ridge and len(sides) == 2:
        box(parts["roof_timber"], Vector(((x0 + x1) / 2, 0, he + s * math.tan(p) + 0.05)),
            (x1 - x0, 0.05, 0.22), mats["charred"] if burning else mats["timber"], ML=ML, rand=0.3)
        if not burning:
            x = x0 - verge
            while x < x1 + verge - 0.05:
                ln = rng.uniform(*rc["ridge_piece_len"])
                xe = min(x + ln, x1 + verge)
                wing = 0.19
                th = 0.045
                dz = rng.uniform(-0.006, 0.006)
                # inverted-V ridge stone cross-section (y, z) extruded along x
                cs = [(-wing * math.cos(p), -wing * math.sin(p)), (0.0, th * 0.6), (wing * math.cos(p), -wing * math.sin(p)),
                      (wing * math.cos(p), -wing * math.sin(p) + th), (0.0, th * 1.9), (-wing * math.cos(p), -wing * math.sin(p) + th)]
                pts0 = [ML @ Vector((x + 0.004, y, ridge_z + z + dz)) for (y, z) in cs]
                pts1 = [ML @ Vector((xe - 0.004, y, ridge_z + z + dz)) for (y, z) in cs]
                pr = rng.random()
                if not (skip and skip(ML @ Vector(((x + xe) / 2, 0, ridge_z)))):
                    mb = parts["ridge"]
                    mb.poly(pts0, mats["ridge"], rand=pr)
                    mb.poly(list(reversed(pts1)), mats["ridge"], rand=pr)
                    for i in range(6):
                        j = (i + 1) % 6
                        mb.poly([pts0[i], pts1[i], pts1[j], pts0[j]], mats["ridge"], rand=pr)
                    stats["ridge_pieces"] = stats.get("ridge_pieces", 0) + 1
                x = xe + 0.006
    return {"ridge_z": he + s * math.tan(p), "top_offset": (rh + bh) / math.cos(p)}


def roof_top_z(y_abs, s, he, pitch_deg, cfg):
    """Height of the slate-bed plane at horizontal distance y_abs from ridge (building space)."""
    rc = cfg["roof"]
    p = math.radians(pitch_deg)
    return he + (s - y_abs) * math.tan(p) + (rc["rafter_section"][1] + rc["batten_section"][1]) / math.cos(p)


def ML_from(origin, xdir, ydir):
    xd = Vector(xdir).normalized()
    yd = Vector(ydir).normalized()
    zd = xd.cross(yd)
    if zd.z < 0:
        zd = -zd
    M = Matrix.Identity(4)
    for r in range(3):
        M[r][0], M[r][1], M[r][2], M[r][3] = xd[r], yd[r], zd[r], origin[r]
    return M

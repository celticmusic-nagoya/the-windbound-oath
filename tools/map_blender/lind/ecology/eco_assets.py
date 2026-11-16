"""LIND-ECO-01 procedural asset generators (candidate, not adopted art).

Every generator: fn(seed, **preset) -> (MeshAcc, info_dict). Pure-python geometry so that
the result is bit-stable for a given seed (geometry hash recorded in the manifest).
Species are generic temperate forms; no species is claimed as canon.
"""
import math

import bpy
from mathutils import Matrix, Vector

from eco_lib import MeshAcc, jitter_col, lerp, new_rng

UP = Vector((0, 0, 1))


def _perp(v):
    ref = UP if abs(v.z) < 0.92 else Vector((1, 0, 0))
    return v.cross(ref).normalized()


# =============================================================================== TREES
TREE_PRESETS = {
    # generic broadleaf village / forest-edge tree
    "deciduous": dict(trunk_len=2.6, trunk_r=0.19, lean=0.06, scaffolds=4, scaffold_at=(0.55, 1.0),
                      scaffold_len=(1.7, 2.3), angle=(28, 48), depth=4, len_decay=(0.62, 0.78), gravi=0.10,
                      card_size=(0.45, 0.62), card_spacing=0.09, tex="broadleaf",
                      tint_in=0.55, tint_out=1.08, bark=(0.20, 0.17, 0.14), apples=0, side_shoots=3,
                      droop=0.0, sides0=12),
    # open-centre orchard apple: short trunk, wide low scaffolds, drooping fruiting wood
    "apple": dict(trunk_len=1.3, trunk_r=0.14, lean=0.05, scaffolds=5, scaffold_at=(0.75, 1.0),
                  scaffold_len=(1.5, 1.9), angle=(48, 64), depth=4, len_decay=(0.6, 0.74), gravi=0.02,
                  card_size=(0.34, 0.46), card_spacing=0.08, tex="apple",
                  tint_in=0.6, tint_out=1.1, bark=(0.24, 0.19, 0.15), apples=90, side_shoots=0,
                  droop=0.16, sides0=10),
    # taller forest tree toward Moss Forest (SE)
    "forest_tall": dict(trunk_len=3.6, trunk_r=0.24, lean=0.03, scaffolds=5, scaffold_at=(0.45, 1.0),
                        scaffold_len=(2.2, 3.0), angle=(24, 42), depth=4, len_decay=(0.62, 0.76), gravi=0.14,
                        card_size=(0.5, 0.7), card_spacing=0.1, tex="broadleaf",
                        tint_in=0.45, tint_out=0.95, bark=(0.17, 0.15, 0.13), apples=0, side_shoots=5,
                        droop=0.0, sides0=12),
}


def paint_leaf_spray(path, seed, kind="broadleaf"):
    """Paint an RGBA leaf-spray texture (twig + ~22 leaves) for alpha cards. Transparent texels
    carry the mean leaf colour (bleed) to avoid light fringes under filtering/mips."""
    import numpy as np
    from PIL import Image
    rng = new_rng(seed, "leafspray:" + kind)
    S = 512
    rgb = np.zeros((S, S, 3), np.float32)
    a = np.zeros((S, S), np.float32)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    base_c = np.array((0.075, 0.17, 0.035)) if kind == "broadleaf" else np.array((0.09, 0.19, 0.04))
    # twig path
    bend = 30 * (1 if rng.random() < 0.5 else -1)
    tw = [(256 + bend * math.sin(t * 2.2) * t, 505 - 360 * t) for t in [i / 40 for i in range(41)]]
    leaves = []
    n = 22 if kind == "broadleaf" else 26
    for k in range(n):
        t = 0.12 + 0.88 * k / (n - 1)
        i = int(t * 40)
        x0, y0 = tw[i]
        side = 1 if k % 2 == 0 else -1
        ang = math.radians(-90 + side * rng.uniform(48, 78) * (1 - 0.45 * t))
        L = (rng.uniform(105, 140) if kind == "broadleaf" else rng.uniform(88, 115)) * (1.0 - 0.4 * t)
        leaves.append((x0, y0, ang, L, rng.uniform(0.85, 1.15), rng.uniform(0.4, 0.5)))
    xe, ye = tw[-1]
    leaves.append((xe, ye, math.radians(-90 + rng.uniform(-10, 10)), 95, 1.05, 0.45))
    # twig first (leaves overlap it)
    for i in range(40):
        (x0, y0), (x1, y1) = tw[i], tw[i + 1]
        for j in range(6):
            f = j / 6
            cx, cy = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
            r = 5.0 * (1 - (i + f) / 46)
            m = (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
            rgb[m] = (0.16, 0.11, 0.07)
            a[m] = 1
    for (x0, y0, ang, L, br, wr) in leaves:
        ca, sa = math.cos(ang), math.sin(ang)
        petiole = 10
        u = (xx - x0) * ca + (yy - y0) * sa - petiole
        v = -(xx - x0) * sa + (yy - y0) * ca
        un = np.clip(u / L, 0, 1)
        half = L * wr * 0.5 * np.maximum(np.sin(np.pi * np.clip(un, 0, 1) ** 0.85), 0) ** 0.9 * (1 - 0.25 * un)
        inside = (u > 0) & (u < L) & (np.abs(v) < half)
        shade = br * (0.8 + 0.35 * un) * np.where(v > 0, 1.08, 0.92)
        col = base_c[None, None, :] * shade[..., None]
        rib = inside & (np.abs(v) < 1.3)
        edge = inside & (np.abs(v) > half - 2.0)
        rgb[inside] = col[inside]
        rgb[rib] = col[rib] * 1.45
        rgb[edge] = col[edge] * 0.8
        a[inside] = 1
        # petiole
        pm = (u > -petiole) & (u <= 0) & (np.abs(v) < 1.5)
        rgb[pm] = (0.14, 0.17, 0.05)
        a[pm] = 1
    mean = rgb[a > 0].mean(axis=0)
    rgb[a == 0] = mean
    img = np.dstack([np.clip(rgb, 0, 1) ** (1 / 2.2) * 255, a * 255]).astype(np.uint8)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(img, "RGBA").save(path, optimize=False)
    return path


def _leaf_card(acc, base, up, normal, size, tint, ww, mat):
    """V-folded alpha card (4 tris); texture twig base sits at the card's bottom-centre."""
    up = up.normalized()
    sd = up.cross(normal).normalized()
    nb = sd.cross(up).normalized()
    h, w = size, size * 0.5
    back = nb * (-0.18 * w)
    droop = nb * (-0.12 * h)
    B = acc.vert(base, tint, ww)
    T = acc.vert(base + up * h + droop, tint, min(1.0, ww + 0.1))
    LB = acc.vert(base - sd * w + back, tint, ww)
    LT = acc.vert(base - sd * w + up * h + back + droop, tint, min(1.0, ww + 0.1))
    RB = acc.vert(base + sd * w + back, tint, ww)
    RT = acc.vert(base + sd * w + up * h + back + droop, tint, min(1.0, ww + 0.1))
    acc.face((LB, B, T, LT), mat, uv=[(0, 0), (0.5, 0), (0.5, 1), (0, 1)])
    acc.face((B, RB, RT, T), mat, uv=[(0.5, 0), (1, 0), (1, 1), (0.5, 1)])


def _leaf(acc, base, direction, normal, L, W, col, ww, mat):
    """8-tri leaf with petiole gap, raised midrib and curled tip."""
    d = direction.normalized()
    s = d.cross(normal).normalized()
    n = s.cross(d).normalized()

    def P(x, y, z):
        return base + s * (x * W) + d * (y * L) + n * (z * L)
    dark = tuple(c * 0.8 for c in col)
    v = [acc.vert(P(0, 0.08, 0), dark, ww),
         acc.vert(P(-0.5, 0.38, -0.03), col, ww), acc.vert(P(0, 0.4, 0.05), col, ww),
         acc.vert(P(0.5, 0.38, -0.03), col, ww),
         acc.vert(P(-0.34, 0.74, -0.02), col, ww), acc.vert(P(0, 0.76, 0.05), col, ww),
         acc.vert(P(0.34, 0.74, -0.02), col, ww), acc.vert(P(0, 1.0, -0.06), col, ww)]
    acc.face((v[0], v[2], v[1]), mat)
    acc.face((v[0], v[3], v[2]), mat)
    acc.face((v[1], v[2], v[5], v[4]), mat)
    acc.face((v[2], v[3], v[6], v[5]), mat)
    acc.face((v[4], v[5], v[7]), mat)
    acc.face((v[5], v[6], v[7]), mat)


def _apple(acc, c, r, col, ww, mat):
    rings, segs = 5, 8
    idx = []
    for i in range(1, rings):
        th = math.pi * i / rings
        row = []
        for j in range(segs):
            ph = math.tau * j / segs
            # slight apple dimple top/bottom
            rr = r * (1.0 - 0.12 * math.cos(th) ** 8)
            p = c + Vector((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th) * 0.92)) * rr
            shade = 0.85 + 0.25 * max(0.0, math.cos(th))
            row.append(acc.vert(p, tuple(min(1, k * shade) for k in col), ww))
        idx.append(row)
    top = acc.vert(c + Vector((0, 0, r * 0.78)), col, ww)
    bot = acc.vert(c - Vector((0, 0, r * 0.82)), col, ww)
    for j in range(segs):
        j2 = (j + 1) % segs
        acc.face((top, idx[0][j], idx[0][j2]), mat)
        acc.face((bot, idx[-1][j2], idx[-1][j]), mat)
        for i in range(rings - 2):
            acc.face((idx[i][j], idx[i + 1][j], idx[i + 1][j2], idx[i][j2]), mat)
    # stalk
    stalk = [c + Vector((0, 0, r * 0.7)), c + Vector((0.005, 0, r * 1.25))]
    acc.tube(stalk, [0.004, 0.003], 3, [(0.25, 0.18, 0.08)] * 2, [ww, ww], mat=0, cap_tip=False)


def build_tree(seed, preset="deciduous"):
    P = TREE_PRESETS[preset]
    rng = new_rng(seed, "tree:" + preset)
    acc = MeshAcc()
    stats = {"branches": 0, "leaf_cards": 0, "apples": 0, "max_depth": P["depth"], "leaf_mode": "alpha_spray_cards", "leaf_texture": P["tex"]}
    bark = P["bark"]
    # first pass: collect branch skeletons (so we can normalise wind weights by path length)
    branches = []  # (pts, radii, depth, path0)

    def grow(start, direction, length, radius, depth, path0):
        nseg = max(3, int(length / 0.22) + (2 if depth == 0 else 0))
        step = length / nseg
        pts, radii = [start.copy()], [radius]
        d = direction.normalized()
        p = start.copy()
        end_r = radius * (0.55 if depth < P["depth"] else 0.25)
        bend_axis = _perp(d)
        for i in range(1, nseg + 1):
            t = i / nseg
            # gravitropism (up) / droop (down at tips) + smooth meander
            g = P["gravi"] * (1.0 - t) - P["droop"] * t * (depth / P["depth"])
            d = (d + UP * g * 0.35 + bend_axis * rng.uniform(-0.12, 0.12)
                 + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.5, 0.5))) * 0.06).normalized()
            p = p + d * step
            pts.append(p.copy())
            radii.append(radius + (end_r - radius) * t ** 0.9)
        branches.append((pts, radii, depth, path0, step))
        if depth >= P["depth"]:
            return
        # children: pipe-model radii, golden-angle azimuths
        if depth == 0:
            k = P["scaffolds"]
            ts = [rng.uniform(*P["scaffold_at"]) for _ in range(k)]
            ts.sort()
        else:
            k = rng.choice((2, 3, 3, 4)) if depth < 3 else rng.choice((2, 3))
            ts = sorted(rng.uniform(0.3, 0.95) for _ in range(k))
        az = rng.uniform(0, math.tau)
        for ci, tc in enumerate(ts):
            i = min(len(pts) - 2, max(1, int(tc * (len(pts) - 1))))
            parent_dir = (pts[i + 1] - pts[i]).normalized()
            az += math.radians(137.5 + rng.uniform(-18, 18))
            ang = math.radians(rng.uniform(*P["angle"]))
            side = _perp(parent_dir)
            side = Matrix.Rotation(az, 3, parent_dir) @ side
            cd = (parent_dir * math.cos(ang) + side * math.sin(ang)).normalized()
            if depth == 0:
                # scaffolds spread out horizontally from the trunk top
                cd = (cd + Vector((cd.x, cd.y, 0)).normalized() * 0.3).normalized()
            clen = length * rng.uniform(*P["len_decay"]) * (1.0 if depth else 0.95)
            if depth == 0:
                clen = rng.uniform(*P["scaffold_len"])
            cr = radii[i] * (0.62 if depth == 0 else rng.uniform(0.55, 0.7))
            grow(pts[i], cd, clen, cr, depth + 1, path0 + step * i)
        # leader continuation for the trunk of forest/deciduous trees
        if depth == 0 and P["side_shoots"]:
            for s in range(P["side_shoots"]):
                i = int(len(pts) * rng.uniform(0.45, 0.7))
                az2 = rng.uniform(0, math.tau)
                parent_dir = (pts[i + 1] - pts[i]).normalized()
                side = Matrix.Rotation(az2, 3, parent_dir) @ _perp(parent_dir)
                cd = (parent_dir * 0.5 + side).normalized()
                grow(pts[i], cd, length * rng.uniform(0.35, 0.5), radii[i] * 0.35, 2, path0 + step * i)

    lean = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized() * P["lean"]
    grow(Vector((0, 0, 0)), (UP + lean).normalized(), P["trunk_len"], P["trunk_r"], 0, 0.0)
    max_path = max(b[3] + b[4] * (len(b[0]) - 1) for b in branches)

    def wwf(path):
        return min(1.0, (path / max_path)) ** 1.6

    leaf_rng = new_rng(seed, "leaves:" + preset)
    crown_c = Vector((0, 0, 0))
    tips = [b[0][-1] for b in branches if b[2] >= P["depth"] - 1]
    for tp in tips:
        crown_c += tp
    crown_c /= max(1, len(tips))
    crown_r = max((tp - crown_c).length for tp in tips) if tips else 1.0
    for pts, radii, depth, path0, step in branches:
        stats["branches"] += 1
        sides = max(3, P["sides0"] - depth * 3) if depth < 3 else 3
        cols, wws = [], []
        rj = []
        for i, p in enumerate(pts):
            # bark: darker at base, a touch of green/lichen on upper sides
            sh = 0.8 + 0.25 * min(1.0, p.z / 3.0)
            cols.append(jitter_col(leaf_rng, tuple(c * sh for c in bark), 0.06))
            wws.append(wwf(path0 + step * i))
            rj.append([1.0 + (0.07 if depth == 0 else 0.03) * math.sin(3 * s + i * 0.7 + depth)
                       for s in range(sides)])
        rr = list(radii)
        if depth == 0:
            # root flare
            for i in range(min(3, len(rr))):
                rr[i] *= 1.0 + 0.55 * (1 - i / 3.0) ** 2
        acc.tube(pts, rr, sides, cols, wws, mat=0, cap_tip=depth >= 2, rjit=rj)
        # leaf-spray alpha cards along the outer two orders (method TREE-L2; single-leaf
        # geometry TREE-L1 gave a see-through crown: 1 self-review FAIL, see attempt ledger)
        if depth >= P["depth"] - 2:
            length = step * (len(pts) - 1)
            dens = {P["depth"]: 1.0, P["depth"] - 1: 0.7}.get(depth, 0.3)
            ncard = max(1, int(length / P["card_spacing"] * dens))
            for li in range(ncard):
                t = leaf_rng.uniform(0.2, 1.0) if li else 1.0
                fi = t * (len(pts) - 1)
                i0 = min(len(pts) - 2, int(fi))
                a = pts[i0].lerp(pts[i0 + 1], fi - i0)
                bd = (pts[i0 + 1] - pts[i0]).normalized()
                rel = (a - crown_c)
                outw = rel.normalized() if rel.length > 1e-3 else UP
                roll = Matrix.Rotation(leaf_rng.uniform(0, math.tau), 3, bd) @ _perp(bd)
                # attempt 2: sprays follow the twig and lift upward; only a small outward component
                # (attempt 1 pointed cards radially -> spiky frond silhouette)
                up = (bd * 0.6 + UP * 0.55 + roll * 0.45 + outw * 0.2).normalized()
                nrm = (UP * 0.7 + outw * 0.5 + roll * 0.3).normalized()
                lightf = max(0.0, min(1.0, 0.35 + 0.65 * rel.length / max(0.01, crown_r))) * \
                    (0.8 + 0.2 * max(-1.0, min(1.0, rel.z / max(0.01, crown_r))))
                tv = P["tint_in"] + (P["tint_out"] - P["tint_in"]) * lightf
                hue = leaf_rng.uniform(-0.06, 0.06)
                tint = (tv * (1 + hue), tv, tv * (1 - hue))
                ww = min(1.0, wwf(path0 + step * fi) + 0.08)
                _leaf_card(acc, a, up, nrm, leaf_rng.uniform(*P["card_size"]), tint, ww, 1)
                stats["leaf_cards"] += 1
    # apples hang beneath fruiting wood
    if P["apples"]:
        ap_rng = new_rng(seed, "apples")
        fruiting = [b for b in branches if b[2] >= P["depth"] - 1]
        for k in range(P["apples"]):
            pts, radii, depth, path0, step = ap_rng.choice(fruiting)
            fi = ap_rng.uniform(0.3, 0.95) * (len(pts) - 1)
            i0 = min(len(pts) - 2, int(fi))
            a = pts[i0].lerp(pts[i0 + 1], fi - i0)
            r = ap_rng.uniform(0.035, 0.045)
            base = (0.62, 0.06, 0.04) if ap_rng.random() < 0.75 else (0.70, 0.45, 0.08)
            _apple(acc, a + Vector((0, 0, -r * 1.3)), r, jitter_col(ap_rng, base, 0.12),
                   min(1.0, wwf(path0 + step * fi) + 0.05), 2)
            stats["apples"] += 1
    # surface roots (buttress) to seat the trunk
    rr_rng = new_rng(seed, "roots")
    for k in range(5):
        az = math.tau * k / 5 + rr_rng.uniform(-0.3, 0.3)
        d = Vector((math.cos(az), math.sin(az), 0))
        pts = [Vector((0, 0, 0.18)) + d * P["trunk_r"] * 0.4, d * P["trunk_r"] * 1.4 + Vector((0, 0, 0.03)),
               d * P["trunk_r"] * 2.6 + Vector((0, 0, -0.04))]
        acc.tube(pts, [P["trunk_r"] * 0.5, P["trunk_r"] * 0.28, P["trunk_r"] * 0.08], 6,
                 [bark] * 3, [0, 0, 0], mat=0)
    stats["height_m"] = round(max(v[2] for v in acc.v), 3)
    return acc, stats


# =============================================================================== GRASS (ECO-G1)
GRASS_PRESETS = {
    # short dense tuft (village verge)
    "tuft_short": dict(tillers=(4, 6), blades=(14, 20), L=(0.12, 0.34), w=(0.006, 0.011), spread=0.07,
                       droop=0.45, seedheads=0, dry=0.12, base=(0.035, 0.07, 0.018), tip=(0.26, 0.40, 0.10)),
    # meadow clump with a few seed stems
    "meadow": dict(tillers=(5, 7), blades=(16, 24), L=(0.16, 0.55), w=(0.006, 0.012), spread=0.10,
                   droop=0.4, seedheads=5, dry=0.15, base=(0.03, 0.065, 0.016), tip=(0.30, 0.42, 0.12)),
    # tall lax clump that flops over (field margins)
    "tall_lax": dict(tillers=(3, 5), blades=(18, 26), L=(0.30, 0.80), w=(0.007, 0.013), spread=0.08,
                     droop=0.55, seedheads=3, dry=0.2, base=(0.03, 0.06, 0.015), tip=(0.34, 0.44, 0.14)),
    # SW coastal dune grass: stiff, blue-grey, rolled leaves
    "coastal_dune": dict(tillers=(4, 6), blades=(14, 20), L=(0.25, 0.62), w=(0.004, 0.007), spread=0.12,
                         droop=0.25, seedheads=4, dry=0.25, base=(0.07, 0.09, 0.06), tip=(0.40, 0.46, 0.33)),
    # riverside reeds / rush with cattail heads (east river banks)
    "reed": dict(tillers=(3, 4), blades=(8, 12), L=(0.6, 1.25), w=(0.007, 0.012), spread=0.09,
                 droop=0.3, seedheads=0, cattails=4, dry=0.18, base=(0.05, 0.08, 0.03), tip=(0.30, 0.38, 0.14)),
}


def _blade(acc, rng, base, lean, L, w, droop, col_b, col_t, ww_scale, mat=0, nseg=6):
    """Length-dependent gravity droop, V-folded cross-section, random axial roll."""
    d0 = lean.normalized()
    horiz = Vector((d0.x, d0.y, 0))
    if horiz.length < 1e-4:
        horiz = Vector((1, 0, 0))
    horiz.normalize()
    side0 = horiz.cross(UP).normalized()
    roll = rng.uniform(-0.6, 0.6)
    # attempt 2 (ECO-G1): clamp sag so tips keep >= ~40% of their height (attempt 1 blades
    # collapsed onto the ground and vanished from the game camera)
    sag = min(droop * (L / 0.5) ** 1.5, 0.6 * max(0.2, d0.z))
    pts, widths, sides, folds, cols, wws = [], [], [], [], [], []
    prev = None
    for i in range(nseg + 1):
        t = i / nseg
        p = base + d0 * (L * t) + horiz * (sag * L * 0.6 * t * t) - UP * (sag * L * t ** 2.2)
        if p.z < 0.004 + 0.01 * t:
            p.z = 0.004 + 0.01 * t
        pts.append(p)
    for i in range(nseg + 1):
        t = i / nseg
        tan = (pts[min(nseg, i + 1)] - pts[max(0, i - 1)]).normalized()
        side = (Matrix.Rotation(roll * t, 3, tan) @ side0)
        side = (side - tan * side.dot(tan)).normalized()
        sides.append(side)
        folds.append(tan.cross(side).normalized())
        widths.append(w * (0.55 + 0.9 * t) * (1 - t) ** 0.9 if i < nseg else 0.0)
        cols.append(lerp(col_b, col_t, t ** 0.8))
        wws.append(ww_scale * t ** 1.5)
    acc.ribbon(pts, widths, sides, cols, wws, mat, fold=0.6, fold_dir=folds)
    return pts[-1]


def build_grass(seed, preset="meadow"):
    P = GRASS_PRESETS[preset]
    rng = new_rng(seed, "grass:" + preset)
    acc = MeshAcc()
    nt = rng.randint(*P["tillers"])
    Lmax = P["L"][1]
    stats = {"tillers": nt, "blades": 0, "seed_stems": 0, "dry_blades": 0}
    clump_lean = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)) * 0.25
    for ti in range(nt):
        # off-centre tillers (not a single radial disc: VEG-F1 stopped)
        a = rng.uniform(0, math.tau)
        r = P["spread"] * (0.35 + 0.65 * rng.random())
        tb = Vector((math.cos(a) * r, math.sin(a) * r, 0))
        tlean = (UP + Vector((math.cos(a), math.sin(a), 0)) * rng.uniform(0.15, 0.45) + clump_lean).normalized()
        nb = int(rng.randint(*P["blades"]) * 1.8) // max(1, nt // 3)
        # basal sheath layer: short, wide, upright, dark leaves that give the clump a solid core
        for si in range(rng.randint(6, 9)):
            phi = si * 2.39996
            lean = (UP + Vector((math.cos(phi), math.sin(phi), 0)) * rng.uniform(0.1, 0.35)).normalized()
            Ls = rng.uniform(0.05, 0.10) * (Lmax / 0.5) ** 0.5
            _blade(acc, rng, tb, lean, Ls, P["w"][1] * 1.4, 0.1, tuple(c * 0.9 for c in P["base"]),
                   lerp(P["base"], P["tip"], 0.55), 0.15, nseg=3)
            stats["sheaths"] = stats.get("sheaths", 0) + 1
        hue = rng.uniform(-0.08, 0.08)
        for bi in range(nb):
            # skewed height: many short, few tall
            u = rng.random() ** 1.8
            L = P["L"][0] + (P["L"][1] - P["L"][0]) * u
            phi = bi * 2.39996 + rng.uniform(-0.3, 0.3)
            cone = rng.uniform(0.05, 0.35) + 0.25 * (1 - u)
            lean = (tlean + Vector((math.cos(phi), math.sin(phi), 0)) * cone).normalized()
            dry = rng.random() < P["dry"]
            cb = P["base"]
            ct = jitter_col(rng, P["tip"], 0.12)
            ct = (ct[0] * (1 + hue), ct[1], ct[2] * (1 - hue))
            if dry:
                cb, ct = (0.16, 0.12, 0.05), (0.46, 0.38, 0.19)
                stats["dry_blades"] += 1
            off = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)) * 0.012
            _blade(acc, rng, tb + off, lean, L, rng.uniform(*P["w"]) * 1.3 * (1.2 if dry else 1.0),
                   P["droop"] * rng.uniform(0.7, 1.3), cb, ct, (L / Lmax) ** 0.5)
            stats["blades"] += 1
    # flowering stems with open panicle of spikelets
    for k in range(P["seedheads"]):
        a = rng.uniform(0, math.tau)
        base = Vector((math.cos(a), math.sin(a), 0)) * P["spread"] * 0.5
        H = Lmax * rng.uniform(1.05, 1.35)
        d = (UP + Vector((math.cos(a), math.sin(a), 0)) * rng.uniform(0.05, 0.25)).normalized()
        pts = [base + d * H * i / 6 + Vector((0, 0, 0)) for i in range(7)]
        sag = rng.uniform(0.02, 0.06)
        for i, p in enumerate(pts):
            p.x += sag * (i / 6) ** 2 * math.cos(a)
            p.y += sag * (i / 6) ** 2 * math.sin(a)
        stem_c = (0.30, 0.34, 0.14)
        acc.tube(pts, [0.0018] * 7, 3, [stem_c] * 7, [(i / 6) ** 1.5 for i in range(7)], cap_tip=True)
        top = pts[-1]
        for s in range(9):
            hgt = rng.uniform(0.0, 0.11)
            q = pts[-1] - d * hgt
            out = Matrix.Rotation(rng.uniform(0, math.tau), 3, d) @ _perp(d)
            sd = (d * 0.5 + out * 0.9).normalized()
            spk = [q, q + sd * 0.025, q + sd * 0.045 - UP * 0.01]
            acc.tube(spk, [0.0035, 0.004, 0.0015], 3, [(0.52, 0.47, 0.28)] * 3, [1.0] * 3)
        stats["seed_stems"] += 1
    for k in range(P.get("cattails", 0)):
        a = rng.uniform(0, math.tau)
        base = Vector((math.cos(a), math.sin(a), 0)) * P["spread"] * 0.4
        H = Lmax * rng.uniform(1.0, 1.25)
        pts = [base + Vector((0.01 * i * math.cos(a), 0.01 * i * math.sin(a), H * i / 8)) for i in range(9)]
        acc.tube(pts, [0.004] * 9, 4, [(0.26, 0.32, 0.12)] * 9, [(i / 8) ** 1.5 for i in range(9)])
        # brown cattail head on the upper stem
        hb = pts[6]
        ht = pts[6] + (pts[8] - pts[6]) * 0.75
        hp = [hb.lerp(ht, j / 4) for j in range(5)]
        acc.tube(hp, [0.008, 0.016, 0.017, 0.016, 0.008], 6, [(0.24, 0.13, 0.06)] * 5, [0.9, 0.93, 0.95, 0.97, 1.0])
        stats["seed_stems"] += 1
    stats["height_m"] = round(max(v[2] for v in acc.v), 3)
    return acc, stats


# =============================================================================== WHEAT FIELD (seeded scatter)
def _wheat_stalk(acc, rng, base, H, ripe):
    lean = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)) * 0.06
    d = (UP + lean).normalized()
    nod = rng.uniform(0.02, 0.07)  # heavy ear nods
    nseg = 5
    pts = []
    for i in range(nseg + 1):
        t = i / nseg
        p = base + d * H * t
        p.x += nod * t ** 3
        pts.append(p)
    stem_c = lerp((0.30, 0.36, 0.10), (0.68, 0.55, 0.26), ripe)
    acc.tube(pts, [0.0032, 0.003, 0.0028, 0.0026, 0.0024, 0.002], 3,
             [jitter_col(rng, lerp(tuple(c * 0.7 for c in stem_c), stem_c, i / nseg), 0.05) for i in range(nseg + 1)],
             [(i / nseg) ** 1.5 for i in range(nseg + 1)], cap_tip=False)
    # ear: spindle with alternating grain bulges
    top = pts[-1]
    ed = (pts[-1] - pts[-2]).normalized()
    eL = rng.uniform(0.075, 0.1)
    epts = [top + ed * eL * j / 8 for j in range(9)]
    erad = [0.0045 + 0.0035 * math.sin(math.pi * min(1, j / 7.0)) * (1.0 if j % 2 == 0 else 0.82) for j in range(9)]
    erad[-1] = 0.001
    ear_c = lerp((0.36, 0.42, 0.13), (0.78, 0.60, 0.27), ripe)
    acc.tube(epts, erad, 4, [jitter_col(rng, ear_c, 0.08)] * 9, [1.0] * 9, cap_tip=True)
    # awns: thin slivers fanning up from the ear
    awn_c = lerp((0.42, 0.46, 0.18), (0.86, 0.72, 0.40), ripe)
    for k in range(4):
        q = epts[2 + k * 2 if 2 + k * 2 < 9 else 8]
        out = Matrix.Rotation(k * 1.9 + rng.uniform(-0.3, 0.3), 3, ed) @ _perp(ed)
        ad = (ed + out * 0.35).normalized()
        i0 = acc.vert(q + out * 0.003, awn_c, 1.0)
        i1 = acc.vert(q - out * 0.003, awn_c, 1.0)
        i2 = acc.vert(q + ad * 0.05, awn_c, 1.0)
        acc.face((i0, i1, i2), 0)
    # two lower leaves
    for k in range(2):
        t = rng.uniform(0.2, 0.5)
        lb = base + (pts[-1] - base) * t
        a = rng.uniform(0, math.tau)
        lean2 = (UP * 0.5 + Vector((math.cos(a), math.sin(a), 0))).normalized()
        _blade(acc, rng, lb, lean2, rng.uniform(0.12, 0.2), 0.006, 0.9,
               tuple(c * 0.8 for c in stem_c), stem_c, t + 0.2, nseg=3)


def build_wheat_patch(seed, size=(3.2, 2.0), density=110.0):
    rng = new_rng(seed, "wheat")
    acc = MeshAcc()
    sx, sy = size
    cell = 1.0 / math.sqrt(density)
    nx, ny = int(sx / cell), int(sy / cell)
    n = 0
    for ix in range(nx):
        for iy in range(ny):
            # jittered grid + drill-row bias (sown in rows 0.15 m apart)
            x = -sx / 2 + (ix + rng.uniform(0.1, 0.9)) * cell
            y = -sy / 2 + (iy + 0.5) * cell + rng.uniform(-0.25, 0.25) * cell
            edge = min(x + sx / 2, sx / 2 - x, y + sy / 2, sy / 2 - y)
            if edge < 0.0:
                continue
            edgef = min(1.0, edge / 0.35)
            if rng.random() > 0.55 + 0.45 * edgef:
                continue
            H = rng.gauss(0.92, 0.07) * (0.82 + 0.18 * edgef)
            ripe = min(1.0, max(0.0, rng.gauss(0.85, 0.12)))
            _wheat_stalk(acc, rng, Vector((x, y, 0)), H, ripe)
            n += 1
    return acc, {"stalks": n, "size_m": list(size), "density_per_m2": density,
                 "height_m": round(max(v[2] for v in acc.v), 3)}


# =============================================================================== VEGETABLE ROWS
def _soil_bed(acc, sx, sy, rows, rng):
    nx, ny = 64, 40
    vid = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            x = -sx / 2 + sx * i / nx
            y = -sy / 2 + sy * j / ny
            ridge = 0.5 + 0.5 * math.cos(math.tau * (y + sy / 2) / (sy / rows))
            z = 0.06 * ridge ** 1.5 + 0.008 * math.sin(x * 23.1 + y * 7.7) + rng.uniform(-0.004, 0.004)
            edge = min(1.0, min(x + sx / 2, sx / 2 - x) / 0.25)
            z *= edge
            c = lerp((0.10, 0.065, 0.04), (0.20, 0.14, 0.09), ridge * 0.7 + rng.uniform(0, 0.3))
            vid[i, j] = acc.vert((x, y, z), c, 0.0)
    for i in range(nx):
        for j in range(ny):
            acc.face((vid[i, j], vid[i + 1, j], vid[i + 1, j + 1], vid[i, j + 1]), 0)


def _cabbage(acc, rng, c):
    head_r = rng.uniform(0.07, 0.095)
    # inner head: lumpy sphere
    rings, segs = 6, 10
    rows = []
    for i in range(rings + 1):
        th = math.pi * i / rings * 0.62
        row = []
        for j in range(segs):
            ph = math.tau * j / segs
            r = head_r * (1.0 + 0.06 * math.sin(3 * ph + i))
            p = c + Vector((math.sin(th) * math.cos(ph) * r, math.sin(th) * math.sin(ph) * r, head_r * 0.6 + math.cos(th) * r * 0.85))
            row.append(acc.vert(p, lerp((0.42, 0.58, 0.28), (0.60, 0.72, 0.42), 1 - i / rings), 0.05))
        rows.append(row)
    for i in range(rings):
        for j in range(segs):
            j2 = (j + 1) % segs
            acc.face((rows[i][j], rows[i + 1][j], rows[i + 1][j2], rows[i][j2]), 0)
    # outer cupped wrapper leaves (4x3 grid, bent outward)
    nl = rng.randint(7, 10)
    for k in range(nl):
        a = math.tau * k / nl + rng.uniform(-0.2, 0.2)
        L = rng.uniform(0.16, 0.22)
        W = L * 0.85
        out = Vector((math.cos(a), math.sin(a), 0))
        side = out.cross(UP)
        grid = {}
        col = jitter_col(rng, (0.16, 0.30, 0.17), 0.12)
        for u in range(5):
            for v in range(4):
                s = (v / 3 - 0.5)
                t = u / 4
                lift = math.sin(math.pi * t * 0.9) * 0.12 + 0.03
                cup = 0.25 * s * s
                p = c + out * (0.03 + L * t) + side * (s * W * math.sin(math.pi * (0.15 + 0.85 * t)))
                p.z = 0.02 + L * lift + L * cup * t
                vein = 1.25 if abs(s) < 0.1 else 1.0
                grid[u, v] = acc.vert(p, tuple(min(1, x * vein * (0.85 + 0.3 * t)) for x in col), 0.25 * t)
        for u in range(4):
            for v in range(3):
                acc.face((grid[u, v], grid[u + 1, v], grid[u + 1, v + 1], grid[u, v + 1]), 0)


def _carrot_top(acc, rng, c):
    n = rng.randint(6, 9)
    for k in range(n):
        a = math.tau * k / n + rng.uniform(-0.3, 0.3)
        lean = (UP + Vector((math.cos(a), math.sin(a), 0)) * rng.uniform(0.4, 0.8)).normalized()
        tip = _blade(acc, rng, c, lean, rng.uniform(0.16, 0.26), 0.0025, 0.5,
                     (0.10, 0.20, 0.05), (0.20, 0.38, 0.09), 1.0, nseg=4)
        # feathery leaflets along the petiole
        for s in range(5):
            t = 0.45 + 0.11 * s
            q = c + (tip - c) * t
            for sgn in (-1, 1):
                d = (Vector((math.cos(a + sgn * 1.2), math.sin(a + sgn * 1.2), 0.6))).normalized()
                i0 = acc.vert(q, (0.14, 0.30, 0.07), t)
                i1 = acc.vert(q + d * 0.035 + UP * 0.005, (0.22, 0.42, 0.10), t)
                i2 = acc.vert(q + d * 0.02 + (tip - c).normalized() * 0.02, (0.20, 0.40, 0.10), t)
                acc.face((i0, i1, i2), 0)
    # orange shoulder peeking from soil
    acc.tube([c - Vector((0, 0, 0.01)), c + Vector((0, 0, 0.012))], [0.012, 0.009], 6,
             [(0.70, 0.28, 0.05)] * 2, [0, 0], cap_tip=True)


def build_vegetable_rows(seed, size=(3.0, 2.0), rows=5):
    rng = new_rng(seed, "veg")
    acc = MeshAcc()
    _soil_bed(acc, size[0], size[1], rows, rng)
    soil_faces = len(acc.f)
    pitch = size[1] / rows
    counts = {"cabbage": 0, "carrot": 0}
    for r in range(rows):
        y = -size[1] / 2 + pitch * (r + 0.0) + 0.0
        y = -size[1] / 2 + pitch * r + pitch * 0.0
        yc = -size[1] / 2 + pitch * r  # ridge crest (cos maximum)
        crop = "cabbage" if r % 2 == 0 else "carrot"
        step = 0.42 if crop == "cabbage" else 0.12
        x = -size[0] / 2 + 0.25
        while x < size[0] / 2 - 0.25:
            if rng.random() > 0.06:  # a few gaps (harvested / failed)
                c = Vector((x + rng.uniform(-0.03, 0.03), yc + rng.uniform(-0.03, 0.03) + (pitch if r == 0 else 0) * 0, 0.055))
                if crop == "cabbage":
                    _cabbage(acc, rng, c)
                else:
                    _carrot_top(acc, rng, c)
                counts[crop] += 1
            x += step * rng.uniform(0.9, 1.1)
    for i in range(soil_faces):
        acc.mi[i] = 1  # soil material slot
    return acc, {"rows": rows, **counts, "size_m": list(size)}


# =============================================================================== FLOWERS
def _flower(acc, rng, base, kind):
    H = {"daisy": rng.uniform(0.22, 0.34), "poppy": rng.uniform(0.35, 0.5), "spike": rng.uniform(0.35, 0.55)}[kind]
    lean = (UP + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)) * 0.15).normalized()
    pts = [base + lean * H * i / 5 for i in range(6)]
    for i, p in enumerate(pts):
        p.x += 0.02 * (i / 5) ** 2
    acc.tube(pts, [0.0025] * 6, 3, [(0.16, 0.30, 0.09)] * 6, [(i / 5) ** 1.5 for i in range(6)], cap_tip=False)
    for k in range(2):
        a = rng.uniform(0, math.tau)
        _blade(acc, rng, base + UP * 0.01, (UP * 0.4 + Vector((math.cos(a), math.sin(a), 0))).normalized(),
               rng.uniform(0.08, 0.14), 0.008, 0.6, (0.10, 0.22, 0.06), (0.20, 0.36, 0.10), 0.4, nseg=3)
    top = pts[-1]
    fd = (pts[-1] - pts[-2]).normalized()
    if kind == "spike":
        col = jitter_col(rng, (0.30, 0.18, 0.55), 0.15)
        for s in range(14):
            t = s / 13
            q = top + fd * (t * 0.12)
            a = s * 2.4
            out = Vector((math.cos(a), math.sin(a), 0))
            r = 0.016 * (1 - 0.7 * t)
            i0 = acc.vert(q, col, 1.0)
            i1 = acc.vert(q + out * r + fd * 0.01, tuple(min(1, x * 1.25) for x in col), 1.0)
            i2 = acc.vert(q + Matrix.Rotation(0.9, 3, UP) @ out * r + fd * 0.006, col, 1.0)
            i3 = acc.vert(q + fd * 0.014, col, 1.0)
            acc.face((i0, i1, i3), 0)
            acc.face((i0, i3, i2), 0)
        return
    if kind == "daisy":
        np_, pl, pw, cup = rng.randint(11, 14), 0.03, 0.0075, -0.05
        pc, dc, dr = (0.92, 0.92, 0.86), (0.80, 0.58, 0.06), 0.009
    else:
        np_, pl, pw, cup = 5, 0.045, 0.028, 0.55
        pc, dc, dr = jitter_col(rng, (0.72, 0.06, 0.04), 0.1), (0.05, 0.04, 0.03), 0.007
    side0 = _perp(fd)
    for k in range(np_):
        a = math.tau * k / np_ + rng.uniform(-0.1, 0.1)
        out = (Matrix.Rotation(a, 3, fd) @ side0)
        sd = out.cross(fd)
        grid = []
        for u in range(4):
            t = u / 3
            row = []
            for v in (-1, 0, 1):
                wv = pw * math.sin(math.pi * (0.2 + 0.8 * t)) * (0.9 if u < 3 else 0.4)
                p = top + out * (dr * 0.8 + pl * t) + fd * (cup * pl * t * t + 0.003) + sd * (v * wv)
                row.append(acc.vert(p, tuple(min(1, x * (0.85 + 0.15 * t)) for x in pc), 1.0))
            grid.append(row)
        for u in range(3):
            acc.face((grid[u][0], grid[u][1], grid[u + 1][1], grid[u + 1][0]), 0)
            acc.face((grid[u][1], grid[u][2], grid[u + 1][2], grid[u + 1][1]), 0)
    disc = [top + fd * 0.002, top + fd * 0.006, top + fd * 0.008]
    acc.tube(disc, [dr, dr * 0.9, dr * 0.5], 8, [dc] * 3, [1.0] * 3, cap_tip=True)


def build_flower_patch(seed, size=(2.4, 1.4), n_clusters=7):
    rng = new_rng(seed, "flowers")
    acc = MeshAcc()
    counts = {"daisy": 0, "poppy": 0, "spike": 0}
    kinds = ["daisy", "poppy", "spike"]
    for c in range(n_clusters):
        # clumped colonies, each dominated by one kind (not uniform confetti)
        cx = rng.uniform(-size[0] / 2 + 0.2, size[0] / 2 - 0.2)
        cy = rng.uniform(-size[1] / 2 + 0.2, size[1] / 2 - 0.2)
        main = kinds[c % 3]
        for k in range(rng.randint(18, 28)):
            r = abs(rng.gauss(0, 0.18))
            a = rng.uniform(0, math.tau)
            kind = main if rng.random() < 0.8 else rng.choice(kinds)
            _flower(acc, rng, Vector((cx + math.cos(a) * r, cy + math.sin(a) * r, 0)), kind)
            counts[kind] += 1
    # interstitial short grass blades so flowers sit in turf
    for k in range(260):
        b = Vector((rng.uniform(-size[0] / 2, size[0] / 2), rng.uniform(-size[1] / 2, size[1] / 2), 0))
        a = rng.uniform(0, math.tau)
        _blade(acc, rng, b, (UP + Vector((math.cos(a), math.sin(a), 0)) * 0.4).normalized(),
               rng.uniform(0.06, 0.16), 0.004, 0.5, (0.04, 0.08, 0.02), (0.24, 0.38, 0.10), 0.6, nseg=3)
    return acc, {**counts, "turf_blades": 260, "size_m": list(size)}


# =============================================================================== FENCE + HEDGEROW
def build_fence(seed, length=6.6, post_gap=2.2):
    rng = new_rng(seed, "fence")
    acc = MeshAcc()
    n_posts = int(round(length / post_gap)) + 1
    posts = []
    wood = (0.30, 0.22, 0.15)
    for i in range(n_posts):
        x = -length / 2 + i * post_gap + rng.uniform(-0.06, 0.06)
        lean = Vector((rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04), 1)).normalized()
        H = rng.uniform(1.02, 1.12)
        base = Vector((x, 0, -0.05))
        pts = [base + lean * H * k / 4 for k in range(5)]
        rj = [[1.0 + 0.12 * math.sin(s * 2.1 + i * 1.7) + rng.uniform(-0.05, 0.05) for s in range(7)] for _ in pts]
        cols = [jitter_col(rng, tuple(c * (0.75 + 0.06 * k) for c in wood), 0.05) for k in range(5)]
        acc.tube(pts, [0.07, 0.068, 0.066, 0.064, 0.05], 7, cols, [0] * 5, cap_tip=True, rjit=rj)
        posts.append(pts)
    # two split rails per bay, sagging, slightly twisted, overhanging the posts
    for i in range(n_posts - 1):
        for hgt in (0.45, 0.88):
            a = posts[i][0] + (posts[i][-1] - posts[i][0]) * (hgt / 1.07)
            b = posts[i + 1][0] + (posts[i + 1][-1] - posts[i + 1][0]) * (hgt / 1.07)
            a = a + Vector((-0.12, 0.075, 0))
            b = b + Vector((0.12, 0.075, 0))
            pts = []
            for k in range(7):
                t = k / 6
                p = a.lerp(b, t)
                p.z -= 0.035 * math.sin(math.pi * t)
                pts.append(p)
            rj = [[(1.25 if s in (0, 3) else 0.85) + rng.uniform(-0.06, 0.06) for s in range(6)] for _ in pts]
            cols = [jitter_col(rng, wood, 0.08) for _ in pts]
            acc.tube(pts, [0.038] * 7, 6, cols, [0] * 7, cap_tip=False, cap_base=False, rjit=rj)
    return acc, {"posts": n_posts, "length_m": length}


def build_hedgerow(seed, length=4.0, height=1.25, depth=0.9):
    rng = new_rng(seed, "hedge")
    acc = MeshAcc()
    leaves = 0
    stems = 9
    for s in range(stems):
        x = -length / 2 + length * (s + 0.5) / stems + rng.uniform(-0.15, 0.15)
        base = Vector((x, rng.uniform(-0.1, 0.1), 0))
        for k in range(3):
            d = (UP + Vector((rng.uniform(-0.6, 0.6), rng.uniform(-0.4, 0.4), 0))).normalized()
            L = height * rng.uniform(0.6, 0.95)
            pts = [base + d * L * i / 5 for i in range(6)]
            acc.tube(pts, [0.02, 0.017, 0.014, 0.01, 0.007, 0.004], 4, [(0.20, 0.16, 0.12)] * 6,
                     [(i / 5) ** 1.5 * 0.6 for i in range(6)])
    # foliage volume: irregular hedge profile (noise-modulated top), denser at the surface
    for k in range(4200):
        x = rng.uniform(-length / 2, length / 2)
        top = height * (0.82 + 0.12 * math.sin(x * 2.3 + 1.1) + 0.06 * math.sin(x * 6.1))
        z = top * (rng.random() ** 0.55)
        half = depth / 2 * (0.6 + 0.4 * math.sin(math.pi * min(1.0, z / top)))
        y = rng.choice((-1, 1)) * half * (rng.random() ** 0.35)
        p = Vector((x, y, z))
        out = Vector((0, 1 if y > 0 else -1, (z / top - 0.5) * 1.4)).normalized()
        d = Matrix.Rotation(rng.uniform(0, math.tau), 3, out) @ _perp(out)
        lightf = min(1.0, z / top) * (0.6 + 0.4 * abs(y) / max(0.01, half))
        col = jitter_col(rng, lerp((0.05, 0.12, 0.03), (0.16, 0.29, 0.07), lightf), 0.15)
        _leaf(acc, p, d, out, rng.uniform(0.06, 0.09), 0.045, col, 0.35 + 0.65 * (z / top) ** 1.5, 1)
        leaves += 1
    return acc, {"length_m": length, "height_m": height, "leaves": leaves}


# =============================================================================== HAYSTACK
def build_haystack(seed, radius=1.0, height=2.1):
    rng = new_rng(seed, "hay")
    acc = MeshAcc()
    rings, segs = 22, 40
    rows = []
    hay = (0.62, 0.50, 0.24)

    def prof(t):  # beehive profile: belly then dome
        return radius * (0.92 + 0.18 * math.sin(math.pi * min(1, t / 0.55) * 0.9)) * (1 - t ** 2.6) ** 0.6

    for i in range(rings + 1):
        t = i / rings
        row = []
        for j in range(segs):
            a = math.tau * j / segs
            r = prof(t) * (1 + 0.035 * math.sin(5 * a + 3 * t) + 0.025 * math.sin(11 * a - 7 * t)) + rng.uniform(-0.012, 0.012)
            p = Vector((math.cos(a) * r, math.sin(a) * r, t * height))
            c = jitter_col(rng, lerp(tuple(x * 0.7 for x in hay), hay, 0.3 + 0.7 * t), 0.1)
            if t < 0.12:
                c = tuple(x * (0.6 + 0.4 * t / 0.12) for x in c)  # damp grey base
            row.append(acc.vert(p, c, 0.0))
        rows.append(row)
    for i in range(rings):
        for j in range(segs):
            j2 = (j + 1) % segs
            acc.face((rows[i][j], rows[i][j2], rows[i + 1][j2], rows[i + 1][j]), 0)
    tip = acc.vert((0, 0, height + 0.02), hay, 0.0)
    for j in range(segs):
        acc.face((rows[-1][j], rows[-1][(j + 1) % segs], tip), 0)
    # surface straw: thin strips lying mostly downward along the surface, some sticking out
    strands = 2200
    for k in range(strands):
        t = rng.random() ** 0.8 * 0.97
        a = rng.uniform(0, math.tau)
        r = prof(t) + 0.004
        p = Vector((math.cos(a) * r, math.sin(a) * r, t * height))
        n = Vector((math.cos(a), math.sin(a), 0.35 * t)).normalized()
        tang = Vector((-math.sin(a), math.cos(a), 0))
        down = n.cross(tang).normalized()
        if down.z > 0:
            down = -down
        d = (down * rng.uniform(0.6, 1.0) + tang * rng.uniform(-0.5, 0.5) + n * rng.uniform(0.0, 0.5)).normalized()
        L = rng.uniform(0.12, 0.3)
        w = 0.004
        c = jitter_col(rng, (0.78, 0.66, 0.35), 0.15)
        loose = rng.random() < 0.15
        ww = 0.35 if loose else 0.0
        i0 = acc.vert(p - tang * w, c, 0)
        i1 = acc.vert(p + tang * w, c, 0)
        e = p + d * L + n * (0.04 if loose else 0.0)
        i2 = acc.vert(e + tang * w * 0.6, c, ww)
        i3 = acc.vert(e - tang * w * 0.6, c, ww)
        acc.face((i0, i1, i2, i3), 0)
    # skirt of fallen straw on the ground
    for k in range(500):
        a = rng.uniform(0, math.tau)
        r = radius * rng.uniform(0.95, 1.5)
        p = Vector((math.cos(a) * r, math.sin(a) * r, 0.005))
        d = Vector((math.cos(a + rng.uniform(-1.5, 1.5)), math.sin(a + rng.uniform(-1.5, 1.5)), 0.02))
        side = d.cross(UP).normalized() * 0.004
        c = jitter_col(rng, (0.66, 0.55, 0.28), 0.18)
        q = p + d * rng.uniform(0.1, 0.25)
        idx = [acc.vert(p - side, c, 0), acc.vert(p + side, c, 0), acc.vert(q + side, c, 0.15), acc.vert(q - side, c, 0.15)]
        acc.face(idx, 0)
    # central pole
    acc.tube([Vector((0, 0, height * 0.7)), Vector((0.02, 0, height + 0.35))], [0.03, 0.022], 6,
             [(0.28, 0.21, 0.14)] * 2, [0, 0], mat=1, cap_tip=True)
    return acc, {"strands": strands, "height_m": round(height + 0.35, 2), "radius_m": radius}


# =============================================================================== LIVESTOCK (metaball form)
def _metaball_mesh(name, elems, resolution):
    mb = bpy.data.metaballs.new(name)
    mb.resolution = resolution
    mb.render_resolution = resolution
    mb.threshold = 0.6
    for kind, co, r, size, rot in elems:
        e = mb.elements.new(type=kind)
        e.co = co
        e.radius = r
        if size:
            e.size_x, e.size_y, e.size_z = size
        if rot:
            e.rotation = rot
        e.stiffness = 2.0
    ob = bpy.data.objects.new(name, mb)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob)
    bpy.data.metaballs.remove(mb)
    return me


def _quat_from(axis, ang):
    from mathutils import Quaternion
    return Quaternion(axis, ang)


def build_chicken(seed):
    """Hen, ~0.42 m tall, +Y forward. Body/neck/head from one metaball family (smooth blend),
    tail sickle feathers, folded wings, serrated comb, wattles, beak, scaled legs, toes as
    separate geometry for a crisp silhouette. No feather groom, no rig."""
    rng = new_rng(seed, "chicken")
    acc = MeshAcc()
    body = _metaball_mesh("ChBody", [
        ("ELLIPSOID", (0, 0.0, 0.25), 0.16, (0.72, 1.0, 0.72), None),
        ("BALL", (0, 0.07, 0.235), 0.115, None, None),           # breast
        ("ELLIPSOID", (0, -0.10, 0.29), 0.10, (0.8, 1.0, 0.7), _quat_from((1, 0, 0), -0.6)),  # saddle rising to tail
        ("ELLIPSOID", (0, -0.03, 0.17), 0.1, (0.75, 1.0, 0.6), None),  # belly fluff
        ("CAPSULE", (0, 0.12, 0.33), 0.06, (0.05, 1, 1), _quat_from((0, 1, 0), math.radians(90)) @ _quat_from((1, 0, 0), 0)),
        ("BALL", (0, 0.135, 0.37), 0.058, None, None),           # neck hackles
        ("BALL", (0, 0.155, 0.415), 0.052, None, None),          # head
    ], 0.011)
    plum = (0.42, 0.20, 0.08)
    plum_light = (0.62, 0.36, 0.15)

    def body_col(co):
        f = max(0.0, min(1.0, (co.z - 0.15) / 0.28))
        c = lerp(plum, plum_light, f * 0.6 + (0.2 if co.y > 0.05 else 0.0))
        if co.y > 0.11 and co.z > 0.34:
            c = lerp(c, (0.70, 0.44, 0.18), 0.5)  # golden hackles
        return c
    acc.add_mesh(body, Matrix.Identity(4), body_col, lambda co: 0.0)
    bpy.data.meshes.remove(body)
    # comb: serrated single comb (row of merged balls) + wattles
    comb = _metaball_mesh("ChComb", [("BALL", (0, 0.13 + 0.016 * i, 0.455 + 0.012 * math.sin(math.pi * i / 4)), 0.022 - 0.002 * abs(i - 2), None, None)
                                     for i in range(5)], 0.006)
    acc.add_mesh(comb, Matrix.Identity(4), lambda co: (0.70, 0.05, 0.04), lambda co: 0.0)
    bpy.data.meshes.remove(comb)
    watt = _metaball_mesh("ChWattle", [("ELLIPSOID", (sx * 0.012, 0.19, 0.375), 0.022, (0.6, 0.7, 1.2), None) for sx in (-1, 1)], 0.006)
    acc.add_mesh(watt, Matrix.Identity(4), lambda co: (0.66, 0.05, 0.04), lambda co: 0.0)
    bpy.data.meshes.remove(watt)
    # beak (4-sided cone, slight hook)
    bk = [Vector((0, 0.195, 0.418)), Vector((0, 0.22, 0.412)), Vector((0, 0.238, 0.402))]
    acc.tube(bk, [0.014, 0.008, 0.002], 6, [(0.80, 0.62, 0.20)] * 3, [0] * 3, cap_tip=True)
    # eyes
    for sx in (-1, 1):
        e = [Vector((sx * 0.036, 0.168, 0.426)), Vector((sx * 0.041, 0.168, 0.426))]
        acc.tube(e, [0.008, 0.007], 8, [(0.55, 0.25, 0.03), (0.02, 0.02, 0.02)], [0, 0], cap_tip=True)
    # folded wings: cupped feather panels along the flanks, primaries tucked under tail
    for sx in (-1, 1):
        grid = {}
        for u in range(6):
            for v in range(4):
                t, s = u / 5, v / 3
                y = 0.08 - 0.25 * t
                z = 0.31 - 0.11 * s - 0.03 * t + 0.04 * t * t
                x = sx * (0.118 - 0.02 * t + 0.012 * math.sin(math.pi * s))
                band = 0.75 if (u % 2 == 0 and s > 0.6) else 1.0
                grid[u, v] = acc.vert((x, y, z), tuple(k * band for k in lerp(plum, (0.30, 0.14, 0.06), t)), 0.0)
        for u in range(5):
            for v in range(3):
                q = (grid[u, v], grid[u + 1, v], grid[u + 1, v + 1], grid[u, v + 1])
                acc.face(q if sx > 0 else tuple(reversed(q)), 0)
    # tail: fan of curved feathers (dark with bronze-green tone), sickles curving down
    for k in range(9):
        f = (k - 4) / 4.0
        base = Vector((f * 0.035, -0.15, 0.32))
        d0 = Vector((f * 0.25, -0.55, 0.85)).normalized()
        L = 0.16 + 0.03 * (1 - abs(f)) + rng.uniform(-0.01, 0.01)
        pts, widths, sides, folds, cols = [], [], [], [], []
        for i in range(6):
            t = i / 5
            p = base + d0 * L * t + Vector((0, -0.09, -0.07)) * t * t
            pts.append(p)
            widths.append(0.022 * math.sin(math.pi * (0.15 + 0.8 * t)) + 0.002)
            cols.append(lerp((0.16, 0.10, 0.05), (0.08, 0.10, 0.06), t))
        for i in range(6):
            tan = (pts[min(5, i + 1)] - pts[max(0, i - 1)]).normalized()
            sd = tan.cross(Vector((1, 0, 0))).cross(tan).normalized() if False else Vector((1, 0, 0))
            sd = (sd - tan * sd.dot(tan)).normalized()
            sides.append(sd)
            folds.append(tan.cross(sd).normalized())
        widths[-1] = 0.0
        acc.ribbon(pts, widths, sides, cols, [0.25 * i / 5 for i in range(6)], 0, fold=0.3, fold_dir=folds)
    # legs: thigh hidden in fluff, scaled shank, toes
    leg_c = (0.78, 0.60, 0.20)
    for sx in (-1, 1):
        hip = Vector((sx * 0.045, 0.0, 0.15))
        knee = Vector((sx * 0.05, 0.01, 0.085))
        foot = Vector((sx * 0.052, 0.015, 0.012))
        acc.tube([hip, knee], [0.022, 0.014], 6, [plum] * 2, [0, 0], cap_tip=False)
        acc.tube([knee, (knee + foot) / 2, foot], [0.009, 0.008, 0.0075], 6, [leg_c] * 3, [0] * 3, cap_tip=False)
        for a in (-0.45, 0.0, 0.45, math.pi):
            d = Vector((math.sin(a), math.cos(a), 0))
            L = 0.035 if a == math.pi else 0.055
            toe = [foot, foot + d * L * 0.6 + Vector((0, 0, -0.006)), foot + d * L + Vector((0, 0, -0.008))]
            acc.tube(toe, [0.006, 0.005, 0.0025], 5, [leg_c] * 3, [0] * 3, cap_tip=True)
    return acc, {"height_m": round(max(v[2] for v in acc.v), 3), "status_note": "procedural form; no groom/rig"}


def build_cow_blockout(seed):
    """STRUCTURAL BLOCKOUT: proportion/silhouette volume only (metaball), not art."""
    acc = MeshAcc()
    elems = [
        ("ELLIPSOID", (0, 0.0, 0.95), 0.55, (0.62, 1.25, 0.62), None),
        ("ELLIPSOID", (0, 0.55, 1.0), 0.40, (0.65, 0.8, 0.7), None),     # shoulders
        ("ELLIPSOID", (0, -0.55, 0.98), 0.40, (0.7, 0.8, 0.62), None),   # hips
        ("CAPSULE", (0, 0.95, 1.05), 0.17, (0.25, 1, 1), _quat_from((0, 0, 1), math.radians(90)) @ _quat_from((0, 1, 0), math.radians(-25))),
        ("ELLIPSOID", (0, 1.22, 0.95), 0.2, (0.75, 1.3, 0.85), None),    # head
        ("ELLIPSOID", (0, 1.42, 0.86), 0.13, (0.9, 0.8, 0.75), None),    # muzzle
        ("BALL", (0, -0.35, 0.55), 0.12, None, None),                    # udder
    ]
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * 0.2, sy * 0.52
            elems.append(("CAPSULE", (x, y, 0.42), 0.085, (0.32, 1, 1), _quat_from((0, 1, 0), math.radians(90))))
    me = _metaball_mesh("CowBlk", elems, 0.035)

    def col(co):
        # black-and-white patches as flat colour fields (blockout read only)
        v = math.sin(co.x * 7 + 1.3) * math.sin(co.y * 4.2) + math.sin(co.z * 5.1 + co.y * 2)
        return (0.06, 0.05, 0.05) if v > 0.6 else (0.82, 0.80, 0.76)
    acc.add_mesh(me, Matrix.Identity(4), col, lambda co: 0.0)
    bpy.data.meshes.remove(me)
    for sx in (-1, 1):  # horns
        acc.tube([Vector((sx * 0.12, 1.15, 1.13)), Vector((sx * 0.22, 1.18, 1.2)), Vector((sx * 0.25, 1.24, 1.28))],
                 [0.03, 0.02, 0.006], 6, [(0.75, 0.70, 0.58)] * 3, [0] * 3)
    acc.tube([Vector((0, -0.95, 1.12)), Vector((0, -1.05, 0.8)), Vector((0, -1.07, 0.5))], [0.03, 0.02, 0.035], 5,
             [(0.1, 0.1, 0.1)] * 3, [0, 0.2, 0.4])
    return acc, {"height_m": round(max(v[2] for v in acc.v), 3), "status_note": "STRUCTURAL_BLOCKOUT_NOT_ART"}

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
    # generic broadleaf village tree (rounded oak-like cloud crown)
    "deciduous": dict(trunk_len=2.4, trunk_r=0.21, lean=0.05, scaffolds=4, scaffold_at=(0.6, 1.0),
                      scaffold_len=(1.8, 2.4), angle=(30, 50), depth=4, len_decay=(0.62, 0.76), gravi=0.12,
                      tex="oak", card_size=(0.75, 1.0), card_density=7.0, lobe_merge=1.0, lobe_pad=0.55,
                      lobe_depth=2, lobe_zscale=0.82, tint=(0.7, 1.2), bark=(0.24, 0.17, 0.11), apples=0,
                      side_shoots=2, droop=0.0, sides0=12, bare_below=2.0),
    # open-centre orchard apple: visible trunk + scaffolds under a low rounded crown, fruit clusters
    "apple": dict(trunk_len=1.35, trunk_r=0.15, lean=0.06, scaffolds=4, scaffold_at=(0.8, 1.0),
                  scaffold_len=(1.3, 1.7), angle=(42, 58), depth=4, len_decay=(0.6, 0.72), gravi=0.06,
                  tex="apple", card_size=(0.55, 0.75), card_density=8.0, lobe_merge=0.8, lobe_pad=0.42,
                  lobe_depth=2, lobe_zscale=0.72, tint=(0.75, 1.2), bark=(0.27, 0.19, 0.13), apples=46,
                  side_shoots=0, droop=0.12, sides0=10, bare_below=1.75),
    # taller forest tree toward Moss Forest (SE): tall ovoid stacked crown, darker smaller leaves
    "forest_tall": dict(trunk_len=4.0, trunk_r=0.26, lean=0.03, scaffolds=6, scaffold_at=(0.4, 1.0),
                        scaffold_len=(1.6, 2.2), angle=(20, 34), depth=4, len_decay=(0.6, 0.72), gravi=0.22,
                        tex="beech", card_size=(0.7, 0.95), card_density=7.5, lobe_merge=1.1, lobe_pad=0.5,
                        lobe_depth=2, lobe_zscale=1.15, tint=(0.6, 1.05), bark=(0.20, 0.17, 0.14), apples=0,
                        side_shoots=4, droop=0.0, sides0=12, bare_below=2.6),
}

LEAF_KINDS = {
    # leaf shape (length px at 1024, width ratio, lobed?), base colour, n leaves, twig origins, extra
    "oak": dict(L=(70, 105), wr=0.55, lobes=3, base=(0.11, 0.25, 0.045), warm=(0.32, 0.40, 0.08), n=150, twigs=4),
    "apple": dict(L=(62, 88), wr=0.5, lobes=0, base=(0.12, 0.27, 0.05), warm=(0.30, 0.42, 0.10), n=125, twigs=5, fruit=7),
    "beech": dict(L=(52, 74), wr=0.5, lobes=0, base=(0.07, 0.19, 0.04), warm=(0.20, 0.32, 0.07), n=270, twigs=4),
}


def _soft_save(path, rgb, a, ss):
    """Downsample a supersampled straight-alpha canvas with premultiplied LANCZOS -> soft AA alpha.
    Transparent texels get the mean leaf colour (bleed) so filtering never halos."""
    import numpy as np
    from PIL import Image
    H, W = a.shape
    pm = np.dstack([rgb * a[..., None], a])
    out = []
    for c in range(4):
        ch = Image.fromarray(pm[..., c].astype(np.float32), "F").resize((W // ss, H // ss), Image.LANCZOS)
        out.append(np.asarray(ch))
    pr, pg, pb, al = [np.clip(x, 0, 1) for x in out]
    alc = np.maximum(al, 1e-6)
    col = np.dstack([pr / alc, pg / alc, pb / alc])
    mean = col[al > 0.5].mean(axis=0)
    col[al < 0.02] = mean
    col = np.clip(col, 0, 1)
    img = np.dstack([col ** (1 / 2.2) * 255, al * 255]).round().astype(np.uint8)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(img, "RGBA").save(path, optimize=False)
    return path


def paint_leaf_cluster(path, seed, kind):
    """Painterly round leaf-cluster card (species-specific), 4x supersampled -> soft alpha edges.
    Leaves radiate from several twig origins inside a rounded cluster; back leaves darker/cooler,
    front/top leaves lighter/warmer; per-leaf hue jitter, midrib, edge darkening."""
    import numpy as np
    K = LEAF_KINDS[kind]
    rng = new_rng(seed, "cluster:" + kind)
    ss, S = 2, 1024  # paint at 1024 -> 512 output (2x supersample per axis = 4x samples)
    rgb = np.zeros((S, S, 3), np.float32)
    a = np.zeros((S, S), np.float32)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    cx, cy, R = S * 0.5, S * 0.5, S * 0.40
    twigs = []
    for t in range(K["twigs"]):
        ang = rng.uniform(0, math.tau)
        r = R * rng.uniform(0.0, 0.45)
        twigs.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r * 0.9 + R * 0.1))
    # twig sticks first
    for (tx, ty) in twigs:
        bx, by = cx + rng.uniform(-30, 30), cy + R * 0.55  # twig stays inside the cluster
        for j in range(60):
            f = j / 59
            px, py = bx + (tx - bx) * f, by + (ty - by) * f
            m = (xx - px) ** 2 + (yy - py) ** 2 <= (7 - 4 * f) ** 2
            rgb[m] = (0.16, 0.11, 0.07)
            a[m] = 1
    leaves = []
    for k in range(K["n"]):
        tx, ty = twigs[rng.randrange(len(twigs))]
        ang = rng.uniform(0, math.tau)
        dist = R * (rng.random() ** 0.6)
        x0 = cx + math.cos(ang) * dist * 0.95
        y0 = cy + math.sin(ang) * dist * 0.88
        # direction: away from the twig origin with jitter (radiating rosettes)
        d = math.atan2(y0 - ty, x0 - tx) + rng.uniform(-0.6, 0.6)
        depth = rng.random()  # 0 back .. 1 front
        leaves.append((depth, x0, y0, d))
    leaves.sort()
    for depth, x0, y0, d in leaves:
        L = rng.uniform(*K["L"])
        W = L * K["wr"] * rng.uniform(0.85, 1.15)
        ca, sa = math.cos(d), math.sin(d)
        x_lo, x_hi = int(max(0, x0 - L - 4)), int(min(S, x0 + L + 4))
        y_lo, y_hi = int(max(0, y0 - L - 4)), int(min(S, y0 + L + 4))
        if x_lo >= x_hi or y_lo >= y_hi:
            continue
        X = xx[y_lo:y_hi, x_lo:x_hi] - x0
        Y = yy[y_lo:y_hi, x_lo:x_hi] - y0
        u = X * ca + Y * sa + L * 0.5
        v = -X * sa + Y * ca
        un = np.clip(u / L, 0, 1)
        half = W * 0.5 * np.maximum(np.sin(np.pi * un ** 0.8), 0) ** 0.8
        if K["lobes"]:
            half = half * (0.82 + 0.18 * np.abs(np.sin(un * np.pi * K["lobes"] * 1.5)))
        inside = (u > 0) & (u < L) & (np.abs(v) < half)
        if not inside.any():
            continue
        topf = 1.0 - (y0 / S)  # upper leaves catch more light
        light = 0.55 + 0.55 * depth * (0.6 + 0.4 * topf)
        base = np.array(K["base"]) * rng.uniform(0.85, 1.15)
        warm = np.array(K["warm"])
        c = base + (warm - base) * min(1.0, max(0.0, light - 0.55) * 1.1)
        c = c * light
        hv = rng.uniform(-0.05, 0.05)
        c = c * np.array((1 + hv, 1.0, 1 - hv))
        side = np.where(v > 0, 1.06, 0.93)[..., None]
        grad = (0.85 + 0.25 * un)[..., None]
        col = c[None, None, :] * side * grad
        rib = inside & (np.abs(v) < 1.8)
        edge = inside & (np.abs(v) > half - 3.0)
        sub_rgb = rgb[y_lo:y_hi, x_lo:x_hi]
        sub_a = a[y_lo:y_hi, x_lo:x_hi]
        sub_rgb[inside] = col[inside]
        sub_rgb[rib] = col[rib] * 1.3
        sub_rgb[edge] = col[edge] * 0.78
        sub_a[inside] = 1
    for k in range(K.get("fruit", 0)):
        ang = rng.uniform(0, math.tau)
        r = R * rng.uniform(0.25, 0.8)
        fx, fy = cx + math.cos(ang) * r, cy + math.sin(ang) * r * 0.8 + R * 0.15
        fr = rng.uniform(22, 30)
        d2 = (xx - fx) ** 2 + (yy - fy) ** 2
        m = d2 <= fr * fr
        shade = np.clip(1.15 - np.sqrt(d2) / fr * 0.5 - (yy - fy) / fr * 0.25, 0.5, 1.3)[..., None]
        red = np.array((0.62, 0.05, 0.03)) if rng.random() < 0.8 else np.array((0.68, 0.40, 0.06))
        rgb[m] = (red[None, None, :] * shade)[m]
        a[m] = 1
        hl = (xx - fx + fr * 0.35) ** 2 + (yy - fy + fr * 0.35) ** 2 <= (fr * 0.22) ** 2
        rgb[hl] = (0.9, 0.55, 0.45)
    return _soft_save(path, rgb, a, ss)


def paint_leaf_spray(path, seed, kind="broadleaf"):
    """Paint an RGBA leaf-spray texture (twig + ~22 leaves) for alpha cards. Transparent texels
    carry the mean leaf colour (bleed) to avoid light fringes under filtering/mips."""
    import numpy as np
    from PIL import Image
    rng = new_rng(seed, "leafspray:" + kind)
    S = 512
    if kind == "needle":
        return _paint_needle_spray(path, rng, S)
    rgb = np.zeros((S, S, 3), np.float32)
    a = np.zeros((S, S), np.float32)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    base_c = np.array((0.10, 0.25, 0.04)) if kind == "broadleaf" else np.array((0.12, 0.27, 0.05))
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


def _paint_needle_spray(path, rng, S):
    """Conifer spray: flat frond of side twiglets densely set with short needles."""
    import numpy as np
    from PIL import Image
    rgb = np.zeros((S, S, 3), np.float32)
    a = np.zeros((S, S), np.float32)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)

    def stroke(x0, y0, x1, y1, r, col):
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / max(0.8, r)))
        for j in range(n + 1):
            f = j / n
            cx, cy = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
            x_lo, x_hi = int(max(0, cx - r - 1)), int(min(S, cx + r + 2))
            y_lo, y_hi = int(max(0, cy - r - 1)), int(min(S, cy + r + 2))
            sub = (xx[y_lo:y_hi, x_lo:x_hi] - cx) ** 2 + (yy[y_lo:y_hi, x_lo:x_hi] - cy) ** 2 <= r * r
            rgb[y_lo:y_hi, x_lo:x_hi][sub] = col
            a[y_lo:y_hi, x_lo:x_hi][sub] = 1

    S = 1024  # 2x supersampled canvas -> 512 soft-alpha output
    rgb = np.zeros((S, S, 3), np.float32)
    a = np.zeros((S, S), np.float32)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    axis = [(512 + 24 * math.sin(t * 3), 1010 - 940 * t) for t in [i / 30 for i in range(31)]]
    for i in range(30):
        stroke(*axis[i], *axis[i + 1], 8.0 * (1 - i / 34), (0.17, 0.11, 0.07))
    for k in range(16):
        t = 0.08 + 0.9 * k / 15
        x0, y0 = axis[int(t * 30)]
        for side in (-1, 1):
            ang = math.radians(-90 + side * rng.uniform(50, 65))
            L = 400 * (1 - 0.75 * t) * rng.uniform(0.85, 1.1)
            x1, y1 = x0 + math.cos(ang) * L, y0 + math.sin(ang) * L
            stroke(x0, y0, x1, y1, 4.0, (0.13, 0.10, 0.06))
            nn = int(L / 10)
            for j in range(nn):
                f = j / max(1, nn)
                px, py = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
                for sd in (-1, 1):
                    na = ang + sd * math.radians(rng.uniform(45, 70))
                    nl = rng.uniform(28, 44) * (1 - 0.4 * f)
                    sh = rng.uniform(0.8, 1.2) * (1.15 if sd < 0 else 0.9)
                    col = (0.05 * sh, 0.15 * sh, 0.055 * sh)
                    stroke(px, py, px + math.cos(na) * nl, py + math.sin(na) * nl, 2.6, col)
    return _soft_save(path, rgb, a, 2)


def build_conifer(seed, height=8.0):
    """Whorled conifer (fir/spruce form): straight tapered trunk, whorls of drooping-then-upturned
    branches, cone-shaped envelope, needle-spray alpha cards held near-horizontal."""
    rng = new_rng(seed, "conifer")
    acc = MeshAcc()
    bark = (0.18, 0.13, 0.10)
    tr = [Vector((0, 0, height * i / 12)) for i in range(13)]
    acc.tube(tr, [0.22 * (1 - i / 12) ** 0.9 + 0.01 for i in range(13)], 10,
             [jitter_col(rng, bark, 0.05) for _ in tr], [(i / 12) ** 2 for i in range(13)], cap_tip=True)
    n_cards = 0
    z = 1.1
    whorl = 0
    while z < height - 0.3:
        hf = z / height
        Lb = (height - z) * 0.42 * rng.uniform(0.85, 1.1) + 0.25
        nb = rng.randint(6, 8)
        az0 = rng.uniform(0, math.tau)
        for b in range(nb):
            az = az0 + math.tau * b / nb + rng.uniform(-0.25, 0.25)
            d = Vector((math.cos(az), math.sin(az), 0))
            pts = []
            for i in range(6):
                t = i / 5
                p = Vector((0, 0, z)) + d * Lb * t + UP * (-0.16 * Lb * math.sin(math.pi * t * 0.8) + 0.10 * Lb * t ** 2)
                pts.append(p)
            ww0 = hf ** 1.6
            acc.tube(pts, [0.045 * (1 - hf) + 0.012, 0.03, 0.022, 0.015, 0.009, 0.004], 4,
                     [bark] * 6, [min(1, ww0 + 0.5 * t ** 1.5) for t in [i / 5 for i in range(6)]])
            nc = max(3, int(Lb / 0.09))
            for c in range(nc):
                t = 0.15 + 0.85 * (c + rng.random()) / nc
                fi = t * 5
                i0 = min(4, int(fi))
                q = pts[i0].lerp(pts[i0 + 1], fi - i0)
                bd = (pts[i0 + 1] - pts[i0]).normalized()
                side = bd.cross(UP).normalized() * rng.choice((-1, 1))
                up = (bd * 0.8 + side * 0.6 + UP * 0.05).normalized()
                nrm = (UP + side * 0.2).normalized()
                lf = 0.6 + 0.6 * t * (0.6 + 0.4 * hf)
                tint = (lf * 0.95, lf, lf * 0.95)
                _leaf_card(acc, q, up, nrm, rng.uniform(0.55, 0.75) * (0.75 + 0.25 * (1 - hf)), tint,
                           min(1.0, ww0 + 0.6 * t ** 1.5), 1)
                n_cards += 1
        whorl += 1
        z += rng.uniform(0.26, 0.36)
    # leader tuft
    for k in range(6):
        a = math.tau * k / 6
        _leaf_card(acc, Vector((0, 0, height - 0.5)), (UP * 1.5 + Vector((math.cos(a), math.sin(a), 0))).normalized(),
                   Vector((math.cos(a), math.sin(a), 0.3)).normalized(), 0.55, (1.0, 1.05, 1.0), 1.0, 1)
        n_cards += 1
    return acc, {"whorls": whorl, "leaf_cards": n_cards, "height_m": round(max(v[2] for v in acc.v), 3),
                 "leaf_mode": "alpha_spray_cards", "leaf_texture": "needle"}


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


def _cluster_card(acc, centre, n, up, size, tint, ww, mat, shade_n):
    """Cupped square cluster card (4 tris) facing n; custom shading normal = shade_n (crown proxy)."""
    sd = up.cross(n).normalized()
    up = n.cross(sd).normalized()
    h = size * 0.5
    C = centre - n * (0.12 * size)
    P_ = [centre - sd * h - up * h, centre + sd * h - up * h, centre + sd * h + up * h, centre - sd * h + up * h]
    uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]
    ids = [acc.vert(q, tint, ww) for q in P_]
    ci = acc.vert(C, tuple(x * 0.85 for x in tint), ww)
    for i in range(4):
        j = (i + 1) % 4
        acc.face((ids[i], ids[j], ci), mat, uv=[uvs[i], uvs[j], (0.5, 0.5)])
    for vi in ids + [ci]:
        acc.vn[vi] = shade_n


def _lobed_crown(acc, P, branches, wwf, rng, stats, seed, preset):
    """TREE-L3: crown = union of ellipsoid lobes grown around the sub-trees of the lobe_depth
    branches; cluster cards only on the outer shell of the union (+ a sparse dark inner fill),
    facing the lobe normal, shaded with a blended lobe/crown normal (normal transfer)."""
    terms = [b for b in branches if b[2] == P["depth"]]
    seeds = [b[0][-1] for b in branches if b[2] == P["lobe_depth"]]
    centres = []
    for q in seeds:  # greedy merge of nearby sub-tree ends
        for c in centres:
            if (c[0] / c[1] - q).length < P["lobe_merge"]:
                c[0] += q
                c[1] += 1
                break
        else:
            centres.append([q.copy(), 1])
    centres = [c[0] / c[1] for c in centres]
    groups = {i: [] for i in range(len(centres))}
    for b in terms:
        tp = b[0][-1]
        i = min(range(len(centres)), key=lambda k: (centres[k] - tp).length)
        groups[i].append(tp)
    lobes = []
    for i, c in enumerate(centres):
        pts = groups[i] or [c]
        cc = sum(pts, Vector()) / len(pts)
        cc = cc.lerp(c, 0.3)
        r = max((p - cc).length for p in pts) * 0.8 + P["lobe_pad"]
        lobes.append((cc, max(0.55, min(2.1, r)), P["lobe_zscale"]))
    stats["lobes"] = len(lobes)
    crown_c = sum((l[0] for l in lobes), Vector()) / len(lobes)
    top = max(l[0].z + l[1] * l[2] for l in lobes)

    def inside_other(q, skip):
        for j, (c, r, zs) in enumerate(lobes):
            if j == skip:
                continue
            d = q - c
            if (d.x / r) ** 2 + (d.y / r) ** 2 + (d.z / (r * zs)) ** 2 < 0.72:
                return True
        return False
    golden = math.pi * (3 - math.sqrt(5))
    lo_t, hi_t = P["tint"]
    for li, (c, r, zs) in enumerate(lobes):
        area = 4 * math.pi * r * r * (0.5 + 0.5 * zs)
        n = int(area * P["card_density"])
        for k in range(n):
            zz = 1 - 2 * (k + rng.random()) / n
            rad = math.sqrt(max(0.0, 1 - zz * zz))
            th = golden * k + rng.uniform(-0.2, 0.2)
            dvec = Vector((math.cos(th) * rad, math.sin(th) * rad, zz))
            if dvec.z < -0.45 and rng.random() < 0.35:
                continue
            q = c + Vector((dvec.x * r, dvec.y * r, dvec.z * r * zs)) * rng.uniform(0.82, 1.0)
            if q.z < P["bare_below"] or inside_other(q, li):
                continue
            nl = Vector((dvec.x / r, dvec.y / r, dvec.z / (r * zs))).normalized()
            ncrown = (q - crown_c).normalized()
            shade = (nl * 0.55 + ncrown * 0.45).normalized()
            face = (nl + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * 0.3).normalized()
            upv = Matrix.Rotation(rng.uniform(-0.7, 0.7), 3, face) @ (UP - face * face.dot(UP) if abs(face.z) < 0.97 else Vector((0, 1, 0)))
            lt = 0.5 + 0.5 * shade.z
            tv = lo_t + (hi_t - lo_t) * lt
            warm = max(0.0, shade.z) * 0.12
            hue = rng.uniform(-0.05, 0.05)
            tint = (tv * (1 + warm + hue), tv * (1 + warm * 0.6), tv * (1 - warm * 1.4 - hue))
            ww = min(1.0, (q.z / top) ** 1.2 + 0.1)
            _cluster_card(acc, q, face, upv.normalized(), rng.uniform(*P["card_size"]), tint, ww, 1, shade)
            stats["leaf_cards"] += 1
        # sparse inner fill: dark-green (not black) depth so gaps never show a void
        for k in range(int(n * 0.18)):
            dvec = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))).normalized()
            q = c + Vector((dvec.x * r, dvec.y * r, dvec.z * r * zs)) * rng.uniform(0.45, 0.7)
            if q.z < P["bare_below"]:
                continue
            face = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.2, 1))).normalized()
            tv = lo_t * 0.85
            _cluster_card(acc, q, face, _perp(face), rng.uniform(*P["card_size"]), (tv, tv, tv * 0.95),
                          min(1.0, (q.z / top) ** 1.2 + 0.05), 1, (q - crown_c).normalized())
            stats["leaf_cards"] += 1
    # fruit clusters on the outer shell (apple), readable at 96 px
    if P["apples"]:
        ap = new_rng(seed, "apples:" + preset)
        for k in range(P["apples"] // 3):
            c, r, zs = lobes[ap.randrange(len(lobes))]
            dvec = Vector((ap.uniform(-1, 1), ap.uniform(-1, 1), ap.uniform(-0.7, 0.35))).normalized()
            q = c + Vector((dvec.x * r, dvec.y * r, dvec.z * r * zs)) * 0.97
            if q.z < P["bare_below"] - 0.2:
                continue
            base = (0.66, 0.05, 0.035) if ap.random() < 0.8 else (0.72, 0.42, 0.06)
            for m in range(ap.randint(2, 4)):
                off = Vector((ap.uniform(-1, 1), ap.uniform(-1, 1), ap.uniform(-1, 0.3))) * 0.07
                rr = ap.uniform(0.045, 0.06)
                _apple(acc, q + dvec * 0.06 + off, rr, jitter_col(ap, base, 0.1), min(1.0, (q.z / top) ** 1.2 + 0.1), 2)
                stats["apples"] += 1


def build_tree(seed, preset="deciduous"):
    P = TREE_PRESETS[preset]
    rng = new_rng(seed, "tree:" + preset)
    acc = MeshAcc()
    stats = {"branches": 0, "leaf_cards": 0, "apples": 0, "lobes": 0, "max_depth": P["depth"], "leaf_mode": "TREE-L3 lobed cluster crown, shell cards, lobe-normal transfer", "leaf_texture": P["tex"]}
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
    for pts, radii, depth, path0, step in branches:
        stats["branches"] += 1
        sides = max(3, P["sides0"] - depth * 3) if depth < 3 else 3
        cols, wws = [], []
        rj = []
        for i, p in enumerate(pts):
            sh = 0.8 + 0.25 * min(1.0, p.z / 3.0)
            cols.append(jitter_col(leaf_rng, tuple(c * sh for c in bark), 0.06))
            wws.append(wwf(path0 + step * i))
            rj.append([1.0 + (0.07 if depth == 0 else 0.03) * math.sin(3 * s + i * 0.7 + depth)
                       for s in range(sides)])
        rr = list(radii)
        if depth == 0:
            for i in range(min(3, len(rr))):
                rr[i] *= 1.0 + 0.55 * (1 - i / 3.0) ** 2
        acc.tube(pts, rr, sides, cols, wws, mat=0, cap_tip=depth >= 2, rjit=rj)
    _lobed_crown(acc, P, branches, wwf, leaf_rng, stats, seed, preset)
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
                       droop=0.45, seedheads=0, dry=0.12, base=(0.03, 0.07, 0.015), tip=(0.36, 0.52, 0.10)),
    # meadow clump with a few seed stems
    "meadow": dict(tillers=(5, 7), blades=(16, 24), L=(0.16, 0.55), w=(0.006, 0.012), spread=0.10,
                   droop=0.4, seedheads=5, dry=0.15, base=(0.03, 0.065, 0.014), tip=(0.42, 0.54, 0.12)),
    # tall lax clump that flops over (field margins)
    "tall_lax": dict(tillers=(3, 5), blades=(18, 26), L=(0.30, 0.80), w=(0.007, 0.013), spread=0.08,
                     droop=0.4, seedheads=3, dry=0.2, base=(0.03, 0.06, 0.014), tip=(0.46, 0.52, 0.14)),
    # SW coastal dune grass: stiff, blue-grey, rolled leaves
    "coastal_dune": dict(tillers=(4, 6), blades=(14, 20), L=(0.25, 0.62), w=(0.004, 0.007), spread=0.12,
                         droop=0.25, seedheads=4, dry=0.25, base=(0.07, 0.09, 0.06), tip=(0.40, 0.46, 0.33)),
    # lush arching bank sedge (east river banks, ditches)
    "sedge": dict(tillers=(4, 6), blades=(14, 20), L=(0.35, 0.75), w=(0.009, 0.015), spread=0.1,
                  droop=0.5, seedheads=2, dry=0.08, base=(0.025, 0.075, 0.015), tip=(0.30, 0.50, 0.08)),
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
    # ECO-G2: droop capped by height so the tip keeps >= ~half of its upright height
    sag = min(droop * (L / 0.5) ** 1.5, 0.5 * max(0.2, d0.z))
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
        # off-centre tillers (not a single radial disc: VEG-F1 stopped); ECO-G2 packs them
        # tighter (0.6x) so they fuse over the basal ring into one silhouette
        a = rng.uniform(0, math.tau)
        r = P["spread"] * 0.6 * (0.35 + 0.65 * rng.random())
        tb = Vector((math.cos(a) * r, math.sin(a) * r, 0))
        tlean = (UP + Vector((math.cos(a), math.sin(a), 0)) * rng.uniform(0.15, 0.45) + clump_lean).normalized()
        nb = int(rng.randint(*P["blades"]) * 1.8) // max(1, nt // 3)
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
    # ECO-G2 fused basal mass: a dense ring of short, wide, outward-arching blades around the clump
    # crown so separate tillers read as one tuft (G2 review 01: tillers separated into tufts)
    Lmean = 0.5 * (P["L"][0] + P["L"][1])
    nring = rng.randint(44, 60)
    for k in range(nring):
        phi = math.tau * k / nring + rng.uniform(-0.08, 0.08)
        rr = P["spread"] * rng.uniform(0.2, 0.55)
        b0 = Vector((math.cos(phi) * rr, math.sin(phi) * rr, 0))
        lean = (UP + Vector((math.cos(phi), math.sin(phi), 0)) * rng.uniform(0.45, 0.9)).normalized()
        Lr = Lmean * rng.uniform(0.35, 0.6)
        _blade(acc, rng, b0, lean, Lr, P["w"][1] * 1.6, 0.25, P["base"], lerp(P["base"], P["tip"], 0.6),
               0.3 * (Lr / Lmax) ** 0.5, nseg=4)
        stats["basal_ring"] = stats.get("basal_ring", 0) + 1
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
    # ECO-G2 clump-level AO: darker low core, light warm crown (applied to all clump vertices)
    hmax = max(v[2] for v in acc.v)
    for i, v in enumerate(acc.v):
        rad = math.hypot(v[0], v[1]) / max(0.01, P["spread"] * 1.5)
        ao = 0.45 + 0.55 * min(1.0, max(0.0, v[2]) / (0.45 * hmax)) ** 0.7 * (0.75 + 0.25 * min(1.0, rad))
        c = acc.col[i]
        acc.col[i] = (c[0] * ao, c[1] * ao, c[2] * ao, 1.0)
    stats["height_m"] = round(hmax, 3)
    stats["method"] = "ECO-G2 fused basal ring + tillers + clump AO"
    return acc, stats


# =============================================================================== WHEAT FIELD (seeded scatter)
def _wheat_stalk(acc, rng, base, H, ripe):
    lean = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)) * (0.06 if rng.random() > 0.06 else 0.55)  # 6% lodged
    d = (UP + lean).normalized()
    nod = rng.uniform(0.02, 0.07)  # heavy ear nods
    nseg = 5
    pts = []
    for i in range(nseg + 1):
        t = i / nseg
        p = base + d * H * t
        p.x += nod * t ** 3
        pts.append(p)
    stem_c = lerp((0.36, 0.42, 0.12), (0.80, 0.58, 0.20), ripe)
    acc.tube(pts, [0.0032, 0.003, 0.0028, 0.0026, 0.0024, 0.002], 3,
             [jitter_col(rng, lerp(tuple(c * 0.7 for c in stem_c), stem_c, i / nseg), 0.05) for i in range(nseg + 1)],
             [(i / nseg) ** 1.5 for i in range(nseg + 1)], cap_tip=False)
    # ear: spindle with alternating grain bulges
    top = pts[-1]
    ed = (pts[-1] - pts[-2]).normalized()
    eL = rng.uniform(0.09, 0.12)
    epts = [top + ed * eL * j / 8 for j in range(9)]
    erad = [0.006 + 0.0045 * math.sin(math.pi * min(1, j / 7.0)) * (1.0 if j % 2 == 0 else 0.8) for j in range(9)]
    erad[-1] = 0.001
    ear_c = lerp((0.42, 0.48, 0.14), (0.88, 0.60, 0.19), ripe)
    acc.tube(epts, erad, 4, [jitter_col(rng, ear_c, 0.08)] * 9, [1.0] * 9, cap_tip=True)
    # awns: thin slivers fanning up from the ear
    awn_c = lerp((0.46, 0.50, 0.18), (0.94, 0.76, 0.40), ripe)
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
            # irregular, soft field boundary (not a hard rectangle)
            edge += 0.12 * math.sin(x * 3.1 + y * 1.7) + 0.07 * math.sin(x * 7.3 - y * 5.1) - 0.1
            if edge < 0.0:
                continue
            edgef = min(1.0, edge / 0.45)
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
            wob = 0.05 * math.sin(x * 1.9 + j * 0.0)  # rows are hand-dug: slight wander
            ridge = 0.5 + 0.5 * math.cos(math.tau * (y + wob + sy / 2) / (sy / rows))
            z = 0.09 * ridge ** 1.5 + 0.012 * math.sin(x * 23.1 + y * 7.7) + rng.uniform(-0.008, 0.008)
            edge = min(1.0, min(x + sx / 2, sx / 2 - x, y + sy / 2, sy / 2 - y) / 0.3)
            z = z * edge - 0.02 * (1 - edge)
            c = lerp((0.09, 0.055, 0.035), (0.21, 0.145, 0.09), ridge * 0.7 + rng.uniform(0, 0.3))
            c = lerp((0.10, 0.18, 0.04), c, edge ** 0.5)  # blend soil into turf at the bed edge
            vid[i, j] = acc.vert((x, y, z), c, 0.0)
    for i in range(nx):
        for j in range(ny):
            acc.face((vid[i, j], vid[i + 1, j], vid[i + 1, j + 1], vid[i, j + 1]), 0)


def _cabbage(acc, rng, c, lettuce=False):
    head_r = rng.uniform(0.06, 0.11) * (0.55 if lettuce else 1.0)
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
        col = jitter_col(rng, (0.30, 0.48, 0.14) if lettuce else (0.16, 0.30, 0.17), 0.12)
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
    counts = {"cabbage": 0, "carrot": 0, "lettuce": 0, "weeds": 0}
    crops = ["cabbage", "carrot", "lettuce", "carrot", "cabbage"]
    for r in range(rows):
        y = -size[1] / 2 + pitch * (r + 0.0) + 0.0
        y = -size[1] / 2 + pitch * r + pitch * 0.0
        yc = -size[1] / 2 + pitch * r  # ridge crest (cos maximum)
        crop = crops[r % len(crops)]
        step = {"cabbage": 0.42, "carrot": 0.12, "lettuce": 0.3}[crop]
        x = -size[0] / 2 + 0.35 + rng.uniform(0, 0.1)
        while x < size[0] / 2 - 0.35:
            if rng.random() > 0.1:  # gaps (harvested / failed)
                wob = 0.05 * math.sin(x * 1.9)
                c = Vector((x + rng.uniform(-0.05, 0.05), yc - wob + rng.uniform(-0.05, 0.05), 0.08))
                if crop in ("cabbage", "lettuce"):
                    _cabbage(acc, rng, c, lettuce=(crop == "lettuce"))
                else:
                    _carrot_top(acc, rng, c)
                counts[crop] += 1
            x += step * rng.uniform(0.8, 1.25)
    # weeds / edge grass around the bed border
    for k in range(160):
        side = rng.randrange(4)
        t = rng.uniform(-0.5, 0.5)
        x = t * size[0] if side < 2 else (-0.5 if side == 2 else 0.5) * size[0] + rng.uniform(-0.15, 0.15)
        y = (-0.5 if side == 0 else 0.5) * size[1] + rng.uniform(-0.15, 0.15) if side < 2 else t * size[1]
        a = rng.uniform(0, math.tau)
        _blade(acc, rng, Vector((x, y, 0)), (UP + Vector((math.cos(a), math.sin(a), 0)) * 0.5).normalized(),
               rng.uniform(0.08, 0.2), 0.006, 0.4, (0.03, 0.07, 0.015), (0.32, 0.48, 0.10), 0.6, nseg=3)
        counts["weeds"] += 1
    for i in range(soil_faces):
        acc.mi[i] = 1  # soil material slot (crops/weeds use slot 0)
    return acc, {"rows": rows, **counts, "size_m": list(size)}


# =============================================================================== FLOWERS
def _flower(acc, rng, base, kind):
    H = {"daisy": rng.uniform(0.25, 0.38), "poppy": rng.uniform(0.35, 0.5), "spike": rng.uniform(0.45, 0.7)}[kind]
    lean = (UP + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)) * 0.15).normalized()
    pts = [base + lean * H * i / 5 for i in range(6)]
    for i, p in enumerate(pts):
        p.x += 0.02 * (i / 5) ** 2
    acc.tube(pts, [0.0025] * 6, 3, [(0.16, 0.30, 0.09)] * 6, [(i / 5) ** 1.5 for i in range(6)], cap_tip=False)
    for k in range(5):  # basal leaf rosette: flowers grow out of foliage, not bare ground
        a = math.tau * k / 5 + rng.uniform(-0.3, 0.3)
        _blade(acc, rng, base + UP * 0.01, (UP * 0.5 + Vector((math.cos(a), math.sin(a), 0))).normalized(),
               rng.uniform(0.10, 0.18), 0.014, 0.5, (0.04, 0.12, 0.03), (0.22, 0.42, 0.09), 0.4, nseg=3)
    top = pts[-1]
    fd = (pts[-1] - pts[-2]).normalized()
    if kind == "spike":
        col = jitter_col(rng, (0.36, 0.16, 0.62), 0.15)
        for s in range(26):
            t = s / 25
            q = top + fd * (t * 0.2 - 0.05)
            a = s * 2.4
            out = Vector((math.cos(a), math.sin(a), 0))
            r = 0.03 * (1 - 0.65 * t)
            i0 = acc.vert(q, col, 1.0)
            i1 = acc.vert(q + out * r + fd * 0.01, tuple(min(1, x * 1.25) for x in col), 1.0)
            i2 = acc.vert(q + Matrix.Rotation(0.9, 3, UP) @ out * r + fd * 0.006, col, 1.0)
            i3 = acc.vert(q + fd * 0.022, col, 1.0)
            acc.face((i0, i1, i3), 0)
            acc.face((i0, i3, i2), 0)
        return
    if kind == "daisy":
        np_, pl, pw, cup = rng.randint(13, 16), 0.04, 0.009, -0.05
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
        main = ["spike", "daisy", "spike", "poppy", "daisy", "spike", "poppy"][c % 7]
        for k in range(rng.randint(22, 32)):
            r = abs(rng.gauss(0, 0.18))
            a = rng.uniform(0, math.tau)
            kind = main if rng.random() < 0.8 else rng.choice(kinds)
            _flower(acc, rng, Vector((cx + math.cos(a) * r, cy + math.sin(a) * r, 0)), kind)
            counts[kind] += 1
    # interstitial short grass blades so flowers sit in turf
    for k in range(900):  # lush grass bed the flowers grow in (soft irregular boundary)
        while True:
            b = Vector((rng.uniform(-size[0] / 2, size[0] / 2), rng.uniform(-size[1] / 2, size[1] / 2), 0))
            e = (b.x / (size[0] / 2)) ** 2 + (b.y / (size[1] / 2)) ** 2
            if e < 1.0 - 0.25 * rng.random():
                break
        a = rng.uniform(0, math.tau)
        _blade(acc, rng, b, (UP + Vector((math.cos(a), math.sin(a), 0)) * 0.4).normalized(),
               rng.uniform(0.08, 0.22), 0.007, 0.45, (0.03, 0.08, 0.015), (0.34, 0.50, 0.10), 0.6, nseg=3)
    return acc, {**counts, "turf_blades": 900, "size_m": list(size)}


# =============================================================================== FENCE + HEDGEROW
def build_fence(seed, length=6.6, post_gap=2.2):
    """Rough-hewn post-and-rail: irregular 6-sided hewn posts with slanted tops, split rails with
    an irregular quadrilateral section (~11x7 cm), rail ends seated into the posts (no overhang),
    dark weathered timber with grey streaks, moss/dirt at the post foot."""
    rng = new_rng(seed, "fence")
    acc = MeshAcc()
    n_posts = int(round(length / post_gap)) + 1
    posts = []
    wood = (0.15, 0.11, 0.08)
    for i in range(n_posts):
        x = -length / 2 + i * post_gap + rng.uniform(-0.08, 0.08)
        lean = Vector((rng.uniform(-0.07, 0.07), rng.uniform(-0.07, 0.07), 1)).normalized()
        H = rng.uniform(1.0, 1.25)
        base = Vector((x, 0, -0.08))
        pts = [base + lean * H * k / 5 for k in range(6)]
        pts[-1] = pts[-1] + Vector((0, 0, rng.uniform(-0.04, 0.04)))
        rj = [[1.0 + 0.18 * math.sin(s * 2.7 + i * 1.3) + rng.uniform(-0.08, 0.08) for s in range(6)] for _ in pts]
        cols = []
        for k in range(6):
            c = jitter_col(rng, wood, 0.1)
            if k == 0:
                c = (0.10, 0.13, 0.05)  # moss / damp soil at the foot
            elif rng.random() < 0.3:
                c = lerp(c, (0.30, 0.29, 0.26), 0.5)  # silvered weathering streak
            cols.append(c)
        acc.tube(pts, [0.085, 0.08, 0.078, 0.076, 0.074, 0.07], 6, cols, [0] * 6, mat=0, cap_tip=False,
                 cap_base=False, rjit=rj)
        top = pts[-1]
        acc.face([acc.vert(top + Vector((math.cos(math.tau * s / 6), math.sin(math.tau * s / 6), 0)) * 0.07,
                           (0.22, 0.20, 0.16), 0) for s in range(6)], 0)
        posts.append((pts, H))
    for i in range(n_posts - 1):
        for hgt in (0.42 + rng.uniform(-0.04, 0.04), 0.86 + rng.uniform(-0.04, 0.04)):
            pa, Ha = posts[i]
            pb, Hb = posts[i + 1]
            a = pa[0] + (pa[-1] - pa[0]) * (hgt / Ha) + Vector((0.02, 0, 0))
            b = pb[0] + (pb[-1] - pb[0]) * (hgt / Hb) - Vector((0.02, 0, 0))
            pts = []
            for k in range(8):
                t = k / 7
                p = a.lerp(b, t)
                p.z -= 0.03 * math.sin(math.pi * t) + rng.uniform(-0.005, 0.005)
                p.y += 0.012 * math.sin(t * 5 + i)
                pts.append(p)
            sec = [1.45, 0.75, 1.3, 0.8]  # split (wedge/quad) section
            rj = [[sec[s] * (1 + rng.uniform(-0.1, 0.1)) for s in range(4)] for _ in pts]
            cols = [jitter_col(rng, lerp(wood, (0.28, 0.26, 0.22), rng.random() * 0.4), 0.1) for _ in pts]
            acc.tube(pts, [0.045] * 8, 4, cols, [0] * 8, mat=1, cap_tip=False, cap_base=False, rjit=rj)
    return acc, {"posts": n_posts, "length_m": length, "rail_section": "split quad ~11x7 cm"}


def build_hedgerow(seed, length=4.0, height=1.3, depth=1.0):
    """Hedge = elongated shell volume with an irregular plan curve, varying height and rounded ends;
    oak cluster cards on the shell (same palette/shading as trees) + dark inner fill, woody stems kept
    inside the volume, grass skirt along the base."""
    rng = new_rng(seed, "hedge")
    acc = MeshAcc()
    half_l = length / 2
    ph = rng.uniform(0, 6)

    def yc(x):
        return 0.16 * math.sin(x * 0.9 + ph)

    def hx(x):
        e = max(0.0, 1 - (abs(x) / half_l) ** 4) ** 0.5
        return height * (0.85 + 0.1 * math.sin(x * 1.7 + ph) + 0.06 * math.sin(x * 4.3)) * e, e
    cards = 0
    for s_ in range(9):
        x = -half_l * 0.75 + 1.5 * half_l * s_ / 8 + rng.uniform(-0.1, 0.1)
        h, e = hx(x)
        base = Vector((x, yc(x), 0))
        for k in range(2):
            d = (UP + Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), 0))).normalized()
            L = h * rng.uniform(0.45, 0.7)
            pts = [base + d * L * i / 4 for i in range(5)]
            acc.tube(pts, [0.025, 0.02, 0.015, 0.01, 0.006], 4, [(0.20, 0.15, 0.10)] * 5, [0.05 * i for i in range(5)])
    n = int(length * height * 52)
    for k in range(n):
        x = rng.uniform(-half_l, half_l)
        h, e = hx(x)
        if h < 0.15:
            continue
        phi = rng.uniform(-0.15 * math.pi, 1.15 * math.pi)  # cross-section arc from ground to ground
        wy = depth / 2 * (0.55 + 0.45 * e)
        rr = rng.uniform(0.85, 1.0)
        y = math.cos(phi) * wy * rr
        z = max(0.05, math.sin(phi) * h * rr)
        # rounded ends: push shell outward along x near the ends
        xe = x + (math.copysign(0.25 * (1 - e), x) if e < 0.6 else 0.0)
        q = Vector((xe, yc(x) + y, z))
        nl = Vector((0.6 * (1 - e) * math.copysign(1, x), math.cos(phi) / wy, math.sin(phi) / max(0.2, h))).normalized()
        face = (nl + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * 0.3).normalized()
        upv = (UP - face * face.dot(UP)) if abs(face.z) < 0.97 else Vector((1, 0, 0))
        upv = Matrix.Rotation(rng.uniform(-0.7, 0.7), 3, face) @ upv
        lt = 0.5 + 0.5 * nl.z
        tv = 0.62 + 0.55 * lt * min(1.0, z / (0.6 * height))
        warm = max(0.0, nl.z) * 0.1
        tint = (tv * (1 + warm), tv * (1 + warm * 0.6), tv * (1 - warm * 1.4))
        _cluster_card(acc, q, face, upv.normalized(), rng.uniform(0.42, 0.58), tint,
                      min(1.0, 0.25 + 0.75 * (z / height) ** 1.5), 1, nl)
        cards += 1
    for k in range(int(n * 0.2)):
        x = rng.uniform(-half_l * 0.85, half_l * 0.85)
        h, e = hx(x)
        q = Vector((x, yc(x) + rng.uniform(-0.25, 0.25) * depth, rng.uniform(0.15, 0.7) * h))
        face = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.3, 1))).normalized()
        _cluster_card(acc, q, face, _perp(face), 0.5, (0.5, 0.5, 0.48), 0.3, 1, Vector((0, 0, 1)))
        cards += 1
    for k in range(220):  # grass skirt: the hedge base sits in long grass
        x = rng.uniform(-half_l - 0.2, half_l + 0.2)
        sd = rng.choice((-1, 1))
        b0 = Vector((x, yc(x) + sd * (depth / 2 * rng.uniform(0.6, 1.05)), 0))
        a_ = rng.uniform(0, math.tau)
        _blade(acc, rng, b0, (UP + Vector((math.cos(a_), math.sin(a_), 0)) * 0.5).normalized(),
               rng.uniform(0.15, 0.4), 0.007, 0.45, (0.03, 0.07, 0.015), (0.38, 0.50, 0.11), 0.7, nseg=4)
    return acc, {"length_m": length, "height_m": height, "leaf_cards": cards, "method": "cluster-card shell"}


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
    plum = (0.30, 0.12, 0.045)
    plum_light = (0.50, 0.25, 0.09)

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
    acc.v = [(x * 0.85, y * 0.85, z * 0.85) for (x, y, z) in acc.v]  # hen ~0.41 m (G2-01: 0.48 too tall)
    return acc, {"height_m": round(max(v[2] for v in acc.v), 3),
                 "status_note": "STRUCTURAL_BLOCKOUT_NOT_ART (metaball form; slab wings/tail, no plumage, no rig)"}


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
        if co.y > 1.3 or (co.z < 0.75 and abs(co.x) < 0.2 and abs(co.y) < 0.6):
            return (0.80, 0.76, 0.68)  # pale muzzle / belly
        return (0.32, 0.17, 0.08) if v < 0.9 else (0.80, 0.76, 0.68)  # brown with white patches
    acc.add_mesh(me, Matrix.Identity(4), col, lambda co: 0.0)
    bpy.data.meshes.remove(me)
    for sx in (-1, 1):  # horns
        acc.tube([Vector((sx * 0.12, 1.15, 1.13)), Vector((sx * 0.22, 1.18, 1.2)), Vector((sx * 0.25, 1.24, 1.28))],
                 [0.03, 0.02, 0.006], 6, [(0.75, 0.70, 0.58)] * 3, [0] * 3)
    acc.tube([Vector((0, -0.95, 1.12)), Vector((0, -1.05, 0.8)), Vector((0, -1.07, 0.5))], [0.03, 0.02, 0.035], 5,
             [(0.1, 0.1, 0.1)] * 3, [0, 0.2, 0.4])
    return acc, {"height_m": round(max(v[2] for v in acc.v), 3), "status_note": "STRUCTURAL_BLOCKOUT_NOT_ART"}


# =============================================================================== ROCKS (river / coastal)
def _rock(acc, rng, centre, size, squash, kind, subdiv=3):
    import bmesh
    from mathutils import noise
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    off = Vector((rng.uniform(-50, 50), rng.uniform(-50, 50), rng.uniform(-50, 50)))
    planes = []
    for k in range(3 if kind == "river" else 5):
        pn = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.3, 1))).normalized()
        planes.append((pn, rng.uniform(0.75, 0.95)))
    vids = {}
    for vx in bm.verts:
        n = vx.co.normalized()
        q = n * 1.3 + off
        d = 0.0
        amp, fr = 0.42, 1.0
        for o in range(5):
            d += amp * noise.noise(q * fr, noise_basis="PERLIN_ORIGINAL")
            amp *= 0.48
            fr *= 2.2
        # cleavage planes: clamp against 3 random planes for angular river cobbles / boulders
        for pl in planes:
            d = min(d, (pl[1] - n.dot(pl[0])) * 1.4)
        if kind == "coastal":
            # sedimentary layering: terraced bands + cleaved flat faces
            z = n.z
            d += 0.07 * math.sin(z * 14 + noise.noise(q * 0.5) * 2) - 0.05 * abs(math.sin(z * 7))
            facet = max(abs(n.x), abs(n.y)) ** 6 * 0.25
            d -= facet
        r = 1.0 + d
        p = Vector((n.x * r * size[0], n.y * r * size[1], n.z * r * size[2] * squash))
        if p.z < -0.15 * size[2]:
            p.z = -0.15 * size[2] - (p.z + 0.15 * size[2]) * 0.1  # buried flat base
        top = max(0.0, n.z)
        if kind == "river":
            base = (0.17, 0.16, 0.145)
            wet = (0.05, 0.048, 0.045)
            moss = (0.10, 0.20, 0.04)
            c = lerp(wet, base, min(1.0, (p.z + 0.05 * size[2]) / (0.35 * size[2]) + 0.2))
            mf = max(0.0, top - 0.55) * 2.2 * (0.5 + 0.5 * noise.noise(q * 3.0))
            c = lerp(c, moss, max(0.0, min(1.0, mf)))
        else:
            base = (0.36, 0.33, 0.28)
            band = 0.85 + 0.15 * math.sin(n.z * 14)
            c = tuple(x * band for x in base)
            if n.z < -0.05:
                c = lerp(c, (0.10, 0.09, 0.08), min(1.0, -n.z * 3))  # wet tide line
            lich = noise.noise(q * 6.0)
            if lich > 0.35 and top > 0.2:
                c = lerp(c, (0.55, 0.50, 0.25), 0.6)  # yellow lichen spots
            if top > 0.75:
                c = lerp(c, (0.20, 0.27, 0.10), 0.5)  # thin turf on the top
        c = jitter_col(rng, c, 0.04)
        vids[vx.index] = acc.vert(centre + p, c, 0.0)
    for f in bm.faces:
        acc.face([vids[v.index] for v in f.verts], 0)
    bm.free()


def build_rock_set(seed, kind="river"):
    rng = new_rng(seed, "rocks:" + kind)
    acc = MeshAcc()
    if kind == "river":
        spec = [((0, 0, 0), (0.55, 0.42, 0.35), 0.8), ((0.75, 0.25, 0), (0.32, 0.26, 0.24), 0.8),
                ((-0.6, 0.35, 0), (0.28, 0.24, 0.2), 0.75), ((0.3, -0.55, 0), (0.22, 0.2, 0.16), 0.7),
                ((-0.25, -0.5, 0), (0.14, 0.12, 0.1), 0.7), ((1.15, -0.2, 0), (0.16, 0.13, 0.11), 0.7),
                ((-1.0, -0.15, 0), (0.12, 0.1, 0.09), 0.7)]
        for c, sz, sq in spec:
            _rock(acc, rng, Vector(c), sz, sq, "river", subdiv=4)
    else:
        spec = [((0, 0, 0), (1.6, 1.1, 1.4), 1.0), ((1.9, 0.6, 0), (0.9, 0.8, 1.1), 1.0),
                ((-1.5, 0.8, 0), (0.8, 0.7, 0.6), 1.0), ((0.9, -1.2, 0), (0.45, 0.4, 0.3), 0.9),
                ((-0.8, -1.1, 0), (0.3, 0.28, 0.22), 0.9)]
        for c, sz, sq in spec:
            _rock(acc, rng, Vector(c), sz, sq, "coastal", subdiv=5 if sz[0] > 0.7 else 4)
    return acc, {"kind": kind, "rocks": len(spec), "height_m": round(max(v[2] for v in acc.v), 3)}


# =============================================================================== RIVER MODULE (water + banks)
RIVER_LEN, RIVER_W = 14.0, 3.0


def river_centre_world(y, x0=0.0, y_scale=1.0, length=RIVER_LEN):
    """World x of the module centreline at world y (module placed at x0, scaled in y)."""
    s = y / y_scale + length / 2
    return x0 + 1.1 * math.sin(s / length * math.pi * 1.4)


def _river_centre(s, length):
    return Vector((1.1 * math.sin(s / length * math.pi * 1.4), s - length / 2, 0))


def build_river_water(seed, length=14.0, width=3.0, nu=16, nv=120):
    """Water surface ribbon following a meandering centreline. Attributes flow_u (m along) and
    flow_v (-1..1 across) feed LIND_WaterFlow; colour = deep centre / shallow edge."""
    acc = MeshAcc()
    fu, fv = [], []
    grid = {}
    for j in range(nv + 1):
        s = length * j / nv
        c = _river_centre(s, length)
        t = (_river_centre(min(length, s + 0.05), length) - _river_centre(max(0, s - 0.05), length)).normalized()
        side = t.cross(UP).normalized()
        w = width * (1 + 0.12 * math.sin(s * 0.9))
        for i in range(nu + 1):
            v = -1 + 2 * i / nu
            p = c + side * (v * w / 2)
            p.z = -0.48
            depth = 1 - v * v
            col = lerp((0.10, 0.22, 0.22), (0.02, 0.07, 0.09), depth)
            grid[i, j] = acc.vert(p, col, 0.0)
            fu.append(s)
            fv.append(v)
    for j in range(nv):
        for i in range(nu):
            acc.face((grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]), 0)
    acc.extra["flow_u"] = fu
    acc.extra["flow_v"] = fv
    return acc, {"length_m": length, "width_m": width, "flow_attrs": ["flow_u", "flow_v"]}


def build_river_bank(seed, length=14.0, width=3.0, nv=120):
    """Static channel: submerged bed + sloped muddy banks rising to a grassy top (preview terrain
    for the module only; WORLD/Codex owns real terrain)."""
    rng = new_rng(seed, "bank")
    acc = MeshAcc()
    # cross-section offsets (fraction of half-width beyond centre) and heights
    prof = [(o, h - 0.42) for o, h in [(-4.6, 0.42), (-2.4, 0.42), (-1.7, 0.40), (-1.35, 0.28), (-1.1, 0.10), (-1.0, -0.05),
                                         (-0.7, -0.32), (0.0, -0.45), (0.7, -0.32), (1.0, -0.05), (1.1, 0.10),
                                         (1.35, 0.28), (1.7, 0.40), (2.4, 0.42), (4.6, 0.42)]]
    grid = {}
    for j in range(nv + 1):
        s = length * j / nv
        c = _river_centre(s, length)
        t = (_river_centre(min(length, s + 0.05), length) - _river_centre(max(0, s - 0.05), length)).normalized()
        side = t.cross(UP).normalized()
        w = width * (1 + 0.12 * math.sin(s * 0.9))
        for i, (o, h) in enumerate(prof):
            ext = o if abs(o) <= 1.0 else math.copysign(1.0 + (abs(o) - 1.0) * (1.6 / w * 2), o)
            p = c + side * (ext * w / 2)
            p.z = h + (0.03 * math.sin(s * 2.3 + i) + rng.uniform(-0.01, 0.01)) * (0.0 if abs(o) > 2.3 else 1.0)
            p.z -= 0.004 if abs(o) > 4.0 else 0.0
            h += 0.42
            if h < -0.1:
                col = lerp((0.12, 0.10, 0.07), (0.20, 0.19, 0.16), rng.random())  # gravel bed
            elif h < 0.2:
                col = (0.10, 0.075, 0.05)  # wet mud
            elif h < 0.35:
                col = lerp((0.14, 0.12, 0.07), (0.09, 0.18, 0.04), 0.5)
            else:
                # blend toward the preview ground tone at the outer edge (no visible seam)
                col = lerp((0.09, 0.19, 0.04), (0.11, 0.20, 0.045), min(1.0, (abs(o) - 1.7) / 0.7))
            grid[i, j] = acc.vert(p, col, 0.0)
    n = len(prof)
    for j in range(nv):
        for i in range(n - 1):
            top = abs(prof[i][0]) >= 2.4 and abs(prof[i + 1][0]) >= 2.4
            acc.face((grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]), 1 if top else 0)
    return acc, {"length_m": length, "status_note": "module-local preview banks; not world terrain"}

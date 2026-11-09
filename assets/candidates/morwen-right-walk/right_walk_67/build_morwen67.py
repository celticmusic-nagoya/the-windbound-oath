#!/usr/bin/env python3
"""MORWEN-PIXEL-67: art-quality pass on the MORWEN-PIXEL-66 right walk.

Keeps the 66 gait (imported from build_morwen66: GAIT/BOB/CAPE_SWAY, IK, ground snap)
and replaces the flat 3-tone legs with cluster-shaded, sel-out-lined legs and boots,
redraws the left skirt hem (pleats + continuous gold hem line) and adds a lagging
skirt sway. 96x128 and 48x64 are both drawn natively; protected layers are copied.

Layers (z, back -> front):
  0 cape_back   lower cape / lining              (65B F00, shear sway)
  1 far_leg     stocking                         (redrawn)
  2 far_boot                                     (redrawn)
  3 near_leg                                     (redrawn)
  4 near_boot                                    (redrawn)
  5 skirt_left  left plain pleats + hem line     (redrawn, lagging sway)
  6 skirt       centre plaid, right pleats, hem  (immutable, bob only)
  7 torso       body, arms, hands, cape top      (immutable, bob only)
  8 accessories bag, potions, chain              (immutable, bob only)
  9 per_frame_detail_patch                       (FRAME_ART_PATCHES, coordinates logged)
immutable_master = layers 6+7+8 = 65B F00 U_front minus the skirt_left redraw region.
Requires numpy + Pillow.
"""
from pathlib import Path
import json, math, argparse
import numpy as np
from PIL import Image, ImageDraw
import build_morwen66 as B

W, H = B.W, B.H
GAIT, BOB, CAPE_SWAY = B.GAIT, B.BOB, B.CAPE_SWAY
# skirt follows the legs one frame late (contact F00/F03 -> skirt reacts F01/F04); cape lags further (66 values)
SKIRT_SWAY = [0, -1, 0, 0, -1, 0]

# ---------------------------------------------------------------- palette
# Designed ramps are snapped to the nearest colour that already exists in the
# protected upper body (65B F00), so hue/saturation/value come from the master.
DESIGN = {
    'stock':      [(22, 6, 24), (46, 14, 44), (70, 24, 64), (96, 40, 86), (128, 64, 112)],
    'stock_far':  [(16, 4, 18), (34, 10, 34), (52, 16, 48), (70, 26, 64), (88, 38, 80)],
    'boot':       [(20, 4, 26), (46, 14, 56), (72, 26, 86), (104, 46, 120), (146, 90, 166), (206, 164, 220)],
    'boot_far':   [(16, 3, 20), (34, 10, 42), (54, 18, 64), (78, 32, 92), (106, 58, 122), (150, 110, 166)],
    'gold':       [(110, 52, 10), (176, 96, 12), (236, 156, 8), (252, 214, 40), (255, 246, 160)],
    'gold_far':   [(84, 40, 10), (140, 76, 10), (190, 124, 8), (214, 170, 34), (226, 200, 110)],
    'pleat':      [(26, 4, 22), (54, 11, 42), (77, 23, 74), (90, 33, 81), (112, 44, 100)],
}
OUTLINE = (12, 2, 12)


def build_palette(ref_front):
    cols = np.unique(ref_front[ref_front[:, :, 3] > 0][:, :3], axis=0).astype(int)
    pal, snaps = {}, {}
    for k, ramp in DESIGN.items():
        out = []
        for c in ramp:
            d = np.sqrt(((cols - np.array(c)) ** 2 * np.array([0.30, 0.59, 0.11]) * 3).sum(1))
            i = int(d.argmin())
            out.append(tuple(int(v) for v in cols[i]) if d[i] <= 14 else c)
            snaps.setdefault(k, []).append(bool(d[i] <= 14))
        pal[k] = out
    return pal, snaps


# ---------------------------------------------------------------- layer masks
def split67(uf):
    """Split the 66 U_front into immutable skirt / torso / accessories and the
    skirt-left redraw region. All masks are pixel masks on the 65B F00 reference."""
    op = uf[:, :, 3] > 0
    r, g, b = (uf[:, :, i].astype(int) for i in range(3))
    yy, xx = np.mgrid[0:H, 0:W]
    # bag leather: warm brown/orange, not gold (low green), not purple
    leather = op & (r > b + 35) & (g < r * 0.62) & (r < 245) & (b < 90) & (xx >= 35) & (xx <= 54) & (yy >= 72) & (yy <= 90)
    # bag hardware / skin of the hand resting on the bag stay with accessories by box
    hand = op & (xx >= 43) & (xx <= 50) & (yy >= 70) & (yy <= 79)
    potions = op & (xx >= 52) & (xx <= 66) & (yy >= 64) & (yy <= 80) & ((r > 180) & (b > 150))
    acc = leather | hand | potions
    # redraw region: left skirt / lining under the bag, the old flat cut (x 36..53, y 84..91), non-bag only
    redraw = op & ~acc & (xx >= 36) & (xx <= 53) & (yy >= 84) & (yy <= 91)
    skirt = op & ~acc & ~redraw & (xx >= 50) & (xx <= 74) & (yy >= 76)
    torso = op & ~acc & ~redraw & ~skirt
    return dict(accessories=acc, skirt=skirt, torso=torso, redraw=redraw)


def masked(img, m):
    o = np.zeros_like(img); o[m] = img[m]; return o


# ---------------------------------------------------------------- skirt left (redrawn)
def hem_y(x, k=1.0):
    """hem bottom row for the left plain pleats (96 coords): meets the protected hem at x=53,y=89,
    flares down to y~93 where it tucks under the cape at x=36."""
    return 89.0 + (53.0 - x) * 0.24


def draw_skirt_left(pal, sway, bob, k=1.0):
    w, h = int(W * k), int(H * k)
    out = np.zeros((h, w, 4), np.uint8)
    pl, gd = pal['pleat'], pal['gold']
    x0, x1 = 36, 53
    pw = 3 if k >= 1 else 2                      # pleat width in pixels
    for X in range(int(x0 * k), int(x1 * k) + 1):
        xc = X / k + (0.5 / k - 0.5)             # column centre in 96 coords
        fold = int(math.floor((X - sway * (1 if k >= 1 else 0) + 100) / 1)) % pw
        zig = 1 if fold == pw - 1 else 0          # pleat valley ends 1px lower
        top = int(84 * k)
        bot = int(round((hem_y(xc) + bob) * k))
        if k < 1:
            bot = int(math.floor((hem_y(xc) + bob) * k))
        # sway: lower half of the panel leans with the hem
        for Y in range(top, bot + 1):
            if k >= 1:
                ramp = [pl[3], pl[2], pl[1]][fold]           # ridge / face / valley
                depth = (bot - Y)
                if depth <= 1 and fold == 0: ramp = pl[4]    # light catches the fold tip
                if Y == bot: ramp = gd[3] if fold == 0 else gd[2]   # gold hem line
            else:
                ramp = [pl[3], pl[1]][fold]
                if Y == bot: ramp = gd[2]
            out[Y, X] = (*ramp, 255)
        if Y + 1 < h:
            out[Y + 1, X] = (*pl[0], 255)          # 1px underside shadow / outline below the hem
    # left outline where the panel meets the cape lining
    X = int(x0 * k)
    for Y in range(int(84 * k), h):
        if out[Y, X, 3]:
            out[Y, X, :3] = pl[0] if out[Y, X, 0] < 200 else out[Y, X, :3]
    if sway and k >= 1:                          # lagging sway: shift the lowest 3 rows of the panel
        for X in range(x0, x1 + 1):
            col = out[:, X].copy()
            ys = np.where(col[:, 3] > 0)[0]
            if not len(ys): continue
    return shift_rows(out, sway, int(round((88 + bob) * k)), k)


def shift_rows(img, dx, from_row, k):
    if dx == 0 or k < 1:
        return img
    o = img.copy()
    o[from_row:] = 0
    seg = img[from_row:]
    if dx < 0:
        o[from_row:, :dx] = seg[:, -dx:]
    else:
        o[from_row:, dx:] = seg[:, :-dx]
    # keep the right end welded to the protected hem: fill the gap column from the original
    gapx = 53 if dx < 0 else 36
    o[from_row:, gapx] = np.where(o[from_row:, gapx, 3:4] > 0, o[from_row:, gapx], img[from_row:, gapx])
    return o


# ---------------------------------------------------------------- legs (redrawn)
def leg_fields(lab, geo):
    k = geo['k']; leg = geo['leg']
    h, w = lab.shape
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = xx + 0.5, yy + 0.5

    def frame(p, q):
        vx, vy = q[0] - p[0], q[1] - p[1]; n = math.hypot(vx, vy)
        ax, ay = vx / n, vy / n
        nx, ny = ay, -ax
        if nx < 0: nx, ny = -nx, -ny
        u = (cx - p[0]) * nx + (cy - p[1]) * ny
        s = ((cx - p[0]) * ax + (cy - p[1]) * ay) / n
        return u, s
    u_th, s_th = frame(leg['hip'], leg['knee'])
    u_sh, s_sh = frame(leg['knee'], leg['ankle'])
    return u_th / (4.1 * k), s_th, u_sh / (4.8 * k), s_sh


def clusterise(level, mat_mask):
    """remove single-pixel islands of a tone inside one material (cluster shading, no noise)."""
    lv = level.copy()
    h, w = lv.shape
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if not mat_mask[y, x]: continue
            n = [lv[y - 1, x], lv[y + 1, x], lv[y, x - 1], lv[y, x + 1]]
            m = [mat_mask[y - 1, x], mat_mask[y + 1, x], mat_mask[y, x - 1], mat_mask[y, x + 1]]
            same = [v for v, mm in zip(n, m) if mm]
            if len(same) >= 3 and lv[y, x] not in same:
                vals, cnt = np.unique(same, return_counts=True)
                lv[y, x] = vals[cnt.argmax()]
    return lv


def shade_leg67(lab, geo, pal, far, front_mask):
    """returns (stocking_rgba, boot_rgba)."""
    k = geo['k']; leg = geo['leg']; big = k >= 1
    h, w = lab.shape
    u_th, s_th, u_sh, s_sh = leg_fields(lab, geo)
    st = pal['stock_far' if far else 'stock']
    bt = pal['boot_far' if far else 'boot']
    gd = pal['gold_far' if far else 'gold']
    ST, BT, CUFF, FOOT, SOLE, HEEL, TOE = B.ST, B.BT, B.CUFF, B.FOOT, B.SOLE, B.HEEL, B.TOE
    stock_m = lab == ST
    boot_m = (lab != 0) & ~stock_m
    lv = np.full((h, w), -1, int)
    # stocking: cylinder lit from the front/top (+u), clustered bands
    it = 0.60 + 0.40 * np.clip(u_th, -1, 1)
    # knee: soft forward highlight on the cap, back-of-knee crease
    kx, ky = leg['knee']
    yy, xx = np.mgrid[0:h, 0:w]
    dk = np.hypot(xx + 0.5 - kx, yy + 0.5 - ky) / max(k, 0.5)
    it = it + np.where((dk < 3.2) & (u_th > 0.2), 0.14, 0) - np.where((dk < 3.0) & (u_th < -0.3), 0.18, 0)
    # skirt occlusion: two rows under whatever is in front (skirt / bag) are darker
    occl = np.zeros((h, w))
    for d, amt in ((1, 0.40), (2, 0.24), (3, 0.10)):
        sh = np.zeros_like(front_mask); sh[d:] = front_mask[:-d]
        occl = np.maximum(occl, np.where(sh, amt * (1 if big else 1.2), 0))
    it = it - occl
    th = [0.18, 0.38, 0.62, 0.88] if big else [0.22, 0.45, 0.72, 2.0]
    lvl_st = np.digitize(it, th)
    lv[stock_m] = lvl_st[stock_m]
    # boot shaft / cuff / foot: glossy leather, specular streak just front of centre
    ib = 0.58 + 0.40 * np.clip(u_sh, -1, 1)
    spec = (u_sh > -0.28) & (u_sh < 0.02) & (s_sh > 0.18) & (s_sh < 0.92)
    tb = [0.16, 0.36, 0.62, 0.88] if big else [0.22, 0.46, 0.80, 2.0]
    lvl_bt = np.digitize(ib, tb)
    if big:
        lvl_bt = np.where(spec, 4, lvl_bt)
    else:
        lvl_bt = np.where(spec, 3, lvl_bt)
    lv[boot_m] = lvl_bt[boot_m]
    lv = clusterise(lv, stock_m)
    lv = clusterise(lv, lab == BT)
    st_img = np.zeros((h, w, 4), np.uint8); bt_img = np.zeros((h, w, 4), np.uint8)
    for L in range(5):
        st_img[stock_m & (lv == L)] = (*st[min(L, len(st) - 1)], 255)
        bt_img[boot_m & (lv == L)] = (*bt[min(L, len(bt) - 1)], 255)
    # cuff strap: darker band, light top edge, gold buckle (frame + dark tongue) on the visible side
    cuff = lab == CUFF
    bt_img[cuff] = (*bt[1], 255)
    top_edge = cuff & ~np.vstack([np.zeros((1, w), bool), cuff[:-1]])
    bt_img[top_edge & (u_sh > -0.2)] = (*bt[3], 255)
    ys, xs = np.where(cuff)
    buckle = []
    if len(xs):
        uu = u_sh[ys, xs]
        order = np.argsort(-uu)
        if big:
            cand = [(ys[i], xs[i]) for i in order if 0.15 < uu[i] < 0.95][:4]
        else:
            cand = [(ys[i], xs[i]) for i in order[:1]]
        for j, (y, x) in enumerate(cand):
            bt_img[y, x] = (*(gd[3] if j == 0 else gd[2]), 255); buckle.append((int(x), int(y)))
        if big and len(cand) >= 3:
            y, x = cand[1]; bt_img[y, x] = (*gd[1], 255)  # tongue shadow inside the frame
    # foot: top plane lighter, toe cap highlight cluster + 1px specular, sole welt + dark tread, heel
    foot = lab == FOOT
    topf = foot & ~np.vstack([np.zeros((1, w), bool), foot[:-1] | (lab[:-1] == BT)])
    bt_img[foot] = (*bt[2], 255)
    bt_img[foot & (np.vstack([foot[1:], np.zeros((1, w), bool)]) == False)] = (*bt[1], 255)
    bt_img[topf] = (*bt[3], 255)
    toe = lab == TOE
    bt_img[toe] = (*bt[4], 255)
    if big and toe.any():
        ty, tx = np.where(toe); i = int(np.argmin(ty * 10 - tx))
        bt_img[ty[i], tx[i]] = (*bt[5], 255)
    sole = lab == SOLE
    bt_img[sole] = (*bt[0], 255)
    welt = sole & ~np.vstack([np.zeros((1, w), bool), sole[:-1]])
    if big: bt_img[welt] = (*bt[2], 255)
    heel = lab == HEEL
    bt_img[heel] = (*bt[1], 255)
    # laces: X-lacing on the front band of the shaft, eyelets dark, period 3 rows (96) / dotted (48)
    shaft = lab == BT
    band = shaft & (u_sh > 0.12) & (u_sh < 0.80) & (s_sh > 0.22) & (s_sh < 0.90)
    if big:
        L = math.hypot(leg['ankle'][0] - leg['knee'][0], leg['ankle'][1] - leg['knee'][1])
        row = np.floor(s_sh * L).astype(int) % 3
        col = np.clip(np.floor((u_sh - 0.12) / 0.227), 0, 2).astype(int)
        steep = abs(math.degrees(math.atan2(leg['ankle'][0] - leg['knee'][0], leg['ankle'][1] - leg['knee'][1]))) > 35
        if not steep:   # full X-lacing; on a steeply swung shaft only the centre crossings stay (avoids diagonal noise)
            bt_img[band & (row == 0) & (col == 0)] = (*gd[2], 255)
            bt_img[band & (row == 0) & (col == 2)] = (*gd[1], 255)
        bt_img[band & (row == 1) & (col == 1)] = (*gd[3], 255)
        bt_img[band & (row == 2) & (col == 1)] = (*bt[1], 255)
    else:
        L = math.hypot(leg['ankle'][0] - leg['knee'][0], leg['ankle'][1] - leg['knee'][1])
        row = np.floor(s_sh * L).astype(int) % 2
        bt_img[band & (u_sh < 0.60) & (row == 0)] = (*gd[2], 255)
    # ankle strap with small buckle (96 only)
    if big:
        ax, ay = leg['ankle']
        strap = shaft & (np.abs(s_sh - 0.93) < 0.045)
        bt_img[strap] = (*bt[1], 255)
        sy, sx = np.where(strap)
        if len(sx):
            i = int(np.argmax(u_sh[sy, sx])); bt_img[sy[i], max(0, sx[i] - 1)] = (*gd[3], 255)
    # flex crease at the ankle for heel-strike / toe-off poses
    if abs(leg['pitch']) >= 14 and big:
        ax, ay = leg['ankle']
        crease = shaft & (np.abs(yy + 0.5 - (ay - 1.2)) < 0.6) & (u_sh > 0.1)
        bt_img[crease & (bt_img[:, :, 3] > 0)] = (*bt[0], 255)
    # sel-out: outer outline coloured by the local material's darkest tone on the lit side,
    # near-black on the shadow side; boot cuff top separates stocking from boot.
    allm = lab != 0
    edge = np.zeros_like(allm)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb = np.zeros_like(allm)
        ys0, ys1 = max(0, dy), h + min(0, dy)
        xs0, xs1 = max(0, dx), w + min(0, dx)
        nb[ys0:ys1, xs0:xs1] = allm[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
        edge |= allm & ~nb
    lit_th, lit_sh = u_th > 0.2, u_sh > 0.2
    st_img[edge & stock_m & lit_th] = (*st[0], 255)
    st_img[edge & stock_m & ~lit_th] = (*OUTLINE, 255)
    keep_gold = (bt_img[:, :, 0] > 180)
    bt_img[edge & boot_m & lit_sh & ~sole & ~keep_gold] = (*bt[0], 255)
    bt_img[edge & boot_m & ~lit_sh & ~keep_gold] = (*OUTLINE, 255)
    bt_img[edge & sole] = (*OUTLINE, 255)
    # stocking pixel right above the cuff = boot rim shadow
    above_cuff = stock_m & np.vstack([cuff[1:], np.zeros((1, w), bool)])
    st_img[above_cuff & ~edge] = (*st[0], 255)
    return st_img, bt_img, {'buckle': buckle}


def separate_near_far(near_rgba, far_rgba, pal, k):
    """near-leg pixels that border a far-leg pixel get a dark contour so the legs read apart."""
    nm = near_rgba[:, :, 3] > 0; fm = far_rgba[:, :, 3] > 0
    h, w = nm.shape
    edge = np.zeros_like(nm)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb = np.zeros_like(fm)
        ys0, ys1 = max(0, dy), h + min(0, dy)
        xs0, xs1 = max(0, dx), w + min(0, dx)
        nb[ys0:ys1, xs0:xs1] = (fm & ~nm)[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
        edge |= nm & nb
    out = near_rgba.copy()
    gold = out[:, :, 0] > 180
    out[edge & ~gold] = (*OUTLINE, 255)
    return out


# ---------------------------------------------------------------- per-frame patches
# (x, y, rgb or None=transparent, reason) in 96x128 coords and (x, y, ...) for 48x64.
# Every entry was placed after inspecting the rendered frame; see FRAME_LOG in README.
FRAME_ART_PATCHES = {0: [], 1: [], 2: [], 3: [], 4: [], 5: []}
FRAME_ART_PATCHES_48 = {0: [], 1: [], 2: [], 3: [], 4: [], 5: []}


def apply_patches(img, patches):
    for x, y, rgb, _why in patches:
        img[y, x] = (0, 0, 0, 0) if rgb is None else (*rgb, 255)
    return img


def over(dst, src):
    m = src[:, :, 3] > 0
    dst[m] = src[m]
    return dst


def front_mask_of(*layers):
    m = np.zeros(layers[0].shape[:2], bool)
    for l in layers: m |= l[:, :, 3] > 0
    return m


def compose(f, L, pal, k):
    """L: dict of fixed layers at this scale (already bob-shifted). returns rgba + layer dict."""
    bob = BOB[f]
    near = B.solve_leg(B.NEAR_HIP_X, B.HIP_Y + bob, f)
    far = B.solve_leg(B.FAR_HIP_X, B.HIP_Y + bob, (f + 3) % 6)
    skl = draw_skirt_left(pal, SKIRT_SWAY[f], bob, k)
    fm = front_mask_of(skl, L['skirt'], L['torso'], L['accessories'])
    lf, gf = B.rasterise_leg(far, k); ln, gn = B.rasterise_leg(near, k)
    fs, fb, _ = shade_leg67(lf, gf, pal, True, fm)
    ns, nb, info = shade_leg67(ln, gn, pal, False, fm)
    far_all = over(fs.copy(), fb)
    near_all = separate_near_far(over(ns.copy(), nb), far_all, pal, k)
    ns2 = np.where((near_all[:, :, 3:4] > 0) & (ns[:, :, 3:4] > 0), near_all, ns)
    nb2 = np.where((near_all[:, :, 3:4] > 0) & (nb[:, :, 3:4] > 0), near_all, nb)
    layers = {'cape_back': L['cape_back'], 'far_leg': fs, 'far_boot': fb, 'near_leg': ns2, 'near_boot': nb2,
              'skirt_left': skl, 'skirt': L['skirt'], 'torso': L['torso'], 'accessories': L['accessories']}
    img = np.zeros_like(L['skirt'])
    for name in ('cape_back', 'far_leg', 'far_boot', 'near_leg', 'near_boot', 'skirt_left', 'skirt', 'torso', 'accessories'):
        over(img, layers[name])
    apply_patches(img, (FRAME_ART_PATCHES if k >= 1 else FRAME_ART_PATCHES_48)[f])
    img[img[:, :, 3] == 0, :3] = 0
    return img, layers, dict(near=near, far=far)


def build(source: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    ref, halo = B.load_reference(source / 'morwen_right_walk_00_96x128.png')
    uf, ub, dropped = B.split_layers(ref)
    m = split67(uf)
    pal, snaps = build_palette(uf)
    fixed = {'skirt': masked(uf, m['skirt']), 'torso': masked(uf, m['torso']), 'accessories': masked(uf, m['accessories'])}
    frames, smalls, logs = [], [], []
    for f in range(6):
        bob = BOB[f]
        L96 = {k: B.shift(v, 0, bob) for k, v in fixed.items()}
        L96['cape_back'] = B.shift(B.shear_cape(ub, CAPE_SWAY[f]), 0, bob)
        img, layers, legs = compose(f, L96, pal, 1.0)
        L48 = {k: v[1::2, 1::2].copy() for k, v in L96.items()}   # NEAREST, identical rule to 65B/66
        sm, _, _ = compose(f, L48, pal, 0.5)
        frames.append(img); smalls.append(sm)
        logs.append({'frame': f, 'bob': bob, 'skirt_sway': SKIRT_SWAY[f], 'cape_sway': CAPE_SWAY[f],
                     'near_phase': GAIT[f]['role'], 'far_phase': GAIT[(f + 3) % 6]['role'],
                     'near': {k: [round(v, 2) for v in legs['near'][k]] for k in ('hip', 'knee', 'ankle')},
                     'far': {k: [round(v, 2) for v in legs['far'][k]] for k in ('hip', 'knee', 'ankle')},
                     'patches_96': FRAME_ART_PATCHES[f], 'patches_48': FRAME_ART_PATCHES_48[f]})
        name = f'morwen_right_walk_{f:02d}'
        Image.fromarray(img, 'RGBA').save(out / f'{name}_96x128.png')
        Image.fromarray(sm, 'RGBA').save(out / f'{name}_48x64.png')
    meta = {'palette': pal, 'palette_snapped_to_upper_body': snaps, 'skirt_sway': SKIRT_SWAY,
            'mask_pixels': {k: int(v.sum()) for k, v in m.items()}, 'halo_removed': halo,
            'old_lower_body_discarded': dropped, 'frames': logs}
    (out / 'build_meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')
    return frames, smalls, fixed, ub, m, meta


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--source', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(); build(a.source, a.out); print('ok')

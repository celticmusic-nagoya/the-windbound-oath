#!/usr/bin/env python3
"""MORWEN-PIXEL-68: lower-body proportion/costume structure + costume secondary motion.

Base: MORWEN-PIXEL-67 (gait from build_morwen66, shading rules from build_morwen67).
New in 68
  * thigh-high stocking structure from the official master: skirt hem -> short skin band ->
    stocking welt -> stocking, with the garter strap and gold clip on the visible thigh.
    The welt sits at a fixed distance along the thigh (S_TOP) so the costume is identical
    in every frame; the skirt occludes whatever lies above it.
  * tapered thigh (hip 4.5 -> knee 3.8), calf curve inside the boot shaft, stance/swing light.
  * secondary motion (deterministic, period 3 frames = one step, lag in frames):
      collar_ribbon, cape_front (shoulder capelet back tip), mantle (outer cape + hem), potions.
    Cloth is warped by backward nearest-pixel mapping with an anchor and a weight that grows
    away from the anchor (no scaling, no interpolation). Gaps are filled from the part's own
    original pixels (stretch); edges against transparency move. Immutable details are re-applied.
Z order (back -> front):
  cape_back, far_leg, far_boot, near_leg, near_boot, skirt_left, skirt, torso, mantle_front,
  cape_front, collar_ribbon, accessories(potions moved / bag+hand fixed), immutable_details,
  per_frame_detail_patch
Requires numpy + Pillow.
"""
from pathlib import Path
import json, math, argparse
import numpy as np
from PIL import Image, ImageDraw
import build_morwen66 as B
import build_morwen67 as C

W, H = B.W, B.H
BOB = B.BOB                                 # primary: [0,1,0,0,1,0]
ST, BT, CUFF, FOOT, SOLE, HEEL, TOE = B.ST, B.BT, B.CUFF, B.FOOT, B.SOLE, B.HEEL, B.TOE
SKIN, WELT = 8, 9
S_TOP = 5.4          # stocking top: distance along the thigh from the hip joint (96 px)
WELT_W = 1.4
R_HIP, R_KNEE = 4.5, 3.8

# ---------------------------------------------------------------- secondary motion
# Offsets are relative to the body (the body itself already bobs). All signals have
# period 3 (one step), so F05 -> F00 is the same transition as F02 -> F03.
# 'lag' documents the design: the cloth reacts one (light) or two (heavy) frames after the bob.
SECONDARY_MOTION = {
    'collar_ribbon': dict(max_offset_px=1, phase_lag=1, dy=[0, 0, 1, 0, 0, 1], dx=[0, 0, -1, 0, 0, -1]),
    'cape_front':    dict(max_offset_px=1, phase_lag=1, dy=[0, 0, 1, 0, 0, 1], dx=[0, 0, 0, 0, 0, 0]),
    'mantle':        dict(max_offset_px=2, phase_lag=2, dy=[0, 0, 1, 0, 0, 1], dx=[-1, -1, -2, -1, -1, -2]),
    'potions':       dict(max_offset_px=1, phase_lag=1, dy=[0, 0, 1, 0, 0, 1], dx=[0, 0, 0, 0, 0, 0]),
}
SKIRT_SWAY = C.SKIRT_SWAY       # left hem, lag 1 (67)

DESIGN_SKIN = [(150, 74, 70), (212, 143, 119), (236, 175, 146), (253, 225, 195)]


# ---------------------------------------------------------------- masks on the 65B F00 reference
def region_masks(uf, ub):
    op = uf[:, :, 3] > 0
    r, g, b = (uf[:, :, i].astype(int) for i in range(3))
    yy, xx = np.mgrid[0:H, 0:W]
    base = C.split67(uf)
    head = op & (yy < 50)                                             # hat, face, hair, earrings
    hat_ribbon = op & (xx <= 40) & (yy >= 50) & (yy <= 58)             # ribbons hanging from the hat
    emblem = op & (xx >= 41) & (xx <= 53) & (yy >= 50) & (yy <= 59)    # open-book crest on the capelet
    immutable = head | hat_ribbon | emblem
    collar = op & ~immutable & (xx >= 57) & (xx <= 66) & (yy >= 51) & (yy <= 58)
    cape_front = op & ~immutable & (xx >= 33) & (xx <= 41) & (yy >= 57) & (yy <= 66)
    mantle = op & ~immutable & (xx <= 41) & (yy >= 64) & ~base['accessories']
    potions = op & (xx >= 54) & (xx <= 63) & (yy >= 70) & (yy <= 79) & (
        ((r > 200) & (b > 170)) | ((r > 200) & (g > 110) & (b < 90)) | ((r > 225) & (g > 215) & (b > 215)))
    fixed_acc = base['accessories'] & ~potions
    torso = base['torso'] & ~immutable & ~collar & ~cape_front & ~mantle & ~potions
    skirt = base['skirt'] & ~potions
    return dict(immutable_details=immutable, collar_ribbon=collar, cape_front=cape_front, mantle=mantle,
                potions=potions, accessories_fixed=fixed_acc, torso=torso, skirt=skirt, redraw=base['redraw'])


ANCHORS = {   # (anchor x, anchor y, reach px) in 96 coords
    'collar_ribbon': (62, 51, 7.0),
    'cape_front': (42, 57, 9.0),
    'mantle': (41, 64, 40.0),
}


def weight(name, k=1.0):
    ax, ay, reach = ANCHORS[name]
    yy, xx = np.mgrid[0:int(H * k), 0:int(W * k)]
    d = np.hypot((xx + 0.5) / k - ax, (yy + 0.5) / k - ay)
    return np.clip(d / reach, 0, 1)


def warp(src, mask, wgt, dx, dy, full_alpha):
    """backward nearest mapping inside the part; stretch fill; edges against transparency move."""
    h, w = mask.shape
    out = np.zeros_like(src)
    out[mask] = src[mask]
    if dx == 0 and dy == 0:
        return out, mask.copy()
    ddx = np.rint(dx * wgt).astype(int); ddy = np.rint(dy * wgt).astype(int)
    pad = 2 + max(abs(dx), abs(dy))
    ys, xs = np.where(mask)
    y0, y1 = max(0, ys.min() - pad), min(h, ys.max() + pad + 1)
    x0, x1 = max(0, xs.min() - pad), min(w, xs.max() + pad + 1)
    newmask = np.zeros_like(mask)
    out[:] = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            sx, sy = x - ddx[y, x], y - ddy[y, x]
            if 0 <= sx < w and 0 <= sy < h and mask[sy, sx]:
                out[y, x] = src[sy, sx]; newmask[y, x] = True
            elif mask[y, x]:
                if 0 <= sx < w and 0 <= sy < h and not full_alpha[sy, sx]:
                    continue                      # the part moved away from open space: edge moves
                out[y, x] = src[y, x]; newmask[y, x] = True   # stretch with the part's own pixel
    return out, newmask


def rigid(src, mask, dx, dy):
    """rigid move of an accessory; the gap at its attachment edge is filled by repeating its own edge row."""
    out = np.zeros_like(src); m2 = np.zeros_like(mask)
    ys, xs = np.where(mask)
    ny, nx = ys + dy, xs + dx
    ok = (ny >= 0) & (ny < src.shape[0]) & (nx >= 0) & (nx < src.shape[1])
    out[ny[ok], nx[ok]] = src[ys[ok], xs[ok]]; m2[ny[ok], nx[ok]] = True
    if dy > 0:   # attachment at the top: keep the original top pixels (cap / loop) so it stays hung
        top = mask & ~np.vstack([np.zeros((1, mask.shape[1]), bool), mask[:-1]])
        out[top & ~m2] = src[top & ~m2]; m2 |= top
    return out, m2


# ---------------------------------------------------------------- legs
def rasterise68(leg, k=1.0):
    w, h = int(W * k), int(H * k)
    L = B.scaled(leg, k)
    SS = B.SS
    big = Image.new('L', (w * SS, h * SS), 0)
    d = ImageDraw.Draw(big)
    hip, knee, ankle, pitch = L['hip'], L['knee'], L['ankle'], L['pitch']
    # tapered thigh
    d.ellipse([(hip[0] - R_HIP * k) * SS, (hip[1] - R_HIP * k) * SS, (hip[0] + R_HIP * k) * SS, (hip[1] + R_HIP * k) * SS], fill=ST)
    B.quad(d, hip, knee, R_HIP * k, R_KNEE * k, ST)
    d.ellipse([(knee[0] - R_KNEE * k) * SS, (knee[1] - R_KNEE * k) * SS, (knee[0] + R_KNEE * k) * SS, (knee[1] + R_KNEE * k) * SS], fill=ST)
    # boot shaft with a calf curve on the back side
    kx, ky = knee; ax, ay = ankle
    vx, vy = ax - kx, ay - ky; n = math.hypot(vx, vy); ux, uy = vx / n, vy / n
    nx, ny = uy, -ux
    if nx < 0: nx, ny = -nx, -ny                     # + = front
    top = (kx - ux * 1.5 * k, ky - uy * 1.5 * k)
    L2 = math.hypot(ax - top[0], ay - top[1])
    prof_back = [5.0, 5.4, 5.2, 4.7, 4.3]            # calf bulge then ankle
    prof_front = [4.9, 4.6, 4.4, 4.3, 4.2]
    front, back = [], []
    for i, t in enumerate(np.linspace(0, 1, 5)):
        px, py = top[0] + ux * L2 * t, top[1] + uy * L2 * t
        front.append((px + nx * prof_front[i] * k, py + ny * prof_front[i] * k))
        back.append((px - nx * prof_back[i] * k, py - ny * prof_back[i] * k))
    d.polygon([(x * SS, y * SS) for x, y in front + back[::-1]], fill=BT)
    cuff_end = (top[0] + ux * 2.4 * k, top[1] + uy * 2.4 * k)
    B.quad(d, (top[0] - ux * 0.6 * k, top[1] - uy * 0.6 * k), cuff_end, 5.4 * k, 5.3 * k, CUFF)
    d.polygon([(x * SS, y * SS) for x, y in B.foot_points(B.FOOT_POLY, ankle, pitch, k)], fill=FOOT)
    if k >= 1:
        d.polygon([(x * SS, y * SS) for x, y in B.foot_points(B.TOE_POLY, ankle, pitch, k)], fill=TOE)
    d.polygon([(x * SS, y * SS) for x, y in B.foot_points(B.SOLE_POLY, ankle, pitch, k)], fill=SOLE)
    d.polygon([(x * SS, y * SS) for x, y in B.foot_points(B.HEEL_POLY, ankle, pitch, k)], fill=HEEL)
    arr = np.array(big).reshape(h, SS, w, SS).transpose(0, 2, 1, 3).reshape(h, w, SS * SS)
    lab = np.zeros((h, w), np.uint8); best = np.zeros((h, w), int)
    for Lb in range(1, 8):
        cnt = (arr == Lb).sum(2)
        lab = np.where(cnt > best, Lb, lab); best = np.maximum(best, cnt)
    lab[(arr != 0).sum(2) < SS * SS // 2] = 0
    # costume structure along the thigh: skin band above the stocking welt
    yy, xx = np.mgrid[0:h, 0:w]
    tx, ty = knee[0] - hip[0], knee[1] - hip[1]; tn = math.hypot(tx, ty)
    s_dist = ((xx + 0.5 - hip[0]) * tx + (yy + 0.5 - hip[1]) * ty) / tn / k   # in 96-px units
    stock = lab == ST
    lab[stock & (s_dist < S_TOP)] = SKIN
    lab[stock & (s_dist >= S_TOP) & (s_dist < S_TOP + WELT_W)] = WELT
    geo = dict(top=top, cuff_end=cuff_end, axis=(ux, uy), leg=L, k=k, s_dist=s_dist)
    return lab, geo


def shade68(lab, geo, pal, far, front_mask, swing):
    k = geo['k']; L = geo['leg']; big = k >= 1
    h, w = lab.shape
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = xx + 0.5, yy + 0.5
    hip, knee, ankle = L['hip'], L['knee'], L['ankle']

    def frame(p, q):
        vx, vy = q[0] - p[0], q[1] - p[1]; n = math.hypot(vx, vy)
        ax_, ay_ = vx / n, vy / n
        nx, ny = ay_, -ax_
        if nx < 0: nx, ny = -nx, -ny
        return (cx - p[0]) * nx + (cy - p[1]) * ny, ((cx - p[0]) * ax_ + (cy - p[1]) * ay_) / n
    u_th, s_th = frame(hip, knee); u_sh, s_sh = frame(knee, ankle)
    r_th = (R_HIP + (R_KNEE - R_HIP) * np.clip(s_th, 0, 1)) * k
    un_th = np.clip(u_th / r_th, -1, 1)
    un_sh = np.clip(u_sh / (4.8 * k), -1, 1)
    st = pal['stock_far' if far else 'stock']; bt = pal['boot_far' if far else 'boot']
    gd = pal['gold_far' if far else 'gold']; sk = pal['skin_far' if far else 'skin']
    swing_d = 0.07 if swing else 0.0           # a swinging leg is under the body: a touch darker
    light_shift = -0.10 if swing else 0.0      # and its light turns toward the top (thigh lifts)
    occl = np.zeros((h, w))
    for dd, amt in ((1, 0.42), (2, 0.24), (3, 0.10)):
        sh = np.zeros_like(front_mask); sh[dd:] = front_mask[:-dd]
        occl = np.maximum(occl, np.where(sh, amt, 0))
    kx, ky = knee
    dk = np.hypot(cx - kx, cy - ky) / max(k, 0.5)
    # stocking: matte fabric, soft broad highlight cluster (no specular)
    it = 0.60 + 0.38 * (un_th + light_shift) - occl - swing_d
    it += np.where((dk < 3.4) & (un_th > 0.15), 0.12, 0) - np.where((dk < 3.0) & (un_th < -0.35), 0.16, 0)
    lv_st = np.digitize(it, [0.18, 0.38, 0.62, 0.90] if big else [0.22, 0.45, 0.74, 2.0])
    # skin band: same light, its own ramp (4)
    lv_sk = np.digitize(it + 0.18, [0.30, 0.55, 0.80] if big else [0.35, 0.65, 2.0])
    if not big:
        lv_sk = np.maximum(lv_sk, 2)   # 48px: keep the skin band readable as a separator (no deep occlusion tone)
    # boot leather: glossy, specular streak on the face turned to the light
    ib = 0.58 + 0.40 * un_sh - swing_d
    lv_bt = np.digitize(ib, [0.16, 0.36, 0.62, 0.88] if big else [0.22, 0.46, 0.80, 2.0])
    spec = (un_sh > -0.28) & (un_sh < 0.02) & (s_sh > 0.18) & (s_sh < 0.92)
    lv_bt = np.where(spec, 4 if big else 3, lv_bt)
    lv = np.full((h, w), -1, int)
    stock_m = lab == ST; skin_m = lab == SKIN; welt_m = lab == WELT
    boot_m = np.isin(lab, (BT, CUFF, FOOT, SOLE, HEEL, TOE))
    lv[stock_m] = lv_st[stock_m]; lv[boot_m] = lv_bt[boot_m]
    lv = C.clusterise(lv, stock_m); lv = C.clusterise(lv, lab == BT)
    S = np.zeros((h, w, 4), np.uint8); Bo = np.zeros((h, w, 4), np.uint8)
    for i in range(5):
        S[stock_m & (lv == i)] = (*st[min(i, 4)], 255)
        Bo[boot_m & (lv == i)] = (*bt[min(i, 5)], 255)
    for i in range(4):
        S[skin_m & (lv_sk == i)] = (*sk[i], 255)
    # welt: denser knit band - one tone darker than the stocking below it, lighter top edge on the lit side
    S[welt_m] = (*st[1], 255)
    welt_top = welt_m & np.vstack([np.zeros((1, w), bool), skin_m[:-1]])
    S[welt_top & (un_th > 0.0)] = (*st[2], 255)
    garter = []
    if not far:   # garter strap (dark) over the skin band with a gold clip on the welt, visible thigh side
        band = skin_m & (np.abs(un_th - 0.25) < (0.17 if big else 0.26))
        S[band] = (*st[0], 255)
        clip_px = welt_m & (np.abs(un_th - 0.25) < (0.22 if big else 0.30))
        ys, xs = np.where(clip_px)
        if len(xs):
            i = int(np.argmin(ys)); S[ys[i], xs[i]] = (*gd[3], 255); garter.append((int(xs[i]), int(ys[i])))
            if big and len(xs) > 1:
                j = int(np.argsort(ys)[1]); S[ys[j], xs[j]] = (*gd[2], 255); garter.append((int(xs[j]), int(ys[j])))
    # ---- boot details (67 rules) ----
    cuff = lab == CUFF
    Bo[cuff] = (*bt[1], 255)
    top_edge = cuff & ~np.vstack([np.zeros((1, w), bool), cuff[:-1]])
    Bo[top_edge & (un_sh > -0.2)] = (*bt[3], 255)
    ys, xs = np.where(cuff)
    if len(xs):
        uu = un_sh[ys, xs]; order = np.argsort(-uu)
        cand = [(ys[i], xs[i]) for i in order if 0.15 < uu[i] < 0.95][:4] if big else [(ys[order[0]], xs[order[0]])]
        for j, (y, x) in enumerate(cand):
            Bo[y, x] = (*(gd[3] if j == 0 else gd[2]), 255)
        if big and len(cand) >= 3:
            y, x = cand[1]; Bo[y, x] = (*gd[1], 255)
    foot = lab == FOOT
    Bo[foot] = (*bt[2], 255)
    Bo[foot & ~np.vstack([foot[1:], np.zeros((1, w), bool)])] = (*bt[1], 255)
    Bo[foot & ~np.vstack([np.zeros((1, w), bool), (foot | (lab == BT))[:-1]])] = (*bt[3], 255)
    toe = lab == TOE
    Bo[toe] = (*bt[4], 255)
    if big and toe.any():
        ty, tx = np.where(toe); i = int(np.argmin(ty * 10 - tx)); Bo[ty[i], tx[i]] = (*bt[5], 255)
    sole = lab == SOLE
    Bo[sole] = (*bt[0], 255)
    if big: Bo[sole & ~np.vstack([np.zeros((1, w), bool), sole[:-1]])] = (*bt[2], 255)
    Bo[lab == HEEL] = (*bt[1], 255)
    shaft = lab == BT
    band = shaft & (un_sh > 0.12) & (un_sh < 0.80) & (s_sh > 0.22) & (s_sh < 0.90)
    Ls = math.hypot(ankle[0] - knee[0], ankle[1] - knee[1])
    if big:
        row = np.floor(s_sh * Ls).astype(int) % 3
        col = np.clip(np.floor((un_sh - 0.12) / 0.227), 0, 2).astype(int)
        steep = abs(math.degrees(math.atan2(ankle[0] - knee[0], ankle[1] - knee[1]))) > 35
        if not steep:
            Bo[band & (row == 0) & (col == 0)] = (*gd[2], 255)
            Bo[band & (row == 0) & (col == 2)] = (*gd[1], 255)
        Bo[band & (row == 1) & (col == 1)] = (*gd[3], 255)
        Bo[band & (row == 2) & (col == 1)] = (*bt[1], 255)
        strap = shaft & (np.abs(s_sh - 0.93) < 0.045)
        Bo[strap] = (*bt[1], 255)
        sy, sx = np.where(strap)
        if len(sx):
            i = int(np.argmax(un_sh[sy, sx])); Bo[sy[i], max(0, sx[i] - 1)] = (*gd[3], 255)
        if abs(L['pitch']) >= 14:
            crease = shaft & (np.abs(cy - (ankle[1] - 1.2)) < 0.6) & (un_sh > 0.1)
            Bo[crease] = (*bt[0], 255)
    else:
        row = np.floor(s_sh * Ls).astype(int) % 2
        Bo[band & (un_sh < 0.60) & (row == 0)] = (*gd[2], 255)
    # ---- sel-out ----
    allm = lab != 0
    edge = np.zeros_like(allm)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb = np.zeros_like(allm)
        ys0, ys1 = max(0, dy), h + min(0, dy); xs0, xs1 = max(0, dx), w + min(0, dx)
        nb[ys0:ys1, xs0:xs1] = allm[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
        edge |= allm & ~nb
    upper = stock_m | skin_m | welt_m
    lit = un_th > 0.2
    S[edge & stock_m & lit] = (*st[0], 255); S[edge & welt_m] = (*st[0], 255)
    S[edge & skin_m & lit] = (*sk[0], 255)
    S[edge & upper & ~lit] = (*C.OUTLINE, 255)
    keep_gold = Bo[:, :, 0] > 180
    lit_s = un_sh > 0.2
    Bo[edge & boot_m & lit_s & ~sole & ~keep_gold] = (*bt[0], 255)
    Bo[edge & boot_m & ~lit_s & ~keep_gold] = (*C.OUTLINE, 255)
    Bo[edge & sole] = (*C.OUTLINE, 255)
    above_cuff = stock_m & np.vstack([cuff[1:], np.zeros((1, w), bool)])
    S[above_cuff & ~edge] = (*st[0], 255)
    return S, Bo, {'garter': garter}


def build_palette68(ref_front):
    pal, snaps = C.build_palette(ref_front)
    cols = np.unique(ref_front[ref_front[:, :, 3] > 0][:, :3], axis=0).astype(int)
    for key, ramp in (('skin', DESIGN_SKIN), ('skin_far', [tuple(int(v * 0.78) for v in c) for c in DESIGN_SKIN])):
        out, sn = [], []
        for c in ramp:
            dd = np.sqrt(((cols - np.array(c)) ** 2 * np.array([0.30, 0.59, 0.11]) * 3).sum(1)); i = int(dd.argmin())
            out.append(tuple(int(v) for v in cols[i]) if dd[i] <= 14 else c); sn.append(bool(dd[i] <= 14))
        pal[key] = out; snaps[key] = sn
    return pal, snaps


# ---------------------------------------------------------------- per-frame patches
# entries: (x, y, before_rgba, after_rgba_or_None, reason). Applied last; 'before' is verified.
FRAME_ART_PATCHES = {0: [], 1: [], 2: [], 3: [], 4: [], 5: []}
FRAME_ART_PATCHES_48 = {0: [], 1: [], 2: [], 3: [], 4: [], 5: []}


def apply_patches(img, patches):
    for x, y, before, after, why in patches:
        if tuple(int(v) for v in img[y, x]) != tuple(before):
            raise ValueError(f'patch precondition failed at {(x, y)}: {tuple(img[y, x])} != {before} ({why})')
        img[y, x] = (0, 0, 0, 0) if after is None else after
    return img


def upper_layers(f, ref_front, ub, masks):
    """96-px fixed + secondary-motion layers for frame f (before the bob shift)."""
    full_alpha = (ref_front[:, :, 3] > 0) | (ub[:, :, 3] > 0)
    L, foot = {}, {}
    for name in ('skirt', 'torso', 'accessories_fixed', 'immutable_details'):
        L[name] = C.masked(ref_front, masks[name])
    sm = SECONDARY_MOTION
    for name in ('collar_ribbon', 'cape_front'):
        L[name], foot[name] = warp(ref_front, masks[name], weight(name), sm[name]['dx'][f], sm[name]['dy'][f], full_alpha)
    # mantle: front part (in U_front) and the lower tail behind the legs share one field
    mant_src = ref_front.copy(); C.over(mant_src, ub)
    mmask = masks['mantle'] | (ub[:, :, 3] > 0)
    mw, mfoot = warp(mant_src, mmask, weight('mantle'), sm['mantle']['dx'][f], sm['mantle']['dy'][f], full_alpha)
    back_rows = np.zeros_like(mfoot)
    # pixels that came from the lower tail stay behind the legs (z), the rest in front
    yy, xx = np.mgrid[0:H, 0:W]
    back_rows = mfoot & (yy >= 91) & ~(np.isin(np.arange(H)[:, None], []) )
    tail_src = ub[:, :, 3] > 0
    from_tail = np.zeros_like(mfoot)
    ddx = np.rint(sm['mantle']['dx'][f] * weight('mantle')).astype(int)
    ddy = np.rint(sm['mantle']['dy'][f] * weight('mantle')).astype(int)
    ys, xs = np.where(mfoot)
    sy = np.clip(ys - ddy[ys, xs], 0, H - 1); sx = np.clip(xs - ddx[ys, xs], 0, W - 1)
    from_tail[ys, xs] = tail_src[sy, sx] & ~masks['mantle'][sy, sx]
    L['cape_back'] = C.masked(mw, from_tail)
    L['mantle_front'] = C.masked(mw, mfoot & ~from_tail)
    foot['mantle'] = mfoot
    L['potions'], foot['potions'] = rigid(ref_front, masks['potions'], sm['potions']['dx'][f], sm['potions']['dy'][f])
    return L, foot


Z = ['cape_back', 'far_leg', 'far_boot', 'near_leg', 'near_boot', 'skirt_left', 'skirt', 'torso', 'mantle_front',
     'cape_front', 'collar_ribbon', 'potions', 'accessories_fixed', 'immutable_details']


def compose68(f, U, pal, k):
    bob = BOB[f]
    near = B.solve_leg(B.NEAR_HIP_X, B.HIP_Y + bob, f)
    far = B.solve_leg(B.FAR_HIP_X, B.HIP_Y + bob, (f + 3) % 6)
    skl = C.draw_skirt_left(pal, SKIRT_SWAY[f], bob, k)
    fm = C.front_mask_of(skl, U['skirt'], U['torso'], U['accessories_fixed'], U['potions'], U['mantle_front'])
    lf, gf = rasterise68(far, k); ln, gn = rasterise68(near, k)
    fs, fb, _ = shade68(lf, gf, pal, True, fm, B.GAIT[(f + 3) % 6]['lift'] > 0)
    ns, nb, info = shade68(ln, gn, pal, False, fm, B.GAIT[f]['lift'] > 0)
    far_all = C.over(fs.copy(), fb)
    near_all = C.separate_near_far(C.over(ns.copy(), nb), far_all, pal, k)
    ns2 = np.where((near_all[:, :, 3:4] > 0) & (ns[:, :, 3:4] > 0), near_all, ns)
    nb2 = np.where((near_all[:, :, 3:4] > 0) & (nb[:, :, 3:4] > 0), near_all, nb)
    layers = dict(U); layers.update(far_leg=fs, far_boot=fb, near_leg=ns2, near_boot=nb2, skirt_left=skl)
    img = np.zeros_like(U['skirt'])
    for name in Z:
        C.over(img, layers[name])
    apply_patches(img, (FRAME_ART_PATCHES if k >= 1 else FRAME_ART_PATCHES_48)[f])
    img[img[:, :, 3] == 0, :3] = 0
    return img, layers, dict(near=near, far=far, garter=info['garter'])


def build(source: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    ref, halo = B.load_reference(source / 'morwen_right_walk_00_96x128.png')
    uf, ub, dropped = B.split_layers(ref)
    masks = region_masks(uf, ub)
    pal, snaps = build_palette68(uf)
    frames, smalls, logs, U96s = [], [], [], []
    for f in range(6):
        bob = BOB[f]
        U, foot = upper_layers(f, uf, ub, masks)
        U96 = {k: B.shift(v, 0, bob) for k, v in U.items()}
        img, layers, legs = compose68(f, U96, pal, 1.0)
        U48 = {k: v[1::2, 1::2].copy() for k, v in U96.items()}
        sm, _, legs48 = compose68(f, U48, pal, 0.5)
        frames.append(img); smalls.append(sm); U96s.append((U96, {k: B.shift(v[..., None].repeat(4, 2).astype(np.uint8) * 255, 0, bob)[:, :, 3] > 0 for k, v in foot.items()}))
        logs.append({'frame': f, 'bob': bob, 'near_phase': B.GAIT[f]['role'], 'far_phase': B.GAIT[(f + 3) % 6]['role'],
                     'secondary': {n: {'dx': SECONDARY_MOTION[n]['dx'][f], 'dy': SECONDARY_MOTION[n]['dy'][f]} for n in SECONDARY_MOTION},
                     'skirt_sway': SKIRT_SWAY[f], 'garter_px_96': legs['garter'], 'garter_px_48': legs48['garter'],
                     'near': {kk: [round(v, 2) for v in legs['near'][kk]] for kk in ('hip', 'knee', 'ankle')},
                     'far': {kk: [round(v, 2) for v in legs['far'][kk]] for kk in ('hip', 'knee', 'ankle')},
                     'patches_96': FRAME_ART_PATCHES[f], 'patches_48': FRAME_ART_PATCHES_48[f]})
        name = f'morwen_right_walk_{f:02d}'
        Image.fromarray(img, 'RGBA').save(out / f'{name}_96x128.png')
        Image.fromarray(sm, 'RGBA').save(out / f'{name}_48x64.png')
    # protection masks (reference frame, before bob) as PNG for review
    mk = out / 'masks'; mk.mkdir(exist_ok=True)
    for name, m in masks.items():
        Image.fromarray((m * 255).astype(np.uint8), 'L').save(mk / f'{name}.png')
    meta = {'palette': pal, 'palette_snapped_to_upper_body': snaps, 'secondary_motion': SECONDARY_MOTION, 'anchors': ANCHORS,
            'stocking_structure': {'S_TOP_px_along_thigh': S_TOP, 'welt_px': WELT_W, 'r_hip': R_HIP, 'r_knee': R_KNEE},
            'mask_pixels': {k: int(v.sum()) for k, v in masks.items()}, 'z_order': Z, 'frames': logs}
    (out / 'build_meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')
    return frames, smalls, uf, ub, masks, U96s, meta


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--source', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(); build(a.source, a.out); print('ok')

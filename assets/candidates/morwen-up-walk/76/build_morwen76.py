#!/usr/bin/env python3
"""MORWEN-WALK-UP-76: up (back view) walk, 12 frames / 840 ms, NEW candidate from the official back profile.

Design: official back profile (assets/official/characters/morwen/turnaround/, SHA-256 9cf2f274...): hat back with the
gold laurel bands, flower + violet ribbon + hat-tip crystal on the hat's right side, short bob, capelet with the book
crest, layered cape with gold thorn embroidery, satchel on the right hip with the strap over the left shoulder, knee
socks and short boots with outer buckles. Head/hat and body are reduced from the painting at two scales so the sprite
has the side walks' chibi proportions (same hat width, neck row, cape hem and ground row) and quantised to ONE palette
taken from the left 74G + right 75 frames (no global filter).
Motion (side-view hip travel is NOT reused): same timing as the side walks (stance 0.66, F00 right heel strike,
840 ms), seen from behind:
  - legs alternate in depth: the planted foot moves from far (row 122) to near (row 124) through stance; the swinging
    foot lifts (max 3 px), shows its sole while trailing and returns to the far position
  - pelvis: lateral weight shift toward the stance leg (1 px) and a 1 px drop on the swing-leg side (tilt)
  - shoulders / capelet: opposite lateral shift, one frame later than the pelvis; head does not sway sideways
  - vertical levels: pelvis / chest / head bob of 74F-C (1 px, head lags)
  - cape hem and ribbon follow the pelvis 2 frames late; hands swing 1 px opposite to the legs
48x64: layers sampled unshifted on a fixed odd grid and moved by whole 48 px (74G stable sampling).
  python3 build_morwen76.py --official-back <png> --palette-from <74G dir> <75 dir> --out <dir>
"""
import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_D74 = _os.environ.get('MORWEN74D_DIR', _os.path.join(_HERE, '..', '..', 'morwen-left-walk', '74D'))
_sys.path[:0] = [_HERE, _D74]
import argparse, glob, json, math
from pathlib import Path
import numpy as np
from PIL import Image
import back_base76 as BB
from walkclean import clean_islands_generic
from oklab import rgb2oklab, oklab2rgb, lch

H, W, NF = 128, 96, 12
STANCE = 0.66
P_DY = [1, 1, 0, -1, -1, 0, 1, 1, 0, -1, -1, 0]      # 74F-C levels (shared rhythm)
C_DY = [0, 1, 1, 0, -1, -1, 0, 1, 1, 0, -1, -1]
H_DY = [0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0]
P_DX = [0, 0, 1, 1, 1, 0, 0, 0, -1, -1, -1, 0]      # weight over the right leg (viewer's right) F02-F04, left F08-F10
S_DX = [0, 0, 0, -1, -1, 0, 0, 0, 0, 1, 1, 0]       # shoulders opposite, 1 frame later
TILT = [0, 0, 1, 1, 1, 0, 0, 0, -1, -1, -1, 0]      # +1: viewer-left hip (left leg swinging) drops
HEM_LAG, SHOULDER_ROW, WAIST_ROW, HEM_ROW = 2, 63, 74, 88
LEG_X = {'R': 52, 'L': 44}                           # character right leg = viewer's right from behind
STK = dict(o=(12, 2, 12), d=(62, 32, 45), m=(85, 52, 65), l=(105, 71, 84), h=(129, 93, 107))
BOOT = dict(o=(12, 2, 12), d=(33, 12, 37), m=(51, 29, 54), l=(72, 49, 76), sole=(17, 1, 20), g=(226, 163, 85), gd=(167, 107, 42))


def leg_state(p):
    """p: phase of this leg, 0 = heel strike. foot_y = ground row of the foot, lift, sole visible."""
    p %= 1.0
    if p < STANCE:
        u = p / STANCE
        return dict(foot=122 + round(2 * u), lift=0, sole=u > 0.8, stance=True)
    u = (p - STANCE) / (1 - STANCE)
    return dict(foot=124 - round(2 * u), lift=round(3 * math.sin(math.pi * u)), sole=u < 0.5, stance=False)


def draw_leg(img, cx, st, top=94):
    """knee sock + short boot from behind, cx = leg centre column. The boot shaft is 8 px wide with the buckle on the
    outer side; the heel block is 2 rows; a lifted trailing foot shows its sole instead of the heel."""
    y_ground = st['foot'] - st['lift']
    boot_top = y_ground - 13
    outer = 1 if cx > 48 else -1
    for y in range(top, boot_top):                      # knee sock, 6 px
        for i, x in enumerate(range(cx - 3, cx + 3)):
            c = STK['o'] if i in (0, 5) else (STK['l'] if i == (3 if outer > 0 else 2) else STK['m'] if i in (2, 3) else STK['d'])
            img[y, x, :3] = c; img[y, x, 3] = 255
    for y in range(boot_top, y_ground + 1):
        heel = y > y_ground - 2
        x0, x1 = (cx - 3, cx + 3) if heel else (cx - 4, cx + 4)
        for x in range(x0, x1):
            edge = x in (x0, x1 - 1) or y == y_ground
            if edge: c = BOOT['o']
            elif heel: c = BOOT['sole'] if st['sole'] else BOOT['d']
            elif y == boot_top: c = BOOT['l']
            else:
                rel = (x - cx) * outer
                c = BOOT['l'] if rel == 1 else BOOT['m'] if rel in (0, 2) else BOOT['d']
            img[y, x, :3] = c; img[y, x, 3] = 255
        if st['sole'] and y == y_ground - 2:              # sole edge line when the heel is up
            for x in range(cx - 3, cx + 3): img[y, x, :3] = BOOT['sole']
    for dy in (2, 7):                                   # outer buckles (official back: two straps per boot)
        y = boot_top + dy; x = cx + outer * 3
        if y < y_ground - 2:
            img[y, x, :3] = BOOT['g']; img[y, x - outer, :3] = BOOT['gd']
            for xx in range(cx - 3, cx + 3):
                if xx not in (x, x - outer): img[y, xx, :3] = BOOT['d']


def outline(img, pal_lab, pal):
    """exterior edge pixels -> the darkest palette colour of their own hue family (side-walk outline look)."""
    a = img[:, :, 3] > 0
    nb = np.zeros_like(a)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb |= ~np.roll(np.roll(a, dy, 0), dx, 1)
    e = a & nb
    if not e.any(): return img
    L, C, h = lch(rgb2oklab(img[e][:, :3].astype(float)))
    tgt = np.stack([L * 0.45, C * 0.6 * np.cos(np.radians(h)), C * 0.6 * np.sin(np.radians(h))], -1)
    d = ((tgt[:, None] - pal_lab[None]) ** 2).sum(-1)
    out = img.copy(); out[e, :3] = pal[d.argmin(1)]
    return out


def shift_rows(layer, oy, ox, colshift=None):
    """oy, ox: per-row integer offsets; colshift: optional per-column extra dy. Pixels only move, never get recoloured."""
    h, w = layer.shape[:2]; out = np.zeros_like(layer)
    ys, xs = np.where(layer[:, :, 3] > 0)
    ny = ys + oy[ys] + (colshift[xs] if colshift is not None else 0); nx = xs + ox[ys]
    ok = (ny >= 0) & (ny < h) & (nx >= 0) & (nx < w)
    out[ny[ok], nx[ok]] = layer[ys[ok], xs[ok]]
    return out


def fill_gaps(img, rows):
    """a band moving 1 px away from the next leaves a transparent row inside the body: repeat the pixel above."""
    a = img[:, :, 3] > 0
    for y in rows:
        if not 0 < y < img.shape[0] - 1: continue
        m = ~a[y] & a[y - 1] & a[y + 1]
        img[y, m] = img[y - 1, m]
    return img


def levels(f, k):
    """(head_dy, chest_dy, pelvis_dy, shoulder_dx, pelvis_dx, hem_dx, tilt) at scale k (1 = 96, 2 = 48: 1 px at 96 is
    rounded like 74G (+1 -> 1, -1 -> 0); lateral moves at 48 only on the peak frames)."""
    sd, pd, hm = S_DX[(f - 1) % NF], P_DX[f], P_DX[(f - HEM_LAG) % NF]
    if k == 1:
        return H_DY[f], C_DY[f], P_DY[f], sd, pd, hm, TILT[f]
    half = lambda v: (v + 1) // 2
    peak = f in (3, 9)
    return half(H_DY[f]), half(C_DY[f]), half(P_DY[f]), (sd if peak else 0), (pd if peak else 0), (hm if f in (5, 11) else 0), 0


def hand_mask48(body):
    return hand_mask(body, 2)


def hand_mask(body, k=1):
    """skin pixels of the hands at the cape sides (official back shows both hands below the cape layers)."""
    L, C, h = lch(rgb2oklab(body[:, :, :3].reshape(-1, 3).astype(float)))
    hh, ww = body.shape[:2]
    L, C, h = (v.reshape(hh, ww) for v in (L, C, h))
    yy, xx = np.mgrid[0:hh, 0:ww]
    return (body[:, :, 3] > 0) & (h > 20) & (h < 80) & (L > 0.62) & (C < 0.12) & (yy > 64 // k) & ((xx < 34 // k) | (xx > 62 // k))


def frame(f, layers, hands, k=1):
    h, w = H // k, W // k
    hd_, cd, pdy, sdx, pdx, hmx, tilt = levels(f, k)
    pR = (f / NF) % 1.0; pL = (pR + 0.5) % 1.0
    sR, sL = leg_state(pR), leg_state(pL)
    legs = np.zeros((H, W, 4), np.uint8)
    for name, st in sorted((('R', sR), ('L', sL)), key=lambda t: t[1]['foot'] - t[1]['lift']):
        draw_leg(legs, LEG_X[name], st)
    if k == 2: legs = legs[1::2, 1::2].copy()
    body = layers['body'].copy()
    if hands.any():   # hand on the side of the leg that has just landed swings back = 1 px lower (closer)
        xs = np.mgrid[0:h, 0:w][1]
        dyR = 1 if pL < 0.33 else 0; dyL = 1 if pR < 0.33 else 0
        moved = np.zeros_like(body)
        for y, x in zip(*np.where(hands)):
            dy = (dyR if x >= w // 2 else dyL) if k == 1 else 0
            if 0 <= y + dy < h: moved[y + dy, x] = body[y, x]
        body[hands] = 0; m = moved[:, :, 3] > 0; body[m] = moved[m]
    yrow = (np.arange(h) * k + (k - 1))
    oy = np.where(yrow < WAIST_ROW, cd, pdy); ox = np.where(yrow < SHOULDER_ROW, sdx, np.where(yrow < WAIST_ROW, 0, np.where(yrow < HEM_ROW, pdx, hmx)))
    col = np.zeros(w, int)
    if tilt > 0: col[:46 // k] = 1
    if tilt < 0: col[51 // k:] = 1
    b = shift_rows(body, oy.astype(int), ox.astype(int), col)
    b = fill_gaps(b, [r // k for r in range(SHOULDER_ROW - 2, HEM_ROW + 30)])
    hdv = shift_rows(layers['head'], np.full(h, hd_), np.zeros(h, int))
    out = np.zeros((h, w, 4), np.uint8)
    for L in (legs, b, hdv):
        m = L[:, :, 3] > 0; out[m] = L[m]
    return out, dict(R=sR, L=sL)


def build(official_back, pal_dirs, out):
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for d in pal_dirs: paths += sorted(glob.glob(str(Path(d) / '*_12f_[0-9][0-9]_96x128.png')))
    pal = BB.palette(paths, 64)
    pal_lab = rgb2oklab(pal.astype(float))
    L96 = {k_: outline(v, pal_lab, pal) for k_, v in BB.base_layers(official_back, pal, 1.0).items()}
    L48 = {k_: outline(v, pal_lab, pal) for k_, v in BB.base_layers(official_back, pal, 0.5).items()}
    h96, h48 = hand_mask(L96['body']), hand_mask48(L48['body'])
    meta = {'task': 'MORWEN-WALK-UP-76', 'frames': {}, 'palette_colours': int(len(pal)), 'hand_px': [int(h96.sum()), int(h48.sum())]}
    for f in range(NF):
        im, st = frame(f, L96, h96, 1)
        im = outline(im, pal_lab, pal); im, n96 = clean_islands_generic(im)
        Image.fromarray(im, 'RGBA').save(out / f'morwen_up_walk_76_12f_{f:02d}_96x128.png')
        s, _ = frame(f, L48, h48, 2)
        s, n48 = clean_islands_generic(s)
        Image.fromarray(s, 'RGBA').save(out / f'morwen_up_walk_76_12f_{f:02d}_48x64.png')
        meta['frames'][f'{f:02d}'] = dict(R=st['R'], L=st['L'], levels96=levels(f, 1), levels48=levels(f, 2), islands=[n96, n48])
    (out / 'build_meta_76.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    return meta


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--official-back', type=Path, required=True)
    ap.add_argument('--palette-from', type=Path, nargs='+', required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(); m = build(a.official_back, a.palette_from, a.out); print('ok', m['palette_colours'], m['hand_px'])

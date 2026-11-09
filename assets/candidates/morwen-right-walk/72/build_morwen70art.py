#!/usr/bin/env python3
"""MORWEN-PIXEL-70 ART pass (ART-70A/B/C) on top of build_morwen70 (easing B).

ART-70A : boots only - buckle as a 3x3 ring with an open centre, X-lacing on a dark
          lace channel (period 2), 2x2 toe highlight cluster, sole welt + tread, heel split.
ART-70B : A + mantle / cape (non-protected motion layers): gold reduced to 3 tones
          (light / mid / dark, each an existing reference colour), 1px isolated noise merged
          into its 2-4px neighbourhood. 48x64 gets the same clean-up after sampling.
ART-70C : PROPOSAL ONLY (not adopted): B + the same clean-up applied inside protected
          layers (hat, flower, glasses gold, capelet, torso, skirt gold); face interior and
          eyes excluded. Delivered as separate frames + diff for review before adoption.
No body/chest motion is added; the collar/ribbon keeps 68's 1-frame-lag cloth motion.
  python3 build_morwen70art.py --source <65B> --out <dir> --art A|B|C
"""
from pathlib import Path
import argparse, json, math
import numpy as np
import build_morwen66 as B
import build_morwen67 as C
import build_morwen68 as D
import build_morwen70 as E

ART = {'level': 'B'}
GOLD3 = {}


def _lum(c): return 0.30 * c[..., 0] + 0.59 * c[..., 1] + 0.11 * c[..., 2]


def is_gold(rgb):
    r, g, b = (rgb[..., i].astype(int) for i in range(3))
    return (r > 150) & (g > 80) & (b < 110) & (r >= g) & (g > b)


def pick_gold3(ref):
    c = ref[ref[:, :, 3] > 0][:, :3].astype(int)
    gm = is_gold(c); L = _lum(c.astype(float))
    out = {}
    for name, lo, hi in (('light', 185, 999), ('mid', 120, 185), ('dark', 0, 120)):
        m = gm & (L >= lo) & (L < hi); cc = c[m]; mean = cc.mean(0)
        out[name] = tuple(int(v) for v in cc[np.argmin(((cc - mean) ** 2).sum(1))])
    return out


def gold3(layer, region=None):
    """map every gold pixel of the layer to one of 3 existing reference golds by luminance band."""
    a = layer[:, :, 3] > 0
    if region is not None: a &= region
    g = a & is_gold(layer[:, :, :3])
    L = _lum(layer[:, :, :3].astype(float))
    out = layer.copy()
    out[g & (L >= 185)] = (*GOLD3['light'], 255)
    out[g & (L >= 120) & (L < 185)] = (*GOLD3['mid'], 255)
    out[g & (L < 120)] = (*GOLD3['dark'], 255)
    return out, int(g.sum())


def denoise(layer, region=None, T=38.0):
    """merge 1px islands: a pixel that differs from all 4 neighbours while >=3 neighbours agree
    takes the neighbours' majority colour. One pass, layer-local, no new colours."""
    h, w = layer.shape[:2]
    a = layer[:, :, 3] > 0
    if region is not None: a = a & region
    src = layer.astype(int); out = layer.copy(); n = 0
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if not a[y, x]: continue
            nb = [(y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)]
            if not all(layer[p][3] > 0 for p in nb): continue
            c = src[y, x, :3]; cols = [src[p][:3] for p in nb]
            if min(np.sqrt(((c - q) ** 2 * [0.3, 0.59, 0.11]).sum() * 3) for q in cols) <= T: continue
            best, cnt = None, 0
            for q in cols:
                k = sum(np.sqrt(((q - r) ** 2 * [0.3, 0.59, 0.11]).sum() * 3) <= T for r in cols)
                if k > cnt: best, cnt = q, k
            if cnt >= 3:
                out[y, x, :3] = best; n += 1
    return out, n


# ------------------------------------------------------------------ boots (ART A)
_shade70 = E.shade70


def shade_art(lab, geo, pal, far, front_mask, swing):
    S, Bo, info = _shade70(lab, geo, pal, far, front_mask, swing)
    k = geo['k']; L = geo['leg']; big = k >= 1
    h, w = lab.shape
    yy, xx = np.mgrid[0:h, 0:w]; cx, cy = xx + 0.5, yy + 0.5
    bt = pal['boot_far' if far else 'boot']
    g_l, g_m, g_d = GOLD3['light'], GOLD3['mid'], GOLD3['dark']
    if far:   # far leg gold one step darker
        g_l, g_m, g_d = g_m, g_d, tuple(int(v * 0.8) for v in GOLD3['dark'])
    knee, ankle = L['knee'], L['ankle']
    vx, vy = ankle[0] - knee[0], ankle[1] - knee[1]; n = math.hypot(vx, vy); ux, uy = vx / n, vy / n
    nx, ny = uy, -ux
    if nx < 0: nx, ny = -nx, -ny
    u = ((cx - knee[0]) * nx + (cy - knee[1]) * ny) / (4.8 * k)
    s = ((cx - knee[0]) * ux + (cy - knee[1]) * uy) / n
    shaft = lab == D.BT; cuff = lab == D.CUFF
    if big:
        # X-lacing on a dark lace channel: rows alternate L+R / centre -> crossings read as X
        band = shaft & (u > 0.12) & (u < 0.80) & (s > 0.24) & (s < 0.90)
        steep = abs(math.degrees(math.atan2(vx, vy))) > 35
        Bo[band] = (*bt[1], 255)
        row = np.floor(s * n).astype(int) % 2
        col = np.clip(np.floor((u - 0.12) / 0.227), 0, 2).astype(int)
        if not steep:
            Bo[band & (row == 0) & (col == 0)] = (*g_m, 255)
            Bo[band & (row == 0) & (col == 2)] = (*g_d, 255)
        Bo[band & (row == 1) & (col == 1)] = (*g_l, 255)
        # buckle: 3x3 ring centred on the cuff, front of centre; centre stays open (boot dark)
        ys, xs = np.where(cuff)
        if len(xs):
            uu = u[ys, xs]; i = int(np.argmin(np.abs(uu - 0.30)))
            by, bx = int(round(ys[ys == ys[i]].mean())), xs[i]
            by = int(np.median(ys[np.abs(xs - bx) <= 1])) if (np.abs(xs - bx) <= 1).any() else by
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    y_, x_ = by + dy, bx + dx
                    if 0 <= y_ < h and 0 <= x_ < w and lab[y_, x_] != 0:
                        if dy == 0 and dx == 0: Bo[y_, x_] = (*bt[0], 255)
                        elif dy == -1 or dx == -1: Bo[y_, x_] = (*(g_l if (dy == -1 and dx == -1) else g_m), 255)
                        else: Bo[y_, x_] = (*g_d, 255)
            info['buckle_96'] = [int(bx), int(by)]
        # toe: 2x2 highlight cluster at the upper front of the toe cap, one specular pixel
        toe = lab == D.TOE
        if toe.any():
            ty, tx = np.where(toe); i = int(np.argmin(ty * 10 - tx))
            for dy in (0, 1):
                for dx in (-1, 0):
                    y_, x_ = ty[i] + dy, tx[i] + dx
                    if 0 <= y_ < h and 0 <= x_ < w and lab[y_, x_] in (D.TOE, D.FOOT): Bo[y_, x_] = (*bt[4], 255)
            Bo[ty[i], tx[i]] = (*bt[5], 255)
        # sole: welt (top row, lighter) + tread; heel split from the sole by one dark column
        sole = lab == D.SOLE; heel = lab == D.HEEL
        welt = sole & ~np.vstack([np.zeros((1, w), bool), sole[:-1]])
        Bo[sole] = (*bt[0], 255); Bo[welt] = (*bt[2], 255)
        hr = heel & ~np.hstack([heel[:, 1:], np.zeros((h, 1), bool)])
        Bo[hr] = (*C.OUTLINE, 255)
        Bo[heel & ~hr] = (*bt[1], 255)
        top_h = heel & ~np.vstack([np.zeros((1, w), bool), heel[:-1]]) & ~hr
        Bo[top_h] = (*bt[2], 255)
    else:
        ys, xs = np.where(cuff)
        if len(xs):
            uu = u[ys, xs]; i = int(np.argmax(uu)); Bo[ys[i], xs[i]] = (*g_l, 255)
            j = [q for q in range(len(xs)) if xs[q] == xs[i] - 1 and ys[q] == ys[i]]
            if j: Bo[ys[j[0]], xs[j[0]]] = (*g_d, 255)
    return S, Bo, info


# ------------------------------------------------------------------ compose with layer polish
def compose_art(f, U, pal, k):
    lvl = ART['level']
    if lvl in ('B', 'C'):
        U = dict(U)
        for name in ('mantle_front', 'cape_back', 'cape_front'):
            U[name], _ = gold3(U[name])
            for _p in range(2): U[name], _ = denoise(U[name])
        if lvl == 'C':
            h = U['torso'].shape[0]; yy, xx = np.mgrid[0:h, 0:U['torso'].shape[1]]
            sc = 1 if k >= 1 else 2
            face = (xx * sc >= 54) & (xx * sc <= 72) & (yy * sc >= 26) & (yy * sc <= 50)   # face interior / eyes excluded
            for name in ('immutable_details', 'torso', 'skirt'):
                U[name], _ = gold3(U[name], ~face)
                for _p in range(2): U[name], _ = denoise(U[name], ~face)
    return _compose68(f, U, pal, k)


_compose68 = D.compose68


def build(source: Path, out: Path, art='B'):
    ref, _ = B.load_reference(source / 'morwen_right_walk_00_96x128.png')
    GOLD3.clear(); GOLD3.update(pick_gold3(ref))
    ART['level'] = art
    uf, ub, _ = B.split_layers(ref)
    E.configure('B', uf)                 # easing B + rim/outline (70)
    D.shade68 = shade_art
    D.compose68 = compose_art
    try:
        res = D.build(source, out)
    finally:
        D.shade68 = E._shade68; D.compose68 = _compose68
    meta = json.loads((out / 'build_meta.json').read_text())
    meta['art70'] = {'level': art, 'gold3': {k: list(v) for k, v in GOLD3.items()},
                     'rim': {k: list(v) for k, v in E._RIM.items()}, 'easing_B': E.EASING_B}
    (out / 'build_meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')
    return res


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--art', choices=('A', 'B', 'C'), default='B')
    a = ap.parse_args(); build(a.source, a.out, a.art); print('ok')

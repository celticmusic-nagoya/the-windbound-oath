#!/usr/bin/env python3
"""PLAYER-WALK-POLISH-02-R2: local repair of the PR #133 down-04 candidate (no mirroring, no redraw).

Fixes, each from official pixels only:
  gap  : empty pixels inside the figure next to the front knee are refilled with the cloth (frill)
         that official 06 has at the same place (same donor shift as the legs); the earlier inpaint
         blob there is replaced by that cloth too.
  seam : the 04 crease that ends at y=850 is removed (inpaint along the thin bright line only);
         the 06 trousers below y=850 are brought to 04's trouser tone with a vertical gain ramp
         (full match at the boundary, fading out towards the knee guard), and the 06 crease is faded
         in over the first rows so it does not start abruptly.
usage: repair_r2.py BEST OUT [--ramp 40] [--crease-fade 18] [--no-gap] [--no-seam] [--debug DIR]
"""
import argparse, json, os
import numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
A = os.path.join(ROOT, 'img/field/characters/aidan/')
RECT = (976, 850, 1207, 1240); SHIFT = 8; Y0 = 850


def hsv(a):
    rgb = a[..., :3].astype(float) / 255; mx, mn = rgb.max(-1), rgb.min(-1); d = mx - mn + 1e-9
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, (g - b) / d % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, np.where(mx > 0, d / (mx + 1e-9), 0), mx


def trousers(a):
    h, s, v = hsv(a)
    return (a[..., 3] > 200) & (v < 0.42) & ((h < 40) | (h > 340)) & (s > 0.3)


def main():
    p = argparse.ArgumentParser(); p.add_argument('best'); p.add_argument('out')
    p.add_argument('--ramp', type=int, default=40); p.add_argument('--crease-fade', type=int, default=18)
    p.add_argument('--no-gap', action='store_true'); p.add_argument('--no-seam', action='store_true'); p.add_argument('--warp', action='store_true'); p.add_argument('--debug')
    o = p.parse_args()
    C = np.array(Image.open(o.best).convert('RGBA')).astype(float)
    O4 = np.array(Image.open(A + 'aidan_walk_down_04.png').convert('RGBA')).astype(float)
    O6 = np.roll(np.array(Image.open(A + 'aidan_walk_down_06.png').convert('RGBA')).astype(float), SHIFT, axis=1)
    H, W = C.shape[:2]; r = np.zeros((H, W), bool); x0, y0, x1, y1 = RECT; r[y0:y1, x0:x1] = True
    # irregular edit boundary: the rectangle plus the official-04 trousers (thighs) between the tunic hem
    # and y=850, so the 04 crease that ends at the old straight cut can be treated. Tunic/cape stay protected.
    t04 = trousers(O4); t04[:790] = False; t04[Y0:] = False; t04[:, :x0] = False; t04[:, x1:] = False
    r |= t04
    info = {}
    if not o.no_gap:
        # pixels inside the figure's outline (closing) that are not opaque, where 06 has opaque CLOTH (not leg)
        op = C[..., 3] > 200
        hull = ndi.binary_fill_holes(ndi.binary_closing(op, iterations=12)) & r
        h6, s6, v6 = hsv(O6)
        cloth6 = (O6[..., 3] > 24) & ~(((h6 < 40) | (h6 > 340)) & (s6 > 0.42)) & ~trousers(O6)
        filled_prev = np.zeros((H, W), bool)
        fm = os.path.join(os.path.dirname(o.best), 'aidan_walk_down_04_candidate_filled_mask.png')
        if os.path.exists(fm):
            filled_prev = np.array(Image.open(fm))[..., 0] > 0 if np.array(Image.open(fm)).ndim == 3 else np.array(Image.open(fm)) > 0
        gap = hull & (C[..., 3] < 200) & cloth6
        blob = filled_prev & cloth6 & r          # the earlier inpaint blob, where 06 has real cloth
        take = gap | blob
        # composite: 06 cloth under whatever the candidate already has opaque, but over the empty pixels / blob
        ta = O6[..., 3:4] / 255; ca = C[..., 3:4] / 255
        under = np.concatenate([(C[..., :3] * ca + O6[..., :3] * ta * (1 - ca)) / np.maximum(ca + ta * (1 - ca), 1e-6), (ca + ta * (1 - ca)) * 255], -1)
        C = np.where(gap[..., None], under, C); C = np.where(blob[..., None], O6, C)
        info['gap_px_filled_from_06_cloth'] = int(gap.sum()); info['inpaint_blob_px_replaced_by_06_cloth'] = int(blob.sum())
        info['remaining_enclosed_transparent_px'] = int((ndi.binary_fill_holes(C[..., 3] > 200) & ~(C[..., 3] > 200) & r).sum())
    if o.warp:
        # seam fix v2 (boundary redesign): the thighs between the 04 tunic hem and the knee guards are rebuilt
        # from the 06 thighs, stretched per column so the 06 hem line maps onto the 04 hem line and the knee-guard
        # top stays where it is. No horizontal cut is left: the trousers start at the hem cloth edge.
        h4, s4, v4 = hsv(O4); hc, sc, vc = hsv(C)
        T4 = trousers(O4); T6 = trousers(O6)
        armorC = (C[..., 3] > 200) & ((hc < 40) | (hc > 340)) & (sc > 0.42) & (vc >= 0.42)
        cols = np.arange(x0 + 10, x1 - 10)
        def first(mask, x, ya, yb):
            ys = np.nonzero(mask[ya:yb, x])[0]; return ya + ys[0] if len(ys) else np.nan
        yh4 = np.array([first(T4, x, 780, 900) for x in cols]); yh6 = np.array([first(T6, x, 780, 940) for x in cols])
        yk = np.array([first(armorC, x, 850, 1000) for x in cols])
        def smooth(v):
            idx = np.nonzero(~np.isnan(v))[0]
            if not len(idx): return v
            f = np.interp(np.arange(len(v)), idx, v[idx]); return ndi.gaussian_filter1d(ndi.median_filter(f, 9), 3)
        yh4s, yh6s, yks = smooth(yh4), smooth(yh6), smooth(yk)
        new = C.copy(); changed = np.zeros((H, W), bool)
        clothC = (C[..., 3] > 24) & ~(((hc < 40) | (hc > 340)) & (sc > 0.3) & (vc < 0.42)) & ~armorC   # hem/frill/cape pixels stay on top
        for i, x in enumerate(cols):
            a4, a6, k = yh4s[i], yh6s[i], yks[i]
            if np.isnan(a4) or np.isnan(a6) or np.isnan(k) or k - a4 < 6 or k - a6 < 6:
                continue
            ys = np.arange(int(np.floor(a4)), int(np.ceil(k)))
            src = a6 + (ys - a4) * (k - a6) / (k - a4)
            for y, sy in zip(ys, src):
                if clothC[y, x] and y < Y0:     # keep the 04 tunic/hem cloth exactly
                    continue
                y0i = int(np.floor(sy)); t = sy - y0i
                pix = O6[y0i, x] * (1 - t) + O6[min(y0i + 1, H - 1), x] * t
                if T6[y0i, x] or T6[min(y0i + 1, H - 1), x]:
                    if clothC[y, x] and y >= Y0:
                        continue
                    new[y, x] = pix; changed[y, x] = True
        C = new; info['warp_px'] = int(changed.sum())
        r |= changed
        if o.debug:
            os.makedirs(o.debug, exist_ok=True)
            json.dump({'cols': cols.tolist(), 'hem04': yh4s.tolist(), 'hem06': yh6s.tolist(), 'knee': yks.tolist()}, open(os.path.join(o.debug, 'contours.json'), 'w'))
    if not o.no_seam:
        T = trousers(C)
        # 1) the 04 crease that stops at y=850: thin bright vertical line inside the 04 trousers just above the seam
        band = np.zeros((H, W), bool); band[Y0 - 40:Y0 + 2, x0:x1] = True
        gray = C[..., :3].mean(-1)
        local = ndi.uniform_filter(gray, 9)
        crease = band & ndi.binary_dilation(T, iterations=3) & (gray - local > 18) & (C[..., 3] > 200)
        lab, n = ndi.label(crease)
        if n:
            sizes = ndi.sum(crease, lab, range(1, n + 1)); hgt = [np.ptp(np.nonzero(lab == i)[0]) for i in range(1, n + 1)]
            crease = np.isin(lab, [i + 1 for i in range(n) if hgt[i] >= 8 and sizes[i] <= 300])
        crease = ndi.binary_dilation(crease, iterations=1)
        if crease.any():
            rgb = np.clip(C[..., :3], 0, 255).astype(np.uint8)
            rgb = cv2.inpaint(rgb, crease.astype(np.uint8) * 255, 4, cv2.INPAINT_TELEA)
            C[crease, :3] = rgb[crease]
        info['crease_04_px_removed'] = int(crease.sum())
        # 2) tone ramp: match the 06 trousers below the seam to the 04 trousers just above it, column-smoothed
        above = T.copy(); above[:Y0 - 14] = False; above[Y0:] = False
        below = T.copy(); below[:Y0] = False; below[Y0 + 14:] = False
        def colmean(mask):
            s = np.zeros((W, 3)); c = np.zeros(W)
            for ch in range(3):
                s[:, ch] = (C[..., ch] * mask).sum(0)
            c = mask.sum(0)
            m = s / np.maximum(c[:, None], 1); valid = c > 2
            return m, valid
        ma, va = colmean(above); mb, vb = colmean(below)
        ok = va & vb
        g = np.ones((W, 3)); g[ok] = ma[ok] / np.maximum(mb[ok], 1)
        g = np.clip(g, 0.6, 2.2)
        # fill columns without data from neighbours and smooth along x
        for ch in range(3):
            col = g[:, ch].copy(); idx = np.nonzero(ok)[0]
            if len(idx):
                col = np.interp(np.arange(W), idx, col[idx]); g[:, ch] = ndi.gaussian_filter1d(col, 6)
        ramp = np.zeros(H); ramp[Y0:Y0 + o.ramp] = np.linspace(1, 0, o.ramp)
        Tb = T.copy(); Tb[:Y0] = False
        k = 1 + (g[None, :, :] - 1) * ramp[:, None, None]
        C[..., :3] = np.where(Tb[..., None], np.clip(C[..., :3] * k, 0, 255), C[..., :3])
        info['tone_gain_median'] = [round(float(x), 3) for x in np.median(g[ok], 0)] if ok.any() else None
        # 3) fade the 06 crease in (bright thin line in the first rows below the seam -> pulled to local trouser tone)
        if o.crease_fade:
            fb = np.zeros((H, W), bool); fb[Y0:Y0 + o.crease_fade, x0:x1] = True
            gray = C[..., :3].mean(-1); local = ndi.median_filter(gray, size=9)
            line = fb & ndi.binary_dilation(T, iterations=3) & (gray - local > 15) & (C[..., 3] > 200)
            w = np.zeros(H); w[Y0:Y0 + o.crease_fade] = np.linspace(1, 0, o.crease_fade)
            med = np.stack([ndi.median_filter(C[..., ch], size=9) for ch in range(3)], -1)
            C[..., :3] = np.where(line[..., None], C[..., :3] * (1 - w[:, None, None]) + med * w[:, None, None], C[..., :3])
            info['crease_06_px_faded'] = int(line.sum())
    out = np.clip(C, 0, 255).round().astype(np.uint8)
    # protection: nothing outside the edit rectangle may differ from official 04
    o4 = O4.astype(np.uint8); out[~r] = o4[~r]
    Image.fromarray(out).save(o.out)
    info['outside_rect_identical_to_official_04'] = bool((out[~r] == o4[~r]).all())
    print(json.dumps(info, ensure_ascii=False))


if __name__ == '__main__':
    main()

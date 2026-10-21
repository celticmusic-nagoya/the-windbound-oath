#!/usr/bin/env python3
"""Aidan idle v1 -- blink overlays built from the official MASTER (never modified).

Method (each eye is processed independently):
  Measured on the MASTER per eye: upper lash band (top edge detected, bottom edge from the manual 'band_bottom' line because the dark pupil merges
  with the lash), lower-lid line B(x), closed-lid line C(x).
  Stage k (0..1):  lash line  L_k = Tc + k (C - Tc)   (Tc = open lash centre),  the lower lid rises  B_k = B - k (B - C)
   * eye content (dark lash / iris / sclera / gold rim, found by colour) ABOVE L_k and BELOW B_k is replaced by lid skin: a per-column gradient between
     the skin measured just above the lash band and the skin measured just under the eye (continuity at both ends); skin-coloured pixels of the zone,
     bangs, brow and the outer lash flare are never touched,
   * the eyeball between L_k and B_k keeps MASTER pixels with a soft lid shadow under the lash line,
   * a lash line is drawn at L_k: dark core + soft brown edge (the MASTER lash colours), tapering at both ends,
   * at k = 1 the aperture is gone: no iris / sclera pixel remains in the zone.
  Overlays are RGBA patches; alpha = 255 only where a pixel differs from the MASTER (open eye = no overlay = the MASTER itself).
usage: make_blink.py MASTER.png OUTDIR   -> OUTDIR/overlay_{L,R}_s{1..4}.png (+ boxes.json)
"""
import sys, json, numpy as np, cv2
from PIL import Image

SS = 4
STAGES = [0.30, 0.60, 0.85, 1.00]

EYES = {   # polylines (x, y) in MASTER pixels, measured on the 2026-10-21 Aidan MASTER (1312x1199)
  'L': dict(box=(838, 220, 888, 254), xr=(843.0, 881.0), band_win=(225, 240), feather=4.0,   # near eye (3/4 view)
            band_bottom=[(843,229.6),(850,230.2),(858,230.8),(864,231.0),(869,231.6),(873,233.0),(877,235.0),(881,237.0)],
            lower=[(843,235),(847,238),(850,241.5),(853,243.8),(857,245.6),(862,247.0),(867,247.0),(871,245.8),(874,243.5),(877,240.5),(881,237.0)],
            closed=[(843,233.0),(847,236.0),(851,239.2),(856,241.6),(862,242.8),(868,242.2),(873,240.2),(877,237.6),(881,235.0)],
            lash_w=(1.9, 3.2)),
  'R': dict(box=(904, 233, 936, 261), xr=(908.0, 923.0), band_win=(236, 248), feather=3.0,   # far eye (half hidden by bangs / cheek line)
            band_bottom=[(908,248.5),(912,247.0),(916,245.2),(920,244.0),(923,243.6)],
            lower=[(908,252),(910,254.5),(913,256.2),(917,256.4),(921,254.6),(924,251.5)],
            closed=[(908,249.0),(912,251.0),(916,252.0),(920,250.6),(923,248.0)],
            lash_w=(1.5, 2.3)),
}
CORE = np.array([34, 16, 11.], np.float32)      # lash core (median of the MASTER lash pixels)
EDGE = np.array([112, 56, 36.], np.float32)     # lash soft edge (the MASTER lash's brown fringe)

def poly_y(pts, x):
    xs, ys = zip(*pts); return np.interp(x, xs, ys)

def lash_top(lum, xr, y0, y1):
    top = {}
    for x in range(int(xr[0]), int(xr[1]) + 1):
        ys = np.where(lum[y0:y1, x] < 0.30)[0]
        if len(ys): top[x] = y0 + ys[0]
    return top

def smooth(v, s): return cv2.GaussianBlur(np.asarray(v, np.float32).reshape(1, -1), (0, 0), s)[0]

def build(master_path, outdir):
    A = np.array(Image.open(master_path).convert('RGBA')); rgb = A[..., :3].astype(np.float32); alpha = A[..., 3]
    lum_all = rgb.mean(-1) / 255
    res = {}
    for eid, E in EYES.items():
        bx0, by0, bx1, by1 = E['box']; W, H = bx1 - bx0, by1 - by0
        xs = np.arange(bx0, bx1) + 0.5; ys = np.arange(by0, by1) + 0.5
        inx = (xs >= E['xr'][0]) & (xs <= E['xr'][1])
        top = lash_top(lum_all, E['xr'], *E['band_win']); keys = sorted(top)
        Tt = smooth(np.interp(xs, keys, [top[k] for k in keys]), 0.8)
        Tb = poly_y(E['band_bottom'], xs).astype(np.float32); Tc = (Tt + Tb) / 2
        Cc = poly_y(E['closed'], xs); Bl = poly_y(E['lower'], xs)
        base = rgb[by0:by1, bx0:bx1]; lum_b = base.mean(-1) / 255
        def ctx(i, ya, yb):
            x = int(xs[i] - bx0); a_, b_ = int(ya) - by0, int(yb) - by0
            px = base[max(a_, 0):max(b_, 1), max(x - 1, 0):x + 2].reshape(-1, 3); l = px.mean(-1) / 255
            px = px[(l > 0.34) & (l < 0.98)]
            return np.median(px, axis=0) if len(px) else None
        def fillnone(arr, default):
            v = np.array([x if x is not None else np.full(3, np.nan) for x in arr], np.float32)
            for c in range(3):
                good = ~np.isnan(v[:, c]); v[:, c] = np.interp(np.arange(W), np.where(good)[0], v[good, c]) if good.any() else default[c]
            return cv2.GaussianBlur(v.reshape(1, W, 3), (0, 0), 4.0)[0]
        peach = np.array([248, 208, 178.], np.float32)
        cTop = fillnone([ctx(i, Tt[i] - 4, Tt[i] - 0.5) if inx[i] else None for i in range(W)], peach)
        cBot = fillnone([ctx(i, Bl[i] + 1.5, Bl[i] + 5) if inx[i] else None for i in range(W)], peach)
        Yc = ys[:, None]
        t = np.clip((Yc - Tt[None, :]) / np.maximum(Bl[None, :] - Tt[None, :], 1), 0, 1); t = t ** 1.2; t = t * t * (3 - 2 * t)
        skin = cv2.GaussianBlur(((0.80 * cTop + 0.20 * cBot)[None] * (1 - t[..., None]) + cBot[None] * t[..., None]).astype(np.float32), (0, 0), 0.7)
        # texture: the skin/bangs-shadow above the band is mirrored across the seam, so strands and grain continue into the lid and fade into the gradient with distance
        full = rgb
        yy_full = (np.arange(H, dtype=np.float32)[:, None] + by0)                        # row index of each box row (pixel centres at integer index)
        seam = (Tt[None, :] - 0.5)                                                       # first row of the band (index space)
        ymir = np.clip(2 * seam - yy_full, by0 - 12, None).astype(np.float32)
        mx_map = (np.arange(W, dtype=np.float32)[None, :] + bx0) * np.ones((H, 1), np.float32)
        mirror = cv2.remap(full, mx_map, ymir, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        wmir = np.clip(1 - (yy_full - seam) / 6.0, 0, 1) ** 1.2
        skin = skin * (1 - wmir[..., None] * 0.85) + mirror * (wmir[..., None] * 0.85)
        # eye content by colour, inside the zone only
        zone = np.zeros((H, W), np.float32)
        for i in range(W):
            if inx[i]:
                ya = int(np.floor(Tt[i] - 0.5)) - by0; yb = int(np.ceil(Bl[i] + 0.5)) - by0; zone[max(ya, 0):min(yb, H), i] = 1
        mx, mn = base.max(-1), base.min(-1); sat = (mx - mn) / np.maximum(mx, 1); val = mx / 255
        r_, g_, b_ = base[..., 0], base[..., 1], base[..., 2]
        dark = lum_b < 0.34; green = (g_ > r_ - 8) & (g_ > b_ + 10); white = (val > 0.90) & (sat < 0.16)
        gold = (sat > 0.35) & (val > 0.55) & (g_ > b_ + 40) & (r_ > b_ + 60) & (g_ > 120) & (np.abs(r_ - g_) < 70)
        cls = cv2.dilate((dark | green | white | gold).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))).astype(np.float32)
        content = zone * cls
        hard = cv2.dilate(dark.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32) * (cv2.dilate(zone, np.ones((5, 5), np.uint8)) > 0)
        content = np.maximum(content, hard)
        up = lambda a: cv2.resize(a, (W * SS, H * SS), interpolation=cv2.INTER_NEAREST)
        content_s, hard_s, zone_s = up(content), up(hard), up(zone)
        fx_ = np.clip(np.minimum(xs - E['xr'][0], E['xr'][1] - xs) / E['feather'], 0, 1); fx_ = np.where(inx, fx_ * fx_ * (3 - 2 * fx_), 0)
        Hs, Ws = H * SS, W * SS
        yy = (np.arange(Hs) + 0.5) / SS + by0; xx = (np.arange(Ws) + 0.5) / SS + bx0
        fxs = np.interp(xx, xs, fx_)[None, :]
        Tts = np.interp(xx, xs, Tt); Bls = np.interp(xx, xs, Bl); Tcs = np.interp(xx, xs, Tc); Ccs = np.interp(xx, xs, Cc)
        Y = yy[:, None]
        for si, k in enumerate(STAGES, 1):
            Ls = Tcs + k * (Ccs - Tcs); Bk = Bls - k * (Bls - Ccs)
            above = (Y < Ls[None, :]) & (Y >= (Tts[None, :] - 1.0))
            below = (Y > Bk[None, :]) & (Y <= (Bls[None, :] + 1.0))
            vf = np.clip((Y - Tts[None, :]) / 2.4, 0, 1); vf = vf * vf * (3 - 2 * vf)
            cover = (above * np.maximum(vf, 0.0) + below * content_s) * zone_s * fxs
            wx = E['lash_w'][0] + (E['lash_w'][1] - E['lash_w'][0]) * np.clip((xx - E['xr'][0]) / (E['xr'][1] - E['xr'][0]), 0, 1)
            taper = np.clip(np.minimum(xx - E['xr'][0], E['xr'][1] - xx) / 4.0, 0.25, 1)
            half = (wx * taper / 2)[None, :]
            core = (np.abs(Y - Ls[None, :]) <= half * 0.62) * fxs.clip(0.0, 1.0)
            fringe = (np.abs(Y - Ls[None, :]) <= half * 1.25 + 0.4) * fxs
            dd = Y - Ls[None, :]
            shadow = np.where((dd > 0) & (dd < 2.6), (1 - dd / 2.6) * 0.28, 0) * fxs
            d = lambda a: a.reshape(H, SS, W, SS).mean((1, 3))
            cov, cor, fri, shd = d(cover), d(core.astype(np.float32)), d(fringe.astype(np.float32)), d(shadow.astype(np.float32))
            out = base * (1 - shd[..., None])
            out = out * (1 - cov[..., None]) + skin * cov[..., None]
            fa = (fri * 0.55)[..., None]; out = out * (1 - fa) + EDGE[None, None, :] * fa
            ca = cor[..., None]; out = out * (1 - ca) + CORE[None, None, :] * ca
            diff = np.abs(out - base).max(-1)
            a = (diff > 0.6).astype(np.float32) * (alpha[by0:by1, bx0:bx1] > 0)
            patch = np.dstack([np.clip(out, 0, 255), a * 255]).astype(np.uint8)
            res[(eid, si)] = patch
            Image.fromarray(patch, 'RGBA').save(f'{outdir}/overlay_{eid}_s{si}.png')
    json.dump({e: E['box'] for e, E in EYES.items()}, open(f'{outdir}/boxes.json', 'w'))
    return res

if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])

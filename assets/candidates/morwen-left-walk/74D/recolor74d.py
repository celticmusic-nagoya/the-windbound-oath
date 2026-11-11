"""ART-74D part-wise colour adjustment of the left-side reference (right-view coords) toward the official left profile.

Not a global hue / saturation filter: every part (hat, hair, collar bow, jacket, skirt, mantle) gets its own target taken
from the official left profile (OKLab statistics of that part, OFFICIAL below), and inside every part
  - lightness  : quantile mapping sprite-part L -> official-part L (shading order kept, contrast kept for pixel art)
  - chroma     : scaled to the official part's median chroma
  - hue        : pulled to the official part hue, the part's own hue variation is kept at 35 %
  - gold       : mapped to the official antique-gold ramp of that part (hat band / mantle trim)
  - 1-px gold specks (no gold 4-neighbour) inside jacket / skirt / mantle / hat crown -> the part's own base colour
    (gold ornament lines and trims stay)
  - skin, whites (blouse frill / lining highlights), eyes + glasses box and earring are not touched.
"""
import numpy as np
from oklab import rgb2oklab, oklab2rgb, lch

# official left profile, OKLab percentiles L(5,25,50,75,95), median chroma, hue (deg) - measured by sample_official()
OFFICIAL = {
    'hat':    dict(L=[0.200, 0.290, 0.365, 0.430, 0.560], C=0.073, h=318),
    'hair':   dict(L=[0.179, 0.271, 0.365, 0.415, 0.444], C=0.057, h=332),
    'bow':    dict(L=[0.190, 0.333, 0.442, 0.625, 0.843], C=0.142, h=315),
    'jacket': dict(L=[0.160, 0.286, 0.379, 0.469, 0.750], C=0.070, h=317),
    'skirt':  dict(L=[0.189, 0.323, 0.431, 0.587, 0.700], C=0.074, h=318),
    'potion': dict(L=[0.339, 0.537, 0.661, 0.849, 0.989], C=0.102, h=322),
    'mantle': dict(L=[0.190, 0.290, 0.370, 0.470, 0.680], C=0.104, h=314),   # measured .223/.327/.417/.512/.747 incl. the light lining; sprite shows the outer side -> darker
}
OFFICIAL_GOLD = {   # measured: hat L .66/.76/.81/.87/.93 C .110 h 67, mantle L .76/.82/.86/.90/.94 C .097 h 71
    'hat':    dict(L=[0.661, 0.759, 0.812, 0.872, 0.933], C=0.110, h=67),
    'mantle': dict(L=[0.759, 0.819, 0.859, 0.902, 0.944], C=0.097, h=71),
}
# pixel-art targets derived from the measurements: small sprite areas read duller and flatter than the painted sheet,
# so purple chroma x1.25 and the gold ramp keeps a dark step for edge definition (hue / light end = official).
PIX_CHROMA = 1.25
GOLD_PIX = dict(L=[0.50, 0.62, 0.73, 0.83, 0.93], C=0.115, h=72)
PARTS = ('hat', 'hair', 'bow', 'jacket', 'skirt', 'mantle', 'potion')
SPECK_PARTS = ('hat', 'jacket', 'skirt', 'mantle')
HUE_KEEP = 0.35


def sample_official(img):
    """recompute OFFICIAL / OFFICIAL_GOLD from the official left profile (1024x1536 RGBA). Boxes in that image."""
    boxes = {'hat': [(520, 20, 700, 120), (260, 40, 700, 330)], 'hair': [(390, 190, 500, 330)], 'bow': [(390, 355, 445, 410)],
             'jacket': [(360, 420, 470, 700)], 'skirt': [(300, 700, 460, 830)], 'mantle': [(520, 580, 780, 1330)],
             'potion': [(300, 620, 340, 700)]}
    out = {}
    for k, bl in boxes.items():
        cs = [img[y0:y1, x0:x1][img[y0:y1, x0:x1, 3] > 250][:, :3] for x0, y0, x1, y1 in bl]
        L, C, h = lch(rgb2oklab(np.concatenate(cs).astype(float)))
        out[k] = dict(L=list(np.round(np.percentile(L, [5, 25, 50, 75, 95]), 3)), C=round(float(np.median(C)), 3))
    return out


def classes(rgb):
    lab = rgb2oklab(rgb.astype(float)); L, C, h = lch(lab)
    gold = (h > 45) & (h < 115) & (C >= 0.085) & (L > 0.42)
    skin = (h > 20) & (h < 80) & (C < 0.11) & (L > 0.62) & ~gold
    white = (L > 0.90) & (C < 0.05)
    return lab, L, C, h, gold, skin, white


def qmap(x, src_q, dst_q):
    """monotone piecewise-linear quantile map, linear extrapolation at both ends."""
    s = np.asarray(src_q, float); d = np.asarray(dst_q, float)
    s = np.maximum.accumulate(s + np.arange(len(s)) * 1e-6)
    y = np.interp(x, s, d)
    lo, hi = x < s[0], x > s[-1]
    y[lo] = d[0] + (x[lo] - s[0]) * (d[1] - d[0]) / max(s[1] - s[0], 1e-6)
    y[hi] = d[-1] + (x[hi] - s[-1]) * (d[-1] - d[-2]) / max(s[-1] - s[-2], 1e-6)
    return np.clip(y, 0.04, 0.97)


def circ_mean(h):
    r = np.radians(h); return float(np.degrees(np.arctan2(np.sin(r).mean(), np.cos(r).mean())) % 360)


def recolor(ref, part, keep):
    """ref: HxWx4 uint8 (right-view coords). part: dict name -> bool mask. keep: bool mask never changed.
    returns (new_ref, log)."""
    out = ref.copy(); log = {}
    op = ref[:, :, 3] > 0
    lab, L, C, h, gold, skin, white = classes(ref[:, :, :3])
    goldn = sum(np.roll(np.roll(gold & op, dy, 0), dx, 1).astype(int) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    for name in PARTS:
        m = part[name] & op & ~keep & ~skin & ~white
        if not m.any(): continue
        speck = (gold & (goldn == 0) & m) if name in SPECK_PARTS else np.zeros_like(m)
        base = m & ~gold
        o = OFFICIAL[name]
        sq = np.percentile(L[base], [5, 25, 50, 75, 95])
        sC = float(np.median(C[base])); sh = circ_mean(h[base])
        k = float(np.clip(o['C'] * PIX_CHROMA / max(sC, 1e-4), 0.25, 1.4))
        tgt = base | speck
        L2 = qmap(L[tgt], sq, o['L'])
        dh = ((h[tgt] - sh + 180) % 360) - 180
        h2 = (o['h'] + HUE_KEEP * dh) % 360
        C2 = C[tgt] * k
        if speck.any():   # specks take the part's median base colour at their own lightness rank
            sp = speck[tgt]
            C2[sp] = o['C'] * PIX_CHROMA; h2[sp] = o['h']; L2[sp] = np.clip(L2[sp] * 0.8, 0.1, 0.9)
        new = np.stack([L2, C2 * np.cos(np.radians(h2)), C2 * np.sin(np.radians(h2))], -1)
        out[tgt, :3] = oklab2rgb(new)
        g = m & gold & ~speck
        log[name] = dict(px=int(m.sum()), base=int(base.sum()), gold=int(g.sum()), specks_removed=int(speck.sum()),
                         src_L=[round(v, 3) for v in sq], src_C=round(sC, 3), src_h=round(sh, 1), chroma_scale=round(k, 3))
        if g.any():
            og = GOLD_PIX
            gq = np.percentile(L[g], [5, 25, 50, 75, 95])
            Lg = qmap(L[g], gq, og['L'])
            Cg = np.clip(C[g] * (og['C'] / max(float(np.median(C[g])), 1e-4)), 0.03, 0.16)
            dhg = ((h[g] - circ_mean(h[g]) + 180) % 360) - 180
            hg = (og['h'] + 0.3 * dhg) % 360
            out[g, :3] = oklab2rgb(np.stack([Lg, Cg * np.cos(np.radians(hg)), Cg * np.sin(np.radians(hg))], -1))
    return out, log

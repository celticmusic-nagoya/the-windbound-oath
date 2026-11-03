#!/usr/bin/env python3
"""DIRECTIVE-ART-04 shared pixel-art helpers (deterministic, numpy + PIL only).

Target style = the delivered outdoor Rilde art (e.g. img/field/moss/rilde/lind/lind_aidan_house.png): 2 source px per world px
(@2x), warm saturated wood, cream plaster, thin dark-brown edges, banded ramp shading lit from the upper left, no blur and no
anti-aliasing (every pixel is a palette colour; alpha is 0 or 255).
"""
import numpy as np
from PIL import Image, ImageDraw


def hx(s):
    s = s.lstrip('#'); return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.uint8)


def ramp(*cols):
    return np.stack([hx(c) for c in cols])


# ---- palettes sampled / derived from the outdoor house art --------------------------------------------------------
WOOD = ramp('#3a2112', '#5a341b', '#7a4724', '#9a5d2e', '#b8743a', '#d28f4c', '#e8ac63')
WOOD_FLOOR = ramp('#6b4a2c', '#86603a', '#9d7445', '#b2874f', '#c49a5c', '#d4ab6a', '#e2bd7c')
DARKWOOD = ramp('#24140b', '#341d10', '#472816', '#5c361e', '#714429', '#875536')
PLASTER = ramp('#9c8a6a', '#b6a27e', '#cdb992', '#ddcba3', '#e9dab5', '#f3e8c8')
STONE = ramp('#3b302a', '#564840', '#706056', '#8a796b', '#a59382', '#bfad99', '#d8c8b2')
IRON = ramp('#18171a', '#2b2a2f', '#403f46', '#5b5a63')
BRASS = ramp('#6b4a14', '#9a6c1e', '#c99a33', '#ecc75e', '#fbe7a0')
CREAM = ramp('#a39276', '#bfae8e', '#d8c9a8', '#ebdfc2', '#f8f0dc')
GREEN = ramp('#173224', '#214632', '#2d5c40', '#3c744f', '#4f8c5f', '#68a572')
GOLD = ramp('#6e4a12', '#9b6d1f', '#c6942f', '#e3b84e', '#f6dc86')
RED = ramp('#3e1410', '#5e1d16', '#80281d', '#a23626', '#c04a33', '#d9694a')
FIRE = ramp('#5a160c', '#9a2a10', '#d24a12', '#f0791c', '#fbab2e', '#ffd659', '#fff4c0')
GLASS = ramp('#3f6f8a', '#5a8eaa', '#79abc4', '#9bc6d8', '#c1dfe9', '#e9f6f8')
EDGE = hx('#2a170c')


# ---- periodic value noise (tiles seamlessly when the image size is a multiple of the cell) -------------------------
def pnoise(w, h, cw, ch, seed, octaves=3):
    rng = np.random.default_rng(seed); out = np.zeros((h, w)); amp = 1.0; tot = 0
    for o in range(octaves):
        gx, gy = max(1, w // cw), max(1, h // ch)
        g = rng.random((gy, gx))
        ys = np.arange(h) * gy / h; xs = np.arange(w) * gx / w
        y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int)
        fy = ys - y0; fx = xs - x0; fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
        y1 = (y0 + 1) % gy; x1 = (x0 + 1) % gx; y0 %= gy; x0 %= gx
        a = g[np.ix_(y0, x0)]; b = g[np.ix_(y0, x1)]; c = g[np.ix_(y1, x0)]; d = g[np.ix_(y1, x1)]
        out += amp * ((a * (1 - fx) + b * fx) * (1 - fy)[:, None] + (c * (1 - fx) + d * fx) * fy[:, None])
        tot += amp; amp *= .5; cw = max(1, cw // 2); ch = max(1, ch // 2)
    return out / tot


def quant(v, pal, dither=None):
    """v in [0,1] -> palette index image; optional 2x2 Bayer dither strength (0..1) only at band borders."""
    n = len(pal); x = np.clip(v, 0, 1) * (n - 1)
    if dither:
        b = np.array([[0, .5], [.75, .25]]) - .375
        h, w = v.shape; x = x + dither * np.tile(b, (h // 2 + 1, w // 2 + 1))[:h, :w]
    return np.clip(np.rint(x), 0, n - 1).astype(int)


class Img:
    """RGBA canvas in source pixels (= half world px)."""
    def __init__(self, w, h):
        self.w, self.h = w, h; self.rgb = np.zeros((h, w, 3), np.uint8); self.a = np.zeros((h, w), np.uint8)

    def put(self, mask, pal, v, dither=None):
        idx = quant(v, pal, dither); self.rgb[mask] = pal[idx][mask]; self.a[mask] = 255

    def solid(self, mask, col):
        self.rgb[mask] = col; self.a[mask] = 255

    def save(self, path):
        Image.fromarray(np.dstack([self.rgb, self.a]), 'RGBA').save(path, optimize=False)

    def pil(self):
        return Image.fromarray(np.dstack([self.rgb, self.a]), 'RGBA')


def poly_mask(w, h, pts):
    im = Image.new('L', (w, h), 0); ImageDraw.Draw(im).polygon([tuple(p) for p in pts], fill=255)
    return np.array(im) > 0


def ellipse_mask(w, h, box):
    im = Image.new('L', (w, h), 0); ImageDraw.Draw(im).ellipse(box, fill=255); return np.array(im) > 0


def rect_mask(w, h, x0, y0, x1, y1):
    m = np.zeros((h, w), bool); m[max(0, y0):min(h, y1), max(0, x0):min(w, x1)] = True; return m


def erode_depth(mask, k=6):
    """Approximate distance to the shape edge (1 = edge pixel) by repeated 4-neighbour erosion."""
    d = np.zeros(mask.shape, int); cur = mask.copy()
    for i in range(1, k + 1):
        nb = cur.copy(); nb[1:] &= cur[:-1]; nb[:-1] &= cur[1:]; nb[:, 1:] &= cur[:, :-1]; nb[:, :-1] &= cur[:, 1:]
        d[cur & ~nb] = i; cur = nb
    d[cur] = k + 1; return d


def shade(mask, k=6, light=(-.6, -.8), base=.45, round_=.35, slope=.35):
    """Banded volume shading for a flat shape: rounder toward the middle, brighter toward the light (upper left)."""
    h, w = mask.shape; ys, xs = np.nonzero(mask)
    if len(xs) == 0: return np.zeros((h, w))
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    X = (np.arange(w)[None, :] - x0) / max(1, x1 - x0) - .5; Y = (np.arange(h)[:, None] - y0) / max(1, y1 - y0) - .5
    lit = -(X * light[0] + Y * light[1])
    d = np.minimum(erode_depth(mask, k), k) / k
    return base + round_ * (d - .5) + slope * lit


def outline(img, mask, col=EDGE, inner=False):
    """1-px edge in a dark material colour on the shape border (inside the shape)."""
    d = erode_depth(mask, 1); e = mask & (d == 1); img.solid(e, col); return e

#!/usr/bin/env python3
"""Make the opposite-foot frame of a front/back walk pose by mirroring only the legs.

The legs (trousers/skin, boots and anything enclosed by them such as boot flowers) are
selected inside a rectangle below a cut line, removed from the frame, mirrored about a
vertical axis and drawn back BEHIND the remaining clothing. The upper body, the cape/skirt,
the face and the equipment stay as painted, so the character design is unchanged.

usage: mirror_legs.py SRC OUT --rect X0 Y0 X1 Y1 [--axis X] [--mask MASK.png]
       [--legs "h0-h1:smin:vmax,..."] [--dark V]
  --axis: mirror axis x (default: the axis that best matches the leg pixels to their mirror)
  --legs: hue ranges (deg) counted as leg colour, each with min saturation and max value
  --dark: any pixel darker than V (0-1) counts as leg (trousers, soles, shadows)
"""
import argparse
import numpy as np
from PIL import Image
from scipy import ndimage as ndi


def hsv(rgb):
    r, g, b = [rgb[..., i] / 255.0 for i in range(3)]
    mx, mn = np.max(rgb, -1) / 255.0, np.min(rgb, -1) / 255.0
    d = mx - mn + 1e-9
    h = np.where(mx == r, (g - b) / d % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    s = np.where(mx > 0, (mx - mn) / (mx + 1e-9), 0)
    return h, s, mx


def leg_mask(a, rect, ranges, dark):
    x0, y0, x1, y1 = rect
    h, s, v = hsv(a[..., :3].astype(float))
    op = a[..., 3] > 24
    m = np.zeros(op.shape, bool)
    for h0, h1, smin, vmax in ranges:
        m |= (h >= h0) & (h <= h1) & (s >= smin) & (v <= vmax)
    m |= (v < dark) & ~((h > 60) & (h < 200) & (s > 0.15))   # dark trousers/soles, but not the dark folds of a green cape
    m &= op
    r = np.zeros_like(m); r[y0:y1, x0:x1] = True
    m &= r
    m = ndi.binary_opening(m, iterations=1)
    lab, n = ndi.label(m)
    if n:
        sizes = ndi.sum(m, lab, range(1, n + 1))
        # keep only blobs that reach the lowest quarter of the rectangle (the feet), so cape trim is never taken
        low = set(np.unique(lab[y0 + (y1 - y0) * 3 // 4:y1, x0:x1])) - {0}
        m = np.isin(lab, [i for i in low if sizes[i - 1] >= 400])
    m = ndi.binary_fill_holes(ndi.binary_closing(m, iterations=2)) & r
    m = ndi.binary_dilation(m, iterations=2) & op & r   # take the anti-aliased rim too (no ghost outline)
    return m


def best_axis(m, lo, hi):
    ys, xs = np.nonzero(m)
    best = (-1, None)
    for ax in np.arange(lo, hi, 0.5):
        mx = np.round(2 * ax - xs).astype(int)
        ok = (mx >= 0) & (mx < m.shape[1])
        sc = m[ys[ok], mx[ok]].mean()
        if sc > best[0]:
            best = (sc, ax)
    return best[1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('src'); p.add_argument('out')
    p.add_argument('--rect', nargs=4, type=int, required=True)
    p.add_argument('--axis', type=float)
    p.add_argument('--mask')
    p.add_argument('--legs', default='0-48:0.25:1.0')
    p.add_argument('--dark', type=float, default=0.30)
    p.add_argument('--feather', type=int, default=1)
    p.add_argument('--sym', action='store_true', help='also take out the mirror image of the selection (refills cape gaps, but can mirror cape trim)')
    o = p.parse_args()
    ranges = [tuple(map(float, t.split(':')[0].split('-'))) + tuple(map(float, t.split(':')[1:])) for t in o.legs.split(',')]
    im = Image.open(o.src).convert('RGBA'); a = np.array(im)
    m = leg_mask(a, o.rect, ranges, o.dark)
    ax = o.axis if o.axis is not None else best_axis(m, o.rect[0] + 40, o.rect[2] - 40)
    # soft edge so the cut inside the clothing does not leave a hard seam
    # make the selection symmetric about the axis: whatever is taken out on one side is refilled
    # by its mirror image from the other side, so no transparent hole can open in the clothing
    H, W = m.shape
    xs = np.arange(W); src_x = np.round(2 * ax - xs).astype(int); valid = (src_x >= 0) & (src_x < W)
    mm = np.zeros_like(m); mm[:, valid] = m[:, src_x[valid]]
    if o.sym:
        m = m | mm
    w = m.astype(float)   # hard selection: the dilated rim already carries the anti-aliasing
    legs = a.astype(float).copy(); legs[..., 3] *= w
    rest = a.astype(float).copy(); rest[..., 3] *= (1 - w)
    # mirror the legs layer about ax (integer flip around 2*ax)
    ml = np.zeros_like(legs); ml[:, valid] = legs[:, src_x[valid]]
    def over(top, bot):
        ta, ba = top[..., 3:4] / 255, bot[..., 3:4] / 255
        oa = ta + ba * (1 - ta)
        rgb = (top[..., :3] * ta + bot[..., :3] * ba * (1 - ta)) / np.maximum(oa, 1e-6)
        return np.concatenate([rgb, oa * 255], -1)
    out = over(rest, ml)
    Image.fromarray(np.clip(out, 0, 255).round().astype(np.uint8)).save(o.out)
    if o.mask:
        Image.fromarray((m * 255).astype(np.uint8)).save(o.mask)
    print('axis', ax, 'leg px', int(m.sum()))


if __name__ == '__main__':
    main()

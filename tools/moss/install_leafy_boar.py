#!/usr/bin/env python3
"""Leafy Boar art intake: split the delivered 36-frame sheet (rows 8/4/6/4/8/6) and install battle + field frames.
usage: install_leafy_boar.py <sheet.png> [--dry-run]
Battle canvas 480x400 (feet row 390, bbox centred on x=240, idle body 246px tall); field canvas 240x160 (= half scale, feet row 154)."""
import sys, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
ROWS = [8, 4, 6, 4, 8, 6]
def segs(proj, n, lo, hi):
    out = [lo]
    for k in range(1, n):
        c = lo + (hi - lo) * k / n; w = (hi - lo) / n * .3
        a, b = int(c - w), int(c + w); out.append(a + int(np.argmin(proj[a:b])))
    out.append(hi); return out
def split(path):
    im = Image.open(path).convert('RGBA'); a = np.array(im); m = a[..., 3] > 16
    rs = m.sum(1).astype(float); ys = np.where(rs > 2)[0]; y_lo, y_hi = ys.min(), ys.max() + 1
    bands = []; s = y_lo   # rows are separated by the emptiest scanline near each expected boundary (effects may touch neighbours)
    weights = [1.0, .85, .95, .95, 1.0, 1.0]
    for r in range(1, len(ROWS)):
        c = y_lo + (y_hi - y_lo) * sum(weights[:r]) / sum(weights); w = (y_hi - y_lo) / len(ROWS) * .3
        a_, b_ = int(c - w), int(c + w); cut = a_ + int(np.argmin(rs[a_:b_])); bands.append((s, cut)); s = cut
    bands.append((s, y_hi))
    frames = {}
    for r, ((y0, y1), n) in enumerate(zip(bands, ROWS), 1):
        cp = m[y0:y1].sum(0).astype(float); xs = np.where(cp > 2)[0]; cuts = segs(cp, n, xs.min(), xs.max() + 1)
        for c in range(n):
            sub = a[y0:y1, cuts[c]:cuts[c + 1]].copy(); mm = sub[..., 3] > 16
            lab, k = ndi.label(ndi.binary_dilation(mm, iterations=4))
            if k > 1: sizes = ndi.sum(mm, lab, range(1, k + 1)); sub[lab != 1 + int(np.argmax(sizes)), 3] = 0
            img = Image.fromarray(sub); img = img.crop(img.getchannel('A').point(lambda v: 255 if v > 16 else 0).getbbox())
            frames[(r, c + 1)] = img
    return frames
def place(img, k, W, H, feet):
    nw, nh = max(1, round(img.width * k)), max(1, round(img.height * k)); im = img.resize((nw, nh), Image.LANCZOS)
    cv = Image.new('RGBA', (W, H), (0, 0, 0, 0)); x = round(W / 2 - nw / 2); y = feet - nh
    assert x >= 0 and y >= 0 and x + nw <= W, (nw, nh); cv.alpha_composite(im, (x, y)); return cv
def main():
    src = sys.argv[1]; dry = '--dry-run' in sys.argv
    F = split(src); k_b = 246 / F[(1, 1)].height; k_f = k_b / 2
    B = 'img/battle/enemies/leafy_boar/'; M = 'img/field/monsters/leafy_boar/'
    out = {}
    for i in range(4): out[B + 'idle/leafy_boar_idle_%02d.png' % i] = (F[(1, i + 1)], 'b')
    out[B + 'leafy_boar_battle_idle.png'] = (F[(1, 1)], 'b')
    for i in range(4):
        out[B + 'motion/leafy_boar_attack_%02d.png' % (i + 1)] = (F[(4, i + 1)], 'b')
        out[B + 'motion/leafy_boar_damage_%02d.png' % (i + 1)] = (F[(5, i + 1)], 'b')
    out[B + 'leafy_boar_attack.png'] = (F[(4, 4)], 'b'); out[B + 'leafy_boar_damage.png'] = (F[(5, 2)], 'b'); out[B + 'leafy_boar_low_hp.png'] = (F[(5, 7)], 'b')
    for i in range(6): out[B + 'motion/leafy_boar_ko_%02d.png' % (i + 1)] = (F[(6, i + 1)], 'b')
    out[B + 'leafy_boar_ko.png'] = (F[(6, 5)], 'b')
    field = [(1, 1), (1, 2), (1, 3), (1, 4), (2, 4), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6)]
    for i, key in enumerate(field): out[M + 'leafy_boar_%02d.png' % (i + 1)] = (F[key], 'f')
    for p, (img, kind) in out.items():
        im = place(img, k_b, 480, 400, 390) if kind == 'b' else place(img, k_f, 240, 160, 154)
        if not dry: im.save(os.path.join(ROOT, p), optimize=True)
    print('frames', len(F), 'battle scale %.3f' % k_b, 'wrote' if not dry else 'dry', len(out))
main()

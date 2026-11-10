#!/usr/bin/env python3
"""MORWEN-OFFICIAL-4DIR-UPDATE-01 / ART-74H (rev 2): left walk updated to the director-adopted left profile
(2026-11-10, SHA-256 81ef16e1...). 74G frames are copied unchanged and three items are DRAWN on top, per frame, with
colours of the side sprites (gold / leather ramps of 74G / 75) and, for the flower only, two pink tones taken from
the official left profile (new to the sprite); nothing alpha-blended:
  1. book-and-laurel crest on the near (left) shoulder: 7x6 at 96 (laurel ring, cream pages, dark spine), 3x3 at 48;
     follows the chest level of each frame (74G levels.chest_dy)
  2. shoulder strap: brown leather 2 px (dark edge + mid + 1 px highlight) from under the capelet edge down across
     the jacket front to the waist, where it passes behind the body (the bag body stays on the far side, hidden);
     follows chest_dy; drawn only on body pixels
  3. small pink hair flower above the ear (official), 1 px clear of the earring; follows the earring of each frame
74G is not modified.  python3 build_morwen74h.py --out ."""
import argparse, json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(HERE / '..' / '74D'))
from oklab import rgb2oklab, lch
G = HERE / '..' / '74G'
NF = 12
LV = json.loads((G / 'build_meta_74g.json').read_text())['levels']
hx = lambda s: tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))
GOLD_D, GOLD_S, GOLD_M, GOLD_L, CREAM = hx('#8f571c'), hx('#a76b2a'), hx('#e2a355'), hx('#ffd388'), hx('#ffe895')
LEA_D, LEA_M, LEA_L, LEA_H = hx('#572e22'), hx('#724231'), hx('#8a5545'), hx('#9a6656')
PINK, PINK_D = (233, 160, 215), (150, 60, 140)

CREST = ['.ggggg.',
         'gWWdWWg',
         'gWWdWWg',
         's.WdW.s',
         '.s...s.',
         '..sss..']
CREST_C = {'g': GOLD_M, 'W': CREAM, 'd': GOLD_D, 's': GOLD_S}
CREST_AT = (49, 52)                      # top-left of the crest at F00 (96, left coords) - centre of the shoulder
STRAP = [(42, 64), (30, 78)]             # from under the capelet edge to the front of the waist (96, F00)


def draw_crest(im, dy, k):
    if k == 1:
        x0, y0 = CREST_AT[0], CREST_AT[1] + dy
        for r, row in enumerate(CREST):
            for c, ch in enumerate(row):
                if ch != '.' and im[y0 + r, x0 + c, 3]: im[y0 + r, x0 + c, :3] = CREST_C[ch]
    else:
        x0, y0 = (CREST_AT[0] + 2) // 2, (CREST_AT[1] + 1 + dy) // 2
        for (x, y), c in {(x0, y0): GOLD_M, (x0 + 1, y0): GOLD_M, (x0 + 2, y0): GOLD_M, (x0, y0 + 1): GOLD_S, (x0 + 1, y0 + 1): CREAM,
                          (x0 + 2, y0 + 1): GOLD_S, (x0 + 1, y0 + 2): GOLD_S}.items():
            if im[y, x, 3]: im[y, x, :3] = c


def draw_strap(im, dy, k):
    (x0, y0), (x1, y1) = STRAP
    n = max(abs(x1 - x0), abs(y1 - y0))
    pts = sorted({(round((x0 + (x1 - x0) * t / n) / k), round((y0 + dy + (y1 - y0) * t / n) / k)) for t in range(n + 1)})
    for x, y in pts:
        if k == 1:
            for dx, c in ((-1, LEA_D), (0, LEA_M), (1, LEA_L), (2, LEA_D)):
                if im[y, x + dx, 3]: im[y, x + dx, :3] = c
            if (x + y) % 3 == 0 and im[y, x, 3]: im[y, x, :3] = LEA_H
        else:
            for dx, c in ((0, LEA_M), (1, LEA_D)):
                if im[y, x + dx, 3]: im[y, x + dx, :3] = c


def earring(im):
    L, Cc, h = (v.reshape(im.shape[:2]) for v in lch(rgb2oklab(im[:, :, :3].reshape(-1, 3).astype(float))))
    yy, xx = np.mgrid[0:im.shape[0], 0:im.shape[1]]
    m = (im[:, :, 3] > 0) & (Cc > 0.14) & (h > 300) & (h < 350) & (xx >= 42) & (xx <= 56) & (yy >= 40) & (yy <= 52)
    ys, xs = np.where(m); return int(round(xs.mean())), int(ys.min())


def draw_flower(im, ex, ey, k):
    if k == 1:
        fx, fy = ex - 1, ey - 7
        cells = {(fx, fy): GOLD_L, (fx - 1, fy): PINK, (fx + 1, fy): PINK, (fx, fy - 1): PINK, (fx, fy + 1): PINK,
                 (fx - 1, fy - 1): PINK_D, (fx + 1, fy + 1): PINK_D, (fx - 1, fy + 1): PINK_D, (fx + 1, fy - 1): PINK_D}
    else:
        fx, fy = (ex - 1) // 2, (ey - 7) // 2
        cells = {(fx, fy): GOLD_L, (fx - 1, fy): PINK}
    for (x, y), c in cells.items(): im[y, x, :3] = c; im[y, x, 3] = 255
    return [fx, fy]


ap = argparse.ArgumentParser(); ap.add_argument('--out', type=Path, required=True); a = ap.parse_args()
log = {}
for f in range(NF):
    cd = LV['chest_dy'][f]
    e96 = earring(np.array(Image.open(G / f'morwen_left_walk_74G_12f_{f:02d}_96x128.png').convert('RGBA')))
    for s, k in (('96x128', 1), ('48x64', 2)):
        im = np.array(Image.open(G / f'morwen_left_walk_74G_12f_{f:02d}_{s}.png').convert('RGBA'))
        draw_strap(im, cd, k); draw_crest(im, cd, k); fl = draw_flower(im, *e96, k)
        Image.fromarray(im, 'RGBA').save(a.out / f'morwen_left_walk_74H_12f_{f:02d}_{s}.png')
        log[f'{f:02d}_{s}'] = dict(chest_dy=cd, flower=fl, earring96=list(e96))
(a.out / 'build_local_74h.json').write_text(json.dumps(log, indent=1), encoding='utf-8')
print('ok')

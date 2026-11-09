#!/usr/bin/env python3
"""ART-74B sheets / GIF / 74A-vs-74B comparison / backgrounds.
  python3 make_sheets74b.py --art <74B dir> --prev <74A dir> --ground <repo>/img/field/moss/art"""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw
ap = argparse.ArgumentParser()
for k in ('art', 'prev', 'ground'): ap.add_argument('--' + k, type=Path, required=True)
a = ap.parse_args()
fr = lambda d, f, s: Image.open(d / f'morwen_left_walk_{f:02d}_{s}.png').convert('RGBA')
def on(im, bg):
    b = Image.new('RGBA', im.size, bg) if isinstance(bg, tuple) else bg.crop((0, 0) + im.size).convert('RGBA')
    b.alpha_composite(im); return b
def up(im, s): return im.resize((im.width * s, im.height * s), Image.NEAREST)
for s, (w, h) in (('96x128', (96, 128)), ('48x64', (48, 64))):
    sh = Image.new('RGBA', (w * 6, h), (0, 0, 0, 0))
    for f in range(6): sh.alpha_composite(fr(a.art, f, s), (f * w, 0))
    sh.save(a.art / f'morwen_left_walk_sheet_{s}.png')
g = [up(on(fr(a.art, f, '96x128'), (164, 184, 150, 255)), 2).convert('P', palette=Image.ADAPTIVE) for f in range(6)]
g[0].save(a.art / 'morwen_left_walk_74B.gif', save_all=True, append_images=g[1:], duration=120, loop=0, disposal=2)
LIGHT, DARK, MID = (236, 232, 220, 255), (40, 36, 52, 255), (164, 184, 150, 255)
moss = Image.open(a.ground / 'ground_moss.png').convert('RGBA')
# --- COMPARE: rows = 74A / 74B ; 96 at 2x, 48 native + 3x, zoom hat / waist F00 6x
W = 6 * (96 * 2 + 8) + 20
cmp = Image.new('RGBA', (W, 1700), (24, 24, 30, 255)); d = ImageDraw.Draw(cmp); y = 6
for lab, dd in (('ART-74A', a.prev), ('ART-74B', a.art)):
    d.text((8, y), f'{lab}  96x128 x2  F00-F05', fill=(255, 255, 255, 255)); y += 14
    for f in range(6): cmp.alpha_composite(up(on(fr(dd, f, '96x128'), MID), 2), (10 + f * (96 * 2 + 8), y))
    y += 128 * 2 + 8
for lab, dd in (('ART-74A', a.prev), ('ART-74B', a.art)):
    d.text((8, y), f'{lab}  48x64 native (left) / x3 (right)  F00-F05', fill=(255, 255, 255, 255)); y += 14
    for f in range(6): cmp.alpha_composite(on(fr(dd, f, '48x64'), MID), (10 + f * 54, y))
    for f in range(6): cmp.alpha_composite(up(on(fr(dd, f, '48x64'), MID), 3), (10 + 6 * 54 + 10 + f * (48 * 3 + 4), y))
    y += 64 * 3 + 8
d.text((8, y), 'F00 zoom x6: hat back (FIX-01)  74A | 74B        waist / mantle (FIX-02)  74A | 74B', fill=(255, 255, 255, 255)); y += 14
x = 10
for box in ((30, 0, 80, 46), (20, 62, 70, 100)):
    for dd in (a.prev, a.art):
        c = up(on(fr(dd, 0, '96x128').crop(box), MID), 6); cmp.alpha_composite(c, (x, y)); x += c.width + 6
    x += 14
y += 46 * 6 + 10
cmp.crop((0, 0, W, y)).save(a.art / 'COMPARE_ART-74A_vs_ART-74B.png')
# --- BACKGROUNDS: light / dark / moss, 96 x1 + x3 and 48 x1 + x3, F00 & F03
bg = Image.new('RGBA', (3 * (96 * 3 + 96 + 48 * 3 + 48 + 40) + 20, 2 * (128 * 3 + 10) + 10), (24, 24, 30, 255)); x0 = 10
for b in (LIGHT, DARK, moss):
    for r, f in enumerate((0, 3)):
        yy = 10 + r * (128 * 3 + 10); x = x0
        for s, k in (('96x128', 3), ('96x128', 1), ('48x64', 3), ('48x64', 1)):
            im = on(fr(a.art, f, s), b); im = up(im, k); bg.alpha_composite(im, (x, yy)); x += im.width + 8
    x0 = x + 10
bg.save(a.art / 'BACKGROUNDS_ART-74B.png')
print('ok')

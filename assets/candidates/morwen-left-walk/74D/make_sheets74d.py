#!/usr/bin/env python3
"""ART-74D comparison material.
  python3 make_sheets74d.py --art <74D dir> --c74 <74C dir> --ground <repo>/img/field/moss/art --official <official left PNG>"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from oklab import rgb2oklab, lch
from recolor74d import classes
ap = argparse.ArgumentParser()
for k in ('art', 'c74', 'ground', 'official'): ap.add_argument('--' + k, type=Path, required=True)
a = ap.parse_args()
meta = json.loads((a.art / 'build_meta_74d.json').read_text())
GREY, LIGHT, DARK = (200, 200, 200, 255), (236, 232, 220, 255), (40, 36, 52, 255)
moss = Image.open(a.ground / 'ground_moss.png').convert('RGBA')
WHITE = (255, 255, 255, 255)
def fr(d, n, f, s='96x128'): return Image.open(d / f'morwen_left_walk_{n}f_{f:02d}_{s}.png').convert('RGBA')
def on(im, bg):
    b = Image.new('RGBA', im.size, bg) if isinstance(bg, tuple) else bg.crop((0, 0) + im.size).convert('RGBA')
    b.alpha_composite(im); return b
up = lambda im, s: im.resize((im.width * s, im.height * s), Image.NEAREST)
off = Image.open(a.official).convert('RGBA')
def offc(box, h):      # crop of the official sheet, scaled to height h
    c = on(off.crop(box), GREY); return c.resize((max(1, int(c.width * h / c.height)), h), Image.LANCZOS)
def sheet(panels, title, path, pad=10):
    W = sum(p[1].width for p in panels) + pad * (len(panels) + 1); Hh = max(p[1].height for p in panels) + 40
    s = Image.new('RGBA', (W, Hh), (24, 24, 30, 255)); d = ImageDraw.Draw(s); d.text((pad, 4), title, fill=WHITE)
    x = pad
    for lab, im in panels:
        d.text((x, 20), lab, fill=WHITE); s.alpha_composite(im, (x, 34)); x += im.width + pad
    s.save(path)
# 1 official vs 74C vs 74D (F00)
sheet([('official left profile (d858c428)', offc((0, 0, 1024, 1536), 640)), ('ART-74C 8f F00 x5', up(on(fr(a.c74, 8, 0), GREY), 5)),
       ('ART-74D 8f F00 x5', up(on(fr(a.art, 8, 0), GREY), 5))], 'MORWEN-ASSET-74D  official left vs ART-74C vs ART-74D', a.art / 'COMPARE_OFFICIAL_74C_74D.png')
# 2 hat / hair / bow zoom (left coords: head box)
HEAD = (14, 0, 80, 60)
sheet([('official: hat / hair / bow', offc((230, 0, 780, 430), 360)), ('74C x6', up(on(fr(a.c74, 8, 0).crop(HEAD), GREY), 6)),
       ('74D x6', up(on(fr(a.art, 8, 0).crop(HEAD), GREY), 6))], 'FIX-01 hat (deep purple + gold band) / hair (dark violet) / collar bow (purple)', a.art / 'ZOOM_HAT_HAIR_BOW_74C_74D.png')
# 3 skirt / socks / boots zoom, two frames (contact F00, passing F02)
LOW = (14, 74, 74, 128)
pan = [('official: skirt / knee socks / short boots', offc((250, 680, 560, 1480), 480))]
for f in (0, 2):
    pan += [(f'74C F{f:02d} x6', up(on(fr(a.c74, 8, f).crop(LOW), GREY), 6)), (f'74D F{f:02d} x6', up(on(fr(a.art, 8, f).crop(LOW), GREY), 6))]
sheet(pan, 'FIX-02/03 short boots (top at mid-shin) + knee socks (lighter warm mauve) vs leather (darker purple-black)', a.art / 'ZOOM_SKIRT_SOCK_BOOT_74C_74D.png')
# 4 48x64 native + x3, 8 frames, on light / dark / moss
rows = []
for lab, d in (('74C', a.c74), ('74D', a.art)):
    for bg, bn in ((LIGHT, 'light'), (DARK, 'dark'), (moss, 'moss')):
        rows.append((f'{lab} 48x64 native, {bn}', [on(fr(d, 8, f, '48x64'), bg) for f in range(8)]))
W = 8 * 54 + 8 * (144 + 6) + 40; Hh = len(rows) * (192 + 22) + 30
s = Image.new('RGBA', (W, Hh), (24, 24, 30, 255)); dr = ImageDraw.Draw(s); dr.text((10, 4), 'FIX-05.4  48x64 native (left block) and x3 (right block), 8 frames', fill=WHITE)
y = 24
for lab, ims in rows:
    dr.text((10, y), lab, fill=WHITE); y += 14
    for f, im in enumerate(ims):
        s.alpha_composite(im, (10 + f * 54, y)); s.alpha_composite(up(im, 3), (8 * 54 + 30 + f * 150, y))
    y += 192 + 8
s.crop((0, 0, W, y)).save(a.art / 'NATIVE48_74C_vs_74D.png')
# 5 GIFs: 74D 8f / 12f, and 74C vs 74D side by side (same cycle 720 ms)
for n in (8, 12):
    g = [up(on(fr(a.art, n, f), (164, 184, 150, 255)), 2).convert('P', palette=Image.ADAPTIVE) for f in range(n)]
    g[0].save(a.art / f'morwen_left_walk_74D_{n}f.gif', save_all=True, append_images=g[1:], duration=720 // n, loop=0, disposal=2)
g = []
for f in range(8):
    im = Image.new('RGBA', (2 * 200 + 2 * 110, 290), (24, 24, 30, 255)); d = ImageDraw.Draw(im)
    for i, (lab, dd) in enumerate((('ART-74C', a.c74), ('ART-74D', a.art))):
        im.alpha_composite(up(on(fr(dd, 8, f), (164, 184, 150, 255)), 2), (4 + i * 200, 18)); d.text((4 + i * 200, 3), f'{lab} 8f F{f:02d}', fill=WHITE)
        im.alpha_composite(up(on(fr(dd, 8, f, '48x64'), (164, 184, 150, 255)), 1), (404 + i * 110, 18)); d.text((404 + i * 110, 90), f'{lab[-3:]} 48 x1', fill=WHITE)
    g.append(im.convert('P', palette=Image.ADAPTIVE))
g[0].save(a.art / 'COMPARE_74C_vs_74D_8f.gif', save_all=True, append_images=g[1:], duration=90, loop=0, disposal=2)
# 6 palette comparison: per part 5 lightness-quantile swatches of the base cloth (official / 74C / 74D) + leg ramps
offa = np.array(off).astype(float)
OB = {'hat': (520, 20, 700, 120), 'hair': (390, 190, 500, 330), 'bow': (390, 355, 445, 410), 'jacket': (360, 420, 470, 700),
      'skirt': (300, 700, 460, 830), 'mantle': (520, 580, 780, 1330), 'potion': (300, 620, 340, 700), 'sock': (405, 930, 460, 1240), 'boot': (360, 1280, 510, 1460)}
pm = np.array(Image.open(a.art / 'PART_MASKS_74D_right_coords.png').convert('RGBA'))
PC = {'hat': (60, 60, 230), 'hair': (220, 50, 50), 'bow': (40, 200, 60), 'jacket': (240, 160, 30), 'skirt': (230, 40, 230), 'mantle': (40, 220, 220), 'potion': (150, 90, 255)}
def qcols(rgb):
    if len(rgb) == 0: return []
    Lv = rgb2oklab(rgb.astype(float))[:, 0]; o = np.argsort(Lv)
    return [tuple(int(v) for v in rgb[o[min(len(o) - 1, int(q * len(o)))]]) for q in (0.05, 0.25, 0.5, 0.75, 0.95)]
def base(rgb):
    _, _, _, _, g, sk, wh = classes(rgb[None].astype(np.uint8))
    return rgb[~(g | sk | wh)[0]]
ref = {'74C': np.array(Image.open(a.c74 / 'REFERENCE_left_side_edit_right_coords.png').convert('RGBA')),
       '74D': np.array(Image.open(a.art / 'REFERENCE_left_side_74D_colour_right_coords.png').convert('RGBA'))}
SW = 22
rows = []
for k in OB:
    x0, y0, x1, y1 = OB[k]; r = offa[y0:y1, x0:x1]; oc = qcols(base(r[r[:, :, 3] > 250][:, :3].astype(np.uint8)))
    row = [('official', oc)]
    if k in PC:
        for lab in ('74C', '74D'):
            m = np.all(pm[:, :, :3] == PC[k], axis=2) & (ref[lab][:, :, 3] > 0)
            row.append((lab, qcols(base(ref[lab][m][:, :3]))))
    else:
        rk = 'stock' if k == 'sock' else 'boot'
        row.append(('74D ramp', [tuple(c) for c in meta['leg_ramps'][rk]]))
    rows.append((k, row))
gold = [('official hat gold (meas.)', None), ('74D gold3 / leg gold', [tuple(v) for v in meta['gold3'].values()] + [tuple(c) for c in meta['leg_ramps']['gold']])]
s = Image.new('RGBA', (620, 40 + len(rows) * 30 * 3 + 120), (24, 24, 30, 255)); d = ImageDraw.Draw(s)
d.text((10, 6), 'FIX-05.6  main palette: official (base cloth, L quantiles 5/25/50/75/95 %) vs 74C vs 74D', fill=WHITE); y = 28
for k, row in rows:
    for lab, cols in row:
        d.text((10, y + 5), f'{k:7s} {lab}', fill=WHITE)
        for i, c in enumerate(cols): d.rectangle([200 + i * (SW + 4), y, 200 + i * (SW + 4) + SW, y + SW], fill=tuple(c) + (255,))
        y += 26
    y += 6
d.text((10, y + 5), 'gold 74D (gold3 + leg gold)', fill=WHITE)
for i, c in enumerate(gold[1][1]): d.rectangle([200 + i * (SW + 4), y, 200 + i * (SW + 4) + SW, y + SW], fill=tuple(c) + (255,))
s.crop((0, 0, 620, y + 40)).save(a.art / 'PALETTE_OFFICIAL_74C_74D.png')
# sheets
for n in (8, 12):
    for sz, (w, h) in (('96x128', (96, 128)), ('48x64', (48, 64))):
        sh = Image.new('RGBA', (w * n, h), (0, 0, 0, 0))
        for f in range(n): sh.alpha_composite(fr(a.art, n, f, sz), (f * w, 0))
        sh.save(a.art / f'morwen_left_walk_{n}f_sheet_{sz}.png')
print('ok')

#!/usr/bin/env python3
"""MORWEN-MODULAR-SPRITE-02: reference package for the front / back 96x128 HD pixel originals.
  python3 make_brief.py --repo ../../../.. --out .
Writes REF_SHEET_FRONT.png, REF_SHEET_BACK.png, SCALE_96_48.png, PALETTE_RAMPS.png + palette_ramps.json,
DETAIL_CROPS_74G_75.png, TEMPLATE_96x128_guides.png, TEMPLATE_96x128_ghost_74G.png, LANDMARKS.json, PART_LABELS.json."""
import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser(); ap.add_argument('--repo', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
a = ap.parse_args(); R = a.repo.resolve(); O = a.out
import sys; sys.path.insert(0, str(R / 'assets/candidates/morwen-left-walk/74D'))
from oklab import rgb2oklab, lch
C = R / 'assets/candidates'; OFF = R / 'assets/official/characters/morwen/turnaround'
SRC = {'front': C / 'morwen-down-walk/77/reference/morwen_front_candidate_73e99f19.png',
       'back': OFF / 'file_00000000055481f8bac7574e5cab00dc.png',
       'right_official': OFF / 'file_00000000a6308211aaeeb9e2482c2e83.png', 'left_official': OFF / 'file_0000000035a0820989d20c639724cc25.png'}
F00 = {'left 74G F00': C / 'morwen-left-walk/74G/morwen_left_walk_74G_12f_00_{s}.png',
       'right 75 F00': C / 'morwen-right-walk/75/morwen_right_walk_75_12f_00_{s}.png'}
GREY = (190, 190, 190, 255); DARK = (24, 24, 30, 255); WHITE = (255, 255, 255, 255)
# landmark rows / columns on the 96x128 grid (taken from 74G / 75; the front / back originals must use the same frame)
LM = {'grid': [96, 128], 'centre_x': 48, 'ground_row': 124, 'anchor_96': [48, 124], 'anchor_48': [24, 62],
      'hat_top': 2, 'hat_brim_rows': [16, 40], 'hat_brim_width_max': 60, 'face_rows': [22, 50], 'neck_row': 52,
      'shoulder_row': 58, 'waist_row': 78, 'skirt_hem_row': 98, 'cape_hem_rows': [106, 114], 'knee_row': 108,
      'boot_top_row': 111, 'figure_width_max': 72, 'head_to_body': 2.8,
      'notes': 'rows are 96 px rows; 48 px = row // 2. Feet of a standing still touch row 124 (both feet) - no floating.'}
GUIDES = [('hat_top', LM['hat_top'], (255, 200, 0)), ('brim', 16, (255, 120, 0)), ('brim', 40, (255, 120, 0)), ('face', 22, (0, 200, 255)),
          ('face', 50, (0, 200, 255)), ('neck', 52, (0, 255, 120)), ('shoulder', 58, (0, 255, 120)), ('waist', 78, (255, 0, 200)),
          ('skirt hem', 98, (255, 0, 200)), ('cape hem', 106, (200, 120, 255)), ('cape hem', 114, (200, 120, 255)),
          ('knee', 108, (120, 255, 255)), ('ground', 124, (255, 0, 0))]
LABELS = {'Body': (255, 220, 190), 'Hair': (60, 40, 60), 'Inner': (240, 240, 240), 'Outer': (120, 60, 160), 'Bottom': (90, 30, 120),
          'Cape': (160, 90, 210), 'Head': (80, 20, 120), 'HairAccessory': (230, 120, 255), 'Legs': (40, 30, 40),
          'Feet': (110, 70, 110), 'Bag': (140, 90, 60), 'Accessory': (255, 200, 60)}

up = lambda im, k: im.resize((im.width * k, im.height * k), Image.NEAREST)
def on(im, bg=GREY):
    b = Image.new('RGBA', im.size, bg); b.alpha_composite(im.convert('RGBA')); return b
def guide_layer(k=1, labels=True):
    g = Image.new('RGBA', (96 * k, 128 * k), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    for name, y, c in GUIDES:
        d.line([(0, y * k), (96 * k, y * k)], fill=c + (170,), width=1)
        if labels and k > 1: d.text((2, y * k - 10), f'{name} {y}', fill=c + (255,))
    d.line([(48 * k, 0), (48 * k, 128 * k)], fill=(255, 255, 255, 110))
    for x in (48 - 30, 48 + 30): d.line([(x * k, 16 * k), (x * k, 40 * k)], fill=(255, 120, 0, 120))   # brim width 60
    return g

# reference sheets: official painting | 74G F00 x5 + guides | 75 F00 x5 + guides | empty 96 template x5 + guides
for view, key in (('FRONT', 'front'), ('BACK', 'back')):
    o = on(Image.open(SRC[key]).convert('RGBA')); o = o.resize((int(o.width * 640 / o.height), 640), Image.LANCZOS)
    sheet = Image.new('RGBA', (o.width + 3 * 490 + 30, 690), DARK); d = ImageDraw.Draw(sheet)
    sheet.alpha_composite(o, (10, 40)); d.text((10, 8), f'{view} design reference ({"candidate 73e99f19" if key == "front" else "official 9cf2f274"})', fill=WHITE)
    for i, (n, p) in enumerate(list(F00.items()) + [('EMPTY 96x128 template', None)]):
        x = o.width + 20 + i * 490
        base = up(on(Image.open(str(p).format(s='96x128'))), 5) if p else Image.new('RGBA', (480, 640), GREY)
        base.alpha_composite(guide_layer(5)); sheet.alpha_composite(base, (x, 40)); d.text((x, 8), n + ' + landmark rows', fill=WHITE)
    sheet.save(O / f'REF_SHEET_{view}.png')
# 96 vs 48
s = Image.new('RGBA', (2 * (96 * 3 + 48 * 3 + 96 + 48 + 40) + 20, 128 * 3 + 40), DARK); d = ImageDraw.Draw(s); x = 10
for n, p in F00.items():
    i96 = on(Image.open(str(p).format(s='96x128'))); i48 = on(Image.open(str(p).format(s='48x64')))
    d.text((x, 4), n + ': 96 x3 | 48 x6 | 96 x1 | 48 x1', fill=WHITE)
    s.alpha_composite(up(i96, 3), (x, 20)); s.alpha_composite(up(i48, 6), (x + 296, 20))
    s.alpha_composite(i96, (x + 296 + 296, 20)); s.alpha_composite(i48, (x + 296 + 296 + 100, 20)); x += 296 + 296 + 100 + 60 + 40
s.save(O / 'SCALE_96_48.png')
# palette ramps per part (k-means on the side frames, sorted dark -> light)
from sklearn.cluster import KMeans
px = []
for p in sorted((C / 'morwen-left-walk/74G').glob('*_12f_[0-9][0-9]_96x128.png')) + sorted((C / 'morwen-right-walk/75').glob('*_12f_[0-9][0-9]_96x128.png')):
    im = np.array(Image.open(p).convert('RGBA')).reshape(-1, 4); px.append(im[im[:, 3] > 0][:, :3])
px = np.concatenate(px); L, Cc, h = lch(rgb2oklab(px.astype(float)))
groups = {'cloth purple': (h > 285) & (h < 335) & (Cc > 0.06) & (L < 0.62),
          'lavender highlight / lining': (h > 285) & (h < 335) & (Cc > 0.06) & (L >= 0.62),
          'gold embroidery': (h > 45) & (h < 115) & (Cc >= 0.085) & (L > 0.42),
          'skin': (h > 25) & (h < 85) & (Cc > 0.02) & (Cc < 0.12) & (L > 0.72),
          'hair / dark cloth': (L < 0.30) & (Cc < 0.07),
          'leather (bag / boots)': (h > 10) & (h < 80) & (Cc > 0.03) & (Cc < 0.12) & (L > 0.30) & (L <= 0.72),
          'white frill': (L > 0.88) & (Cc < 0.03)}
pal = {}
for g, m in groups.items():
    v = px[m][::3]
    if len(v) < 50: continue
    km = KMeans(min(8, len(np.unique(v, axis=0))), n_init=3, random_state=0).fit(rgb2oklab(v.astype(float)))
    cols = []
    for c in range(km.n_clusters):
        mm = km.labels_ == c; vv = v[mm]; j = np.argmin(((rgb2oklab(vv.astype(float)) - km.cluster_centers_[c]) ** 2).sum(1))
        cols.append((float(km.cluster_centers_[c][0]), tuple(int(t) for t in vv[j]), int(mm.sum())))
    cols.sort()
    pal[g] = [dict(hex='#%02x%02x%02x' % c[1], share=round(c[2] / len(v), 3)) for c in cols]
(O / 'palette_ramps.json').write_text(json.dumps(pal, indent=1), encoding='utf-8')
s = Image.new('RGBA', (8 * 70 + 260, len(pal) * 48 + 20), DARK); d = ImageDraw.Draw(s)
for r, (g, cols) in enumerate(pal.items()):
    y = 10 + r * 48; d.text((10, y + 14), g, fill=WHITE)
    for i, c in enumerate(cols):
        rgb = tuple(int(c['hex'][j:j + 2], 16) for j in (1, 3, 5))
        d.rectangle([250 + i * 70, y, 250 + i * 70 + 60, y + 30], fill=rgb + (255,)); d.text((250 + i * 70, y + 32), c['hex'], fill=WHITE)
s.save(O / 'PALETTE_RAMPS.png')
# detail crops x8 (how the side originals draw gold, hair, face, cloth folds, boots)
crops = [('74G hat brim gold', 'left 74G F00', (14, 10, 46, 34)), ('74G cape fold + hem gold', 'left 74G F00', (50, 84, 86, 112)),
         ('74G face / hair / earring', 'left 74G F00', (18, 22, 50, 54)), ('75 flower + ribbon + crystal', 'right 75 F00', (12, 12, 44, 44)),
         ('75 bag + potions', 'right 75 F00', (30, 70, 62, 98)), ('74G boots / knee socks', 'left 74G F00', (20, 100, 52, 126))]
s = Image.new('RGBA', (3 * (32 * 8 + 20) + 10, 2 * (32 * 8 + 30) + 10), DARK); d = ImageDraw.Draw(s)
for i, (n, src, bx) in enumerate(crops):
    im = on(Image.open(str(F00[src]).format(s='96x128'))).crop(bx)
    x = 10 + (i % 3) * (32 * 8 + 20); y = 10 + (i // 3) * (32 * 8 + 30)
    s.alpha_composite(up(im, 8), (x, y + 16)); d.text((x, y), n, fill=WHITE)
s.save(O / 'DETAIL_CROPS_74G_75.png')
# templates for the artist: guide layer (transparent) and a 25 % ghost of 74G F00
guide_layer(1, False).save(O / 'TEMPLATE_96x128_guides.png')
g = np.array(Image.open(str(F00['left 74G F00']).format(s='96x128')).convert('RGBA')); g[:, :, 3] = (g[:, :, 3] * 0.25).astype(np.uint8)
Image.fromarray(g).save(O / 'TEMPLATE_96x128_ghost_74G.png')
(O / 'LANDMARKS.json').write_text(json.dumps(LM, indent=1), encoding='utf-8')
(O / 'PART_LABELS.json').write_text(json.dumps({'format': 'RGB label map, same size as the original, one exact colour per slot, '
    'alpha 0 where the original is transparent', 'slots': {k: '#%02x%02x%02x' % v for k, v in LABELS.items()}}, indent=1), encoding='utf-8')
print('ok', list(pal))

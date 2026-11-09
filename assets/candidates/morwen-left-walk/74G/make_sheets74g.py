#!/usr/bin/env python3
"""ART-74G comparison material.
  python3 make_sheets74g.py --art <74G dir> --f74 <74F dir> --repo <repo root> --official <official left PNG>"""
import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ap = argparse.ArgumentParser()
for k in ('art', 'f74', 'repo', 'official'): ap.add_argument('--' + k, type=Path, required=True)
a = ap.parse_args()
WHITE = (255, 255, 255, 255); GREY = (200, 200, 200, 255); MID = (164, 184, 150, 255)
NF = 12; CYCLE_MS = 840; SPEED = 41.6 / NF
VER = {'74F-C': lambda f, s: a.f74 / f'morwen_left_walk_74FC_12f_{f:02d}_{s}.png',
       '74G': lambda f, s: a.art / f'morwen_left_walk_74G_12f_{f:02d}_{s}.png'}
fr = lambda v, f, s='96x128': Image.open(VER[v](f, s)).convert('RGBA')
def on(im, bg):
    b = Image.new('RGBA', im.size, bg) if isinstance(bg, tuple) else bg.crop((0, 0) + im.size).convert('RGBA')
    b.alpha_composite(im); return b
up = lambda im, s: im.resize((im.width * s, im.height * s), Image.NEAREST)
def tex(p, mul=1.0, tint=(0, 0, 0)):
    im = Image.open(p).convert('RGB').resize((400, 400), Image.LANCZOS)
    return Image.fromarray(np.clip(np.array(im).astype(float) * mul + np.array(tint), 0, 255).astype(np.uint8)).convert('RGBA')
art = a.repo / 'img' / 'field'
BG = {'moss forest (ground_moss)': tex(art / 'moss' / 'art' / 'ground_moss.png'), 'meadow (lind_grass)': tex(art / 'lind' / 'terrain' / 'lind_grass.png'),
      'dark cave (lind_stone x0.28, simulated)': tex(art / 'lind' / 'terrain' / 'lind_stone.png', 0.28),
      'night field (lind_grass x0.22 + blue, simulated)': tex(art / 'lind' / 'terrain' / 'lind_grass.png', 0.22, (4, 8, 26))}
moss = BG['moss forest (ground_moss)']
for s, (w, h) in (('96x128', (96, 128)), ('48x64', (48, 64))):
    sh = Image.new('RGBA', (w * NF, h), (0, 0, 0, 0))
    for f in range(NF): sh.alpha_composite(fr('74G', f, s), (f * w, 0))
    sh.save(a.art / f'morwen_left_walk_74G_12f_sheet_{s}.png')
for s, k, name in (('96x128', 2, 'morwen_left_walk_74G_12f.gif'), ('48x64', 1, 'morwen_left_walk_74G_12f_48native.gif'), ('48x64', 3, 'morwen_left_walk_74G_12f_48x3.gif')):
    g = [up(on(fr('74G', f, s), MID), k).convert('P', palette=Image.ADAPTIVE) for f in range(NF)]
    g[0].save(a.art / name, save_all=True, append_images=g[1:], duration=CYCLE_MS // NF, loop=0, disposal=2)
def synced(s, k, name):
    w, h = (96, 128) if s == '96x128' else (48, 64)
    frames = []
    for f in range(NF):
        im = Image.new('RGBA', (2 * (w * k + 8) + 8, h * k + 40), (24, 24, 30, 255)); d = ImageDraw.Draw(im)
        for i, v in enumerate(VER):
            x0 = 8 + i * (w * k + 8); im.alpha_composite(up(on(fr(v, f, s), moss), k), (x0, 16))
            d.text((x0, 2), f'{v} F{f:02d}', fill=WHITE)
        d.text((8, h * k + 22), f'{s} x{k}  same cycle 840 ms', fill=WHITE)
        frames.append(im.convert('P', palette=Image.ADAPTIVE))
    frames[0].save(a.art / name, save_all=True, append_images=frames[1:], duration=CYCLE_MS // NF, loop=0, disposal=2)
synced('96x128', 2, 'COMPARE_74FC_vs_74G_96x2.gif'); synced('48x64', 3, 'COMPARE_74FC_vs_74G_48x3.gif'); synced('48x64', 1, 'COMPARE_74FC_vs_74G_48native.gif')
# backgrounds: 4 grounds x F00 / F03 / F06 / F09 (96 x2 + 48 x1 + 48 x3)
s = Image.new('RGBA', (4 * (192 + 8 + 48 + 8 + 144 + 16) + 10, len(BG) * (256 + 30) + 10), (24, 24, 30, 255)); d = ImageDraw.Draw(s); y = 6
for name, bg in BG.items():
    d.text((10, y), f'74G  {name}', fill=WHITE); x = 10
    for f in (0, 3, 6, 9):
        s.alpha_composite(up(on(fr('74G', f), bg), 2), (x, y + 14)); s.alpha_composite(on(fr('74G', f, '48x64'), bg), (x + 200, y + 14))
        s.alpha_composite(up(on(fr('74G', f, '48x64'), bg), 3), (x + 256, y + 14)); x += 192 + 8 + 48 + 8 + 144 + 16
    y += 256 + 30
s.save(a.art / 'BACKGROUNDS_74G.png')
# clean-up evidence: F00..F11 isolated pixels removed (red) at 96 x3
q = json.loads((a.art / 'QA_REPORT_74G.json').read_text()) if (a.art / 'QA_REPORT_74G.json').exists() else None
s = Image.new('RGBA', (6 * (96 * 3 + 8) + 8, 2 * (128 * 3 + 24) + 8), (24, 24, 30, 255)); d = ImageDraw.Draw(s)
for i, f in enumerate((0, 2, 4, 6, 8, 10)):
    for r, v in enumerate(VER):
        im = fr(v, f); x0 = 8 + i * (96 * 3 + 8); y0 = 8 + r * (128 * 3 + 24)
        s.alpha_composite(up(on(im, GREY), 3), (x0, y0 + 16)); d.text((x0, y0), f'{v} F{f:02d}', fill=WHITE)
s.save(a.art / 'COMPARE_74FC_vs_74G_x3.png')
# official vs 74F-C vs 74G
off = Image.open(a.official).convert('RGBA'); ob = on(off, GREY); ob = ob.resize((int(off.width * 640 / off.height), 640), Image.LANCZOS)
s = Image.new('RGBA', (ob.width + 2 * 490 + 20, 680), (24, 24, 30, 255)); d = ImageDraw.Draw(s)
s.alpha_composite(ob, (10, 30)); d.text((10, 8), 'official left profile (d858c428)', fill=WHITE)
for i, v in enumerate(VER):
    x = ob.width + 20 + i * 490; s.alpha_composite(up(on(fr(v, 3), GREY), 5), (x, 30)); d.text((x, 8), f'{v} F03 x5', fill=WHITE)
s.save(a.art / 'COMPARE_OFFICIAL_74FC_74G.png')
print('ok')

#!/usr/bin/env python3
"""ART-74E comparison material.
  python3 make_sheets74e.py --art <74E dir> --d74 <74D dir> --repo <repo root> --official <official left PNG>"""
import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ap = argparse.ArgumentParser()
for k in ('art', 'd74', 'repo', 'official'): ap.add_argument('--' + k, type=Path, required=True)
a = ap.parse_args()
WHITE = (255, 255, 255, 255); GREY = (200, 200, 200, 255); MID = (164, 184, 150, 255)
CYCLE_MS = 840          # recommended game cycle (video cycle is slow motion; see README)
meta = json.loads((a.art / 'build_meta_74e.json').read_text()); d_meta_speed = 34.0
SPEED = {'74D': d_meta_speed / 8, '8f': meta['motion_8f']['ground_speed_px_per_frame']['96x128'], '12f': meta['motion_12f']['ground_speed_px_per_frame']['96x128']}
def fr(tag, f, s='96x128'):
    p = a.d74 / f'morwen_left_walk_8f_{f:02d}_{s}.png' if tag == '74D' else a.art / f'morwen_left_walk_{tag}_{f:02d}_{s}.png'
    return Image.open(p).convert('RGBA')
NUM = {'74D': 8, '8f': 8, '12f': 12}
def on(im, bg):
    b = Image.new('RGBA', im.size, bg) if isinstance(bg, tuple) else bg.crop((0, 0) + im.size).convert('RGBA')
    b.alpha_composite(im); return b
up = lambda im, s: im.resize((im.width * s, im.height * s), Image.NEAREST)
# backgrounds: meadow / moss forest from the repository, cave / night are darkened versions (simulated)
def tex(p, mul=1.0, tint=(0, 0, 0)):
    im = Image.open(p).convert('RGB').resize((400, 400), Image.LANCZOS)
    x = np.clip(np.array(im).astype(float) * mul + np.array(tint), 0, 255).astype(np.uint8)
    return Image.fromarray(x).convert('RGBA')
art = a.repo / 'img' / 'field'
BG = {'meadow (lind_grass)': tex(art / 'lind' / 'terrain' / 'lind_grass.png'),
      'moss forest (ground_moss)': tex(art / 'moss' / 'art' / 'ground_moss.png'),
      'dark cave (lind_stone x0.28, simulated)': tex(art / 'lind' / 'terrain' / 'lind_stone.png', 0.28),
      'night field (lind_grass x0.22 + blue, simulated)': tex(art / 'lind' / 'terrain' / 'lind_grass.png', 0.22, (4, 8, 26))}
# sheets + GIFs
for n in (8, 12):
    tag = f'{n}f'
    for s, (w, h) in (('96x128', (96, 128)), ('48x64', (48, 64))):
        sh = Image.new('RGBA', (w * n, h), (0, 0, 0, 0))
        for f in range(n): sh.alpha_composite(fr(tag, f, s), (f * w, 0))
        sh.save(a.art / f'morwen_left_walk_{n}f_sheet_{s}.png')
    g = [up(on(fr(tag, f), MID), 2).convert('P', palette=Image.ADAPTIVE) for f in range(n)]
    g[0].save(a.art / f'morwen_left_walk_74E_{n}f.gif', save_all=True, append_images=g[1:], duration=CYCLE_MS // n, loop=0, disposal=2)
def synced(cols, path, label):
    frames = []
    for tick in range(24):
        im = Image.new('RGBA', (len(cols) * 200, 292), (24, 24, 30, 255)); d = ImageDraw.Draw(im)
        for i, (tag, lab) in enumerate(cols):
            n = NUM[tag]; f = tick * n // 24; x0 = i * 200 + 4
            d.rectangle([x0, 18, x0 + 192, 18 + 256], fill=MID)
            off = (SPEED[tag] * (tick * n / 24)) % 16
            for k in range(-2, 14):
                xx = x0 + int(round((k * 16 + off) * 2))
                if x0 <= xx <= x0 + 192: d.line([xx, 18 + 249, xx, 18 + 255], fill=(60, 70, 50, 255), width=2)
            im.alpha_composite(up(fr(tag, f), 2), (x0, 18)); d.text((x0, 3), f'{lab} F{f:02d}', fill=WHITE)
        d.text((4, 278), label, fill=WHITE)
        frames.append(im.convert('P', palette=Image.ADAPTIVE))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=CYCLE_MS // 24, loop=0, disposal=2)
synced([('74D', 'ART-74D 8f'), ('8f', 'ART-74E 8f')], a.art / 'COMPARE_74D_vs_74E_8f_synced.gif', 'same cycle; ground marks move at each version\'s speed')
synced([('8f', 'ART-74E 8f'), ('12f', 'ART-74E 12f')], a.art / 'COMPARE_74E_8f_vs_12f_synced.gif', 'same cycle, same speed')
# official vs 74D vs 74E
off = Image.open(a.official).convert('RGBA'); ob = on(off, GREY); ob = ob.resize((int(off.width * 640 / off.height), 640), Image.LANCZOS)
s = Image.new('RGBA', (ob.width + 2 * 480 + 40, 680), (24, 24, 30, 255)); d = ImageDraw.Draw(s)
s.alpha_composite(ob, (10, 30)); d.text((10, 8), 'official left profile (d858c428)', fill=WHITE)
for i, (tag, f, lab) in enumerate((('74D', 0, 'ART-74D 8f F00 x5'), ('8f', 0, 'ART-74E 8f F00 x5 (heel strike)'))):
    x = ob.width + 20 + i * 490; s.alpha_composite(up(on(fr(tag, f), GREY), 5), (x, 30)); d.text((x, 8), lab, fill=WHITE)
s.save(a.art / 'COMPARE_OFFICIAL_74D_74E.png')
# backgrounds
rows = list(BG.items())
cw = 96 * 2 + 10 + 48 * 3 + 10 + 48 + 20
s = Image.new('RGBA', (2 * 2 * cw + 30, len(rows) * (256 + 30) + 20), (24, 24, 30, 255)); d = ImageDraw.Draw(s)
y = 10
for name, bg in rows:
    d.text((10, y), name, fill=WHITE); x = 10
    for tag, f in (('74D', 0), ('74D', 4), ('8f', 0), ('8f', 4)):
        im = up(on(fr(tag, f), bg), 2); s.alpha_composite(im, (x, y + 14))
        im3 = up(on(fr(tag, f, '48x64'), bg), 3); s.alpha_composite(im3, (x + 202, y + 14))
        s.alpha_composite(on(fr(tag, f, '48x64'), bg), (x + 202 + 154, y + 14))
        d.text((x, y + 14 + 258), f'{"74D" if tag == "74D" else "74E"} F{f:02d}', fill=WHITE)
        x += cw
    y += 256 + 30
s.save(a.art / 'BACKGROUNDS_74D_vs_74E.png')
# 48 native
s = Image.new('RGBA', (12 * 54 + 20, 3 * (64 + 22) + 10), (24, 24, 30, 255)); d = ImageDraw.Draw(s); y = 6
for tag, lab in (('74D', '74D 8f'), ('8f', '74E 8f'), ('12f', '74E 12f')):
    d.text((10, y), f'{lab} 48x64 native (moss)', fill=WHITE); y += 14
    for f in range(NUM[tag]): s.alpha_composite(on(fr(tag, f, '48x64'), BG['moss forest (ground_moss)']), (10 + f * 54, y))
    y += 64 + 8
s.save(a.art / 'NATIVE48_74D_vs_74E.png')
print('ok')

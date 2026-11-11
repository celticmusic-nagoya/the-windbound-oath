#!/usr/bin/env python3
"""ART-74F comparison material.
  python3 make_sheets74f.py --art <74F dir> --e74 <74E dir> --repo <repo root> --official <official left PNG>"""
import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ap = argparse.ArgumentParser()
for k in ('art', 'e74', 'repo', 'official'): ap.add_argument('--' + k, type=Path, required=True)
a = ap.parse_args()
WHITE = (255, 255, 255, 255); GREY = (200, 200, 200, 255); MID = (164, 184, 150, 255)
NF = 12; CYCLE_MS = 840; SPEED = 41.6 / NF
meta = json.loads((a.art / 'build_meta_74f.json').read_text())
VER = {'74E': lambda f, s: a.e74 / f'morwen_left_walk_12f_{f:02d}_{s}.png',
       '74F-B': lambda f, s: a.art / f'morwen_left_walk_74FB_12f_{f:02d}_{s}.png',
       '74F-C': lambda f, s: a.art / f'morwen_left_walk_74FC_12f_{f:02d}_{s}.png'}
fr = lambda v, f, s='96x128': Image.open(VER[v](f, s)).convert('RGBA')
def on(im, bg):
    b = Image.new('RGBA', im.size, bg) if isinstance(bg, tuple) else bg.crop((0, 0) + im.size).convert('RGBA')
    b.alpha_composite(im); return b
up = lambda im, s: im.resize((im.width * s, im.height * s), Image.NEAREST)
def tex(p, mul=1.0, tint=(0, 0, 0)):
    im = Image.open(p).convert('RGB').resize((400, 400), Image.LANCZOS)
    return Image.fromarray(np.clip(np.array(im).astype(float) * mul + np.array(tint), 0, 255).astype(np.uint8)).convert('RGBA')
art = a.repo / 'img' / 'field'
moss = tex(art / 'moss' / 'art' / 'ground_moss.png')
BG = {'meadow': tex(art / 'lind' / 'terrain' / 'lind_grass.png'), 'moss forest': moss,
      'dark cave (sim.)': tex(art / 'lind' / 'terrain' / 'lind_stone.png', 0.28), 'night field (sim.)': tex(art / 'lind' / 'terrain' / 'lind_grass.png', 0.22, (4, 8, 26))}
# sheets + single GIFs
for v, tag in (('74F-B', '74FB'), ('74F-C', '74FC')):
    for s, (w, h) in (('96x128', (96, 128)), ('48x64', (48, 64))):
        sh = Image.new('RGBA', (w * NF, h), (0, 0, 0, 0))
        for f in range(NF): sh.alpha_composite(fr(v, f, s), (f * w, 0))
        sh.save(a.art / f'morwen_left_walk_{tag}_12f_sheet_{s}.png')
    g = [up(on(fr(v, f), MID), 2).convert('P', palette=Image.ADAPTIVE) for f in range(NF)]
    g[0].save(a.art / f'morwen_left_walk_{tag}_12f.gif', save_all=True, append_images=g[1:], duration=CYCLE_MS // NF, loop=0, disposal=2)
# synced 96 (x2) with ground ruler
frames = []
for f in range(NF):
    im = Image.new('RGBA', (3 * 200, 292), (24, 24, 30, 255)); d = ImageDraw.Draw(im)
    for i, v in enumerate(VER):
        x0 = i * 200 + 4; d.rectangle([x0, 18, x0 + 192, 18 + 256], fill=MID)
        off = (SPEED * f) % 16
        for k in range(-2, 14):
            xx = x0 + int(round((k * 16 + off) * 2))
            if x0 <= xx <= x0 + 192: d.line([xx, 18 + 249, xx, 18 + 255], fill=(60, 70, 50, 255), width=2)
        im.alpha_composite(up(fr(v, f), 2), (x0, 18)); d.text((x0, 3), f'{v} F{f:02d}', fill=WHITE)
    d.text((4, 278), 'same cycle 840 ms, same speed 41.6 px/cycle (96 px)', fill=WHITE)
    frames.append(im.convert('P', palette=Image.ADAPTIVE))
frames[0].save(a.art / 'COMPARE_74E_74FB_74FC_synced.gif', save_all=True, append_images=frames[1:], duration=CYCLE_MS // NF, loop=0, disposal=2)
# 48 native GIFs (x1 and x3), moss
for scale, name in ((1, 'NATIVE48_74E_74FB_74FC_x1.gif'), (3, 'NATIVE48_74E_74FB_74FC_x3.gif')):
    frames = []
    for f in range(NF):
        im = Image.new('RGBA', (3 * (48 * scale + 8) + 8, 64 * scale + 22), (24, 24, 30, 255)); d = ImageDraw.Draw(im)
        for i, v in enumerate(VER):
            im.alpha_composite(up(on(fr(v, f, '48x64'), moss), scale), (8 + i * (48 * scale + 8), 16))
            d.text((8 + i * (48 * scale + 8), 2), v if scale > 1 else v[-1], fill=WHITE)
        frames.append(im.convert('P', palette=Image.ADAPTIVE))
    frames[0].save(a.art / name, save_all=True, append_images=frames[1:], duration=CYCLE_MS // NF, loop=0, disposal=2)
# official vs 74E vs 74F-C
off = Image.open(a.official).convert('RGBA'); ob = on(off, GREY); ob = ob.resize((int(off.width * 640 / off.height), 640), Image.LANCZOS)
s = Image.new('RGBA', (ob.width + 3 * 490 + 20, 680), (24, 24, 30, 255)); d = ImageDraw.Draw(s)
s.alpha_composite(ob, (10, 30)); d.text((10, 8), 'official left profile (d858c428)', fill=WHITE)
for i, (v, f) in enumerate((('74E', 3), ('74F-B', 3), ('74F-C', 3))):
    x = ob.width + 20 + i * 490; s.alpha_composite(up(on(fr(v, f), GREY), 5), (x, 30)); d.text((x, 8), f'{v} F03 (mid-stance) x5', fill=WHITE)
s.save(a.art / 'COMPARE_OFFICIAL_74E_74FB_74FC.png')
# backgrounds (74F-C, F00 / F03 / F06 / F09)
s = Image.new('RGBA', (4 * (192 + 8 + 48 + 16) + 20, len(BG) * (256 + 30) + 10), (24, 24, 30, 255)); d = ImageDraw.Draw(s); y = 6
for name, bg in BG.items():
    d.text((10, y), f'74F-C  {name}', fill=WHITE); x = 10
    for f in (0, 3, 6, 9):
        s.alpha_composite(up(on(fr('74F-C', f), bg), 2), (x, y + 14)); s.alpha_composite(on(fr('74F-C', f, '48x64'), bg), (x + 200, y + 14)); x += 192 + 8 + 48 + 16
    y += 256 + 30
s.save(a.art / 'BACKGROUNDS_74FC.png')
# frame design table (74F-C) + phase chart
C = meta['C']['frames']; Bm = meta['B']['frames']
W = NF * 110 + 180
s = Image.new('RGBA', (W, 260 + 26 * 15), (24, 24, 30, 255)); d = ImageDraw.Draw(s)
d.text((10, 6), 'ART-74F-C frame design (12f). +1 = 1 px down (screen). B = same levels / pelvis dx / capelet; C adds hand, collar, hair, mantle, skirt phases and the F08 toe push', fill=WHITE)
for f in range(NF):
    s.alpha_composite(on(fr('74F-C', f), GREY).crop((10, 0, 90, 128)).resize((80, 128), Image.NEAREST), (180 + f * 110, 24)); d.text((180 + f * 110, 154), f'F{f:02d}', fill=WHITE)
rows = [('t', lambda c: f"{c['t']:.3f}"), ('near leg', lambda c: c['near_role'][:16]), ('far leg', lambda c: c['far_role'][:16]),
        ('near lift / pitch', lambda c: f"{c['near']['lift']} / {c['near']['pitch']:.0f}"), ('pelvis dy', lambda c: f"{c['pelvis_dy']:+d}"),
        ('chest dy', lambda c: f"{c['chest_dy']:+d}"), ('head dy', lambda c: f"{c['head_dy']:+d}"), ('pelvis dx', lambda c: f"{c['pelvis_dx']:+d}"),
        ('arm dx', lambda c: f"{c['secondary']['arm']['dx']:+d}"), ('hand dx (C)', lambda c: f"{c['secondary']['hand']['dx']:+d}"),
        ('capelet dx', lambda c: f"{c['secondary']['cape_front']['dx']:+d}"), ('collar dy', lambda c: f"{c['secondary']['collar_ribbon']['dy']:+d}"),
        ('hair dy', lambda c: f"{c['secondary']['hair_tips']['dy']:+d}"), ('mantle dx/dy', lambda c: f"{c['secondary']['mantle']['dx']:+d}/{c['secondary']['mantle']['dy']:+d}"),
        ('skirt hem', lambda c: f"{c['skirt_sway']:+d}")]
y = 172
for lab, fnc in rows:
    d.text((10, y), lab, fill=WHITE)
    for f in range(NF): d.text((180 + f * 110, y), fnc(C[f]), fill=WHITE)
    y += 26
s.save(a.art / 'FRAME_DESIGN_TABLE_74F.png')
print('ok')

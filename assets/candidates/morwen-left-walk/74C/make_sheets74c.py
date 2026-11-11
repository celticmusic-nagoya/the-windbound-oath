#!/usr/bin/env python3
"""ART-74C sheets / GIFs / comparisons.
  python3 make_sheets74c.py --art <74C dir> --b74 <74B dir> --ground <repo>/img/field/moss/art --official <left profile PNG>"""
import argparse, json
from pathlib import Path
from PIL import Image, ImageDraw
ap = argparse.ArgumentParser()
for k in ('art', 'b74', 'ground', 'official'): ap.add_argument('--' + k, type=Path, required=True)
a = ap.parse_args()
VAR = {'6f': 6, '8f': 8, '12f': 12}
meta = json.loads((a.art / 'build_meta_74c.json').read_text())
SPEED = {'74B': 6.0, '6f': 6.0, '8f': meta['motion_8f']['ground_speed_px_per_frame']['96x128'],
         '12f': meta['motion_12f']['ground_speed_px_per_frame']['96x128']}
def fr(tag, f, s='96x128'):
    p = a.b74 / f'morwen_left_walk_{f:02d}_{s}.png' if tag == '74B' else a.art / f'morwen_left_walk_{tag}_{f:02d}_{s}.png'
    return Image.open(p).convert('RGBA')
NUM = {'74B': 6, **VAR}
def on(im, bg):
    b = Image.new('RGBA', im.size, bg) if isinstance(bg, tuple) else bg.crop((0, 0) + im.size).convert('RGBA')
    b.alpha_composite(im); return b
up = lambda im, s: im.resize((im.width * s, im.height * s), Image.NEAREST)
LIGHT, DARK, MID = (236, 232, 220, 255), (40, 36, 52, 255), (164, 184, 150, 255)
moss = Image.open(a.ground / 'ground_moss.png').convert('RGBA')
# sheets + single GIFs (same cycle time 720 ms for every variant)
for tag, n in VAR.items():
    for s, (w, h) in (('96x128', (96, 128)), ('48x64', (48, 64))):
        sh = Image.new('RGBA', (w * n, h), (0, 0, 0, 0))
        for f in range(n): sh.alpha_composite(fr(tag, f, s), (f * w, 0))
        sh.save(a.art / f'morwen_left_walk_{tag}_sheet_{s}.png')
    g = [up(on(fr(tag, f), MID), 2).convert('P', palette=Image.ADAPTIVE) for f in range(n)]
    g[0].save(a.art / f'morwen_left_walk_74C_{tag}.gif', save_all=True, append_images=g[1:], duration=720 // n, loop=0, disposal=2)
# synced comparison GIF with a moving ground ruler (shows foot slide): 24 ticks per cycle, 30 ms -> 720 ms cycle
cols = ['74B', '8f', '12f']
lab = {'74B': '74B 6f', '8f': '74C 8f', '12f': '74C 12f'}
frames = []
for tick in range(24):
    im = Image.new('RGBA', (len(cols) * 200, 290), (24, 24, 30, 255)); d = ImageDraw.Draw(im)
    for i, tag in enumerate(cols):
        n = NUM[tag]; f = tick * n // 24
        x0 = i * 200 + 4
        d.rectangle([x0, 18, x0 + 192, 18 + 256], fill=MID)
        # ground ruler: world moves right (character walks left), marks every 16 px (96 scale) -> x2
        off = (SPEED[tag] * (tick * n / 24)) % 16
        for k in range(-2, 14):
            xx = x0 + int(round((k * 16 + off) * 2))
            if x0 <= xx <= x0 + 192: d.line([xx, 18 + 249, xx, 18 + 255], fill=(60, 70, 50, 255), width=2)
        im.alpha_composite(up(fr(tag, f), 2), (x0, 18))
        d.text((x0, 3), f'{lab[tag]}  F{f:02d}', fill=(255, 255, 255, 255))
    frames.append(im.convert('P', palette=Image.ADAPTIVE))
frames[0].save(a.art / 'COMPARE_74B6f_74C8f_74C12f_synced.gif', save_all=True, append_images=frames[1:], duration=30, loop=0, disposal=2)
# static comparison sheet: 74B 6f / 74C 8f / 74C 12f, 96 x2, then 48 native + x3
W = 12 * (96 + 6) + 20
cmp = Image.new('RGBA', (W, 2000), (24, 24, 30, 255)); d = ImageDraw.Draw(cmp); y = 6
for tag in ('74B', '6f', '8f', '12f'):
    n = NUM[tag]; name = {'74B': 'ART-74B 6f (base)', '6f': 'ART-74C 6f (74B motion + 74C design only)', '8f': 'ART-74C 8f', '12f': 'ART-74C 12f'}[tag]
    d.text((8, y), f'{name}  96x128 x1  (same cycle; columns aligned to cycle phase)', fill=(255, 255, 255, 255)); y += 14
    for f in range(n):
        x = 10 + int(f * 12 / n) * (96 + 6)
        cmp.alpha_composite(on(fr(tag, f), MID), (x, y))
    y += 128 + 8
for tag in ('74B', '8f', '12f'):
    n = NUM[tag]
    d.text((8, y), f'{lab[tag]}  48x64 native (top) / x3', fill=(255, 255, 255, 255)); y += 14
    for f in range(n): cmp.alpha_composite(on(fr(tag, f, '48x64'), MID), (10 + int(f * 12 / n) * 54, y))
    y += 70
    for f in range(min(n, 8)): cmp.alpha_composite(up(on(fr(tag, f, '48x64'), MID), 3), (10 + f * (144 + 6), y))
    y += 192 + 8
cmp.crop((0, 0, W, y)).save(a.art / 'COMPARE_74B_6f_vs_74C_8f_12f.png')
# backgrounds: light / dark / moss, 8f F00 & F04, 96 x1/x3 + 48 x1/x3
bgim = Image.new('RGBA', (3 * (96 * 3 + 96 + 48 * 3 + 48 + 40) + 20, 2 * (128 * 3 + 10) + 10), (24, 24, 30, 255)); x0 = 10
for b in (LIGHT, DARK, moss):
    for r, f in enumerate((0, 4)):
        yy = 10 + r * (128 * 3 + 10); x = x0
        for s, k in (('96x128', 3), ('96x128', 1), ('48x64', 3), ('48x64', 1)):
            im = up(on(fr('8f', f, s), b), k); bgim.alpha_composite(im, (x, yy)); x += im.width + 8
    x0 = x + 10
bgim.save(a.art / 'BACKGROUNDS_74C_8f.png')
# official left profile vs 74C (design check sheet)
off = Image.open(a.official).convert('RGBA'); ob = on(off, (200, 200, 200, 255))
oh = 128 * 5; ob = ob.resize((int(off.width * oh / off.height), oh), Image.LANCZOS)
sheet = Image.new('RGBA', (ob.width + 96 * 5 * 2 + 40, oh + 24), (24, 24, 30, 255)); d = ImageDraw.Draw(sheet)
sheet.alpha_composite(ob, (10, 20)); d.text((10, 4), 'official left profile (turnaround, SHA d858c428)', fill=(255, 255, 255, 255))
sheet.alpha_composite(up(on(fr('74B', 0), (200, 200, 200, 255)), 5), (ob.width + 20, 20)); d.text((ob.width + 20, 4), 'ART-74B F00', fill=(255, 255, 255, 255))
sheet.alpha_composite(up(on(fr('8f', 0), (200, 200, 200, 255)), 5), (ob.width + 30 + 480, 20)); d.text((ob.width + 30 + 480, 4), 'ART-74C 8f F00 (jewel + strap removed)', fill=(255, 255, 255, 255))
sheet.save(a.art / 'OFFICIAL_LEFT_vs_74B_74C.png')
print('ok')

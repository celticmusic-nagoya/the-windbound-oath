#!/usr/bin/env python3
"""DIRECTIVE-ART-07C: Aidan side-walk cadence study (offline, deterministic; the adopted frames are used unmodified).
The runtime picks the side frame by walked distance: phase = floor(dist / (STRIDE_CYCLE/4)) % 4 (js/field/moss-forest-runtime.js).
Renders the camera-centred hero over ground ticks for STRIDE_CYCLE = 90 (current) and 52 (matched to the painted stride).
Output: docs/art/qa/art-07b/aidan_side_cadence_compare.gif"""
import pathlib
from PIL import Image, ImageDraw, ImageFont

R = pathlib.Path(__file__).resolve().parents[2]; OUT = R / 'docs/art/qa/art-07b'
F = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 15)
K = 3                       # world px -> screen px
SCALE = 0.0625 * K          # source px -> screen px (runtime scale 0.0625)
ANCHOR = (1024, 1230)
FR = {}
for i in range(1, 5):
    im = Image.open(R / f'img/field/characters/aidan/aidan_walk_right_{i:02d}.png').convert('RGBA')
    FR[i] = im.resize((round(im.width * SCALE), round(im.height * SCALE)), Image.LANCZOS)


def panel(dist, stride, title):
    W, H = 300, 260; S = Image.new('RGB', (W, H), (52, 62, 48)); d = ImageDraw.Draw(S)
    gy = 220; d.rectangle([0, gy, W, H], fill=(150, 120, 80))
    shift = int(dist * K) % (10 * K)
    for wx in range(-60, 70, 10):              # ground ticks every 10 world px, scrolling with the walked distance
        sx = W // 2 + wx * K - shift
        d.line([(sx, gy), (sx, gy + 8)], fill=(90, 70, 45), width=2)
    ph = int(dist // (stride / 4)) % 4 + 1; im = FR[ph]
    S.paste(im, (W // 2 - round(ANCHOR[0] * SCALE), gy - round(ANCHOR[1] * SCALE)), im)
    d.text((6, 4), title, fill=(240, 228, 190), font=F); d.text((6, 24), f'walk_right_{ph:02d}', fill=(200, 210, 200), font=F)
    return S


def main():
    OUT.mkdir(parents=True, exist_ok=True); frames = []
    for t in range(90):                          # 3 s at 30 fps, 60 world px/s
        dist = t * 2.0
        S = Image.new('RGB', (620, 260), (20, 24, 22))
        S.paste(panel(dist, 90, '現行 STRIDE_CYCLE=90'), (0, 0)); S.paste(panel(dist, 52, '候補 STRIDE_CYCLE=52'), (320, 0))
        frames.append(S.convert('P', palette=Image.ADAPTIVE, colors=200))
    frames[0].save(OUT / 'aidan_side_cadence_compare.gif', save_all=True, append_images=frames[1:], duration=33, loop=0)
    print('ok')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""DIRECTIVE-ART-08C preview (offline, deterministic): Aidan walking right over ground ticks, frame chosen by walked distance
exactly like js/field/moss-forest-runtime.js (phase = floor(dist / (stride/n)) % n).
Panels: A adopted 4 frames, stride 90 (current) / B adopted 4 frames, stride 52 (ART-08B test) / C trial 6 frames (far leg shaded,
05/06 derived), stride 52. Also a still strip (x0.5 crops). Output: docs/art/candidates/art-08c/."""
import pathlib
from PIL import Image, ImageDraw, ImageFont

R = pathlib.Path(__file__).resolve().parents[2]; D = R / 'docs/art/candidates/art-08c'
F = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 14)
K = 3; SCALE = 0.0625 * K; ANCHOR = (1024, 1230)


def load(p):
    im = Image.open(p).convert('RGBA'); return im.resize((round(im.width * SCALE), round(im.height * SCALE)), Image.LANCZOS)


ADOPT = [load(R / f'img/field/characters/aidan/aidan_walk_right_{i:02d}.png') for i in range(1, 5)]
TRIAL = [load(D / f'aidan_walk_right_{i:02d}_candidate.png') for i in range(1, 7)]


def panel(dist, frames, stride, title):
    W, H = 300, 250; S = Image.new('RGB', (W, H), (52, 62, 48)); d = ImageDraw.Draw(S); gy = 212
    d.rectangle([0, gy, W, H], fill=(150, 120, 80)); sh = int(dist * K) % (10 * K)
    for wx in range(-60, 70, 10): sx = W // 2 + wx * K - sh; d.line([(sx, gy), (sx, gy + 8)], fill=(90, 70, 45), width=2)
    n = len(frames); ph = int(dist // (stride / n)) % n; im = frames[ph]
    S.paste(im, (W // 2 - round(ANCHOR[0] * SCALE), gy - round(ANCHOR[1] * SCALE)), im)
    d.text((6, 4), title, fill=(240, 228, 190), font=F); d.text((6, 22), f'{ph + 1:02d}/{n:02d}', fill=(200, 210, 200), font=F); return S


def main():
    frames = []
    for t in range(120):
        dist = t * 1.5; S = Image.new('RGB', (930, 250), (20, 24, 22))
        for j, (fr, st, tt) in enumerate(((ADOPT, 90, 'A 現行4コマ・周期90'), (ADOPT, 52, 'B 現行4コマ・周期52'), (TRIAL, 52, 'C 試作6コマ・周期52'))):
            S.paste(panel(dist, fr, st, tt), (j * 315, 0))
        frames.append(S.convert('P', palette=Image.ADAPTIVE, colors=220))
    frames[0].save(D / 'loop_aidan_side_compare.gif', save_all=True, append_images=frames[1:], duration=33, loop=0)
    # still strip: adopted 01-04 (05/06 = repeats of 02/03) vs trial 01-06, legs crop
    cw, chh = 330, 233; S = Image.new('RGB', (6 * cw + 20, 2 * (chh + 26) + 40), (20, 24, 22)); d = ImageDraw.Draw(S)
    for r, (lab, srcs) in enumerate((('採用（現行）', [R / f'img/field/characters/aidan/aidan_walk_right_{k:02d}.png' for k in (1, 2, 3, 4, 2, 3)]),
                                     ('試作（奥の脚に影・05/06追加）', [D / f'aidan_walk_right_{k:02d}_candidate.png' for k in range(1, 7)]))):
        y = 36 + r * (chh + 26); d.text((10, y - 22), lab + ('　※05・06の位置は現行では存在しない（02・03を参考表示）' if r == 0 else ''), fill=(240, 228, 190), font=F)
        for i, p in enumerate(srcs):
            im = Image.open(p).convert('RGBA').crop((740, 760, 1420, 1240)).resize((cw, chh), Image.LANCZOS)
            B = Image.new('RGBA', im.size, (72, 84, 66, 255)); B.alpha_composite(im); S.paste(B.convert('RGB'), (10 + i * cw, y)); d.text((14 + i * cw, y + 4), f'{i + 1:02d}', fill=(255, 255, 255), font=F)
    S.save(D / 'compare_aidan_side_strip.png'); print('ok')


if __name__ == '__main__':
    main()

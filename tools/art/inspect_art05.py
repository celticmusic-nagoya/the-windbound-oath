#!/usr/bin/env python3
"""DIRECTIVE-ART-05A: technical inspection of the adopted soldier PNG (read-only on the input) + an alpha-only fix candidate.

Input : docs/art/candidates/art-05/soldier_front_idle_112x168_candidate.png (user delivery, kept byte-for-byte)
Output: inspection.json, check_backgrounds.png, soldier_front_idle_112x168_alphafix_candidate.png
The fix changes ONLY the alpha of near-opaque body pixels (alpha >= 240 -> 255). RGB, shape, face, gear and colours are untouched.
"""
import hashlib, json, pathlib
import numpy as np
from PIL import Image, ImageDraw

R = pathlib.Path(__file__).resolve().parents[2]; D = R / 'docs/art/candidates/art-05'
SRC = D / 'soldier_front_idle_112x168_candidate.png'; FIX = D / 'soldier_front_idle_112x168_alphafix_candidate.png'


def stats(path):
    im = Image.open(path); a = np.array(im.convert('RGBA')).astype(int); al = a[..., 3]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; mx = np.maximum(np.maximum(r, g), b); mn = np.minimum(np.minimum(r, g), b)
    rows = np.where((al > 128).any(1))[0]; cols = np.where((al > 128).any(0))[0]
    boot = (al > 200) & (r > 90) & (g > 50) & (b < 70) & (r > g)
    bc = np.where(boot[155:166].any(0))[0]
    helmet = (al > 200) & (mx - mn < 30) & (mx > 120); hr = np.where(helmet[:, 50:90].sum(1) > 3)[0]
    return dict(file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), size=list(im.size), mode=im.mode,
                alpha_zero=int((al == 0).sum()), alpha_255=int((al == 255).sum()), alpha_240_254=int(((al >= 240) & (al < 255)).sum()),
                alpha_edge_1_239=int(((al > 0) & (al < 240)).sum()),
                transparent_rgb_variants=int(len(np.unique(a[al == 0][:, :3].reshape(-1, 3), axis=0))),
                content_rows_alpha128=[int(rows.min()), int(rows.max())], content_cols_alpha128=[int(cols.min()), int(cols.max())],
                top_row_max_alpha=int(al[0].max()), top_row_px=int((al[0] > 0).sum()), bottom_row_max_alpha=int(al[-1].max()),
                boots_x=[int(bc.min()), int(bc.max())], boots_bottom_y=int(np.where(boot.any(1))[0].max()), helmet_top_y=int(hr.min()),
                feet_centre_x=float((bc.min() + bc.max()) / 2))


def main():
    s = stats(SRC)
    a = np.array(Image.open(SRC).convert('RGBA')); a[..., 3] = np.where(a[..., 3] >= 240, 255, a[..., 3])
    Image.fromarray(a, 'RGBA').save(FIX)
    f = stats(FIX)
    # world-scale derived values (display 56x84 world = 0.5 world per px)
    s['world'] = dict(display=[56, 84], feet_above_anchor=(168 - 1 - s['boots_bottom_y']) * .5, helmet_top_height=(s['boots_bottom_y'] - s['helmet_top_y']) * .5,
                      plume_top_height=(s['boots_bottom_y'] - s['content_rows_alpha128'][0]) * .5, feet_centre_offset_x=(s['feet_centre_x'] - 55.5) * .5)
    (D / 'inspection.json').write_text(json.dumps(dict(input=s, alphafix=f), ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    im = Image.open(SRC).convert('RGBA'); W, H = im.size; bgs = [(255, 255, 255), (24, 24, 24), (255, 0, 255), (60, 120, 60)]
    S = Image.new('RGB', ((W + 8) * len(bgs) * 2, H + 8), (0, 0, 0))
    for k, src in enumerate((SRC, FIX)):
        im = Image.open(src).convert('RGBA')
        for i, c in enumerate(bgs):
            B = Image.new('RGBA', (W, H), c + (255,)); B.alpha_composite(im); x = (k * len(bgs) + i) * (W + 8) + 4
            S.paste(B.convert('RGB'), (x, 4)); d = ImageDraw.Draw(S); d.line([(x, 4 + H - 1), (x + W - 1, 4 + H - 1)], fill=(255, 32, 80))
            d.line([(x + W // 2, 4 + H - 6), (x + W // 2, 4 + H - 1)], fill=(255, 32, 80))
    S.resize((S.width * 3, S.height * 3), Image.NEAREST).save(D / 'check_backgrounds.png')
    print(json.dumps(s, ensure_ascii=False)[:900])


if __name__ == '__main__':
    main()

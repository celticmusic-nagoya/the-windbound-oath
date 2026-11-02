#!/usr/bin/env python3
"""DIRECTIVE-ART-08E: Aidan side walk 6 frames (right + left) from the adopted 4 per side - CANDIDATES (trial implementation).

Method = ART-08D gate 1 (approved): the FAR leg is shaded (x0.66, slight desaturation) on leg-coloured pixels inside hand-measured
regions; no pixel is moved or repainted. 05/06 reuse 02/03 with the near/far roles swapped, giving
  01 near leg forward & planted / 02 weight on near, far leg lifts / 03 far leg passes / 04 far leg forward & planted /
  05 weight on far, near leg lifts / 06 near leg passes -> 01.
Right-facing: near = character's right leg. Left-facing: near = character's left leg (mirror convention; the left set is a
separate painting, so its regions are measured separately). Arms and cape are not touched (deferred by the directive).
Output: docs/art/candidates/art-08e/aidan_walk_{right,left}_0N.png (+ qa.json, region check sheet)."""
import hashlib, json, pathlib
import numpy as np
from PIL import Image, ImageDraw
import make_art08c_aidan_side as C

R = pathlib.Path(__file__).resolve().parents[2]; SRC = R / 'img/field/characters/aidan'; OUT = R / 'docs/art/candidates/art-08e'
W, H = 2048, 1280; SHADE = .66

POLY = dict(C.POLY)
POLY.update({   # left-facing set (full resolution), measured on the adopted aidan_walk_left_0N.png
    'L01_rear': [(1120, 960), (1215, 960), (1250, 1050), (1340, 1095), (1362, 1170), (1335, 1222), (1180, 1222), (1190, 1110), (1150, 1050), (1110, 1000)],
    'L02_rear': [(1075, 955), (1150, 955), (1195, 1005), (1300, 1025), (1325, 1100), (1290, 1198), (1200, 1200), (1195, 1110), (1115, 1060), (1070, 1010)],
    'L02_front': [(925, 870), (1035, 870), (1045, 1000), (1025, 1110), (1035, 1225), (880, 1225), (888, 1150), (932, 1110), (925, 1000)],
    'L03_swing': [(885, 845), (1012, 845), (1042, 960), (1062, 1022), (1142, 1038), (1142, 1112), (1088, 1120), (1008, 1100), (998, 1040), (958, 982), (885, 952)],
    'L03_plant': [(955, 955), (1005, 955), (1012, 1030), (1002, 1110), (1078, 1128), (1078, 1228), (890, 1228), (900, 1168), (972, 1138), (982, 1050)],
    'L04_front': [(928, 875), (1035, 875), (1040, 1000), (1015, 1110), (1015, 1228), (910, 1228), (918, 1110), (932, 1000)],
})
# frame -> (source frame, far-leg region, region subtracted from it)
PLAN = {
    'right': {'01': ('01', '01_rear', None), '02': ('02', '02_rear', None), '03': ('03', '03_swing', None), '04': ('04', '04_front', None),
              '05': ('02', '02_front', '02_rear'), '06': ('03', '03_plant', '03_swing')},
    'left': {'01': ('01', 'L01_rear', None), '02': ('02', 'L02_rear', None), '03': ('03', 'L03_swing', None), '04': ('04', 'L04_front', None),
             '05': ('02', 'L02_front', 'L02_rear'), '06': ('03', 'L03_plant', 'L03_swing')},
}


def mask(name):
    im = Image.new('L', (W, H), 0); ImageDraw.Draw(im).polygon(POLY[name], fill=255); return np.array(im) > 0


def shade(a, m):
    o = a.copy(); px = o[m][..., :3].astype(float); lum = px.mean(1, keepdims=True)
    o[..., :3][m] = np.clip((px * .85 + lum * .15) * SHADE, 0, 255).astype(np.uint8); return o


def main():
    OUT.mkdir(parents=True, exist_ok=True); info = {}
    for side, plan in PLAN.items():
        for k, (src, far, minus) in plan.items():
            a = np.array(Image.open(SRC / f'aidan_walk_{side}_{src}.png').convert('RGBA'))
            m = mask(far)
            if minus: m &= ~mask(minus)
            m &= C.legcolour(a); o = shade(a, m)
            name = f'aidan_walk_{side}_{k}.png'; Image.fromarray(o, 'RGBA').save(OUT / name, optimize=True); diff = (o != a).any(2)
            info[name] = dict(source=f'aidan_walk_{side}_{src}.png', far_leg=far, shaded=int(m.sum()), changed_outside_far_leg=int((diff & ~m).sum()),
                              alpha_identical=bool((o[..., 3] == a[..., 3]).all()), size=list(o.shape[1::-1]), sha256=hashlib.sha256((OUT / name).read_bytes()).hexdigest())
    # gate-1 continuity: right 01/04 must equal the approved PR #111 candidates (same method/regions)
    (OUT / 'qa.json').write_text(json.dumps(dict(method='far-leg shading x0.66; 05/06 = 02/03 roles swapped', **info), ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    # region check sheet (left set): far region outlined in magenta
    S = Image.new('RGB', (6 * 330, 330), (20, 24, 22))
    for i, k in enumerate(['01', '02', '03', '04', '05', '06']):
        src, far, minus = PLAN['left'][k]
        im = Image.open(OUT / f'aidan_walk_left_{k}.png').convert('RGBA'); B = Image.new('RGBA', im.size, (72, 84, 66, 255)); B.alpha_composite(im)
        ImageDraw.Draw(B).line(POLY[far] + [POLY[far][0]], fill=(255, 60, 220), width=4)
        S.paste(B.crop((780, 820, 1420, 1240)).resize((320, 210)).convert('RGB'), (5 + i * 330, 60))
        ImageDraw.Draw(S).text((8 + i * 330, 30), f'left_{k}', fill=(240, 228, 190))
    S.save(OUT / 'check_left_regions.png')
    for n, v in info.items(): print(n, v['source'], v['far_leg'], v['shaded'], v['changed_outside_far_leg'], v['alpha_identical'])


if __name__ == '__main__':
    main()

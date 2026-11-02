#!/usr/bin/env python3
"""DIRECTIVE-ART-08C trial: Aidan right-walk passing frames 05/06 derived from the adopted 01-04 (CANDIDATES ONLY).

Finding (ART-07B): the side set is 01 contact / 02 weight+rear leg lifts / 03 rear leg swings forward / 04 contact with the other
leg, and then jumps back to 01 - the second passing pair is missing, and the near and far legs are painted identically, so the eye
cannot tell which leg is forward. Trial, without repainting:
  * the far leg ("B") is put in shade (value x0.66, slight desaturation) in every frame, so near/far read at game size;
  * 05 = 02 with the roles swapped (planted leg = far/shaded, lifted leg = near/bright);
  * 06 = 03 with the roles swapped (planted leg = far/shaded, swinging leg = near/bright).
Only pixels inside hand-measured leg regions that are leg-coloured (bronze armour / brown cloth; not the green/white cape) are
darkened; nothing is moved or redrawn, so shapes, face, hair, cape, sword and pouch stay identical to the adopted frames.
Known limit: in 03 the swinging leg is drawn in front of the planted leg; as the far leg it should pass behind it (that overlap
needs repainting). Output: docs/art/candidates/art-08c/."""
import hashlib, json, pathlib
import numpy as np
from PIL import Image, ImageDraw

R = pathlib.Path(__file__).resolve().parents[2]; SRC = R / 'img/field/characters/aidan'; OUT = R / 'docs/art/candidates/art-08c'
W, H = 2048, 1280
SHADE = .66

POLY = {   # full-resolution (2048x1280) leg regions measured on the adopted frames
    '01_rear': [(825, 1235), (972, 1235), (972, 1150), (1005, 1060), (1078, 1012), (1082, 945), (1010, 940), (960, 985), (895, 1068), (822, 1088)],
    '02_rear': [(1150, 890), (1156, 960), (1110, 1000), (1062, 1060), (1040, 1120), (1012, 1188), (938, 1178), (898, 1060), (935, 1008), (1000, 978), (1058, 930), (1080, 890)],
    '02_front': [(1160, 870), (1240, 870), (1250, 960), (1265, 1000), (1282, 1130), (1345, 1148), (1350, 1228), (1148, 1228), (1145, 1120), (1160, 1000), (1158, 960)],
    '03_swing': [(1150, 825), (1312, 825), (1312, 905), (1212, 962), (1162, 1092), (1095, 1092), (1095, 990), (1130, 930)],
    '03_plant': [(998, 860), (1095, 860), (1095, 1100), (1212, 1108), (1216, 1228), (1022, 1228), (1028, 1110), (998, 1000)],
    '04_front': [(1150, 880), (1235, 880), (1240, 960), (1262, 1000), (1276, 1110), (1402, 1114), (1402, 1228), (1198, 1228), (1194, 1100), (1150, 1000)],
}
# which region is the FAR (shaded) leg in each frame of the 6-step cycle; 05/06 reuse 02/03 with the other leg shaded
PLAN = {'01': ('01', ['01_rear']), '02': ('02', ['02_rear']), '03': ('03', ['03_swing']), '04': ('04', ['04_front']),
        '05': ('02', ['02_front']), '06': ('03', ['03_plant'])}


def mask(name):
    im = Image.new('L', (W, H), 0); ImageDraw.Draw(im).polygon(POLY[name], fill=255); return np.array(im) > 0


def legcolour(a):
    r, g, b = [a[..., i].astype(int) for i in range(3)]
    mx = np.maximum(np.maximum(r, g), b); mn = np.minimum(np.minimum(r, g), b)
    greenish = g > r + 4                       # cape green
    whitish = (mn > 170) & (mx - mn < 60)      # cape cream / white
    return (a[..., 3] > 0) & ~greenish & ~whitish


def shade(a, m):
    o = a.copy(); px = o[m][..., :3].astype(float); lum = px.mean(1, keepdims=True)
    px = (px * .85 + lum * .15) * SHADE; o[..., :3][m] = np.clip(px, 0, 255).astype(np.uint8); return o


def main():
    OUT.mkdir(parents=True, exist_ok=True); info = {}; base = {k: np.array(Image.open(SRC / f'aidan_walk_right_{k}.png').convert('RGBA')) for k in ('01', '02', '03', '04')}
    for k, (src, regions) in PLAN.items():
        a = base[src]; m = np.zeros((H, W), bool)
        for rgn in regions: m |= mask(rgn)
        if k == '06': m &= ~mask('03_swing')
        if k == '05': m &= ~mask('02_rear')
        m &= legcolour(a); o = shade(a, m)
        name = f'aidan_walk_right_{k}_candidate.png'; Image.fromarray(o, 'RGBA').save(OUT / name, optimize=True)
        diff = (o != a).any(2)
        info[name] = dict(source=f'aidan_walk_right_{src}.png', shaded_pixels=int(m.sum()), alpha_identical=bool((o[..., 3] == a[..., 3]).all()),
                          changed_outside_leg_regions=int((diff & ~m).sum()), sha256=hashlib.sha256((OUT / name).read_bytes()).hexdigest())
    (OUT / 'qa.json').write_text(json.dumps(dict(method='far-leg shading of the adopted right-walk frames; 05/06 = 02/03 with roles swapped', shade=SHADE, **info), ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(info, ensure_ascii=False, indent=0)[:1500])


if __name__ == '__main__':
    main()

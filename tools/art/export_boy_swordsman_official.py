#!/usr/bin/env python3
"""Export the official blond 10-year-old boy swordsman (6-frame sheet, 1536x1024 RGBA) to the Rilde NPC frames.
usage: export_boy_swordsman_official.py <sheet.png> <npc_dir> [map.json]
- cut: each frame = its own connected core (alpha>=200), edge band = core dilated 20 px, alpha = smoothstep(110..235) of the source alpha inside that band
  (the sheet carries a soft brown glow with alpha<=200 around the figures; it is NOT kept), specks not attached to the core dropped.
- export: 288x256 RGBA (2x the 144x128 canvas / 72x64 display box), scale 0.40 (body ~189 px = ~47 px on screen, old placeholder 45.5), premultiplied-alpha area downscale,
  feet anchored at (146,252) = midpoint of the two boots' lowest 25 source px. NOT mirrored: the art faces right like the old placeholder (the walker mirrors with scaleX(-1) for dir -1).
- order 1..6 = reading order of the sheet (Ready, Raise, High Guard, Downswing, Follow-through, Recovery); idle = Ready (f01).
"""
import sys, json, hashlib
import numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi
sheet, outdir = sys.argv[1], sys.argv[2]
SCALE, CW, CH, FX, FY = 0.40, 288, 256, 146, 252
A = np.array(Image.open(sheet).convert('RGBA')); a = A[:, :, 3].astype(np.float32)
core = cv2.morphologyEx((a >= 200).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
lab, k = ndi.label(core); sl = ndi.find_objects(lab); sizes = ndi.sum(core, lab, range(1, k + 1))
comps = sorted([(sl[i][1].start, sl[i][0].start, i + 1) for i, s in enumerate(sizes) if s > 6000], key=lambda t: (t[1] > 450, t[0]))
assert len(comps) == 6, 'expected 6 figures, found %d' % len(comps)
t = np.clip((a - 110) / 125, 0, 1); t = t * t * (3 - 2 * t)
report = []
for n, (_, _, lid) in enumerate(comps, 1):
    m = (lab == lid).astype(np.uint8)
    band = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41)))
    na = t * band; l2, _ = ndi.label(na > 0.05); na = na * np.isin(l2, np.unique(l2[m > 0]))
    ys, xs = np.nonzero(na > 0.03); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    rgb = A[y0:y1, x0:x1, :3].astype(np.float32); al = na[y0:y1, x0:x1]
    solid = al > 0.78; fy = np.nonzero(solid.any(1))[0].max(); band_x = np.nonzero(solid[max(0, fy - 25):fy + 1].any(0))[0]
    fx = (band_x.min() + band_x.max()) / 2.0
    P = np.dstack([rgb * al[:, :, None], al])                       # premultiplied
    sw, sh = max(1, round((x1 - x0) * SCALE)), max(1, round((y1 - y0) * SCALE))
    Ps = cv2.resize(P, (sw, sh), interpolation=cv2.INTER_AREA)
    ox, oy = int(round(FX - fx * SCALE)), int(round(FY + 1 - (fy + 1) * SCALE))
    canvas = np.zeros((CH, CW, 4), np.float32)
    assert ox >= 1 and oy >= 1 and ox + sw <= CW - 1 and oy + sh <= CH - 1, ('frame %d does not fit' % n, ox, oy, sw, sh)
    canvas[oy:oy + sh, ox:ox + sw] = Ps
    a_ = canvas[:, :, 3:4]; out = np.dstack([np.where(a_ > 1e-4, canvas[:, :, :3] / np.maximum(a_, 1e-4), 0), a_ * 255]).clip(0, 255).round().astype(np.uint8)
    Image.fromarray(out, 'RGBA').save('%s/boy_swordsman_f%02d.png' % (outdir, n), optimize=True)
    report.append({'frame': n, 'src_rect': [int(x0), int(y0), int(x1), int(y1)], 'foot_src': [round(float(fx) + x0, 1), int(fy + y0)], 'out_bbox': [ox, oy, ox + sw, oy + sh], 'clipped': False})
    print(n, report[-1])
Image.open('%s/boy_swordsman_f01.png' % outdir).save('%s/boy_swordsman_idle.png' % outdir, optimize=True)
if len(sys.argv) > 3:
    json.dump({'scale': SCALE, 'canvas': [CW, CH], 'foot_xy': [FX, FY], 'mirrored': False, 'idle': 'copy of f01 (Ready)', 'source_sha256': hashlib.sha256(open(sheet, 'rb').read()).hexdigest(), 'frames': report}, open(sys.argv[3], 'w'), indent=1)

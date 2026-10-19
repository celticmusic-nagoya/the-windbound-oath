#!/usr/bin/env python3
"""Normalize a delivered foreground PNG into a game-placement copy: RGB of fully transparent pixels (alpha==0) is set to 0; every pixel with alpha>0 is left byte-identical
(semi-transparent outline pixels are NOT touched). The delivered original is never modified. Prints a JSON audit line.
usage: normalize_fore_png.py SRC.png DST.png"""
import sys, json, hashlib
import numpy as np
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src); assert im.mode == 'RGBA', im.mode
a = np.array(im); t = a[..., 3] == 0
junk_before = int((a[..., :3][t].sum(axis=1) > 0).sum())
vis_before = a[~t].tobytes()
a[t, :3] = 0
Image.fromarray(a, 'RGBA').save(dst, optimize=True)
b = np.array(Image.open(dst).convert('RGBA'))
ok_vis = b[b[..., 3] > 0].tobytes() == vis_before
print(json.dumps({'src': src, 'dst': dst, 'size': im.size, 'alpha0_px': int(t.sum()), 'alpha0_with_rgb_before': junk_before,
                  'alpha0_with_rgb_after': int((b[..., :3][b[..., 3] == 0].sum(axis=1) > 0).sum()), 'visible_px_identical': ok_vis,
                  'alpha_min_max': [int(b[..., 3].min()), int(b[..., 3].max())], 'src_sha256': hashlib.sha256(open(src, 'rb').read()).hexdigest(), 'dst_sha256': hashlib.sha256(open(dst, 'rb').read()).hexdigest()}))

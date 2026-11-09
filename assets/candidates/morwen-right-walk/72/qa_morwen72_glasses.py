#!/usr/bin/env python3
"""Rebuild 72 (= build_morwen71 --proposal GLASSES) and verify every change vs 71 is a gold pixel inside the glasses box.
  python3 qa_morwen72_glasses.py <65B dir> <71 dir> <out dir>"""
import sys, json, numpy as np
from pathlib import Path
from PIL import Image
import build_morwen66 as B, build_morwen68 as D, build_morwen71 as M
src, c71, out = map(Path, sys.argv[1:4])
M.build(src, out, 'GLASSES')
ok = True
for f in range(6):
    for s, k in (('96x128', 1), ('48x64', 2)):
        a = np.array(Image.open(c71 / f'morwen_right_walk_{f:02d}_{s}.png')); b = np.array(Image.open(out / f'morwen_right_walk_{f:02d}_{s}.png'))
        d = np.any(a != b, axis=2); box = np.roll(M.box('glasses'), B.BOB[f], 0); box = box if k == 1 else box[1::2, 1::2]
        r, g, bb = (a[:, :, i].astype(int) for i in range(3)); gold = (r > 150) & (g > 80) & (bb < 110) & (r >= g) & (g > bb)
        bad = int((d & ~(box & gold)).sum()); ok &= bad == 0
        print(f'F{f} {s} changed={int(d.sum())} unintended={bad}')
print('PASS' if ok else 'FAIL'); sys.exit(0 if ok else 2)

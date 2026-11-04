#!/usr/bin/env python3
"""Support-boot ground gap, same method as PR #138 analyze_support.py (alpha contour, ROI + central columns,
gap = 1230 - (bottom covered row + 1), median over central columns). usage: measure_gap.py FRAME:PNG ..."""
import json, sys
import numpy as np
from PIL import Image
ANNOT = {1: ([1080, 1110, 1175, 1230], [1100, 1150]), 5: ([1090, 1110, 1180, 1230], [1100, 1170]),
         2: ([1015, 1090, 1100, 1230], [1040, 1090]), 6: ([1025, 1100, 1120, 1230], [1040, 1100])}
out = {}
for arg in sys.argv[1:]:
    n, path = arg.split(':', 1); n = int(n); (x0, y0, x1, y1), (cx0, cx1) = ANNOT[n]
    v = np.array(Image.open(path).convert('RGBA'))
    r = {}
    for th in (128, 200):
        gaps = []
        for x in range(cx0, cx1 + 1):
            ys = np.where(v[y0:y1, x, 3] > th)[0]
            if len(ys):
                gaps.append(1230 - (ys.max() + y0 + 1))
        r[th] = {'median': float(np.median(gaps)), 'range': [int(min(gaps)), int(max(gaps))]}
    out[path] = {'frame': n, **{'alpha>%d' % k: v_ for k, v_ in r.items()}}
print(json.dumps(out, indent=1))

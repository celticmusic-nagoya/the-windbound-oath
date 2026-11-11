"""Raise a boot's top (cuff) without touching the sole or the heel.
Inside a column box only: rows [top_old, cuff_end) move up by D unchanged (cuff + upper strap keep
their shape); rows [cuff_end, keep_from) - a plain or laced shaft section - are stretched to fill
[cuff_end - D, keep_from); everything from keep_from down (lower strap, heel, sole) is untouched.
Rows above top_old - D and all columns outside the box are untouched.
Usage: python3 boot_extend.py IN.png OUT.png x0 x1 top_old cuff_end keep_from D"""
import sys, numpy as np
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
x0, x1, top_old, cuff_end, keep_from, D = map(int, sys.argv[3:9])
a = np.asarray(Image.open(src).convert("RGBA")).astype(np.float64)
pm = a.copy(); pm[..., :3] *= pm[..., 3:4] / 255.0
out = pm.copy()
for y in range(top_old - D, keep_from):
    if y < cuff_end - D:
        ys = y + D
    else:
        ys = cuff_end + (y - (cuff_end - D)) * (keep_from - cuff_end) / (keep_from - cuff_end + D)
    y0 = int(np.floor(ys)); f = ys - y0
    row = pm[y0, x0:x1] * (1 - f) + pm[min(y0 + 1, pm.shape[0] - 1), x0:x1] * f
    if y < top_old:
        # above the old top only the moved cuff is drawn over the sock; keep the sock where the cuff is absent
        al = row[:, 3:4] / 255.0
        out[y, x0:x1] = row + out[y, x0:x1] * (1 - al)
    else:
        out[y, x0:x1] = row
al = out[..., 3:4]
res = np.where(al > 0, out[..., :3] * 255.0 / np.maximum(al, 1e-6), 0)
o = np.dstack([res, al]).clip(0, 255).round().astype(np.uint8)
Image.fromarray(o, "RGBA").save(dst)

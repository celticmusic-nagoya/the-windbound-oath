"""Lightness/chroma correction of one material inside a feathered box.
kind = leather (Lab hue -10..70 deg, L<70, C>5) or purple (Lab hue < -20 deg).
Usage: python3 region_fix.py IN.png OUT.png kind x0 y0 x1 y1 dL kC"""
import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage import color
src, dst, kind = sys.argv[1:4]
x0, y0, x1, y1 = map(int, sys.argv[4:8]); dL, kC = float(sys.argv[8]), float(sys.argv[9])
a = np.asarray(Image.open(src).convert("RGBA")).astype(np.float64)
lab = color.rgb2lab(a[..., :3] / 255.0)
h = np.degrees(np.arctan2(lab[..., 2], lab[..., 1])); C = np.hypot(lab[..., 1], lab[..., 2])
def ramp(x, lo, hi, f): return np.clip(np.minimum(x - lo, hi - x) / f, 0, 1)
if kind == "leather":
    w = ramp(h, -10, 70, 6) * np.clip((70 - lab[..., 0]) / 5, 0, 1) * np.clip((C - 5) / 3, 0, 1)
else:
    w = np.clip((-20 - h) / 6, 0, 1)
box = np.zeros(w.shape); box[y0:y1, x0:x1] = 1
w = w * ndi.gaussian_filter(box, 6) * (a[..., 3] > 0)
L2 = np.clip(lab[..., 0] + dL * w, 0, 100); C2 = C * (1 + (kC - 1) * w); H = np.radians(h)
lab2 = np.dstack([L2, C2 * np.cos(H), C2 * np.sin(H)])
o = a.copy(); o[..., :3] = np.round(np.clip(color.lab2rgb(lab2), 0, 1) * 255); o[a[..., 3] == 0, :3] = 0
Image.fromarray(o.astype(np.uint8), "RGBA").save(dst)

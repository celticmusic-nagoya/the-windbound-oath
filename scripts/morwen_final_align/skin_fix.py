"""Lift skin lightness (face/hands) by DL inside a soft Lab skin window (L>60, 4<a*<26, -2<b*<20).
Used because the hue-class colour match also catches orange-gold, so skin is corrected separately.
Usage: python3 skin_fix.py IN.png OUT.png DL"""
import sys, numpy as np
from PIL import Image
from skimage import color
from scipy import ndimage as ndi
a = np.asarray(Image.open(sys.argv[1]).convert("RGBA")).astype(np.float64)
lab = color.rgb2lab(a[..., :3] / 255.0); dl = float(sys.argv[3])
L, A, B = lab[..., 0], lab[..., 1], lab[..., 2]
def ramp(x, lo, hi, f=3.0): return np.clip(np.minimum(x - lo, hi - x) / f, 0, 1)
w = np.clip((L - 60) / 6, 0, 1) * ramp(A, 4, 26) * ramp(B, -2, 20)
core = ndi.binary_opening(w > 0.5, iterations=1)
lb, n = ndi.label(core); sz = ndi.sum(core, lb, range(1, n + 1))
region = ndi.binary_dilation(np.isin(lb, np.nonzero(sz >= 300)[0] + 1), iterations=3)
w = ndi.gaussian_filter(w * region, 1.0)
lab[..., 0] = np.clip(L + dl * w, 0, 100)
o = a.copy(); o[..., :3] = np.round(np.clip(color.lab2rgb(lab), 0, 1) * 255); o[a[..., 3] == 0, :3] = 0
Image.fromarray(o.astype(np.uint8), "RGBA").save(sys.argv[2])

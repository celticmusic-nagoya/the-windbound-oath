"""Scale lightness/chroma of one colormatch.py material class over the whole image.
Usage: python3 class_scale.py IN.png OUT.png CLASS dL kC   (CLASS = gold, gold_dark, purple, ...)"""
import sys, numpy as np
from PIL import Image
from skimage import color
import colormatch as cm
src, dst, name = sys.argv[1:4]; dL, kC = float(sys.argv[4]), float(sys.argv[5])
a, lab, hsv = cm.prep(src)
_, rh, rl = [c for c in cm.CLS if c[0] == name][0]
w = cm.weights(lab, hsv, rh, rl) * (a[..., 3] > 0)
C = np.hypot(lab[..., 1], lab[..., 2]) * (1 + (kC - 1) * w); H = np.arctan2(lab[..., 2], lab[..., 1])
lab2 = np.dstack([np.clip(lab[..., 0] + dL * w, 0, 100), C * np.cos(H), C * np.sin(H)])
o = a.copy(); o[..., :3] = np.round(np.clip(color.lab2rgb(lab2), 0, 1) * 255); o[a[..., 3] == 0, :3] = 0
Image.fromarray(o.astype(np.uint8), "RGBA").save(dst)

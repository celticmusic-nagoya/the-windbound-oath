"""Region-limited purple correction (feathered box): chroma factor and lightness delta applied to the
purple class inside the box (used for the left cape in final-align-01 and the back hair in final-04).
Usage: python3 cape_fix.py IN.png OUT.png x0 y0 x1 y1 chroma_factor L_delta"""
import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage import color
import colormatch as cm
src, dst = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = map(int, sys.argv[3:7]); kC, dL = float(sys.argv[7]), float(sys.argv[8])
a, lab, hsv = cm.prep(src)
box = np.zeros(a.shape[:2]); box[y0:y1, x0:x1] = 1
box = ndi.gaussian_filter(box, 20)
w = cm.weights(lab, hsv, (275, 325), (0, 101)) * box
C = np.hypot(lab[..., 1], lab[..., 2]) * (1 + (kC - 1) * w); H = np.arctan2(lab[..., 2], lab[..., 1])
lab2 = np.dstack([np.clip(lab[..., 0] + dL * w, 0, 100), C * np.cos(H), C * np.sin(H)])
o = a.copy(); o[..., :3] = np.round(np.clip(color.lab2rgb(lab2), 0, 1) * 255); o[a[..., 3] == 0, :3] = 0
Image.fromarray(o.astype(np.uint8), "RGBA").save(dst)

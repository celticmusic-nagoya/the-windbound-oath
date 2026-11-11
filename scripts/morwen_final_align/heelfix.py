import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
src, dst = sys.argv[1], sys.argv[2]
a = np.asarray(Image.open(src).convert("RGBA")).astype(np.float64)
H, W = a.shape[:2]
Y0, YB = 1440, 1518          # shear starts at the ankle (Y0); heel bottom row in the source (YB)
X_HEEL, X_ARCH = 575, 600     # full drop left of X_HEEL, none right of X_ARCH (forefoot stays)
DROP = 6.0                    # heel bottom 1518 -> 1524 (same row as the forefoot sole)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
fx = np.clip((X_ARCH - xx) / (X_ARCH - X_HEEL), 0, 1)
fy = np.clip((yy - Y0) / (YB + DROP - Y0), 0, 1)
dy = DROP * fx * fy
dy[(xx > 760) | (xx < 505)] = 0
# inverse map: output pixel (y,x) samples input at (y - dy, x)
out = np.empty_like(a)
pm = a.copy(); pm[..., :3] *= pm[..., 3:4] / 255.0   # premultiplied resampling
for c in range(4):
    out[..., c] = ndi.map_coordinates(pm[..., c], [yy - dy, xx], order=1, mode="constant")
al = out[..., 3:4]
out[..., :3] = np.where(al > 0, out[..., :3] * 255.0 / np.maximum(al, 1e-6), 0)
out = np.clip(np.round(out), 0, 255).astype(np.uint8)
Image.fromarray(out, "RGBA").save(dst)

#!/usr/bin/env python3
"""Trial: opposite-foot frame by TRANSLATING (not mirroring) each leg to the other leg's place.
Lighting and the boot drawing keep their original orientation. usage: SRC OUT --rect X0 Y0 X1 Y1 --split X [--mask M]"""
import argparse, sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from mirror_legs import leg_mask
p = argparse.ArgumentParser(); p.add_argument('src'); p.add_argument('out')
p.add_argument('--rect', nargs=4, type=int, required=True); p.add_argument('--split', type=float, required=True); p.add_argument('--mask')
o = p.parse_args()
a = np.array(Image.open(o.src).convert('RGBA')).astype(float)
m = leg_mask(a.astype(np.uint8), o.rect, [(0, 38, 0.42, 1.0)], 0.30)
H, W = m.shape; X = np.arange(W)[None, :].repeat(H, 0)
from skimage.segmentation import watershed
from skimage.filters import sobel
gray = a[..., :3].mean(-1)
mk = np.zeros(m.shape, int)
ys, xs = np.nonzero(m); yb = ys.max()
# seeds: lowest blob pixels on each side of the split (the two boot soles) + the thigh tops
mk[(m) & (X < o.split - 25) & (np.arange(H)[:, None] > yb - 140)] = 1
mk[(m) & (X > o.split + 25) & (np.arange(H)[:, None] > yb - 60)] = 2
lab = watershed(sobel(gray / 255), mk, mask=m)
left, right = lab == 1, lab == 2      # screen-left leg, screen-right leg
cl = np.nonzero(left)[1].mean(); cr = np.nonzero(right)[1].mean(); dx = int(round(cr - cl))
# which leg is in front (lower bottom = nearer the camera in a front view)
front_is_right = np.nonzero(right)[0].max() >= np.nonzero(left)[0].max()
rest = a.copy(); rest[m, 3] = 0
def layer(mask, shift):
    L = np.zeros_like(a); L[mask] = a[mask]; return np.roll(L, shift, axis=1)
Lr = layer(right, -dx)   # screen-right leg moved to the left place
Ll = layer(left, dx)     # screen-left leg moved to the right place
def over(t, b):
    ta, ba = t[..., 3:4] / 255, b[..., 3:4] / 255; oa = ta + ba * (1 - ta)
    return np.concatenate([(t[..., :3] * ta + b[..., :3] * ba * (1 - ta)) / np.maximum(oa, 1e-6), oa * 255], -1)
legs = over(Lr, Ll) if front_is_right else over(Ll, Lr)   # the leg that was in front stays in front
out = over(rest, legs)
Image.fromarray(np.clip(out, 0, 255).round().astype(np.uint8)).save(o.out)
if o.mask: Image.fromarray((m * 255).astype(np.uint8)).save(o.mask)
print('dx', dx, 'front is screen-right:', front_is_right)

"""Cut a figure out of a pure-black background (rev2).

Background = pixels with max channel <= BG_T that touch the border, plus enclosed regions of
>= MIN_HOLE px (ring holes, leg gaps). Edge pixels (within EDGE px of background and darker than
OPAQUE_T) get alpha = brightness / brightness of the nearest solid pixel, and that solid pixel's
colour (no division, so dark-noise is not amplified). Faint haze and detached specks are removed.
Enclosed dark regions are only treated as background when listed in HOLES (checked by eye:
background seen through a gap), because the art also contains pure-black fold lines and shadows.
Usage: python3 matte.py SRC_RGB.png DST_RGBA.png {back|left}
"""
import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
BG_T, EDGE, OPAQUE_T, A_MIN, SPECK = 8, 4, 40, 0.15, 600
# seeds (y, x) of enclosed background regions; boxes (x0, y0, x1, y1, max_brightness) for see-through ring holes
HOLES = {"back": {"seeds": [(1264, 484), (351, 372)], "boxes": []},
         "left": {"seeds": [(1221, 659)], "boxes": [(718, 180, 737, 194, 40)]}}
src, dst, view = sys.argv[1], sys.argv[2], sys.argv[3]
C = np.asarray(Image.open(src).convert("RGB")).astype(np.float64)
m = C.max(-1)
lab, n = ndi.label(m <= BG_T)
sizes = ndi.sum(np.ones_like(m), lab, range(n + 1))
border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
seeds = [int(lab[y, x]) for y, x in HOLES[view]["seeds"] if lab[y, x]]
keep = sorted(border | set(seeds))
bg = np.isin(lab, keep)
for x0, y0, x1, y1, t in HOLES[view]["boxes"]:
    box = np.zeros_like(bg); box[y0:y1, x0:x1] = True
    bg |= box & (m <= t)
near = ndi.binary_dilation(bg, iterations=EDGE) & ~bg & (m < OPAQUE_T)
solid = ~bg & ~near
_, (iy, ix) = ndi.distance_transform_edt(~solid, return_indices=True)
F = C[iy, ix]
a = np.ones(m.shape)
a[near] = np.clip(m[near] / np.maximum(F.max(-1)[near], OPAQUE_T), 0, 1)
a[bg] = 0
a[a < A_MIN] = 0
out = C.copy()
out[near] = F[near]
# drop detached specks (8-connected pieces of the alpha mask not part of the figure)
lab2, n2 = ndi.label(a > 0, structure=np.ones((3, 3)))
if n2 > 1:
    s2 = ndi.sum(np.ones_like(a), lab2, range(1, n2 + 1))
    main = int(np.argmax(s2)) + 1
    small = [i + 1 for i, s in enumerate(s2) if i + 1 != main and s < SPECK]
    a[np.isin(lab2, small)] = 0
A = np.round(a * 255).astype(np.uint8)
rgba = np.dstack([np.clip(np.round(out), 0, 255).astype(np.uint8), A])
rgba[A == 0, :3] = 0
Image.fromarray(rgba, "RGBA").save(dst)
print(dst, "bg", round(float(bg.mean()), 4), "edge", int(near.sum()), "holes", len(seeds),
      "specks removed", len(small) if n2 > 1 else 0)

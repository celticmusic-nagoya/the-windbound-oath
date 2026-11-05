#!/usr/bin/env python3
"""PLAYER-WALK-UP-06 step 2: close the speckled gaps between the new right knee and the hem underside.
Zone x 1095-1140, y 955-1012 only. Inside the PR #150 mask: pixels with alpha<200 that lie inside the morphological
closing (3 px) of the opaque area are filled from their neighbours (alpha 255). The 9 enclosed semi-transparent pixels
of official 03 that sit just OUTSIDE the mask are filled the same way: this is a recorded mask extension (MASK_EXT).
usage: close_speckles.py IN OUT"""
import json, os, sys
import numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
M = np.array(Image.open(os.path.join(ROOT, 'assets/candidates/player-walk-polish01/up-03-image-edit-kit/proposed_mask.png'))) > 0
a = np.array(Image.open(sys.argv[1])).astype(float); H, W = M.shape
zone = np.zeros((H, W), bool); zone[955:1012, 1095:1140] = True
op = a[..., 3] > 200
closed = ndi.binary_closing(op, iterations=3) | ndi.binary_fill_holes(op)
fill = zone & closed & ~op
ext = fill & ~M
rgb = np.clip(a[..., :3], 0, 255).astype(np.uint8); rgb = cv2.inpaint(rgb, fill.astype(np.uint8) * 255, 3, cv2.INPAINT_TELEA)
a[fill, :3] = rgb[fill]; a[fill, 3] = 255
res = np.clip(a, 0, 255).round().astype(np.uint8); Image.fromarray(res).save(sys.argv[2])
ext_mask = M | ext
Image.fromarray((ext * 255).astype(np.uint8)).save(os.path.join(os.path.dirname(sys.argv[2]), 'mask_extension_px.png'))
o = res[..., 3] > 200; enc = ndi.binary_fill_holes(o) & ~o
o24 = res[..., 3] > 24; enc24 = ndi.binary_fill_holes(o24) & ~o24
print(json.dumps({'filled_px': int(fill.sum()), 'mask_extension_px': int(ext.sum()), 'mask_extension_coords': [[int(x), int(y)] for y, x in zip(*np.nonzero(ext))],
                  'enclosed_alpha200_after': int(enc.sum()), 'enclosed_alpha24_after': int(enc24.sum())}))

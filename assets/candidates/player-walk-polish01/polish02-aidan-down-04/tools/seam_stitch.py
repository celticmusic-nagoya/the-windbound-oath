#!/usr/bin/env python3
"""PLAYER-WALK-POLISH-02-R2 method B': stitch official 06 (shifted +8 px onto the 04 hips) into official 04
along a minimum-difference seam instead of a straight cut.

The seam is found by dynamic programming on |04 - 06| (premultiplied RGBA):
  top seam    : left->right through rows TOP_BAND, where both frames are nearly identical (tunic skirt);
  side seams  : from the ends of the top seam down to the bottom of the canvas, through the cloth beside the legs.
Inside the enclosed region every pixel is official 06 (legs, thighs, tunic hem, frills as painted there);
outside it every pixel is official 04. A FEATHER-px premultiplied cross-fade along the seam hides the switch.
Nothing is mirrored, scaled, rotated or painted; the only new pixel values are the feather mixes of the two
official frames and are recorded in the output report.
usage: seam_stitch.py OUT [--top 770 815] [--xspan 995 1195] [--feather 3] [--debug DIR]
"""
import argparse, json, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
A = os.path.join(ROOT, 'img/field/characters/aidan/')
SHIFT = 8


def prem(a):
    return np.concatenate([a[..., :3] * a[..., 3:] / 255, a[..., 3:]], -1)


def dp_horizontal(cost):
    """min-cost path left->right, one row per column, |dy|<=1"""
    H, W = cost.shape; acc = cost.copy(); back = np.zeros((H, W), int)
    for x in range(1, W):
        prev = acc[:, x - 1]
        cand = np.stack([np.r_[np.inf, prev[:-1]], prev, np.r_[prev[1:], np.inf]])
        k = cand.argmin(0); acc[:, x] += cand[k, np.arange(H)]; back[:, x] = k - 1
    y = int(acc[:, -1].argmin()); path = [y]
    for x in range(W - 1, 0, -1):
        y = y + back[y, x]; path.append(y)
    return np.array(path[::-1])


def dp_vertical(cost, x_start):
    """min-cost path top->bottom starting at column x_start (row 0), |dx|<=1"""
    H, W = cost.shape; acc = np.full((H, W), np.inf); acc[0, x_start] = cost[0, x_start]; back = np.zeros((H, W), int)
    for y in range(1, H):
        prev = acc[y - 1]
        cand = np.stack([np.r_[np.inf, prev[:-1]], prev, np.r_[prev[1:], np.inf]])
        k = cand.argmin(0); acc[y] = cost[y] + cand[k, np.arange(W)]; back[y] = k - 1
    x = int(acc[-1].argmin()); path = [x]
    for y in range(H - 1, 0, -1):
        x = x + back[y, x]; path.append(x)
    return np.array(path[::-1])


def main():
    p = argparse.ArgumentParser(); p.add_argument('out')
    p.add_argument('--top', nargs=2, type=int, default=[770, 815]); p.add_argument('--xspan', nargs=2, type=int, default=[995, 1195])
    p.add_argument('--side', type=int, default=45, help='search width of the side seams, outward from the top seam ends')
    p.add_argument('--feather', type=int, default=3); p.add_argument('--debug')
    o = p.parse_args()
    O4 = np.array(Image.open(A + 'aidan_walk_down_04.png').convert('RGBA')).astype(float)
    O6 = np.roll(np.array(Image.open(A + 'aidan_walk_down_06.png').convert('RGBA')).astype(float), SHIFT, axis=1)
    H, W = O4.shape[:2]
    D = np.abs(prem(O4) - prem(O6)).mean(-1)
    D = ndi.uniform_filter(D, 3) + 2.0          # small constant: prefer short seams
    xl, xr = o.xspan; yt0, yt1 = o.top
    top = dp_horizontal(D[yt0:yt1, xl:xr + 1]) + yt0                     # y of the seam for x in [xl, xr]
    # side seams: from (xl, top[0]) and (xr, top[-1]) down to the bottom, searching outward of the legs only
    lw0 = xl - o.side; L = dp_vertical(D[top[0]:H, lw0:xl + 1], o.side) + lw0
    rw1 = xr + o.side; Rr = dp_vertical(D[top[-1]:H, xr:rw1 + 1], 0) + xr
    region = np.zeros((H, W), bool)
    for i, x in enumerate(range(xl, xr + 1)):
        region[top[i]:, x] = True
    for i, y in enumerate(range(top[0], H)):
        region[y, L[i]:xl] = True
    for i, y in enumerate(range(top[-1], H)):
        region[y, xr + 1:Rr[i] + 1] = True
    # the region must contain both legs entirely (06 legs and the 04 legs being replaced)
    w = region.astype(float)
    if o.feather:
        w = ndi.gaussian_filter(w, o.feather / 2)
        w = np.where(ndi.binary_erosion(region, iterations=o.feather), 1.0, np.where(ndi.binary_dilation(region, iterations=o.feather), w, 0.0))
    # cross-fade only where both frames are opaque; across a silhouette edge (cloth in one frame, background in
    # the other) take one frame or the other outright, so no half-transparent ghost edge can appear
    both = (O4[..., 3] >= 250) & (O6[..., 3] >= 250)
    w = np.where(both, w, region.astype(float))
    P = prem(O4) * (1 - w[..., None]) + prem(O6) * w[..., None]
    a = P[..., 3:4]; rgb = np.where(a > 0, P[..., :3] * 255 / np.maximum(a, 1e-6), 0)
    out = np.clip(np.concatenate([rgb, a], -1), 0, 255).round().astype(np.uint8)
    Image.fromarray(out).save(o.out)
    mixed = (w > 0) & (w < 1)
    info = {'top_seam_rows': [int(top.min()), int(top.max())], 'left_seam_x': [int(L.min()), int(L.max())], 'right_seam_x': [int(Rr.min()), int(Rr.max())],
            'region_px_from_06': int((w >= 1).sum()), 'feather_mixed_px': int(mixed.sum()),
            'seam_mean_diff': round(float(np.mean([D[top[i], xl + i] for i in range(len(top))]) - 2), 2)}
    if o.debug:
        os.makedirs(o.debug, exist_ok=True)
        Image.fromarray((region * 255).astype(np.uint8)).save(os.path.join(o.debug, 'region.png'))
        Image.fromarray((mixed * 255).astype(np.uint8)).save(os.path.join(o.debug, 'feather.png'))
    print(json.dumps(info))


if __name__ == '__main__':
    main()

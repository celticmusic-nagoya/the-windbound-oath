#!/usr/bin/env python3
"""PLAYER-WALK-GROUND-01: lower ONLY the support boot of official aidan_walk_down_06 (anatomical right leg,
screen-left) so its sole reaches the ground line like frames 01/05/02. Body, cape, other leg: unchanged.

Method (local vertical warp, official pixels only):
  - the support leg is separated from the lifted leg by a top-to-bottom minimum-cost path through the gap
    between them (columns SPLIT_LO..SPLIT_HI);
  - inside the support leg, below the knee guard, every row is pulled down by d(y):
        d = 0                          for y <= TOP     (knee guard / shin top: untouched, no seam)
        d = SHIFT * smoothstep(y)      for TOP < y < FULL (shin stretched by SHIFT px over FULL-TOP rows)
        d = SHIFT                      for y >= FULL    (ankle, boot, decorations, sole: moved rigidly, not stretched)
    out(x, y) = in(x, y - d(y)), linear interpolation in y; nothing is painted or mirrored;
  - the lifted leg and all pixels outside the support-leg region are copied from official 06 unchanged.
usage: ground_support_boot.py OUT --shift 7 [--top 1060] [--full 1170] [--mask MASK.png]
"""
import argparse, json, os
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
SRC = os.path.join(ROOT, 'img/field/characters/aidan/aidan_walk_down_06.png')
X_LO, X_HI = 990, 1140          # columns that may belong to the support leg (screen-left)
SPLIT_LO, SPLIT_HI = 1100, 1132  # search band for the path between the two legs
Y_SPLIT0 = 1000                  # rows from here down are split (above: thighs/hem, never edited)


def split_path(a):
    """x of the boundary between support leg (left) and lifted leg (right) for rows Y_SPLIT0..H-1"""
    y0 = Y_SPLIT0; band = a[y0:, SPLIT_LO:SPLIT_HI + 1].astype(float)
    cost = band[..., 3] / 255 * (0.3 + band[..., :3].mean(-1) / 255) + 0.02   # follow background / dark outline
    H, W = cost.shape; acc = cost.copy(); back = np.zeros((H, W), int)
    for y in range(1, H):
        prev = acc[y - 1]
        cand = np.stack([np.r_[np.inf, prev[:-1]], prev, np.r_[prev[1:], np.inf]])
        k = cand.argmin(0); acc[y] += cand[k, np.arange(W)]; back[y] = k - 1
    x = int(acc[-1].argmin()); path = [x]
    for y in range(H - 1, 0, -1):
        x += back[y, x]; path.append(x)
    return np.array(path[::-1]) + SPLIT_LO


def main():
    p = argparse.ArgumentParser(); p.add_argument('out')
    p.add_argument('--shift', type=float, required=True); p.add_argument('--top', type=int, default=1060); p.add_argument('--full', type=int, default=1170)
    p.add_argument('--mask')
    o = p.parse_args()
    a = np.array(Image.open(SRC).convert('RGBA')).astype(float); H, W = a.shape[:2]
    path = split_path(a)
    cut = np.full(H, X_HI); cut[Y_SPLIT0:] = path
    X = np.arange(W)[None, :]; Y = np.arange(H)[:, None]
    support_cols = (X >= X_LO) & (X < cut[:, None]) & (Y >= o.top)          # destination region
    ys = np.arange(H, dtype=float)
    t = np.clip((ys - o.top) / max(1, o.full - o.top), 0, 1); d = o.shift * t * t * (3 - 2 * t)
    d[ys <= o.top] = 0
    out = a.copy()
    rows = np.nonzero(d > 0)[0]
    for y in rows:
        sy = y - d[y]; y0 = int(np.floor(sy)); f = sy - y0
        cols = np.nonzero(support_cols[y])[0]
        if not len(cols):
            continue
        # source pixel must itself lie on the support side of the split (never pull lifted-leg pixels)
        src = a[y0, cols] * (1 - f) + a[min(y0 + 1, H - 1), cols] * f
        okc = cols < cut[y0]
        # premultiplied interpolation keeps anti-aliased edges clean
        pa = a[y0, cols, 3:4] * (1 - f); pb = a[min(y0 + 1, H - 1), cols, 3:4] * f; al = pa + pb
        rgb = (a[y0, cols, :3] * pa + a[min(y0 + 1, H - 1), cols, :3] * pb) / np.maximum(al, 1e-6)
        val = np.concatenate([rgb, al], -1)
        out[y, cols[okc]] = val[okc]
        out[y, cols[~okc], 3] = 0                                               # would-be lifted-leg pixel on the support side -> background
    res = np.clip(out, 0, 255).round().astype(np.uint8)
    Image.fromarray(res).save(o.out)
    changed = (res != a.astype(np.uint8)).any(-1)
    if o.mask:
        Image.fromarray((support_cols & (d[:, None] > 0)).astype(np.uint8) * 255).save(o.mask)
    print(json.dumps({'shift': o.shift, 'top': o.top, 'full': o.full, 'changed_px': int(changed.sum()),
                      'changed_bbox': [int(v) for v in (np.nonzero(changed)[1].min(), np.nonzero(changed)[0].min(), np.nonzero(changed)[1].max(), np.nonzero(changed)[0].max())] if changed.any() else None,
                      'split_x_range_rows_1040_1230': [int(path[40:].min()), int(path[40:].max())]}))


if __name__ == '__main__':
    main()

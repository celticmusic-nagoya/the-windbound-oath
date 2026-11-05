#!/usr/bin/env python3
"""FEASIBILITY PROBE ONLY (not a candidate): can the missing 'right support late, left leg swinging forward'
pose be assembled from official pixels? Base = official 06 (right foot planted). Its screen-right (anatomical left)
lifted leg is replaced by the screen-right leg of official 01 (anatomical left, forward), raised by LIFT px and moved
onto 06's hips. Legs are separated by a minimum-cost top-to-bottom path through the gap between them. No mirroring, no painting.
usage: probe_06_late_support.py OUT [--lift 18] [--debug DIR]"""
import argparse, os, sys, json
import numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'assets/candidates/player-walk-polish01/polish02-aidan-down-04/tools'))
from mirror_legs import leg_mask  # noqa
A = os.path.join(ROOT, 'img/field/characters/aidan/')
RECT = (960, 880, 1260, 1240)


def legs_split(a, xlo, xhi):
    """split the leg mask with a top-to-bottom minimum-cost path inside columns [xlo, xhi]:
    cost = opacity + brightness, so the path follows the background gap / dark outline between the legs"""
    m = leg_mask(a, RECT, [(0, 38, 0.42, 1.0)], 0.30)
    y0, y1 = RECT[1], RECT[3]
    cost = (a[y0:y1, xlo:xhi + 1, 3] / 255.0) * (0.3 + a[y0:y1, xlo:xhi + 1, :3].mean(-1) / 255.0) + 0.02
    H, W = cost.shape; acc = cost.copy(); back = np.zeros((H, W), int)
    for y in range(1, H):
        prev = acc[y - 1]
        cand = np.stack([np.r_[np.inf, prev[:-1]], prev, np.r_[prev[1:], np.inf]])
        k = cand.argmin(0); acc[y] += cand[k, np.arange(W)]; back[y] = k - 1
    x = int(acc[-1].argmin()); path = [x]
    for y in range(H - 1, 0, -1):
        x += back[y, x]; path.append(x)
    path = np.array(path[::-1]) + xlo
    X = np.arange(a.shape[1])[None, :]; cut = np.full(a.shape[0], (xlo + xhi) // 2); cut[y0:y1] = path
    left = m & (X < cut[:, None]); right = m & (X >= cut[:, None])
    return left, right


def over(t, b):
    ta, ba = t[..., 3:4] / 255, b[..., 3:4] / 255; oa = ta + ba * (1 - ta)
    return np.concatenate([(t[..., :3] * ta + b[..., :3] * ba * (1 - ta)) / np.maximum(oa, 1e-6), oa * 255], -1)


def main():
    p = argparse.ArgumentParser(); p.add_argument('out'); p.add_argument('--lift', type=int, default=18); p.add_argument('--debug')
    o = p.parse_args()
    b6 = np.array(Image.open(A + 'aidan_walk_down_06.png').convert('RGBA'))
    b1 = np.array(Image.open(A + 'aidan_walk_down_01.png').convert('RGBA'))
    # 06: screen-left boot planted (x~1030-1100, y~1200-1220); screen-right boot lifted (x~1140-1200, y~1120-1150)
    l6, r6 = legs_split(b6, 1095, 1150)
    # 01: screen-right boot planted (x~1090-1170, y~1200-1226); screen-left boot lifted (x~990-1050, y~1130-1165)
    l1, r1 = legs_split(b1, 1050, 1100)
    dx, dy = -6, -o.lift            # 01 hips are 6 px right of 06 hips; raise the foot off the ground
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    leg = np.zeros_like(b1); leg[r1] = b1[r1]
    leg = cv2.warpAffine(leg, M, (b1.shape[1], b1.shape[0]), flags=cv2.INTER_NEAREST, borderValue=(0, 0, 0, 0))
    base = b6.astype(float).copy(); base[r6, 3] = 0
    out = over(leg.astype(float), base)       # forward-swinging left leg drawn in front of the support leg
    op = out[..., 3] > 200; r = np.zeros_like(op); r[RECT[1]:RECT[3], RECT[0]:RECT[2]] = True
    hole = ndi.binary_fill_holes(op) & ~op & r
    Image.fromarray(np.clip(out, 0, 255).round().astype(np.uint8)).save(o.out)
    info = {'removed_06_left_leg_px': int(r6.sum()), 'inserted_01_left_leg_px': int(r1.sum()), 'shift': [dx, dy], 'enclosed_hole_px': int(hole.sum())}
    if o.debug:
        os.makedirs(o.debug, exist_ok=True); dbg = np.zeros(b6.shape[:2] + (3,), np.uint8)
        dbg[l6] = (60, 160, 60); dbg[r6] = (200, 60, 60); Image.fromarray(dbg).save(os.path.join(o.debug, 'split06.png'))
        dbg = np.zeros(b6.shape[:2] + (3,), np.uint8); dbg[l1] = (60, 160, 60); dbg[r1] = (60, 60, 220); Image.fromarray(dbg).save(os.path.join(o.debug, 'split01.png'))
    print(json.dumps(info))


if __name__ == '__main__':
    main()

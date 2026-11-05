#!/usr/bin/env python3
"""PLAYER-WALK-UP-02 trial: anatomical-RIGHT push-off (back view, screen-right) for the Aidan up walk.
Base  : official aidan_walk_up_03 (left foot planted, right leg small and receding).
Donor : the push-off leg of official aidan_walk_up_04 (screen-left leg, sole towards the camera, toe on the ground line).
The donor leg is TRANSLATED (never mirrored) to the right hip; the base's own right leg is removed; the base's cloth
(hem, skirt, cape) stays on top; the planted left leg stays underneath the near (push-off) foot.
usage: pushoff.py OUT --dx N [--dy 0] [--debug DIR]"""
import argparse, json, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
A = os.path.join(ROOT, 'img/field/characters/aidan/')
Y0 = 780

def hsv(a):
    rgb = a[..., :3] / 255; mx, mn = rgb.max(-1), rgb.min(-1); d = mx - mn + 1e-9; r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, (g - b) / d % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, d / (mx + 1e-9), mx

def legcol(a):
    h, s, v = hsv(a); return (a[..., 3] > 24) & ((((h < 40) | (h > 340)) & (s > 0.38)) | (v < 0.30))

def split(a, xlo, xhi):
    y0, y1 = Y0, 1240; c = (a[y0:y1, xlo:xhi + 1, 3] / 255) * (0.3 + a[y0:y1, xlo:xhi + 1, :3].mean(-1) / 255) + 0.02
    H, W = c.shape; acc = c.copy(); back = np.zeros((H, W), int)
    for y in range(1, H):
        p = acc[y - 1]; cand = np.stack([np.r_[np.inf, p[:-1]], p, np.r_[p[1:], np.inf]]); k = cand.argmin(0); acc[y] += cand[k, np.arange(W)]; back[y] = k - 1
    x = int(acc[-1].argmin()); path = [x]
    for y in range(H - 1, 0, -1):
        x += back[y, x]; path.append(x)
    cut = np.full(a.shape[0], (xlo + xhi) // 2); cut[y0:y1] = np.array(path[::-1]) + xlo; return cut

def over(t, b):
    ta, ba = t[..., 3:4] / 255, b[..., 3:4] / 255; oa = ta + ba * (1 - ta)
    return np.concatenate([(t[..., :3] * ta + b[..., :3] * ba * (1 - ta)) / np.maximum(oa, 1e-6), oa * 255], -1)

def main():
    p = argparse.ArgumentParser(); p.add_argument('out'); p.add_argument('--dx', type=int, required=True); p.add_argument('--dy', type=int, default=0); p.add_argument('--debug')
    o = p.parse_args()
    B = np.array(Image.open(A + 'aidan_walk_up_03.png').convert('RGBA')).astype(float)
    S = np.array(Image.open(A + 'aidan_walk_up_04.png').convert('RGBA')).astype(float)
    H, W = B.shape[:2]; X = np.arange(W)[None, :]; Yr = np.arange(H)[:, None]
    # base: separate planted left (screen-left) from the receding right leg
    cb = split(B, 1022, 1050)
    legB = legcol(B); legB[:Y0] = False
    h, sB, vB = hsv(B); trousers = (B[..., 3] > 24) & (vB < 0.36) & ((h < 40) | (h > 340))
    # attempt 3: columns limited to the legs; above the boots (y < 880) only dark trouser pixels, so gold cape trim stays
    legB = np.where(Yr < 880, trousers, legB) & (X >= 1000) & (X < 1145)
    rightB = legB & (X >= cb[:, None]) & (X < 1145)
    rightB = ndi.binary_dilation(rightB, iterations=1) & (B[..., 3] > 0) & (X >= cb[:, None]) & (Yr >= Y0)
    cloth = (B[..., 3] > 24) & ~legcol(B)                         # hem / skirt / cape of the base: stays on top
    # donor: push-off leg = screen-left leg of 04
    cs = split(S, 1032, 1058)
    legS = legcol(S); legS[:Y0] = False
    hS, sS, vS = hsv(S); trS = (S[..., 3] > 24) & (vS < 0.36) & ((hS < 40) | (hS > 340))
    legS = np.where(Yr < 880, trS, legS) & (X >= 925) & (X < 1060)
    donor = legS & (X < cs[:, None]) & (X >= 925)
    donor = ndi.binary_fill_holes(ndi.binary_closing(donor, iterations=3)) & (S[..., 3] > 0) & (X < cs[:, None]) & (Yr >= Y0)
    lab, n = ndi.label(donor); sz = ndi.sum(donor, lab, range(1, n + 1)); donor = lab == (1 + int(np.argmax(sz)))
    L = np.zeros_like(S); L[donor] = S[donor]; L = np.roll(np.roll(L, o.dx, axis=1), o.dy, axis=0)
    rest = B.copy(); rest[rightB, 3] = 0                          # remove the old right leg
    clothL = np.zeros_like(B); clothL[cloth & (Yr >= Y0)] = B[cloth & (Yr >= Y0)]
    out = over(clothL, over(L, rest))                             # cloth > new near leg > planted left leg
    res = np.clip(out, 0, 255).round().astype(np.uint8); Image.fromarray(res).save(o.out)
    diff = (res != B.astype(np.uint8)).any(-1)
    if o.debug:
        os.makedirs(o.debug, exist_ok=True)
        m = np.zeros((H, W, 3), np.uint8); m[rightB] = (200, 60, 60); m[np.roll(np.roll(donor, o.dx, 1), o.dy, 0)] = (60, 60, 220)
        Image.fromarray(m).save(os.path.join(o.debug, 'masks.png')); Image.fromarray((diff * 255).astype(np.uint8)).save(os.path.join(o.debug, 'diff.png'))
    op = res[..., 3] > 200
    print(json.dumps({'dx': o.dx, 'dy': o.dy, 'changed_px': int(diff.sum()), 'rows_above_780_identical': bool(not diff[:Y0].any()),
                      'removed_right_leg_px': int(rightB.sum()), 'donor_leg_px': int(donor.sum()), 'enclosed_holes': int((ndi.binary_fill_holes(op) & ~op).sum()),
                      'lowest_row': int(np.nonzero((res[..., 3] > 128).any(1))[0].max())}))

if __name__ == '__main__':
    main()

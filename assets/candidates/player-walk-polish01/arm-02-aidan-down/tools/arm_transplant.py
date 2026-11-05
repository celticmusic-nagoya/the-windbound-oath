#!/usr/bin/env python3
"""PLAYER-WALK-ARM-01: give one production frame the anatomical-LEFT arm (screen-right) of another official frame.

The donor frame is registered on the target by the chest/shoulder band (integer shift). Inside a closed contour
around the arm the pixels come from the donor; outside, the target is untouched. The contour is not a fixed shape:
starting from a core polygon that covers both arms, a closed minimum-difference path (polar dynamic programming,
radius limited to the core + BAND px) is chosen through cloth where donor and target already agree, so the switch
lands on near-identical pixels. A 3 px cross-fade is applied only where both frames are opaque. No mirroring,
rotation, scaling, painting or inpainting; legs (y >= LEG_Y) can never be touched.
usage: arm_transplant.py TARGET DONOR OUT [--shift DX DY] [--band 28] [--debug DIR]
"""
import argparse, json, os
import numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi

CORE = np.array([(1232, 592), (1302, 592), (1348, 698), (1350, 818), (1248, 818), (1230, 700)], np.int32)
BOX = (1180, 540, 1410, 870)     # hard limit of the edit
LEG_Y = 870                      # nothing at or below this row may change (legs / PR #139 grounding)
CHEST = (760, 300, 1340, 500)


def prem(a):
    return np.concatenate([a[..., :3] * a[..., 3:] / 255, a[..., 3:]], -1)


def gray(a):
    bg = np.array([70, 100, 70], np.float32)
    return (a[..., :3] * a[..., 3:] / 255 + bg * (1 - a[..., 3:] / 255)).mean(-1).astype(np.float32)


ARM_BOX = (1228, 600, 1372, 840)


def arm_mask(a):
    """screen-right forearm + glove (brown) + gauntlet (gold) of one frame, as one filled blob"""
    rgb = a[..., :3].astype(np.float32) / 255; mx, mn = rgb.max(-1), rgb.min(-1); d = mx - mn + 1e-9
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, (g - b) / d % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60; s = d / (mx + 1e-9)
    m = (a[..., 3] > 200) & (h < 42) & (s > 0.45) & (mx > 0.12)
    box = np.zeros_like(m); x0, y0, x1, y1 = ARM_BOX; box[y0:y1, x0:x1] = True; m &= box
    m = ndi.binary_opening(m, iterations=2)
    lab, n = ndi.label(m)
    if not n:
        return m
    sz = ndi.sum(m, lab, range(1, n + 1)); m = lab == (1 + int(np.argmax(sz)))
    return ndi.binary_fill_holes(ndi.binary_closing(m, iterations=5))


def main():
    p = argparse.ArgumentParser(); p.add_argument('target'); p.add_argument('donor'); p.add_argument('out')
    p.add_argument('--shift', nargs=2, type=int); p.add_argument('--band', type=int, default=28); p.add_argument('--feather', type=int, default=3)
    p.add_argument('--debug')
    p.add_argument('--tight', action='store_true', help='core = the two arms only (ARM-02)')
    o = p.parse_args()
    T = np.array(Image.open(o.target).convert('RGBA')).astype(float); D0 = np.array(Image.open(o.donor).convert('RGBA')).astype(float)
    H, W = T.shape[:2]
    if o.shift:
        dx, dy = o.shift
    else:
        x0, y0, x1, y1 = CHEST
        (sx, sy), _ = cv2.phaseCorrelate(gray(T)[y0:y1, x0:x1], gray(D0)[y0:y1, x0:x1]); dx, dy = -round(sx), -round(sy)
    D = cv2.warpAffine(D0.astype(np.float32), np.float32([[1, 0, dx], [0, 1, dy]]), (W, H), flags=cv2.INTER_NEAREST, borderValue=(0, 0, 0, 0)).astype(float)
    if o.tight:
        # ARM-02: core = the two arms only (glove + gauntlet colours, connected, holes filled) so the cloth and the
        # white lining around them stay the target's own; only where the target's old arm leaves a gap does donor
        # cloth come in, and the seam is chosen inside BAND px of the arms
        core = ndi.binary_dilation(arm_mask(T) | arm_mask(D), iterations=2)
    else:
        core = np.zeros((H, W), np.uint8); cv2.fillPoly(core, [CORE], 1); core = core.astype(bool)
    cost = ndi.uniform_filter(np.abs(prem(T) - prem(D)).mean(-1), 3) + 2.0
    # polar DP around the core centroid
    cy, cx = np.nonzero(core); c0 = (cx.mean(), cy.mean()); N = 720
    ang = np.linspace(0, 2 * np.pi, N, endpoint=False)
    rmax = np.zeros(N)
    for i, t in enumerate(ang):          # core radius per angle
        r = 0
        while True:
            x, y = int(round(c0[0] + (r + 1) * np.cos(t))), int(round(c0[1] + (r + 1) * np.sin(t)))
            if not (0 <= x < W and 0 <= y < H) or not core[y, x]:
                break
            r += 1
        rmax[i] = r
    R0 = 2; K = o.band
    Cm = np.full((N, K), np.inf)
    for i, t in enumerate(ang):
        for k in range(K):
            r = rmax[i] + R0 + k; x, y = int(round(c0[0] + r * np.cos(t))), int(round(c0[1] + r * np.sin(t)))
            if BOX[0] <= x < BOX[2] and BOX[1] <= y < min(BOX[3], LEG_Y - 4):
                Cm[i, k] = cost[y, x]
    best = None
    for start in range(K):               # closed path: fix the start radius, require the end to match
        acc = np.full((N, K), np.inf); acc[0, start] = Cm[0, start]; back = np.zeros((N, K), int)
        for i in range(1, N):
            prev = acc[i - 1]
            cand = np.stack([np.r_[np.inf, prev[:-1]], prev, np.r_[prev[1:], np.inf]])
            k = cand.argmin(0); acc[i] = Cm[i] + cand[k, np.arange(K)]; back[i] = k - 1
        end = [kk for kk in (start - 1, start, start + 1) if 0 <= kk < K]
        kk = min(end, key=lambda e: acc[-1, e])
        if best is None or acc[-1, kk] < best[0]:
            path = [kk]
            for i in range(N - 1, 0, -1):
                kk += back[i, kk]; path.append(kk)
            best = (acc[-1, path[0]], path[::-1])
    path = np.array(best[1])
    pts = np.array([(c0[0] + (rmax[i] + R0 + path[i]) * np.cos(t), c0[1] + (rmax[i] + R0 + path[i]) * np.sin(t)) for i, t in enumerate(ang)])
    region = np.zeros((H, W), np.uint8); cv2.fillPoly(region, [np.round(pts).astype(np.int32)], 1); region = region.astype(bool) | core
    region[LEG_Y:] = False
    w = region.astype(float)
    if o.feather:
        w = ndi.gaussian_filter(w, o.feather / 2)
        w = np.where(ndi.binary_erosion(region, iterations=o.feather), 1.0, np.where(ndi.binary_dilation(region, iterations=o.feather), w, 0.0))
    both = (T[..., 3] >= 250) & (D[..., 3] >= 250)
    w = np.where(both, w, region.astype(float)); w[LEG_Y:] = 0
    P = prem(T) * (1 - w[..., None]) + prem(D) * w[..., None]
    a = P[..., 3:4]; rgb = np.where(a > 0, P[..., :3] * 255 / np.maximum(a, 1e-6), 0)
    out = np.clip(np.concatenate([rgb, a], -1), 0, 255).round().astype(np.uint8)
    Image.fromarray(out).save(o.out)
    t8 = T.astype(np.uint8); diff = (out != t8).any(-1)
    info = {'target': o.target, 'donor': o.donor, 'donor_shift': [int(dx), int(dy)], 'region_px': int(region.sum()),
            'changed_px': int(diff.sum()), 'changed_bbox': [int(v) for v in (np.nonzero(diff)[1].min(), np.nonzero(diff)[0].min(), np.nonzero(diff)[1].max(), np.nonzero(diff)[0].max())] if diff.any() else None,
            'rows_from_%d_unchanged' % LEG_Y: bool(not diff[LEG_Y:].any()), 'seam_mean_diff': round(float(best[0] / N - 2), 2)}
    if o.debug:
        os.makedirs(o.debug, exist_ok=True)
        Image.fromarray((region * 255).astype(np.uint8)).save(os.path.join(o.debug, 'region.png'))
    print(json.dumps(info))


if __name__ == '__main__':
    main()

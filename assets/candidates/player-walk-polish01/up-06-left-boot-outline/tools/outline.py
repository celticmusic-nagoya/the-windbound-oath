#!/usr/bin/env python3
"""PLAYER-WALK-UP-06: smooth the right outline of the planted LEFT boot in the PR #152 candidate.
Per row y in [1015,1100] the boot's right edge e(y) is found (first gap after x=1040). The target edge t(y) is a
morphological closing of e (window W rows) i.e. notches are bridged between the neighbouring plate edges.
Added pixels (x in (e,t]) are painted by vertical interpolation between the nearest rows above and below that are
opaque at that x (the plate itself continues across the notch); the outermost 1 px gets the outline tone of the
boot edge (median of existing edge pixels). Only pixels inside the approved edit mask can change.
usage: outline.py OUT [--window 13] [--debug DIR]"""
import argparse, json, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
SRC = os.path.join(ROOT, 'assets/candidates/player-walk-polish01/up-05-pushoff-repair/aidan_walk_up_pushoff_candidate.png')
MASK = os.path.join(ROOT, 'assets/candidates/player-walk-polish01/up-03-image-edit-kit/proposed_mask.png')
O3 = os.path.join(ROOT, 'img/field/characters/aidan/aidan_walk_up_03.png')
Y0, Y1, X0 = 1015, 1114, 1040

def main():
    p = argparse.ArgumentParser(); p.add_argument('out'); p.add_argument('--window', type=int, default=13); p.add_argument('--debug'); o = p.parse_args()
    C = np.array(Image.open(SRC).convert('RGBA')).astype(float); M = np.array(Image.open(MASK)) > 0
    e = np.zeros(1280, int)
    for y in range(Y0, Y1):
        row = C[y, X0:X0 + 60, 3] > 200; gaps = np.nonzero(~row)[0]; e[y] = X0 + (gaps[0] if len(gaps) else 60) - 1
    seg = e[Y0:Y1].astype(float)
    t = ndi.minimum_filter1d(ndi.maximum_filter1d(seg, o.window), o.window)      # closing: bridge notches only
    t = np.minimum(t, ndi.uniform_filter1d(t, 5) + 1)
    ramp = np.clip((Y1 - np.arange(Y0, Y1)) / 16.0, 0, 1)                    # taper back to the original edge at the bottom
    t = (seg + (t - seg) * ramp).round().astype(int)
    edge_px = [C[y, e[y]] for y in range(Y0, Y1) if t[y - Y0] == e[y]]
    edge_tone = np.median(np.array(edge_px)[:, :3], 0)
    out = C.copy(); added = np.zeros(M.shape, bool)
    for y in range(Y0, Y1):
        for x in range(e[y] + 1, t[y - Y0] + 1):
            if not M[y, x] or C[y, x, 3] > 200:
                continue
            up = next((yy for yy in range(y - 1, Y0 - 25, -1) if C[yy, x, 3] > 200), None)
            dn = next((yy for yy in range(y + 1, Y1 + 25) if C[yy, x, 3] > 200), None)
            if up is None and dn is None:
                continue
            if up is None: col = C[dn, x, :3]
            elif dn is None: col = C[up, x, :3]
            else:
                w = (y - up) / (dn - up); col = C[up, x, :3] * (1 - w) + C[dn, x, :3] * w
            if x == t[y - Y0]:
                col = col * 0.4 + edge_tone * 0.6                                     # outline tone on the new rim
            out[y, x, :3] = col; out[y, x, 3] = 255; added[y, x] = True
    # anti-aliased rim: 1 px half-alpha just outside the new edge where it grew by >=2 px
    for y in range(Y0, Y1):
        x = t[y - Y0] + 1
        if t[y - Y0] - e[y] >= 2 and M[y, x] and out[y, x, 3] < 128:
            out[y, x, :3] = edge_tone; out[y, x, 3] = 110; added[y, x] = True
    res = np.clip(out, 0, 255).round().astype(np.uint8); Image.fromarray(res).save(o.out)
    o3 = np.array(Image.open(O3)); d3 = (res != o3).any(-1); dC = (res != C.astype(np.uint8)).any(-1)
    op = res[..., 3] > 200; enc = ndi.binary_fill_holes(op) & ~op
    info = {'window': o.window, 'added_px': int(added.sum()), 'changed_vs_pr152': int(dC.sum()), 'changed_vs_pr152_outside_rows_1015_1100_or_x_lt_1040': int((dC & ~((np.arange(1280)[:, None] >= Y0) & (np.arange(1280)[:, None] < Y1 + 1) & (np.arange(2048)[None, :] >= X0))).sum()),
            'changed_vs_official03_outside_mask': int((d3 & ~M).sum()), 'edge_profile_before': e[Y0:Y1].tolist(), 'edge_profile_after': t.tolist(),
            'max_notch_depth_before': int(max(seg.max() - 0, 0) and (ndi.minimum_filter1d(ndi.maximum_filter1d(seg, o.window), o.window) - seg).max()),
            'enclosed_holes_alpha200': int(enc.sum()), 'enclosed_holes_inside_mask': int((enc & M).sum()), 'edge_tone_rgb': [round(float(v), 1) for v in edge_tone]}
    if o.debug:
        os.makedirs(o.debug, exist_ok=True); Image.fromarray((added * 255).astype(np.uint8)).save(os.path.join(o.debug, 'added_px.png'))
    print(json.dumps({k: v for k, v in info.items() if not k.startswith('edge_profile')}))
    json.dump(info, open(os.path.splitext(o.out)[0] + '_info.json', 'w'), indent=1)

if __name__ == '__main__':
    main()

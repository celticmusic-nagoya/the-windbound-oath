#!/usr/bin/env python3
"""PLAYER-WALK-UP-04: local composite of the ChatGPT right-leg drawing onto official aidan_walk_up_03.
The generated image is only a SOURCE of the right lower body: it is scaled uniformly (no warping) and
registered on 03 by its planted LEFT boot (the same leg exists in both). Only pixels inside the PR #150
proposed mask can change; inside the mask the old right leg of 03 is removed and the generated right
leg (trousers + armour + boot colours only; its cloak/hem are discarded) is placed on top.
usage: composite.py OUT --scale S [--dx DX --dy DY] [--soften SIGMA] [--debug DIR]"""
import argparse, json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'assets/candidates/player-walk-polish01/up-03-image-edit-kit/tools'))
from legs import load, split, legs, SPL, hsv  # noqa: E402
GEN = os.path.join(HERE, '..', 'input', 'chatgpt_right_leg_generated.png')
MASK = os.path.join(ROOT, 'assets/candidates/player-walk-polish01/up-03-image-edit-kit/proposed_mask.png')
# registration points: planted LEFT boot bottom-centre in the generated image and in official 03
GEN_LBOOT = (375.0, 1560.0); O3_LBOOT = (1009.0, 1229.0)


def over(t, b):
    ta, ba = t[..., 3:4] / 255, b[..., 3:4] / 255; oa = ta + ba * (1 - ta)
    return np.concatenate([(t[..., :3] * ta + b[..., :3] * ba * (1 - ta)) / np.maximum(oa, 1e-6), oa * 255], -1)


def main():
    p = argparse.ArgumentParser(); p.add_argument('out'); p.add_argument('--scale', type=float, required=True)
    p.add_argument('--dx', type=float, default=0); p.add_argument('--dy', type=float, default=0); p.add_argument('--soften', type=float, default=0.0); p.add_argument('--debug'); p.add_argument('--armor-top', type=int, default=990); p.add_argument('--poly', action='store_true'); p.add_argument('--left-edge', type=int, default=1072); p.add_argument('--keep-thigh-until', type=int, default=960)
    o = p.parse_args()
    B = load(3); H, W = B.shape[:2]; mask = np.array(Image.open(MASK)) > 0
    g = Image.open(GEN).convert('RGBA'); s = o.scale
    gs = g.resize((round(g.width * s), round(g.height * s)), Image.LANCZOS)
    ox = round(O3_LBOOT[0] - GEN_LBOOT[0] * s + o.dx); oy = round(O3_LBOOT[1] - GEN_LBOOT[1] * s + o.dy)
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); layer.alpha_composite(gs, (max(0, ox), max(0, oy)), (max(0, -ox), max(0, -oy)))
    G = np.array(layer).astype(float)
    if o.soften:
        for c in range(4):
            G[..., c] = ndi.gaussian_filter(G[..., c], o.soften)
    h, sat, v = hsv(G)
    Yc = np.arange(H)[:, None]
    trousers = (G[..., 3] > 24) & ((h < 40) | (h > 340)) & (sat > 0.25) & (v < 0.45)
    bronze = (G[..., 3] > 24) & ((((h < 42) | (h > 340)) & (sat > 0.30)) | (v < 0.36))
    # attempt 2: above y=o.armor_top only trousers (the generated cloak border is gold and must not be taken)
    legcol = np.where(Yc < o.armor_top, trousers, bronze)
    if o.poly:
        # attempt 3: geometric selection of the raised right leg in GENERATED coordinates (no colour segmentation of
        # the leg itself); only the generated cloak (green / white / bright gold trim) is excluded by colour
        import cv2
        GP = np.array([(495, 600), (745, 560), (770, 640), (805, 780), (835, 950), (835, 1150), (805, 1270), (700, 1275), (610, 1205), (580, 1000), (560, 820), (520, 680)], float)
        cp = np.round(GP * s + [ox, oy]).astype(np.int32); pm = np.zeros((H, W), np.uint8); cv2.fillPoly(pm, [cp], 1); pm = pm.astype(bool)
        green = (h > 60) & (h < 180) & (sat > 0.15); white = (sat < 0.18) & (v > 0.70); trim = (h >= 36) & (h < 60) & (v > 0.70)
        legcol = pm & (G[..., 3] > 24) & ~green & ~white & ~trim
    newleg = legcol & mask
    lab, n = ndi.label(newleg)
    if n:
        newleg = lab == (1 + int(np.argmax(ndi.sum(newleg, lab, range(1, n + 1)))))
    newleg = ndi.binary_fill_holes(newleg) & (G[..., 3] > 0) & mask
    cut = split(B, *SPL[3]); _, R03 = legs(B, cut)
    Lleg, _ = legs(B, cut); Lleg = ndi.binary_fill_holes(ndi.binary_closing(Lleg, iterations=3))
    kill = mask & ndi.binary_dilation(R03, iterations=2) & ~Lleg & (np.arange(H)[:, None] >= o.keep_thigh_until)   # old right leg out below the thigh, never the left leg
    if o.poly:
        X = np.arange(W)[None, :]; Y = np.arange(H)[:, None]
        hb, sb, vb = hsv(B); cloth03 = (B[..., 3] > 24) & ((((hb > 60) & (hb < 180)) & (sb > 0.12)) | ((sb < 0.22) & (vb > 0.60)))
        if o.left_edge <= 0:   # follow the planted left boot's own dark outline (min-cost path) instead of a straight column
            edge = split(B, 1052, 1080, 980, 1240); edge[:980] = 1072
        else:
            edge = np.full(H, o.left_edge)
        kill = mask & (Y >= o.keep_thigh_until) & (X >= edge[:, None]) & ~cloth03   # geometric; planted left boot (x<left_edge) and the cloak/frills are never touched
    base = B.copy(); base[kill, 3] = 0
    L = np.zeros_like(G); L[newleg] = G[newleg]
    comp = over(L, base)
    out = B.copy(); out[mask] = comp[mask]
    res = np.clip(out, 0, 255).round().astype(np.uint8); Image.fromarray(res).save(o.out)
    b8 = B.astype(np.uint8); diff = (res != b8).any(-1); op = res[..., 3] > 200
    info = {'scale': s, 'offset': [ox, oy], 'soften': o.soften, 'changed_px': int(diff.sum()), 'changed_outside_mask': int((diff & ~mask).sum()),
            'new_leg_px': int(newleg.sum()), 'old_right_leg_removed_px': int(kill.sum()),
            'enclosed_holes': {'candidate': int((ndi.binary_fill_holes(op) & ~op).sum()), 'official_03': int((ndi.binary_fill_holes(b8[..., 3] > 200) & ~(b8[..., 3] > 200)).sum())},
            'new_leg_bbox': [int(v) for v in (np.nonzero(newleg)[1].min(), np.nonzero(newleg)[0].min(), np.nonzero(newleg)[1].max(), np.nonzero(newleg)[0].max())] if newleg.any() else None,
            'generated_leg_px_outside_mask_dropped': int((legcol & ~mask & (np.arange(W)[None, :] > 1045) & (np.arange(H)[:, None] > 880)).sum())}
    if o.debug:
        os.makedirs(o.debug, exist_ok=True); Image.fromarray((diff * 255).astype(np.uint8)).save(os.path.join(o.debug, 'diff.png'))
        Image.fromarray(np.clip(G, 0, 255).astype(np.uint8)).save(os.path.join(o.debug, 'gen_layer.png'))
    print(json.dumps(info))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""MORWEN-PIXEL-71: local art polish on ART-70B (director-approved candidate).

ADOPTED (71): ART-70B + boots polish on existing colours only
    lit-side boot outline one tone lighter (reads on dark backgrounds), toe front rim,
    ankle crease in every frame, heel back-edge highlight + dark ground line.
PROPOSALS (not adopted, protected pixels): each = 71 + one change, with diff masks
    HAT_GOLD   : hat gold trim -> 3 existing gold tones
    FLOWER     : 1px noise merge inside the hat flower box (petals/centre)
    GLASSES    : glasses gold -> 3 existing gold tones (eyes untouched)
    UPPER_GOLD : torso / skirt gold -> 3 existing gold tones (no noise merge)
No motion change (gait, ground, secondary motion and silhouettes = ART-70B).
  python3 build_morwen71.py --source <65B> --out <dir> [--proposal NAME]
"""
from pathlib import Path
import argparse, json, math
import numpy as np
import build_morwen66 as B
import build_morwen67 as C
import build_morwen68 as D
import build_morwen70 as E
import build_morwen70art as A

PROPOSALS = ('HAT_GOLD', 'FLOWER', 'GLASSES', 'UPPER_GOLD')
BOX = {   # 96x128 reference coordinates (before bob), inspected on 65B F00
    'flower': (30, 12, 50, 31),
    'glasses': (57, 29, 70, 39),
    'face': (54, 26, 72, 50),
}
STATE = {'proposal': None}


def box(name, h=128, w=96):
    x0, y0, x1, y1 = BOX[name]; yy, xx = np.mgrid[0:h, 0:w]
    return (xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1)


# ---------------------------------------------------------------- boots (adopted)
_shade_art = A.shade_art


def shade71(lab, geo, pal, far, front_mask, swing):
    S, Bo, info = _shade_art(lab, geo, pal, far, front_mask, swing)
    k = geo['k']; L = geo['leg']; big = k >= 1
    h, w = lab.shape
    bt = pal['boot_far' if far else 'boot']
    yy, xx = np.mgrid[0:h, 0:w]; cx, cy = xx + 0.5, yy + 0.5
    knee, ankle = L['knee'], L['ankle']
    vx, vy = ankle[0] - knee[0], ankle[1] - knee[1]; n = math.hypot(vx, vy)
    nx, ny = vy / n, -vx / n
    if nx < 0: nx, ny = -nx, -ny
    u = ((cx - knee[0]) * nx + (cy - knee[1]) * ny) / (4.8 * k)
    boot = np.isin(lab, (D.BT, D.CUFF, D.FOOT, D.TOE, D.HEEL))
    allm = lab != 0
    edge = np.zeros_like(allm)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb = np.zeros_like(allm)
        ys0, ys1 = max(0, dy), h + min(0, dy); xs0, xs1 = max(0, dx), w + min(0, dx)
        nb[ys0:ys1, xs0:xs1] = allm[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
        edge |= allm & ~nb
    gold = (Bo[:, :, 0] > 170) & (Bo[:, :, 2] < 90)
    up = np.vstack([np.zeros((1, w), bool), allm[:-1]])          # pixel above is leg
    if not far:
        # lit-side outline one tone lighter (top/front faces), keeps the near-black line on shadow/ground side
        m = edge & boot & (u > 0.35) & ~gold & up.__invert__() | (edge & (lab == D.BT) & (u > 0.35) & ~gold)
        Bo[m & boot] = (*bt[2], 255)
        # toe front rim: frontmost toe/foot edge pixels above the sole get the lit tone
        foot = np.isin(lab, (D.FOOT, D.TOE))
        if foot.any():
            fx = np.where(foot.any(0))[0].max()
            col = foot[:, fx]; ys = np.where(col)[0]
            for y in ys[:-1]:
                Bo[y, fx] = (*bt[3], 255)
    if big:
        # ankle crease in every frame (front half, one dark pixel row just above the ankle)
        ax, ay = ankle
        crease = (lab == D.BT) & (np.abs(cy - (ay - 1.5)) < 0.55) & (u > 0.05) & (u < 0.9) & ~gold
        Bo[crease] = (*bt[1], 255)
        # heel: back edge highlight on the top half, ground line dark
        heel = lab == D.HEEL
        if heel.any():
            hx = np.where(heel.any(0))[0].min()
            ys = np.where(heel[:, hx])[0]
            for y in ys[:max(1, len(ys) // 2)]:
                Bo[y, hx] = (*bt[2], 255)
            Bo[heel & ~np.vstack([heel[1:], np.zeros((1, w), bool)])] = (*C.OUTLINE, 255)
    return S, Bo, info


# ---------------------------------------------------------------- proposals (protected, not adopted)
_compose_art = A.compose_art


def compose71(f, U, pal, k):
    p = STATE['proposal']
    if p:
        U = dict(U)
        sc = 1 if k >= 1 else 2
        bob = B.BOB[f]
        def reg(m96):
            m = np.roll(m96, bob, 0)
            return m if sc == 1 else m[1::2, 1::2]
        face = reg(box('face'))
        if p == 'HAT_GOLD':
            yy, xx = np.mgrid[0:128, 0:96]
            r = reg((yy <= 31)) & ~reg(box('flower')) & ~reg(box('glasses')) & ~face
            U['immutable_details'], _ = A.gold3(U['immutable_details'], r)
        elif p == 'FLOWER':
            r = reg(box('flower'))
            for _ in range(2): U['immutable_details'], _ = A.denoise(U['immutable_details'], r)
        elif p == 'GLASSES':
            U['immutable_details'], _ = A.gold3(U['immutable_details'], reg(box('glasses')))
        elif p == 'UPPER_GOLD':
            for name in ('torso', 'skirt'):
                U[name], _ = A.gold3(U[name])
    return _compose_art(f, U, pal, k)


def build(source: Path, out: Path, proposal=None):
    ref, _ = B.load_reference(source / 'morwen_right_walk_00_96x128.png')
    A.GOLD3.clear(); A.GOLD3.update(A.pick_gold3(ref)); A.ART['level'] = 'B'
    uf, ub, _ = B.split_layers(ref)
    E.configure('B', uf)
    STATE['proposal'] = proposal
    D.shade68 = shade71; D.compose68 = compose71
    try:
        res = D.build(source, out)
    finally:
        D.shade68 = E._shade68; D.compose68 = A._compose68; STATE['proposal'] = None
    meta = json.loads((out / 'build_meta.json').read_text())
    meta['morwen71'] = {'base': 'ART-70B', 'proposal': proposal, 'boxes': BOX, 'gold3': {k: list(v) for k, v in A.GOLD3.items()}}
    (out / 'build_meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')
    return res


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--proposal', choices=PROPOSALS)
    a = ap.parse_args(); build(a.source, a.out, a.proposal); print('ok')

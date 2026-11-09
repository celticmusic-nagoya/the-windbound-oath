#!/usr/bin/env python3
"""MORWEN-PIXEL-70: motion polish + dot finishing on top of MORWEN-PIXEL-68.

Scope (agreed 2026-11-09): no new body/chest motion. Only
  * easing: plan B = keep the 6-frame timing, hold the peak of the heavy mantle
    in the pixel layout (constant change, replaces 68's mantle table, not added to it);
  * dot finishing of the legs so they sit with the upper body: lit-side outline in a
    material mid-dark (sel-out like the upper body), reflected cape light (rim) on the
    back edge, palette snapped to the 65B upper body; black-purple boots kept;
  * stocking / garter / skin band structure, vest folds, waist chain and plaid unchanged.
Everything else is MORWEN-PIXEL-68 code, reused unchanged (build_morwen68.py).
  python3 build_morwen70.py --source <65B> --out <dir> [--easing A|B]
"""
from pathlib import Path
import argparse, copy, json, math
import numpy as np
import build_morwen66 as B
import build_morwen67 as C
import build_morwen68 as D

# ---------------- constants changed in 70 ----------------
MOTION_68 = copy.deepcopy(D.SECONDARY_MOTION)
EASING_B = {   # only the mantle changes; light parts already hold their peak in absolute terms (body bob + lag 1)
    'mantle': dict(max_offset_px=2, phase_lag=1, dy=[0, 0, 1, 0, 0, 1], dx=[-1, -2, -2, -1, -2, -2],
                   note='ease: reaches the trailing peak one frame after the push and holds it for 2 frames'),
}
EASING_C_WEIGHTS = [1, 1.25, 0.75, 1, 1.25, 0.75]   # display-time weights from the user's timing prototype

RIM_DESIGN = {'boot': (132, 44, 120), 'stock': (104, 34, 96), 'boot_far': (92, 30, 88), 'stock_far': (74, 24, 70)}
SOFT_OUTLINE = True       # lit-side outline uses the material's 2nd tone (near leg only)


def _snap(c, cols):
    d = np.sqrt(((cols - np.array(c)) ** 2 * np.array([0.30, 0.59, 0.11]) * 3).sum(1)); i = int(d.argmin())
    return tuple(int(v) for v in cols[i]) if d[i] <= 14 else tuple(c)


_shade68 = D.shade68
_RIM = {}


def shade70(lab, geo, pal, far, front_mask, swing):
    S, Bo, info = _shade68(lab, geo, pal, far, front_mask, swing)
    k = geo['k']; L = geo['leg']
    h, w = lab.shape
    yy, xx = np.mgrid[0:h, 0:w]; cx, cy = xx + 0.5, yy + 0.5

    def un(p, q, r):
        vx, vy = q[0] - p[0], q[1] - p[1]; n = math.hypot(vx, vy)
        nx, ny = vy / n, -vx / n
        if nx < 0: nx, ny = -nx, -ny
        return np.clip(((cx - p[0]) * nx + (cy - p[1]) * ny) / r, -1.5, 1.5)
    u_th = un(L['hip'], L['knee'], D.R_KNEE * k); u_sh = un(L['knee'], L['ankle'], 4.8 * k)
    allm = lab != 0
    def edge_of(m):
        e = np.zeros_like(m)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = np.zeros_like(m)
            ys0, ys1 = max(0, dy), h + min(0, dy); xs0, xs1 = max(0, dx), w + min(0, dx)
            nb[ys0:ys1, xs0:xs1] = m[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
            e |= m & ~nb
        return e
    edge = edge_of(allm)
    inner = edge_of(allm & ~edge)                  # first ring inside the outline
    stock = lab == D.ST; shaft_ = None  # welt/skin/garter = costume structure, untouched
    shaft = np.isin(lab, (D.BT, D.CUFF))
    gold = lambda img: (img[:, :, 0] > 170) & (img[:, :, 2] < 90)
    big = k >= 1
    # 1) lit-side outline: material 2nd tone instead of the darkest (near leg), like the upper body's coloured line
    if SOFT_OUTLINE and not far and big:
        st, bt = pal['stock'], pal['boot']
        m = edge & stock & (u_th > 0.35) & ~gold(S); S[m] = (*st[1], 255)
        m = edge & shaft & (u_sh > 0.35) & ~gold(Bo); Bo[m] = (*bt[1], 255)
    # 2) reflected cape light on the back edge (one ring inside the outline), shaft + thigh only
    rb = _RIM['boot_far' if far else 'boot']; rs = _RIM['stock_far' if far else 'stock']
    m = inner & shaft & (u_sh < -0.45) & ~gold(Bo) & (Bo[:, :, 3] > 0)
    if big or not far:
        Bo[m] = (*rb, 255)
    m = inner & (lab == D.ST) & (u_th < -0.45) & (S[:, :, 3] > 0) & ~gold(S)
    if big:
        S[m] = (*rs, 255)
    return S, Bo, info


def configure(easing, ref_front):
    cols = np.unique(ref_front[ref_front[:, :, 3] > 0][:, :3], axis=0).astype(int)
    _RIM.clear(); _RIM.update({k: _snap(v, cols) for k, v in RIM_DESIGN.items()})
    D.SECONDARY_MOTION = copy.deepcopy(MOTION_68)
    if easing == 'B':
        for k, v in EASING_B.items():
            D.SECONDARY_MOTION[k] = {kk: vv for kk, vv in v.items() if kk != 'note'}
    D.shade68 = shade70


def build(source: Path, out: Path, easing='B'):
    ref, _ = B.load_reference(source / 'morwen_right_walk_00_96x128.png')
    uf, ub, _ = B.split_layers(ref)
    configure(easing, uf)
    res = D.build(source, out)
    meta = json.loads((out / 'build_meta.json').read_text())
    meta['morwen70'] = {'easing': easing, 'easing_B': EASING_B, 'easing_C_weights': EASING_C_WEIGHTS,
                        'rim_palette_snapped': {k: list(v) for k, v in _RIM.items()}, 'soft_outline': SOFT_OUTLINE,
                        'motion_68_reference': MOTION_68}
    (out / 'build_meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')
    D.shade68 = _shade68
    return res


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--easing', choices=('A', 'B'), default='B')
    a = ap.parse_args(); build(a.source, a.out, a.easing); print('ok')

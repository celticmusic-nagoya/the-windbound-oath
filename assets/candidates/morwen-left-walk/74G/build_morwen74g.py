#!/usr/bin/env python3
"""ART-74G: final art pass on ART-74F-C (12 frames; motion, timing, design unchanged).

1. Stable seam rows: 74F stretched / dropped the row where the neck and waist ramps crossed 0.5, which moved between
   frames and duplicated gold rows (gold flicker). 74G uses ONE fixed switch row per band for every frame, chosen
   in the 74E reference as the row with the fewest gold and edge pixels (neck band 50-58, waist band 78-86).
2. 1-px clean-up on the finished 96 and 48 frames: an opaque pixel whose four opaque neighbours all differ from it
   and agree among themselves (>= 3) takes that neighbour colour. Not touched: face / glasses / eyes box and the
   earring (design detail), gold dots on the boots (official eyelets), anything on the silhouette edge (alpha and
   outline unchanged).
  python3 build_morwen74g.py --ref74c ../74C/REFERENCE_left_side_edit_right_coords.png --source ../74A/source_65B_F00 --out <dir>
"""
import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_PIPE = _os.environ.get('MORWEN72_PIPELINE', _os.path.join(_HERE, '..', '..', 'morwen-right-walk', '72'))
_F74 = _os.environ.get('MORWEN74F_DIR', _os.path.join(_HERE, '..', '74F'))
_E74 = _os.environ.get('MORWEN74E_DIR', _os.path.join(_HERE, '..', '74E'))
_D74 = _os.environ.get('MORWEN74D_DIR', _os.path.join(_HERE, '..', '74D'))
_C74 = _os.environ.get('MORWEN74C_DIR', _os.path.join(_HERE, '..', '74C'))
_B74 = _os.environ.get('MORWEN74B_DIR', _os.path.join(_HERE, '..', '74B'))
_sys.path[:0] = [_HERE, _F74, _E74, _D74, _C74, _B74, _PIPE]
import argparse, json, shutil
from pathlib import Path
import numpy as np
from PIL import Image
import build_morwen66 as B
import build_morwen74f as F
from parts74d import part_masks, EYE_BOX, EAR_BOX
from recolor74d import recolor

H, W, NF = 128, 96, 12


def gold_mask(img):
    r, g, b = (img[:, :, i].astype(int) for i in range(3))
    return (r > 150) & (g > 90) & (b < 120) & (r > g) & (g > b) & (img[:, :, 3] > 0)


def pick_switch_rows(ref):
    """per band: the row whose gold + horizontal-edge content is smallest (duplicating / dropping it is least visible)."""
    a = ref[:, :, 3] > 0; gm = gold_mask(ref)
    lum = ref[:, :, :3].astype(int).sum(2)
    edge = np.zeros((H, W), bool); edge[1:] = np.abs(lum[1:] - lum[:-1]) > 90
    score = lambda y: int(gm[y].sum()) * 3 + int((edge[y] & a[y]).sum())
    rows = {}
    for name, (lo, hi) in (('neck', F.NECK), ('waist', F.WAIST)):
        cand = list(range(lo + 1, hi + 1))
        rows[name] = min(cand, key=lambda y: (score(y), abs(y - (lo + hi) / 2)))
        rows[name + '_score'] = {y: score(y) for y in cand}
    return rows


SW = {}


def row_offsets_g(f):
    """step (not ramp) offsets at the fixed switch rows; same levels as 74F-C."""
    y = np.arange(H)
    hd, cs, p = F.HD[f], F.CST[f], F.P_LEVEL[f]
    oy = np.where(y < SW['neck'], hd, np.where(y < SW['waist'], cs, p))
    ox = np.where(y < SW['waist'], 0, F.PDX[f])
    return oy.astype(int), ox.astype(int)


def u48_stable(U, f):
    """48x64 layers sampled from the UNSHIFTED 96 layers on a fixed (odd) row/column grid, then moved by whole 48 px:
    oy48 = (oy96 + 1) // 2 (1 px down at 96 -> 1 px at 48, 1 px up -> 0). The sampled rows stay the same relative to
    the body in every frame, so gold lines no longer appear / vanish with the 1 px level changes."""
    oy, ox = row_offsets_g(f)
    out = {}
    for k_, v in U.items():
        small = v[1::2, 1::2]
        h2, w2 = small.shape[:2]
        o = np.zeros_like(small)
        for y in range(h2):
            dy = (oy[2 * y + 1] + 1) // 2; dx = (ox[2 * y + 1] + 1) // 2
            sy = y - dy
            if not (0 <= sy < h2): continue
            if dx >= 0: o[y, dx:] = small[sy, :w2 - dx]
            else: o[y, :w2 + dx] = small[sy, -dx:]
        out[k_] = o
    return out


def patch_run_variant():
    import inspect, textwrap
    src = textwrap.dedent(inspect.getsource(F.run_variant))
    old = "U48 = {k: v[1::2, 1::2].copy() for k, v in U96.items()}"
    assert old in src
    src = src.replace(old, "U48 = U48_FN(U, f)")
    F.U48_FN = u48_stable
    exec(compile(src, F.__file__, 'exec'), F.__dict__)


def protect_mask(h, w, k):
    """left-view coordinates: eye / glasses box and earring (mirrored from the right-view boxes, +-1 row for the bob),
    plus the boot rows for gold dots (handled by colour)."""
    m = np.zeros((h, w), bool)
    for x0, y0, x1, y1 in (EYE_BOX, EAR_BOX):
        lx0, lx1 = 95 - x1, 95 - x0
        m[max(0, int((y0 - 1) * k)):int((y1 + 2) * k), max(0, int(lx0 * k)):int((lx1 + 1) * k)] = True
    return m


def clean_islands(img, k):
    h, w = img.shape[:2]; op = img[:, :, 3] > 0; c = img[:, :, :3].astype(int)
    prot = protect_mask(h, w, k); gm = gold_mask(img); yy = np.mgrid[0:h, 0:w][0]
    out = img.copy(); n = 0
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if not op[y, x] or prot[y, x]: continue
            if gm[y, x] and y >= int(100 * k): continue           # boot eyelets
            nbp = [(y + dy, x + dx) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            if not all(op[p] for p in nbp): continue               # silhouette edge: keep
            nb = [tuple(c[p]) for p in nbp]
            me = tuple(c[y, x])
            if me in nb: continue
            best = max(set(nb), key=nb.count)
            if nb.count(best) >= 3:
                out[y, x, :3] = best; n += 1
    return out, n


def build(ref74c_path, source, out):
    F.E74.patch_x()
    out.mkdir(parents=True, exist_ok=True)
    w = out / '_work'
    if w.exists(): shutil.rmtree(w)
    ref74c, _ = B.load_reference(ref74c_path)
    full74c = np.array(Image.open(ref74c_path).convert('RGBA'))
    uf, ub, _ = B.split_layers(ref74c)
    parts, keep = part_masks(F.X.region_masks8(uf, ub), uf[:, :, 3] > 0, ub[:, :, 3] > 0)
    full74d, _ = recolor(full74c, parts, keep)
    full74e, _, _ = F.E74.add_rim(full74d, parts)
    rows = pick_switch_rows(full74e); SW.update(rows)
    refdir = w / 'ref'; refdir.mkdir(parents=True)
    Image.fromarray(full74e, 'RGBA').save(refdir / 'morwen_right_walk_00_96x128.png')
    ref74e, _ = B.load_reference(refdir / 'morwen_right_walk_00_96x128.png')
    o_ro, o_rv = F.row_offsets, F.run_variant
    F.row_offsets = row_offsets_g; patch_run_variant()
    try:
        meta = F.run_variant(ref74e, ref74c, source, w / 'C', 'C')
    finally:
        F.row_offsets, F.run_variant = o_ro, o_rv
    clean = {}
    for f in range(NF):
        for s, k in (('96x128', 1.0), ('48x64', 0.5)):
            im = np.array(Image.open(w / 'C' / f'morwen_right_walk_{f:02d}_{s}.png').convert('RGBA'))[:, ::-1].copy()   # mirror -> left
            im, n = clean_islands(im, k); clean[f'{f:02d}_{s}'] = n
            Image.fromarray(im, 'RGBA').save(out / f'morwen_left_walk_74G_12f_{f:02d}_{s}.png')
    m = {'base': 'ART-74F-C (motion / timing / design identical)', 'switch_rows': {k: v for k, v in rows.items()},
         'levels': {'pelvis_dy': F.P_LEVEL, 'chest_dy': F.CST, 'head_dy': F.HD, 'pelvis_dx': F.PDX},
         'islands_cleaned': clean, 'C': meta}
    (out / 'build_meta_74g.json').write_text(json.dumps(m, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    shutil.rmtree(w)
    return m


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref74c', type=Path, required=True); ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(); m = build(a.ref74c, a.source, a.out); print('ok', m['switch_rows']['neck'], m['switch_rows']['waist'], sum(m['islands_cleaned'].values()))

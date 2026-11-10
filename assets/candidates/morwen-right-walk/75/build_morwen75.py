#!/usr/bin/env python3
"""MORWEN-WALK-RIGHT-75: right walk, 12 frames, rebuilt on the ART-74G pipeline from the RIGHT design (not a mirror).

Design source: right walk 72 F00 (right-view art: hat flower + ribbon on the hat's back side, hat-tip jewel, satchel on
the near hip, shoulder crest, gold glasses). Checked against the official right profile
(assets/official/characters/morwen/turnaround/, SHA-256 7eeff76a...). Nothing is removed or added.

Same as the left 74G (shared rhythm, scale, ground row, palette):
  - 74D part-wise official colour (same OKLab targets as the left) + short boots / knee socks
  - 74E video-derived gait (stance 0.66, 41.6 px / cycle at 96, pivot correction), rim light
  - 74F-C phase lags (pelvis -> chest -> head, PDX, hand split) and cloth secondary motion
  - 74G fixed seam rows, stable 48 sampling, 1-px island clean-up
Right-only parts (kept out of the shared part recolor, mapped to their own official right-profile targets):
  - satchel leather -> official brown (gold buckle / clasp kept as gold)
  - hat flower, hanging ribbons and hat-tip crystal -> official violet (not magenta); flower centre gold kept
Output: morwen_right_walk_75_12f_{00..11}_{96x128,48x64}.png (right-facing, no mirror).
  python3 build_morwen75.py --ref ../72/morwen_right_walk_00_96x128.png --source ../../morwen-left-walk/74A/source_65B_F00 --out <dir>
"""
import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_LEFT = _os.environ.get('MORWEN_LEFT_DIR', _os.path.join(_HERE, '..', '..', 'morwen-left-walk'))
_G74 = _os.environ.get('MORWEN74G_DIR', _os.path.join(_LEFT, '74G'))
_os.environ.setdefault('MORWEN74F_DIR', _os.path.join(_LEFT, '74F'))
_os.environ.setdefault('MORWEN74E_DIR', _os.path.join(_LEFT, '74E'))
_os.environ.setdefault('MORWEN74D_DIR', _os.path.join(_LEFT, '74D'))
_os.environ.setdefault('MORWEN74C_DIR', _os.path.join(_LEFT, '74C'))
_os.environ.setdefault('MORWEN74B_DIR', _os.path.join(_LEFT, '74B'))
_os.environ.setdefault('MORWEN72_PIPELINE', _os.path.join(_HERE, '..', '72'))
_sys.path[:0] = [_HERE, _G74]
import argparse, json, shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import build_morwen74g as G
from build_morwen74g import B, F, part_masks, recolor, EYE_BOX, EAR_BOX
from oklab import rgb2oklab, oklab2rgb, lch
from recolor74d import qmap, circ_mean

H, W, NF = 128, 96, 12
# official right profile (1024x1536), OKLab, measured with official_stats75() (boxes there)
OFFICIAL_R = {
    'bag':    dict(L=[0.26, 0.36, 0.45, 0.55, 0.70], C=0.070, h=38),     # measured L .29/.46/.56/.67/.81 incl. highlights; sprite reads darker
    'violet': dict(L=[0.33, 0.44, 0.53, 0.64, 0.80], C=0.150, h=313),    # ribbon .20/.33/.44/.53/.67 C .154 h 314; petals lighter
}
FLOWER_POLY = [(26, 10), (57, 10), (57, 29), (45, 33), (41, 57), (27, 57), (25, 30)]
JEWEL_BOX = (17, 22, 27, 38)
BAG_BOX = (33, 73, 54, 93)


def poly(p):
    im = Image.new('L', (W, H), 0); ImageDraw.Draw(im).polygon(p, fill=1); return np.array(im) > 0


def box(b):
    yy, xx = np.mgrid[0:H, 0:W]; return (xx >= b[0]) & (xx <= b[2]) & (yy >= b[1]) & (yy <= b[3])


def right_parts(ref):
    """satchel leather and flower / ribbon / crystal masks on the right reference (right-view coords)."""
    op = ref[:, :, 3] > 0
    r, g, b = (ref[:, :, i].astype(float) for i in range(3))
    L, C, h = lch(rgb2oklab(ref[:, :, :3].astype(float)))
    goldlike = (g / np.maximum(r, 1) > 0.62) & (r > 150) & (b < 120)
    bag = box(BAG_BOX) & op & (h > 15) & (h < 85) & (r > g) & (g > b) & ~goldlike & (L > 0.25)
    pink = ((h > 285) | (h < 20)) & (L > 0.50) & (C > 0.05)
    light = (L > 0.80) & ~goldlike
    flower = (poly(FLOWER_POLY) | box(JEWEL_BOX)) & op & (pink | light)
    return bag, flower


def map_part(out, src, m, tgt, hue_keep=0.35, cmin=0.0):
    if not m.any(): return {}
    L, C, h = lch(rgb2oklab(src[m, :3].astype(float)))
    sq = np.percentile(L, [5, 25, 50, 75, 95]); sC = float(np.median(C)); sh = circ_mean(h)
    L2 = qmap(L, sq, tgt['L']); k = float(np.clip(tgt['C'] / max(sC, 1e-4), 0.2, 1.4)); C2 = C * k
    C2 = np.maximum(C2, np.where(L2 > 0.5, cmin, 0))     # light petals keep a violet tint (official), not grey
    dh = ((h - sh + 180) % 360) - 180; h2 = (tgt['h'] + hue_keep * dh) % 360
    out[m, :3] = oklab2rgb(np.stack([L2, C2 * np.cos(np.radians(h2)), C2 * np.sin(np.radians(h2))], -1))
    return dict(px=int(m.sum()), src_L=[round(float(v), 3) for v in sq], src_C=round(sC, 3), src_h=round(sh, 1), chroma_scale=round(k, 3))


def protect_mask_right(h, w, k):
    m = np.zeros((h, w), bool)
    for x0, y0, x1, y1 in (EYE_BOX, EAR_BOX):
        m[max(0, int((y0 - 1) * k)):int((y1 + 2) * k), max(0, int(x0 * k)):int((x1 + 1) * k)] = True
    return m


def build(ref_path, source, out):
    F.E74.patch_x()
    out.mkdir(parents=True, exist_ok=True)
    w = out / '_work'
    if w.exists(): shutil.rmtree(w)
    ref, _ = B.load_reference(ref_path)
    full = np.array(Image.open(ref_path).convert('RGBA'))
    uf, ub, _ = B.split_layers(ref)
    parts, keep = part_masks(F.X.region_masks8(uf, ub), uf[:, :, 3] > 0, ub[:, :, 3] > 0)
    bag, flower = right_parts(full)
    full_d, log = recolor(full, parts, keep | bag | flower)
    log['bag'] = map_part(full_d, full, bag, OFFICIAL_R['bag'])
    log['flower_ribbon_crystal'] = map_part(full_d, full, flower, OFFICIAL_R['violet'], cmin=0.075)
    full_e, _, _ = F.E74.add_rim(full_d, parts)
    rows = G.pick_switch_rows(full_e); G.SW.update(rows)
    refdir = w / 'ref'; refdir.mkdir(parents=True)
    Image.fromarray(full_e, 'RGBA').save(refdir / 'morwen_right_walk_00_96x128.png')
    Image.fromarray(full_e, 'RGBA').save(out / 'REFERENCE_right_75_colour.png')
    ref_e, _ = B.load_reference(refdir / 'morwen_right_walk_00_96x128.png')
    o_ro, o_rv, o_pm = F.row_offsets, F.run_variant, G.protect_mask
    F.row_offsets = G.row_offsets_g; G.patch_run_variant(); G.protect_mask = protect_mask_right
    try:
        meta = F.run_variant(ref_e, ref, source, w / 'C', 'C')
        clean = {}
        for f in range(NF):
            for s, k in (('96x128', 1.0), ('48x64', 0.5)):
                im = np.array(Image.open(w / 'C' / f'morwen_right_walk_{f:02d}_{s}.png').convert('RGBA'))   # right-facing, no mirror
                im, n = G.clean_islands(im, k); clean[f'{f:02d}_{s}'] = n
                Image.fromarray(im, 'RGBA').save(out / f'morwen_right_walk_75_12f_{f:02d}_{s}.png')
    finally:
        F.row_offsets, F.run_variant, G.protect_mask = o_ro, o_rv, o_pm
    m = {'task': 'MORWEN-WALK-RIGHT-75', 'design_source': str(Path(ref_path).name), 'pipeline': 'ART-74G (shared with left)',
         'switch_rows': rows, 'recolor': log, 'right_part_px': {'bag': int(bag.sum()), 'flower_ribbon_crystal': int(flower.sum())},
         'islands_cleaned': clean, 'C': meta}
    (out / 'build_meta_75.json').write_text(json.dumps(m, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    shutil.rmtree(w)
    return m


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref', type=Path, required=True); ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(); m = build(a.ref, a.source, a.out)
    print('ok', m['switch_rows']['neck'], m['switch_rows']['waist'], sum(m['islands_cleaned'].values()), m['right_part_px'])

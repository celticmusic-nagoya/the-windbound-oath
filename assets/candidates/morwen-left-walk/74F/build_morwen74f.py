#!/usr/bin/env python3
"""ART-74F: 12-frame elegant-walk refinement on ART-74E (12f). Two candidates, same cycle / speed as 74E:

  B  phase offsets only: pelvis (lower body) / chest / head levels with timing differences, pelvis fore-aft 1 px,
     shoulder (capelet) counter-motion one frame late. Legs, arm, cloth tables = 74E.
  C  B + toe push held through F08 (toe-off at t 0.675), per-part secondary phases (collar 1 f, potions 1 f, hair 1.5 f,
     mantle 2 f / longer), hand + cuff 0.5 f behind the forearm (arm lead over the legs kept), skirt hem follows the
     pelvis 1 f late.

How the body levels are drawn without tearing the sprite: one per-row offset map is applied to every upper layer
(same map for all layers -> no gaps between layers):
   rows <= 50 (head)          : head level  Hd
   rows 50..58 (neck->chest)  : ramp Hd -> chest level Cst   (1 row stretched / dropped inside the neck band)
   rows 58..78 (chest/waist)  : Cst
   rows 78..86 (waist->hips)  : ramp Cst -> pelvis level P
   rows >= 86 (skirt, hips)   : P ; the legs use the same P for the hip joint
and horizontally rows 78..86 ramp 0 -> pelvis fore-aft Pdx (skirt / hips), legs hip x + Pdx.
Levels (12f, +1 = 1 px down, 74E video phase: lowest heel strike..loading, highest mid-stance):
   P   = [+1,+1, 0,-1,-1, 0] x2      (director table shifted 1 frame earlier to match the measured video phase)
   Cst = P one frame later
   Hd  = 1 only when the chest has been down for 2 frames (0.5-frame posture correction, head moves 2/12 frames)
  python3 build_morwen74f.py --ref74c ../74C/REFERENCE_left_side_edit_right_coords.png --source ../74A/source_65B_F00 --out <dir>
"""
import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_PIPE = _os.environ.get('MORWEN72_PIPELINE', _os.path.join(_HERE, '..', '..', 'morwen-right-walk', '72'))
_E74 = _os.environ.get('MORWEN74E_DIR', _os.path.join(_HERE, '..', '74E'))
_D74 = _os.environ.get('MORWEN74D_DIR', _os.path.join(_HERE, '..', '74D'))
_C74 = _os.environ.get('MORWEN74C_DIR', _os.path.join(_HERE, '..', '74C'))
_B74 = _os.environ.get('MORWEN74B_DIR', _os.path.join(_HERE, '..', '74B'))
_sys.path[:0] = [_HERE, _E74, _D74, _C74, _B74, _PIPE]
import argparse, copy, json, math, shutil
from pathlib import Path
import numpy as np
from PIL import Image
import build_morwen66 as B, build_morwen68 as D, build_morwen70 as E, build_morwen70art as A
import build_morwen71 as M
import build_morwen74e as E74
from parts74d import part_masks
from recolor74d import recolor

H, W = 128, 96
NF = 12
X = E74.X
P_LEVEL = [1, 1, 0, -1, -1, 0] * 2
NECK = (50, 58); WAIST = (78, 86)
PDX = [0, 0, 0, 1, 1, 0] * 2              # pelvis forward 1 px at mid / terminal stance (push), neutral at contact


def lagged(seq, k): n = len(seq); return [seq[(i - k) % n] for i in range(n)]


CST = lagged(P_LEVEL, 1)
HD = [1 if (CST[i] == 1 and CST[i - 1] == 1) else 0 for i in range(NF)]


def ramp(y, a, b): return np.clip((y - a) / float(b - a), 0.0, 1.0)


def row_offsets(f):
    y = np.arange(H, dtype=float)
    hd, cs, p = HD[f], CST[f], P_LEVEL[f]
    oy = hd + (cs - hd) * ramp(y, *NECK) + (p - cs) * ramp(y, *WAIST)
    ox = PDX[f] * ramp(y, *WAIST)
    return np.rint(oy).astype(int), np.rint(ox).astype(int)


def rowmap(layer, oy, ox):
    """backward per-row mapping: out[y, x] = in[y - oy[y], x - ox[y]] (same map for every layer -> no seams)."""
    out = np.zeros_like(layer)
    for y in range(H):
        sy = y - oy[y]
        if not (0 <= sy < H): continue
        s = ox[y]
        if s >= 0: out[y, s:] = layer[sy, :W - s]
        else: out[y, :W + s] = layer[sy, -s:]
    return out


def tables_f(variant):
    T = E74.tables(NF)
    ts = T['t']
    T['bob'] = list(P_LEVEL)          # hip joint level for the legs (compose68 uses D.BOB)
    mo = T['motion']
    # shoulder (capelet) counter-motion: opposite to the pelvis fore-aft, one frame later (B and C)
    mo['cape_front'] = dict(mo['cape_front']); mo['cape_front']['dx'] = [-v for v in lagged(PDX, 1)]
    if variant == 'C':
        low = [1 if v == 1 else 0 for v in P_LEVEL]        # pelvis low -> cloth drop
        mo['collar_ribbon'] = dict(max_offset_px=1, phase_lag='1f', dy=lagged(low, 1), dx=[-v for v in lagged(low, 1)])
        mo['potions'] = dict(max_offset_px=1, phase_lag='1f', dy=lagged(low, 1), dx=[0] * NF)   # dx would open holes (nothing behind the potions)
        mo['hair_tips'] = dict(max_offset_px=1, phase_lag='1.5f', dy=[1 if (lagged(low, 1)[i] and lagged(low, 2)[i]) else 0 for i in range(NF)], dx=[0] * NF)
        mo['mantle'] = dict(max_offset_px=2, phase_lag='2f', dy=[1 if (lagged(low, 2)[i] or lagged(low, 3)[i]) else 0 for i in range(NF)],
                            dx=[-2 if v else -1 for v in lagged(PDX, 2)])
        mo['hand'] = dict(max_offset_px=2, phase_lag='0.5f behind forearm', dy=[0] * NF,
                          dx=[E74.arm_dx(t - 1.0 / 24) for t in ts])
        T['skirt'] = [-1 if v else 0 for v in lagged(low, 1)]
    return T


def run_variant(ref74e, ref74c, source, out, variant, level='C'):
    out.mkdir(parents=True, exist_ok=True)
    oref, _ = B.load_reference(source / 'morwen_right_walk_00_96x128.png'); ouf, _, _ = B.split_layers(oref)
    pal = copy.deepcopy(D.build_palette68(ouf)[0]); pal.update({k: list(v) for k, v in E74.P74D.LEG_RAMPS.items()})
    uf, ub, _ = B.split_layers(ref74e); cuf, cub, _ = B.split_layers(ref74c)
    A.GOLD3.clear(); A.GOLD3.update(E74.P74D.GOLD3_74D); A.ART['level'] = level
    E.configure('B', ouf); E._RIM.clear(); E._RIM.update(E74.P74D.RIM_74D)
    o_toff = E74.T_OFF
    if variant == 'C': E74.T_OFF = 0.675        # toe keeps pushing through F08 (t 0.667)
    X.CUR['nf'] = NF; T = tables_f(variant)
    D.SECONDARY_MOTION = copy.deepcopy(T['motion'])
    M.STATE['proposal'] = 'GLASSES'
    D.shade68 = M.shade71; D.compose68 = M.compose71
    o_r = D.rasterise68; D.rasterise68 = E74.P74D.rasterise74d
    saved = X.setup_motion(T)
    B.BOB = list(HD)                               # glasses region follows the head level
    o_solve = B.solve_leg
    def solve_f(hip_x, hip_y, phase):              # pelvis fore-aft for both hips
        return o_solve(hip_x + PDX[X.CUR['f']], hip_y, phase)
    B.solve_leg = solve_f
    o_ul, o_rm = D.upper_layers, D.region_masks
    if variant == 'C':
        def rm_c(uf_, ub_):
            m = o_rm(uf_, ub_); yy = np.mgrid[0:H, 0:W][0]
            m['hand'] = m['arm'] & (yy >= 75); m['arm'] = m['arm'] & (yy < 75); return m
        def ul_c(f, ref_front, ub_, masks):
            L, foot = o_ul(f, ref_front, ub_, masks)
            fa = (ref_front[:, :, 3] > 0) | (ub_[:, :, 3] > 0); sm = D.SECONDARY_MOTION['hand']
            L['hand'], foot['hand'] = D.warp(ref_front, masks['hand'], D.weight('hand'), sm['dx'][f], sm['dy'][f], fa)
            return L, foot
        D.region_masks, D.upper_layers = rm_c, ul_c
        D.ANCHORS['hand'] = (46, 72, 6.0); D.Z.insert(D.Z.index('arm') + 1, 'hand')
    o_skl = D.C.draw_skirt_left
    def skl_f(pal_, sway, bob, k=1.0):
        # pelvis raised (bob -1): the rear pleat panel's fixed top row (84) would leave a 1-row gap under the
        # raised skirt layer -> extend the panel up by the same amount (copy of its own top row)
        out_ = o_skl(pal_, sway, bob, k)
        if bob < 0:
            top = int(84 * k)
            for dy in range(1, -bob + 1):
                row = out_[top].copy(); m = row[:, 3] > 0
                out_[top - dy][m] = row[m]
        return out_
    D.C.draw_skirt_left = skl_f
    logs = []
    try:
        masks = D.region_masks(cuf, cub)
        for f in range(NF):
            X.CUR['f'] = f
            U, foot = D.upper_layers(f, uf, ub, masks)
            oy, ox = row_offsets(f)
            U96 = {k: rowmap(v, oy, ox) for k, v in U.items()}
            img, layers, legs = D.compose68(f, U96, pal, 1.0)
            U48 = {k: v[1::2, 1::2].copy() for k, v in U96.items()}
            sm, _, _ = D.compose68(f, U48, pal, 0.5)
            r96 = E74.leg_rim(img, 1.0); r48 = E74.leg_rim(sm, 0.5)
            Image.fromarray(img, 'RGBA').save(out / f'morwen_right_walk_{f:02d}_96x128.png')
            Image.fromarray(sm, 'RGBA').save(out / f'morwen_right_walk_{f:02d}_48x64.png')
            t = T['t'][f]
            logs.append({'frame': f, 't': round(t, 4), 'pelvis_dy': P_LEVEL[f], 'chest_dy': CST[f], 'head_dy': HD[f], 'pelvis_dx': PDX[f],
                         'near': X.pivot_corrected(X.tf(f)), 'far': X.pivot_corrected(X.tf(f, True)),
                         'near_role': E74.role_at(t), 'far_role': E74.role_at((t + 0.5) % 1),
                         'secondary': {n: {'dx': T['motion'][n]['dx'][f], 'dy': T['motion'][n]['dy'][f]} for n in T['motion']},
                         'skirt_sway': T['skirt'][f], 'leg_rim_px': [r96, r48]})
    finally:
        D.region_masks, D.upper_layers = o_rm, o_ul; D.C.draw_skirt_left = o_skl
        X.restore(saved)
        D.rasterise68 = o_r; D.shade68 = E._shade68; D.compose68 = A._compose68; M.STATE['proposal'] = None; A.ART['level'] = 'B'
        E74.T_OFF = o_toff
    return {'variant': variant, 'frames': logs, 'toe_off_t': 0.675 if variant == 'C' else o_toff,
            'ground_speed_px_per_cycle': {'96x128': 4 * E74.S, '48x64': 2 * E74.S},
            'ground_speed_px_per_frame': {'96x128': round(4 * E74.S / NF, 4), '48x64': round(2 * E74.S / NF, 4)}}


def build(ref74c_path, source, out):
    E74.patch_x()
    out.mkdir(parents=True, exist_ok=True)
    w = out / '_work'
    if w.exists(): shutil.rmtree(w)
    ref74c, _ = B.load_reference(ref74c_path)
    full74c = np.array(Image.open(ref74c_path).convert('RGBA'))
    uf, ub, _ = B.split_layers(ref74c)
    parts, keep = part_masks(X.region_masks8(uf, ub), uf[:, :, 3] > 0, ub[:, :, 3] > 0)
    full74d, _ = recolor(full74c, parts, keep)
    full74e, rim_px, rim_col = E74.add_rim(full74d, parts)        # = the 74E reference (design unchanged)
    refdir = w / 'ref'; refdir.mkdir(parents=True)
    Image.fromarray(full74e, 'RGBA').save(refdir / 'morwen_right_walk_00_96x128.png')
    ref74e, _ = B.load_reference(refdir / 'morwen_right_walk_00_96x128.png')
    metas = {}
    for v in ('B', 'C'):
        metas[v] = run_variant(ref74e, ref74c, source, w / v, v)
        for f in range(NF):
            for s in ('96x128', '48x64'):
                Image.open(w / v / f'morwen_right_walk_{f:02d}_{s}.png').transpose(Image.FLIP_LEFT_RIGHT).save(out / f'morwen_left_walk_74F{v}_12f_{f:02d}_{s}.png')
    meta = {'base': 'ART-74E 12f (design identical, reference = 74E reference)', 'levels': {'pelvis_dy': P_LEVEL, 'chest_dy': CST, 'head_dy': HD, 'pelvis_dx': PDX},
            'row_map': {'neck_ramp_rows': NECK, 'waist_ramp_rows': WAIST}, 'B': metas['B'], 'C': metas['C']}
    (out / 'build_meta_74f.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')
    shutil.rmtree(w)
    return meta


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref74c', type=Path, required=True); ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(); build(a.ref74c, a.source, a.out); print('ok')

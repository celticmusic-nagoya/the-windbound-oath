#!/usr/bin/env python3
"""ART-74E: video-analysed walk on the ART-74D design.

Source of motion: VIDEO_ANALYSIS_74E.json (standard-walk grid-overlay video, side view, one full cycle f134-f240,
manual keypoints on 9 frames + automatic silhouette series). Video values are scaled to Morwen's 2.8-head field
sprite (hip->ankle 31 px at 96 px) with a stride restraint factor STRIDE_K; the design of ART-74D (colours, short boots,
knee socks, no unofficial ornaments) is reused unchanged except a minimal lit-side rim on the hat / mantle silhouette
(dark-background readability) and the level-C gold / 1-px clean-up of the head, torso and skirt layers.

Timing (fraction of the cycle from this leg's heel strike; video): heel strike 0, foot flat 0.07, mid-stance 0.25,
heel rise 0.43, opposite heel strike 0.5, toe-off 0.66 (stance 66 %, double support 16 % each), initial swing 0.69,
mid swing 0.75, terminal swing 0.88, reach 0.93. Head lowest from heel strike through loading.
  python3 build_morwen74e.py --ref74c ../74C/REFERENCE_left_side_edit_right_coords.png --source ../74A/source_65B_F00 --out <dir>
"""
import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_PIPE = _os.environ.get('MORWEN72_PIPELINE', _os.path.join(_HERE, '..', '..', 'morwen-right-walk', '72'))
_B74 = _os.environ.get('MORWEN74B_DIR', _os.path.join(_HERE, '..', '74B'))
_C74 = _os.environ.get('MORWEN74C_DIR', _os.path.join(_HERE, '..', '74C'))
_D74 = _os.environ.get('MORWEN74D_DIR', _os.path.join(_HERE, '..', '74D'))
_sys.path[:0] = [_HERE, _D74, _C74, _B74, _PIPE]
import argparse, copy, json, math, shutil
from pathlib import Path
import numpy as np
from PIL import Image
import build_morwen66 as B, build_morwen68 as D, build_morwen70 as E, build_morwen70art as A
import build_morwen71 as M
import build_morwen74c as X
import build_morwen74d as P74D
import build_morwen67 as C67
C_OUTLINE = C67.OUTLINE
from oklab import oklab2rgb, rgb2oklab, lch
from parts74d import part_masks
from recolor74d import recolor

H, W = 128, 96
LEG_L = 31.0          # sprite hip -> ankle (96 px)
STRIDE_K = 0.78       # restraint on the video stride (chibi proportions, elegant / not long-striding)
VIDEO_STANCE_HALF = 0.43   # video ankle reach at heel strike / opposite heel strike, in leg lengths (0.40 / -0.45..-0.51)
S = round(VIDEO_STANCE_HALF * LEG_L * STRIDE_K, 2)          # = 10.4 px
T_OFF = 0.66          # toe-off (video stance share 0.66)
# stance: flat-foot reference travels linearly (no slide) S -> -S over t 0..0.5 and continues to toe-off;
# pitch from the video (heel strike toe-up 19-24 deg, foot flat by 0.07, heel rise from 0.43, -31 at 0.5, -44 at 0.57,
# -75 at 0.62; clamped to -60 at toe-off for the pixel foot)
STANCE_PITCH = [(0.0, 19), (0.07, 0), (0.36, 0), (0.43, -8), (0.50, -28), (0.57, -42), (0.62, -55), (T_OFF, -60)]
# swing: ankle x relative to hip from the video (in L) x STRIDE_K; lift = lowest foot point above ground (video toe
# clearance 12 / 7 / 5 / 3 / 2 px of a 132 px leg -> 2.8 / 1.6 / 1.2 / 0.7 / 0.5 px, rounded up so a swing foot never
# touches early); pitch from the video, foot-hang clamped to -70 for readability
SWING = [  # t, ankle rel hip (L, video), pitch, lift, role
    (0.689, -0.379, -70, 3, 'initial swing'),
    (0.745, -0.254, -50, 2, 'mid swing (passing)'),
    (0.811, -0.013, -25, 1, 'mid-late swing'),
    (0.877, +0.262, +8, 1, 'terminal swing'),
    (0.934, +0.410, +22, 1, 'reach before heel strike'),
]
ROLES = [(0.0, 'heel strike'), (0.04, 'loading'), (0.16, 'mid-stance'), (0.34, 'terminal stance'), (0.46, 'pre-swing / opposite heel strike'),
         (0.58, 'late pre-swing (toe contact)'), (0.66, 'toe-off'), (0.68, 'initial swing'), (0.72, 'mid swing'), (0.80, 'mid-late swing'), (0.86, 'terminal swing'), (0.90, 'reach')]
BOB_WIN = (0.0, 0.12)          # body 1 px lower from heel strike through early loading (video: lowest plateau)
ARM_AMP = 2                    # px at the hand (video wrist +-0.29 L: kept small on purpose, capelet covers the upper arm)
ARM_LEAD = 0.06                # video: the arm reaches its back extreme ~0.06 cycle before the same-side heel strike
PELVIS_ROT_PX, PELVIS_DROP_SWING = 0.6, 0.5


def _interp(keys, t):
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t0 <= t <= t1 + 1e-9:
            return v0 + (v1 - v0) * (t - t0) / max(t1 - t0, 1e-9)
    return keys[-1][1]


def role_at(t):
    r = ROLES[0][1]
    for t0, n in ROLES:
        if t + 1e-9 >= t0: r = n
    return r


def stance_flat_dx(t): return S - 4 * S * t


def _pivot(g):
    poly = B.FOOT_POLY + B.SOLE_POLY + B.HEEL_POLY
    flat = B.foot_points(poly, (0.0, 0.0), 0); tilt = B.foot_points(poly, (0.0, 0.0), g['pitch'])
    fy = max(y for _, y in flat); base = [x for x, y in flat if y >= fy - 1e-6]
    ty = max(y for _, y in tilt); piv = [x for x, y in tilt if y >= ty - 1e-6]
    return (min(base) - min(piv)) if g['pitch'] > 0 else (max(base) - max(piv))


def gait_at(t):
    t = t % 1.0
    if t <= T_OFF + 1e-9:
        return dict(dx=round(stance_flat_dx(t), 3), pitch=round(_interp(STANCE_PITCH, t), 2), lift=0, role=role_at(t))
    off = pivot_corrected(T_OFF)
    keys = [(T_OFF, off['dx'], off['pitch'], 0)] + [(tt, r * LEG_L * STRIDE_K, p, l) for tt, r, p, l, _ in SWING] + \
           [(1.0, S + _pivot(dict(pitch=STANCE_PITCH[0][1])), STANCE_PITCH[0][1], 0)]
    for (t0, d0, p0, l0), (t1, d1, p1, l1) in zip(keys, keys[1:]):
        if t0 <= t <= t1 + 1e-9:
            u = (t - t0) / (t1 - t0)
            # swing ankle path: smooth (cosine) easing between key poses, lift taken as the max of neighbours
            # within the first / last 20 % so the foot never grazes the ground between two lifted keys
            us = 0.5 - 0.5 * math.cos(math.pi * u)
            lift = max(l0, l1) if (l0 > 0 and l1 > 0) else int(round(l0 + (l1 - l0) * u))
            return dict(dx=round(d0 + (d1 - d0) * us, 3), pitch=round(p0 + (p1 - p0) * us, 2), lift=int(lift), role=role_at(t))
    raise ValueError(t)


def pivot_corrected(t):
    g = gait_at(t) if (t % 1.0) > T_OFF + 1e-9 else dict(dx=round(stance_flat_dx(t % 1.0), 3), pitch=round(_interp(STANCE_PITCH, t % 1.0), 2), lift=0, role=role_at(t % 1.0))
    if g['lift'] == 0 and g['pitch'] != 0 and (t % 1.0) <= T_OFF + 1e-9:
        g['dx'] = round(g['dx'] + _pivot(g), 3)
    return g


def inwin(t, a, b): return a <= (t % 0.5) < b


def arm_dx(t):
    return int(round(-ARM_AMP * math.cos(2 * math.pi * (t + ARM_LEAD))))


def tables(nf):
    ts = [f / nf for f in range(nf)]
    bob = [1 if inwin(t, *BOB_WIN) else 0 for t in ts]
    lag = [1 if inwin(t - 0.125, *BOB_WIN) else 0 for t in ts]
    heavy = [1 if inwin(t - 0.125, BOB_WIN[0], BOB_WIN[1] + 0.12) else 0 for t in ts]
    return dict(
        t=ts, bob=bob,
        skirt=[-1 if inwin(t, 0.04, 0.30) else 0 for t in ts],          # hem settles back during loading / mid-stance
        motion={
            'collar_ribbon': dict(max_offset_px=1, phase_lag=0.125, dy=lag, dx=[-v for v in lag]),
            'cape_front':    dict(max_offset_px=1, phase_lag=0.125, dy=lag, dx=[0] * nf),
            'mantle':        dict(max_offset_px=2, phase_lag=0.125, dy=heavy, dx=[-2 if inwin(t, 0.10, 0.36) else -1 for t in ts]),
            'potions':       dict(max_offset_px=1, phase_lag=0.125, dy=lag, dx=[0] * nf),
            'hair_tips':     dict(max_offset_px=1, phase_lag=0.125, dy=lag, dx=[0] * nf),
            'arm':           dict(max_offset_px=ARM_AMP, phase_lag=-ARM_LEAD, dy=[0] * nf, dx=[arm_dx(t) for t in ts]),
        })


def patch_x():
    X.gait_at = gait_at; X.pivot_corrected = pivot_corrected; X.tables = tables; X.arm_dx = arm_dx
    X.PELVIS_ROT_PX = PELVIS_ROT_PX; X.PELVIS_DROP_SWING = PELVIS_DROP_SWING
    X.STRIDE_PX = 2 * S


# ---------------------------------------------------------------- dark-background rim (lit side only)
RIM_PARTS = ('hat', 'mantle')
def add_rim(ref, parts):
    """top / front (light-facing, right coords +x = front) outline pixels of hat and mantle that are almost black
    -> one deep-purple rim tone (OKLab L .34). Other outline pixels stay dark. Returns (ref, px)."""
    out = ref.copy(); a = ref[:, :, 3] > 0
    up = np.zeros_like(a); up[1:] = a[:-1]                     # opaque above?
    rt = np.zeros_like(a); rt[:, :-1] = a[:, 1:]               # opaque to the front?
    edge_top = a & ~up; edge_front = a & ~rt
    L, C, h = lch(rgb2oklab(ref[:, :, :3].astype(float)))
    rim = np.zeros_like(a)
    for n in RIM_PARTS:
        rim |= parts[n] & (edge_top | edge_front) & (L < 0.26)
    col = oklab2rgb(np.array([0.34, 0.09 * math.cos(math.radians(316)), 0.09 * math.sin(math.radians(316))]))
    out[rim, :3] = col
    return out, int(rim.sum()), [int(v) for v in col]


LEG_RIM_ROW = 99      # 96 px rows >= this are legs / boots (below the skirt hem in every frame)
def leg_rim(img, k):
    """front-facing (+x, right coords) and top outline pixels of the legs that use the near-black outline colour
    -> the boot ramp's 3rd tone, so socks / boots stay readable on dark ground. Shape unchanged. Returns px."""
    a = img[:, :, 3] > 0; h, w = a.shape
    rt = np.zeros_like(a); rt[:, :-1] = a[:, 1:]
    up = np.zeros_like(a); up[1:] = a[:-1]
    yy = np.mgrid[0:h, 0:w][0]
    ol = np.all(img[:, :, :3] == np.array(C_OUTLINE), axis=2)
    m = a & ol & (~rt | ~up) & (yy >= int(LEG_RIM_ROW * k))
    img[m, :3] = P74D.LEG_RAMPS['boot'][2]
    return int(m.sum())


def run(ref74e, ref74c, source, out, nframes, level):
    out.mkdir(parents=True, exist_ok=True)
    oref, _ = B.load_reference(source / 'morwen_right_walk_00_96x128.png'); ouf, _, _ = B.split_layers(oref)
    pal = copy.deepcopy(D.build_palette68(ouf)[0]); pal.update({k: list(v) for k, v in P74D.LEG_RAMPS.items()})
    uf, ub, _ = B.split_layers(ref74e); cuf, cub, _ = B.split_layers(ref74c)
    A.GOLD3.clear(); A.GOLD3.update(P74D.GOLD3_74D); A.ART['level'] = level
    E.configure('B', ouf); E._RIM.clear(); E._RIM.update(P74D.RIM_74D)
    X.CUR['nf'] = nframes; T = X.tables(nframes)
    D.SECONDARY_MOTION = copy.deepcopy(T['motion'])
    M.STATE['proposal'] = 'GLASSES'
    D.shade68 = M.shade71; D.compose68 = M.compose71
    o_r = D.rasterise68; D.rasterise68 = P74D.rasterise74d
    saved = X.setup_motion(T); logs = []
    try:
        masks = D.region_masks(cuf, cub)
        for f in range(nframes):
            X.CUR['f'] = f; bob = T['bob'][f]
            U, foot = D.upper_layers(f, uf, ub, masks)
            U96 = {k: B.shift(v, 0, bob) for k, v in U.items()}
            img, layers, legs = D.compose68(f, U96, pal, 1.0)
            U48 = {k: v[1::2, 1::2].copy() for k, v in U96.items()}
            sm, _, _ = D.compose68(f, U48, pal, 0.5)
            r96 = leg_rim(img, 1.0); r48 = leg_rim(sm, 0.5)
            Image.fromarray(img, 'RGBA').save(out / f'morwen_right_walk_{f:02d}_96x128.png')
            Image.fromarray(sm, 'RGBA').save(out / f'morwen_right_walk_{f:02d}_48x64.png')
            t = T['t'][f]
            logs.append({'frame': f, 't': round(t, 4), 'bob': bob, 'near': X.pivot_corrected(X.tf(f)), 'far': X.pivot_corrected(X.tf(f, True)),
                         'near_role': role_at(t), 'far_role': role_at((t + 0.5) % 1),
                         'secondary': {n: {'dx': T['motion'][n]['dx'][f], 'dy': T['motion'][n]['dy'][f]} for n in T['motion']},
                         'skirt_sway': T['skirt'][f], 'leg_rim_px': [r96, r48]})
    finally:
        X.restore(saved); D.rasterise68 = o_r
        D.shade68 = E._shade68; D.compose68 = A._compose68; M.STATE['proposal'] = None; A.ART['level'] = 'B'
    return {'frames_per_cycle': nframes, 'frames': logs, 'ground_speed_px_per_cycle': {'96x128': 4 * S, '48x64': 2 * S},
            'ground_speed_px_per_frame': {'96x128': round(4 * S / nframes, 4), '48x64': round(2 * S / nframes, 4)}}


def build(ref74c_path, source, out, level='C'):
    patch_x()
    out.mkdir(parents=True, exist_ok=True)
    w = out / '_work'
    if w.exists(): shutil.rmtree(w)
    ref74c, _ = B.load_reference(ref74c_path)
    full74c = np.array(Image.open(ref74c_path).convert('RGBA'))
    uf, ub, _ = B.split_layers(ref74c)
    parts, keep = part_masks(X.region_masks8(uf, ub), uf[:, :, 3] > 0, ub[:, :, 3] > 0)
    full74d, clog = recolor(full74c, parts, keep)
    full74e, rim_px, rim_col = add_rim(full74d, parts)
    refdir = w / 'ref'; refdir.mkdir(parents=True)
    Image.fromarray(full74e, 'RGBA').save(refdir / 'morwen_right_walk_00_96x128.png')
    Image.fromarray(full74e, 'RGBA').save(out / 'REFERENCE_left_side_74E_right_coords.png')
    ref74e, _ = B.load_reference(refdir / 'morwen_right_walk_00_96x128.png')
    metas = {}
    for nf in (8, 12):
        metas[nf] = run(ref74e, ref74c, source, w / f'r{nf}', nf, level)
        for f in range(nf):
            for s in ('96x128', '48x64'):
                Image.open(w / f'r{nf}' / f'morwen_right_walk_{f:02d}_{s}.png').transpose(Image.FLIP_LEFT_RIGHT).save(out / f'morwen_left_walk_{nf}f_{f:02d}_{s}.png')
    meta = {'base': 'ART-74D design + video-analysed motion', 'art_level': level, 'rim': {'parts': RIM_PARTS, 'px': rim_px, 'rgb': rim_col},
            'scale': {'leg_length_px': LEG_L, 'stride_k': STRIDE_K, 'stance_half_px': S, 'toe_off_t': T_OFF},
            'stance_pitch': STANCE_PITCH, 'swing_keys': SWING, 'roles': ROLES, 'bob_window': BOB_WIN,
            'arm': {'amp_px': ARM_AMP, 'lead': ARM_LEAD}, 'pelvis': {'rot_px': PELVIS_ROT_PX, 'drop_swing_px': PELVIS_DROP_SWING},
            'motion_8f': metas[8], 'motion_12f': metas[12]}
    (out / 'build_meta_74e.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')
    shutil.rmtree(w)
    return meta


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref74c', type=Path, required=True); ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True); ap.add_argument('--level', default='C')
    a = ap.parse_args(); build(a.ref74c, a.source, a.out, a.level); print('ok')

#!/usr/bin/env python3
"""ART-74C: Morwen left walk = 74B art + official-left design check + 8-frame elegant walk candidate.

Design (official left profile, assets/official/characters/morwen/turnaround/ SHA-256 d858c428...):
  on top of the 74B left-side reference (right-view coords) remove the two items the official left view does not show:
    - hat-tip jewel (gold bead + purple drop hanging from the hat tip)       -> transparent (outside the hat silhouette)
    - re-routed cross-body strap drawn by 74A (STRAP_NEW)                    -> refilled from the bodice around it
  everything else of 74B is kept (no bag / flower / ribbon / crest; earring = gold + purple drop, matches the official).
Motion (one cycle as a function of phase; 8f and 12f sample the SAME cycle - candidate only, the 6-frame spec is NOT replaced):
  near leg at t, far leg at t+0.5; stance travel 17 px (34 px / cycle, 74B: 36) with pivot correction (foot rolls over a
  fixed heel / toe point), low foot lift (max 4 px), body bob 1 px on the loading frames only, pelvic rotation +-0.6 px +
  0.5 px swing-side drop, near arm 1 px counter-phase, collar / cape / potions / hair tips / mantle / skirt lag 1/8 cycle.
  Body shape is not changed. Values are design values (no video was analysed, see VIDEO_ANALYSIS_74C.md).
Outputs (mirrored to left): morwen_left_walk_{8f,12f}_NN_{96x128,48x64}.png and the 6-frame design-only variant
morwen_left_walk_6f_NN_{...}.png (74B motion + 74C design).
  python3 build_morwen74c.py --source <65B F00 dir> --out <dir>
"""
import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_PIPE = _os.environ.get('MORWEN72_PIPELINE', _os.path.join(_HERE, '..', '..', 'morwen-right-walk', '72'))
_B74 = _os.environ.get('MORWEN74B_DIR', _os.path.join(_HERE, '..', '74B'))
_sys.path[:0] = [_HERE, _B74, _PIPE]
import argparse, copy, json, math, shutil
from pathlib import Path
import numpy as np
from PIL import Image
import build_morwen66 as B, build_morwen67 as C, build_morwen68 as D, build_morwen70 as E, build_morwen70art as A
import build_morwen71 as M
import build_morwen74b as P74B
from inpaint74 import exemplar, drop_islands

H, W = 128, 96
# ------------------------------------------------------------------ one walk cycle as a function of phase t in [0,1)
# (near leg at t, far leg at t+0.5). 8- and 12-frame versions SAMPLE THE SAME CYCLE: same stride, same ground speed per
# cycle (28 px / cycle at 96 px), so adding frames never changes the walking speed.
# Key poses of one leg (right-view coords, +x = forward). Stance = t 0 .. 0.5 (ankle moves back linearly = no foot slide,
# +8.5 -> -8.5 px before the pivot correction), swing = 0.5 .. 1. Values are design values from general gait mechanics (no video was analysed).
KEYS = [  # t, ankle dx, foot pitch (+ toe up), lift px, role
    (0.000, +8.5, +14, 0, 'heel strike'),
    (0.125, +4.25, 0, 0, 'loading, foot flat'),
    (0.250, 0.0, 0, 0, 'mid-stance'),
    (0.375, -4.25, -6, 0, 'terminal stance, heel rising'),
    (0.500, -8.5, -24, 0, 'toe-off'),
    (0.625, -5.0, -20, 4, 'initial swing'),
    (0.750, +1.0, -4, 3, 'mid swing (passing)'),
    (0.875, +6.0, +10, 1, 'terminal swing, reaching'),
    (1.000, +8.5, +14, 0, 'heel strike'),
]
STRIDE_PX = 17.0                                     # stance travel; ground speed = 2 * STRIDE_PX per cycle (6f: 36)


def gait_at(t):
    t = t % 1.0
    for (t0, d0, p0, l0, r0), (t1, d1, p1, l1, r1) in zip(KEYS, KEYS[1:]):
        if t0 <= t <= t1 + 1e-9:
            u = (t - t0) / (t1 - t0)
            if t <= 0.5:     # stance: exact linear travel (no slide)
                dx = STRIDE_PX / 2 - 2 * STRIDE_PX * t
            else:
                dx = d0 + (d1 - d0) * u
            return dict(dx=round(dx, 3), pitch=round(p0 + (p1 - p0) * u, 2), lift=int(round(l0 + (l1 - l0) * u)),
                        role=r0 if u < 0.5 else r1)
    raise ValueError(t)


def pivot_corrected(t):
    """stance frames with a tilted foot: shift the ankle so the ground pivot (heel back corner for heel strike, toe tip
    for heel-rise / toe-off) sits exactly where the flat foot's heel back / toe front edge is at that moment -> the
    planted foot rolls over a fixed point instead of sliding."""
    g = gait_at(t)
    if g['lift'] == 0 and g['pitch'] != 0 and (t % 1.0) <= 0.5 + 1e-9:
        poly = B.FOOT_POLY + B.SOLE_POLY + B.HEEL_POLY
        flat = B.foot_points(poly, (0.0, 0.0), 0); tilt = B.foot_points(poly, (0.0, 0.0), g['pitch'])
        fy = max(y for _, y in flat); base = [x for x, y in flat if y >= fy - 1e-6]
        ty = max(y for _, y in tilt); piv = [x for x, y in tilt if y >= ty - 1e-6]
        if g['pitch'] > 0: g['dx'] = round(g['dx'] + min(base) - min(piv), 3)
        else: g['dx'] = round(g['dx'] + max(base) - max(piv), 3)
    return g


def inwin(t, a, b):
    return a <= (t % 0.5) < b


def arm_dx(t):
    c = -math.cos(2 * math.pi * t)            # near arm back when the near leg reaches forward
    return 0 if abs(c) < 0.45 else (1 if c > 0 else -1)


def tables(nf):
    ts = [f / nf for f in range(nf)]
    bob = [1 if inwin(t, 1 / 16, 3 / 16) else 0 for t in ts]                       # 1 px down while loading only
    lag = [1 if inwin(t - 0.125, 1 / 16, 3 / 16) else 0 for t in ts]                # light cloth: same drop, 1/8 cycle later
    heavy = [1 if inwin(t - 0.125, 1 / 16, 5 / 16) else 0 for t in ts]              # mantle: later and longer
    return dict(
        t=ts, bob=bob,
        skirt=[-1 if inwin(t, 1 / 16, 6 / 16) else 0 for t in ts],
        motion={
            'collar_ribbon': dict(max_offset_px=1, phase_lag=0.125, dy=lag, dx=[-v for v in lag]),
            'cape_front':    dict(max_offset_px=1, phase_lag=0.125, dy=lag, dx=[0] * nf),
            'mantle':        dict(max_offset_px=2, phase_lag=0.125, dy=heavy, dx=[-2 if inwin(t, 0.1875, 0.4375) else -1 for t in ts]),
            'potions':       dict(max_offset_px=1, phase_lag=0.125, dy=lag, dx=[0] * nf),
            'hair_tips':     dict(max_offset_px=1, phase_lag=0.125, dy=lag, dx=[0] * nf),
            'arm':           dict(max_offset_px=1, phase_lag=0, dy=[0] * nf, dx=[arm_dx(t) for t in ts]),
        })


PELVIS_ROT_PX = 0.6        # hip of the forward-reaching leg forward (pelvic rotation seen from the side)
PELVIS_DROP_SWING = 0.5    # swing-side hip slightly lower
EXTRA_ANCHORS = {'hair_tips': (48, 39, 10.0), 'arm': (46, 65, 11.0)}
CUR = {'f': 0, 'nf': 8}


def tf(f, half=False):
    return (f / CUR['nf'] + (0.5 if half else 0.0)) % 1.0


class GaitView:
    """compose68 asks GAIT[f] for the near leg and GAIT[(f+3)%6] for the far leg; with 8 frames the far leg is (f+4)%8."""
    def __getitem__(self, key):
        f = CUR['f']
        return pivot_corrected(tf(f, key != f))


_solve_leg = B.solve_leg


def solve_leg8(hip_x, hip_y, phase):
    f = CUR['f']
    t = tf(f, phase != f)
    hip_x = hip_x + PELVIS_ROT_PX * math.cos(2 * math.pi * t)
    if gait_at(t)['lift'] > 0:   # (pivot correction only moves the ankle, the lift is the same)
        hip_y = hip_y + PELVIS_DROP_SWING
    return _solve_leg(hip_x, hip_y, phase)


_region_masks = D.region_masks


def region_masks8(uf, ub):
    m = _region_masks(uf, ub)
    yy, xx = np.mgrid[0:H, 0:W]
    r, g, b = (uf[:, :, i].astype(int) for i in range(3))
    gold = (r > 170) & (b < 90); bright = (r > 200) & (b > 150)
    skin = (r > 220) & (g > 160) & (b > 120) & (b < 215)
    hair = m['immutable_details'] & (xx >= 38) & (xx <= 56) & (yy >= 42) & (yy <= 49) & ~gold & ~bright & ~skin
    arm = m['torso'] & (xx >= 42) & (xx <= 51) & (yy >= 70) & (yy <= 79)
    m['immutable_details'] = m['immutable_details'] & ~hair
    m['torso'] = m['torso'] & ~arm
    m['hair_tips'] = hair; m['arm'] = arm
    return m


_upper_layers = D.upper_layers


def upper_layers8(f, ref_front, ub, masks):
    L, foot = _upper_layers(f, ref_front, ub, masks)
    full_alpha = (ref_front[:, :, 3] > 0) | (ub[:, :, 3] > 0)
    sm = D.SECONDARY_MOTION
    for name in ('hair_tips', 'arm'):
        L[name], foot[name] = D.warp(ref_front, masks[name], D.weight(name), sm[name]['dx'][f], sm[name]['dy'][f], full_alpha)
    return L, foot


def setup_motion(T):
    saved = dict(GAIT=B.GAIT, BOB=B.BOB, DBOB=D.BOB, solve=B.solve_leg, rm=D.region_masks, ul=D.upper_layers, Z=list(D.Z),
                 sway=D.SKIRT_SWAY, fp=D.FRAME_ART_PATCHES, fp48=D.FRAME_ART_PATCHES_48, anchors=dict(D.ANCHORS))
    nf = CUR['nf']
    B.GAIT = GaitView(); B.BOB = T['bob']; D.BOB = T['bob']; B.solve_leg = solve_leg8
    D.region_masks = region_masks8; D.upper_layers = upper_layers8
    D.SKIRT_SWAY = T['skirt']
    D.FRAME_ART_PATCHES = {f: [] for f in range(nf)}; D.FRAME_ART_PATCHES_48 = {f: [] for f in range(nf)}
    D.ANCHORS.update(EXTRA_ANCHORS)
    z = [n for n in D.Z]
    z.insert(z.index('torso') + 1, 'arm'); z.insert(z.index('immutable_details') + 1, 'hair_tips')
    D.Z[:] = z
    return saved


def restore(s):
    B.GAIT, B.BOB, D.BOB, B.solve_leg = s['GAIT'], s['BOB'], s['DBOB'], s['solve']
    D.region_masks, D.upper_layers, D.SKIRT_SWAY = s['rm'], s['ul'], s['sway']
    D.FRAME_ART_PATCHES, D.FRAME_ART_PATCHES_48 = s['fp'], s['fp48']
    D.Z[:] = s['Z']; D.ANCHORS.clear(); D.ANCHORS.update(s['anchors'])


# ------------------------------------------------------------------ design corrections (official left)
STRAP_NEW = P74B.STRAP_NEW


def design_edit(ref74b):
    a = ref74b.copy(); yy, xx = np.mgrid[0:H, 0:W]
    jewel = (a[:, :, 3] > 0) & (xx <= 25) & (yy >= 24) & (yy <= 35)
    a[jewel] = 0
    strap = np.zeros((H, W), bool)
    for i, (x, y) in enumerate(STRAP_NEW):
        strap[y, x] = True
        if i % 2 == 0: strap[y - 1, x] = True
    src = (a[:, :, 3] > 0) & ~strap & (xx >= 44) & (xx <= 68) & (yy >= 56) & (yy <= 78)
    a2, left = exemplar(a, strap, src); a[strap] = a2[strap]
    isl = drop_islands(a)
    a[a[:, :, 3] == 0, :3] = 0
    return a, dict(jewel_px=int(jewel.sum()), strap_px=int(strap.sum()), strap_unfilled=int(left.sum()), islands_removed=isl)


# ------------------------------------------------------------------ build
def run_pipeline(refdir, source, out, nframes):
    oref, _ = B.load_reference(source / 'morwen_right_walk_00_96x128.png'); ouf, _, _ = B.split_layers(oref)
    g3 = A.pick_gold3(oref); pal68 = D.build_palette68(ouf)
    if nframes == 6:          # unchanged 72 pipeline (as 74B), palettes from the ORIGINAL reference
        o_pick, o_pal, o_conf = A.pick_gold3, D.build_palette68, E.configure
        A.pick_gold3 = lambda ref: dict(g3); D.build_palette68 = lambda uf: pal68
        E.configure = lambda easing, ref_front: o_conf(easing, ouf)
        try:
            M.build(refdir, out, 'GLASSES')
        finally:
            A.pick_gold3, D.build_palette68, E.configure = o_pick, o_pal, o_conf
        return None
    # 8 frames: same setup as build_morwen71.build(..., 'GLASSES'), own frame loop
    out.mkdir(parents=True, exist_ok=True)
    ref, _ = B.load_reference(refdir / 'morwen_right_walk_00_96x128.png')
    A.GOLD3.clear(); A.GOLD3.update(g3); A.ART['level'] = 'B'
    uf, ub, _ = B.split_layers(ref)
    E.configure('B', ouf)
    CUR['nf'] = nframes; T = tables(nframes)
    D.SECONDARY_MOTION = copy.deepcopy(T['motion'])
    M.STATE['proposal'] = 'GLASSES'
    D.shade68 = M.shade71; D.compose68 = M.compose71
    saved = setup_motion(T)
    logs = []
    try:
        masks = D.region_masks(uf, ub)
        for f in range(nframes):
            CUR['f'] = f
            bob = T['bob'][f]
            U, foot = D.upper_layers(f, uf, ub, masks)
            U96 = {k: B.shift(v, 0, bob) for k, v in U.items()}
            img, layers, legs = D.compose68(f, U96, pal68[0], 1.0)
            U48 = {k: v[1::2, 1::2].copy() for k, v in U96.items()}
            sm, _, _ = D.compose68(f, U48, pal68[0], 0.5)
            Image.fromarray(img, 'RGBA').save(out / f'morwen_right_walk_{f:02d}_96x128.png')
            Image.fromarray(sm, 'RGBA').save(out / f'morwen_right_walk_{f:02d}_48x64.png')
            logs.append({'frame': f, 't': round(T['t'][f], 4), 'bob': bob, 'near': pivot_corrected(tf(f)), 'far': pivot_corrected(tf(f, True)),
                         'near_joints': {kk: [round(v, 6) for v in legs['near'][kk]] for kk in ('hip', 'knee', 'ankle')},
                         'far_joints': {kk: [round(v, 6) for v in legs['far'][kk]] for kk in ('hip', 'knee', 'ankle')},
                         'secondary': {n: {'dx': T['motion'][n]['dx'][f], 'dy': T['motion'][n]['dy'][f]} for n in T['motion']},
                         'skirt_sway': T['skirt'][f]})
    finally:
        restore(saved)
        D.shade68 = E._shade68; D.compose68 = A._compose68; M.STATE['proposal'] = None
    return {'frames_per_cycle': nframes, 'key_poses': KEYS, 'stride_px_96': STRIDE_PX, 'pelvis_rot_px': PELVIS_ROT_PX,
            'pelvis_drop_swing_px': PELVIS_DROP_SWING, 'extra_anchors': EXTRA_ANCHORS, 'frames': logs,
            'ground_speed_px_per_cycle': {'96x128': 2 * STRIDE_PX, '48x64': STRIDE_PX},
            'ground_speed_px_per_frame': {'96x128': round(2 * STRIDE_PX / nframes, 4), '48x64': round(STRIDE_PX / nframes, 4)}}


def build(source: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    w = out / '_work'
    if w.exists(): shutil.rmtree(w)
    P74B.edit_reference(source, w / 'ref74b')
    ref74b = np.array(Image.open(w / 'ref74b' / 'morwen_right_walk_00_96x128.png').convert('RGBA'))
    ref74c, dlog = design_edit(ref74b)
    refdir = w / 'ref74c'; refdir.mkdir(parents=True)
    Image.fromarray(ref74c, 'RGBA').save(refdir / 'morwen_right_walk_00_96x128.png')
    for p in source.glob('*_48x64.png'): shutil.copy(p, refdir / p.name)
    Image.fromarray(ref74c, 'RGBA').save(out / 'REFERENCE_left_side_edit_right_coords.png')
    Image.fromarray((np.any(ref74c != ref74b, axis=2) * 255).astype(np.uint8), 'L').save(out / 'REFERENCE_DESIGN_EDIT_74C_vs_74B_right_coords.png')
    run_pipeline(refdir, source, w / 'r6', 6)
    meta8 = run_pipeline(refdir, source, w / 'r8', 8)
    meta12 = run_pipeline(refdir, source, w / 'r12', 12)
    for tag, d, n in (('6f', w / 'r6', 6), ('8f', w / 'r8', 8), ('12f', w / 'r12', 12)):
        for f in range(n):
            for s in ('96x128', '48x64'):
                Image.open(d / f'morwen_right_walk_{f:02d}_{s}.png').transpose(Image.FLIP_LEFT_RIGHT).save(out / f'morwen_left_walk_{tag}_{f:02d}_{s}.png')
    (out / 'build_meta_74c.json').write_text(json.dumps({'design_edit': dlog, 'official_left_sha256': 'd858c428c64007596302057453f414dd43c580bc1546b9578c3d1dfb0af17591',
                                                         'motion_8f': meta8, 'motion_12f': meta12}, ensure_ascii=False, indent=1), encoding='utf-8')
    shutil.rmtree(w)
    return dlog


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--source', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(); print(build(a.source, a.out))

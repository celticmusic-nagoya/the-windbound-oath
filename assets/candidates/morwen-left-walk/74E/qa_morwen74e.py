#!/usr/bin/env python3
"""ART-74E static / technical QA.
  python3 qa_morwen74e.py --art <74E dir> --d74 <74D dir> --c74 <74C dir> --b74 <74B dir> --a74 <74A dir> --right72 <72 dir>"""
import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_PIPE = _os.environ.get('MORWEN72_PIPELINE', _os.path.join(_HERE, '..', '..', 'morwen-right-walk', '72'))
_sys.path[:0] = [_HERE, _PIPE]
import argparse, json, hashlib, math
from pathlib import Path
import numpy as np
from PIL import Image
from qa_morwen66 import components
import build_morwen74e as E74
import build_morwen66 as B
from oklab import rgb2oklab, lch

ap = argparse.ArgumentParser()
for k in ('art', 'd74', 'c74', 'b74', 'a74', 'right72'): ap.add_argument('--' + k, type=Path, required=True)
a = ap.parse_args()
L_ = lambda p: np.array(Image.open(p).convert('RGBA'))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
meta = json.loads((a.art / 'build_meta_74e.json').read_text())
fails, rep = [], {'task': 'MORWEN-ASSET-74E', 'static_qa': None, 'third_party_art_qa': 'NOT_RUN', 'android_device_qa': 'NOT_RUN'}
fn = lambda d, n, f, s: d / f'morwen_left_walk_{n}f_{f:02d}_{s}.png'
GROUND = {'96x128': 124, '48x64': 61}
# ---- 1 video analysis evidence
need = ['VIDEO_ANALYSIS_74E.json', 'ann_v2.json', 'v2_series.json', 'VIDEO_KEYPOSES_74E.png', 'VIDEO_SERIES_74E.png', 'VIDEO_vs_74E_POSES.png']
rep['video_evidence'] = {n: (a.art / n).exists() for n in need}
if not all(rep['video_evidence'].values()): fails.append('video evidence missing')
# ---- 2 format / ground
fr = {}
for n in (8, 12):
    for f in range(n):
        for s, size in (('96x128', (96, 128)), ('48x64', (48, 64))):
            im = Image.open(fn(a.art, n, f, s)); x = np.array(im)
            ok = im.mode == 'RGBA' and im.size == size and bool(np.isin(x[:, :, 3], (0, 255)).all()) \
                and bool(np.all(x[x[:, :, 3] == 0, :3] == 0)) and not components(x[:, :, 3] > 0)[1:]
            low = int(np.where(x[:, :, 3].any(1))[0].max())
            ncol = len(np.unique(x[x[:, :, 3] > 0][:, :3], axis=0))
            fr[f'{n}f_{f:02d}_{s}'] = {'format_ok': ok, 'lowest_row': low, 'colours': ncol, 'sha256': sha(fn(a.art, n, f, s))}
            if not ok: fails.append(f'{n}f F{f} {s} format')
            if low != GROUND[s]: fails.append(f'{n}f F{f} {s} ground {low}')
rep['frames'] = fr
# colour count vs 74D (same frame index, 8f)
cc = {s: (int(np.mean([fr[f'8f_{f:02d}_{s}']['colours'] for f in range(8)])),
          int(np.mean([len(np.unique(L_(fn(a.d74, 8, f, s))[L_(fn(a.d74, 8, f, s))[:, :, 3] > 0][:, :3], axis=0)) for f in range(8)])))
      for s in ('96x128', '48x64')}
rep['mean_colours_per_frame_74E_vs_74D'] = cc
for s, (e, d) in cc.items():
    if e > d: fails.append(f'colour count increased {s}')
# ---- 3 foot slide / contact (re-solve the legs exactly as the build does)
E74.patch_x(); X = E74.X
def legs(nf):
    X.CUR['nf'] = nf; T = X.tables(nf); saved = X.setup_motion(T); res = []
    try:
        for f in range(nf):
            X.CUR['f'] = f; bob = T['bob'][f]
            n_ = B.solve_leg(B.NEAR_HIP_X, B.HIP_Y + bob, f); f_ = B.solve_leg(B.FAR_HIP_X, B.HIP_Y + bob, (f + 3) % 6)
            res.append((n_, f_, X.gait_at(X.tf(f))['lift'], X.gait_at(X.tf(f, True))['lift']))
    finally:
        X.restore(saved)
    return res
def slide(frames, speed):
    out = []; n = len(frames)
    for side in (0, 1):
        for f in range(n):
            g = (f + 1) % n
            if frames[f][2 + side] > 0 or frames[g][2 + side] > 0: continue
            def contact(leg):
                lab, _ = B.rasterise_leg(leg); xs = np.where(lab[B.GROUND] > 0)[0]
                return xs.min(), xs.max(), leg['pitch']
            a0, b0, p0 = contact(frames[f][side]); a1, b1, p1 = contact(frames[g][side])
            d = abs((b1 + speed) - b0) if p1 < 0 else abs((a1 + speed) - a0)
            out.append({'leg': 'near' if side == 0 else 'far', 'from': f, 'to': g, 'drift_px': round(float(d), 2)})
    return out
rep['foot_slide_96'] = {}
for n in (8, 12):
    v = slide(legs(n), meta[f'motion_{n}f']['ground_speed_px_per_frame']['96x128'])
    rep['foot_slide_96'][f'{n}f'] = {'max_drift_px': max(x['drift_px'] for x in v), 'pairs': v}
    if rep['foot_slide_96'][f'{n}f']['max_drift_px'] >= 1.5: fails.append(f'{n}f foot slide')
rep['cycle'] = {'8f_px_per_cycle_96': meta['motion_8f']['ground_speed_px_per_cycle']['96x128'], '12f_px_per_cycle_96': meta['motion_12f']['ground_speed_px_per_cycle']['96x128'],
                'stance_share_design': meta['scale']['toe_off_t'], 'stance_share_video': 0.66}
if rep['cycle']['8f_px_per_cycle_96'] != rep['cycle']['12f_px_per_cycle_96']: fails.append('8f/12f speed differ')
# ---- 4 arm / leg phase, pelvis, lag
for n in (8, 12):
    fl = meta[f'motion_{n}f']['frames']
    arm = np.array([x['secondary']['arm']['dx'] for x in fl], float); leg = np.array([x['near']['dx'] for x in fl], float)
    r = float(np.corrcoef(arm, leg)[0, 1])
    rep.setdefault('arm_leg_phase', {})[f'{n}f'] = {'corr_near_arm_vs_near_ankle': round(r, 3), 'arm_dx': arm.astype(int).tolist()}
    hs = arm[0]; opp = arm[n // 2]           # near heel strike (t=0) / opposite heel strike (t=0.5)
    rep['arm_leg_phase'][f'{n}f'].update({'arm_at_near_heel_strike': int(hs), 'arm_at_far_heel_strike': int(opp)})
    if not (hs < 0 < opp and r < -0.5): fails.append(f'{n}f arm not counter-phase')
    bob = [x['bob'] for x in fl]; lag = [x['secondary']['collar_ribbon']['dy'] for x in fl]
    shift = (n // 8) if n % 8 == 0 else round(n / 8)
    rep.setdefault('secondary_lag', {})[f'{n}f'] = {'body_bob': bob, 'cloth_dy': lag, 'mantle_dx': [x['secondary']['mantle']['dx'] for x in fl],
                                                    'skirt': [x['skirt_sway'] for x in fl]}
rep['pelvis_shoulder'] = {'pelvis_rotation_px': meta['pelvis']['rot_px'], 'pelvis_drop_swing_px': meta['pelvis']['drop_swing_px'],
                          'shoulder': 'expressed by the 2 px counter-phase arm (capelet / torso layer kept rigid)'}
# ---- 5 loop seam / head
def consec(n):
    c = [int(np.any(L_(fn(a.art, n, f, '96x128')) != L_(fn(a.art, n, (f + 1) % n, '96x128')), axis=2).sum()) for f in range(n)]
    # the seam (last -> F00) is a body-bob transition; it is compared with the same transition half a cycle
    # earlier (n/2-1 -> n/2) instead of the mean, which mixes bob and non-bob transitions
    ref = c[n // 2 - 1]
    return {'changed_px': c, 'seam': c[-1], 'same_transition_half_cycle_earlier': ref, 'seam_ratio': round(c[-1] / ref, 3)}
rep['loop_96'] = {'8f': consec(8), '12f': consec(12)}
for k, v in rep['loop_96'].items():
    if v['seam_ratio'] > 1.15: fails.append(f'{k} loop seam')
rep['head_top_row_96'] = {f'{n}f': [int(np.where(L_(fn(a.art, n, f, '96x128'))[:, :, 3].any(1))[0].min()) for f in range(n)] for n in (8, 12)}
# ---- 6 design kept from 74D (reference identical except rim, colours not back to magenta)
r74d = L_(a.d74 / 'REFERENCE_left_side_74D_colour_right_coords.png'); r74e = L_(a.art / 'REFERENCE_left_side_74E_right_coords.png')
diff = np.any(r74d != r74e, axis=2)
rep['reference_diff_vs_74D_px'] = int(diff.sum()); rep['rim_px_design'] = meta['rim']['px']
if int(diff.sum()) != meta['rim']['px']: fails.append('reference differs from 74D beyond the rim')
def magenta(img):
    m = img[:, :, 3] > 0; _, C, h = lch(rgb2oklab(img[m][:, :3].astype(float)))
    return round(float((((h > 330) | (h < 10)) & (C > 0.12)).mean()), 4)
rep['magenta_share_8f_F00'] = {'74C': magenta(L_(fn(a.c74, 8, 0, '96x128'))), '74D': magenta(L_(fn(a.d74, 8, 0, '96x128'))), '74E': magenta(L_(fn(a.art, 8, 0, '96x128')))}
if rep['magenta_share_8f_F00']['74E'] > rep['magenta_share_8f_F00']['74D'] + 0.005: fails.append('magenta increased')
# ---- 7 protected files
rep['protected_sha256'] = {name: {p.name: sha(p) for p in sorted(d.glob('*.png'))} for name, d in (('74A', a.a74), ('74B', a.b74), ('74C', a.c74), ('74D', a.d74), ('right72', a.right72))}
rep['fails'] = fails; rep['static_qa'] = 'PASS' if not fails else 'FAIL'
(a.art / 'QA_REPORT_74E.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding='utf-8')
with open(a.art / 'SHA256SUMS_74E.txt', 'w') as fh:
    for p in sorted(a.art.glob('*.png')) + sorted(a.art.glob('*.gif')):
        fh.write(f'{sha(p)}  {p.name}\n')
print(rep['static_qa'], fails)
print({k: v['max_drift_px'] for k, v in rep['foot_slide_96'].items()}, rep['arm_leg_phase'], rep['loop_96'], rep['magenta_share_8f_F00'], cc, rep['head_top_row_96'])

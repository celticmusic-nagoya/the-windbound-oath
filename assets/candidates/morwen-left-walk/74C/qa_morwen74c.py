#!/usr/bin/env python3
"""ART-74C technical QA (self-QA; art QA / Android are separate gates).
  python3 qa_morwen74c.py --art <74C dir> --b74 <74B dir> --a74 <74A dir> --right72 <72 dir>
Checks: PNG format / transparency / size / one component (6f, 8f, 12f); ground rows; foot slide of the planted foot
(per leg, analytic re-rasterisation of the logged joints, world x = sprite x + ground speed * frame); stride and speed
per cycle; head (hat) vertical motion; loop seam (last -> F00) vs. the other transitions; 6f design-only variant vs 74B
(changes only in the design-edit zone); SHA-256 of every output and of the protected 74A / 74B / right 72 files."""
import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_PIPE = _os.environ.get('MORWEN72_PIPELINE', _os.path.join(_HERE, '..', '..', 'morwen-right-walk', '72'))
_B74 = _os.environ.get('MORWEN74B_DIR', _os.path.join(_HERE, '..', '74B'))
_sys.path[:0] = [_HERE, _B74, _PIPE]
import argparse, json, hashlib, math
from pathlib import Path
import numpy as np
from PIL import Image
import build_morwen66 as B, build_morwen68 as D
from qa_morwen66 import components

ap = argparse.ArgumentParser()
for k in ('art', 'b74', 'a74', 'right72'): ap.add_argument('--' + k, type=Path, required=True)
a = ap.parse_args()
L = lambda p: np.array(Image.open(p).convert('RGBA'))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
meta = json.loads((a.art / 'build_meta_74c.json').read_text())
fails, rep = [], {'task': 'MORWEN-ASSET-74C', 'technical_qa': None, 'art_qa': 'NOT_RUN (third-party)', 'android': 'NOT_RUN'}
VAR = {'6f': 6, '8f': 8, '12f': 12}
fn = lambda tag, f, s: a.art / f'morwen_left_walk_{tag}_{f:02d}_{s}.png'
# ---------------------------------------------------------------- 1 format / ground
fmt = {}
for tag, n in VAR.items():
    for s, (w, h), g in (('96x128', (96, 128), 124), ('48x64', (48, 64), 61)):
        for f in range(n):
            im = Image.open(fn(tag, f, s)); x = np.array(im)
            ok = im.mode == 'RGBA' and im.size == (w, h) and bool(np.isin(x[:, :, 3], (0, 255)).all()) \
                and bool(np.all(x[x[:, :, 3] == 0, :3] == 0)) and not components(x[:, :, 3] > 0)[1:]
            low = int(np.where(x[:, :, 3].any(1))[0].max())
            fmt[f'{tag}_{f:02d}_{s}'] = {'format_ok': ok, 'lowest_row': low, 'sha256': sha(fn(tag, f, s))}
            if not ok: fails.append(f'{tag} F{f} {s} format')
            if low != g: fails.append(f'{tag} F{f} {s} ground row {low} != {g}')
rep['frames'] = fmt
# ---------------------------------------------------------------- 2 foot slide (planted foot, per leg)
def foot_slide(frames, speed):
    """frames: list of (near_leg, far_leg, near_lift, far_lift) in right-view coords. Returns max world drift of the
    contact edge between consecutive planted frames of the same leg (heel edge while the heel is down, toe edge after)."""
    out = []
    n = len(frames)
    for side in (0, 1):
        for f in range(n):
            g = (f + 1) % n
            l0, l1 = frames[f][side], frames[g][side]
            if frames[f][2 + side] > 0 or frames[g][2 + side] > 0:
                continue
            def contact(leg):
                lab, _ = B.rasterise_leg(leg)
                xs = np.where(lab[B.GROUND] > 0)[0]
                if not len(xs): raise ValueError(('no contact', side, f, leg))
                return xs.min(), xs.max(), leg['pitch']
            x0a, x0b, p0 = contact(l0); x1a, x1b, p1 = contact(l1)
            w0a, w0b = x0a, x0b                # one frame later the world has moved by `speed` px
            w1a, w1b = x1a + speed, x1b + speed
            # heel down in both -> back edge must hold; toe pivot (pitch < 0 in the second) -> front edge must hold
            d = abs(w1b - w0b) if p1 < 0 else abs(w1a - w0a)
            out.append({'leg': 'near' if side == 0 else 'far', 'from': f, 'to': g, 'drift_px': round(float(d), 2)})
    return out

def legs_8_12(nf):
    """re-solve the legs exactly as the build does (logged joints are rounded and the 8x supersampled raster is
    sensitive to 1e-7 px)."""
    import build_morwen74c as X
    X.CUR['nf'] = nf; T = X.tables(nf); saved = X.setup_motion(T); res = []
    try:
        for f in range(nf):
            X.CUR['f'] = f; bob = T['bob'][f]
            n = B.solve_leg(B.NEAR_HIP_X, B.HIP_Y + bob, f); fr = B.solve_leg(B.FAR_HIP_X, B.HIP_Y + bob, (f + 3) % 6)
            res.append((n, fr, X.gait_at(X.tf(f))['lift'], X.gait_at(X.tf(f, True))['lift']))
    finally:
        X.restore(saved)
    return res


def legs_6():
    res = []
    for f in range(6):
        bob = B.BOB[f]
        n = B.solve_leg(B.NEAR_HIP_X, B.HIP_Y + bob, f); fr = B.solve_leg(B.FAR_HIP_X, B.HIP_Y + bob, (f + 3) % 6)
        res.append((n, fr, B.GAIT[f]['lift'], B.GAIT[(f + 3) % 6]['lift']))
    return res

_l6 = legs_6()
slide = {'74B_6f': foot_slide(_l6, 6.0)}
for tag in ('8f', '12f'):
    m = meta[f'motion_{tag}']
    slide['74C_' + tag] = foot_slide(legs_8_12(VAR[tag]), m['ground_speed_px_per_frame']['96x128'])
rep['foot_slide_96'] = {k: {'max_drift_px': max(x['drift_px'] for x in v), 'pairs': v} for k, v in slide.items()}
for k in ('74C_8f', '74C_12f'):
    # criterion: < 1.5 px. Ground speeds are fractional (8f 4.25, 12f 2.83 px/frame at 96 px), so a planted edge
    # rendered on integer pixels can show up to ~1 px of quantisation even with exact geometry; 74B 6f measures 3 px.
    if rep['foot_slide_96'][k]['max_drift_px'] >= 1.5: fails.append(f'{k} foot slide >= 1.5px')
rep['speed'] = {'74B_6f_px_per_cycle_96': 36.0,
                '74C_8f_px_per_cycle_96': meta['motion_8f']['ground_speed_px_per_cycle']['96x128'],
                '74C_12f_px_per_cycle_96': meta['motion_12f']['ground_speed_px_per_cycle']['96x128']}
if rep['speed']['74C_8f_px_per_cycle_96'] != rep['speed']['74C_12f_px_per_cycle_96']: fails.append('8f / 12f speed differ')
# ---------------------------------------------------------------- 3 head stability (top opaque row = hat top)
def head_rows(tag, n, prefix=None):
    p = (lambda f: prefix / f'morwen_left_walk_{f:02d}_96x128.png') if prefix else (lambda f: fn(tag, f, '96x128'))
    return [int(np.where(L(p(f))[:, :, 3].any(1))[0].min()) for f in range(n)]
hr = {'74B_6f': head_rows(None, 6, a.b74), '74C_8f': head_rows('8f', 8), '74C_12f': head_rows('12f', 12)}
rep['head_top_row_96'] = {k: {'rows': v, 'range_px': max(v) - min(v), 'share_of_cycle_moved': round(sum(1 for r in v if r != min(v)) / len(v), 3)} for k, v in hr.items()}
# ---------------------------------------------------------------- 4 loop seam
def consec(load, n):
    return [int(np.any(load(f) != load((f + 1) % n), axis=2).sum()) for f in range(n)]
seam = {}
for tag, n in (('8f', 8), ('12f', 12)):
    c = consec(lambda f: L(fn(tag, f, '96x128')), n)
    seam['74C_' + tag] = {'changed_px': c, 'seam_last_to_F00': c[-1], 'mean': round(float(np.mean(c)), 1), 'seam_ratio_to_mean': round(c[-1] / float(np.mean(c)), 3)}
    if c[-1] > 1.5 * np.mean(c): fails.append(f'{tag} loop seam jump')
c = consec(lambda f: L(a.b74 / f'morwen_left_walk_{f:02d}_96x128.png'), 6)
seam['74B_6f'] = {'changed_px': c, 'seam_last_to_F00': c[-1], 'mean': round(float(np.mean(c)), 1), 'seam_ratio_to_mean': round(c[-1] / float(np.mean(c)), 3)}
rep['loop_96'] = seam
# ---------------------------------------------------------------- 5 6f design-only variant vs 74B
def dil(m, n):
    o = m.copy()
    for _ in range(n): o = o | np.roll(o, 1, 0) | np.roll(o, -1, 0) | np.roll(o, 1, 1) | np.roll(o, -1, 1)
    return o
dz = np.array(Image.open(a.art / 'REFERENCE_DESIGN_EDIT_74C_vs_74B_right_coords.png')) > 0
v6 = []
for f in range(6):
    for s in ('96x128', '48x64'):
        x = L(fn('6f', f, s)); y = L(a.b74 / f'morwen_left_walk_{f:02d}_{s}.png')
        d = np.any(x != y, axis=2)
        z = np.roll(dil(dz, 3), B.BOB[f], 0)[:, ::-1]
        if s == '48x64': z = dil(z[1::2, 1::2], 1)
        v6.append({'frame': f, 'size': s, 'changed_vs_74B': int(d.sum()), 'outside_design_zone': int((d & ~z).sum())})
        if (d & ~z).any(): fails.append(f'6f F{f} {s} change outside design zone')
rep['design_only_6f_vs_74B'] = v6
# ---------------------------------------------------------------- 7 protected files
prot = {}
for name, d in (('74A', a.a74), ('74B', a.b74), ('right72', a.right72)):
    prot[name] = {p.name: sha(p) for p in sorted(d.glob('*.png'))}
rep['protected_sha256'] = prot
rep['fails'] = fails
rep['technical_qa'] = 'PASS' if not fails else 'FAIL'
(a.art / 'QA_REPORT_74C.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding='utf-8')
with open(a.art / 'SHA256SUMS_74C.txt', 'w') as fh:
    for p in sorted(a.art.glob('*.png')) + sorted(a.art.glob('*.gif')):
        fh.write(f'{sha(p)}  {p.name}\n')
print(rep['technical_qa'], fails)
print({k: v['max_drift_px'] for k, v in rep['foot_slide_96'].items()})
print(rep['head_top_row_96']); print({k: (v['seam_last_to_F00'], v['mean']) for k, v in seam.items()})

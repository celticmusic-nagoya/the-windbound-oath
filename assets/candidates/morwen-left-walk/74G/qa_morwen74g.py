#!/usr/bin/env python3
"""ART-74G technical QA (12 frames) against ART-74F-C.
  python3 qa_morwen74g.py --art <74G dir> --f74 <74F dir> --e74 <74E dir> --d74 --c74 --b74 --a74 <dirs> --right72 <72 dir>"""
import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_PIPE = _os.environ.get('MORWEN72_PIPELINE', _os.path.join(_HERE, '..', '..', 'morwen-right-walk', '72'))
_F74 = _os.environ.get('MORWEN74F_DIR', _os.path.join(_HERE, '..', '74F'))
_sys.path[:0] = [_HERE, _F74, _PIPE]
import argparse, json, hashlib
from pathlib import Path
import numpy as np, cv2
from PIL import Image
from qa_morwen66 import components
import build_morwen74f as F
import build_morwen74g as G
import build_morwen66 as B

ap = argparse.ArgumentParser()
for k in ('art', 'f74', 'e74', 'd74', 'c74', 'b74', 'a74', 'right72'): ap.add_argument('--' + k, type=Path, required=True)
a = ap.parse_args()
L_ = lambda p: np.array(Image.open(p).convert('RGBA'))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
meta = json.loads((a.f74 / 'build_meta_74f.json').read_text()); gmeta = json.loads((a.art / 'build_meta_74g.json').read_text())
NF = 12; GROUND = {'96x128': 124, '48x64': 61}
fails = []; rep = {'task': 'MORWEN-ASSET-74G', 'technical_qa': None, 'self_art_qa': 'see README (self review only)',
                   'third_party_art_qa': 'NOT_RUN', 'android_device_qa': 'NOT_RUN'}
VER = {'74E': lambda f, s: a.e74 / f'morwen_left_walk_12f_{f:02d}_{s}.png',
       '74F-C': lambda f, s: a.f74 / f'morwen_left_walk_74FC_12f_{f:02d}_{s}.png',
       '74G': lambda f, s: a.art / f'morwen_left_walk_74G_12f_{f:02d}_{s}.png'}
def holes(x):
    t = (x[:, :, 3] == 0).astype(np.uint8); n, _ = cv2.connectedComponents(t, connectivity=4); return n - 2
def islands(x):
    """1-px noise: opaque pixels whose 4 neighbours all differ from it and agree with each other (>=3)."""
    h, w = x.shape[:2]; c = x[:, :, :3].astype(int); op = x[:, :, 3] > 0; n = 0
    for y in range(1, h - 1):
        for xx in range(1, w - 1):
            if not op[y, xx]: continue
            nb = [tuple(c[y + dy, xx + dx]) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)) if op[y + dy, xx + dx]]
            if len(nb) == 4 and tuple(c[y, xx]) not in nb and max(nb.count(v) for v in nb) >= 3: n += 1
    return n
def gold(x):
    r, g, b = (x[:, :, i].astype(int) for i in range(3)); return int(((r > 150) & (g > 90) & (b < 120) & (r > g) & (g > b) & (x[:, :, 3] > 0)).sum())
per = {}
for v, fn in VER.items():
    rows = []
    for f in range(NF):
        ent = {}
        for s, size in (('96x128', (96, 128)), ('48x64', (48, 64))):
            im = Image.open(fn(f, s)); x = np.array(im)
            ok = im.mode == 'RGBA' and im.size == size and bool(np.isin(x[:, :, 3], (0, 255)).all()) \
                and bool(np.all(x[x[:, :, 3] == 0, :3] == 0)) and not components(x[:, :, 3] > 0)[1:]
            low = int(np.where(x[:, :, 3].any(1))[0].max())
            ent[s] = {'format_ok': ok, 'lowest_row': low, 'holes': holes(x), 'colours': len(np.unique(x[x[:, :, 3] > 0][:, :3], axis=0)),
                      'gold_px': gold(x), 'sha256': sha(fn(f, s))}
            if s == '96x128': ent[s]['isolated_1px'] = islands(x)
            if v == '74G':
                if not ok: fails.append(f'{v} F{f} {s} format')
                if low != GROUND[s]: fails.append(f'{v} F{f} {s} ground {low}')
        rows.append(ent)
    per[v] = rows
rep['frames'] = per
summ = {}
for v, rows in per.items():
    summ[v] = {s: {'holes_max': max(r[s]['holes'] for r in rows), 'colours_mean': int(np.mean([r[s]['colours'] for r in rows])),
                   'gold_px_cv': round(float(np.std([r[s]['gold_px'] for r in rows]) / np.mean([r[s]['gold_px'] for r in rows])), 4)}
               for s in ('96x128', '48x64')}
    summ[v]['isolated_1px_mean_96'] = round(float(np.mean([r['96x128']['isolated_1px'] for r in rows])), 1)
rep['summary'] = summ
for s in ('96x128', '48x64'):
    if summ['74G'][s]['holes_max'] > summ['74F-C'][s]['holes_max']: fails.append(f'74G {s} new holes')
    if summ['74G'][s]['gold_px_cv'] > summ['74F-C'][s]['gold_px_cv']: fails.append(f'74G {s} gold flicker not reduced')
if summ['74G']['isolated_1px_mean_96'] >= summ['74F-C']['isolated_1px_mean_96']: fails.append('74G isolated pixels not reduced')
# 48 isolated pixels as well
for v in VER:
    summ[v]['isolated_1px_mean_48'] = round(float(np.mean([islands(L_(VER[v](f, '48x64'))) for f in range(NF)])), 2)
if summ['74G']['isolated_1px_mean_48'] > summ['74F-C']['isolated_1px_mean_48']: fails.append('74G 48 isolated pixels increased')
# silhouette vs 74F-C: legs region identical, upper body only inside the neck / waist bands
sil = []
for f in range(NF):
    for s_, k in (('96x128', 1.0), ('48x64', 0.5)):
        g_ = L_(VER['74G'](f, s_))[:, :, 3] > 0; c_ = L_(VER['74F-C'](f, s_))[:, :, 3] > 0
        d_ = g_ != c_; yy = np.where(d_)[0]
        sil.append({'frame': f, 'size': s_, 'alpha_diff_px': int(d_.sum()), 'rows': [int(yy.min()), int(yy.max())] if len(yy) else None})
rep['silhouette_vs_74F-C'] = sil
# ---- foot slide (re-solve legs with the variant settings)
F.E74.patch_x(); X = F.X
def legs(variant):
    o_toff = F.E74.T_OFF
    if variant == 'C': F.E74.T_OFF = 0.675
    X.CUR['nf'] = NF; T = F.tables_f(variant); saved = X.setup_motion(T); res = []
    o = B.solve_leg
    try:
        for f in range(NF):
            X.CUR['f'] = f; p = F.P_LEVEL[f]; dx = F.PDX[f]
            n_ = o(B.NEAR_HIP_X + dx, B.HIP_Y + p, f); f_ = o(B.FAR_HIP_X + dx, B.HIP_Y + p, (f + 3) % 6)
            res.append((n_, f_, X.gait_at(X.tf(f))['lift'], X.gait_at(X.tf(f, True))['lift']))
    finally:
        X.restore(saved); F.E74.T_OFF = o_toff
    return res
def slide(frames, speed):
    out = []
    for side in (0, 1):
        for f in range(NF):
            g = (f + 1) % NF
            if frames[f][2 + side] > 0 or frames[g][2 + side] > 0: continue
            def contact(leg):
                lab, _ = B.rasterise_leg(leg); xs = np.where(lab[B.GROUND] > 0)[0]; return xs.min(), xs.max(), leg['pitch']
            a0, b0, p0 = contact(frames[f][side]); a1, b1, p1 = contact(frames[g][side])
            d = abs((b1 + speed) - b0) if p1 < 0 else abs((a1 + speed) - a0)
            out.append({'leg': 'near' if side == 0 else 'far', 'from': f, 'to': g, 'drift_px': round(float(d), 2)})
    return out
rep['foot_slide_96'] = {}
sp = gmeta['C']['ground_speed_px_per_frame']['96x128']
s_ = slide(legs('C'), sp)
rep['foot_slide_96']['74G'] = {'max_drift_px': max(x['drift_px'] for x in s_), 'stance_pairs': len(s_), 'pairs': s_}
if rep['foot_slide_96']['74G']['max_drift_px'] > 0.53: fails.append('74G foot slide worse than 74F-C')
f_q = json.loads((a.f74 / 'QA_REPORT_74F.json').read_text())
rep['foot_slide_96']['74F-C_reference'] = f_q['foot_slide_96']['74F-C']['max_drift_px']
rep['speed'] = {'74F-C': meta['C']['ground_speed_px_per_cycle']['96x128'], '74G': gmeta['C']['ground_speed_px_per_cycle']['96x128'], 'cycle_ms': 840}
if rep['speed']['74G'] != rep['speed']['74F-C']: fails.append('speed differs from 74F-C')
# ---- loop seam & frame differences
def consec(fn):
    return [int(np.any(L_(fn(f, '96x128')) != L_(fn((f + 1) % NF, '96x128')), axis=2).sum()) for f in range(NF)]
rep['frame_diff_96'] = {}
for v, fn in VER.items():
    c = consec(fn); rep['frame_diff_96'][v] = {'changed_px': c, 'seam_F11_F00': c[-1], 'max_other': max(c[:-1]), 'seam_ratio_to_max_other': round(c[-1] / max(c[:-1]), 3)}
    if v == '74G' and c[-1] > 1.1 * max(c[:-1]): fails.append(f'{v} loop seam')
# ---- design: reference identical to 74E (meta), protected files
rep['protected_sha256'] = {n: {p.name: sha(p) for p in sorted(d.glob('*.png'))} for n, d in (('74A', a.a74), ('74B', a.b74), ('74C', a.c74), ('74D', a.d74), ('74E', a.e74), ('74F', a.f74), ('right72', a.right72))}
rep['fails'] = fails; rep['technical_qa'] = 'PASS' if not fails else 'FAIL'
(a.art / 'QA_REPORT_74G.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding='utf-8')
with open(a.art / 'SHA256SUMS_74G.txt', 'w') as fh:
    for p in sorted(a.art.glob('*.png')) + sorted(a.art.glob('*.gif')):
        fh.write(f'{sha(p)}  {p.name}\n')
print(rep['technical_qa'], fails)
print(json.dumps(summ)); print({k: (v['max_drift_px'] if isinstance(v, dict) else v) for k, v in rep['foot_slide_96'].items()})
print({k: (v['seam_F11_F00'], v['max_other']) for k, v in rep['frame_diff_96'].items()})

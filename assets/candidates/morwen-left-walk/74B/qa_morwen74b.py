#!/usr/bin/env python3
"""ART-74B technical QA: format / transparency / ground / legs / changes vs 74A only in FIX zones / changes vs DEV only in the 74 edit zone.
  python3 qa_morwen74b.py --art <74B dir> --prev <74A dir> --dev <DEV dir> --right72 <72 dir> --repo <repo>"""
import os as _os, sys as _sys
_HERE=_os.path.dirname(_os.path.abspath(__file__))
_PIPE=_os.environ.get('MORWEN72_PIPELINE', _os.path.join(_HERE,'..','..','morwen-right-walk','72'))
_sys.path[:0]=[_HERE,_PIPE]
import argparse, json, hashlib
from pathlib import Path
import numpy as np
from PIL import Image
import build_morwen66 as B
from qa_morwen66 import components
ap = argparse.ArgumentParser()
for k in ('art', 'prev', 'dev', 'right72', 'repo'): ap.add_argument('--' + k, type=Path, required=True)
a = ap.parse_args()
L = lambda p: np.array(Image.open(p).convert('RGBA'))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
art = lambda d, f, s: d / f'morwen_left_walk_{f:02d}_{s}.png'
dev = lambda f, w: a.dev / f'm{w}_left_DEV_F{f:02d}.png'
r72 = lambda f, s: a.right72 / f'morwen_right_walk_{f:02d}_{s}.png'
def dil(m, n):
    o = m.copy()
    for _ in range(n): o = o | np.roll(o, 1, 0) | np.roll(o, -1, 0) | np.roll(o, 1, 1) | np.roll(o, -1, 1)
    return o
yy, xx = np.mgrid[0:128, 0:96]
e = np.array(Image.open(a.art / 'REFERENCE_EDIT_MASK_right_coords.png')) > 0
zone74 = dil(e, 4) | ((xx >= 34) & (xx <= 56) & (yy >= 72) & (yy <= 96))
# FIX zone = pixels where the 74B edited reference differs from the 74A edited reference (right coords), +3px motion reach
refdiff = np.any(L(a.art / 'REFERENCE_left_side_edit_right_coords.png') != L(a.prev / 'REFERENCE_left_side_edit_right_coords.png'), axis=2)
fixzone = dil(refdiff, 3)
rep = {'task': 'MORWEN-ASSET-74B', 'status': 'CANDIDATE - third-party art QA NOT_RUN, Android NOT_RUN', 'frames': []}
rep['reference_diff_74A_74B_px'] = {'total': int(refdiff.sum()), 'hat_y<=46': int((refdiff & (yy <= 46)).sum()), 'waist_y70-96': int((refdiff & (yy >= 70) & (yy <= 96)).sum()), 'other': int((refdiff & (yy > 46) & ((yy < 70) | (yy > 96))).sum())}
rep['sha256_right72_unchanged'] = {f'{f:02d}_{s}': sha(r72(f, s)) for f in range(6) for s in ('96x128', '48x64')}
fails = []
for f in range(6):
    ent = {'frame': f}
    for s, (w, h) in (('96x128', (96, 128)), ('48x64', (48, 64))):
        im = Image.open(art(a.art, f, s)); x = np.array(im)
        ok = im.mode == 'RGBA' and im.size == (w, h) and bool(np.isin(x[:, :, 3], (0, 255)).all()) and bool(np.all(x[x[:, :, 3] == 0, :3] == 0)) and not components(x[:, :, 3] > 0)[1:]
        sh = lambda z: (dil(np.roll(z, B.BOB[f], 0)[:, ::-1][1::2, 1::2], 1) if w == 48 else np.roll(z, B.BOB[f], 0)[:, ::-1])
        dA = np.any(x != L(art(a.prev, f, s)), axis=2); dD = np.any(x != L(dev(f, w)), axis=2)
        low = int(np.where(x[:, :, 3].any(1))[0].max()); lowA = int(np.where(L(art(a.prev, f, s))[:, :, 3].any(1))[0].max())
        ent[s] = {'format_ok': ok, 'changed_vs_74A': int(dA.sum()), 'changed_vs_74A_outside_fix_zone': int((dA & ~sh(fixzone)).sum()),
                  'changed_vs_dev_mirror': int(dD.sum()), 'changed_vs_dev_outside_74_zone': int((dD & ~sh(zone74)).sum()),
                  'lowest_row': low, 'lowest_row_74A': lowA, 'sha256': sha(art(a.art, f, s))}
        if not ok: fails.append(f'F{f} {s} format')
        if (dA & ~sh(fixzone)).any(): fails.append(f'F{f} {s} change outside FIX zone')
        if (dD & ~sh(zone74)).any(): fails.append(f'F{f} {s} change vs DEV outside 74 zone')
        if low != lowA: fails.append(f'F{f} {s} ground row moved')
    x = L(art(a.art, f, '96x128'))
    ent['legs_rows>=96_identical_to_74A'] = bool((x[96:] == L(art(a.prev, f, '96x128'))[96:]).all())
    ent['legs_rows>=96_identical_to_72_mirror'] = bool((x[96:] == L(r72(f, '96x128'))[:, ::-1][96:]).all())
    if not (ent['legs_rows>=96_identical_to_74A'] and ent['legs_rows>=96_identical_to_72_mirror']): fails.append(f'F{f} legs changed')
    rep['frames'].append(ent)
consec = lambda fn: [int(np.any(fn(f) != fn((f + 1) % 6), axis=2).sum()) for f in range(6)]
rep['consecutive_change_incl_F05_to_F00'] = {s: {'ART-74B': consec(lambda f: L(art(a.art, f, s))), 'ART-74A': consec(lambda f: L(art(a.prev, f, s)))} for s in ('96x128', '48x64')}
rep['fails'] = fails; rep['technical_qa'] = 'PASS' if not fails else 'FAIL'
(a.art / 'QA_REPORT_74B.json').write_text(json.dumps(rep, indent=1), encoding='utf-8')
S = 3
sh_ = Image.new('RGB', (6 * (96 * S + 6), 128 * S), (30, 30, 30))
for f in range(6):
    x = L(art(a.art, f, '96x128')); d = np.any(x != L(art(a.prev, f, '96x128')), axis=2)
    base = x.copy(); base[..., :3] //= 3; base[..., 3] = 255; base[d] = (255, 50, 50, 255)
    sh_.paste(Image.fromarray(base).convert('RGB').resize((96 * S, 128 * S), Image.NEAREST), (f * (96 * S + 6), 0))
sh_.save(a.art / 'CHANGE_MASK_74B_vs_74A.png')
print(rep['technical_qa'], fails)
print([(e_['96x128']['changed_vs_74A'], e_['48x64']['changed_vs_74A']) for e_ in rep['frames']])
print(rep['consecutive_change_incl_F05_to_F00'])

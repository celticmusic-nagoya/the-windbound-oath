#!/usr/bin/env python3
"""ART-74A technical QA + comparison sheets.  python3 qa_morwen74a.py --art <o74> --dev <DEV zip dir> --right72 <72 dir> --repo <repo>"""
import os as _os, sys as _sys
_HERE=_os.path.dirname(_os.path.abspath(__file__))
_PIPE=_os.environ.get('MORWEN72_PIPELINE', _os.path.join(_HERE,'..','..','morwen-right-walk','72'))
_sys.path[:0]=[_HERE,_PIPE]
import argparse, json, hashlib, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
pass; sys.path.insert(0, str(Path(__file__).parent))
import build_morwen66 as B
from qa_morwen66 import components
ap = argparse.ArgumentParser()
for k in ('art', 'dev', 'right72', 'repo'): ap.add_argument('--' + k, type=Path, required=True)
a = ap.parse_args()
L = lambda p: np.array(Image.open(p).convert('RGBA'))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
A, DV, R = a.art, a.dev, a.right72
art = lambda f, s: A / f'morwen_left_walk_{f:02d}_{s}.png'
dev = lambda f, w: DV / f'm{w}_left_DEV_F{f:02d}.png'
r72 = lambda f, s: R / f'morwen_right_walk_{f:02d}_{s}.png'
rep = {'task': 'MORWEN-ASSET-74 ART-74A', 'status': 'CANDIDATE - third-party art QA NOT_RUN, Android NOT_RUN', 'frames': []}
rep['sha256'] = {'master_v3': sha(a.repo / 'assets/companions/morwen/master/morwen-full-body-v3.png'),
                 'right72': {f'{f:02d}_{s}': sha(r72(f, s)) for f in range(6) for s in ('96x128', '48x64')}}
rep['dev_zip_equals_mirror_of_72'] = all((L(dev(f, 96)) == L(r72(f, '96x128'))[:, ::-1]).all() and (L(dev(f, 48)) == L(r72(f, '48x64'))[:, ::-1]).all() for f in range(6))
e = np.array(Image.open(A / 'REFERENCE_EDIT_MASK_right_coords.png')) > 0
def dil(m, n):
    o = m.copy()
    for _ in range(n): o = o | np.roll(o, 1, 0) | np.roll(o, -1, 0) | np.roll(o, 1, 1) | np.roll(o, -1, 1)
    return o
yy, xx = np.mgrid[0:128, 0:96]
zone = dil(e, 4) | ((xx >= 34) & (xx <= 56) & (yy >= 72) & (yy <= 96))   # edits + motion reach + side-skirt panel
fails = []; masks = []
for f in range(6):
    ent = {'frame': f}
    for s, (w, h) in (('96x128', (96, 128)), ('48x64', (48, 64))):
        im = Image.open(art(f, s)); x = np.array(im)
        ok = im.mode == 'RGBA' and im.size == (w, h) and bool(np.isin(x[:, :, 3], (0, 255)).all()) and bool(np.all(x[x[:, :, 3] == 0, :3] == 0)) and not components(x[:, :, 3] > 0)[1:]
        d = np.any(x != L(dev(f, w)), axis=2)
        z = np.roll(zone, B.BOB[f], 0)[:, ::-1]
        if w == 48: z = dil(z[1::2, 1::2], 1)
        ent[s] = {'format_ok': ok, 'changed_vs_dev_mirror': int(d.sum()), 'changed_outside_edit_zone': int((d & ~z).sum()),
                  'lowest_row': int(np.where(x[:, :, 3].any(1))[0].max()), 'sha256': sha(art(f, s))}
        if not ok: fails.append(f'F{f} {s} format')
        if (d & ~z).any(): fails.append(f'F{f} {s} outside zone')
        if w == 96: masks.append(d)
    x, dv = L(art(f, '96x128')), L(dev(f, 96))
    ent['legs_rows>=96_identical_to_72_mirror'] = bool((x[96:] == dv[96:]).all())
    if not ent['legs_rows>=96_identical_to_72_mirror']: fails.append(f'F{f} legs changed')
    ent['silhouette_px'] = {'art': int((x[:, :, 3] > 0).sum()), 'dev': int((dv[:, :, 3] > 0).sum())}
    rep['frames'].append(ent)
consec = lambda fn: [int(np.any(fn(f) != fn((f + 1) % 6), axis=2).sum()) for f in range(6)]
rep['consecutive_change'] = {s: {'ART-74A': consec(lambda f: L(art(f, s))), 'DEV': consec(lambda f: L(dev(f, 96 if s == '96x128' else 48)))} for s in ('96x128', '48x64')}
rep['fails'] = fails; rep['technical_qa'] = 'PASS' if not fails else 'FAIL'
(A / 'QA_REPORT_74A.json').write_text(json.dumps(rep, indent=1), encoding='utf-8')
S = 3
sh = Image.new('RGB', (6 * (96 * S + 6), 128 * S), (30, 30, 30))
for f, d in enumerate(masks):
    base = L(art(f, '96x128')).copy(); base[..., :3] //= 3; base[..., 3] = 255; base[d] = (255, 50, 50, 255)
    sh.paste(Image.fromarray(base).convert('RGB').resize((96 * S, 128 * S), Image.NEAREST), (f * (96 * S + 6), 0))
sh.save(A / 'CHANGE_MASK_74A_vs_DEV_mirror.png')
print(rep['technical_qa'], fails, rep['dev_zip_equals_mirror_of_72'])
print([(e_['96x128']['changed_vs_dev_mirror'], e_['48x64']['changed_vs_dev_mirror']) for e_ in rep['frames']])
print(rep['consecutive_change'])

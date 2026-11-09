#!/usr/bin/env python3
"""ART-74D static QA.
  python3 qa_morwen74d.py --art <74D dir> --c74 <74C dir> --b74 <74B dir> --a74 <74A dir> --right72 <72 dir> --official <official left PNG>
- format / transparency / size / one component / ground rows (8f, 12f)
- motion protection: alpha identical to 74C except inside the lower-leg zone (sock / boot outline), every frame
- part colour statistics (OKLab median chroma / hue / lightness) for official, 74C, 74D on the same part masks
- boot height and sock / boot separation per frame (96 and 48)
- loop seam, SHA-256 of all outputs and of the protected 74A / 74B / 74C / right 72 files."""
import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_PIPE = _os.environ.get('MORWEN72_PIPELINE', _os.path.join(_HERE, '..', '..', 'morwen-right-walk', '72'))
_sys.path[:0] = [_HERE, _PIPE]
import argparse, json, hashlib
from pathlib import Path
import numpy as np
from PIL import Image
from qa_morwen66 import components
from oklab import rgb2oklab, lch
from recolor74d import classes

ap = argparse.ArgumentParser()
for k in ('art', 'c74', 'b74', 'a74', 'right72', 'official'): ap.add_argument('--' + k, type=Path, required=True)
a = ap.parse_args()
L_ = lambda p: np.array(Image.open(p).convert('RGBA'))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
meta = json.loads((a.art / 'build_meta_74d.json').read_text())
fails, rep = [], {'task': 'MORWEN-ASSET-74D', 'static_qa': None, 'third_party_art_qa': 'NOT_RUN', 'android_device_qa': 'NOT_RUN'}
fn = lambda d, n, f, s: d / f'morwen_left_walk_{n}f_{f:02d}_{s}.png'
GROUND = {'96x128': 124, '48x64': 61}
LEG_ZONE = {'96x128': 95, '48x64': 47}     # rows >= : sock / boot (below the skirt hem)
fr = {}
for n in (8, 12):
    for f in range(n):
        for s, size in (('96x128', (96, 128)), ('48x64', (48, 64))):
            im = Image.open(fn(a.art, n, f, s)); x = np.array(im)
            ok = im.mode == 'RGBA' and im.size == size and bool(np.isin(x[:, :, 3], (0, 255)).all()) \
                and bool(np.all(x[x[:, :, 3] == 0, :3] == 0)) and not components(x[:, :, 3] > 0)[1:]
            low = int(np.where(x[:, :, 3].any(1))[0].max())
            c = L_(fn(a.c74, n, f, s))
            da = (x[:, :, 3] > 0) != (c[:, :, 3] > 0)
            out_zone = int(da[:LEG_ZONE[s]].sum())
            fr[f'{n}f_{f:02d}_{s}'] = {'format_ok': ok, 'lowest_row': low, 'alpha_diff_vs_74C': int(da.sum()),
                                       'alpha_diff_vs_74C_above_leg_zone': out_zone, 'sha256': sha(fn(a.art, n, f, s))}
            if not ok: fails.append(f'{n}f F{f} {s} format')
            if low != GROUND[s]: fails.append(f'{n}f F{f} {s} ground {low}')
            if out_zone: fails.append(f'{n}f F{f} {s} silhouette changed above the leg zone')
rep['frames'] = fr
# ---- part colour statistics (F00 96, mirrored part masks of the right-coords reference)
pm = L_(a.art / 'PART_MASKS_74D_right_coords.png')
PC = {'hat': (60, 60, 230), 'hair': (220, 50, 50), 'bow': (40, 200, 60), 'jacket': (240, 160, 30), 'skirt': (230, 40, 230), 'mantle': (40, 220, 220), 'potion': (150, 90, 255)}
def part_stats(img_right):
    out = {}
    for name, c in PC.items():
        _, _, _, _, gold, skin, white = classes(img_right[:, :, :3])
        m = np.all(pm[:, :, :3] == c, axis=2) & (img_right[:, :, 3] > 0) & ~gold & ~skin & ~white   # base cloth only
        if not m.any(): continue
        Lv, Cv, hv = lch(rgb2oklab(img_right[m][:, :3].astype(float)))
        r = np.radians(hv)
        out[name] = {'L_med': round(float(np.median(Lv)), 3), 'C_med': round(float(np.median(Cv)), 3),
                     'h_mean': round(float(np.degrees(np.arctan2(np.sin(r).mean(), np.cos(r).mean())) % 360), 1)}
    return out
ref74c = L_(a.c74 / 'REFERENCE_left_side_edit_right_coords.png'); ref74d = L_(a.art / 'REFERENCE_left_side_74D_colour_right_coords.png')
s74c, s74d = part_stats(ref74c), part_stats(ref74d)
offi = meta['official_targets']
rep['part_colour'] = {k: {'official': {'L_med': offi[k]['L'][2], 'C_med': offi[k]['C'], 'h': offi[k]['h']}, '74C': s74c.get(k), '74D': s74d.get(k)} for k in PC}
for k in ('hat', 'hair', 'bow', 'jacket', 'skirt', 'mantle'):
    o = offi[k]; d = s74d[k]; c = s74c[k]
    dh = abs(((d['h_mean'] - o['h'] + 180) % 360) - 180)
    if not (abs(d['C_med'] - o['C'] * meta['pixel_chroma_factor']) <= abs(c['C_med'] - o['C'] * meta['pixel_chroma_factor']) and dh <= 20):
        fails.append(f'colour {k} not closer to official')
# ---- magenta share (hue 330-360 / 0-10 with C > 0.12) over the whole frame
def magenta_share(img):
    m = img[:, :, 3] > 0; Lv, Cv, hv = lch(rgb2oklab(img[m][:, :3].astype(float)))
    return round(float((((hv > 330) | (hv < 10)) & (Cv > 0.12)).mean()), 4)
rep['magenta_share_96'] = {'74C_8f_F00': magenta_share(L_(fn(a.c74, 8, 0, '96x128'))), '74D_8f_F00': magenta_share(L_(fn(a.art, 8, 0, '96x128')))}
if rep['magenta_share_96']['74D_8f_F00'] >= rep['magenta_share_96']['74C_8f_F00']: fails.append('magenta not reduced')
# ---- boot height / sock-boot separation (palette membership)
ramps = meta['leg_ramps']
def legs(img, keyset):
    cols = {tuple(c) for k in keyset for c in ramps[k]}
    flat = img[:, :, :3].reshape(-1, 3); m = np.array([tuple(c) in cols for c in flat]).reshape(img.shape[:2]) & (img[:, :, 3] > 0)
    return m
bo = {}
for n in (8,):
    for f in range(n):
        for s in ('96x128', '48x64'):
            x = L_(fn(a.art, n, f, s)); c = L_(fn(a.c74, n, f, s))
            sock = legs(x, ('stock', 'stock_far')); boot = legs(x, ('boot', 'boot_far'))
            r_s = np.where(sock.any(1))[0]; r_b = np.where(boot.any(1))[0]
            bo[f'{f:02d}_{s}'] = {'boot_rows': [int(r_b.min()), int(r_b.max())] if len(r_b) else None,
                                  'sock_rows': [int(r_s.min()), int(r_s.max())] if len(r_s) else None,
                                  'sock_px': int(sock.sum()), 'boot_px': int(boot.sum())}
            if not len(r_s) or not len(r_b): fails.append(f'8f F{f} {s} sock/boot missing')
rep['sock_boot'] = bo
Ls = [rgb2oklab(np.array(c, float))[0] for c in ramps['stock']]; Lb = [rgb2oklab(np.array(c, float))[0] for c in ramps['boot']]
rep['sock_boot_lightness'] = {'sock_mid_L': round(float(np.mean(Ls[1:4])), 3), 'boot_mid_L': round(float(np.mean(Lb[1:4])), 3)}
rep['boot_design'] = {'74C_boot_top': 'just above the knee (t=-0.05 of knee->ankle)', '74D_boot_top_t': meta['boot_top_t']}
# ---- loop seam
def consec(n):
    c = [int(np.any(L_(fn(a.art, n, f, '96x128')) != L_(fn(a.art, n, (f + 1) % n, '96x128')), axis=2).sum()) for f in range(n)]
    return {'changed_px': c, 'seam_ratio_to_mean': round(c[-1] / float(np.mean(c)), 3)}
rep['loop_96'] = {'8f': consec(8), '12f': consec(12)}
for k, v in rep['loop_96'].items():
    if v['seam_ratio_to_mean'] > 1.5: fails.append(f'{k} loop seam jump')
# ---- protected
rep['protected_sha256'] = {name: {p.name: sha(p) for p in sorted(d.glob('*.png'))} for name, d in (('74A', a.a74), ('74B', a.b74), ('74C', a.c74), ('right72', a.right72))}
rep['official_left_sha256'] = sha(a.official)
rep['fails'] = fails; rep['static_qa'] = 'PASS' if not fails else 'FAIL'
(a.art / 'QA_REPORT_74D.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding='utf-8')
with open(a.art / 'SHA256SUMS_74D.txt', 'w') as fh:
    for p in sorted(a.art.glob('*.png')) + sorted(a.art.glob('*.gif')):
        fh.write(f'{sha(p)}  {p.name}\n')
print(rep['static_qa'], fails)
print(json.dumps(rep['part_colour'], ensure_ascii=False))
print(rep['magenta_share_96'], rep['sock_boot_lightness'], rep['sock_boot']['02_96x128'], rep['sock_boot']['02_48x64'])

#!/usr/bin/env python3
"""MORWEN-MODULAR-SPRITE-02 technical gate for a front / back 96x128 original (before art QA).
  python3 qa_original_still.py --still <png 96x128> [--still48 <png 48x64>] --facing down|up --repo ../../../.. [--out report.json]
Checks: size, full transparency (alpha 0/255), ground row 124 (48: 61-62), centre, height / width vs the side
frames, colour density and gold share vs 74G / 75 F00 (side_metrics.json), palette distance to the side ramps,
1-px islands, enclosed holes, detached pieces. A PASS here is NOT art QA: art QA stays a separate, independent gate."""
import argparse, json
from pathlib import Path
import numpy as np, cv2
from PIL import Image
ap = argparse.ArgumentParser()
ap.add_argument('--still', type=Path, required=True); ap.add_argument('--still48', type=Path); ap.add_argument('--facing', required=True)
ap.add_argument('--repo', type=Path, required=True); ap.add_argument('--out', type=Path)
a = ap.parse_args(); R = a.repo.resolve(); HERE = Path(__file__).resolve().parent
import sys; sys.path.insert(0, str(R / 'assets/candidates/morwen-left-walk/74D'))
from oklab import rgb2oklab, lch
LM = json.loads((HERE / 'LANDMARKS.json').read_text()); SM = json.loads((HERE / 'side_metrics.json').read_text())
pal = json.loads((HERE / 'palette_ramps.json').read_text())
P = np.array([[int(c['hex'][i:i + 2], 16) for i in (1, 3, 5)] for g in pal.values() for c in g]); PL = rgb2oklab(P.astype(float))
def islands(x):
    h, w = x.shape[:2]; c = x[:, :, :3].astype(int); op = x[:, :, 3] > 0; n = 0
    for y in range(1, h - 1):
        for xx in range(1, w - 1):
            if not op[y, xx]: continue
            nb = [tuple(c[y + dy, xx + dx]) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)) if op[y + dy, xx + dx]]
            if len(nb) == 4 and tuple(c[y, xx]) not in nb and max(nb.count(v) for v in nb) >= 3: n += 1
    return n
def check(p, size, ground):
    x = np.array(Image.open(p).convert('RGBA')); r = {'file': str(p)}; f = []
    r['size'] = list(x.shape[1::-1]); f += [] if x.shape[:2] == size[::-1] else ['size']
    al = set(np.unique(x[:, :, 3]).tolist()); r['alpha_values'] = sorted(al)[:6]; f += [] if al <= {0, 255} else ['semi-transparent pixels']
    op = x[:, :, 3] > 0; ys, xs = np.where(op)
    r['bottom_row'] = int(ys.max()); r['top_row'] = int(ys.min()); r['centre_x'] = round(float((xs.min() + xs.max()) / 2), 1)
    if r['bottom_row'] not in ground: f.append(f'ground row {r["bottom_row"]} not in {ground}')
    if abs(r['centre_x'] - size[0] / 2) > size[0] * 0.08: f.append('figure not centred')
    n, lab, st, _ = cv2.connectedComponentsWithStats(op.astype(np.uint8), connectivity=8); r['pieces'] = n - 1
    if n - 1 > 1: f.append(f'{n - 1} detached pieces')
    t = (~op).astype(np.uint8); nh, _ = cv2.connectedComponents(t, connectivity=4); r['enclosed_holes'] = nh - 2
    r['isolated_1px'] = islands(x)
    v = x[op][:, :3]; r['colours'] = int(len(np.unique(v, axis=0)))
    L, C, h = lch(rgb2oklab(v.astype(float))); r['gold_share'] = round(float(((h > 45) & (h < 115) & (C >= 0.085) & (L > 0.42)).mean()), 3)
    d = np.sqrt(((rgb2oklab(v.astype(float))[:, None] - PL[None]) ** 2).sum(-1)).min(1)
    r['palette_dist_median'] = round(float(np.median(d)), 4); r['palette_dist_p95'] = round(float(np.percentile(d, 95)), 4)
    if r['palette_dist_p95'] > 0.08: f.append('colours far from the side ramps (p95 > 0.08)')
    r['opaque_px'] = int(op.sum()); r['fails'] = f
    return r
rep = {'facing': a.facing, 'gate': 'technical (not art QA)', 's96': check(a.still, (96, 128), [124])}
side = list(SM.values())
ref = dict(colours=min(s['colours'] for s in side), gold=min(s['gold_share'] for s in side), px=np.mean([s['opaque_px'] for s in side]))
s = rep['s96']
if s['colours'] < 0.4 * ref['colours']: s['fails'].append(f'colour density {s["colours"]} < 40 % of the side frames ({ref["colours"]})')
if s['gold_share'] < 0.5 * ref['gold']: s['fails'].append(f'gold share {s["gold_share"]} < half of the side frames ({ref["gold"]})')
if not 0.75 * ref['px'] <= s['opaque_px'] <= 1.3 * ref['px']: s['fails'].append(f'body volume {s["opaque_px"]} px vs side ~{int(ref["px"])}')
if s['top_row'] > LM['hat_top'] + 3: s['fails'].append('hat lower than the side frames (top row)')
if a.still48: rep['s48'] = check(a.still48, (48, 64), [61, 62])
rep['result'] = 'PASS' if not any(v['fails'] for k, v in rep.items() if k.startswith('s')) else 'FAIL'
txt = json.dumps(rep, indent=1, default=str); (a.out.write_text(txt) if a.out else None); print(txt)

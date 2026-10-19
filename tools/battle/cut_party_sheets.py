#!/usr/bin/env python3
"""Cut a delivered 3x2 six-frame sheet (original untouched) into six game frames <actor>_<state>_NN.png (left-top -> right-bottom).
Pixels are copied 1:1 (no resample, no recolour); every frame is placed on ONE common canvas per state: aligned on the main body's foot row and body centre,
then padded with transparent pixels to a 3:2 aspect (the battle <img> is object-fit:contain, so apparent size follows the aspect).
usage: cut_party_sheets.py <sheet.png> <actor> <state> [--out DIR]   -> prints a JSON record (sizes, per-frame offsets, SHA-256)"""
import sys, os, json, hashlib
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
def seam(sig, lo, hi, axis, rng):
    a, b = rng; prof = sig[a:b, :].sum(axis=0) if axis == 0 else sig[:, a:b].sum(axis=1)
    k = int(np.argmin(prof[lo:hi])); return lo + k, int(prof[lo + k])
def cut(path, actor, state, out):
    im = Image.open(path).convert('RGBA'); a = np.array(im); al = a[..., 3]; H, W = al.shape; cols, rows = 3, 2
    cw, ch = W / cols, H / rows; sig = al >= 30; win = int(min(cw, ch) * .12)
    hy, hcost = seam(sig, int(ch) - win, int(ch) + win, 1, (0, W)); cost = [hcost]; boxes = []
    for r in range(rows):
        y0, y1 = (0, hy) if r == 0 else (hy, H); xc = [0]
        for c in range(1, cols): x, cs = seam(sig, int(c * cw) - win, int(c * cw) + win, 0, (y0, y1)); xc.append(x); cost.append(cs)
        xc.append(W); boxes += [(xc[c], y0, xc[c + 1], y1) for c in range(cols)]
    parts = []
    for (x0, y0, x1, y1) in boxes:
        m = np.zeros(al.shape, bool); m[y0:y1, x0:x1] = al[y0:y1, x0:x1] > 0
        ys, xs = np.where(m & (al >= 30)); bb = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
        lab, n = ndi.label(ndi.binary_dilation(m & (al >= 30), iterations=6)); sz = np.bincount(lab.ravel()); sz[0] = 0
        bm = (lab == int(sz.argmax())) & (al >= 200); by, bx = np.where(bm); foot = int(by.max()); cx = int(np.median(bx))
        # keep every pixel of the cell (faint glow too), not only the >=30 core
        bb = [min(bb[0], int(np.where(m)[1].min())), min(bb[1], int(np.where(m)[0].min())), max(bb[2], int(np.where(m)[1].max()) + 1), max(bb[3], int(np.where(m)[0].max()) + 1)]
        parts.append((np.where(m[..., None], a, 0).astype(np.uint8), bb, foot, cx))
    L = max(cx - bb[0] for _, bb, _, cx in parts); R = max(bb[2] - cx for _, bb, _, cx in parts); T = max(f - bb[1] for _, bb, f, _ in parts); B = max(bb[3] - f for _, bb, f, _ in parts)
    CW, CH = L + R, T + B
    if CW / CH < 1.5: CW2, CH2 = int(round(CH * 1.5)), CH
    else: CW2, CH2 = CW, int(round(CW / 1.5))
    padx, pady = (CW2 - CW) // 2, CH2 - CH
    rec = {'sheet': os.path.basename(path), 'sheet_sha256': hashlib.sha256(open(path, 'rb').read()).hexdigest(), 'sheet_size': [W, H], 'seam_alpha_px_cut': cost, 'canvas': [CW2, CH2], 'frames': []}
    os.makedirs(out, exist_ok=True)
    for n, (sub, bb, f, cx) in enumerate(parts, 1):
        c = Image.new('RGBA', (CW2, CH2), (0, 0, 0, 0)); ox, oy = padx + L - (cx - bb[0]), pady + T - (f - bb[1])
        c.alpha_composite(Image.fromarray(sub, 'RGBA').crop(tuple(bb)), (ox, oy))
        fn = os.path.join(out, '%s_%s_%02d.png' % (actor, state, n)); c.save(fn, optimize=True)
        ca = np.array(c)[..., 3]; opaque_in = int((np.array(Image.fromarray(sub, 'RGBA'))[..., 3] > 0).sum()); opaque_out = int((ca > 0).sum())
        rec['frames'].append({'file': os.path.basename(fn), 'offset': [ox, oy], 'foot_y': oy + (f - bb[1]), 'sha256': hashlib.sha256(open(fn, 'rb').read()).hexdigest(), 'nonzero_alpha_px_in_cell': opaque_in, 'nonzero_alpha_px_out': opaque_out})
        assert opaque_in == opaque_out, 'pixel loss in %s' % fn
    return rec
if __name__ == '__main__':
    p, actor, state = sys.argv[1:4]; out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(ROOT, 'img/battle/characters', actor, 'motion')
    print(json.dumps(cut(p, actor, state, out), indent=1))

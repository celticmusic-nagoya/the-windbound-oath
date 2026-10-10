#!/usr/bin/env python3
"""Cut a generated walk-cycle CONTACT SHEET (opaque JPG/PNG, flat background, one character per cell) into
1 frame = 1 transparent RGBA PNG, normalised for the field (shared scale, feet on one baseline, torso-centred).
usage: extract_walk_sheet.py <sheet> <npc_id> <cols>x<rows> <outdir> [--bg white|green] [--frames N] [--canvas WxH] [--height H]
  - background removed by border flood-fill against a fitted background (gradient-aware), edge colour un-mixed (no green/white halo)
  - caption text under the sheet is dropped (small components)
  - frames are returned in reading order (row by row); --frames keeps the first N
  - writes <outdir>/<npc_id>_walk_01.png .. and a contact preview <outdir>/<npc_id>_preview.png
Requires: pillow, numpy, scipy."""
import sys, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

def fit_bg(a, mode):
    h, w, _ = a.shape
    if mode == 'white': return np.full(a.shape, 255.0)
    # green: plane fit on the border band + dark-corner pixels, robust to the characters
    ys, xs = np.mgrid[0:h, 0:w]
    band = np.zeros((h, w), bool); b = max(6, min(h, w) // 40); band[:b] = band[-b:] = True; band[:, :b] = band[:, -b:] = True
    A = np.c_[np.ones(band.sum()), xs[band] / w, ys[band] / h]
    out = np.zeros(a.shape)
    for c in range(3):
        coef, *_ = np.linalg.lstsq(A, a[..., c][band], rcond=None)
        out[..., c] = coef[0] + coef[1] * xs / w + coef[2] * ys / h
    return out

def extract(path, mode, cols, rows):
    im = Image.open(path).convert('RGB'); a = np.asarray(im).astype(float)
    bg = fit_bg(a, mode)
    d = np.sqrt(((a - bg) ** 2).sum(-1))
    T = 38 if mode == 'green' else 30
    is_bg = d < T
    lab, n = ndi.label(is_bg)
    border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    outside = np.isin(lab, list(border))
    fg = ~outside
    fg = ndi.binary_opening(fg, iterations=1)
    # drop caption letters: keep components whose area is large; fill holes inside characters
    cl, cn = ndi.label(ndi.binary_closing(fg, iterations=3))
    areas = ndi.sum(np.ones_like(cl), cl, range(1, cn + 1))
    big = max(areas) * 0.25
    keep = np.isin(cl, [i + 1 for i, s in enumerate(areas) if s >= big])
    fg &= ndi.binary_dilation(keep, iterations=2)
    fg = ndi.binary_fill_holes(fg)
    # soft alpha from distance to the background near the boundary, then un-mix the background colour
    edge = ndi.binary_dilation(fg, iterations=2) & ~ndi.binary_erosion(fg, iterations=2)
    alpha = fg.astype(float)
    ramp = np.clip((d - T * 0.55) / (T * 1.1), 0, 1)
    alpha[edge] = np.where(fg[edge], np.maximum(ramp[edge], 0.0) * 0 + np.clip(ramp[edge] + 0.35, 0, 1), np.clip(ramp[edge] - 0.35, 0, 1))
    alpha[~ndi.binary_dilation(fg, iterations=2)] = 0
    al = np.clip(alpha, 0, 1)[..., None]
    F = np.where(al > 0.02, (a - (1 - al) * bg) / np.maximum(al, 0.02), a)
    F = np.clip(F, 0, 255)
    rgba = np.dstack([F, al[..., 0] * 255]).astype(np.uint8)
    # grid cells by clustering component centroids
    cl2, cn2 = ndi.label(alpha > 0.5)
    objs = ndi.find_objects(cl2)
    comps = []
    for i, sl in enumerate(objs):
        m = cl2[sl] == i + 1
        if m.sum() < big * 0.5: continue
        comps.append((sl, m))
    # merge fragments (detached hands/items) into the nearest big component horizontally overlapping
    comps.sort(key=lambda c: (c[0][0].start + c[0][0].stop) / 2)
    if len(comps) != cols * rows:
        raise SystemExit('expected %d characters, found %d components (adjust --bg / grid)' % (cols * rows, len(comps)))
    rowsets = [sorted(comps[r * cols:(r + 1) * cols], key=lambda c: (c[0][1].start + c[0][1].stop) / 2) for r in range(rows)]
    frames = []
    for r in rowsets:
        for sl, m in r:
            y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
            pad = 4
            y0, x0 = max(0, y0 - pad), max(0, x0 - pad); y1, x1 = min(rgba.shape[0], y1 + pad), min(rgba.shape[1], x1 + pad)
            crop = rgba[y0:y1, x0:x1].copy()
            full = np.zeros(rgba.shape[:2], bool); full[sl][m] = True
            crop[~ndi.binary_dilation(full[y0:y1, x0:x1], iterations=3), 3] = 0   # keep only this character
            frames.append(Image.fromarray(crop, 'RGBA'))
    return frames

def normalise(frames, canvas, height):
    W, H = canvas
    hs = [f.getchannel('A').point(lambda v: 255 if v > 24 else 0).getbbox() for f in frames]
    heights = sorted(b[3] - b[1] for b in hs); med = heights[len(heights) // 2]
    s = height / med
    out = []
    for f, b in zip(frames, hs):
        f = f.crop(b); f = f.resize((max(1, round(f.width * s)), max(1, round(f.height * s))), Image.LANCZOS)
        a = np.asarray(f.getchannel('A')) > 24
        cx = int(np.average(np.where(a)[1])) if a.any() else f.width // 2      # torso-centred: centroid, not bbox
        c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        c.alpha_composite(f, (W // 2 - cx, H - 12 - f.height)); out.append(c)
    return out

if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) < 4: print(__doc__); sys.exit(2)
    sheet, npc, grid, outdir = a[:4]
    cols, rows = map(int, grid.lower().split('x'))
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    mode = opt('--bg', 'green'); canvas = tuple(map(int, opt('--canvas', '420x520').split('x'))); height = int(opt('--height', '400'))
    os.makedirs(outdir, exist_ok=True)
    frames = normalise(extract(sheet, mode, cols, rows), canvas, height)
    n = int(opt('--frames', len(frames))); frames = frames[:n]
    for i, f in enumerate(frames, 1): f.save(os.path.join(outdir, '%s_walk_%02d.png' % (npc, i)), optimize=True)
    prev = Image.new('RGB', (canvas[0] * len(frames) // 2, canvas[1] // 2), (70, 100, 80))
    for i, f in enumerate(frames):
        t = f.resize((canvas[0] // 2, canvas[1] // 2), Image.LANCZOS); prev.paste(t, (i * canvas[0] // 2, 0), t)
    prev.save(os.path.join(outdir, npc + '_preview.png')); print('wrote', len(frames), 'frames for', npc, '->', outdir)

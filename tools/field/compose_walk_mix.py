#!/usr/bin/env python3
"""Compose one hero's walk set from NEW (prepare_new_walk.py output) and OLD (previous installed) frames on a COMMON canvas,
registered by the BODY (torso centre column) instead of the cropped-bbox left edge, so the torso stays put while the feet swing
(left-edge registration made the body drift against the stride = skating). Then run install_hero_frames.py on the result.
usage: compose_walk_mix.py <hero> <new_dir> <old_dir> <out_dir> <spec.json>   (see main())
  every frame is scaled so the (new|old) idle_down body height = 1000 px; the canvas is 1600x1500, body column 800, feet row 1400."""
import sys, os, numpy as np
from PIL import Image
def bbox(a, t=16):
    ys, xs = np.where(a[..., 3] > t); return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
def load(p): return np.array(Image.open(p).convert('RGBA'))
def body_x(a):
    x0, y0, x1, y1 = bbox(a); h = y1 - y0
    cols = np.where(a[y0 + int(h * .40):y0 + int(h * .62), :, 3] > 16)[1]
    return float((np.percentile(cols, 25) + np.percentile(cols, 75)) / 2)
def put(src, dst, k):
    a = load(src); bx = body_x(a); x0, y0, x1, y1 = bbox(a)
    im = Image.fromarray(a[y0:y1, x0:x1]); im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    cv = Image.new('RGBA', (1600, 1500), (0, 0, 0, 0)); cv.alpha_composite(im, (800 - round((bx - x0) * k), 1400 - im.height)); cv.save(dst)
def main():
    """compose_walk_mix.py <hero> <new_dir> <old_dir> <out_dir> <spec.json>
    spec: {"idle": {"down": "old", ...}, "walk": {"down": [["old", 1], ["new", 4], ...], ...}}  (frame numbers refer to the source dir's walk_<dir>_NN)"""
    import json
    hero, newd, oldd, out, spec = sys.argv[1:6]; spec = json.load(open(spec)); os.makedirs(out, exist_ok=True)
    def h(p): a = load(p); b = bbox(a); return b[3] - b[1]
    src = {'new': (newd, 1000 / h(f'{newd}/{hero}_idle_down.png')), 'old': (oldd, 1000 / h(f'{oldd}/{hero}_idle_down.png'))}
    for d in ['down', 'left', 'right', 'up']:
        sd, k = src[spec['idle'][d]]; put(f'{sd}/{hero}_idle_{d}.png', f'{out}/{hero}_idle_{d}.png', k)
        for n, (which, i) in enumerate(spec['walk'][d], 1):
            sd, k = src[which]; put(f'{sd}/{hero}_walk_{d}_{i:02d}.png', f'{out}/{hero}_walk_{d}_{n:02d}.png', k)
        print(d, [f'{w[0]}{i}' for w, i in [(w, i) for w, i in spec['walk'][d]]])
main()

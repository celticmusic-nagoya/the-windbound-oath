#!/usr/bin/env python3
"""GOBLIN-20F-FIX01: restore the head volume of the 4 back-view (walk_up) goblin frames.

The back-view frames were drawn with a flat, low hood whose top fades to semi-transparent pixels, so the head reads as
missing. This adds, *underneath* each existing up frame, the hood cap of the same goblin taken from walk_down_01
(cloth pixels above the face only, mirrored for the back view), aligned to each frame's hood and walk bob.
Every existing visible pixel of the up frame stays on top; feet/anchor (160,288), canvas, scale and other frames are unchanged.
Run from the repo root. Idempotent only from the original #119 frames (keeps their SHA in the manifest note)."""
import hashlib, json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'img/field/monsters/goblin'
ORIGINAL_UP_SHA = {1: '8c9d46d20150246ba7a93b470b13536f80212280880c912bb4f1765d83363ff3',
                   2: '26e1040a8e3bce524ba1e189ea5078ade73f0096ec35b4f4b9c8894eb0b7c03b',
                   3: '44046759aface0e71aa7242df3eb3950bd9dea7110d0feaa2d134b02ed55e7b3',
                   4: '14b49e1c0a9d1a7e4843d9428c75d91686e7ea68842ea9a83a843eb012f677d0'}
RAISE = 16   # back hood top sits this many px above the flat top, matching the front view's head height


def cloth(a):
    r, g, b, al = (a[..., i].astype(int) for i in range(4))
    return (al > 128) & (r > g + 8) & (r > b + 25)   # hood cloth; ears/skin are olive (g >= r)


def hood_cap(a, ymax=112):
    m = np.zeros(a.shape[:2], bool); m[:ymax] = cloth(a)[:ymax]
    lab, n = ndimage.label(m, np.ones((3, 3)))
    m = lab == (1 + int(np.argmax(ndimage.sum(m, lab, range(1, n + 1)))))
    m = ndimage.binary_fill_holes(ndimage.binary_closing(m, iterations=2)) & (a[..., 3] > 128)
    cap = np.zeros_like(a); cap[m] = a[m]; cap[m, 3] = 255
    return cap[:, ::-1]   # back view: mirrored


def main():
    cap = hood_cap(np.array(Image.open(D / 'goblin_walk_down_01.png').convert('RGBA')))
    ys, xs = np.nonzero(cap[..., 3]); cx, ctop = (xs.min() + xs.max()) / 2, ys.min()
    log = []
    for i in range(1, 5):
        p = D / f'goblin_walk_up_{i:02d}.png'
        assert hashlib.sha256(p.read_bytes()).hexdigest() == ORIGINAL_UP_SHA[i], f'{p.name} is not the #119 original'
        up = np.array(Image.open(p).convert('RGBA'))
        yy, xx = np.nonzero(cloth(up)[:130]); top, ux = yy.min(), (xx.min() + xx.max()) / 2
        dy, dx = int(top - RAISE - ctop), int(round(ux - cx))
        assert ctop + dy >= 0
        layer = Image.fromarray(np.roll(np.roll(cap, dy, 0), dx, 1), 'RGBA')
        layer.alpha_composite(Image.fromarray(up, 'RGBA'))
        out = np.array(layer); out[out[..., 3] == 0] = 0
        assert (out[160:] == np.where(up[160:, :, 3:] == 0, 0, up[160:])).all(), 'body / feet must be untouched'
        Image.fromarray(out, 'RGBA').save(p, optimize=True)
        log.append({'frame': p.name, 'cap_offset': [dx, dy], 'hood_top_before': int(top), 'hood_top_after': int(ctop + dy),
                    'before_sha256': ORIGINAL_UP_SHA[i], 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
    print(json.dumps(log, indent=1))
    return log


if __name__ == '__main__':
    main()

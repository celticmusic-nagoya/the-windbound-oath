#!/usr/bin/env python3
"""GOBLIN-20F-FIX01 (down): install the director-delivered front-view walk cycle (4 frames, alternating legs).
Delivered bytes are kept unchanged in assets/candidates/goblin-field-20f/fix01-down-delivered/. The game copies only drop
detached specks (<12 px, 8-connectivity) and keep transparent RGB at 0; every pixel of the figure is unchanged.
Canvas 320x320, anchor (160,288) and scale are the same as the other goblin frames. Run from the repo root."""
import hashlib, json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'assets/candidates/goblin-field-20f/fix01-down-delivered'
DST = ROOT / 'img/field/monsters/goblin'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    log = []
    for i in range(1, 5):
        name = f'goblin_walk_down_{i:02d}.png'
        a = np.array(Image.open(SRC / name).convert('RGBA'))
        assert a.shape == (320, 320, 4)
        lab, n = ndimage.label(a[..., 3] > 0, np.ones((3, 3)))
        sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
        drop = np.isin(lab, [k + 1 for k, s in enumerate(sizes) if s < 12])
        a[drop] = 0; a[a[..., 3] == 0] = 0
        ys = np.nonzero(a[..., 3] > 128)[0]
        assert 280 <= ys.max() <= 289, (name, ys.max())          # feet on the shared anchor row
        out = DST / name; Image.fromarray(a, 'RGBA').save(out, optimize=True)
        log.append({'frame': name, 'delivered_sha256': sha(SRC / name), 'speck_pixels_removed': int(drop.sum()), 'sha256': sha(out)})
    print(json.dumps(log, indent=1)); return log


if __name__ == '__main__':
    main()

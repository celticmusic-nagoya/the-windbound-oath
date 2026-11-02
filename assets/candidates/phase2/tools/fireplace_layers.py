"""Build fireplace body / fire / composite from a lit and an unlit drawing normalised with identical transforms.
fire = lit pixels inside the opening (where lit differs from unlit); composite = body with fire pasted -> body+fire == composite exactly."""
import sys, json, pathlib
import numpy as np
from PIL import Image
from scipy import ndimage

def build(lit_p, body_p, outdir, box):
    L = np.array(Image.open(lit_p).convert('RGBA')); B = np.array(Image.open(body_p).convert('RGBA'))
    x0, y0, x1, y1 = box; roi = np.zeros(L.shape[:2], bool); roi[y0:y1, x0:x1] = True
    d = (np.abs(L.astype(int) - B).max(2) > 24) & roi
    m = ndimage.binary_closing(d, np.ones((5, 5)), iterations=2); m = ndimage.binary_fill_holes(m) & roi
    lab, n = ndimage.label(m); m = lab == (1 + np.argmax(ndimage.sum(m, lab, range(1, n + 1))))
    m &= (L[..., 3] > 0) & (B[..., 3] > 0)
    fire = np.zeros_like(L); fire[m] = L[m]; comp = B.copy(); comp[m] = L[m]
    out = pathlib.Path(outdir); out.mkdir(parents=True, exist_ok=True)
    for name, a in [('body', B), ('fire', fire), ('', comp)]:
        Image.fromarray(a, 'RGBA').save(out / ('furn_h01_fireplace' + ('_' + name if name else '') + '.png'), optimize=True)
    ys, xs = np.nonzero(m); return dict(fire_px=int(m.sum()), fire_bbox=[int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1])

if __name__ == '__main__':
    print(json.dumps(build(sys.argv[1], sys.argv[2], sys.argv[3], [int(v) for v in sys.argv[4].split(',')])))

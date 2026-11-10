"""Place figures on a 1200x1600 canvas so that the measured boot contact sits on (600,1540).
Contact = lowest alpha>=128 row (y) and the centre of the outer sole span 6 rows above it (x),
the same definition as scripts/qa_morwen_final_align.py. Integer translation only (no scaling). Alpha: >=250 -> 255, <=12 -> 0, detached specks and faint haze (>2 px outside, alpha<64) removed.
Usage: python3 place_auto.py OUT_DIR name=path [name=path ...]"""
import json, sys, numpy as np
from PIL import Image
W, H, AX, AY = 1200, 1600, 600, 1540
def runs(r):
    xs = np.nonzero(r)[0]; out = []; s = q = xs[0]
    for x in xs[1:]:
        if x != q + 1: out.append((int(s), int(q))); s = x
        q = x
    out.append((int(s), int(q))); return out
out_dir = sys.argv[1]; meta = {}
for arg in sys.argv[2:]:
    name, path = arg.split("=", 1)
    im = Image.open(path).convert("RGBA"); a = np.asarray(im)
    al = a[..., 3] >= 128
    b = int(np.nonzero(al.any(1))[0].max())
    segs = [(x0 + 300, x1 + 300) for x0, x1 in runs(al[b - 6, 300:820]) if x1 - x0 > 12]
    cx = (segs[0][0] + segs[-1][1]) / 2
    ox, oy = int(round(AX - cx)), AY - b
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sx, sy = max(0, -ox), max(0, -oy)
    assert not a[:sy, :, 3].any() and not a[:, :sx, 3].any(), "content would be cut"
    canvas.alpha_composite(im.crop((sx, sy, im.width, im.height)), (ox + sx, oy + sy))
    c = np.asarray(canvas).copy(); A = c[..., 3]; A[A >= 250] = 255; A[A <= 12] = 0
    from scipy import ndimage as ndi   # drop detached specks (< 600 px pieces not joined to the figure)
    lab, n = ndi.label(A > 0, structure=np.ones((3, 3)))
    if n > 1:
        sz = np.bincount(lab.ravel()); sz[0] = 0; main = sz.argmax()
        A[(lab != main) & (lab > 0) & (sz[lab] < 600)] = 0
    # faint haze: alpha < 64 more than 2 px outside the solid (alpha >= 128) outline
    A[(A < 64) & (ndi.distance_transform_edt(A < 128) > 2)] = 0
    c[A == 0, :3] = 0
    Image.fromarray(c, "RGBA").save(f"{out_dir}/morwen_{name}_aligned.png", optimize=True)
    meta[name] = dict(source=path, contact_source=[cx, b], contact_segments=segs, offset=[ox, oy], residual_x=round(ox + cx - AX, 2))
json.dump(meta, open(f"{out_dir}/place_meta.json", "w"), indent=1); print(json.dumps(meta))

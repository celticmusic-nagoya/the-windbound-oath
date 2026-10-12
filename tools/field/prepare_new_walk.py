#!/usr/bin/env python3
"""Turn the delivered walk sheets (aidan_fiona_new_walk.zip, 2026-10) into the per-frame source set that install_hero_frames.py expects.
usage: prepare_new_walk.py <extracted_zip_dir> <out_dir>      then:  install_hero_frames.py <out_dir>/<hero> --hero <hero> --height-world <printed> --xs 1.0 [--mixed-walk-counts]

What it does (the sheets are RGBA but carry a wide semi-transparent halo + speckles around the art):
  * splits each 6-frame sheet into cells (cut at the emptiest column near each boundary),
  * keeps only the opaque art (alpha >= 235), drops speckles / halo, softens the edge,
  * mirrors right-facing art for the left direction,
  * scales every direction to ONE body height (staff excluded) so the hero does not change size when turning,
  * picks the idle pose = the walk frame with the feet closest together,
  * Fiona has no delivered back view: her existing 'up' frames (same design) are reused, scaled to the same body height.
Delivered files (zip names -> role): see SHEETS below."""
import os, sys, glob
import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage as ndi
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
SHEETS = {   # role: (file, row, n_rows, facing)
    'aidan_down':  ('file_000000003ba08206899ce3138cf0e68f.png', 0, 1, 'front'),
    'aidan_up':    ('file_00000000740c82099a25818601204d7f.png', 0, 1, 'back'),
    'aidan_right': ('file_000000004efc81f6ac45a4be5cb94856.png', 0, 2, 'right'),   # 1536x1024, 2 rows x 6: row 0, sword on the back (matches the front/back sheets)
    'fiona_right': ('file_000000007920820986c7033f11b79209.png', 0, 1, 'right'),
    'fiona_down':  ('file_000000007a6c8206a9416cabec351c29.png', 0, 1, 'front'),
}
BODY_H = 1000   # px: every direction of a hero is scaled so that its body (head top -> feet) is this tall
def clean(rgba, thr=235, keep_frac=0.012, close=3):
    a = rgba[..., 3]
    m = ndi.binary_fill_holes(ndi.binary_closing(a >= thr, iterations=close))
    lab, n = ndi.label(m)
    if n == 0: return rgba
    sizes = ndi.sum(m, lab, range(1, n + 1)); keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s >= sizes.max() * keep_frac])
    near = ndi.binary_dilation(keep, iterations=2)
    soft = np.clip((a.astype(np.float32) - 60) / (thr - 60), 0, 1) * near
    out = rgba.copy(); out[..., 3] = np.where(keep, 255, soft * 255).astype(np.uint8)
    red = (rgba[..., 0] > 215) & (rgba[..., 1] < 45) & (rgba[..., 2] < 45)    # pure-red matting speckles (the art has none)
    out[..., 3][ndi.binary_dilation(red, iterations=2)] = 0
    return out
def bbox(a, t=16):
    ys, xs = np.where(a[..., 3] > t); return (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
def cells_cut(rgba, n, row, rows):
    """Cut at the emptiest column near each boundary; art pieces that touch a cut (the neighbour's toe / staff / cape tip) are dropped."""
    H, W = rgba.shape[:2]; rh = H // rows; part = rgba[row * rh:(row + 1) * rh]
    col = (part[..., 3] > 200).sum(0).astype(float); cuts = [0]
    for i in range(1, n):
        c = int(W * i / n); lo, hi = c - int(W / n * .12), c + int(W / n * .12); cuts.append(lo + int(np.argmin(col[lo:hi])))
    cuts.append(W); out = []
    for i in range(n):
        fr = part[:, cuts[i]:cuts[i + 1]].copy(); m = ndi.binary_closing(fr[..., 3] >= 235, iterations=2); lab, k = ndi.label(m)
        if k > 1:
            sizes = ndi.sum(m, lab, range(1, k + 1)); main = int(np.argmax(sizes)) + 1; keep = lab == main
            for j, sl in enumerate(ndi.find_objects(lab), 1):
                if j != main and sl[1].start > 2 and sl[1].stop < fr.shape[1] - 2 and sizes[j - 1] > 40: keep |= lab == j   # inner pieces (ribbons, leaves) stay
            keep = ndi.binary_dilation(keep, iterations=3); fr[..., 3] = np.where(keep, fr[..., 3], 0)
        out.append(fr)
    return out
def cells(rgba, n=6, row=0, rows=1):
    """Split one sheet row into n frames. Frames overlap a little (cape tips, toes), so cutting at fixed columns slices art; instead label the opaque
    art, take the n biggest pieces as the bodies and hand every small piece (toe, staff leaves, ribbon tip) to the nearest body."""
    H, W = rgba.shape[:2]; rh = H // rows; part = rgba[row * rh:(row + 1) * rh].copy()
    m = ndi.binary_closing(part[..., 3] >= 235, iterations=2)
    lab, k = ndi.label(m); idx = list(range(1, k + 1)); sizes = np.array(ndi.sum(m, lab, idx)); boxes = ndi.find_objects(lab)
    order = np.argsort(-sizes)
    if k < n or sizes[order[n - 1]] < sizes[order[0]] * .2: return cells_cut(rgba, n, row, rows)   # figures touch each other: fall back to column cuts
    bodies = sorted(order[:n], key=lambda i: (boxes[i][1].start + boxes[i][1].stop) / 2); owner = {int(b): j for j, b in enumerate(bodies)}
    def gap(a, b):
        ya, xa, yb, xb = boxes[a][0], boxes[a][1], boxes[b][0], boxes[b][1]
        return max(0, max(xa.start, xb.start) - min(xa.stop, xb.stop)) + max(0, max(ya.start, yb.start) - min(ya.stop, yb.stop))
    for i in order[n:]:
        if sizes[i] < 40: continue
        j = min(bodies, key=lambda b: gap(i, b))
        if gap(i, j) <= 36: owner[int(i)] = owner[int(j)]
    out = []
    for f in range(n):
        keep = np.isin(lab, [i + 1 for i, o in owner.items() if o == f]); keep = ndi.binary_dilation(keep, iterations=3)
        fr = part.copy(); fr[..., 3] = np.where(keep, fr[..., 3], 0); out.append(fr)
    return out
def body_height(a, staff):
    x0, y0, x1, y1 = bbox(a)
    if not staff: return y1 - y0
    xc = x0 + int((x1 - x0) * .62); ys = np.where(a[:, x0:xc, 3] > 16)[0]    # staff sits to the right of the head
    return y1 - ys.min()
def feet_spread(a):
    x0, y0, x1, y1 = bbox(a); band = a[int(y1 - (y1 - y0) * .12):y1, :, 3] > 16; xs = np.where(band.any(0))[0]; return xs.max() - xs.min()
def pad(a, m=8):
    return np.pad(a, ((m, m), (m, m), (0, 0)))   # transparent margin: the intake tool rejects opaque canvas corners
def save_set(hero, direction, frames, out, idle_idx):
    d = os.path.join(out, hero); os.makedirs(d, exist_ok=True); idle = frames[idle_idx]; frames = [pad(a) for a in frames]; idle = pad(idle)
    for i, a in enumerate(frames, 1): Image.fromarray(a).save(os.path.join(d, '%s_walk_%s_%02d.png' % (hero, direction, i)))
    Image.fromarray(idle).save(os.path.join(d, '%s_idle_%s.png' % (hero, direction)))
def normalise(frames, staff=False):
    hs = [body_height(a, staff) for a in frames]; k = BODY_H / float(np.median(hs)); out = []
    for a in frames:
        x0, y0, x1, y1 = bbox(a); im = Image.fromarray(a[y0:y1, x0:x1]); im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS); out.append(np.array(im))
    return out
def main():
    if len(sys.argv) < 3: print(__doc__); sys.exit(2)
    src, out = sys.argv[1], sys.argv[2]; res = {}
    for role, (f, row, rows, face) in SHEETS.items():
        hero, d = role.split('_'); a = np.array(Image.open(os.path.join(src, f)).convert('RGBA'))
        fr = [clean(c) for c in cells(a, 6, row, rows)]; res[role] = normalise(fr, staff=(role == 'fiona_down'))
    for hero in ('aidan', 'fiona'):
        sets = {d: res['%s_%s' % (hero, d)] for d in ('down', 'up', 'right') if '%s_%s' % (hero, d) in res}
        if hero == 'fiona':   # no delivered back view -> reuse the existing 'up' frames (same character design)
            old = [np.array(Image.open(f).convert('RGBA')) for f in sorted(glob.glob(os.path.join(ROOT, 'img/field/moss/real/fiona/fiona_walk_up_0*.png')))]
            sets['up'] = normalise(old)
        sets['left'] = [np.array(ImageOps.mirror(Image.fromarray(a))) for a in sets['right']]
        for d, fr in sets.items(): save_set(hero, d, fr, out, int(np.argmin([feet_spread(a) for a in fr])))
        idle = np.array(Image.open(os.path.join(out, hero, '%s_idle_down.png' % hero))); bh = bbox(idle); ratio = (bh[3] - bh[1]) / float(body_height(idle, hero == 'fiona'))
        body_world = 59.5 if hero == 'aidan' else 58.0     # on-screen body height (world px), matches the previous art's walk frames
        print('%s: frames ok; run install_hero_frames.py %s --hero %s --height-world %.2f --xs 1.0%s' % (hero, os.path.join(out, hero), hero, body_world * ratio, ' --mixed-walk-counts' if hero == 'fiona' else ''))
main()

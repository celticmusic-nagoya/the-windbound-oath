#!/usr/bin/env python3
"""PLAYER-WALK-POLISH-02: rebuild a walk frame's legs from ANOTHER official frame (no mirroring).

The donor's leg pixels (trousers + boots, as painted, same lighting) are moved by the hip offset
between the two official frames and drawn UNDER the base frame's own cape/tunic/hem. Inside the
leg rectangle the base's own leg pixels are removed; everything else is the base frame untouched.
usage: compose_legs.py BASE DONOR OUT --rect X0 Y0 X1 Y1 [--dx N --dy N] [--blend ROWS] [--debug DIR]
  --dx/--dy : donor shift; default = phase correlation of the hip band (y 600..880)
  --blend   : rows above the rectangle top over which the donor trousers fade into the base trousers
"""
import argparse, json, os, sys
import numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mirror_legs import leg_mask  # noqa: E402  (colour/shape test of trousers+boots only; no mirroring used)

LEGS = [(0, 38, 0.42, 1.0)]


def lum(a, y0, y1):
    return (a[..., :3].mean(-1) * (a[..., 3] / 255)).astype(np.float32)[y0:y1]


def raw_leg(a):
    rgb = a[..., :3].astype(float) / 255; mx, mn = rgb.max(-1), rgb.min(-1); d = mx - mn + 1e-9
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, (g - b) / d % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    s = np.where(mx > 0, d / (mx + 1e-9), 0)
    return (a[..., 3] > 24) & ((((h <= 38) | (h >= 345)) & (s >= 0.42)) | ((mx < 0.30) & ~((h > 60) & (h < 200) & (s > 0.15))))


def over(t, b):
    ta, ba = t[..., 3:4] / 255, b[..., 3:4] / 255; oa = ta + ba * (1 - ta)
    return np.concatenate([(t[..., :3] * ta + b[..., :3] * ba * (1 - ta)) / np.maximum(oa, 1e-6), oa * 255], -1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('base'); p.add_argument('donor'); p.add_argument('out')
    p.add_argument('--rect', nargs=4, type=int, required=True)
    p.add_argument('--dx', type=float); p.add_argument('--dy', type=float)
    p.add_argument('--blend', type=int, default=0)
    p.add_argument('--debug')
    p.add_argument('--top-band', type=int, default=0, help='rows below the rectangle top swapped by colour only (attempt 3)')
    p.add_argument('--fill-holes', action='store_true', help='inpaint enclosed empty pixels; their mask is saved next to OUT')
    p.add_argument('--drop-specks', type=int, default=0, help='max size of floating base cloth fragments replaced by the donor leg (attempt 4)')
    p.add_argument('--layered', action='store_true', help='keep every non-leg pixel of the base on top (attempt 2)')
    o = p.parse_args()
    B = np.array(Image.open(o.base).convert('RGBA')); D = np.array(Image.open(o.donor).convert('RGBA'))
    if o.dx is None:
        (sx, sy), _ = cv2.phaseCorrelate(lum(B, 600, 880), lum(D, 600, 880))
        dx, dy = -round(sx), -round(sy)          # move the donor onto the base's hips
    else:
        dx, dy = round(o.dx), round(o.dy or 0)
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    Ds = cv2.warpAffine(D, M, (D.shape[1], D.shape[0]), flags=cv2.INTER_NEAREST, borderValue=(0, 0, 0, 0))
    mb = leg_mask(B, o.rect, LEGS, 0.30)          # base legs (removed)
    md = leg_mask(Ds, o.rect, LEGS, 0.30)         # donor legs (inserted)
    if o.layered:
        # attempt 2: per-pixel colour test instead of the filled region, so the base frame's own
        # cape / tunic / frills inside the rectangle stay on top and are never cut
        rb, rd = raw_leg(B), raw_leg(Ds)
        mb = ndi.binary_dilation(mb & rb, iterations=1) & mb       # base leg pixels (+1px rim)
        md = md & (rd | ndi.binary_erosion(md, iterations=3))       # donor legs, without donor frills
    if o.top_band:
        # attempt 3: filled masks for the boots (keeps their bright highlights), but in the top band
        # where the legs meet the tunic/frills, only true leg-coloured pixels are swapped
        rb, rd = raw_leg(B), raw_leg(Ds)
        band = np.zeros(B.shape[:2], bool); band[o.rect[1]:o.rect[1] + o.top_band] = True
        mb = np.where(band, mb & ndi.binary_dilation(rb, iterations=1), mb)
        md = np.where(band, md & rd, md)
    if o.drop_specks:
        # attempt 4: small base cloth fragments in the top band that would float on the new knee
        # (pieces of frill that hung in front of the OLD leg, not attached to the tunic/cape) give way to the donor leg
        band = np.zeros(B.shape[:2], bool); band[o.rect[1]:o.rect[1] + o.top_band, o.rect[0]:o.rect[2]] = True
        cloth = (B[..., 3] > 24) & ~mb & band
        lab, n = ndi.label(cloth)
        attached = set(np.unique(lab[o.rect[1]:o.rect[1] + 2])) - {0}   # pieces touching the band top belong to the tunic/cape
        sizes = ndi.sum(cloth, lab, range(1, n + 1))
        speck = np.isin(lab, [i for i in range(1, n + 1) if i not in attached and sizes[i - 1] < o.drop_specks]) & ndi.binary_dilation(md, iterations=2)
        mb = mb | speck
    rest = B.astype(float).copy(); rest[mb, 3] = 0
    legs = np.zeros_like(rest); legs[md] = Ds[md]
    if o.blend:   # fade the donor trousers in above the cut so there is no hard horizontal seam
        y0 = o.rect[1]; w = np.zeros(B.shape[:2])
        for i in range(o.blend):
            w[y0 - o.blend + i] = (i + 1) / (o.blend + 1)
        band = np.zeros(B.shape[:2], bool); band[y0 - o.blend:y0, o.rect[0]:o.rect[2]] = True
        dark = band & (Ds[..., 3] > 200) & (Ds[..., :3].mean(-1) < 110) & (B[..., :3].mean(-1) < 110) & (B[..., 3] > 200)
        rest[dark, :3] = rest[dark, :3] * (1 - w[dark, None]) + Ds[dark, :3] * w[dark, None]
    out = over(rest, legs)
    filled = 0
    if o.fill_holes:
        # pixels that were opaque in the base, are enclosed by the new silhouette and are now empty:
        # inpaint them from their neighbours (recorded as 補完 area)
        op = out[..., 3] > 200
        r = np.zeros_like(op); x0, y0, x1, y1 = o.rect; r[y0:y1, x0:x1] = True
        hole = ndi.binary_fill_holes(op) & ~op & r & (B[..., 3] > 200)
        filled = int(hole.sum())
        if filled:
            rgb = np.clip(out[..., :3], 0, 255).astype(np.uint8)
            rgb = cv2.inpaint(rgb, hole.astype(np.uint8) * 255, 3, cv2.INPAINT_TELEA)
            out[..., :3] = np.where(hole[..., None], rgb, out[..., :3]); out[hole, 3] = 255
            Image.fromarray((hole * 255).astype(np.uint8)).save(o.out.replace('.png', '_filled_mask.png'))
    Image.fromarray(np.clip(out, 0, 255).round().astype(np.uint8)).save(o.out)
    info = {'base': o.base, 'donor': o.donor, 'donor_shift': [int(dx), int(dy)], 'rect': o.rect,
            'base_leg_px_removed': int(mb.sum()), 'donor_leg_px_inserted': int(md.sum()), 'blend_rows': o.blend, 'layered': o.layered, 'top_band': o.top_band, 'filled_px': filled, 'drop_specks': o.drop_specks}
    if o.debug:
        os.makedirs(o.debug, exist_ok=True)
        dbg = np.zeros(B.shape[:2] + (3,), np.uint8); dbg[mb] = (200, 60, 60); dbg[md] = (60, 60, 220); dbg[mb & md] = (200, 60, 220)
        Image.fromarray(dbg).save(os.path.join(o.debug, 'masks.png'))
    print(json.dumps(info))


if __name__ == '__main__':
    main()

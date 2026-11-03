#!/usr/bin/env python3
"""Profile walk: make the opposite-leg version of a frame (far leg leading) without repainting the body.

In Fiona's profile frames the leading boot is always the near (camera-side) leg: it carries the
visible flower cluster on its outer cuff. Each boot's flower sits on its outer side, so when the
FAR leg leads, the leading boot shows no flower and the trailing (near) boot shows it.
This tool keeps every boot shape and position and only swaps the near/far cues:
  1. the white petals are taken off the leading boot and refilled with the colour of the nearest
     leaf/leather pixel of the same boot (the boot silhouette does not change);
  2. the flower (petals + touching leaves) is placed on the trailing boot's cuff, clipped to that
     boot's silhouette so nothing hangs outside it;
  3. the leading boot is shaded like a far leg, the trailing boot like a near leg
     (luminance ratio measured between the two boots of the source frame).
usage: swap_side_legs.py SRC OUT [--band 700] [--debug DBG.png] [--facing left|right]
"""
import argparse
import numpy as np
from PIL import Image
from scipy import ndimage as ndi


def hsv(rgb):
    rgb = rgb.astype(float) / 255
    mx, mn = rgb.max(-1), rgb.min(-1); d = mx - mn + 1e-9
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, (g - b) / d % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, np.where(mx > 0, d / (mx + 1e-9), 0), mx


def boots(alpha, band):
    """two largest alpha components below `band`, ordered (leading, trailing) for a left-facing frame"""
    m = alpha > 24; m[:band] = False
    lab, n = ndi.label(m)
    sizes = ndi.sum(m, lab, range(1, n + 1))
    ids = 1 + np.argsort(sizes)[::-1][:2]
    comps = [lab == i for i in ids]
    comps.sort(key=lambda c: np.nonzero(c)[1].mean())
    return comps  # left-most = leading for a left-facing profile


def grow_up(alpha, comp, band, rows=45):
    """extend a boot component upward into the shin/cuff rows above the band, column by column"""
    out = comp.copy(); xs = np.nonzero(comp[band])[0]
    if not len(xs):
        return out
    x0, x1 = xs.min() - 6, xs.max() + 7
    cols = np.zeros(alpha.shape[1], bool); cols[max(0, x0):x1] = True
    for y in range(band - 1, band - rows, -1):
        row = (alpha[y] > 24) & cols & ndi.binary_dilation(out[y + 1], iterations=3)
        if not row.any():
            break
        out[y] = row
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('src'); p.add_argument('out')
    p.add_argument('--band', type=int, default=700)
    p.add_argument('--top', type=int, default=0, help='rows above the band that still belong to the boots (cuff)')
    p.add_argument('--debug')
    o = p.parse_args()
    a = np.array(Image.open(o.src).convert('RGBA')).astype(float)
    A = a[..., 3]
    lead, trail = boots(A, o.band)
    if o.top:
        lead, trail = grow_up(A, lead, o.band, o.top), grow_up(A, trail, o.band, o.top)
    h, s, v = hsv(a[..., :3].astype(np.uint8))
    # flower cluster on the leading boot: white petals + green leaves in the upper part of the boot
    ly, lx = np.nonzero(lead)
    top, bot = ly.min(), ly.max()
    upper = lead.copy(); upper[int(top + (bot - top) * 0.55):] = False
    petals = upper & (s < 0.30) & (v > 0.70)
    leaves = upper & (h > 36) & (h < 170) & (s > 0.22)
    # the flower = white petals plus the leaves that touch them; only the petals are removed from
    # the leading boot (the leafy cuff is shared by both boots), so the silhouette never changes
    clus = ndi.binary_dilation(petals, iterations=2) & (A > 0)
    flower = (ndi.binary_dilation(petals, iterations=7) & (petals | leaves | upper)) & (A > 24)
    cy, cx = np.nonzero(flower)
    cb = (cy.min(), cx.min(), cy.max() + 1, cx.max() + 1)
    patch = a[cb[0]:cb[2], cb[1]:cb[3]].copy(); pm = flower[cb[0]:cb[2], cb[1]:cb[3]].astype(float)
    pm = ndi.gaussian_filter(pm, 1.0) * flower[cb[0]:cb[2], cb[1]:cb[3]]
    patch[..., 3] *= pm
    out = a.copy()
    # 1. petals -> colour of the nearest non-petal pixel of the same boot (leaf / leather)
    donor = lead & ~clus & (A > 200)
    _, (iy, ix) = ndi.distance_transform_edt(~donor, return_indices=True)
    ys, xs = np.nonzero(clus & lead)
    out[ys, xs, :3] = a[iy[ys, xs], ix[ys, xs], :3]
    # 2. tone: leading boot -> far-leg shade, trailing boot -> near-leg shade
    vl = v[lead & ~clus].mean(); vt = v[trail].mean()
    k = vt / vl
    for comp, f in ((lead, k), (trail, 1 / k)):
        out[comp, :3] = np.clip(out[comp, :3] * f, 0, 255)
    # 3. place the cluster on the trailing boot's cuff (same relative spot: near its top, front edge)
    ty, tx = np.nonzero(trail)
    ttop = ty.min(); row = np.nonzero(trail[ttop + 6])[0]
    ox = int(row.min() + (cb[1] - np.nonzero(lead[top + 6])[0].min()))
    oy = int(ttop + (cb[0] - top))
    H, W = pm.shape
    region = out[oy:oy + H, ox:ox + W]
    clipm = ndi.binary_dilation(trail, iterations=2)[oy:oy + H, ox:ox + W]
    patch[..., 3] *= clipm
    pa = patch[..., 3:4] / 255
    region[..., :3] = patch[..., :3] * pa + region[..., :3] * (1 - pa)
    region[..., 3:4] = np.maximum(region[..., 3:4], patch[..., 3:4])
    Image.fromarray(np.clip(out, 0, 255).round().astype(np.uint8)).save(o.out)
    if o.debug:
        dbg = np.zeros(a.shape[:2] + (3,), np.uint8)
        dbg[lead] = (200, 60, 60); dbg[trail] = (60, 60, 200); dbg[clus] = (255, 255, 255)
        Image.fromarray(dbg).save(o.debug)
    print('lead/trail shade ratio %.3f cluster %s -> (%d,%d)' % (k, cb, oy, ox))


if __name__ == '__main__':
    main()

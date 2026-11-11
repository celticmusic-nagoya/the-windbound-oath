#!/usr/bin/env python3
"""PLAYER-WALK-UP-05: local repair of the PR #151 attempt-4 composite (aidan_walk_up_pushoff_trial.png).
Five fixes, all confined to the PR #150 proposed mask; outside the mask the result is official 03 byte-for-byte.
  1 sole/armour style : tread pattern removed (smooth dark-brown sole, tone from official 02's sole), armour softened
  2 knee-top seam     : the new greave fades in over 03's own trousers instead of starting on a straight line
  3 left boot outline : 03's left-boot pixels restored where the removal path notched into the boot (outline closed)
  4 frill remnant     : 03 frill pieces left inside the mask next to the new knee removed
  5 enclosed holes    : filled from the surrounding trousers/armour
usage: repair.py OUT [--debug DIR]"""
import argparse, json, os, sys
import numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
TRIAL = os.path.join(ROOT, 'assets/candidates/player-walk-polish01/up-04-pushoff-composite/aidan_walk_up_pushoff_trial.png')
MASK = os.path.join(ROOT, 'assets/candidates/player-walk-polish01/up-03-image-edit-kit/proposed_mask.png')
A = os.path.join(ROOT, 'img/field/characters/aidan/')


def hsv(a):
    rgb = a[..., :3] / 255; mx, mn = rgb.max(-1), rgb.min(-1); d = mx - mn + 1e-9; r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, (g - b) / d % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, d / (mx + 1e-9), mx


def nblur(img, m, sigma):
    """blur restricted to mask m (normalized convolution)"""
    w = ndi.gaussian_filter(m.astype(float), sigma); out = np.zeros_like(img)
    for c in range(img.shape[-1]):
        out[..., c] = ndi.gaussian_filter(img[..., c] * m, sigma) / np.maximum(w, 1e-6)
    return out


def main():
    p = argparse.ArgumentParser(); p.add_argument('out'); p.add_argument('--debug'); o = p.parse_args()
    T = np.array(Image.open(TRIAL).convert('RGBA')).astype(float); B = np.array(Image.open(A + 'aidan_walk_up_03.png').convert('RGBA')).astype(float)
    S2 = np.array(Image.open(A + 'aidan_walk_up_02.png').convert('RGBA')).astype(float)
    M = np.array(Image.open(MASK)) > 0; H, W = M.shape; X = np.arange(W)[None, :]; Y = np.arange(H)[:, None]
    out = T.copy(); info = {}
    N = M & (T != B).any(-1) & (T[..., 3] > 24)                    # pixels of the new right leg
    h, s, v = hsv(T)
    # 1. sole: the dark inner part of the new boot below y=1005; tone taken from official 02's (left) sole, not its shape
    sole = N & (v < 0.42) & (Y > 1005) & (X > 1070)
    sole = ndi.binary_fill_holes(ndi.binary_closing(sole, iterations=3)) & N
    sole = ndi.binary_erosion(sole, iterations=5)                # keep the boot rim / welt drawn as it is
    lab, n = ndi.label(sole)
    if n:
        sole = lab == (1 + int(np.argmax(ndi.sum(sole, lab, range(1, n + 1)))))
    h2, s2, v2 = hsv(S2); ref = (S2[..., 3] > 200) & (v2 < 0.40); ref[:1060] = False; ref[:, 1060:] = False; ref[:, :960] = False
    ref_mean, ref_std = S2[ref][:, :3].mean(0), S2[ref][:, :3].std(0)
    smooth = nblur(T[..., :3], sole, 2.5)
    cur_mean, cur_std = smooth[sole].mean(0), smooth[sole].std(0)
    matched = (smooth - cur_mean) * 0.8 + (cur_mean * 0.4 + ref_mean * 0.6)
    out[sole, :3] = matched[sole]
    # armour: soften (blur + 20 % contrast reduction toward a wide local mean) like the painterly official boots
    armour = N & ~sole
    a1 = nblur(T[..., :3], armour, 0.9); a4 = nblur(T[..., :3], armour, 4.0)
    out[armour, :3] = (a1 * 0.8 + a4 * 0.2)[armour]
    info['sole_px'] = int(sole.sum()); info['armour_px_softened'] = int(armour.sum()); info['sole_tone_ref_official02_rgb'] = [round(float(x), 1) for x in ref_mean]
    # 2. knee-top seam: fade the new greave in over 03's trousers across 18 rows below its top edge
    top = np.full(W, H); cols = np.nonzero(N.any(0))[0]
    for x in cols:
        top[x] = np.nonzero(N[:, x])[0].min()
    ramp = np.ones((H, W))
    for x in cols:
        for k in range(18):
            y = top[x] + k
            if y < H and B[y, x, 3] > 200:
                ramp[y, x] = (k + 1) / 19
    fade = N & (ramp < 1)
    a = ramp[..., None]; out[fade] = (out * a + B * (1 - a))[fade]
    info['knee_seam_px_faded'] = int(fade.sum())
    # 3. left boot outline: right edge of the planted left boot per row (opaque run from x=980), notches closed
    e = np.zeros(H, int)
    for y in range(1000, 1230):
        row = out[y, 960:1100, 3] > 24; xs = np.nonzero(~row[20:])[0]
        e[y] = 960 + 20 + (xs[0] if len(xs) else 120)
    sm = ndi.minimum_filter1d(ndi.maximum_filter1d(e, 25), 25)          # morphological closing of the outline profile
    restore = np.zeros((H, W), bool)
    for y in range(1000, 1230):
        if sm[y] > e[y]:
            restore[y, e[y]:sm[y] + 1] = True
    sys.path.insert(0, os.path.join(ROOT, 'assets/candidates/player-walk-polish01/up-03-image-edit-kit/tools'))
    from legs import split, legs
    cut = split(B, 1022, 1050); L03, _ = legs(B, cut); L03 = ndi.binary_fill_holes(ndi.binary_closing(L03, iterations=3)) & (B[..., 3] > 24)
    # attempt 5: 03's own pixels in a 3 px ring around the left boot silhouette (its original dark outline), no straight cut
    lb = (out[..., 3] > 24) & (X < 1075) & (Y >= 1000) & ~N
    lab, n = ndi.label(lb); lb = lab == (1 + int(np.argmax(ndi.sum(lb, lab, range(1, n + 1))))) if n else lb
    restore = M & ~N & (out != B).any(-1) & (B[..., 3] > 24) & ndi.binary_dilation(lb, iterations=3) & ~lb
    out[restore] = B[restore]
    info['left_boot_outline_px_restored'] = int(restore.sum())
    # 4. frill remnant (needs L03 from step 3): 03 cloth inside the mask next to the new knee (x>=1110, y 900-1030) -> removed
    hb, sb, vb = hsv(B)
    cloth = (B[..., 3] > 24) & (((hb > 60) & (hb < 180) & (sb > 0.12)) | ((sb < 0.25) & (vb > 0.55)))
    right_of_leg = np.zeros((H, W), bool)
    for y in range(900, 1060):
        xs = np.nonzero(N[y])[0]
        if len(xs):
            right_of_leg[y, xs.max() + 1:] = True
    # attempt 3: between the new knee and 03's frill the hem underside is closed (03 cloth restored, the old
    # right-leg pixels behind it become hem underside by inpainting from that cloth); below the hem: transparent
    Z = M & ~N & right_of_leg & ~L03
    keep = Z & cloth & (B[..., 3] > 24); out[keep] = B[keep]
    oldleg = Z & ~cloth & (B[..., 3] > 24)
    under = oldleg & (Y < 1000) & ndi.binary_dilation(keep, iterations=6)
    gone = (oldleg & ~under) | (Z & ~keep & ~oldleg)
    if under.any():
        src = np.clip(out[..., :3], 0, 255).astype(np.uint8); src = cv2.inpaint(src, under.astype(np.uint8) * 255, 4, cv2.INPAINT_TELEA)
        out[under, :3] = src[under]; out[under, 3] = 255
    out[gone, 3] = 0
    small = (out[..., 3] > 24) & Z; lab, n = ndi.label(small)
    for k in range(1, n + 1):
        if (lab == k).sum() < 30:
            out[lab == k, 3] = 0
    frill = gone | under
    info['frill_remnant_px_removed'] = int(frill.sum())
    # 5. enclosed holes -> filled from the neighbours (inside the mask only)
    op = out[..., 3] > 200
    op = out[..., 3] > 24
    hole = (ndi.binary_fill_holes(op) & ~op & M) | (ndi.binary_fill_holes(out[..., 3] > 200) & (out[..., 3] <= 200) & M)
    if hole.any():
        rgb = np.clip(out[..., :3], 0, 255).astype(np.uint8); rgb = cv2.inpaint(rgb, ndi.binary_dilation(hole).astype(np.uint8) * 255, 3, cv2.INPAINT_TELEA)
        out[hole, :3] = rgb[hole]; out[hole, 3] = 255
    info['holes_filled_px'] = int(hole.sum())
    out[~M] = B[~M]                                                    # protection: outside the mask = official 03
    res = np.clip(out, 0, 255).round().astype(np.uint8); Image.fromarray(res).save(o.out)
    b8 = B.astype(np.uint8); diff = (res != b8).any(-1); op = res[..., 3] > 200
    enc = ndi.binary_fill_holes(op) & ~op
    info.update({'changed_outside_mask': int((diff & ~M).sum()), 'enclosed_holes_alpha200': int(enc.sum()), 'enclosed_holes_alpha200_inside_mask': int((enc & M).sum()),
                 'enclosed_holes_alpha200_outside_mask_note': '03 own anti-aliased pixels (alpha<200), unchanged, now surrounded by the new leg' if (enc & ~M).any() else None,
                 'changed_vs_trial': int((res != T.astype(np.uint8)).any(-1).sum())})
    if o.debug:
        os.makedirs(o.debug, exist_ok=True)
        for k, m in (('sole', sole), ('knee_fade', fade), ('left_outline_restore', restore), ('frill_removed', frill), ('holes', hole)):
            Image.fromarray((m * 255).astype(np.uint8)).save(os.path.join(o.debug, 'fix_%s.png' % k))
    print(json.dumps(info))


if __name__ == '__main__':
    main()

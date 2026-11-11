#!/usr/bin/env python3
"""ART-74B (= ART-74A + art fixes FIX-01/02, see FIXES_74B below): official LEFT walk candidate for Morwen (not a plain mirror).

Method (right/left asymmetry, official master morwen-full-body-v3.png):
  All asymmetric items of the costume sit on Morwen's RIGHT side (bag on the right hip, book crest on the right
  shoulder of the capelet, hat flower + hanging ribbons on the right of the hat); the bag strap is a cross-body strap
  from the LEFT shoulder to the right hip. A right-facing view shows her right side, a left-facing view her left side.
  1. Edit the 65B F00 reference (right-view coordinates) into "her left side": remove the near-side bag, crest, hat
     flower and ribbons (they are on the far side and occluded), re-route the strap (near shoulder -> front waist),
     fill what was behind them from neighbouring pixels of the same part (iterative majority, no new colours).
  2. Run the unchanged MORWEN-PIXEL-72 pipeline (build_morwen71 + GLASSES) on that reference -> 96x128 and 48x64.
  3. Mirror horizontally (the drawn geometry/gait/anchor are symmetric; light stays on the front).
Kept as is (symmetric or verified on both sides): face, glasses, hair, earring (pair assumed - UNVERIFIED), hat tip
jewel, capelet trim, mantle, skirt plaid/pleats, knee socks/garter (garter on the near thigh), boots, potions (belt front).
  python3 build_morwen74b.py --source <65B dir> --out <dir>
"""
import os as _os, sys as _sys
_HERE=_os.path.dirname(_os.path.abspath(__file__))
_PIPE=_os.environ.get('MORWEN72_PIPELINE', _os.path.join(_HERE,'..','..','morwen-right-walk','72'))
_sys.path[:0]=[_HERE,_PIPE]
import argparse, json, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
pass
import build_morwen66 as B, build_morwen71 as M
from masks74 import refmasks
from inpaint74 import exemplar, drop_islands
H, W = 128, 96
STRAP_NEW = [(50, 64), (51, 65), (52, 66), (53, 67), (54, 68), (55, 69), (56, 70), (57, 71)]   # right-view coords; after the mirror: near shoulder -> front waist


def inpaint(img, hole, allow=None, iters=40):
    """fill hole pixels with the majority colour of already-known 8-neighbours (existing colours only)."""
    out = img.copy(); known = (img[:, :, 3] > 0) & ~hole
    if allow is not None: known &= allow
    todo = hole.copy()
    for _ in range(iters):
        if not todo.any(): break
        new = []
        for y, x in zip(*np.where(todo)):
            cols = {}
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if (dy or dx) and 0 <= yy < H and 0 <= xx < W and known[yy, xx]:
                        c = tuple(int(v) for v in out[yy, xx]); w = 2 if dy == 0 else 1
                        cols[c] = cols.get(c, 0) + w
            if sum(cols.values()) >= 3:
                new.append((y, x, max(cols.items(), key=lambda t: t[1])[0]))
        for y, x, c in new:
            out[y, x] = c; known[y, x] = True; todo[y, x] = False
    return out, todo



# ------------------------------------------------------------------ ART-74B fixes (third-party art QA on 74A)
FIXES_74B = {
    'FIX-01': 'hat back (where the far-side flower was removed): dark speckles merged, colour clusters flattened (3x3 majority, '
              'existing colours only), hat fabric / brim / back hair separated by keeping the existing outline rows',
    'FIX-02': 'waist (where the far-side bag was removed): no transparent hole inside the skirt (pleats painted y78-83 for every '
              'pixel of the side-skirt band), mantle front edge continued with the existing gold trim tone next to the pleats',
}
def _lum(c): return 0.30 * c[..., 0] + 0.59 * c[..., 1] + 0.11 * c[..., 2]
def _majority(a, y, x, region, include_self=True):
    cols = {}
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if not include_self and dy == 0 and dx == 0: continue
            yy, xx = y + dy, x + dx
            if 0 <= yy < H and 0 <= xx < W and a[yy, xx, 3] > 0 and region[yy, xx]:
                c = tuple(int(v) for v in a[yy, xx]); cols[c] = cols.get(c, 0) + (2 if dy == 0 and dx == 0 else 1)
    return max(cols.items(), key=lambda t: t[1]) if cols else (None, 0)
def flatten(a, region, passes=2):
    n = 0
    # 1) dark speckles: a near-black pixel whose neighbours are mostly not dark takes their majority colour
    for y, x in zip(*np.where(region & (a[:, :, 3] > 0))):
        if _lum(a[y, x, :3].astype(float)) < 40:
            nb = [a[y + dy, x + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy or dx) and 0 <= y + dy < H and 0 <= x + dx < W and a[y + dy, x + dx, 3] > 0]
            dark = sum(_lum(c[:3].astype(float)) < 40 for c in nb)
            if len(nb) >= 6 and dark <= 2:
                c, _ = _majority(a, y, x, region & (_lum(a[:, :, :3].astype(float)) >= 40), include_self=False)
                if c: a[y, x] = c; n += 1
    # 2) cluster flattening: 3x3 majority inside the region (self counts double -> stable clusters stay)
    for _ in range(passes):
        b = a.copy()
        for y, x in zip(*np.where(region & (a[:, :, 3] > 0))):
            c, k = _majority(a, y, x, region)
            if c and k >= 4 and c != tuple(int(v) for v in a[y, x]): b[y, x] = c; n += 1
        a[:] = b
    return n
def apply_fixes_74b(a, m, ribbon, skirt_side, xx, yy):
    log = {}
    # FIX-01: re-fill the hat back (where the flower / hair ribbons were) by STRUCTURE instead of one mixed exemplar pass.
    #   zone BAND : the gold-patterned hat band, continued along its own direction (copy from the visible band, step (11,-7))
    #   zone CONE : purple hat fabric above the band (exemplar from cone fabric only -> no gold dots inside the fabric)
    #   zone BACK : brim underside / back hair below the band (exemplar from dark purple + hair only -> no gold / no pink specks)
    hole = (m['flower'] | ribbon) & (a[:, :, 3] > 0) & (yy <= 44)
    U = 8 + (48 - xx) * 0.64                                     # band upper edge (right coords)
    L = np.where(xx >= 44, 22 + (62 - xx) * 0.64, U + 5 + np.clip(xx - 28, 0, None) * (18.0 / 16))   # band lower edge (tapers to 5px round the back)
    band = (yy >= U) & (yy <= L)
    cone = yy < U
    back = yy > L
    before = a.copy()
    known = (a[:, :, 3] > 0) & ~hole
    hb = hole & band; nb = 0
    for y, x in sorted(zip(*np.where(hb)), key=lambda t: -t[1]):
        for k in range(1, 8):
            for sgn in (1, -1):
                sy, sx = y - 7 * k * sgn, x + 11 * k * sgn
                if 0 <= sy < H and 0 <= sx < W and known[sy, sx] and band[sy, sx]:
                    a[y, x] = a[sy, sx]; known[y, x] = True; nb += 1; break
            else: continue
            break
    rest = hole & ~known
    lum = _lum(a[:, :, :3].astype(float))
    gold = (a[:, :, 0] > 200) & (a[:, :, 1] > 110) & (a[:, :, 2] < 120)
    skin = (a[:, :, 0] > 220) & (a[:, :, 1] > 160) & (a[:, :, 2] > 120)
    src_cone = cone & known & ~gold & (xx >= 20) & (xx <= 46) & (yy >= 4)
    src_back = back & known & ~gold & ~skin & (xx >= 26) & (xx <= 58) & (yy >= 26) & (yy <= 50)
    for zone, src in ((cone, src_cone), (back | band, src_back)):
        h = rest & zone
        if h.any():
            a2, left = exemplar(a, h, src)
            a[h] = a2[h]
    # isolated pixels left inside the re-filled area -> neighbour majority (same zone only)
    inner = hole.copy()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        inner &= np.roll(np.roll(hole, dy, 0), dx, 1)
    nf = 0
    for zone in (cone & ~band, back & ~band):
        nf += flatten(a, inner & zone, passes=1)
    log['FIX-01_band_copied'] = nb
    log['FIX-01_changed'] = int((a != before).any(2).sum())
    # FIX-02a: side-skirt band y78-83 fully painted with plain pleats (no transparent hole)
    band = (xx >= 42) & (xx <= 54) & (yy >= 78) & (yy <= 83) & (skirt_side | (a[:, :, 3] == 0))
    import build_morwen68 as _D
    pal = _D.build_palette68(B.split_layers(B.load_reference(_SRC[0] / 'morwen_right_walk_00_96x128.png')[0])[0])[0]['pleat']
    for y, x in zip(*np.where(band)):
        a[y, x] = (*pal[[3, 2, 1][x % 3]], 255)
    log['FIX-02_pleat_px'] = int(band.sum())
    # FIX-02b: mantle front edge next to the pleats gets the existing gold trim tone (gold mid of the 72 palette)
    import build_morwen70art as _A
    g = _A.pick_gold3(B.load_reference(_SRC[0] / 'morwen_right_walk_00_96x128.png')[0])['mid']
    trim = 0
    for y in range(74, 93):
        x = 41
        if a[y, x, 3] > 0 and a[y, x + 1, 3] >= 0 and not (a[y, x, 0] > 150 and a[y, x, 2] < 110):
            a[y, x] = (*g, 255); trim += 1
    log['FIX-02_trim_px'] = trim
    return log
_SRC = [None]

def edit_reference(src: Path, dst_dir: Path):
    _SRC[0] = src
    ref = np.array(Image.open(src / 'morwen_right_walk_00_96x128.png').convert('RGBA'))
    uf, m = refmasks(src)
    r, g, b = (ref[:, :, i].astype(int) for i in range(3))
    yy, xx = np.mgrid[0:H, 0:W]
    a = ref.copy()
    a[a[:, :, 3] < 128] = 0; a[a[:, :, 3] >= 128, 3] = 255
    ribbon = m['ribbon'] & ~((xx <= 24) & (yy <= 36))          # keep the hat-tip jewel
    holes = m['bag'] | m['strap'] | m['emblem'] | m['flower'] | ribbon
    # outside the silhouette of what remains -> transparent (row span of non-hole opaque pixels)
    op = (a[:, :, 3] > 0) & ~holes
    trans = np.zeros_like(holes)
    for y in range(H):
        xs = np.where(op[y])[0]
        if not len(xs): trans[y] = holes[y]; continue
        trans[y] = holes[y] & ((xx[y] < xs.min()) | (xx[y] > xs.max()))
    a[trans] = 0
    fill = holes & ~trans
    # the bag hole below the waist on her side = plain pleats: let the 67 skirt panel draw them (leave transparent there)
    skirt_side = m['bag'] & (xx >= 42) & (yy >= 78)
    a[skirt_side] = 0
    fill &= ~skirt_side
    log = {}
    face = (xx >= 54) & (xx <= 72) & (yy >= 26) & (yy <= 50)
    body = (a[:, :, 3] > 0) & ~holes
    regions = (
        ('flower', m['flower'] & fill & (yy <= 24), body & (yy <= 26) & (xx >= 14) & ~face),
        ('flower_low', m['flower'] & fill & (yy > 24), body & (yy >= 18) & (yy <= 36) & (xx >= 20) & (xx <= 60) & ~face),
        ('ribbon_hair', ribbon & fill & (yy < 46), body & (xx >= 26) & (xx <= 50) & (yy >= 24) & (yy <= 48) & ~face),
        ('ribbon_cape', ribbon & fill & (yy >= 46), body & (xx >= 14) & (xx <= 46) & (yy >= 44) & (yy <= 70)),
        ('emblem', m['emblem'] & fill, body & (xx >= 30) & (xx <= 60) & (yy >= 48) & (yy <= 66) & ~m['emblem']),
        ('strap', m['strap'] & fill, body & (xx >= 50) & (xx <= 70) & (yy >= 56) & (yy <= 76)),
        ('bag_upper', m['bag'] & ~skirt_side & fill & (xx >= 42), body & (xx >= 44) & (xx <= 68) & (yy >= 60) & (yy <= 80) & ~m['hand']),
        ('bag_mantle', m['bag'] & ~skirt_side & fill & (xx < 42), body & (xx >= 14) & (xx <= 41) & (yy >= 64) & (yy <= 100)),
    )
    for name, h, src_region in regions:
        a2, left = exemplar(a, h, src_region)
        a[h] = a2[h]; a[left] = 0
        log[name] = {'holes': int(h.sum()), 'unfilled': int(left.sum())}
    log['islands_removed'] = drop_islands(a)
    # pleats for the side-skirt hole above the panel top (y 78..83), plain pleat colours from 70 meta
    import build_morwen68 as _D
    _ouf = B.split_layers(B.load_reference(src / 'morwen_right_walk_00_96x128.png')[0])[0]
    pal = _D.build_palette68(_ouf)[0]['pleat']
    for y in range(78, 84):
        for x in range(42, 55):
            if skirt_side[y, x]:
                a[y, x] = (*pal[[3, 2, 1][x % 3]], 255)
    # re-routed cross-body strap: 2 tones taken from the removed strap
    sc = ref[m['strap']][:, :3].astype(int); L = sc.sum(1)
    dark = tuple(int(v) for v in sc[np.argsort(L)[len(L) // 4]]); light = tuple(int(v) for v in sc[np.argsort(L)[3 * len(L) // 4]])
    for i, (x, y) in enumerate(STRAP_NEW):
        a[y, x] = (*dark, 255)
        if i % 2 == 0 and y - 1 >= 0 and a[y - 1, x, 3]: a[y - 1, x] = (*light, 255)
    fixlog = apply_fixes_74b(a, m, ribbon, skirt_side, xx, yy)
    log['fixes_74b'] = fixlog
    a[a[:, :, 3] == 0, :3] = 0
    dst_dir.mkdir(parents=True, exist_ok=True)
    Image.fromarray(a, 'RGBA').save(dst_dir / 'morwen_right_walk_00_96x128.png')
    # the 72 pipeline also reads the 48px 65B F00 for nothing else; copy the rest of the source dir for completeness
    for p in src.glob('*_48x64.png'): shutil.copy(p, dst_dir / p.name)
    diff = np.any(a != ref, axis=2)
    return log, diff, {'strap_dark': dark, 'strap_light': light}


def build(source: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    refdir = out / '_left_side_reference'
    log, diff, strap = edit_reference(source, refdir)
    tmp = out / '_right_view_without_far_items'
    # palettes (gold 3 tones, leg/boot/rim snapping) must stay those of MORWEN-PIXEL-72: derive them from the ORIGINAL
    # reference, not from the edited one (removing the crest/flower would otherwise shift the snapped colours)
    import build_morwen67 as C, build_morwen68 as D, build_morwen70 as E, build_morwen70art as A
    oref, _ = B.load_reference(source / 'morwen_right_walk_00_96x128.png'); ouf, _, _ = B.split_layers(oref)
    g3 = A.pick_gold3(oref); pal68 = D.build_palette68(ouf)
    o_pick, o_pal, o_conf = A.pick_gold3, D.build_palette68, E.configure
    A.pick_gold3 = lambda ref: dict(g3)
    D.build_palette68 = lambda uf: pal68
    E.configure = lambda easing, ref_front: o_conf(easing, ouf)
    try:
        M.build(refdir, tmp, 'GLASSES')
    finally:
        A.pick_gold3, D.build_palette68, E.configure = o_pick, o_pal, o_conf
    for f in range(6):
        for s in ('96x128', '48x64'):
            im = Image.open(tmp / f'morwen_right_walk_{f:02d}_{s}.png')
            im.transpose(Image.FLIP_LEFT_RIGHT).save(out / f'morwen_left_walk_{f:02d}_{s}.png')
    Image.fromarray((diff * 255).astype(np.uint8), 'L').save(out / 'REFERENCE_EDIT_MASK_right_coords.png')
    (out / 'build_meta_74b.json').write_text(json.dumps({'inpaint': log, 'strap_colours': strap, 'strap_new_right_coords': STRAP_NEW,
                                                         'reference_pixels_edited': int(diff.sum())}, indent=1), encoding='utf-8')
    return log


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--source', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(); print(build(a.source, a.out))

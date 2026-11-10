#!/usr/bin/env python3
"""MORWEN-ASSET-74I: final match of the left walk to the official left profile (SHA-256 81ef16e1...).
Starts from the 74H frames (74G / 74H are not modified) and edits only the pixels named below, per frame, following
the head level of that frame (74G levels.head_dy); colours are drawn, never blended:
  FIX-01 hat-tip crystal: gold chain (2 px) from the drooping tip + 3x4 violet crystal with a catch-light; 48: chain 1 px
         + crystal 2 px, joined to the tip (no loose pixel)
  FIX-02 round gold glasses: clean elliptical rim around the eye (x29-36, y31-39), light gold on the upper-left arc,
         eye interior untouched; temple arm 1 px back to the ear; 48: 3-px rim in front of the eye + 1 behind
  FIX-03 violet eyes: dark / brown iris pixels -> violet ramp, pink glints -> light violet; white catch-lights, lashes,
         skin and hair untouched
  FIX-04 collar frill vs bow: white frill row under the chin (x33-37, y48-49); white pixels inside the bow -> pale
         lavender so the bow reads purple and the frill white (96 and 48)
  FIX-05 74H crest / strap / ear flower: kept as they are (only checked)
python3 build_morwen74i.py --out ."""
import argparse, json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(HERE / '..' / '74D'))
from oklab import rgb2oklab, lch
H74 = HERE / '..' / '74H'; G74 = HERE / '..' / '74G'; NF = 12
HD = json.loads((G74 / 'build_meta_74g.json').read_text())['levels']['head_dy']
GD, GM, GL = (167, 107, 42), (226, 163, 85), (255, 211, 138)
VD, VM, VL, VH = (74, 24, 110), (128, 62, 186), (196, 146, 240), (238, 222, 255)
WH, WS, LAV = (253, 253, 253), (214, 204, 226), (222, 186, 250)


def LCH(im):
    L, C, h = lch(rgb2oklab(im[:, :, :3].reshape(-1, 3).astype(float))); s = im.shape[:2]
    return L.reshape(s), C.reshape(s), h.reshape(s)


def tip_96(im):
    """lowest pixel of the drooping hat tip (rightmost hat column block above the brim)."""
    a = im[:, :, 3] > 0; ys, xs = np.where(a[10:30, 66:80]); ys += 10; xs += 66
    x = xs.max(); col = ys[xs >= x - 1]; return int(x - 1), int(col.max())


def fix96(im, dy):
    L, C, h = LCH(im)
    # FIX-01 crystal
    tx, ty = tip_96(im)
    for (x, y), c in {(tx, ty + 1): GD, (tx, ty + 2): GM}.items(): im[y, x, :3] = c; im[y, x, 3] = 255
    cy = ty + 3
    cr = {(tx, cy): VL, (tx - 1, cy + 1): VM, (tx, cy + 1): VH, (tx + 1, cy + 1): VM, (tx - 1, cy + 2): VD, (tx, cy + 2): VM,
          (tx + 1, cy + 2): VD, (tx, cy + 3): VD}
    for (x, y), c in cr.items(): im[y, x, :3] = c; im[y, x, 3] = 255
    # FIX-03 iris (inside the rim box, before the rim is drawn)
    for y in range(32 + dy, 39 + dy):
        for x in range(30, 36):
            if not im[y, x, 3]: continue
            l, c_, hh = L[y, x], C[y, x], h[y, x]
            gold = 45 < hh < 115 and c_ >= 0.085 and l > 0.42
            if gold or (l > 0.93 and c_ < 0.03): continue
            if l < 0.13 and y <= 33 + dy: continue                              # top lash line
            if l < 0.20: im[y, x, :3] = VD
            elif l < 0.55 and (hh < 80 or hh > 300): im[y, x, :3] = VM
            elif c_ > 0.08 and (hh > 300 or hh < 20) and l >= 0.55: im[y, x, :3] = VL
    # FIX-02 rim: ellipse outline x29-36 y31-39, temple to the ear
    m = Image.new('L', (96, 128), 0); ImageDraw.Draw(m).ellipse([29, 31 + dy, 36, 39 + dy], outline=1)
    ys, xs = np.where(np.array(m) > 0)
    for y, x in zip(ys, xs):
        if not im[y, x, 3]: continue
        im[y, x, :3] = GL if (x <= 31 and y <= 34 + dy) else GM
    for x in range(37, 41): im[34 + dy, x, :3] = GD
    # FIX-04 frill + bow
    for x in range(33, 38):
        for y in (48 + dy, 49 + dy):
            if im[y, x, 3]: im[y, x, :3] = WH if (x + y) % 2 == 0 else WS
    L, C, h = LCH(im)
    for y in range(52 + dy, 59 + dy):
        for x in range(29, 39):
            if im[y, x, 3] and L[y, x] > 0.92 and C[y, x] < 0.05: im[y, x, :3] = LAV
    return im


def fix48(im, dy):
    a = im[:, :, 3] > 0
    ys, xs = np.where(a[4:16, 32:40]); ys += 4; xs += 32
    x = xs.max(); ty = ys[xs >= x].max()
    for (xx, yy), c in {(x, ty + 1): GM, (x, ty + 2): VM, (x, ty + 3): VD}.items(): im[yy, xx, :3] = c; im[yy, xx, 3] = 255
    d = (dy + 1) // 2                                                            # 74G stable 48 offset
    # iris / lash / glint (positions of the 74G eye at 48, shifted with the head)
    for (x, y), c in {(17, 16): VM, (16, 17): VD, (17, 17): VL, (16, 18): VM}.items():
        if im[y + d, x, 3]: im[y + d, x, :3] = c
    # glasses: 3-px gold rim in front of the eye + 1 behind (round lens seen in profile)
    for (x, y) in ((15, 16), (15, 17), (15, 18), (18, 17)):
        if im[y + d, x, 3]: im[y + d, x, :3] = GM
    for x in (17, 18):
        if im[24 + d, x, 3]: im[24 + d, x, :3] = WH
    L, C, h = LCH(im)
    for y in range(25 + d, 30 + d):                                   # bow: no white inside it
        for x in range(13, 21):
            if im[y, x, 3] and L[y, x] > 0.88 and C[y, x] < 0.06: im[y, x, :3] = LAV
    return im


ap = argparse.ArgumentParser(); ap.add_argument('--out', type=Path, required=True); a = ap.parse_args()
for f in range(NF):
    for s, fx in (('96x128', fix96), ('48x64', fix48)):
        im = np.array(Image.open(H74 / f'morwen_left_walk_74H_12f_{f:02d}_{s}.png').convert('RGBA'))
        Image.fromarray(fx(im, HD[f]), 'RGBA').save(a.out / f'morwen_left_walk_74I_12f_{f:02d}_{s}.png')
print('ok')

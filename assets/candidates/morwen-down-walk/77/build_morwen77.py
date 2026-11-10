#!/usr/bin/env python3
"""MORWEN-ASSET-77 / MORWEN-WALK-DOWN-77: down (front view) walk, 12 frames / 840 ms, NEW candidate.

Design reference: the director-supplied front illustration, registered here as a CANDIDATE reference
(reference/morwen_front_candidate_73e99f19.png, SHA-256 73e99f19...; not yet in the official turnaround set).
Same method and palette as up 76 (shared code imported from ../../morwen-up-walk/76): head + hat reduced at 0.124,
body at 0.075 wide with the torso 330-850 -> rows 43-94 and the cape below the skirt 850-1420 -> rows 94-108, so the
sprite keeps the side walks' chibi proportions (hat width, neck row, legs ~30 rows, ground 124); legs are drawn per
frame (knee socks + short boots with front lacing dots and buckles).
Front-view walk (timing shared: 840 ms, stance 0.66, F00 right heel strike):
  - the right leg is on the viewer's LEFT; a landing foot is near (row 124) and moves away (row 122) through stance;
    the swinging foot lifts (max 3 px) and comes back to the near position; legs never cross / vanish
  - pelvis 1 px toward the stance leg; the cape side on the swing leg drops 1 px; shoulders 1 px opposite, 1 frame late
  - head: no sideways sway, 74F-C vertical levels (hat bob <= 1 px)
  - hands swing 1 px opposite to the legs; hat ribbon and cape hem follow 2 frames late
  python3 build_morwen77.py --front reference/morwen_front_candidate_73e99f19.png --palette-from <74G> <75> --out .
"""
import os as _os, sys as _sys
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_U76 = _os.environ.get('MORWEN76_DIR', _os.path.join(_HERE, '..', '..', 'morwen-up-walk', '76'))
_sys.path[:0] = [_HERE, _U76]
import argparse, glob, json, math
from pathlib import Path
import numpy as np
from PIL import Image
import build_morwen76 as U          # shared walk code (also puts 74D/oklab on the path)
import back_base76 as BB
from oklab import rgb2oklab, lch
from walkclean import clean_islands_generic, fill_small_holes

H, W, NF = 128, 96, 12
CX_SRC = 511
HEAD_SRC, HEAD_S, HEAD_TOP = (0, 345), 0.124, 2
S_H = 0.075
SEG = [((330, 850), (43, 94)), ((850, 1420), (94, 108))]
LEGS_CUT = (855, 380, 645)            # official rows >= 855, columns 380..645: legs between the cape fronts (drawn instead)

# front-view tables (mirror of the back view: the right leg is on the viewer's left)
P_DX = [-v for v in U.P_DX]
S_DX = [-v for v in U.S_DX]
TILT = [-v for v in U.TILT]
LEG_X = {'R': 44, 'L': 52}


def leg_state(p):
    p %= 1.0
    if p < U.STANCE:
        u = p / U.STANCE
        return dict(foot=124 - round(3 * u), lift=0, sole=False, stance=True)
    u = (p - U.STANCE) / (1 - U.STANCE)
    return dict(foot=121 + round(3 * u), lift=round(5 * math.sin(math.pi * u)), sole=False, stance=False)


SK, BT = U.STK, U.BOOT


def draw_leg(img, cx, st, top=92):
    """front view: knee sock 6 px, boot shaft 8 px with a lace line of gold dots and two outer buckles, rounded toe."""
    yg = st['foot'] - st['lift']; bt = yg - 12
    outer = -1 if cx < 48 else 1
    for y in range(top, bt):
        for i, x in enumerate(range(cx - 3, cx + 3)):
            c = SK['o'] if i in (0, 5) else (SK['l'] if i == (2 if outer > 0 else 3) else SK['m'] if i in (2, 3) else SK['d'])
            img[y, x, :3] = c; img[y, x, 3] = 255
    for y in range(bt, yg + 1):
        toe = y >= yg - 2
        x0, x1 = (cx - 4, cx + 4) if not toe else (cx - 4 + (1 if y == yg else 0), cx + 4 - (1 if y == yg else 0))
        for x in range(x0, x1):
            edge = x in (x0, x1 - 1) or y == yg
            if edge: c = BT['o']
            elif y == bt: c = BT['l']
            elif toe: c = BT['l'] if x in (cx - 1, cx) and y == yg - 2 else BT['m']
            else:
                rel = (x - cx) * outer
                c = BT['l'] if rel == -2 else BT['m'] if rel in (-1, 0) else BT['d']
            img[y, x, :3] = c; img[y, x, 3] = 255
        if bt < y < yg - 2 and (y - bt) % 2 == 0:            # lace dots down the front
            img[y, cx - 1 if outer > 0 else cx, :3] = BT['gd']
    for dy in (2, 8):
        y = bt + dy
        if y < yg - 2:
            x = cx + outer * 3 if outer > 0 else cx - 4
            img[y, x, :3] = BT['g']


def base_layers_front(front, pal, k=1.0):
    o = np.array(Image.open(front).convert('RGBA')); o[o[:, :, 3] < 200, 3] = 0
    o[LEGS_CUT[0]:, LEGS_CUT[1]:LEGS_CUT[2], 3] = 0
    # head: hat + face + hair; below row 330 keep only hair ends at the sides and the hanging ribbon
    hs = o[:HEAD_SRC[1] + 60].copy()
    L, C, h = lch(BB.oklab(hs[:, :, :3].reshape(-1, 3)))
    L, C, h = (v.reshape(hs.shape[:2]) for v in (L, C, h))
    yy, xx = np.mgrid[0:hs.shape[0], 0:hs.shape[1]]
    ribbon = (C > 0.14) & (h > 285) & (h < 340) & (xx < 420)
    hair_side = (L < 0.32) & ((xx < 445) | (xx > 585)) & (yy < 385)
    hs[(yy >= HEAD_SRC[1]) & ~ribbon & ~hair_side, 3] = 0
    hh, ww = int(H * k), int(W * k)
    head = np.zeros((hh, ww, 4), np.uint8); body = np.zeros((hh, ww, 4), np.uint8)
    hd = BB.sharpen(BB.area_down(hs, HEAD_S * k))
    BB.place(head, hd, int(48 * k) - round(CX_SRC * HEAD_S * k), int(round(HEAD_TOP * k)))
    import cv2
    for (s0, s1), (r0, r1) in SEG:
        seg = o[s0:s1]
        a = seg[:, :, 3:4].astype(float) / 255
        pm = np.concatenate([seg[:, :, :3] * a, a * 255], 2).astype(np.float32)
        nh = max(1, round((r1 - r0) * k)); nw = round(seg.shape[1] * S_H * k)
        sm = cv2.resize(pm, (nw, nh), interpolation=cv2.INTER_AREA)
        al = sm[:, :, 3] / 255
        rgb = np.where(al[..., None] > 1e-3, sm[:, :, :3] / np.maximum(al[..., None], 1e-3), 0)
        part = np.zeros((nh, nw, 4), np.uint8); part[..., :3] = np.clip(rgb, 0, 255); part[..., 3] = np.where(al >= 0.5, 255, 0)
        BB.place(body, BB.sharpen(part), int(48 * k) - round(CX_SRC * S_H * k), int(round(r0 * k)))
    return {'head': BB.quantize(head, pal), 'body': BB.quantize(body, pal)}


FACE_BOX = (36, 24, 60, 42)            # x0, y0, x1, y1 at 96: eyes, glasses rims, mouth


def keep_face_lines(h96, h48):
    """48 px face: where a 2x2 block of the 96 face holds an eye / glasses line (dark or gold-rim pixel), use it, so the
    eyes and glasses survive the reduction instead of averaging into skin."""
    out = h48.copy(); x0, y0, x1, y1 = FACE_BOX
    for y in range(y0 // 2, y1 // 2):
        for x in range(x0 // 2, x1 // 2):
            blk = h96[2 * y:2 * y + 2, 2 * x:2 * x + 2].reshape(-1, 4)
            blk = blk[blk[:, 3] > 0]
            if not len(blk) or not out[y, x, 3]: continue
            L, C, hh = lch(rgb2oklab(blk[:, :3].astype(float)))
            i = int(np.argmin(L))
            if L[i] < 0.62 and L.max() - L[i] > 0.12: out[y, x] = blk[i]
    # violet irises (96 rows 28-37, inside the face 43..55): each iris pixel marks the 48 pixel one row lower than y//2
    # (the 48 head is reduced from the painting, its face sits ~1 row lower), coloured with the iris colour
    sub = h96[28:38, 43:56]; L, C, hh = lch(rgb2oklab(sub[:, :, :3].reshape(-1, 3).astype(float)))
    eye = (sub[:, :, 3] > 0).reshape(-1) & (C > 0.10) & (hh > 275) & (hh < 345) & (L < 0.5)
    if eye.any():
        col = sub.reshape(-1, 4)[eye][np.argmin(L[eye])]
        for j in np.where(eye)[0]:
            y, x = 28 + j // 13, 43 + j % 13
            out[(y + 2) // 2, x // 2] = col
    return out


def use_front_tables():
    U.P_DX, U.S_DX, U.TILT, U.LEG_X = P_DX, S_DX, TILT, LEG_X
    U.leg_state, U.draw_leg = leg_state, draw_leg
    U.HAIR_ROWS = (30, 48); U.RIBBON_FROM = 36; U.NECK_ROWS = (40, 50)


def build(front, pal_dirs, out):
    use_front_tables()
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for d in pal_dirs: paths += sorted(glob.glob(str(Path(d) / '*_12f_[0-9][0-9]_96x128.png')))
    pal = BB.palette(paths, U.PAL_K); pal_lab = rgb2oklab(pal.astype(float))
    L96 = {k_: U.outline(v, pal_lab, pal) for k_, v in base_layers_front(front, pal, 1.0).items()}
    L48 = {k_: U.outline(v, pal_lab, pal) for k_, v in base_layers_front(front, pal, 0.5).items()}
    L96['head'] = U.ribbon_violet(L96['head'], pal, pal_lab); L48['head'] = U.ribbon_violet(L48['head'], pal, pal_lab)
    L48['head'] = keep_face_lines(L96['head'], L48['head'])
    L96['ribbon'] = U.ribbon_mask(L96['head'], 1); L48['ribbon'] = U.ribbon_mask(L48['head'], 2)
    h96, h48 = U.hand_mask(L96['body']), U.hand_mask48(L48['body'])
    face = np.zeros((H, W), bool); face[20:44, 36:60] = True       # glasses / eyes / earrings: no island clean-up
    meta = {'task': 'MORWEN-WALK-DOWN-77', 'design_reference': 'reference/morwen_front_candidate_73e99f19.png (candidate)',
            'frames': {}, 'palette_colours': int(len(pal)), 'hand_px': [int(h96.sum()), int(h48.sum())]}
    for f in range(NF):
        im, st = U.frame(f, L96, h96, 1)
        im = U.outline(im, pal_lab, pal); im, n96 = clean_islands_generic(im, face)
        im, _ = fill_small_holes(im, 3)
        Image.fromarray(im, 'RGBA').save(out / f'morwen_down_walk_77_12f_{f:02d}_96x128.png')
        s, _ = U.frame(f, L48, h48, 2)
        s, n48 = clean_islands_generic(s, face[::2, ::2])
        s, _ = fill_small_holes(s, 3)
        Image.fromarray(s, 'RGBA').save(out / f'morwen_down_walk_77_12f_{f:02d}_48x64.png')
        meta['frames'][f'{f:02d}'] = dict(R=st['R'], L=st['L'], levels96=U.levels(f, 1), levels48=U.levels(f, 2), islands=[n96, n48])
    (out / 'build_meta_77.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    return meta


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--front', type=Path, required=True)
    ap.add_argument('--palette-from', type=Path, nargs='+', required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(); m = build(a.front, a.palette_from, a.out); print('ok', m['palette_colours'], m['hand_px'])

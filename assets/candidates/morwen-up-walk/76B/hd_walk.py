"""MORWEN-WALK-4DIR-ART-FIX-02 driver shared by up 76B and down 77B: HD pixel re-draw (hdpix) + the 12-frame walk
machinery of 76 / 77 (legs, pelvis / shoulder phase, tilt on the cape side, ribbon / hem lag, hands, gap fill,
chain join). The earlier 76 / 77 candidates are left untouched for comparison."""
import os, sys, json, glob
from pathlib import Path
HERE = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(HERE, '..', '..')
sys.path[:0] = [HERE, os.path.join(CAND, 'morwen-up-walk', '76'), os.path.join(CAND, 'morwen-down-walk', '77'),
                os.path.join(CAND, 'morwen-left-walk', '74D')]
import numpy as np
from PIL import Image
import hdpix as HP
import build_morwen76 as U
from walkclean import clean_islands_generic, fill_small_holes

NF = 12
HD_ROWS = dict(SHOULDER_ROW=62, WAIST_ROW=78, HEM_ROW=94, NECK_ROWS=(46, 58), CAPE_SIDE=(30, 66))


def side_paths():
    return (sorted(glob.glob(os.path.join(CAND, 'morwen-left-walk/74G/*_12f_[0-9][0-9]_96x128.png'))) +
            sorted(glob.glob(os.path.join(CAND, 'morwen-right-walk/75/*_12f_[0-9][0-9]_96x128.png'))))


def layers(src, segs, cut, hair_rows, cx, front, ramps):
    o = np.array(Image.open(src).convert('RGBA'))
    a = o[:, :, 3].copy(); a[cut[0]:, cut[1]:cut[2]] = 0
    lab, L = HP.classify(o[:, :, :3], a, hair_rows)
    CL = HP.class_L(lab, L)
    out = {}
    for k, (W, H) in ((1, (96, 128)), (2, (48, 64))):
        sg = [((s0, s1), (d0 // k, d1 // k), sh / k) for (s0, s1), (d0, d1), sh in segs]
        lb, Lm = HP.block_render(o[:, :, :3], a, lab, L, sg, (W, H), cx, W // 2, 0.27 if k == 1 else 0.35)
        neck = HD_ROWS['NECK_ROWS'][0] // k + 6 // k        # head layer = rows above the collar, body = below
        img, _, lb2 = HP.paint(lb, Lm, ramps, CL, inner_lines=(k == 1))
        face = HP.face_front(img, k, ramps, lb2) if front else None
        head = img.copy(); body = img.copy()
        split = (segs[0][1][1]) // k
        head[split:] = 0; body[:split] = 0
        out[k] = dict(head=head, body=body, face=face, lab=lb2)
    return out


def build(view, src, segs, cut, hair_rows, cx, out, prefix, task):
    front = view == 'front'
    if front:
        import build_morwen77 as F77; F77.use_front_tables()
    for kk, v in HD_ROWS.items(): setattr(U, kk, v)
    ramps = HP.side_ramps(side_paths())
    pal = np.array(sorted({c for r in ramps.values() for c in r} | {HP.OUTLINE}), np.uint8)
    pal_lab = HP.rgb2oklab(pal.astype(float))
    Ls = layers(src, segs, cut, hair_rows, cx, front, ramps)
    out.mkdir(parents=True, exist_ok=True)
    meta = dict(task=task, view=view, method='hdpix part-label cel re-draw (side ramps) + 76/77 walk', ramps=ramps,
                segments=segs, frames={})
    for k, s in ((1, '96x128'), (2, '48x64')):
        L = dict(head=Ls[k]['head'], body=Ls[k]['body'])
        L['ribbon'] = U.ribbon_mask(L['head'], k)
        hands = U.hand_mask(L['body'], k)
        prot = np.zeros(L['head'].shape[:2], bool)
        if Ls[k]['face']:
            x0, y0, x1, y1 = Ls[k]['face']; prot[max(0, y0 - 1):y1 + 2, max(0, x0):x1 + 1] = True
            meta.setdefault('face_box', {})[s] = [int(max(0, x0)), int(max(0, y0 - 2)), int(x1 + 1), int(y1 + 3)]   # x0,y0,x1,y1 (+1 px head bob)
        for f in range(NF):
            im, st = U.frame(f, L, hands, k)
            im, n = clean_islands_generic(im, prot); im, nh = fill_small_holes(im, 3)
            Image.fromarray(im, 'RGBA').save(out / f'{prefix}_12f_{f:02d}_{s}.png')
            meta['frames'].setdefault(f'{f:02d}', {})[s] = dict(islands=n, holes=nh, R=st['R'], L=st['L'])
    (out / f'build_meta_{prefix.split("_")[-1]}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    return meta

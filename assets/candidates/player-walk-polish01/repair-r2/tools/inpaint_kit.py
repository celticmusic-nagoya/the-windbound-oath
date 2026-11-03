#!/usr/bin/env python3
"""Leg-repaint kit for frames that need NEW drawing (PLAYER-WALK-POLISH-01).

make : writes, per target frame (base = the official PNG named in index.json, not copied), a repaint mask (white = may be repainted:
       both legs, the space either leg may move into, and a margin of hem) and a short brief.
merge: takes a repainted image from any drawing/inpainting tool and keeps ONLY the masked pixels;
       every pixel outside the mask is restored from the official PNG, so face, hair, body, sword,
       cape and canvas/anchor cannot change. Then checks size, alpha and the foot baseline.

usage (repository root):
  python3 assets/candidates/player-walk-polish01/repair-r2/tools/inpaint_kit.py make
  python3 assets/candidates/player-walk-polish01/repair-r2/tools/inpaint_kit.py merge TARGET EDITED.png OUT.png
"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mirror_legs import leg_mask  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
KIT = os.path.join(ROOT, 'assets/candidates/player-walk-polish01/repair-r2/inpaint-kit')
A = 'img/field/characters/aidan/'
# target -> (official base, rect, axis, baseline y, pose brief)
TARGETS = {
    'aidan_walk_down_04': (A + 'aidan_walk_down_01.png', (976, 890, 1207, 1240), 1091, 1229,
                           '右足（画面左）を前に出して接地、左足（画面右）は後方で浮かせる。main 01 の左右の役割を逆にした姿勢'),
    'aidan_walk_down_05': (A + 'aidan_walk_down_02.png', (976, 890, 1207, 1240), 1091, 1229,
                           '右足で支持、左足（画面右）は後ろへ蹴り出し（靴底が見える）。main 02 の左右逆'),
    'aidan_walk_down_06': (A + 'aidan_walk_down_06.png', (976, 890, 1207, 1240), 1091, 1229,
                           '右支持の後半、左足（画面右）が右足の横を通過。main 06 の左右逆'),
    'aidan_walk_up_04': (A + 'aidan_walk_up_03.png', (925, 900, 1155, 1240), 1040, 1229,
                         '左足（画面左）を前方（奥）に接地、右足（画面右）は手前で支持。main 03 の左右逆'),
    'aidan_walk_up_05': (A + 'aidan_walk_up_04.png', (925, 900, 1155, 1240), 1040, 1229,
                         '左支持、右足（画面右）のつま先が離れ靴底が見える。main 04 の左右逆'),
    'aidan_walk_up_06': (A + 'aidan_walk_up_06.png', (925, 900, 1155, 1240), 1040, 1229,
                         '左支持の後半、右足（画面右）が通過。main 06 の左右逆'),
}
LEGS = [(0, 38, 0.42, 1.0)]


def mask_for(a, rect, axis):
    m = leg_mask(a, rect, LEGS, 0.30)
    W = m.shape[1]; xs = np.arange(W); src = np.round(2 * axis - xs).astype(int); ok = (src >= 0) & (src < W)
    mm = np.zeros_like(m); mm[:, ok] = m[:, src[ok]]
    r = np.zeros_like(m); x0, y0, x1, y1 = rect; r[y0 - 30:y1, x0 - 30:x1 + 30] = True
    return ndi.binary_dilation(m | mm, iterations=14) & r   # room for the new leg position + hem margin


def make():
    os.makedirs(KIT, exist_ok=True); index = {}
    for t, (base, rect, axis, base_y, brief) in TARGETS.items():
        a = np.array(Image.open(os.path.join(ROOT, base)).convert('RGBA'))
        m = mask_for(a, rect, axis)
        Image.fromarray((m * 255).astype(np.uint8)).save(os.path.join(KIT, t + '_mask.png'))
        # preview: base with the repaint area tinted
        p = a.astype(float).copy(); p[m, :3] = p[m, :3] * 0.5 + np.array([255, 40, 160]) * 0.5; p[m, 3] = np.maximum(p[m, 3], 120)
        Image.fromarray(p.astype(np.uint8)).crop((rect[0] - 200, rect[1] - 400, rect[2] + 200, 1260)).save(os.path.join(KIT, t + '_mask_preview.png'))
        index[t] = {'base': base, 'canvas': list(a.shape[1::-1]), 'anchor': [1024, 1230], 'baseline_y': base_y,
                    'mask_bbox': list(map(int, (np.nonzero(m)[1].min(), np.nonzero(m)[0].min(), np.nonzero(m)[1].max() + 1, np.nonzero(m)[0].max() + 1))),
                    'pose': brief}
    json.dump(index, open(os.path.join(KIT, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('kit:', len(index), 'targets ->', os.path.relpath(KIT, ROOT))


def merge(target, edited, out):
    base, rect, axis, base_y, _ = TARGETS[target]
    a = np.array(Image.open(os.path.join(ROOT, base)).convert('RGBA'))
    e = Image.open(edited).convert('RGBA')
    if e.size != (a.shape[1], a.shape[0]):
        sys.exit('NG: size %s != %s (keep the canvas; do not crop or rescale)' % (e.size, a.shape[1::-1]))
    e = np.array(e); m = mask_for(a, rect, axis)
    o = a.copy(); o[m] = e[m]
    al = o[..., 3]; ys = np.nonzero(al > 0)[0]
    res = {'outside_mask_identical': bool((o[~m] == a[~m]).all()), 'feet_bottom': int(ys.max()), 'on_baseline': abs(int(ys.max()) - base_y) <= 2,
           'opaque_background_px_in_mask': int(((al == 255) & m & (o[..., :3].std(-1) < 2) & (o[..., :3].mean(-1) > 240)).sum())}
    Image.fromarray(o).save(out); print(json.dumps(res, ensure_ascii=False))


if __name__ == '__main__':
    if sys.argv[1:2] == ['make']:
        make()
    elif sys.argv[1:2] == ['merge'] and len(sys.argv) == 5:
        merge(*sys.argv[2:5])
    else:
        sys.exit(__doc__)

#!/usr/bin/env python3
"""Before/after sheets and per-frame checks for PLAYER-WALK-POLISH-01. Run from the repository root."""
import json, os
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
CAND = os.path.join(ROOT, 'assets/candidates/player-walk-polish01')
OUT = os.path.join(CAND, 'compare')
AID, FIO = 'img/field/characters/aidan/', 'img/field/moss/real/fiona/'
BG = (70, 100, 70, 255)

SETS = {
    # name: (before files, after files, crop full, crop legs, baseline y)
    'aidan_down': ([AID + 'aidan_walk_down_%02d.png' % i for i in range(1, 7)], ['aidan/frames/aidan_walk_down_%02d.png' % i for i in range(1, 7)], (560, 100, 1600, 1240), (930, 860, 1260, 1240), 1230),
    'aidan_up': ([AID + 'aidan_walk_up_%02d.png' % i for i in range(1, 7)], ['aidan/frames/aidan_walk_up_%02d.png' % i for i in range(1, 7)], (560, 100, 1600, 1240), (880, 860, 1210, 1240), 1230),
    'fiona_side_left': ([FIO + 'fiona_side_left_%02d.png' % i for i in range(1, 7)], ['reference/fiona-side-cue-swap/fiona_side_left_%02d.png' % i for i in range(1, 7)], (400, 170, 860, 800), (410, 620, 810, 795), 790),
    'fiona_side_right': ([FIO + 'fiona_side_right_%02d.png' % i for i in range(1, 7)], ['reference/fiona-side-cue-swap/fiona_side_right_%02d.png' % i for i in range(1, 7)], (270, 170, 730, 800), (280, 620, 680, 795), 790),
    'fiona_up': ([FIO + 'fiona_walk_up_%02d.png' % i for i in range(1, 5)], ['fiona/frames/fiona_walk_up_%02d.png' % i for i in range(1, 5)], (380, 120, 900, 800), (520, 600, 780, 795), 790),
}


def tile(p, box, h):
    im = Image.open(p).convert('RGBA'); bg = Image.new('RGBA', im.size, BG); bg.alpha_composite(im)
    t = bg.crop(box); return t.resize((round(t.width * h / t.height), h), Image.LANCZOS)


def sheet(name, before, after, box, legs):
    rows = []
    for label, files, base in (('BEFORE (main)', before, ROOT), ('AFTER (candidate)', after, CAND)):
        for b, h in ((box, 300), (legs, 170)):
            ts = [tile(os.path.join(base, f), b, h) for f in files]
            w = sum(t.width for t in ts) + 4 * len(ts)
            r = Image.new('RGBA', (w + 150, h + 18), (30, 30, 30, 255)); d = ImageDraw.Draw(r)
            d.text((4, 4), label, fill='white')
            x = 150
            for i, t in enumerate(ts):
                r.paste(t, (x, 18)); d.text((x + 3, 4), '%02d' % (i + 1), fill='white'); x += t.width + 4
            rows.append(r)
    W = max(r.width for r in rows); H = sum(r.height for r in rows)
    s = Image.new('RGB', (W, H), (30, 30, 30)); y = 0
    for r in rows:
        s.paste(r, (0, y)); y += r.height
    s.save(os.path.join(OUT, name + '.png'))


def checks(files, base, baseline):
    res = []
    for f in files:
        a = np.array(Image.open(os.path.join(base, f)).convert('RGBA'))
        al = a[..., 3]
        bb = Image.fromarray(al).getbbox()
        partial = int(((al > 0) & (al < 255)).sum())
        # interior pinholes: transparent pixels fully enclosed by opaque body
        from scipy import ndimage as ndi
        op = al > 200
        holes = int((ndi.binary_fill_holes(op) & ~op).sum())
        res.append({'file': f, 'size': list(a.shape[1::-1]), 'bbox': list(bb), 'feet_bottom': bb[3] - 1, 'on_baseline': bb[3] - 1 >= baseline - 2,
                    'partial_alpha_px': partial, 'enclosed_hole_px': holes})
    return res


def main():
    os.makedirs(OUT, exist_ok=True)
    rep = {}
    for name, (before, after, box, legs, base_y) in SETS.items():
        sheet(name, before, after, box, legs)
        rep[name] = {'before': checks(before, ROOT, base_y), 'after': checks(after, CAND, base_y)}
    json.dump(rep, open(os.path.join(OUT, 'frame_checks.json'), 'w'), indent=1)
    for name, r in rep.items():
        for k in ('before', 'after'):
            print(name, k, ' '.join('%s:%s/%d' % (c['feet_bottom'], 'ok' if c['on_baseline'] else 'NG', c['enclosed_hole_px']) for c in r[k]))


if __name__ == '__main__':
    main()

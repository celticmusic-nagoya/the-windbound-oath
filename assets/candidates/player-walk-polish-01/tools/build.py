#!/usr/bin/env python3
"""PLAYER-WALK-POLISH-01 candidate frames: rebuild every candidate PNG from the production PNGs on main.

Production PNGs are only READ. Output goes to assets/candidates/player-walk-polish-01/{aidan,fiona}/
and a manifest.json with the source of every frame and sha256 of sources and outputs.
Run from the repository root:  python3 assets/candidates/player-walk-polish-01/tools/build.py
"""
import hashlib, json, os, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
CAND = os.path.join(ROOT, 'assets/candidates/player-walk-polish-01')
TOOLS = os.path.dirname(os.path.abspath(__file__))
AID = 'img/field/characters/aidan/'
FIO = 'img/field/moss/real/fiona/'
LEGS = ['--legs', '0-38:0.42:1.0', '--dark', '0.30']

# Aidan front/back: the painted cycles plant the same foot (his left) in every frame.
# New 6-frame cycles = 3 painted frames + the same 3 with only the legs mirrored (other foot).
#   down: contact(01) -> support/kick(02) -> passing(06) -> mirrored 01, 02, 06
#   up:   contact(03) -> toe-off(04)      -> passing(06) -> mirrored 03, 04, 06
AIDAN = {
    'down': {'axis': 1091, 'rect': (976, 890, 1207, 1240), 'order': ['01', '02', '06', 'M01', 'M02', 'M06']},
    'up':   {'axis': 1040, 'rect': (940, 900, 1141, 1240), 'order': ['03', '04', '06', 'M03', 'M04', 'M06'],
             'rect_override': {'04': (925, 900, 1155, 1240)}},   # the lifted sole of 04 is wider
}
# Fiona profile: the near (flower) boot leads in all 6 painted frames. New cycle:
#   contact(04) -> narrowing(03) -> passing(01) -> same three with the far leg leading (S = swapped cues)
FIONA_SIDE = ['04', '03', '01', 'S04', 'S03', 'S01']
RIGHT_SHIFT = {'01': -148, '02': -148, '03': -148, '04': -149, '05': -148, '06': -149}   # right = flip(left) rolled (verified pixel-exact on main)
# Fiona back: 01/03/04 are painted ~5% larger than idle/02 (the head pumps every step) -> scale about the foot anchor
FIONA_UP_SCALE = {'01': 0.955, '02': 1.0, '03': 0.945, '04': 0.955}
ANCHOR_F = (640, 790)


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def run(tool, *args):
    subprocess.run([sys.executable, '-I', os.path.join(TOOLS, tool), *map(str, args)], check=True, stdout=subprocess.DEVNULL)


def scale_about(src, dst, s, anchor):
    im = Image.open(src).convert('RGBA')
    if s == 1.0:
        im.save(dst); return
    # exact scale about the anchor (no rounding of the paste offset): output(x,y) <- input(ax + (x-ax)/s, ay + (y-ay)/s)
    ax, ay = anchor
    out = im.transform(im.size, Image.AFFINE, (1 / s, 0, ax - ax / s, 0, 1 / s, ay - ay / s), resample=Image.BICUBIC)
    out.save(dst)


def main():
    man = {'task': 'PLAYER-WALK-POLISH-01', 'status': 'candidate (not adopted)', 'frames': {}}
    def rec(out, kind, srcs, note):
        man['frames'][os.path.relpath(out, CAND)] = {'kind': kind, 'sources': {s: sha(os.path.join(ROOT, s)) for s in srcs}, 'sha256': sha(out), 'note': note}

    for d, cfg in AIDAN.items():
        for i, tag in enumerate(cfg['order'], 1):
            out = os.path.join(CAND, 'aidan', 'aidan_walk_%s_%02d.png' % (d, i))
            src = AID + 'aidan_walk_%s_%s.png' % (d, tag.lstrip('M'))
            if tag.startswith('M'):
                rect = cfg.get('rect_override', {}).get(tag[1:], cfg['rect'])
                run('mirror_legs.py', os.path.join(ROOT, src), out, '--axis', cfg['axis'], '--rect', *rect, '--sym', *LEGS)
                rec(out, 'legs-mirrored', [src], 'other foot: legs mirrored about x=%d, body unchanged' % cfg['axis'])
            else:
                shutil.copyfile(os.path.join(ROOT, src), out)
                rec(out, 'copy', [src], 'painted frame, unchanged (new cycle position %d)' % i)

    tmp = tempfile.mkdtemp()
    for i, tag in enumerate(FIONA_SIDE, 1):
        n = tag.lstrip('S'); src = FIO + 'fiona_side_left_%s.png' % n
        left = os.path.join(CAND, 'fiona', 'fiona_side_left_%02d.png' % i)
        if tag.startswith('S'):
            run('swap_side_legs.py', os.path.join(ROOT, src), left, '--band', 720, '--top', 60)
            rec(left, 'near-far-swapped', [src], 'far leg leading: flower moved to the trailing (near) boot, near/far shading swapped')
        else:
            shutil.copyfile(os.path.join(ROOT, src), left)
            rec(left, 'copy', [src], 'painted frame, unchanged (new cycle position %d)' % i)
        a = np.array(Image.open(left).convert('RGBA'))[:, ::-1]
        right = os.path.join(CAND, 'fiona', 'fiona_side_right_%02d.png' % i)
        Image.fromarray(np.roll(a, RIGHT_SHIFT[n], axis=1)).save(right)
        rec(right, 'mirror-of-left', [src], 'same rule as main: right = left flipped and shifted %d px' % RIGHT_SHIFT[n])

    for n, s in FIONA_UP_SCALE.items():
        src = FIO + 'fiona_walk_up_%s.png' % n
        out = os.path.join(CAND, 'fiona', 'fiona_walk_up_%s.png' % n)
        scale_about(os.path.join(ROOT, src), out, s, ANCHOR_F)
        rec(out, 'rescaled' if s != 1 else 'copy', [src], 'scaled x%.3f about the foot anchor (640,790) to idle size' % s if s != 1 else 'unchanged')

    json.dump(man, open(os.path.join(CAND, 'manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('frames:', len(man['frames']))


if __name__ == '__main__':
    main()

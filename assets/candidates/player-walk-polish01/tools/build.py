#!/usr/bin/env python3
"""PLAYER-WALK-POLISH-01 candidate frames: rebuild every candidate PNG from the production PNGs on main.

Production PNGs are only READ. Output goes to assets/candidates/player-walk-polish01/{aidan,fiona}/
and a manifest.json with the source of every frame and sha256 of sources and outputs.
Run from the repository root:  python3 assets/candidates/player-walk-polish01/tools/build.py
"""
import hashlib, json, os, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
CAND = os.path.join(ROOT, 'assets/candidates/player-walk-polish01')
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
# main: right = flip(left) rolled by -148/-149 px (a 14.8-14.9 world px registration error, PR #129).
# Not carried over: the reference right frames are the plain flip, i.e. centred on the shared anchor x=640.
RIGHT_SHIFT = {'01': 0, '02': 0, '03': 0, '04': 0, '05': 0, '06': 0}
# Fiona back: 01/03/04 are painted ~5% larger than idle/02 (the head pumps every step) -> scale about the foot anchor
FIONA_UP_SCALE = {'01': 0.955, '02': 1.0, '03': 0.945, '04': 0.955}
ANCHOR_F = (640, 790)


# Anatomical annotation (front view: the person's LEFT foot is on screen RIGHT; back view: LEFT is screen LEFT;
# profile facing screen-left shows the LEFT side, so the near leg is the LEFT leg; facing right -> near = RIGHT).
G = lambda support, swing, phase, contact, note='': {'support': support, 'swing': swing, 'phase': phase, 'contact': contact, 'uncertain': note or None}
GAIT = {
 'aidan/frames/aidan_walk_down_01.png': G('L', 'R', '1 左足接地・右足後方', 'L heel/sole on ground (screen right, low)'),
 'aidan/frames/aidan_walk_down_02.png': G('L', 'R', '2 左支持・右足蹴り出し', 'L flat; R sole shown', 'R sole: toe-off vs heel strike not certain from a still'),
 'aidan/frames/aidan_walk_down_03.png': G('L', 'R', '3 左支持後半・右足通過', 'L flat; R just above ground'),
 'aidan/frames/aidan_walk_down_04.png': G('R', 'L', '4 右足接地・左足後方', 'legs-mirror of 01'),
 'aidan/frames/aidan_walk_down_05.png': G('R', 'L', '5 右支持・左足蹴り出し', 'legs-mirror of 02', 'same as 02'),
 'aidan/frames/aidan_walk_down_06.png': G('R', 'L', '6 右支持後半・左足通過', 'legs-mirror of 06'),
 'aidan/frames/aidan_walk_up_01.png': G('L', 'R', '1 右足前方接地・左足後方支持', 'R far (higher); L near, planted', 'support labelled as the planted near foot'),
 'aidan/frames/aidan_walk_up_02.png': G('R', 'L', '2 右支持・左足つま先離れ', 'L sole shown (toe-off)'),
 'aidan/frames/aidan_walk_up_03.png': G('R', 'L', '3 右支持後半・左足通過', 'L raised beside R'),
 'aidan/frames/aidan_walk_up_04.png': G('R', 'L', '4 左足前方接地・右足後方支持', 'legs-mirror of 01', 'as 01'),
 'aidan/frames/aidan_walk_up_05.png': G('L', 'R', '5 左支持・右足つま先離れ', 'legs-mirror of 02'),
 'aidan/frames/aidan_walk_up_06.png': G('L', 'R', '6 左支持後半・右足通過', 'legs-mirror of 03'),
 'fiona/frames/fiona_walk_up_01.png': G('R', 'L', '右足前方接地・左足つま先離れ（靴底）', 'L sole shown, screen left'),
 'fiona/frames/fiona_walk_up_02.png': G('both', None, '中立（待機画像と同一）', 'both flat', 'passing pose not drawn; identical to idle_up'),
 'fiona/frames/fiona_walk_up_03.png': G('L', 'R', '左足前方接地・右足つま先離れ（靴底）', 'R sole shown, screen right'),
 'fiona/frames/fiona_walk_up_04.png': G('both', None, '中立（両足接地）', 'both near ground', 'passing pose weak'),
}
for side, near, far in (('left', 'L', 'R'), ('right', 'R', 'L')):
    for i, (lead, ph) in enumerate(((near, '接地・最大歩幅'), (near, '支持前半・歩幅縮小'), (near, '両足接地（すれ違いではない）'),
                                   (far, '接地・最大歩幅'), (far, '支持前半・歩幅縮小'), (far, '両足接地（すれ違いではない）')), 1):
        GAIT['reference/fiona-side-cue-swap/fiona_side_%s_%02d.png' % (side, i)] = G(
            {'L': 'R', 'R': 'L'}[lead], lead, '前足=%s %s' % (lead, ph), 'silhouette = main frame; only flower/shade cues differ' if i > 3 else 'painted main frame',
            'REFERENCE ONLY: shading/cue swap does not count as an opposite-foot contact (spec PR #129); no crossing/passing frame' if i > 3 else 'near leg leads in every painted frame')
BANK = {**{'aidan/frames/aidan_walk_%s_%02d.png' % (d, i): ('aidan walk_%s' % d,) for d in ('up', 'down') for i in range(1, 7)},
        **{'fiona/frames/fiona_walk_up_%02d.png' % i: ('fiona walk_up',) for i in range(1, 5)},
        **{'reference/fiona-side-cue-swap/fiona_side_%s_%02d.png' % (s, i): ('reference only (fiona side_%s)' % s,) for s in ('left', 'right') for i in range(1, 7)}}


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
    man = {'task': 'PLAYER-WALK-POLISH-01', 'approval_status': 'CANDIDATE_NOT_ADOPTED', 'base_main': 'e63780543d7ba1719a39a2f68b9924dc6d5b3933',
           'spec': 'docs/art/PLAYER-WALK-POLISH-01_CLAUDE.md @ 84e5c0c5 (PR #129)', 'frames': {}}
    def rec(out, kind, srcs, note):
        key = os.path.relpath(out, CAND); im = Image.open(out)
        man['frames'][key] = {'kind': kind, 'target_bank': BANK.get(key, (None,))[0], 'size': list(im.size),
                              'sources': {s: sha(os.path.join(ROOT, s)) for s in srcs}, 'sha256': sha(out), 'note': note,
                              'gait': GAIT.get(key)}

    for d, cfg in AIDAN.items():
        for i, tag in enumerate(cfg['order'], 1):
            out = os.path.join(CAND, 'aidan', 'frames', 'aidan_walk_%s_%02d.png' % (d, i))
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
        left = os.path.join(CAND, 'reference', 'fiona-side-cue-swap', 'fiona_side_left_%02d.png' % i)
        if tag.startswith('S'):
            run('swap_side_legs.py', os.path.join(ROOT, src), left, '--band', 720, '--top', 60)
            rec(left, 'near-far-swapped', [src], 'far leg leading: flower moved to the trailing (near) boot, near/far shading swapped')
        else:
            shutil.copyfile(os.path.join(ROOT, src), left)
            rec(left, 'copy', [src], 'painted frame, unchanged (new cycle position %d)' % i)
        a = np.array(Image.open(left).convert('RGBA'))[:, ::-1]
        right = os.path.join(CAND, 'reference', 'fiona-side-cue-swap', 'fiona_side_right_%02d.png' % i)
        Image.fromarray(np.roll(a, RIGHT_SHIFT[n], axis=1)).save(right)
        rec(right, 'mirror-of-left', [src], 'left flipped about the anchor x=640 (main shifts it 148/149 px; not carried over)')

    for n, s in FIONA_UP_SCALE.items():
        src = FIO + 'fiona_walk_up_%s.png' % n
        out = os.path.join(CAND, 'fiona', 'frames', 'fiona_walk_up_%s.png' % n)
        scale_about(os.path.join(ROOT, src), out, s, ANCHOR_F)
        rec(out, 'rescaled' if s != 1 else 'copy', [src], 'scaled x%.3f about the foot anchor (640,790) to idle size' % s if s != 1 else 'unchanged')

    json.dump(man, open(os.path.join(CAND, 'manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('frames:', len(man['frames']))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""PLAYER-WALK-ARM-01: build the arm-swing candidates, QA json and comparison material. Run from the repository root.
Candidates (only the anatomical-left arm, screen-right, is replaced; everything else stays the production frame):
  slot 01 (production aidan_walk_down_01) <- left arm of official aidan_walk_down_02 (lowered arm)
  slot 02 (production aidan_walk_down_02) <- left arm of production down4/aidan_walk_down_06_ground (raised arm)
  slot 05 and slot 06 (PR #139 grounded 06): unchanged."""
import hashlib, json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
D = os.path.join(ROOT, 'assets/candidates/player-walk-polish01/arm-01-aidan-down'); T = os.path.join(D, 'tools'); C = os.path.join(D, 'compare')
A = os.path.join(ROOT, 'img/field/characters/aidan/')
PROD = {'01': A + 'aidan_walk_down_01.png', '05': A + 'aidan_walk_down_05.png', '02': A + 'aidan_walk_down_02.png', '06': A + 'down4/aidan_walk_down_06_ground.png'}
JOBS = {'01': PROD['02'], '02': PROD['06']}            # target slot -> donor of the left arm
BG = (70, 100, 70, 255)
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
load = lambda p: np.array(Image.open(p).convert('RGBA')).astype(int)
# Manual fist annotations (native px, read on 10 px grids at x3; +-3 px): fist bottom of the screen-right (anat. left)
# arm and fist centre-y of the screen-left (anat. right) arm, minus the chest/shoulder vertical shift vs. frame 01.
CHEST_DY = {'01': 0.0, '05': 0.8, '02': 5.1, '06': -0.8}
ANNOT = {'left_arm_fist_bottom': {'official': {'01': 790, '05': 790, '02': 812, '06': 777}, 'candidate': {'01': 805, '05': 790, '02': 780, '06': 777}},
         'right_arm_fist_centre': {'official': {'01': 695, '05': 690, '02': 722, '06': 713}}}


def run(*a):
    return subprocess.run([sys.executable, '-I', *a], check=True, capture_output=True, text=True).stdout


def tile(p, box, h, label=None, bg=BG):
    im = Image.open(p).convert('RGBA'); b = Image.new('RGBA', im.size, bg); b.alpha_composite(im)
    t = b.crop(box); t = t.resize((max(1, round(t.width * h / t.height)), h), Image.LANCZOS).convert('RGB')
    if label:
        d = ImageDraw.Draw(t); d.rectangle((0, 0, 7 * len(label) + 8, 15), fill=(0, 0, 0)); d.text((3, 2), label, fill='white')
    return t


def row(ts, gap=6):
    s = Image.new('RGB', (sum(t.width for t in ts) + gap * (len(ts) - 1), max(t.height for t in ts)), (30, 30, 30)); x = 0
    for t in ts:
        s.paste(t, (x, 0)); x += t.width + gap
    return s


def stack(rs):
    s = Image.new('RGB', (max(r.width for r in rs), sum(r.height for r in rs) + 6 * (len(rs) - 1)), (30, 30, 30)); y = 0
    for r in rs:
        s.paste(r, (0, y)); y += r.height + 6
    return s


def main():
    os.makedirs(C, exist_ok=True); qa = {'approval_status': 'CANDIDATE_NOT_ADOPTED', 'production_sha256': {k: sha(v) for k, v in PROD.items()}, 'frames': {}}
    cand = dict(PROD)
    for slot, donor in JOBS.items():
        out = os.path.join(D, 'aidan_walk_down_%s_arm_candidate.png' % slot); dbg = os.path.join(D, '_dbg%s' % slot)
        info = json.loads(run(os.path.join(T, 'arm_transplant.py'), PROD[slot], donor, out, '--debug', dbg))
        os.replace(os.path.join(dbg, 'region.png'), os.path.join(D, 'edit_mask_%s.png' % slot)); os.rmdir(dbg)
        t, c = load(PROD[slot]), load(out); diff = (c != t).any(-1); m = np.array(Image.open(os.path.join(D, 'edit_mask_%s.png' % slot))) > 0
        Image.fromarray((diff * 255).astype(np.uint8)).save(os.path.join(D, 'pixel_diff_%s.png' % slot))
        edit = ndi.binary_dilation(m, iterations=4)
        op = c[..., 3] >= 200; opt = t[..., 3] >= 200
        im = Image.open(out)
        qa['frames'][slot] = {
            'candidate': os.path.relpath(out, ROOT), 'sha256': sha(out), 'base': os.path.relpath(PROD[slot], ROOT), 'arm_donor': os.path.relpath(donor, ROOT), 'tool': info,
            'size_mode_ok': im.size == (2048, 1280) and im.mode == 'RGBA',
            'changed_px': int(diff.sum()), 'changed_outside_edit_region': int((diff & ~edit).sum()),
            'head_face_rows_0_560_identical': bool((c[:560] == t[:560]).all()), 'legs_rows_870_1280_identical': bool((c[870:] == t[870:]).all()),
            'screen_left_half_x_lt_1150_identical': bool((c[:, :1150] == t[:, :1150]).all()),
            'enclosed_hole_px': {'candidate': int((ndi.binary_fill_holes(op) & ~op).sum()), 'production': int((ndi.binary_fill_holes(opt) & ~opt).sum())},
            'canvas_corner_alpha_max': int(max(c[:8, :8, 3].max(), c[:8, -8:, 3].max(), c[-8:, :8, 3].max(), c[-8:, -8:, 3].max())),
            'lowest_opaque_row': {'candidate': int(np.nonzero((c[..., 3] > 128).any(1))[0].max()), 'production': int(np.nonzero((t[..., 3] > 128).any(1))[0].max())}}
        cand[slot] = out
    # swing balance from the manual annotations (relative to the chest)
    rel = lambda d: {k: v - CHEST_DY[k] for k, v in d.items()}
    L0, L1, R = rel(ANNOT['left_arm_fist_bottom']['official']), rel(ANNOT['left_arm_fist_bottom']['candidate']), rel(ANNOT['right_arm_fist_centre']['official'])
    order = ['01', '05', '02', '06']
    def stats(Lr):
        l = np.array([Lr[k] for k in order]); r = np.array([R[k] for k in order])
        mv = lambda v: [round(float(abs(v[(i + 1) % 4] - v[i])), 1) for i in range(4)]
        return {'left_rel_y': [round(float(x), 1) for x in l], 'left_range': round(float(np.ptp(l)), 1), 'left_moves_per_transition': mv(l),
                'right_rel_y': [round(float(x), 1) for x in r], 'right_range': round(float(np.ptp(r)), 1), 'right_moves_per_transition': mv(r),
                'corr_left_vs_right': round(float(np.corrcoef(l, r)[0, 1]), 2)}
    qa['swing_analysis'] = {'method': 'manual fist annotations on 10px grids (x3), +-3 px; y relative to chest shift; corr < 0 = arms in opposite phase',
                            'order': order, 'official': stats(L0), 'candidate': stats(L1), 'annotations': ANNOT, 'chest_dy': CHEST_DY}
    json.dump(qa, open(os.path.join(D, 'qa.json'), 'w'), indent=1, ensure_ascii=False)
    # ---- material
    full, arm = (560, 100, 1600, 1240), (1150, 520, 1420, 880)
    for slot in JOBS:
        row([tile(PROD[slot], arm, 420, 'production %s' % slot), tile(cand[slot], arm, 420, 'candidate %s' % slot), tile(JOBS[slot], arm, 420, 'arm donor')]).save(os.path.join(C, 'arm_zoom_%s.png' % slot))
        row([tile(PROD[slot], full, 420, 'production %s' % slot), tile(cand[slot], full, 420, 'candidate %s' % slot)]).save(os.path.join(C, 'full_%s.png' % slot))
    off = [PROD[k] for k in order]; new = [cand[k] for k in order]
    stack([row([tile(p, (780, 440, 1420, 880), 260, 'prod ' + k) for p, k in zip(off, order)]),
           row([tile(p, (780, 440, 1420, 880), 260, 'cand ' + k) for p, k in zip(new, order)])]).save(os.path.join(C, 'cycle4_arms_strip.png'))
    row([tile(p, (780, 440, 1420, 880), 300, l) for p, l in zip([cand['06'], cand['01']], ('06 (PR139, unchanged)', '01 candidate'))]).save(os.path.join(C, 'wrap_06_01.png'))
    def game(p, k):
        im = Image.open(p).convert('RGBA'); g = im.resize((round(2048 * .0625 * k), round(1280 * .0625 * k)), Image.LANCZOS)
        b = Image.new('RGBA', g.size, BG); b.alpha_composite(g); return b.convert('RGB')
    for k, n in ((1, 'game_scale_1x.png'), (2.625, 'game_scale_dpr2625.png')):
        stack([row([game(p, k) for p in off], 4), row([game(p, k) for p in new], 4)]).save(os.path.join(C, n))
    for name, seq in (('cycle4_production', off), ('cycle4_candidate', new)):
        for suf, h, ms in (('x4', 320, 75), ('game1x', 80, 75), ('arms_x2_slow', 440, 250)):
            box = (780, 440, 1420, 880) if suf.startswith('arms') else full
            fr = [tile(p, box, h) for p in seq]
            fr[0].save(os.path.join(C, '%s_%s.gif' % (name, suf)), save_all=True, append_images=fr[1:], duration=ms, loop=0)
    print(json.dumps({'frames': {k: {kk: v[kk] for kk in ('sha256', 'changed_px', 'changed_outside_edit_region', 'head_face_rows_0_560_identical', 'legs_rows_870_1280_identical', 'enclosed_hole_px')} for k, v in qa['frames'].items()},
                      'swing': {k: qa['swing_analysis'][k] for k in ('official', 'candidate')}}, indent=1))


if __name__ == '__main__':
    main()

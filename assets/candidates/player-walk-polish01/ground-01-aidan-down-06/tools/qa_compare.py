#!/usr/bin/env python3
"""PLAYER-WALK-GROUND-01: build the candidate set, QA json and comparison material. Run from the repository root.
Writes trials (shift 5/6/7), the chosen candidate, edit mask, pixel diff, re-measured gaps and compare/*."""
import hashlib, json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
D = os.path.join(ROOT, 'assets/candidates/player-walk-polish01/ground-01-aidan-down-06'); T = os.path.join(D, 'tools'); C = os.path.join(D, 'compare')
A = os.path.join(ROOT, 'img/field/characters/aidan/')
O6 = A + 'aidan_walk_down_06.png'; CAND = os.path.join(D, 'aidan_walk_down_06_ground_candidate.png')
SHIFTS = (5, 6, 7); CHOSEN = 7; BG = (70, 100, 70, 255)
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
load = lambda p: np.array(Image.open(p).convert('RGBA')).astype(int)
run = lambda *a: subprocess.run([sys.executable, '-I', *a], check=True, capture_output=True, text=True).stdout


def gaps(n, path):
    return json.loads(run(os.path.join(T, 'measure_gap.py'), '%d:%s' % (n, path)))[path]


def tile(p, box, h, label=None, bg=BG, line=True):
    im = Image.open(p).convert('RGBA'); b = Image.new('RGBA', im.size, bg); b.alpha_composite(im)
    if line:
        ImageDraw.Draw(b).line([(box[0], 1229), (box[2], 1229)], fill=(255, 80, 80, 255))
    t = b.crop(box); t = t.resize((max(1, round(t.width * h / t.height)), h), Image.NEAREST if h / (box[3] - box[1]) >= 2 else Image.LANCZOS).convert('RGB')
    if label:
        d = ImageDraw.Draw(t); d.rectangle((0, 0, 7 * len(label) + 8, 15), fill=(0, 0, 0)); d.text((3, 2), label, fill='white')
    return t


def row(ts, gap=6):
    s = Image.new('RGB', (sum(t.width for t in ts) + gap * (len(ts) - 1), max(t.height for t in ts)), (30, 30, 30)); x = 0
    for t in ts:
        s.paste(t, (x, 0)); x += t.width + gap
    return s


def main():
    os.makedirs(os.path.join(D, 'trials'), exist_ok=True); os.makedirs(C, exist_ok=True)
    trials = {}
    for s in SHIFTS:
        out = os.path.join(D, 'trials', 'shift%d.png' % s)
        info = json.loads(run(os.path.join(T, 'ground_support_boot.py'), out, '--shift', str(s), '--mask', os.path.join(D, 'trials', 'shift%d_mask.png' % s)))
        trials[s] = {'file': os.path.relpath(out, ROOT), 'sha256': sha(out), 'tool': info, 'gap': gaps(6, out)}
    # chosen candidate = trial with SHIFTS==CHOSEN (byte-identical copy)
    src = os.path.join(D, 'trials', 'shift%d.png' % CHOSEN)
    open(CAND, 'wb').write(open(src, 'rb').read())
    os.replace(os.path.join(D, 'trials', 'shift%d_mask.png' % CHOSEN), os.path.join(D, 'edit_mask.png'))
    for s in SHIFTS:
        m = os.path.join(D, 'trials', 'shift%d_mask.png' % s)
        if os.path.exists(m):
            os.remove(m)
    os.remove(src); trials[CHOSEN]['file'] = os.path.relpath(CAND, ROOT)
    o, c = load(O6), load(CAND); mask = np.array(Image.open(os.path.join(D, 'edit_mask.png'))) > 0
    diff = (c != o).any(-1)
    Image.fromarray((diff * 255).astype(np.uint8)).save(os.path.join(D, 'pixel_diff.png'))
    op, so = c[..., 3] >= 200, o[..., 3] >= 200
    semi_c, semi_o = (c[..., 3] > 0) & (c[..., 3] < 255), (o[..., 3] > 0) & (o[..., 3] < 255)
    im = Image.open(CAND); first = int(np.nonzero(diff.any(1))[0].min())
    ref = {n: gaps(n, A + 'aidan_walk_down_%02d.png' % n) for n in (1, 5, 2, 6)}
    qa = {
        'candidate': os.path.relpath(CAND, ROOT), 'sha256': sha(CAND), 'source_official_06_sha256': sha(O6),
        'size': list(im.size), 'mode': im.mode, 'size_mode_ok': im.size == (2048, 1280) and im.mode == 'RGBA', 'anchor': [1024, 1230],
        'method': 'support boot (anatomical right, screen-left) pulled down by a local vertical warp: 0 px at y<=1060, smoothstep to +7 px at y=1170, rigid +7 px below (ankle/boot/sole not stretched); official pixels only',
        'changed_px': int(diff.sum()), 'changed_px_outside_edit_mask': int((diff & ~mask).sum()),
        'outside_edit_mask_identical_to_official_06': bool(not (diff & ~mask).any()),
        'first_changed_row': first, 'rows_above_identical': bool((c[:first] == o[:first]).all()),
        'changed_bbox': [int(v) for v in (np.nonzero(diff)[1].min(), np.nonzero(diff)[0].min(), np.nonzero(diff)[1].max(), np.nonzero(diff)[0].max())],
        'shin_stretch': {'rows': 110, 'added_px': 7, 'ratio': round(7 / 110, 4)},
        'canvas_corner_alpha_max': int(max(c[:8, :8, 3].max(), c[:8, -8:, 3].max(), c[-8:, :8, 3].max(), c[-8:, -8:, 3].max())),
        'edge_opaque_px': int((c[0, :, 3] > 0).sum() + (c[-1, :, 3] > 0).sum() + (c[:, 0, 3] > 0).sum() + (c[:, -1, 3] > 0).sum()),
        'enclosed_hole_px': {'candidate': int((ndi.binary_fill_holes(op) & ~op).sum()), 'official_06': int((ndi.binary_fill_holes(so) & ~so).sum())},
        'semi_alpha_px': {'candidate': int(semi_c.sum()), 'official_06': int(semi_o.sum())},
        'lowest_opaque_row': {'candidate': int(np.nonzero((c[..., 3] > 128).any(1))[0].max()), 'official_06': int(np.nonzero((o[..., 3] > 128).any(1))[0].max())},
        'ground_gap_native_pr138_method': {'official_01': ref[1], 'official_05': ref[5], 'official_02': ref[2], 'official_06': ref[6], 'candidate_06': trials[CHOSEN]['gap']},
        'trials': trials,
    }
    json.dump(qa, open(os.path.join(D, 'qa.json'), 'w'), indent=1, ensure_ascii=False)
    # ---- comparison material
    full, legs, boot = (560, 100, 1600, 1240), (900, 820, 1280, 1240), (1000, 1100, 1140, 1240)
    t5, t6 = os.path.join(D, 'trials', 'shift5.png'), os.path.join(D, 'trials', 'shift6.png')
    row([tile(O6, full, 420, 'official 06'), tile(CAND, full, 420, 'candidate 06 (+7 boot)')]).save(os.path.join(C, 'full_official_vs_candidate.png'))
    row([tile(O6, boot, 420, 'official 06 x3'), tile(t5, boot, 420, '+5'), tile(t6, boot, 420, '+6'), tile(CAND, boot, 420, '+7 chosen')]).save(os.path.join(C, 'boot_zoom_trials.png'))
    row([tile(O6, (1000, 1040, 1140, 1240), 600, 'official 06 (1:3)'), tile(CAND, (1000, 1040, 1140, 1240), 600, 'candidate (1:3)')]).save(os.path.join(C, 'ankle_shin_zoom.png'))
    row([tile(CAND, legs, 380, 'on black', (0, 0, 0, 255), False), tile(CAND, legs, 380, 'on white', (255, 255, 255, 255), False)]).save(os.path.join(C, 'alpha_black_white.png'))
    seq_off = [A + 'aidan_walk_down_%02d.png' % n for n in (1, 5, 2, 6)]; seq_new = seq_off[:3] + [CAND]
    stack = [row([tile(p, (960, 1080, 1240, 1240), 220, l) for p, l in zip(seq_off, ('01', '05', '02', '06 official'))]),
             row([tile(p, (960, 1080, 1240, 1240), 220, l) for p, l in zip(seq_new, ('01', '05', '02', '06 candidate'))])]
    W = max(r.width for r in stack); s = Image.new('RGB', (W, sum(r.height for r in stack) + 6), (30, 30, 30)); s.paste(stack[0], (0, 0)); s.paste(stack[1], (0, stack[0].height + 6))
    s.save(os.path.join(C, 'cycle4_feet_ground_line.png'))
    row([tile(p, (960, 1080, 1240, 1240), 260, l) for p, l in zip([A + 'aidan_walk_down_02.png', CAND, A + 'aidan_walk_down_01.png'], ('02', '06 candidate', '01'))]).save(os.path.join(C, 'wrap_02_06_01.png'))
    def game(p, k):
        im = Image.open(p).convert('RGBA'); g = im.resize((round(2048 * .0625 * k), round(1280 * .0625 * k)), Image.LANCZOS)
        b = Image.new('RGBA', g.size, BG); b.alpha_composite(g); return b.convert('RGB')
    for k, n in ((1, 'game_scale_1x.png'), (2.625, 'game_scale_dpr2625.png')):
        row([game(p, k) for p in (A + 'aidan_walk_down_02.png', O6, CAND, A + 'aidan_walk_down_01.png')], 4).save(os.path.join(C, n))
    for name, seq in (('cycle4_official', seq_off), ('cycle4_candidate', seq_new)):
        for suf, h in (('x4', 320), ('game1x', 80)):
            fr = [tile(p, full, h) for p in seq]
            fr[0].save(os.path.join(C, '%s_%s.gif' % (name, suf)), save_all=True, append_images=fr[1:], duration=75, loop=0)
    print(json.dumps({k: qa[k] for k in ('sha256', 'changed_px', 'outside_edit_mask_identical_to_official_06', 'first_changed_row', 'enclosed_hole_px', 'ground_gap_native_pr138_method')}, indent=1))


if __name__ == '__main__':
    main()

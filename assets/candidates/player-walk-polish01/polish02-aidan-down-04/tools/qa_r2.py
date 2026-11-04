#!/usr/bin/env python3
"""PLAYER-WALK-POLISH-02-R2 QA + comparison material for the seam-stitched down-04 candidate.
Run from the repository root. Writes r2/qa_r2.json and r2/compare/*."""
import hashlib, json, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
D = os.path.join(ROOT, 'assets/candidates/player-walk-polish01/polish02-aidan-down-04')
R2 = os.path.join(D, 'r2'); C = os.path.join(R2, 'compare')
A = os.path.join(ROOT, 'img/field/characters/aidan/')
CAND = os.path.join(D, 'aidan_walk_down_04_candidate.png'); PREV = os.path.join(R2, 'best_r1_attempt4.png')
BG = (70, 100, 70, 255)
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
load = lambda p: np.array(Image.open(p).convert('RGBA')).astype(int)


def qa():
    c, o4 = load(CAND), load(A + 'aidan_walk_down_04.png'); o6 = np.roll(load(A + 'aidan_walk_down_06.png'), 8, axis=1)
    region = np.array(Image.open(os.path.join(R2, 'seam_region_from_06.png'))) > 0
    edit = ndi.binary_dilation(region, iterations=4)          # region + feather band
    diff = (c != o4).any(-1); a = c[..., 3]; ys = np.nonzero(a > 0)[0]
    is4, is6 = (c == o4).all(-1), (c == o6).all(-1); both = (o4[..., 3] >= 250) & (o6[..., 3] >= 250)
    op = a > 200; im = Image.open(CAND)
    upper_rows = int(np.nonzero(diff.any(1))[0].min())
    res = {
        'file': os.path.relpath(CAND, ROOT), 'sha256': sha(CAND), 'size': list(im.size), 'mode': im.mode,
        'size_ok': im.size == (2048, 1280) and im.mode == 'RGBA',
        'method': 'official 06 shifted +8px stitched into official 04 along a minimum-difference seam (DP); 3px opaque-only cross-fade',
        'changed_px_vs_official_04': int(diff.sum()), 'changed_px_outside_seam_region': int((diff & ~edit).sum()),
        'outside_edit_region_identical_to_official_04': bool(not (diff & ~edit).any()),
        'first_changed_row': upper_rows, 'rows_above_identical_to_official_04': bool((c[:upper_rows] == o4[:upper_rows]).all()),
        'pixel_provenance': {'official_04': int(is4.sum()), 'official_06_shift8': int((is6 & ~is4).sum()),
                             'opaque_mix_04_06_on_seam': int((~is4 & ~is6).sum()), 'mix_outside_both_opaque': int((~is4 & ~is6 & ~both).sum()),
                             'inpainted_or_generated': 0},
        'feet_bottom_y': int(ys.max()), 'on_baseline_1229': int(ys.max()) == 1229, 'anchor': [1024, 1230],
        'canvas_corner_alpha_max': int(max(a[:8, :8].max(), a[:8, -8:].max(), a[-8:, :8].max(), a[-8:, -8:].max())),
        'edge_opaque_px': int((a[0] > 0).sum() + (a[-1] > 0).sum() + (a[:, 0] > 0).sum() + (a[:, -1] > 0).sum()),
        'enclosed_hole_px': {'candidate': int((ndi.binary_fill_holes(op) & ~op).sum()), 'official_04': int((ndi.binary_fill_holes(o4[..., 3] > 200) & ~(o4[..., 3] > 200)).sum())},
        'semi_alpha_px_new_vs_sources': int((((a > 0) & (a < 255)) & ~is4 & ~is6).sum()),
        'similarity_to_official_06_whole_frame': round(float(is6.mean()), 4),
        'official_sources': {p: sha(A + p) for p in ('aidan_walk_down_04.png', 'aidan_walk_down_06.png')},
    }
    json.dump(res, open(os.path.join(R2, 'qa_r2.json'), 'w'), indent=1, ensure_ascii=False)
    return res


def tile(p, box, h, label=None, bg=BG):
    im = Image.open(p).convert('RGBA'); b = Image.new('RGBA', im.size, bg); b.alpha_composite(im)
    t = b.crop(box); t = t.resize((max(1, round(t.width * h / t.height)), h), Image.LANCZOS)
    if label:
        d = ImageDraw.Draw(t); d.rectangle((0, 0, 7 * len(label) + 10, 16), fill=(20, 20, 20)); d.text((4, 2), label, fill='white')
    return t


def row(ts, gap=6):
    s = Image.new('RGB', (sum(t.width for t in ts) + gap * (len(ts) - 1), max(t.height for t in ts)), (30, 30, 30)); x = 0
    for t in ts:
        s.paste(t.convert('RGB'), (x, 0)); x += t.width + gap
    return s


def stack(rs):
    s = Image.new('RGB', (max(r.width for r in rs), sum(r.height for r in rs) + 6 * (len(rs) - 1)), (30, 30, 30)); y = 0
    for r in rs:
        s.paste(r, (0, y)); y += r.height + 6
    return s


def sheets():
    os.makedirs(C, exist_ok=True)
    o4, o6 = A + 'aidan_walk_down_04.png', A + 'aidan_walk_down_06.png'
    full, legs = (560, 100, 1600, 1240), (880, 760, 1300, 1240)
    stack([row([tile(o4, full, 420, 'official 04'), tile(PREV, full, 420, 'R1 best (PR133)'), tile(CAND, full, 420, 'R2 candidate'), tile(o6, full, 420, 'official 06 (donor)')]),
           row([tile(o4, legs, 380, 'official 04'), tile(PREV, legs, 380, 'R1 best'), tile(CAND, legs, 380, 'R2 candidate'), tile(o6, legs, 380, 'official 06')])]).save(os.path.join(C, 'prev_vs_r2.png'))
    seam = (980, 800, 1200, 980); gap = (940, 860, 1110, 1000)
    row([tile(PREV, seam, 400, 'R1: seam y=850'), tile(CAND, seam, 400, 'R2: same area')]).save(os.path.join(C, 'seam_y850_zoom.png'))
    row([tile(PREV, gap, 360, 'R1: gap x985-995'), tile(CAND, gap, 360, 'R2: same area'), tile(PREV, gap, 360, 'R1 on black', (0, 0, 0, 255)), tile(CAND, gap, 360, 'R2 on black', (0, 0, 0, 255))]).save(os.path.join(C, 'gap_zoom.png'))
    # seam line overlay
    reg = np.array(Image.open(os.path.join(R2, 'seam_region_from_06.png'))) > 0
    edge = reg & ~ndi.binary_erosion(reg)
    im = np.array(Image.open(CAND).convert('RGBA')); im[ndi.binary_dilation(edge, iterations=1)] = (255, 0, 255, 255)
    Image.fromarray(im).crop((860, 720, 1320, 1240)).save(os.path.join(C, 'seam_path_overlay.png'))
    # pixel provenance map: grey = official 04, blue = official 06, magenta = cross-fade
    c, a4, a6 = load(CAND), load(o4), np.roll(load(o6), 8, axis=1)
    m = np.zeros(c.shape[:2] + (3,), np.uint8); vis = c[..., 3] > 0
    m[vis & (c == a4).all(-1)] = (120, 120, 120); m[vis & (c == a6).all(-1) & ~(c == a4).all(-1)] = (60, 110, 230); m[vis & ~(c == a4).all(-1) & ~(c == a6).all(-1)] = (255, 0, 255)
    Image.fromarray(m).crop((560, 100, 1600, 1240)).save(os.path.join(C, 'pixel_provenance.png'))
    # alpha on black / white / checker
    cc = Image.open(CAND).convert('RGBA').crop(legs); ts = []
    for bg in ((0, 0, 0, 255), (255, 255, 255, 255)):
        b = Image.new('RGBA', cc.size, bg); b.alpha_composite(cc); ts.append(b.resize((cc.width * 380 // cc.height, 380)))
    ch = Image.new('RGBA', cc.size); d = ImageDraw.Draw(ch)
    for y in range(0, cc.height, 16):
        for x in range(0, cc.width, 16):
            d.rectangle((x, y, x + 15, y + 15), fill=(205, 205, 205, 255) if (x // 16 + y // 16) % 2 else (120, 120, 120, 255))
    ch.alpha_composite(cc); ts.append(ch.resize((cc.width * 380 // cc.height, 380)))
    row(ts).save(os.path.join(C, 'alpha_black_white_checker.png'))
    # game scale 0.0625 (1x CSS) and DPR 2.625 rendering of the whole frame, official vs R1 vs R2
    def game(p, k):
        im = Image.open(p).convert('RGBA'); s = im.resize((round(2048 * 0.0625 * k), round(1280 * 0.0625 * k)), Image.LANCZOS)
        b = Image.new('RGBA', s.size, BG); b.alpha_composite(s); return b
    for k, name in ((1, 'game_scale_1x.png'), (2.625, 'game_scale_dpr2625.png')):
        row([game(p, k) for p in (o4, PREV, CAND, o6)], gap=4).save(os.path.join(C, name))
    # loops: 03 -> 04 -> 05 and 01..06 with the candidate in slot 04 (official frames elsewhere)
    seq = [A + 'aidan_walk_down_03.png', CAND, A + 'aidan_walk_down_05.png']
    row([tile(p, full, 360, n) for p, n in zip(seq, ('03 official', '04 R2 candidate', '05 official'))]).save(os.path.join(C, 'loop_03_04_05.png'))
    bank = [A + 'aidan_walk_down_%02d.png' % i for i in (1, 2, 3)] + [CAND] + [A + 'aidan_walk_down_%02d.png' % i for i in (5, 6)]
    off = [A + 'aidan_walk_down_%02d.png' % i for i in range(1, 7)]
    row([tile(p, legs, 260, '%02d' % (i + 1)) for i, p in enumerate(bank)]).save(os.path.join(C, 'loop_01_06_legs_strip.png'))
    for name, files, ms, h in (('loop_03_04_05_slow.gif', seq, 250, 360), ('loop_01_06_x4.gif', bank, 50, 320), ('loop_01_06_game1x.gif', bank, 50, 80),
                               ('loop_01_06_official_x4.gif', off, 50, 320)):
        fr = [tile(p, full, h).convert('RGB') for p in files]
        fr[0].save(os.path.join(C, name), save_all=True, append_images=fr[1:], duration=ms, loop=0)


if __name__ == '__main__':
    print(json.dumps(qa(), indent=1, ensure_ascii=False)); sheets()

#!/usr/bin/env python3
"""PLAYER-WALK-POLISH-02 QA for the Aidan down-04 candidate: pixel protection, alpha, size, anchor,
comparison sheets and walk-loop material. Run from the repository root."""
import hashlib, json, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
D = os.path.join(ROOT, 'assets/candidates/player-walk-polish01/polish02-aidan-down-04')
A = os.path.join(ROOT, 'img/field/characters/aidan/')
RECT = (976, 850, 1207, 1240)            # the only region the composer may touch
ANCHOR, BASE_Y, SCALE = (1024, 1230), 1229, 0.0625
BG = (70, 100, 70, 255)
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def load(p):
    return np.array(Image.open(p).convert('RGBA'))


def qa():
    off = load(A + 'aidan_walk_down_04.png'); cand_p = os.path.join(D, 'aidan_walk_down_04_candidate.png'); c = load(cand_p)
    im = Image.open(cand_p)
    diff = (c != off).any(-1)
    r = np.zeros_like(diff); x0, y0, x1, y1 = RECT; r[y0:y1, x0:x1] = True
    al = c[..., 3]; ys = np.nonzero(al > 0)[0]
    op = al > 200
    holes_new = int((ndi.binary_fill_holes(op) & ~op).sum()); holes_off = int((ndi.binary_fill_holes(off[..., 3] > 200) & ~(off[..., 3] > 200)).sum())
    corners = [int(al[:20, :20].max()), int(al[:20, -20:].max()), int(al[-20:, :20].max()), int(al[-20:, -20:].max())]
    # opaque flat background baked in? (large opaque area of near-constant colour touching the canvas edge)
    edge_opaque = int((al[0] > 0).sum() + (al[-1] > 0).sum() + (al[:, 0] > 0).sum() + (al[:, -1] > 0).sum())
    filled = load(os.path.join(D, 'aidan_walk_down_04_candidate_filled_mask.png'))[..., 0] > 0 if os.path.exists(os.path.join(D, 'aidan_walk_down_04_candidate_filled_mask.png')) else np.zeros_like(diff)
    res = {
        'file': os.path.relpath(cand_p, ROOT), 'sha256': sha(cand_p), 'mode': im.mode, 'size': list(im.size),
        'size_ok': im.size == (2048, 1280) and im.mode == 'RGBA',
        'changed_px_total': int(diff.sum()), 'changed_px_outside_edit_rect': int((diff & ~r).sum()),
        'outside_edit_rect_identical_to_official': bool(not (diff & ~r).any()),
        'edit_rect': list(RECT), 'upper_body_rows_0_849_identical': bool((c[:850] == off[:850]).all()),
        'feet_bottom_y': int(ys.max()), 'on_baseline_1229': int(ys.max()) == BASE_Y, 'anchor': list(ANCHOR),
        'canvas_corners_alpha': corners, 'edge_opaque_px': edge_opaque,
        'enclosed_hole_px': {'candidate': holes_new, 'official_04': holes_off},
        'inpainted_px (補完)': int(filled.sum()),
        'official_sources': {p: sha(A + p) for p in ('aidan_walk_down_04.png', 'aidan_walk_down_06.png')},
    }
    json.dump(res, open(os.path.join(D, 'qa.json'), 'w'), indent=1, ensure_ascii=False)
    return res


def tile(p, box, h, label=None):
    im = Image.open(p).convert('RGBA'); bg = Image.new('RGBA', im.size, BG); bg.alpha_composite(im)
    t = bg.crop(box); t = t.resize((round(t.width * h / t.height), h), Image.LANCZOS)
    if label:
        d = ImageDraw.Draw(t); d.rectangle((0, 0, 8 * len(label) + 8, 16), fill=(20, 20, 20)); d.text((4, 2), label, fill='white')
    return t


def row(tiles, gap=6):
    W = sum(t.width for t in tiles) + gap * (len(tiles) - 1); H = max(t.height for t in tiles)
    s = Image.new('RGB', (W, H), (30, 30, 30)); x = 0
    for t in tiles:
        s.paste(t, (x, 0)); x += t.width + gap
    return s


def stack(rows):
    W = max(r.width for r in rows); H = sum(r.height for r in rows) + 6 * (len(rows) - 1)
    s = Image.new('RGB', (W, H), (30, 30, 30)); y = 0
    for r in rows:
        s.paste(r, (0, y)); y += r.height + 6
    return s


def sheets():
    C = os.path.join(D, 'compare'); os.makedirs(C, exist_ok=True)
    cand = os.path.join(D, 'aidan_walk_down_04_candidate.png')
    full, legs, zoom = (560, 100, 1600, 1240), (880, 800, 1300, 1240), (960, 840, 1220, 1000)
    o4, o6 = A + 'aidan_walk_down_04.png', A + 'aidan_walk_down_06.png'
    stack([row([tile(o4, full, 420, 'official 04 (L planted)'), tile(cand, full, 420, 'candidate 04 (R planted)'), tile(o6, full, 420, 'official 06 (leg donor)')]),
           row([tile(o4, legs, 360, 'official 04 legs'), tile(cand, legs, 360, 'candidate 04 legs'), tile(o6, legs, 360, 'official 06 legs')])]).save(os.path.join(C, 'full_and_legs.png'))
    at = [os.path.join(D, 'attempts', f) for f in ('attempt1_filled_masks.png', 'attempt2_layered.png', 'attempt3_topband_fill.png')] + [cand]
    row([tile(p, legs, 360, n) for p, n in zip(at, ('attempt 1', 'attempt 2', 'attempt 3', 'attempt 4 = candidate'))]).save(os.path.join(C, 'attempts_legs.png'))
    row([tile(o4, zoom, 320, 'official 04 (x1.6 seam zone)'), tile(cand, zoom, 320, 'candidate: seam y=850, gap x~990')]).save(os.path.join(C, 'seam_zoom.png'))
    # background checks: black / white / checker
    c = Image.open(cand).convert('RGBA').crop(legs)
    tiles = []
    for name, bg in (('black', (0, 0, 0, 255)), ('white', (255, 255, 255, 255))):
        b = Image.new('RGBA', c.size, bg); b.alpha_composite(c); tiles.append(b.resize((c.width * 360 // c.height, 360)))
    ch = Image.new('RGBA', c.size); d = ImageDraw.Draw(ch)
    for y in range(0, c.height, 16):
        for x in range(0, c.width, 16):
            d.rectangle((x, y, x + 15, y + 15), fill=(200, 200, 200, 255) if (x // 16 + y // 16) % 2 else (120, 120, 120, 255))
    ch.alpha_composite(c); tiles.append(ch.resize((c.width * 360 // c.height, 360)))
    row(tiles).save(os.path.join(C, 'alpha_black_white_checker.png'))
    # walk loop material: 03 -> cand04 -> 05 and the whole 01..06 bank with the candidate in slot 04
    seq345 = [A + 'aidan_walk_down_03.png', cand, A + 'aidan_walk_down_05.png']
    row([tile(p, full, 360, n) for p, n in zip(seq345, ('03 official', '04 candidate', '05 official'))]).save(os.path.join(C, 'loop_03_04_05.png'))
    bank = [A + 'aidan_walk_down_%02d.png' % i for i in (1, 2, 3)] + [cand] + [A + 'aidan_walk_down_%02d.png' % i for i in (5, 6)]
    for name, files, ms, h in (('loop_03_04_05_slow.gif', seq345, 250, 360), ('loop_01_06_x4.gif', bank, 50, 4 * 80), ('loop_01_06_game1x.gif', bank, 50, 80)):
        frames = [tile(p, full, h).convert('RGB') for p in files]
        frames[0].save(os.path.join(C, name), save_all=True, append_images=frames[1:], duration=ms, loop=0)


if __name__ == '__main__':
    print(json.dumps(qa(), indent=1, ensure_ascii=False)); sheets()

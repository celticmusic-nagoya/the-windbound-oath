#!/usr/bin/env python3
"""PLAYER-WALK-ARM-02: rebuild the left-arm candidates with a tight arm-only core, QA and comparison material.
Run from the repository root.
  slot 01: production, unchanged (removes PR #142's large 06->01 return)
  slot 05: left arm of official aidan_walk_down_02 (lowered)    -- tight core, band 6
  slot 02: left arm of production grounded 06 (raised)           -- tight core, band 6
  slot 06: production grounded 06 (PR #139), unchanged
Writes candidates, masks (core and core+feather envelope), diffs, qa.json, compare/*.png, *.gif, *.mp4."""
import hashlib, json, math, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
D = os.path.join(ROOT, 'assets/candidates/player-walk-polish01/arm-02-aidan-down'); T = os.path.join(D, 'tools'); C = os.path.join(D, 'compare')
A = os.path.join(ROOT, 'img/field/characters/aidan/'); P142 = os.path.join(ROOT, 'assets/candidates/player-walk-polish01/arm-01-aidan-down/')
PROD = {'01': A + 'aidan_walk_down_01.png', '05': A + 'aidan_walk_down_05.png', '02': A + 'aidan_walk_down_02.png', '06': A + 'down4/aidan_walk_down_06_ground.png'}
V142 = dict(PROD, **{'01': P142 + 'aidan_walk_down_01_arm_candidate.png', '02': P142 + 'aidan_walk_down_02_arm_candidate.png'})
JOBS = {'05': PROD['02'], '02': PROD['06']}; BAND = 6; FEATHER = 3
ORDER = ['01', '05', '02', '06']; BG = (70, 100, 70, 255)
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
load = lambda p: np.array(Image.open(p).convert('RGBA')).astype(int)
# Fist landmarks. Official frames: manual reading (10 px grid x3, +-3 px, same values as ARM-01 README).
# Candidate frames: the donor landmark moved by the exact donor shift (the glove pixels are copied, not redrawn).
MANUAL_LEFT_BOTTOM = {'01': 790, '05': 790, '02': 812, '06': 777}; MANUAL_RIGHT_CENTRE = {'01': 695, '05': 690, '02': 722, '06': 713}
CHEST_DY = {'01': 0.0, '05': 0.8, '02': 5.1, '06': -0.8}


def run(*a):
    return subprocess.run([sys.executable, '-I', *a], check=True, capture_output=True, text=True).stdout


def comp(p):
    v = load(p).astype(float); return v[..., :3] * v[..., 3:4] / 255 + (1 - v[..., 3:4] / 255) * 40


def tile(p, box, h, label=None, bg=BG, nearest=False):
    im = Image.open(p).convert('RGBA'); b = Image.new('RGBA', im.size, bg); b.alpha_composite(im)
    t = b.crop(box); t = t.resize((max(1, round(t.width * h / t.height)), h), Image.NEAREST if nearest else Image.LANCZOS).convert('RGB')
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
    os.makedirs(C, exist_ok=True)
    NEW = dict(PROD); qa = {'approval_status': 'CANDIDATE_NOT_ADOPTED', 'production_sha256': {k: sha(v) for k, v in PROD.items()}, 'frames': {}}
    shifts = {}
    for slot, donor in JOBS.items():
        out = os.path.join(D, 'aidan_walk_down_%s_arm02_candidate.png' % slot); dbg = os.path.join(D, '_dbg%s' % slot)
        info = json.loads(run(os.path.join(T, 'arm_transplant.py'), PROD[slot], donor, out, '--tight', '--band', str(BAND), '--feather', str(FEATHER), '--debug', dbg))
        os.replace(os.path.join(dbg, 'region.png'), os.path.join(D, 'edit_core_%s.png' % slot)); os.rmdir(dbg)
        shifts[slot] = info['donor_shift']; NEW[slot] = out
        t, c = load(PROD[slot]), load(out); diff = (c != t).any(-1); core = np.array(Image.open(os.path.join(D, 'edit_core_%s.png' % slot))) > 0
        env = ndi.binary_dilation(core, iterations=FEATHER)
        Image.fromarray((env * 255).astype(np.uint8)).save(os.path.join(D, 'edit_envelope_%s.png' % slot))
        Image.fromarray((diff * 255).astype(np.uint8)).save(os.path.join(D, 'pixel_diff_%s.png' % slot))
        op, opt = c[..., 3] >= 200, t[..., 3] >= 200; im = Image.open(out)
        qa['frames'][slot] = {'candidate': os.path.relpath(out, ROOT), 'sha256': sha(out), 'base': os.path.relpath(PROD[slot], ROOT), 'arm_donor': os.path.relpath(donor, ROOT), 'tool': info,
                              'size_mode_ok': im.size == (2048, 1280) and im.mode == 'RGBA', 'changed_px': int(diff.sum()),
                              'changed_outside_core': int((diff & ~core).sum()), 'changed_outside_core_plus_%dpx_feather' % FEATHER: int((diff & ~env).sum()),
                              'alpha_changed_px': int((c[..., 3] != t[..., 3]).sum()),
                              'head_rows_0_560_identical': bool((c[:560] == t[:560]).all()), 'legs_rows_870_1280_identical': bool((c[870:] == t[870:]).all()),
                              'x_lt_1150_identical': bool((c[:, :1150] == t[:, :1150]).all()),
                              'alpha_bbox_unchanged': Image.fromarray(c[..., 3].astype(np.uint8)).getbbox() == Image.fromarray(t[..., 3].astype(np.uint8)).getbbox(),
                              'enclosed_hole_px': {'candidate': int((ndi.binary_fill_holes(op) & ~op).sum()), 'production': int((ndi.binary_fill_holes(opt) & ~opt).sum())}}
    # appearance change per cycle edge (same ROIs and metric as the independent QA in PR #143)
    rois = {'glove': (1240, 710, 1360, 825), 'white_lining': (1300, 740, 1390, 855), 'other_arm': (840, 560, 1000, 800), 'chest': (760, 300, 1340, 500)}
    edges = {}
    for name, S in (('production', PROD), ('pr142', V142), ('arm02', NEW)):
        Cm = {k: comp(p) for k, p in S.items()}; edges[name] = {}
        for a, b in zip(ORDER, ORDER[1:] + ORDER[:1]):
            edges[name]['%s>%s' % (a, b)] = {k: round(float(np.abs(Cm[a][y0:y1, x0:x1] - Cm[b][y0:y1, x0:x1]).mean()), 2) for k, (x0, y0, x1, y1) in rois.items()}
    qa['edge_appearance_mae'] = edges
    # fist landmarks relative to the chest
    left = dict(MANUAL_LEFT_BOTTOM); left['05'] = MANUAL_LEFT_BOTTOM['02'] + shifts['05'][1]; left['02'] = MANUAL_LEFT_BOTTOM['06'] + shifts['02'][1]
    def stat(L):
        l = np.array([L[k] - CHEST_DY[k] for k in ORDER]); r = np.array([MANUAL_RIGHT_CENTRE[k] - CHEST_DY[k] for k in ORDER])
        mv = lambda v: [round(float(abs(v[(i + 1) % 4] - v[i])), 1) for i in range(4)]
        return {'left': [round(float(x), 1) for x in l], 'left_moves': mv(l), 'right': [round(float(x), 1) for x in r], 'right_moves': mv(r), 'corr': round(float(np.corrcoef(l, r)[0, 1]), 2)}
    left142 = dict(MANUAL_LEFT_BOTTOM); left142['01'] = MANUAL_LEFT_BOTTOM['02'] - 5; left142['02'] = MANUAL_LEFT_BOTTOM['06'] + 9
    qa['fist_landmarks'] = {'note': 'official values: manual, +-3 px; candidate values: donor landmark + exact donor shift', 'order': ORDER,
                            'production': stat(MANUAL_LEFT_BOTTOM), 'pr142_shift_derived': stat(left142), 'arm02': stat(left)}
    json.dump(qa, open(os.path.join(D, 'qa.json'), 'w'), indent=1, ensure_ascii=False)
    # ---- material
    arm, full, body = (1180, 560, 1420, 880), (560, 100, 1600, 1240), (780, 440, 1420, 880)
    sets = (('production', PROD), ('PR142', V142), ('ARM-02', NEW))
    stack([row([tile(S[k], body, 240, '%s %s' % (n, k)) for k in ORDER]) for n, S in sets]).save(os.path.join(C, 'cycle4_three_versions.png'))
    for a, b in (('05', '02'), ('02', '06'), ('06', '01')):
        stack([row([tile(S[a], arm, 360, '%s %s' % (n, a)), tile(S[b], arm, 360, '%s %s' % (n, b))]) for n, S in sets]).save(os.path.join(C, 'edge_%s_%s_zoom.png' % (a, b)))
    for slot in JOBS:
        row([tile(PROD[slot], arm, 420, 'production %s' % slot), tile(V142[slot], arm, 420, 'PR142 %s' % slot), tile(NEW[slot], arm, 420, 'ARM-02 %s' % slot)]).save(os.path.join(C, 'slot_%s_versions.png' % slot))
    def game(p, k):
        im = Image.open(p).convert('RGBA'); g = im.resize((round(2048 * .0625 * k), round(1280 * .0625 * k)), Image.LANCZOS)
        b = Image.new('RGBA', g.size, BG); b.alpha_composite(g); return b.convert('RGB')
    for k, n in ((1, 'game_scale_1x.png'), (2.625, 'game_scale_dpr2625.png')):
        stack([row([game(S[f], k) for f in ORDER], 4) for _, S in sets]).save(os.path.join(C, n))
    # loop video: distance-driven like the game (300 world/s, stride 90, 4 frames, bob 25%), DPR 2.625, 60 fps, 3 cycles
    k = 2.625; s = 0.0625 * k; W, H = round(140 * k), round(80 * k)
    cache = {}
    def sprite(p):
        if p not in cache:
            im = Image.open(p).convert('RGBA'); cache[p] = im.resize((round(2048 * s), round(1280 * s)), Image.LANCZOS)
        return cache[p]
    tmp = tempfile.mkdtemp(); frames = []
    for i in range(int(60 * 0.3 * 3)):
        dist = i / 60 * 300; idx = int(dist // (90 / 4)) % 4
        bob = -abs(math.sin(dist / 45 * math.pi)) * 1.5 * 0.25           # world px = CSS px
        canvas = Image.new('RGB', (W * 3 + 8, H + 18), (30, 30, 30)); d = ImageDraw.Draw(canvas)
        for j, (n, S) in enumerate(sets):
            panel = Image.new('RGBA', (W, H), BG); sp = sprite(S[ORDER[idx]])
            ox = round(W / 2 - 1024 * s); oy = H - 6 * k - 1230 * s + bob * k
            # sub-pixel vertical offset: affine translate
            spt = sp.transform(sp.size, Image.AFFINE, (1, 0, 0, 0, 1, -(oy - math.floor(oy))), resample=Image.BILINEAR)
            panel.alpha_composite(spt, (ox, math.floor(oy)) if ox >= 0 else (0, 0))
            canvas.paste(panel.convert('RGB'), (j * (W + 4), 18)); d.text((j * (W + 4) + 3, 3), '%s  %s' % (n, ORDER[idx]), fill='white')
        fp = os.path.join(tmp, 'f%04d.png' % i); canvas.save(fp); frames.append(canvas)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '60', '-i', os.path.join(tmp, 'f%04d.png'), '-vf', 'scale=iw*2:ih*2:flags=neighbor,pad=ceil(iw/2)*2:ceil(ih/2)*2',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', os.path.join(C, 'loop_3versions_cycle90_bob25_dpr2625.mp4')], check=True)
    frames[0].save(os.path.join(C, 'loop_3versions_cycle90_bob25_dpr2625.gif'), save_all=True, append_images=frames[1:], duration=17, loop=0)
    for n, S in sets:
        fr = [tile(S[f], body, 300) for f in ORDER]
        fr[0].save(os.path.join(C, 'arms_slow_%s.gif' % n), save_all=True, append_images=fr[1:], duration=250, loop=0)
    print(json.dumps({'frames': {k: {kk: v[kk] for kk in ('sha256', 'changed_px', 'changed_outside_core', 'changed_outside_core_plus_3px_feather', 'head_rows_0_560_identical', 'legs_rows_870_1280_identical', 'x_lt_1150_identical', 'alpha_bbox_unchanged', 'enclosed_hole_px')} for k, v in qa['frames'].items()},
                      'edges': edges, 'landmarks': qa['fist_landmarks']}, indent=1))


if __name__ == '__main__':
    main()

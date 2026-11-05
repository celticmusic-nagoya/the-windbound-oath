#!/usr/bin/env python3
"""PLAYER-WALK-UP-02: comparison material (attempt sheet, A/B/C loops) and the repaint kit for the missing pose.
A = current 6 frames, bob 100%; B = 03-04-01-06, bob 25%; C = 5 frames with the push-off slot inserted
(06 -> PUSH -> 03 -> 04 -> 01), bob 25%, using the attempt-3 trial ONLY as a timing placeholder (not adoptable).
Run from the repository root."""
import json, math, os, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
D = os.path.join(ROOT, 'assets/candidates/player-walk-polish01/up-02-aidan-up-pushoff'); C = os.path.join(D, 'compare'); K = os.path.join(D, 'repaint-kit')
A = os.path.join(ROOT, 'img/field/characters/aidan/'); BG = (70, 100, 70, 255)
F = {n: A + 'aidan_walk_up_%02d.png' % n for n in range(1, 7)}; TRIAL = os.path.join(D, 'trials/attempt3_trousers_only_dx90.png')
VARIANTS = [('A current 01-06 bob100', [F[n] for n in range(1, 7)], 1.0),
            ('B 03-04-01-06 bob25', [F[n] for n in (3, 4, 1, 6)], .25),
            ('C PUSH-03-04-01-06 bob25 (placeholder)', [TRIAL, F[3], F[4], F[1], F[6]], .25)]

def tile(p, box, h, label=None):
    im = Image.open(p).convert('RGBA'); b = Image.new('RGBA', im.size, BG); b.alpha_composite(im)
    t = b.crop(box).resize((round((box[2] - box[0]) * h / (box[3] - box[1])), h), Image.LANCZOS).convert('RGB')
    if label:
        d = ImageDraw.Draw(t); d.rectangle((0, 0, 7 * len(label) + 8, 15), fill=(0, 0, 0)); d.text((3, 2), label, fill='white')
    return t

def row(ts):
    s = Image.new('RGB', (sum(t.width + 6 for t in ts) - 6, max(t.height for t in ts)), (30, 30, 30)); x = 0
    for t in ts:
        s.paste(t, (x, 0)); x += t.width + 6
    return s

def main():
    os.makedirs(C, exist_ok=True); os.makedirs(K, exist_ok=True)
    legs = (860, 760, 1260, 1240)
    row([tile(F[3], legs, 360, 'official 03 (base)'), tile(os.path.join(D, 'trials/attempt1_y960.png'), legs, 360, 'attempt 1'),
         tile(os.path.join(D, 'trials/attempt2_y780_dx95.png'), legs, 360, 'attempt 2'), tile(TRIAL, legs, 360, 'attempt 3'), tile(F[4], legs, 360, 'official 04 (donor leg)')]).save(os.path.join(C, 'attempts_legs.png'))
    # loops at DPR 2.625, 60 fps, distance driven (300 world/s, stride 90)
    k = 2.625; s = .0625 * k; W, H = round(140 * k), round(80 * k); cache = {}
    def sp(p):
        if p not in cache:
            cache[p] = Image.open(p).convert('RGBA').resize((round(2048 * s), round(1280 * s)), Image.LANCZOS)
        return cache[p]
    tmp = tempfile.mkdtemp()
    for i in range(54):
        dist = i / 60 * 300; canvas = Image.new('RGB', (W * 3 + 8, H + 18), (30, 30, 30)); d = ImageDraw.Draw(canvas)
        for j, (name, seq, bs) in enumerate(VARIANTS):
            idx = int(dist // (90 / len(seq))) % len(seq); bob = -abs(math.sin(dist / 45 * math.pi)) * 1.5 * bs
            oy = H - 6 * k - 1230 * s + bob * k; im = sp(seq[idx])
            im = im.transform(im.size, Image.AFFINE, (1, 0, 0, 0, 1, -(oy - math.floor(oy))), resample=Image.BILINEAR)
            panel = Image.new('RGBA', (W, H), BG); panel.alpha_composite(im, (round(W / 2 - 1024 * s), math.floor(oy)))
            canvas.paste(panel.convert('RGB'), (j * (W + 4), 18)); d.text((j * (W + 4) + 3, 3), '%s [%d]' % (name.split(' ')[0], idx + 1), fill='white')
        canvas.save(os.path.join(tmp, 'f%04d.png' % i))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '60', '-i', os.path.join(tmp, 'f%04d.png'), '-vf', 'scale=iw*2:ih*2:flags=neighbor,pad=ceil(iw/2)*2:ceil(ih/2)*2',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', os.path.join(C, 'loop_A_B_C_cycle90_dpr2625.mp4')], check=True)
    for name, seq, _ in VARIANTS:
        fr = [tile(p, (560, 100, 1600, 1240), 300) for p in seq]
        fr[0].save(os.path.join(C, 'slow_%s.gif' % name.split(' ')[0]), save_all=True, append_images=fr[1:], duration=250, loop=0)
    # repaint kit for the missing pose: base = official 03, repaint only the right-leg area below the hem
    b = np.array(Image.open(F[3]).convert('RGBA')); m = np.zeros(b.shape[:2], bool)
    poly = np.array([(1030, 790), (1150, 790), (1175, 1000), (1180, 1240), (1000, 1240), (1010, 1000)])
    import cv2
    mm = np.zeros(b.shape[:2], np.uint8); cv2.fillPoly(mm, [poly.astype(np.int32)], 1); m = mm.astype(bool)
    Image.fromarray((m * 255).astype(np.uint8)).save(os.path.join(K, 'aidan_walk_up_pushoff_mask.png'))
    pv = b.astype(float).copy(); pv[m, :3] = pv[m, :3] * .5 + np.array([255, 40, 160]) * .5; pv[m, 3] = np.maximum(pv[m, 3], 120)
    Image.fromarray(pv.astype(np.uint8)).crop((800, 600, 1300, 1260)).save(os.path.join(K, 'aidan_walk_up_pushoff_mask_preview.png'))
    json.dump({'target': 'aidan_walk_up_pushoff (new slot between 06 and 03)', 'base': 'img/field/characters/aidan/aidan_walk_up_03.png', 'canvas': [2048, 1280], 'anchor': [1024, 1230], 'baseline_y': 1229,
               'repaint_area': 'aidan_walk_up_pushoff_mask.png (white). Everything outside is restored from the base PNG when merged.',
               'pose': 'Back view. Anatomical RIGHT leg (screen right) extended behind the body towards the camera: knee slightly bent, heel lifted, sole facing the camera, toe on the ground line y~1229. Anatomical LEFT leg (screen left) as drawn in 03: planted, carrying the weight. Right boot = the right boot of the official set (do NOT copy the left boot; buckles/plates on the outer side of the right foot). Right thigh enters under the existing hem/cape; nothing above y=790 changes.',
               'references': ['aidan_walk_up_01/02/05 (left push-off: sole drawing, scale, shading)', 'aidan_walk_up_03 (right boot design, trousers)', 'docs/art/reference/characters/walk_delivery_20261011/aidan_back_a.png, aidan_back_b.png'],
               'merge': 'adapt assets/candidates/player-walk-polish01/repair-r2/tools/inpaint_kit.py (PR #132) merge with this mask'}, open(os.path.join(K, 'index.json'), 'w'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main()

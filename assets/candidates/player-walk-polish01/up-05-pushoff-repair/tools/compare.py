#!/usr/bin/env python3
"""PLAYER-WALK-UP-05 comparison material. Run from the repository root."""
import json, math, os, subprocess, tempfile, hashlib
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
D = os.path.join(ROOT, 'assets/candidates/player-walk-polish01/up-05-pushoff-repair'); C = os.path.join(D, 'compare'); os.makedirs(C, exist_ok=True)
A = os.path.join(ROOT, 'img/field/characters/aidan/'); BG = (70, 100, 70, 255)
F = {n: A + 'aidan_walk_up_%02d.png' % n for n in range(1, 7)}
NEW = os.path.join(D, 'aidan_walk_up_pushoff_candidate.png'); OLD = os.path.join(ROOT, 'assets/candidates/player-walk-polish01/up-04-pushoff-composite/aidan_walk_up_pushoff_trial.png')
MASK = os.path.join(ROOT, 'assets/candidates/player-walk-polish01/up-03-image-edit-kit/proposed_mask.png')
def tile(p, box, h, label=None, bg=BG):
    im = Image.open(p).convert('RGBA'); b = Image.new('RGBA', im.size, bg); b.alpha_composite(im)
    t = b.crop(box).resize((round((box[2] - box[0]) * h / (box[3] - box[1])), h), Image.NEAREST if h / (box[3] - box[1]) > 1.5 else Image.LANCZOS).convert('RGB')
    if label:
        d = ImageDraw.Draw(t); d.rectangle((0, 0, 7 * len(label) + 8, 15), fill=(0, 0, 0)); d.text((3, 2), label, fill='white')
    return t
def row(ts):
    s = Image.new('RGB', (sum(t.width + 6 for t in ts) - 6, max(t.height for t in ts)), (30, 30, 30)); x = 0
    for t in ts:
        s.paste(t, (x, 0)); x += t.width + 6
    return s
legs = (900, 780, 1220, 1250)
row([tile(F[3], legs, 440, 'official 03'), tile(OLD, legs, 440, 'PR151 trial (before)'), tile(NEW, legs, 440, 'UP-05 candidate (after)')]).save(os.path.join(C, 'before_after.png'))
items = [('1_sole_style', (1060, 990, 1150, 1145)), ('2_knee_top', (1040, 915, 1145, 975)), ('3_left_boot_outline', (1030, 990, 1090, 1170)),
         ('4_frill_remnant', (1095, 900, 1175, 1030)), ('5_holes', (1050, 960, 1140, 1035))]
for name, box in items:
    row([tile(OLD, box, 360, 'before'), tile(NEW, box, 360, 'after'), tile(F[3], box, 360, 'official 03')]).save(os.path.join(C, 'fix%s.png' % name))
o = np.array(Image.open(F[3])).astype(int); n = np.array(Image.open(NEW)).astype(int); m = np.array(Image.open(MASK)) > 0
diff = (o != n).any(-1); dv = np.zeros(o.shape[:2] + (3,), np.uint8); dv[m] = (60, 30, 60); dv[diff] = (255, 255, 255)
Image.fromarray(dv).crop((900, 760, 1240, 1250)).resize((680, 980), Image.NEAREST).save(os.path.join(C, 'rgba_diff_vs_official03.png'))
json.dump({'candidate_sha256': hashlib.sha256(open(NEW, 'rb').read()).hexdigest(), 'official03_sha256': hashlib.sha256(open(F[3], 'rb').read()).hexdigest(),
           'size': list(Image.open(NEW).size), 'mode': Image.open(NEW).mode, 'changed_px': int(diff.sum()), 'changed_outside_mask': int((diff & ~m).sum()),
           'lowest_opaque_row': int(np.nonzero((n[..., 3] > 128).any(1))[0].max())}, open(os.path.join(D, 'qa.json'), 'w'), indent=1)
def game(p, k):
    im = Image.open(p).convert('RGBA'); g = im.resize((round(2048 * .0625 * k), round(1280 * .0625 * k)), Image.LANCZOS)
    b = Image.new('RGBA', g.size, BG); b.alpha_composite(g); return b.convert('RGB')
row([game(p, 2.625) for p in (F[6], NEW, F[3], F[4], F[1])]).save(os.path.join(C, 'game_scale_dpr2625_cycle5.png'))
k = 2.625; s = .0625 * k; W, H = round(140 * k), round(80 * k); cache = {}
def sp(p):
    if p not in cache:
        cache[p] = Image.open(p).convert('RGBA').resize((round(2048 * s), round(1280 * s)), Image.LANCZOS)
    return cache[p]
V = [('4f 03-04-01-06', [F[3], F[4], F[1], F[6]]), ('5f NEW-03-04-01-06', [NEW, F[3], F[4], F[1], F[6]])]
tmp = tempfile.mkdtemp()
for i in range(54):
    dist = i / 60 * 300; canvas = Image.new('RGB', (W * 2 + 4, H + 18), (30, 30, 30)); d = ImageDraw.Draw(canvas)
    for j, (name, seq) in enumerate(V):
        idx = int(dist // (90 / len(seq))) % len(seq); bob = -abs(math.sin(dist / 45 * math.pi)) * 1.5 * .25
        oy = H - 6 * k - 1230 * s + bob * k; im = sp(seq[idx]); im = im.transform(im.size, Image.AFFINE, (1, 0, 0, 0, 1, -(oy - math.floor(oy))), resample=Image.BILINEAR)
        panel = Image.new('RGBA', (W, H), BG); panel.alpha_composite(im, (round(W / 2 - 1024 * s), math.floor(oy)))
        canvas.paste(panel.convert('RGB'), (j * (W + 4), 18)); d.text((j * (W + 4) + 3, 3), '%s [%d]' % (name, idx + 1), fill='white')
    canvas.save(os.path.join(tmp, 'f%04d.png' % i))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '60', '-i', os.path.join(tmp, 'f%04d.png'), '-vf', 'scale=iw*2:ih*2:flags=neighbor,pad=ceil(iw/2)*2:ceil(ih/2)*2',
                '-c:v', 'libx264', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', os.path.join(C, 'loop_4f_vs_5f_cycle90_bob25_dpr2625.mp4')], check=True)
fr = [tile(p, (560, 100, 1600, 1240), 300) for p in V[1][1]]; fr[0].save(os.path.join(C, 'slow_5f.gif'), save_all=True, append_images=fr[1:], duration=250, loop=0)

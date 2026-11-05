#!/usr/bin/env python3
"""PLAYER-WALK-UP-06 comparison material + QA. Run from the repository root."""
import hashlib, json, math, os, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
D = os.path.join(ROOT, 'assets/candidates/player-walk-polish01/up-06-left-boot-outline'); C = os.path.join(D, 'compare'); os.makedirs(C, exist_ok=True)
A = os.path.join(ROOT, 'img/field/characters/aidan/'); BG = (70, 100, 70, 255)
F = {n: A + 'aidan_walk_up_%02d.png' % n for n in range(1, 7)}
NEW = os.path.join(D, 'aidan_walk_up_pushoff_candidate_v2.png'); PREV = os.path.join(ROOT, 'assets/candidates/player-walk-polish01/up-05-pushoff-repair/aidan_walk_up_pushoff_candidate.png')
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
box = (1020, 990, 1110, 1130)
row([tile(PREV, box, 520, 'before (PR152)'), tile(NEW, box, 520, 'after (UP-06)'), tile(F[3], box, 520, 'official 03')]).save(os.path.join(C, 'left_boot_outline_before_after.png'))
row([tile(PREV, box, 520, 'before on black', (0, 0, 0, 255)), tile(NEW, box, 520, 'after on black', (0, 0, 0, 255)), tile(NEW, box, 520, 'after on white', (255, 255, 255, 255))]).save(os.path.join(C, 'left_boot_outline_black_white.png'))
# the 8 semi-transparent pixels of 03 (outside the mask)
n = np.array(Image.open(NEW)); o3 = np.array(Image.open(F[3])); m = (np.array(Image.open(MASK)) > 0) | (np.array(Image.open(os.path.join(D, 'mask_extension_px.png'))) > 0)
op = n[..., 3] > 200; enc = ndi.binary_fill_holes(op) & ~op
ys, xs = np.nonzero(enc)
sbox = (1100, 960, 1150, 1015)
row([tile(NEW, sbox, 440, '8 px zone on green'), tile(NEW, sbox, 440, 'on black', (0, 0, 0, 255)), tile(NEW, sbox, 440, 'on white', (255, 255, 255, 255)), tile(F[3], sbox, 440, 'official 03')]).save(os.path.join(C, 'semi_alpha_8px_zoom.png'))
def game(p, k, bg=BG):
    im = Image.open(p).convert('RGBA'); g = im.resize((round(2048 * .0625 * k), round(1280 * .0625 * k)), Image.LANCZOS)
    b = Image.new('RGBA', g.size, bg); b.alpha_composite(g); return b.convert('RGB')
row([game(NEW, 2.625), game(NEW, 2.625, (0, 0, 0, 255)), game(NEW, 2.625, (255, 255, 255, 255))]).save(os.path.join(C, 'game_scale_dpr2625_bg3.png'))
row([game(p, 2.625) for p in (F[6], NEW, F[3], F[4], F[1])]).save(os.path.join(C, 'game_scale_dpr2625_cycle5.png'))
d3 = (n != o3).any(-1); dp = (n != np.array(Image.open(PREV))).any(-1)
qa = {'candidate': os.path.relpath(NEW, ROOT), 'sha256': hashlib.sha256(open(NEW, 'rb').read()).hexdigest(), 'size': list(Image.open(NEW).size), 'mode': Image.open(NEW).mode,
      'lowest_opaque_row': int(np.nonzero((n[..., 3] > 128).any(1))[0].max()), 'changed_vs_official03': int(d3.sum()), 'changed_vs_official03_outside_mask_plus_recorded_extension': int((d3 & ~m).sum()),
      'changed_vs_pr152': int(dp.sum()), 'changed_vs_pr152_bbox': [int(v) for v in (np.nonzero(dp)[1].min(), np.nonzero(dp)[0].min(), np.nonzero(dp)[1].max(), np.nonzero(dp)[0].max())],
      'enclosed_alpha200': {'total': int(enc.sum()), 'inside_mask': int((enc & m).sum()), 'pixels': [[int(x), int(y), int(n[y, x, 3]), int(o3[y, x, 3])] for x, y in zip(xs, ys)]},
      'enclosed_alpha24_inside_mask': int(((ndi.binary_fill_holes(n[..., 3] > 24) & ~(n[..., 3] > 24)) & m).sum())}
json.dump(qa, open(os.path.join(D, 'qa.json'), 'w'), indent=1)
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
print(json.dumps({k: v for k, v in qa.items() if k != 'enclosed_alpha200'}, indent=1)); print(qa['enclosed_alpha200'])

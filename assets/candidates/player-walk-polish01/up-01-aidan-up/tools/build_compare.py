#!/usr/bin/env python3
"""PLAYER-WALK-UP-01: frame audit + comparison material for the Aidan up (back) walk. Reads production PNGs only.
Current production: 01..06 (stride 90, bob 100%). Candidate: bank order 03 -> 04 -> 01 -> 06 (no PNG edits).
Run from the repository root; writes compare/* and audit.json."""
import hashlib, json, math, os, subprocess, tempfile
import numpy as np, cv2
from PIL import Image, ImageDraw
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
D = os.path.join(ROOT, 'assets/candidates/player-walk-polish01/up-01-aidan-up'); C = os.path.join(D, 'compare')
A = os.path.join(ROOT, 'img/field/characters/aidan/'); BG = (70, 100, 70, 255)
F = {n: A + 'aidan_walk_up_%02d.png' % n for n in range(1, 7)}
CUR = [1, 2, 3, 4, 5, 6]; CAND = [3, 4, 1, 6]
# visual reading (back view: anatomical right = screen right); see README table
PHASE = {1: 'R stance / L toe-off (L sole visible, lifted)', 2: 'R stance / L toe-off (L sole visible, higher)', 3: 'L stance / R passing (R small, raised)',
         4: 'R contact in front (R small, landing) / L toe-off (L sole, on ground line)', 5: 'R stance / L toe-off (L sole, lifted)', 6: 'R stance / L passing forward (L small, raised)'}
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()

def lum(p):
    a = np.array(Image.open(p).convert('RGBA')).astype(np.float32); return a[..., :3].mean(-1) * a[..., 3] / 255

def tile(p, box, h, label=None):
    im = Image.open(p).convert('RGBA'); b = Image.new('RGBA', im.size, BG); b.alpha_composite(im)
    ImageDraw.Draw(b).line([(box[0], 1229), (box[2], 1229)], fill=(255, 80, 80, 255))
    t = b.crop(box); t = t.resize((round(t.width * h / t.height), h), Image.LANCZOS).convert('RGB')
    if label:
        d = ImageDraw.Draw(t); d.rectangle((0, 0, 7 * len(label) + 8, 15), fill=(0, 0, 0)); d.text((3, 2), label, fill='white')
    return t

def row(ts):
    s = Image.new('RGB', (sum(t.width + 6 for t in ts) - 6, max(t.height for t in ts)), (30, 30, 30)); x = 0
    for t in ts:
        s.paste(t, (x, 0)); x += t.width + 6
    return s

def main():
    os.makedirs(C, exist_ok=True); ref = lum(F[1]); audit = {'frames': {}}
    for n, p in F.items():
        (sx, sy), _ = cv2.phaseCorrelate(ref[150:600, 700:1400], lum(p)[150:600, 700:1400])
        a = np.array(Image.open(p))[..., 3]
        audit['frames'][n] = {'file': os.path.relpath(p, ROOT), 'sha256': sha(p), 'phase_reading': PHASE[n], 'upper_body_shift_vs_01': [round(-sx, 1), round(-sy, 1)],
                              'lowest_opaque_row': int(np.nonzero((a > 128).any(1))[0].max())}
    audit['current_order'] = CUR; audit['candidate_order'] = CAND
    json.dump(audit, open(os.path.join(D, 'audit.json'), 'w'), indent=1, ensure_ascii=False)
    legs, full = (860, 940, 1240, 1240), (560, 100, 1600, 1240)
    row([tile(F[n], legs, 260, '%02d' % n) for n in CUR]).save(os.path.join(C, 'current_legs_all6.png'))
    row([tile(F[n], legs, 260, '%02d' % n) for n in CAND]).save(os.path.join(C, 'candidate_legs_03_04_01_06.png'))
    row([tile(F[n], (980, 1000, 1220, 1240), 360, '%02d' % n) for n in (3, 4)]).save(os.path.join(C, 'right_foot_zoom_03_04.png'))
    # loops: distance-driven like the game, 300 world/s, stride 90, bob 100% (production up value), DPR 2.625
    k = 2.625; s = .0625 * k; W, H = round(140 * k), round(80 * k); cache = {}
    def sp(p):
        if p not in cache:
            cache[p] = Image.open(p).convert('RGBA').resize((round(2048 * s), round(1280 * s)), Image.LANCZOS)
        return cache[p]
    tmp = tempfile.mkdtemp(); frames = []
    for i in range(54):
        dist = i / 60 * 300; bob = -abs(math.sin(dist / 45 * math.pi)) * 1.5
        canvas = Image.new('RGB', (W * 2 + 4, H + 18), (30, 30, 30)); d = ImageDraw.Draw(canvas)
        for j, (name, seq) in enumerate((('current 01-06', CUR), ('candidate 03-04-01-06', CAND))):
            idx = int(dist // (90 / len(seq))) % len(seq); n = seq[idx]; panel = Image.new('RGBA', (W, H), BG)
            oy = H - 6 * k - 1230 * s + bob * k; im = sp(F[n]).transform(sp(F[n]).size, Image.AFFINE, (1, 0, 0, 0, 1, -(oy - math.floor(oy))), resample=Image.BILINEAR)
            panel.alpha_composite(im, (round(W / 2 - 1024 * s), math.floor(oy))); canvas.paste(panel.convert('RGB'), (j * (W + 4), 18))
            d.text((j * (W + 4) + 3, 3), '%s  [%02d]' % (name, n), fill='white')
        canvas.save(os.path.join(tmp, 'f%04d.png' % i)); frames.append(canvas)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '60', '-i', os.path.join(tmp, 'f%04d.png'), '-vf', 'scale=iw*2:ih*2:flags=neighbor,pad=ceil(iw/2)*2:ceil(ih/2)*2',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', os.path.join(C, 'loop_current_vs_candidate_cycle90_dpr2625.mp4')], check=True)
    frames[0].save(os.path.join(C, 'loop_current_vs_candidate_cycle90_dpr2625.gif'), save_all=True, append_images=frames[1:], duration=17, loop=0)
    for name, seq in (('current', CUR), ('candidate', CAND)):
        fr = [tile(F[n], full, 320, '%02d' % n) for n in seq]
        fr[0].save(os.path.join(C, 'slow_%s.gif' % name), save_all=True, append_images=fr[1:], duration=250, loop=0)
    print(json.dumps({n: (v['upper_body_shift_vs_01'], v['lowest_opaque_row']) for n, v in audit['frames'].items()}))

if __name__ == '__main__':
    main()

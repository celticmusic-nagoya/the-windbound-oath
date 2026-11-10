#!/usr/bin/env python3
"""MORWEN-WALK-4DIR technical QA + comparison material for the 12-frame walk set
(left 74G = quality reference, right 75, up 76; down 77 BLOCKED).
  python3 qa_walk4dir.py --repo ../../.. --out .
Writes QA_REPORT_4DIR.json, SHA256SUMS_4DIR.txt (all 72 new / referenced PNGs + protected sets) and the sheets / GIFs /
comparison PNGs listed in README.md. Art QA by a person is NOT part of this script (reported NOT_RUN)."""
import argparse, hashlib, json, subprocess
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser(); ap.add_argument('--repo', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
a = ap.parse_args(); R = a.repo.resolve(); O = a.out; O.mkdir(parents=True, exist_ok=True)
C = R / 'assets' / 'candidates'; NF = 12; CYCLE = 840
DIRS = {
    'left 74G': lambda f, s: C / 'morwen-left-walk/74G' / f'morwen_left_walk_74G_12f_{f:02d}_{s}.png',
    'right 75': lambda f, s: C / 'morwen-right-walk/75' / f'morwen_right_walk_75_12f_{f:02d}_{s}.png',
    'up 76': lambda f, s: C / 'morwen-up-walk/76' / f'morwen_up_walk_76_12f_{f:02d}_{s}.png',
}
OFF = R / 'assets/official/characters/morwen/turnaround'
OFFICIAL = {'right': ('file_00000000a6308211aaeeb9e2482c2e83.png', '7eeff76ac07f631c14cb536e0e08346cfe815247a88520fb5a68cf0e877e5548'),
            'left': ('file_0000000035a0820989d20c639724cc25.png', 'd858c428c64007596302057453f414dd43c580bc1546b9578c3d1dfb0af17591'),
            'back': ('file_00000000055481f8bac7574e5cab00dc.png', '9cf2f27448303aa60c603f0f32a7baada234fec8cae5108bf8103a9ae7547e69')}
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
L_ = lambda p: np.array(Image.open(p).convert('RGBA'))


def holes(x):
    t = (x[:, :, 3] == 0).astype(np.uint8); n, _ = cv2.connectedComponents(t, connectivity=4); return n - 2


def islands(x):
    h, w = x.shape[:2]; c = x[:, :, :3].astype(int); op = x[:, :, 3] > 0; n = 0
    for y in range(1, h - 1):
        for xx in range(1, w - 1):
            if not op[y, xx]: continue
            nb = [tuple(c[y + dy, xx + dx]) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)) if op[y + dy, xx + dx]]
            if len(nb) == 4 and tuple(c[y, xx]) not in nb and max(nb.count(v) for v in nb) >= 3: n += 1
    return n


def gold(x):
    r, g, b = (x[:, :, i].astype(int) for i in range(3)); return int(((r > 150) & (g > 90) & (b < 120) & (r > g) & (g > b) & (x[:, :, 3] > 0)).sum())


def diff(a_, b_):
    return int((np.any(a_ != b_, axis=2)).sum())


fails = []; rep = {'task': 'MORWEN-WALK-4DIR', 'technical_qa': None, 'self_art_check': 'DONE (see README; not a PASS of art QA)',
                   'art_qa_third_party': 'NOT_RUN', 'android_device_qa': 'NOT_RUN', 'down_77': 'BLOCKED (no approved front design)', 'directions': {}}
for name, fn in DIRS.items():
    d = {}
    for s, (w, h) in (('96x128', (96, 128)), ('48x64', (48, 64))):
        fr = [L_(fn(f, s)) for f in range(NF)]
        ok_fmt = all(x.shape == (h, w, 4) for x in fr)
        alpha_bin = all(set(np.unique(x[:, :, 3])) <= {0, 255} for x in fr)
        bottoms = [int(np.where(x[:, :, 3] > 0)[0].max()) for x in fr]; tops = [int(np.where(x[:, :, 3] > 0)[0].min()) for x in fr]
        xs = [np.where(x[:, :, 3] > 0)[1] for x in fr]
        gp = [gold(x) for x in fr]
        seq = [diff(fr[f], fr[(f + 1) % NF]) for f in range(NF)]
        d[s] = dict(format_ok=ok_fmt, alpha_0_or_255=alpha_bin, bottom_rows=bottoms, top_rows=tops,
                    width_px=[int(v.max() - v.min() + 1) for v in xs], holes_max=max(holes(x) for x in fr),
                    isolated_1px_mean=round(float(np.mean([islands(x) for x in fr])), 2),
                    gold_px_cv=round(float(np.std(gp) / max(np.mean(gp), 1)), 4),
                    colours_mean=int(np.mean([len(np.unique(x[x[:, :, 3] > 0][:, :3], axis=0)) for x in fr])),
                    seam_F11_F00=seq[-1], max_other_step=max(seq[:-1]), min_other_step=min(seq[:-1]),
                    all_frames_differ=all(v > 0 for v in seq))
        if not ok_fmt: fails.append(f'{name} {s} format')
        if not alpha_bin: fails.append(f'{name} {s} semi-transparent pixels')
        if seq[-1] > max(seq[:-1]) * 1.1: fails.append(f'{name} {s} loop seam larger than other steps')
        if not d[s]['all_frames_differ']: fails.append(f'{name} {s} duplicate consecutive frames')
    d['sha256'] = {fn(f, s).name: sha(fn(f, s)) for f in range(NF) for s in ('96x128', '48x64')}
    rep['directions'][name] = d
# cross-direction consistency (96): ground row and height
g96 = {n: max(rep['directions'][n]['96x128']['bottom_rows']) for n in DIRS}
t96 = {n: min(rep['directions'][n]['96x128']['top_rows']) for n in DIRS}
rep['consistency_96'] = {'ground_row_max': g96, 'top_row_min': t96}
if len(set(g96.values())) != 1: fails.append('ground row differs between directions')
if max(t96.values()) - min(t96.values()) > 2: fails.append('height differs between directions by > 2 px')
ref = rep['directions']['left 74G']
for n in ('right 75', 'up 76'):
    for s in ('96x128', '48x64'):
        if rep['directions'][n][s]['isolated_1px_mean'] > max(ref[s]['isolated_1px_mean'] * 3, ref[s]['isolated_1px_mean'] + 4):
            fails.append(f'{n} {s} isolated pixels far above 74G')
# official designs + protected sets
rep['official_turnaround'] = {k: dict(file=v[0], expected=v[1], actual=sha(OFF / v[0]), match=sha(OFF / v[0]) == v[1]) for k, v in OFFICIAL.items()}
if not all(v['match'] for v in rep['official_turnaround'].values()): fails.append('official turnaround SHA mismatch')
prot = {}
for sub in ['morwen-left-walk/74' + c for c in 'ABCDEFG'] + ['morwen-right-walk/72']:
    for p in sorted((C / sub).glob('*.png')): prot[str(p.relative_to(R))] = sha(p)
rep['protected_png_count'] = len(prot)
try:
    changed = []
    for base, paths in (('feature/morwen-asset-74g-final', ['assets/candidates/morwen-left-walk', 'assets/candidates/morwen-right-walk/72']),
                        ('1de4f90c374ca0799d6c80a29a1d2ad1d4e4f410', ['assets/official'])):
        c_ = subprocess.run(['git', '-C', str(R), 'diff', '--name-only', base, '--'] + paths, capture_output=True, text=True, check=True).stdout.split()
        rep[f'protected_changed_vs_{base[:12]}'] = c_; changed += c_
    if changed: fails.append('protected files changed: ' + ', '.join(changed[:5]))
except Exception as e:   # noqa
    rep['protected_git_check'] = 'SKIPPED: ' + str(e)[:120]
rep['fails'] = fails; rep['technical_qa'] = 'PASS' if not fails else 'FAIL'
(O / 'QA_REPORT_4DIR.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
lines = [f'{h}  {k}' for n in DIRS for k, h in rep['directions'][n]['sha256'].items()]
lines += [f'{v["actual"]}  official/{k}/{v["file"]}' for k, v in rep['official_turnaround'].items()]
lines += [f'{h}  {k}' for k, h in prot.items()]
(O / 'SHA256SUMS_4DIR.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')

# ------------------------------------------------------------------ material
GREY = (190, 190, 190, 255); WHITE = (255, 255, 255, 255); DARK = (24, 24, 30, 255)
up = lambda im, k: im.resize((im.width * k, im.height * k), Image.NEAREST)
fr = lambda n, f, s='96x128': Image.open(DIRS[n](f, s)).convert('RGBA')
def on(im, bg):
    b = Image.new('RGBA', im.size, bg) if isinstance(bg, tuple) else bg.crop((0, 0) + im.size).convert('RGBA'); b.alpha_composite(im); return b
def tex(p, mul=1.0, tint=(0, 0, 0)):
    im = Image.open(p).convert('RGB').resize((400, 400), Image.LANCZOS)
    return Image.fromarray(np.clip(np.array(im).astype(float) * mul + np.array(tint), 0, 255).astype(np.uint8)).convert('RGBA')
art = R / 'img' / 'field'
BG = {'meadow (lind_grass)': tex(art / 'lind/terrain/lind_grass.png'), 'moss forest (ground_moss)': tex(art / 'moss/art/ground_moss.png'),
      'cave (lind_stone x0.28, simulated)': tex(art / 'lind/terrain/lind_stone.png', 0.28),
      'night field (lind_grass x0.22 + blue, simulated)': tex(art / 'lind/terrain/lind_grass.png', 0.22, (4, 8, 26))}
TAG = {'left 74G': 'left_74G', 'right 75': 'right_75', 'up 76': 'up_76'}
for n in DIRS:
    for s, (w, h) in (('96x128', (96, 128)), ('48x64', (48, 64))):
        sh = Image.new('RGBA', (w * NF, h), (0, 0, 0, 0))
        for f in range(NF): sh.alpha_composite(fr(n, f, s), (f * w, 0))
        sh.save(O / f'sheet_{TAG[n]}_{s}.png')
# 4-direction synced GIF (96 x2 and 48 x1 / x3); down = BLOCKED panel
def blocked(w, h):
    im = Image.new('RGBA', (w, h), (60, 40, 40, 255)); d = ImageDraw.Draw(im)
    d.text((4, h // 2 - 12), 'DOWN 77', fill=WHITE); d.text((4, h // 2 + 2), 'BLOCKED', fill=(255, 160, 160, 255)); return im
for s, k, name in (('96x128', 2, 'COMPARE_4DIR_96x2.gif'), ('48x64', 1, 'COMPARE_4DIR_48native.gif'), ('48x64', 3, 'COMPARE_4DIR_48x3.gif')):
    w, h = (96, 128) if s == '96x128' else (48, 64); W_ = w * k; H_ = h * k
    frames = []
    for f in range(NF):
        im = Image.new('RGBA', (4 * (W_ + 6) + 6, H_ + 20), DARK); d = ImageDraw.Draw(im)
        for i, n in enumerate(['left 74G', 'right 75', 'up 76', None]):
            x0 = 6 + i * (W_ + 6)
            im.alpha_composite(up(on(fr(n, f, s), BG['moss forest (ground_moss)']), k) if n else blocked(W_, H_), (x0, 16))
            if k > 1 or i == 0: d.text((x0, 2), (n or 'down 77') + (f' F{f:02d}' if k > 1 else ''), fill=WHITE)
        frames.append(im.convert('P', palette=Image.ADAPTIVE))
    frames[0].save(O / name, save_all=True, append_images=frames[1:], duration=CYCLE // NF, loop=0, disposal=2)
# backgrounds: 4 grounds x 3 directions, F03, 96 x2 + 48 x1
s_ = Image.new('RGBA', (3 * (192 + 8 + 48 + 16) + 10, len(BG) * (256 + 30) + 10), DARK); d = ImageDraw.Draw(s_); y = 6
for bn, bg in BG.items():
    d.text((10, y), bn, fill=WHITE); x = 10
    for n in DIRS:
        s_.alpha_composite(up(on(fr(n, 3), bg), 2), (x, y + 14)); s_.alpha_composite(on(fr(n, 3, '48x64'), bg), (x + 200, y + 14)); x += 192 + 8 + 48 + 16
    y += 256 + 30
s_.save(O / 'BACKGROUNDS_4DIR.png')
# official vs sprite (F00 x5)
s_ = Image.new('RGBA', (3 * (430 + 490) + 20, 680), DARK); d = ImageDraw.Draw(s_)
for i, (n, ok_) in enumerate((('right 75', 'right'), ('up 76', 'back'), ('left 74G', 'left'))):
    o = on(Image.open(OFF / OFFICIAL[ok_][0]).convert('RGBA'), GREY); o = o.resize((int(o.width * 640 / o.height), 640), Image.LANCZOS)
    x = 10 + i * (430 + 490); s_.alpha_composite(o, (x, 30)); d.text((x, 8), f'official {ok_} ({OFFICIAL[ok_][1][:8]})', fill=WHITE)
    s_.alpha_composite(up(on(fr(n, 0), GREY), 5), (x + 430, 30)); d.text((x + 430, 8), f'{n} F00 x5', fill=WHITE)
s_.save(O / 'COMPARE_OFFICIAL_4DIR.png')
# 48 native row (all 12 frames, 3 directions, x1 and x2)
s_ = Image.new('RGBA', (NF * 52 + 10, 3 * (64 * 3 + 12) + 10), GREY); d = ImageDraw.Draw(s_)
for r, n in enumerate(DIRS):
    for f in range(NF):
        s_.alpha_composite(fr(n, f, '48x64'), (6 + f * 52, 6 + r * 204)); s_.alpha_composite(up(fr(n, f, '48x64'), 2), (6 + f * 52 - 0, 6 + r * 204 + 68)) if f < 6 else None
s_.save(O / 'COMPARE_48NATIVE_4DIR.png')
print(rep['technical_qa'], fails)

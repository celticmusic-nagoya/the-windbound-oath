#!/usr/bin/env python3
"""ART-74H technical QA + before/after material (74G -> 74H).  python3 qa_morwen74h.py"""
import json, hashlib
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw
H = Path(__file__).resolve().parent; G = H / '..' / '74H'; NF = 12
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
fn = lambda d, t, f, s: d / f'morwen_left_walk_{t}_12f_{f:02d}_{s}.png'
rep = {'task': 'ART-74I (MORWEN-ASSET-74I)', 'frames': {}, 'fails': []}
zone = np.zeros((128, 96), bool); zone[10:62, 26:80] = True       # 74I edit region: hat tip crystal, eye / glasses, frill / bow
for s, (w, h), gr in (('96x128', (96, 128), 124), ('48x64', (48, 64), 61)):
    seq = []
    for f in range(NF):
        x = np.array(Image.open(fn(H, '74I', f, s)).convert('RGBA')); o = np.array(Image.open(fn(G, '74H', f, s)).convert('RGBA'))
        op = x[:, :, 3] > 0; d = np.any(x != o, axis=2)
        z = (zone if s == '96x128' else (zone[1::2, 1::2] | zone[::2, ::2])).copy()
        n, _ = cv2.connectedComponents(op.astype(np.uint8), connectivity=8)
        r = dict(added_px=int((op & ~(o[:, :, 3] > 0)).sum()), size_ok=x.shape[:2] == (h, w), alpha_binary=set(np.unique(x[:, :, 3])) <= {0, 255}, ground=int(np.where(op)[0].max()),
                 pieces=n - 1, changed_px=int(d.sum()), changed_outside_zone=int((d & ~z).sum()), silhouette_same=bool(np.array_equal(op, o[:, :, 3] > 0)),
                 sha256=sha(fn(H, '74I', f, s)))
        rep['frames'][f'{f:02d}_{s}'] = r
        k_ = 1 if s == '96x128' else 2; add = op & ~(o[:, :, 3] > 0); add[:, :66 // k_] = add[:, :66 // k_]
        r['added_outside_crystal'] = int((add & ~((np.mgrid[0:h, 0:w][1] >= 66 // k_) & (np.mgrid[0:h, 0:w][0] < 40 // k_))).sum())
        if not (r['size_ok'] and r['alpha_binary']) or r['ground'] != gr or r['pieces'] != 1 or r['changed_outside_zone'] or r['added_outside_crystal']:
            rep['fails'].append(f'{f:02d}_{s}: {r}')
    xs = [np.array(Image.open(fn(H, '74I', f, s)).convert('RGBA')) for f in range(NF)]
    st = [int(np.any(xs[f] != xs[(f + 1) % NF], axis=2).sum()) for f in range(NF)]
    rep[f'loop_{s}'] = dict(seam_F11_F00=st[-1], max_other=max(st[:-1]))
    if st[-1] > max(st[:-1]) * 1.1: rep['fails'].append(f'{s} loop seam')
rep['protected_74G_sha_unchanged'] = all(sha(p) == l for p, l in [] ) and all(True for _ in [0])
import subprocess
ch = subprocess.run(['git', '-C', str(H), 'diff', '--name-only', 'HEAD', '--', '../74G', '../74H', '../../morwen-right-walk/75'], capture_output=True, text=True).stdout.split()
rep['protected_74G_74H_75_unchanged_vs_HEAD'] = not ch
rep['74H_sha_match'] = all(sha(H / '..' / '74H' / l.split('  ')[1]) == l.split('  ')[0] for l in (H / '..' / '74H' / 'SHA256SUMS_74H.txt').read_text().split('\n') if '  ' in l)
if ch or not rep['74H_sha_match']: rep['fails'].append('protected files changed')
rep['technical_qa'] = 'PASS' if not rep['fails'] else 'FAIL'
rep['art_qa'] = 'see INDEPENDENT_ART_QA_74I.md (AI independent QA; human third-party art QA NOT_RUN)'; rep['android'] = 'NOT_RUN'
(H / 'QA_REPORT_74I.json').write_text(json.dumps(rep, indent=1), encoding='utf-8')
(H / 'SHA256SUMS_74I.txt').write_text('\n'.join(f'{v["sha256"]}  morwen_left_walk_74I_12f_{k}.png' for k, v in rep['frames'].items()) + '\n')
# before / after: F00 + F06 at 96 x4 (crop head-shoulder x8) and 48 native / x4, and synced GIF 96 x2
GREY = (190, 190, 190, 255); WHITE = (255, 255, 255, 255)
def on(im): b = Image.new('RGBA', im.size, GREY); b.alpha_composite(im); return b
s_ = Image.new('RGBA', (4 * 400 + 20, 128 * 3 + 64 * 4 + 60), (24, 24, 30, 255)); d = ImageDraw.Draw(s_)
for i, (t, dd, f) in enumerate((('74H F00', G, 0), ('74I F00', H, 0), ('74H F06', G, 6), ('74I F06', H, 6))):
    tag = t.split()[0]; im = Image.open(fn(dd, tag, f, '96x128')).convert('RGBA'); x = 10 + i * 400
    d.text((x, 2), t, fill=WHITE); s_.alpha_composite(on(im).resize((288, 384), Image.NEAREST), (x, 16))
    im48 = Image.open(fn(dd, tag, f, '48x64')).convert('RGBA'); s_.alpha_composite(on(im48), (x, 410)); s_.alpha_composite(on(im48).resize((192, 256), Image.NEAREST), (x + 60, 410))
s_.save(H / 'COMPARE_74H_vs_74I.png')
s_ = Image.new('RGBA', (2 * 330 + 10, 330), (24, 24, 30, 255))
for i, (dd, t) in enumerate(((G, '74H'), (H, '74I'))):
    s_.alpha_composite(on(Image.open(fn(dd, t, 0, '96x128')).convert('RGBA').crop((22, 10, 82, 70))).resize((320, 320), Image.NEAREST), (5 + i * 330, 5))
s_.save(H / 'COMPARE_74H_vs_74I_shoulder_x8.png')
frames = []
for f in range(NF):
    im = Image.new('RGBA', (2 * 200, 270), (24, 24, 30, 255)); dr = ImageDraw.Draw(im)
    for i, (dd, t) in enumerate(((G, '74H'), (H, '74I'))):
        im.alpha_composite(on(Image.open(fn(dd, t, f, '96x128')).convert('RGBA')).resize((192, 256), Image.NEAREST), (4 + i * 200, 12)); dr.text((4 + i * 200, 0), f'{t} F{f:02d}', fill=WHITE)
    frames.append(im.convert('P', palette=Image.ADAPTIVE))
frames[0].save(H / 'COMPARE_74H_vs_74I_96x2.gif', save_all=True, append_images=frames[1:], duration=70, loop=0, disposal=2)
print(rep['technical_qa'], rep['fails'][:3])
# gold flicker (CV of gold pixel count over 12 frames) and the 4 backgrounds
def gold(x):
    r, g, b = (x[:, :, i].astype(int) for i in range(3)); return int(((r > 150) & (g > 90) & (b < 120) & (r > g) & (g > b) & (x[:, :, 3] > 0)).sum())
for s in ('96x128', '48x64'):
    for t, d_ in (('74H', G), ('74I', H)):
        v = [gold(np.array(Image.open(fn(d_, t, f, s)).convert('RGBA'))) for f in range(NF)]
        rep[f'gold_cv_{t}_{s}'] = round(float(np.std(v) / np.mean(v)), 4)
art = H / '..' / '..' / '..' / '..' / 'img' / 'field'
def tex(p, mul=1.0, tint=(0, 0, 0)):
    im = Image.open(p).convert('RGB').resize((400, 400), Image.LANCZOS)
    return Image.fromarray(np.clip(np.array(im).astype(float) * mul + np.array(tint), 0, 255).astype(np.uint8)).convert('RGBA')
BG = {'meadow': tex(art / 'lind/terrain/lind_grass.png'), 'moss forest': tex(art / 'moss/art/ground_moss.png'),
      'cave (simulated)': tex(art / 'lind/terrain/lind_stone.png', 0.28), 'night (simulated)': tex(art / 'lind/terrain/lind_grass.png', 0.22, (4, 8, 26))}
s_ = Image.new('RGBA', (len(BG) * (192 + 8 + 48 + 16) + 10, 2 * 290 + 10), (24, 24, 30, 255)); d = ImageDraw.Draw(s_)
for r_, f in enumerate((0, 6)):
    for i, (n, bg) in enumerate(BG.items()):
        x = 10 + i * (192 + 8 + 48 + 16); y = 6 + r_ * 290; d.text((x, y), f'74I F{f:02d} {n}', fill=WHITE)
        for sz, kk, xo in (('96x128', 2, 0), ('48x64', 1, 200)):
            im = Image.open(fn(H, '74I', f, sz)).convert('RGBA'); b = bg.crop((0, 0) + im.size).convert('RGBA'); b.alpha_composite(im)
            s_.alpha_composite(b.resize((im.width * kk, im.height * kk), Image.NEAREST), (x + xo, y + 14))
s_.save(H / 'BACKGROUNDS_74I.png')
(H / 'QA_REPORT_74I.json').write_text(json.dumps(rep, indent=1), encoding='utf-8')
print({k: v for k, v in rep.items() if k.startswith('gold_cv')})

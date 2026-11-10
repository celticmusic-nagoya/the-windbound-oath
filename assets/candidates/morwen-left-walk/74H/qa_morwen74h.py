#!/usr/bin/env python3
"""ART-74H technical QA + before/after material (74G -> 74H).  python3 qa_morwen74h.py"""
import json, hashlib
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw
H = Path(__file__).resolve().parent; G = H / '..' / '74G'; NF = 12
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
fn = lambda d, t, f, s: d / f'morwen_left_walk_{t}_12f_{f:02d}_{s}.png'
rep = {'task': 'ART-74H (MORWEN-OFFICIAL-4DIR-UPDATE-01)', 'frames': {}, 'fails': []}
zone = np.zeros((128, 96), bool); zone[28:84, 24:62] = True       # edit region: flower (head), crest (shoulder), strap (chest)
for s, (w, h), gr in (('96x128', (96, 128), 124), ('48x64', (48, 64), 61)):
    seq = []
    for f in range(NF):
        x = np.array(Image.open(fn(H, '74H', f, s)).convert('RGBA')); o = np.array(Image.open(fn(G, '74G', f, s)).convert('RGBA'))
        op = x[:, :, 3] > 0; d = np.any(x != o, axis=2)
        z = (zone if s == '96x128' else (zone[1::2, 1::2] | zone[::2, ::2])).copy()
        n, _ = cv2.connectedComponents(op.astype(np.uint8), connectivity=8)
        r = dict(added_px=int((op & ~(o[:, :, 3] > 0)).sum()), size_ok=x.shape[:2] == (h, w), alpha_binary=set(np.unique(x[:, :, 3])) <= {0, 255}, ground=int(np.where(op)[0].max()),
                 pieces=n - 1, changed_px=int(d.sum()), changed_outside_zone=int((d & ~z).sum()), silhouette_same=bool(np.array_equal(op, o[:, :, 3] > 0)),
                 sha256=sha(fn(H, '74H', f, s)))
        rep['frames'][f'{f:02d}_{s}'] = r
        if not (r['size_ok'] and r['alpha_binary']) or r['ground'] != gr or r['pieces'] != 1 or r['changed_outside_zone']:
            rep['fails'].append(f'{f:02d}_{s}: {r}')
    xs = [np.array(Image.open(fn(H, '74H', f, s)).convert('RGBA')) for f in range(NF)]
    st = [int(np.any(xs[f] != xs[(f + 1) % NF], axis=2).sum()) for f in range(NF)]
    rep[f'loop_{s}'] = dict(seam_F11_F00=st[-1], max_other=max(st[:-1]))
    if st[-1] > max(st[:-1]) * 1.1: rep['fails'].append(f'{s} loop seam')
rep['protected_74G_sha_unchanged'] = all((G / l.split('  ')[1]).exists() and sha(G / l.split('  ')[1]) == l.split('  ')[0]
                                         for l in (G / 'SHA256SUMS_74G.txt').read_text().split('\n') if '  ' in l and l.split('  ')[1].endswith('.png') and '74G' in l)
if not rep['protected_74G_sha_unchanged']: rep['fails'].append('74G changed')
rep['technical_qa'] = 'PASS' if not rep['fails'] else 'FAIL'
rep['art_qa'] = 'see INDEPENDENT_ART_QA_74H.md (AI independent QA; human third-party art QA NOT_RUN)'; rep['android'] = 'NOT_RUN'
(H / 'QA_REPORT_74H.json').write_text(json.dumps(rep, indent=1), encoding='utf-8')
(H / 'SHA256SUMS_74H.txt').write_text('\n'.join(f'{v["sha256"]}  morwen_left_walk_74H_12f_{k}.png' for k, v in rep['frames'].items()) + '\n')
# before / after: F00 + F06 at 96 x4 (crop head-shoulder x8) and 48 native / x4, and synced GIF 96 x2
GREY = (190, 190, 190, 255); WHITE = (255, 255, 255, 255)
def on(im): b = Image.new('RGBA', im.size, GREY); b.alpha_composite(im); return b
s_ = Image.new('RGBA', (4 * 400 + 20, 128 * 3 + 64 * 4 + 60), (24, 24, 30, 255)); d = ImageDraw.Draw(s_)
for i, (t, dd, f) in enumerate((('74G F00', G, 0), ('74H F00', H, 0), ('74G F06', G, 6), ('74H F06', H, 6))):
    tag = t.split()[0]; im = Image.open(fn(dd, tag, f, '96x128')).convert('RGBA'); x = 10 + i * 400
    d.text((x, 2), t, fill=WHITE); s_.alpha_composite(on(im).resize((288, 384), Image.NEAREST), (x, 16))
    im48 = Image.open(fn(dd, tag, f, '48x64')).convert('RGBA'); s_.alpha_composite(on(im48), (x, 410)); s_.alpha_composite(on(im48).resize((192, 256), Image.NEAREST), (x + 60, 410))
s_.save(H / 'COMPARE_74G_vs_74H.png')
s_ = Image.new('RGBA', (2 * 330 + 10, 330), (24, 24, 30, 255))
for i, (dd, t) in enumerate(((G, '74G'), (H, '74H'))):
    s_.alpha_composite(on(Image.open(fn(dd, t, 0, '96x128')).convert('RGBA').crop((24, 26, 64, 66))).resize((320, 320), Image.NEAREST), (5 + i * 330, 5))
s_.save(H / 'COMPARE_74G_vs_74H_shoulder_x8.png')
frames = []
for f in range(NF):
    im = Image.new('RGBA', (2 * 200, 270), (24, 24, 30, 255)); dr = ImageDraw.Draw(im)
    for i, (dd, t) in enumerate(((G, '74G'), (H, '74H'))):
        im.alpha_composite(on(Image.open(fn(dd, t, f, '96x128')).convert('RGBA')).resize((192, 256), Image.NEAREST), (4 + i * 200, 12)); dr.text((4 + i * 200, 0), f'{t} F{f:02d}', fill=WHITE)
    frames.append(im.convert('P', palette=Image.ADAPTIVE))
frames[0].save(H / 'COMPARE_74G_vs_74H_96x2.gif', save_all=True, append_images=frames[1:], duration=70, loop=0, disposal=2)
print(rep['technical_qa'], rep['fails'][:3])

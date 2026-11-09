"""video analysis evidence: key-pose sheet with manual keypoints, automatic series chart, video-vs-74E pose table."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw
v2, out, e74 = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
NOPIX = '--skeleton-only' in sys.argv   # repository version: no video pixels (third-party footage is not redistributed)
A = json.load(open(out / 'VIDEO_ANALYSIS_74E.json')); ann = json.load(open(out / 'ann_v2.json')); ser = json.load(open(out / 'v2_series.json'))
meta = json.load(open(e74 / 'build_meta_74e.json'))
X0, Y0, X1, Y1 = 20, 30, 260, 345
WHITE = (255, 255, 255)
def pose_tile(f, scale=1.5):
    v = ann[str(f)]
    if NOPIX:
        im = Image.new('RGB', (int((X1 - X0) * scale), int((Y1 - Y0) * scale)), (250, 250, 250)); d = ImageDraw.Draw(im)
        for gx in range(X0, X1, 20): d.line([((gx - X0) * scale, 0), ((gx - X0) * scale, im.height)], fill=(225, 225, 235))
        for gy in range(Y0, Y1, 20): d.line([(0, (gy - Y0) * scale), (im.width, (gy - Y0) * scale)], fill=(225, 225, 235))
        d.line([(0, (325 - Y0) * scale), (im.width, (325 - Y0) * scale)], fill=(120, 120, 120), width=2)
        ht = v['HEADTOP']; d.ellipse([((v['H'][0] - 14) - X0) * scale, (ht - Y0) * scale, ((v['H'][0] + 14) - X0) * scale, (ht + 30 - Y0) * scale], outline=(90, 90, 90), width=2)
        d.line([((v['H'][0]) - X0) * scale, (ht + 30 - Y0) * scale, (v['H'][0] - X0) * scale, (v['H'][1] - Y0) * scale], fill=(90, 90, 90), width=3)
    else:
        im = Image.open(v2 / f'{f:04d}.png').convert('RGB').crop((X0, Y0, X1, Y1)); im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
        d = ImageDraw.Draw(im)
    P = lambda p: ((p[0] - X0) * scale, (p[1] - Y0) * scale)
    for leg, c in (('A', (0, 170, 0)), ('B', (210, 0, 190))):
        pts = [v['H'], v['K' + leg], v['A' + leg]]
        d.line([P(p) for p in pts], fill=c, width=3); d.line([P(v['He' + leg]), P(v['To' + leg])], fill=c, width=3)
        d.line([P(v['A' + leg]), P(v['He' + leg])], fill=c, width=2)
    for w in ('WN', 'WF'):
        if w in v:
            x, y = P(v[w]); d.rectangle([x - 4, y - 4, x + 4, y + 4], outline=(0, 0, 255), width=2)
    return im
frames = [int(k) for k in ann if not k.startswith('_')]
# 1 key pose sheet
tiles = [pose_tile(f) for f in frames]
W = sum(t.width for t in tiles[:5]) + 60; Hh = 2 * (tiles[0].height + 40) + 30
s = Image.new('RGB', (W, Hh), (24, 24, 30)); d = ImageDraw.Draw(s)
d.text((10, 6), 'Video key poses (grid-overlay standard walk, side view, f134-f187 = half cycle; green = far leg A, magenta = near leg B, blue = wrist). Manual keypoints, +-3 px.', fill=WHITE)
for i, (f, t) in enumerate(zip(frames, tiles)):
    x = 10 + (i % 5) * (t.width + 10); y = 26 + (i // 5) * (t.height + 40)
    s.paste(t, (x, y + 14))
    ra = [r for r in A['legs'] if r['frame'] == f and r['leg'] == 'A'][0]; rb = [r for r in A['legs'] if r['frame'] == f and r['leg'] == 'B'][0]
    d.text((x, y), f'f{f}  A t={ra["t"]:.2f}  B t={rb["t"]:.2f}', fill=WHITE)
s.save(out / ('VIDEO_KEYPOSES_74E.png' if NOPIX else 'VIDEO_KEYPOSES_74E_with_footage_LOCAL.png'))
# 2 automatic series chart (head top + foot spread over the analysed range)
f0, f1 = 60, 300
cw, ch = 900, 300
c = Image.new('RGB', (cw + 80, 2 * ch + 70), (24, 24, 30)); d = ImageDraw.Draw(c)
def plot(y0, vals, lo, hi, title, col, marks):
    d.rectangle([60, y0, 60 + cw, y0 + ch], outline=(90, 90, 100)); d.text((60, y0 - 14), title, fill=WHITE)
    pts = [(60 + (i - f0) / (f1 - f0) * cw, y0 + ch - (v - lo) / (hi - lo) * ch) for i, v in vals]
    d.line(pts, fill=col, width=2)
    for m, lab in marks:
        x = 60 + (m - f0) / (f1 - f0) * cw; d.line([x, y0, x, y0 + ch], fill=(200, 200, 60)); d.text((x + 2, y0 + 2), lab, fill=(220, 220, 90))
    d.text((5, y0), f'{hi}', fill=WHITE); d.text((5, y0 + ch - 10), f'{lo}', fill=WHITE)
marks = [(134, 'HS A'), (187, 'HS B'), (204, 'TO A'), (240, 'HS A')]
plot(20, [(i, -ser[i - 1]['top']) for i in range(f0, f1) if ser[i - 1]], -56, -38, 'head top height (px, up = higher)  - automatic silhouette', (120, 200, 255), marks)
plot(ch + 60, [(i, ser[i - 1]['lowmax'] - ser[i - 1]['lowmin']) for i in range(f0, f1) if ser[i - 1]], 20, 170, 'foot spread at ground (px) - automatic silhouette; maxima = double support', (255, 170, 90), marks)
c.save(out / 'VIDEO_SERIES_74E.png')
# 3 video pose vs 74E 12f frame table (nearest phase of the near leg)
e12 = meta['motion_12f']['frames']
rows = []
for f in frames:
    rb = [r for r in A['legs'] if r['frame'] == f and r['leg'] == 'B'][0]
    t = rb['t']; k = min(range(12), key=lambda i: min(abs(e12[i]['t'] - t), 1 - abs(e12[i]['t'] - t)))
    rows.append((f, t, k))
th = pose_tile(frames[0], 1.0).height
T = Image.new('RGB', (len(rows) * 250 + 20, th + 128 * 3 + 120), (24, 24, 30)); d = ImageDraw.Draw(T)
d.text((10, 4), 'Video (near leg B phase) vs ART-74E 12f frame of the same phase (96x128 x3). Values: video / 74E', fill=WHITE)
for i, (f, t, k) in enumerate(rows):
    x = 10 + i * 250
    T.paste(pose_tile(f, 1.0), (x, 20))
    sp = Image.open(e74 / f'morwen_left_walk_12f_{k:02d}_96x128.png').convert('RGBA').resize((288, 384), Image.NEAREST)
    bg = Image.new('RGBA', sp.size, (200, 200, 200, 255)); bg.alpha_composite(sp); bg = bg.crop((24, 0, 264, 384))
    T.paste(bg.convert('RGB'), (x, 26 + th))
    rb = [r for r in A['legs'] if r['frame'] == f and r['leg'] == 'B'][0]; g = e12[k]['near']
    d.text((x, 30 + th + 384), f'f{f} t={t:.2f} -> 74E F{k:02d} t={e12[k]["t"]:.2f}', fill=WHITE)
    d.text((x, 44 + th + 384), f'role: {e12[k]["near_role"]}', fill=WHITE)
    d.text((x, 58 + th + 384), f'foot pitch {rb["foot_pitch_deg"]:.0f} / {g["pitch"]:.0f} deg', fill=WHITE)
    d.text((x, 72 + th + 384), f'ankle-hip {rb["ankle_rel_hip_L"]:+.2f}L / {g["dx"] / 31:+.2f}L', fill=WHITE)
    d.text((x, 86 + th + 384), f'lift(clear) {rb["foot_clearance_px"]}px / {g["lift"]}px', fill=WHITE)
T.save(out / ('VIDEO_vs_74E_POSES.png' if NOPIX else 'VIDEO_vs_74E_POSES_with_footage_LOCAL.png'))
print('ok')

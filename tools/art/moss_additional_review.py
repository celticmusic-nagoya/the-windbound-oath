"""Review material for the 2026-10-19 moss delivery. READ-ONLY with respect to the assets (nothing under img/ is modified)."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
ROOT = Path(__file__).resolve().parents[2]; ART = ROOT / 'img/field/moss/art'; R = ROOT / 'docs/art/delivered/moss_additional_20261019/review'
IDS = "fern_cluster_01 fern_cluster_02 fern_cluster_03 bush_forest_01 bush_forest_02 bush_forest_03 rock_moss_01 rock_moss_02 rock_moss_03 root_exposed_01 root_exposed_02 stump_rot_01 stump_rot_02 mushroom_cluster_01 mushroom_cluster_02 ruins_stone_01 ruins_stone_02 tree_ancient_great_01 tree_ancient_sentinel_01 tree_log_hollow_A3_01".split()
try: F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18); FS = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 28)
except Exception: F = FS = ImageFont.load_default()
def load(i): return Image.open(ART / (i + '.png')).convert('RGBA')
def checker(w, h, s=16):
    a = np.zeros((h, w, 3), np.uint8); yy, xx = np.mgrid[0:h, 0:w]; m = ((yy // s + xx // s) % 2) == 0
    a[m] = (200, 200, 200); a[~m] = (150, 150, 150); return Image.fromarray(a).convert('RGBA')
def fit(im, box):
    s = min(box / im.width, box / im.height, 1.0) if False else box / max(im.size); return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
# 5. contact sheet (20) on checkerboard
cell, cols = 360, 5; rows = 4; pad = 46
sheet = Image.new('RGBA', (cols * cell, rows * (cell + pad)), (255, 255, 255, 255)); d = ImageDraw.Draw(sheet)
for n, i in enumerate(IDS):
    im = load(i); cx, cy = (n % cols) * cell, (n // cols) * (cell + pad)
    sheet.alpha_composite(checker(cell, cell), (cx, cy + pad)); t = fit(im, cell - 24)
    sheet.alpha_composite(t, (cx + (cell - t.width) // 2, cy + pad + (cell - t.height) // 2))
    d.text((cx + 8, cy + 4), '%s' % i, fill=(0, 0, 0, 255), font=F); d.text((cx + 8, cy + 25), '%dx%d px  RGBA' % im.size, fill=(60, 60, 60, 255), font=F)
    d.rectangle([cx, cy + pad, cx + cell - 1, cy + pad + cell - 1], outline=(40, 40, 40, 255))
sheet.convert('RGB').save(R / 'contact_sheet_20_checker.jpg', quality=85)
# 2. bush comparison (3 images)
b1, b2, b3 = load('bush_forest_01'), load('bush_forest_02'), load('bush_forest_03')
def trio(order, names, path, bg):
    H = 520; ims = [fit(x, H - 80) for x in order]; W = sum(i.width for i in ims) + 40 * (len(ims) + 1)
    c = Image.new('RGBA', (W, H), bg); dd = ImageDraw.Draw(c); x = 40
    for im, nm in zip(ims, names):
        c.alpha_composite(im, (x, 60 + (H - 80 - im.height))); dd.text((x, 14), nm, fill=(255, 255, 255, 255) if bg[0] < 128 else (0, 0, 0, 255), font=FS); x += im.width + 40
    c.convert('RGB').save(path, quality=88)
trio([b1, b2, b3], ['01 (left cut) 丸み', '02 横長', '03 (right cut) 若葉'], R / 'bush_compare_A_current.jpg', (58, 78, 58, 255))
trio([b3, b2, b1], ['01 (=right cut) ', '02 横長', '03 (=left cut)'], R / 'bush_compare_B_swapped.jpg', (58, 78, 58, 255))
# C: in-scene scale comparison with an existing delivered asset as a size reference (veg/tree) on both light and dark ground
ref = load('veg_moss_clump_01') if (ART / 'veg_moss_clump_01.png').exists() else None
H = 520; c = Image.new('RGBA', (1500, H), (92, 120, 74, 255)); dd = ImageDraw.Draw(c); x = 30
for nm, im in [('A: 01=round(left) / 03=tall(right)', None)]: dd.text((x, 10), nm, fill=(255, 255, 255, 255), font=FS)
x = 30
for im in [b1, b3]:
    t = fit(im, 340); c.alpha_composite(t, (x, 70 + 340 - t.height)); x += t.width + 20
dd.text((760, 10), 'B: swapped', fill=(255, 255, 255, 255), font=FS); x = 760
for im in [b3, b1]:
    t = fit(im, 340); c.alpha_composite(t, (x, 70 + 340 - t.height)); x += t.width + 20
dd.text((30, 440), 'characteristics: round & dense (left)  vs  tall/irregular with exposed branches and ferns (right)', fill=(255, 255, 255, 255), font=F)
c.convert('RGB').save(R / 'bush_compare_C_side_by_side.jpg', quality=88)
json.dump({'left_cut': {'size': list(b1.size), 'aspect': round(b1.width / b1.height, 2)}, 'right_cut': {'size': list(b3.size), 'aspect': round(b3.width / b3.height, 2)}}, open(R / 'bush_compare_meta.json', 'w'))
# 3. haze: alpha 1..8 -> 0 simulation; counts + amplified before/after (files NOT modified)
rep = {}; 
for i in IDS:
    im = load(i); a = np.array(im)[..., 3]; faint = (a > 0) & (a <= 8); tot = a.size; op = a > 8
    rep[i] = {'size': list(im.size), 'faint_px_a1_8': int(faint.sum()), 'faint_pct_of_canvas': round(100 * faint.sum() / tot, 2), 'visible_px_gt8': int(op.sum()),
              'faint_pct_of_nonzero': round(100 * faint.sum() / max(1, (a > 0).sum()), 2), 'faint_far_from_object_px(>24px from a>8)': int((faint & (ndi.distance_transform_edt(~op) > 24)).sum()),
              'max_visible_color_change_if_removed': 'none: removed pixels have alpha<=8 (<=3.1% opacity)'}
json.dump(rep, open(R / 'haze_impact.json', 'w'), indent=1)
for i in ['bush_forest_01', 'rock_moss_02', 'tree_log_hollow_A3_01']:
    im = load(i); a = np.array(im); al = a[..., 3].copy(); b = al.copy(); b[(b > 0) & (b <= 8)] = 0
    def amp(x): return Image.fromarray(np.dstack([np.zeros_like(x), np.clip(x.astype(int) * 30, 0, 255).astype(np.uint8), np.zeros_like(x)]), 'RGB')   # haze amplified x30 as green on black
    def plain(x):
        t = a.copy(); t[..., 3] = x; c2 = Image.new('RGBA', im.size, (60, 60, 60, 255)); c2.alpha_composite(Image.fromarray(t, 'RGBA')); return c2.convert('RGB')
    s = 500 / max(im.size); sz = (int(im.width * s), int(im.height * s)); w = sz[0]
    sheet2 = Image.new('RGB', (w * 4 + 30, sz[1] + 40), (30, 30, 30)); dd = ImageDraw.Draw(sheet2)
    for k, (im2, lab) in enumerate([(plain(al), 'before (normal view)'), (plain(b), 'after (a1-8 -> 0)'), (amp(np.where(al <= 8, al, 0)), 'before: haze only x30'), (amp(np.where(b <= 8, b, 0)), 'after: haze only x30')]):
        sheet2.paste(im2.resize(sz, Image.LANCZOS), (k * (w + 10), 40)); dd.text((k * (w + 10) + 4, 10), lab, fill=(255, 255, 255), font=F)
    sheet2.save(R / ('haze_before_after_%s.jpg' % i), quality=88)
# 4. log hollow bottom alpha
a = np.array(load('tree_log_hollow_A3_01'))[..., 3]; ys, xs = np.where(a > 8)
rows_ = {int(y): int((a[y] > 0).sum()) for y in range(a.shape[0] - 12, a.shape[0])}
hi = np.where(a >= 40); print('alpha>=40 count', len(hi[0]), 'rows', hi[0].min() if len(hi[0]) else None, hi[0].max() if len(hi[0]) else None)
print('rows near bottom nonzero counts', rows_)
print('max alpha per bottom 8 rows', [int(a[y].max()) for y in range(a.shape[0] - 8, a.shape[0])])

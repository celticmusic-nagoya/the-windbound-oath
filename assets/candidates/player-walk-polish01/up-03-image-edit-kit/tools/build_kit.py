#!/usr/bin/env python3
"""PLAYER-WALK-UP-03: build the verified image-edit kit for the Aidan back-view RIGHT push-off pose.
Reads production PNGs only; writes OUT/PLAYER-WALK-UP-03/... and the ZIP. usage: build_kit.py OUTDIR"""
import hashlib, json, os, shutil, sys, zipfile
import numpy as np, cv2
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from legs import load, split, legs, SPL, A  # noqa: E402

OUT = os.path.abspath(sys.argv[1]); K = os.path.join(OUT, 'PLAYER-WALK-UP-03'); BG = (70, 100, 70, 255)
OLD_POLY = np.array([(1030, 790), (1150, 790), (1175, 1000), (1180, 1240), (1000, 1240), (1010, 1000)], np.int32)   # PR #149 mask
CROP = (940, 760, 1220, 1240)        # right-leg crop, original canvas coordinates (x0, y0, x1, y1), exclusive
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def lbl(img, text, xy=(4, 3)):
    d = ImageDraw.Draw(img); w = 7 * len(text) + 10; d.rectangle((xy[0] - 2, xy[1] - 2, xy[0] + w, xy[1] + 14), fill=(0, 0, 0)); d.text(xy, text, fill='white'); return img


def on_bg(rgba, bg=BG):
    b = Image.new('RGBA', rgba.size, bg); b.alpha_composite(rgba); return b


def main():
    if os.path.exists(K):
        shutil.rmtree(K)
    for d in ('01_original', '02_masks', '03_guides', '04_references', '05_crops', '06_prompts'):
        os.makedirs(os.path.join(K, d))
    man = {'task': 'PLAYER-WALK-UP-03', 'canvas': [2048, 1280], 'anchor': [1024, 1230], 'ground_y': 1229, 'files': {}}
    def rec(rel, **kw):
        p = os.path.join(K, rel); im = Image.open(p)
        man['files'][rel] = {'sha256': sha(p), 'size': list(im.size), 'mode': im.mode, 'has_alpha': im.mode in ('RGBA', 'LA'), **kw}
    # A. originals (byte copies)
    for n in (1, 2, 3, 4, 6):
        src = A + 'aidan_walk_up_%02d.png' % n; dst = os.path.join(K, '01_original', 'aidan_walk_up_%02d.png' % n)
        shutil.copyfile(src, dst); rel = os.path.relpath(dst, K)
        rec(rel, source='img/field/characters/aidan/aidan_walk_up_%02d.png' % n, source_sha256=sha(src), byte_identical=sha(src) == sha(dst))
    B = load(3); H, W = B.shape[:2]; X = np.arange(W)[None, :]; Y = np.arange(H)[:, None]
    cut = split(B, *SPL[3]); Lleg, Rleg = legs(B, cut)
    # left planted leg = connected left blob (fill holes) ; right leg of 03
    lab, n = ndi.label(Lleg); Lleg = lab == (1 + int(np.argmax(ndi.sum(Lleg, lab, range(1, n + 1)))))
    Lleg = ndi.binary_fill_holes(ndi.binary_closing(Lleg, iterations=3)) & (B[..., 3] > 24)
    from legs import hsv
    h, s, v = hsv(B)
    cloth = (B[..., 3] > 24) & ~((((h < 40) | (h > 340)) & (s > 0.38)) | (v < 0.36))       # hem, skirt, cape, trim
    # estimated push-off foot zone (see README 4): centre x = 2*1041 - 995 = 1087, width of the left push-off boot in 04 (~100 px)
    zone = np.zeros((H, W), np.uint8)
    cv2.ellipse(zone, (1088, 1170), (66, 72), 0, 0, 360, 1, -1)                        # boot + sole incl. margin
    cv2.fillPoly(zone, [np.array([(1040, 790), (1150, 790), (1160, 1110), (1030, 1110)], np.int32)], 1)   # thigh / shin corridor
    zone = zone.astype(bool) | ndi.binary_dilation(Rleg, iterations=6)
    overlap = Lleg & (X >= 1036) & (Y >= 1090)          # near push-off foot may cover this strip of the planted left boot
    trousers = (B[..., 3] > 24) & (v < 0.36) & ((h < 40) | (h > 340))
    above_ok = (B[..., 3] <= 24) | trousers | Rleg                # above y=1000 only trousers / own right leg / empty space
    proposed = zone & ~(Lleg & ~overlap) & np.where(Y < 1000, above_ok, True) & (Y >= 780) & (Y < 1240)
    proposed = ndi.binary_opening(proposed, iterations=2)
    lab, n = ndi.label(proposed); proposed = lab == (1 + int(np.argmax(ndi.sum(proposed, lab, range(1, n + 1)))))   # one region, no islands on the cape
    proposed = ndi.gaussian_filter(proposed.astype(float), 2.5) > 0.5                     # rounded outline, no long straight edges
    proposed &= ~(Lleg & ~overlap) & np.where(Y < 1000, above_ok, True)
    old = np.zeros((H, W), np.uint8); cv2.fillPoly(old, [OLD_POLY], 1); old = old.astype(bool)
    Image.fromarray((old * 255).astype(np.uint8)).save(os.path.join(K, '02_masks/original_mask.png'))
    Image.fromarray((proposed * 255).astype(np.uint8)).save(os.path.join(K, '02_masks/proposed_mask.png'))
    # straight-edge check: longest run of the outline along one row/column
    def longest_straight(m):
        e = m & ~ndi.binary_erosion(m); best = 0
        for arr in (e, e.T):
            for line in arr:
                run = 0
                for x in line:
                    run = run + 1 if x else 0; best = max(best, run)
        return best
    zone_pf = np.zeros((H, W), np.uint8); cv2.ellipse(zone_pf, (1088, 1170), (52, 60), 0, 0, 360, 1, -1); zone_pf = zone_pf.astype(bool)
    def stats(m):
        return {'px': int(m.sum()), 'bbox': [int(np.nonzero(m)[1].min()), int(np.nonzero(m)[0].min()), int(np.nonzero(m)[1].max()) + 1, int(np.nonzero(m)[0].max()) + 1],
                'left_leg_px_inside': int((m & Lleg).sum()), 'left_leg_px_inside_outside_overlap_strip': int((m & Lleg & ~overlap).sum()),
                'right_leg_03_px_covered_pct': round(100 * float((m & Rleg).sum()) / max(1, Rleg.sum()), 1),
                'cloth_px_inside_above_y1000': int((m & cloth & (Y < 1000)).sum()), 'estimated_pushoff_boot_covered_pct': round(100 * float((m & zone_pf).sum()) / zone_pf.sum(), 1),
                'longest_straight_outline_px': longest_straight(m)}
    man['masks'] = {'02_masks/original_mask.png': {'origin': 'PR #149 repaint-kit polygon', 'polygon': OLD_POLY.tolist(), **stats(old)},
                    '02_masks/proposed_mask.png': {'origin': 'PLAYER-WALK-UP-03', **stats(proposed),
                                                   'overlap_strip_on_left_boot': {'rule': 'left-leg pixels with x>=1036 and y>=1090', 'px': int((proposed & overlap).sum())}}}
    # comparison image
    base = on_bg(Image.open(A + 'aidan_walk_up_03.png').convert('RGBA')); arr = np.array(base)
    def tint(m, col):
        a = arr.copy().astype(float); a[m, :3] = a[m, :3] * .45 + np.array(col) * .55; return Image.fromarray(a.astype(np.uint8))
    box = (860, 740, 1260, 1250)
    t1 = lbl(tint(old & ~Lleg, (255, 40, 160)).crop(box), 'ORIGINAL mask (PR149)')
    a2 = np.array(t1.convert('RGBA'))
    t1 = tint(old, (255, 40, 160)); t1 = Image.fromarray(np.array(t1)); t1a = np.array(t1).astype(float)
    t1a[old & Lleg, :3] = t1a[old & Lleg, :3] * .3 + np.array([255, 0, 0]) * .7; t1 = lbl(Image.fromarray(t1a.astype(np.uint8)).crop(box), 'ORIGINAL (red = left leg edited!)')
    t2a = np.array(tint(proposed, (255, 40, 160))).astype(float); t2a[proposed & overlap, :3] = t2a[proposed & overlap, :3] * .3 + np.array([255, 200, 0]) * .7
    t2a[Lleg & ~proposed, :3] = t2a[Lleg & ~proposed, :3] * .6 + np.array([0, 120, 255]) * .4
    t2 = lbl(Image.fromarray(t2a.astype(np.uint8)).crop(box), 'PROPOSED (yellow=allowed overlap, blue=protected L)')
    cmp = Image.new('RGB', (t1.width * 2 + 8, t1.height), (30, 30, 30)); cmp.paste(t1.convert('RGB'), (0, 0)); cmp.paste(t2.convert('RGB'), (t1.width + 8, 0))
    cmp = cmp.resize((cmp.width * 2, cmp.height * 2), Image.NEAREST); cmp.save(os.path.join(K, '02_masks/mask_comparison.png'))
    # E. guides
    g = np.array(base).astype(float); g[proposed, :3] = g[proposed, :3] * .55 + np.array([255, 40, 160]) * .45
    g[Lleg & ~proposed, :3] = g[Lleg & ~proposed, :3] * .6 + np.array([0, 120, 255]) * .4
    gi = Image.fromarray(g.astype(np.uint8)); d = ImageDraw.Draw(gi)
    d.line([(700, 1229), (1400, 1229)], fill=(255, 60, 60, 255), width=3); d.line([(1024, 1190), (1024, 1260)], fill=(255, 255, 0, 255), width=3)
    d.text((1190, 1205), 'ground y=1229', fill='white'); d.text((960, 1240), 'anchor (1024,1230)', fill='yellow')
    d.text((1160, 900), 'magenta = editable', fill='white'); d.text((760, 1100), 'blue = protected left leg', fill='white')
    lbl(gi.crop((700, 560, 1400, 1270)), 'canvas 2048x1280 / crop shown x700-1400 y560-1270').convert('RGB').save(os.path.join(K, '03_guides/anchor_ground_guide.png'))
    pg = base.copy(); d = ImageDraw.Draw(pg)
    d.ellipse((1088 - 52, 1170 - 60, 1088 + 52, 1170 + 60), outline=(255, 220, 0, 255), width=3)
    d.line([(1095, 860), (1092, 1100)], fill=(255, 220, 0, 255), width=4); d.polygon([(1080, 1095), (1104, 1095), (1092, 1118)], fill=(255, 220, 0, 255))
    d.line([(1040, 1229), (1140, 1229)], fill=(255, 60, 60, 255), width=3)
    d.text((1150, 1110), 'estimated sole (toe on y=1229)', fill='yellow'); d.text((1110, 900), 'right thigh comes out under the hem', fill='yellow')
    d.text((760, 1160), 'LEFT foot stays planted', fill='white')
    lbl(pg.crop((740, 760, 1300, 1260)), 'RIGHT (anatomical) push-off: estimate, not a drawing').convert('RGB').resize((1120, 1000), Image.NEAREST).save(os.path.join(K, '03_guides/right_leg_pose_guide.png'))
    # B/C. references (no mirroring anywhere)
    def crop(n, box, scale, text):
        im = on_bg(Image.open(A + 'aidan_walk_up_%02d.png' % n).convert('RGBA')).crop(box)
        return lbl(im.resize((im.width * scale, im.height * scale), Image.NEAREST), text).convert('RGB')
    def strip(tiles):
        s = Image.new('RGB', (sum(t.width + 8 for t in tiles) - 8, max(t.height for t in tiles)), (30, 30, 30)); x = 0
        for t in tiles:
            s.paste(t, (x, 0)); x += t.width + 8
        return s
    strip([crop(1, (1000, 1060, 1140, 1235), 3, 'up01 ANAT. RIGHT boot (screen right)'), crop(6, (1010, 1060, 1140, 1235), 3, 'up06 ANAT. RIGHT boot (screen right)'),
           crop(2, (1030, 1000, 1150, 1235), 3, 'up02 ANAT. RIGHT boot (screen right)')]).save(os.path.join(K, '04_references/right_boot_details.png'))
    strip([crop(1, (930, 780, 1180, 1235), 2, 'up01: L push-off | R planted'), crop(3, (930, 780, 1180, 1235), 2, 'up03: L planted | R receding'),
           crop(6, (930, 780, 1180, 1235), 2, 'up06: L passing | R planted')]).save(os.path.join(K, '04_references/leg_anatomy_comparison.png'))
    strip([crop(4, (900, 780, 1180, 1235), 2, 'up04 LEFT push-off: posture/sole only, do NOT copy'), crop(2, (900, 780, 1180, 1235), 2, 'up02 LEFT push-off: posture only')]).save(os.path.join(K, '04_references/push_off_motion_reference.png'))
    # crops (native pixels, plus nearest x3)
    x0, y0, x1, y1 = CROP
    c = Image.open(A + 'aidan_walk_up_03.png').convert('RGBA').crop(CROP); c.save(os.path.join(K, '05_crops/right_leg_crop.png'))
    c.resize((c.width * 3, c.height * 3), Image.NEAREST).save(os.path.join(K, '05_crops/right_leg_crop_x3_nearest.png'))
    Image.fromarray((proposed[y0:y1, x0:x1] * 255).astype(np.uint8)).save(os.path.join(K, '05_crops/right_leg_crop_mask.png'))
    man['crop'] = {'source': 'aidan_walk_up_03.png', 'box_xyxy_exclusive': list(CROP), 'paste_back_at': [x0, y0], 'x3_version': 'nearest neighbour, no interpolation'}
    for rel in ('02_masks/original_mask.png', '02_masks/proposed_mask.png', '02_masks/mask_comparison.png', '03_guides/anchor_ground_guide.png', '03_guides/right_leg_pose_guide.png',
                '04_references/right_boot_details.png', '04_references/leg_anatomy_comparison.png', '04_references/push_off_motion_reference.png',
                '05_crops/right_leg_crop.png', '05_crops/right_leg_crop_x3_nearest.png', '05_crops/right_leg_crop_mask.png'):
        rec(rel)
    txt = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'kit_text')
    shutil.copyfile(os.path.join(txt, '00_README.md'), os.path.join(K, '00_README.md'))
    shutil.copyfile(os.path.join(txt, 'image_edit_instructions.md'), os.path.join(K, '06_prompts/image_edit_instructions.md'))
    man['minimal_chatgpt_set'] = ['05_crops/right_leg_crop.png', '05_crops/right_leg_crop_mask.png', '04_references/right_boot_details.png']
    man['proposed_mask_rule'] = 'right leg of 03 dilated 6 px + hem-to-boot corridor + estimated push-off boot ellipse c(1088,1170) r(66,72); minus planted left leg except strip x>=1036,y>=1090; above y=1000 only trousers/empty; single region; gaussian-rounded'
    json.dump(man, open(os.path.join(K, 'manifest.json'), 'w'), indent=1, ensure_ascii=False)
    z = os.path.join(OUT, 'PLAYER-WALK-UP-03_image-edit-kit.zip')
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as f:
        for root, _, files in os.walk(K):
            for fn in sorted(files):
                fp = os.path.join(root, fn); f.write(fp, os.path.relpath(fp, OUT))
    print(json.dumps(man['masks'], indent=1))


if __name__ == '__main__':
    main()

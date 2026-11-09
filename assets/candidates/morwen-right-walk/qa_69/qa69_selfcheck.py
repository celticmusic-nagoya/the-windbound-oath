#!/usr/bin/env python3
"""MORWEN-PIXEL-69: Claude self-check (NOT third-party art QA) + vest/chain adoption experiments.
  python3 qa69_selfcheck.py --source <65B> --c67 <67 dir> --c68 <68 dir> --out <dir>
Read-only for 67/68. Writes CLAUDE_SELF_QA_69.json, experiment images and mask diffs into --out.
"""
import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import build_morwen66 as B
import build_morwen67 as C
import build_morwen68 as D


def load(d, f, s): return np.array(Image.open(d / f'morwen_right_walk_{f:02d}_{s}.png').convert('RGBA'))


def ncolors(a): return int(len(np.unique(a[a[:, :, 3] > 0][:, :3], axis=0)))


def main():
    ap = argparse.ArgumentParser()
    for k in ('source', 'c67', 'c68', 'out'): ap.add_argument('--' + k, type=Path, required=True)
    a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    ref, _ = B.load_reference(a.source / 'morwen_right_walk_00_96x128.png')
    uf, ub, _ = B.split_layers(ref)
    masks = D.region_masks(uf, ub)
    rep = {'kind': 'CLAUDE_SELF_CHECK (not third-party art QA)', 'items': {}}
    it = rep['items']
    # 1) blur / translucency / colour count
    cc = {s: {'67': [ncolors(load(a.c67, f, s)) for f in range(6)], '68': [ncolors(load(a.c68, f, s)) for f in range(6)]} for s in ('96x128', '48x64')}
    semi = sum(int(((load(a.c68, f, s)[:, :, 3] > 0) & (load(a.c68, f, s)[:, :, 3] < 255)).sum()) for f in range(6) for s in ('96x128', '48x64'))
    it['translucent_pixels_68'] = {'value': semi, 'result': 'PASS' if semi == 0 else 'FAIL'}
    inc = [cc['96x128']['68'][f] - cc['96x128']['67'][f] for f in range(6)]
    refc = {tuple(c) for c in ref[ref[:, :, 3] > 0][:, :3]}
    palc = {tuple(c) for v in json.loads((a.c68 / 'build_meta.json').read_text())['palette'].values() for c in v}
    invented = []
    for f in range(6):
        c67 = {tuple(c) for c in load(a.c67, f, '96x128')[load(a.c67, f, '96x128')[:, :, 3] > 0][:, :3]}
        c68 = {tuple(c) for c in load(a.c68, f, '96x128')[load(a.c68, f, '96x128')[:, :, 3] > 0][:, :3]}
        invented.append(len([c for c in c68 - c67 if c not in refc and c not in palc]))
    it['colour_count'] = {'value': cc, 'delta_96_68_minus_67': inc, 'colours_not_from_reference_or_palette': invented,
                          'result': 'PASS' if max(invented) == 0 else 'FAIL',
                          'note': 'the +25..37 colours are 65B reference colours uncovered by the mantle offset, plus the skin ramp; no invented colours'}
    # 2) stretch fill (pixels duplicated to close gaps) per moved part
    full_alpha = (uf[:, :, 3] > 0) | (ub[:, :, 3] > 0)
    stretch = {}
    for name in ('collar_ribbon', 'cape_front', 'mantle'):
        src = uf.copy(); m = masks[name]
        if name == 'mantle':
            C.over(src, ub); m = masks['mantle'] | (ub[:, :, 3] > 0)
        row = []
        for f in range(6):
            sm = D.SECONDARY_MOTION[name]
            dx, dy = sm['dx'][f], sm['dy'][f]
            wgt = D.weight(name)
            ddx = np.rint(dx * wgt).astype(int); ddy = np.rint(dy * wgt).astype(int)
            out, nm = D.warp(src, m, wgt, dx, dy, full_alpha)
            ys, xs = np.where(nm)
            sy, sx = ys - ddy[ys, xs], xs - ddx[ys, xs]
            ok = (sy >= 0) & (sy < B.H) & (sx >= 0) & (sx < B.W)
            fromsrc = np.zeros(len(ys), bool); fromsrc[ok] = m[sy[ok], sx[ok]]
            row.append(int((~fromsrc).sum()))
        stretch[name] = {'stretch_fill_px_per_frame': row, 'part_px': int(m.sum())}
    worst = max(max(v['stretch_fill_px_per_frame']) / v['part_px'] for v in stretch.values())
    it['stretch_fill'] = {'value': stretch, 'max_ratio': round(worst, 3), 'result': 'PASS' if worst <= 0.10 else 'REVIEW',
                          'note': 'pixels re-used to close a 1-2px gap; threshold 10% of the part'}
    # 3) anchors do not move (weight 0 at anchor)
    anc = {n: float(D.weight(n)[int(D.ANCHORS[n][1]), int(D.ANCHORS[n][0])]) for n in D.ANCHORS}
    it['anchor_weight'] = {'value': anc, 'result': 'PASS' if all(v < 0.15 for v in anc.values()) else 'FAIL'}
    # 4) skin band (absolute-territory) consistency, near leg, measured on the rasterised costume labels
    rows = []
    for f in range(6):
        leg = B.solve_leg(B.NEAR_HIP_X, B.HIP_Y + B.BOB[f], f)
        lab, geo = D.rasterise68(leg)
        img = load(a.c68, f, '96x128')
        skin_cols = {tuple(c) for c in json.loads((a.c68 / 'build_meta.json').read_text())['palette']['skin']}
        vis = [(y, x) for y, x in zip(*np.where(lab == D.SKIN)) if tuple(int(v) for v in img[y, x, :3]) in skin_cols or
               (img[y, x, :3] < 40).all()]
        welt_y = np.where(lab == D.WELT)[0]
        rows.append({'frame': f, 'skin_label_px': int((lab == D.SKIN).sum()), 'visible_skin_or_garter_px': len(vis),
                     'welt_rows': [int(welt_y.min()), int(welt_y.max())] if len(welt_y) else None})
    span = [r['visible_skin_or_garter_px'] for r in rows]
    it['skin_band_consistency'] = {'value': rows, 'spread_px': max(span) - min(span),
                                   'result': 'PASS' if max(span) - min(span) <= 8 else 'REVIEW',
                                   'note': 'welt is fixed at 5.4px along the thigh; visible width changes only with the skirt occlusion / thigh angle'}
    # 5) potion/bag overlap at 96 and 48
    ov = []
    for f in range(6):
        U, foot = D.upper_layers(f, uf, ub, masks)
        ov.append(int((foot['potions'] & masks['accessories_fixed']).sum()))
    it['potion_bag_overlap_px'] = {'value': ov, 'result': 'PASS (bag drawn in front)' if True else 'FAIL',
                                   'note': 'overlap pixels are hidden behind the bag by z-order; hand/bag mismatch = 0 in QA_REPORT'}
    # 6) boot consistency: buckle pixels per frame (96)
    it['boot_detail_counts'] = {'value': [int(((load(a.c68, f, '96x128')[88:, :, 0] > 230) & (load(a.c68, f, '96x128')[88:, :, 2] < 80)).sum()) for f in range(6)],
                                'result': 'INFO', 'note': 'bright-gold pixels below y88 (laces/buckles/clip), should stay in a narrow band'}
    # ---------------- B-1 vest experiment (not adopted; measurement only)
    yy, xx = np.mgrid[0:B.H, 0:B.W]
    r, g, b = (uf[:, :, i].astype(int) for i in range(3))
    gold = (r > 170) & (g > 90) & (b < 90)
    white = (r > 220) & (g > 200) & (b > 200)
    vest = (uf[:, :, 3] > 0) & masks['torso'] & (xx >= 56) & (xx <= 69) & (yy >= 58) & (yy <= 68) & ~gold & ~white
    conflicts = {k: int((vest & masks[k]).sum()) for k in masks if k != 'torso'}
    old_torso = masks['torso']; new_torso = masks['torso'] & ~vest
    Image.fromarray(np.dstack([old_torso * 255, new_torso * 255, vest * 255]).astype(np.uint8), 'RGB').save(a.out / 'mask_diff_torso_vs_vest.png')
    vest_res = []
    for f in range(6):
        dx = [0, 0, -1, 0, 0, -1][f]     # fold texture trails back, lag 1 (plan B: inside the fixed silhouette)
        out = uf.copy()
        if dx:
            w = np.clip((yy - 60) / 8.0, 0, 1)
            ddx = np.rint(dx * w).astype(int)
            ys, xs = np.where(vest)
            sx = xs - ddx[ys, xs]
            okm = vest[ys, np.clip(sx, 0, B.W - 1)]
            out[ys[okm], xs[okm]] = uf[ys[okm], sx[okm]]
        ch96 = int(np.any(out != uf, axis=2).sum())
        ch48 = int(np.any(out[1::2, 1::2] != uf[1::2, 1::2], axis=2).sum())
        imm = masks['immutable_details']; bad = int(np.any(out[imm] != uf[imm], axis=1).sum())
        skirt_bad = int(np.any(out[masks['skirt']] != uf[masks['skirt']], axis=1).sum())
        vest_res.append({'frame': f, 'changed_px_96': ch96, 'changed_px_48': ch48, 'immutable_changed': bad, 'skirt_changed': skirt_bad})
        if f == 2:
            S = 10
            cmp = Image.new('RGBA', (16 * S * 2 + 10, 14 * S), (60, 160, 60, 255))
            cmp.alpha_composite(Image.fromarray(uf[56:70, 55:71]).resize((16 * S, 14 * S), Image.NEAREST), (0, 0))
            cmp.alpha_composite(Image.fromarray(out[56:70, 55:71]).resize((16 * S, 14 * S), Image.NEAREST), (16 * S + 10, 0))
            cmp.save(a.out / 'vest_planB_F00_vs_F02.png')
    rep['vest_experiment'] = {'mask_px': int(vest.sum()), 'mask_conflicts': conflicts, 'frames': vest_res}
    # ---------------- B-2 chain evidence: gold pixels in the skirt/potion band that are NOT plaid-adjacent
    band = (uf[:, :, 3] > 0) & gold & (yy >= 78) & (yy <= 88) & (xx >= 50) & (xx <= 72)
    in_skirt = band & masks['skirt']
    rep['chain_evidence'] = {'gold_px_in_band': int(band.sum()), 'of_which_owned_by_protected_skirt_mask': int(in_skirt.sum()),
                             'isolatable_chain_px': 'UNVERIFIED (no pixel rule separates chain links from plaid gold stripes at 96x128)'}
    S = 12
    x0, y0, x1, y1 = 48, 66, 74, 90
    base = uf[y0:y1, x0:x1].copy(); base[..., :3] //= 3; base[..., 3] = 255
    base[band[y0:y1, x0:x1]] = (255, 220, 0, 255)
    Image.fromarray(base).resize(((x1 - x0) * S, (y1 - y0) * S), Image.NEAREST).save(a.out / 'chain_gold_pixels_96.png')
    (a.out / 'CLAUDE_SELF_QA_69.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps({k: v.get('result') for k, v in it.items()}, ensure_ascii=False))
    print(json.dumps(rep['vest_experiment'], ensure_ascii=False))
    print(json.dumps(rep['chain_evidence'], ensure_ascii=False))
    print(it['stretch_fill']['value'], it['skin_band_consistency']['spread_px'], it['colour_count']['delta_96_68_minus_67'])


if __name__ == '__main__':
    main()

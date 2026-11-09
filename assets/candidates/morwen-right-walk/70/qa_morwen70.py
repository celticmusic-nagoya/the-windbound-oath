#!/usr/bin/env python3
"""MORWEN-PIXEL-70 build (easing A and B) + QA + reports.
  python3 qa_morwen70.py --source <65B> --c67 <67 dir> --c68 <68 dir> --out <70 dir> [--repo <repo root>]
Exit 2 if a protected pixel changed outside a declared motion footprint.
"""
import argparse, json, hashlib, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
import build_morwen66 as B
import build_morwen67 as C
import build_morwen68 as D
import build_morwen70 as E
from qa_morwen66 import components


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(d, f, s): return np.array(Image.open(Path(d) / f'morwen_right_walk_{f:02d}_{s}.png').convert('RGBA'))
def lum(c): return 0.30 * c[..., 0] + 0.59 * c[..., 1] + 0.11 * c[..., 2]


def main():
    ap = argparse.ArgumentParser()
    for k in ('source', 'c67', 'c68', 'out'): ap.add_argument('--' + k, type=Path, required=True)
    ap.add_argument('--repo', type=Path)
    a = ap.parse_args()
    outA = a.out / 'easing_A'
    E.build(a.source, outA, 'A')
    frames, smalls, uf, ub, masks, U96s, meta = E.build(a.source, a.out, 'B')
    E.configure('B', uf)                      # keep the B tables active for the footprint checks below
    fails, rep = [], {'task': 'MORWEN-PIXEL-70', 'base': 'MORWEN-PIXEL-68 code (unchanged) + 70 constants',
                      'scope': 'no new body/chest motion (agreed 2026-11-09); easing + dot finishing only',
                      'frames': []}
    pal = meta['palette']; skin_cols = {tuple(c) for c in pal['skin'] + pal['skin_far']}
    for f in range(6):
        e = {'frame': f}; bob = B.BOB[f]
        for size in ('96x128', '48x64'):
            p = a.out / f'morwen_right_walk_{f:02d}_{size}.png'; im = Image.open(p); arr = np.array(im)
            ok = im.mode == 'RGBA' and im.size == ((96, 128) if size == '96x128' else (48, 64))
            rgb0 = bool(np.all(arr[arr[:, :, 3] == 0, :3] == 0)); binary = bool(np.isin(arr[:, :, 3], (0, 255)).all())
            comps = components(arr[:, :, 3] > 0)
            e[size] = {'rgba_size_ok': ok, 'transparent_rgb_zero': rgb0, 'alpha_binary': binary, 'stray_components': comps[1:], 'sha256': sha(p)}
            if not (ok and rgb0 and binary) or comps[1:]: fails.append(f'F{f} {size} format/stray')
        img, sm = load(a.out, f, '96x128'), load(a.out, f, '48x64')
        imm = B.shift(C.masked(uf, masks['immutable_details']), 0, bob); m = imm[:, :, 3] > 0
        bad = int(np.any(imm[m] != img[m], axis=1).sum()); bad48 = int(np.any(imm[1::2, 1::2][m[1::2, 1::2]] != sm[m[1::2, 1::2]], axis=1).sum())
        U96, foot = U96s[f]
        prot = np.zeros_like(uf)
        for k in ('skirt', 'torso', 'accessories_fixed'): C.over(prot, B.shift(C.masked(uf, masks[k]), 0, bob))
        pm = prot[:, :, 3] > 0
        moved = np.zeros(pm.shape, bool)
        for k in ('collar_ribbon', 'cape_front', 'potions', 'mantle'): moved |= foot[k]
        diff = pm & np.any(prot != img, axis=2)
        e['protected'] = {'immutable_mismatch_96': bad, 'immutable_mismatch_48': bad48,
                          'covered_by_declared_motion': int((diff & moved).sum()), 'unexplained_change': int((diff & ~moved).sum())}
        if bad or bad48 or e['protected']['unexplained_change']: fails.append(f'F{f} PROTECTED CHANGED')
        acc = B.shift(C.masked(uf, masks['accessories_fixed']), 0, bob); am = acc[:, :, 3] > 0
        e['hand_bag_mismatch'] = int(np.any(acc[am] != img[am], axis=1).sum())
        if e['hand_bag_mismatch']: fails.append(f'F{f} hand/bag')
        # costume (stocking structure) identical to 68: skin band + garter + welt pixels
        i68 = load(a.c68, f, '96x128')
        skin68 = np.array([[px[3] > 0 and tuple(int(v) for v in px[:3]) in skin_cols for px in row] for row in i68])
        dark_or_gold = (i68[:, :, 3] > 0) & ((i68[:, :, 0] > 170) & (i68[:, :, 2] < 90) | (lum(i68[..., :3].astype(float)) < 30))
        costume = skin68 | (np.roll(skin68, 1, 0) & dark_or_gold)      # skin band, its garter strap/clip row below
        cdiff = int((costume & np.any(i68 != img, axis=2)).sum())
        e['costume_skin_garter_changed_vs_68'] = cdiff
        if cdiff: fails.append(f'F{f} costume changed {cdiff}')
        # changed-pixel report vs 68
        d96 = np.any(i68 != img, axis=2)
        yy, xx = np.mgrid[0:B.H, 0:B.W]
        e['changed_px_vs_68'] = {'total': int(d96.sum()), 'legs_y>=88_x>=40': int((d96 & (yy >= 88) & (xx >= 40)).sum()),
                                 'mantle_region_x<=41': int((d96 & (xx <= 41)).sum()),
                                 'other': int((d96 & ~((yy >= 88) & (xx >= 40)) & ~(xx <= 41)).sum()),
                                 'changed_px_48': int(np.any(load(a.c68, f, '48x64') != sm, axis=2).sum())}
        if e['changed_px_vs_68']['other']: fails.append(f'F{f} unexpected change outside legs/mantle')
        rep['frames'].append(e)
    # ground + gait identical to 68
    m68 = json.loads((a.c68 / 'build_meta.json').read_text())
    same = all(m68['frames'][f][s][k] == meta['frames'][f][s][k] for f in range(6) for s in ('near', 'far') for k in ('hip', 'knee', 'ankle'))
    rep['gait_identical_to_68'] = same
    if not same: fails.append('gait changed')
    for f in range(6):
        for side, ph in (('near', f), ('far', (f + 3) % 6)):
            leg = B.solve_leg(B.NEAR_HIP_X if side == 'near' else B.FAR_HIP_X, B.HIP_Y + B.BOB[f], ph)
            lab, _ = D.rasterise68(leg); low = int(np.where(lab > 0)[0].max())
            if low != B.GROUND - B.GAIT[ph]['lift']: fails.append(f'F{f} {side} ground')
    # motion: lag / steps / anchors
    mot = {}
    for n, s in D.SECONDARY_MOTION.items():
        absdy = [B.BOB[f] + s['dy'][f] for f in range(6)]
        steps = [max(abs(s['dx'][(i + 1) % 6] - s['dx'][i]), abs(absdy[(i + 1) % 6] - absdy[i])) for i in range(6)]
        mot[n] = {'dx': s['dx'], 'dy_rel': s['dy'], 'dy_abs': absdy, 'body_bob': B.BOB, 'max_step_px': max(steps), 'F05_to_F00_px': steps[5]}
        if max(steps) > 1: fails.append(f'{n} step>1')
    # one-frame lag of the cloth vs the trunk: absolute cloth dy reaches the body's down position, then stays one frame longer
    lag_ok = all(mot[n]['dy_abs'][f] == max(B.BOB[f], B.BOB[f - 1]) for n in ('collar_ribbon', 'cape_front', 'potions') for f in range(6))
    rep['cloth_one_frame_lag'] = {'result': 'PASS' if lag_ok else 'FAIL', 'rule': 'dy_abs(f) = max(bob(f), bob(f-1))'}
    if not lag_ok: fails.append('lag rule')
    anchors = {}
    full_alpha = (uf[:, :, 3] > 0) | (ub[:, :, 3] > 0)
    for n in D.ANCHORS:
        ax, ay = int(D.ANCHORS[n][0]), int(D.ANCHORS[n][1])
        src = uf.copy(); mk = masks[n]
        if n == 'mantle':
            C.over(src, ub); mk = masks['mantle'] | (ub[:, :, 3] > 0)
        wgt = D.weight(n); near = mk & (wgt < 0.25)
        moved_px = 0
        for f in range(6):
            o, _ = D.warp(src, mk, wgt, D.SECONDARY_MOTION[n]['dx'][f], D.SECONDARY_MOTION[n]['dy'][f], full_alpha)
            moved_px += int(np.any(o[near] != src[near], axis=1).sum())
        anchors[n] = {'anchor': [ax, ay], 'part_px_within_25pct_of_reach': int(near.sum()), 'moved_px_over_6_frames': moved_px}
        if moved_px: fails.append(f'anchor {n} moved')
    rep['secondary_motion'] = mot; rep['anchor_fixed'] = anchors
    # easing comparison
    v = 6.0 / 125.0
    def slide(wts):
        return [round(abs(6.0 - v * 125.0 * w_), 2) for w_ in wts]
    rep['easing'] = {
        'A_uniform': {'frames': 'easing_A/', 'timing_ms': [125] * 6, 'foot_slide_px': slide([1] * 6), 'note': '68 motion tables + 70 dot finishing'},
        'B_pixel_hold': {'frames': './', 'timing_ms': [125] * 6, 'foot_slide_px': slide([1] * 6),
                         'mantle_dx': E.EASING_B['mantle']['dx'], 'note': E.EASING_B['mantle']['note'],
                         'changed_px_vs_A': [int(np.any(load(outA, f, '96x128') != load(a.out, f, '96x128'), axis=2).sum()) for f in range(6)]},
        'C_display_time': {'frames': 'easing_A/', 'weights': E.EASING_C_WEIGHTS, 'timing_ms': [round(125 * w_) for w_ in E.EASING_C_WEIGHTS],
                           'foot_slide_px': slide(E.EASING_C_WEIGHTS),
                           'result': 'REJECT', 'reason': 'stance foot advances 6px every frame; with constant walk speed the ground moves 7.5px in a 156ms frame and 4.5px in a 94ms frame -> 1.5px sliding per frame'},
        'recommendation': 'B'}
    # 48x64 flicker: changed pixels between consecutive frames in the upper body (bob-aligned)
    def flicker(d):
        out = []
        for f in range(6):
            g = (f + 1) % 6
            A_ = np.roll(load(d, f, '48x64'), -(B.BOB[f] // 1) * 0, 0)[:42]; B_ = load(d, g, '48x64')[:42]
            out.append(int(np.any(A_ != B_, axis=2).sum()))
        return out
    rep['flicker_48_upper_rows<42'] = {'68': flicker(a.c68), '70A': flicker(outA), '70B': flicker(a.out),
                                       'note': 'includes the 1px body bob; compare relative'}
    # background contrast of the leg silhouette edge
    bgs = {'light': (238, 234, 226), 'dark': (18, 16, 22)}
    if a.repo:
        for k, fn in (('moss', 'ground_moss.png'), ('dirt', 'ground_mossdirt.png')):
            g = np.array(Image.open(a.repo / 'img/field/moss/art' / fn).convert('RGB')).reshape(-1, 3).mean(0); bgs[k] = tuple(int(x) for x in g)
    def contrast(d):
        res = {}
        for name, bgc in bgs.items():
            vals = []
            for f in range(6):
                im = load(d, f, '96x128'); op = im[:, :, 3] > 0
                nb = np.zeros_like(op)
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): nb |= ~np.roll(np.roll(op, dy, 0), dx, 1)
                edge = op & nb; edge[:90] = False
                vals.append(float(np.abs(lum(im[edge][:, :3].astype(float)) - lum(np.array(bgc, float))).mean()))
            res[name] = round(float(np.mean(vals)), 1)
        return res
    rep['leg_edge_contrast'] = {'background_rgb': bgs, '68': contrast(a.c68), '70': contrast(a.out)}
    # colours
    refc = {tuple(c) for c in uf[uf[:, :, 3] > 0][:, :3]} | {tuple(c) for c in ub[ub[:, :, 3] > 0][:, :3]}
    palc = {tuple(c) for vv in pal.values() for c in vv} | {tuple(v_) for v_ in E._RIM.values()} | {tuple(C.OUTLINE)}
    inv = [len([c for c in {tuple(c) for c in load(a.out, f, '96x128')[load(a.out, f, '96x128')[:, :, 3] > 0][:, :3]} if c not in refc and c not in palc]) for f in range(6)]
    rep['colours_not_from_reference_or_palette'] = inv
    if max(inv): fails.append(f'invented colours {inv}')
    rep['rim_snapped_to_upper_body'] = {k: list(v) for k, v in E._RIM.items()}
    # repo checks
    if a.repo:
        master = a.repo / 'assets/companions/morwen/master/morwen-full-body-v3.png'
        rep['master_v3_sha256'] = sha(master)
        try:
            ch = subprocess.run(['git', '-C', str(a.repo), 'diff', '--name-status', 'HEAD', '--', 'assets/candidates/morwen-right-walk/right_walk_66',
                                 'assets/candidates/morwen-right-walk/right_walk_67', 'assets/candidates/morwen-right-walk/right_walk_68',
                                 'assets/companions', 'img', 'data'], capture_output=True, text=True).stdout.strip()
            rep['existing_assets_changed_in_worktree'] = ch or 'none'
            if ch: fails.append('existing assets changed')
        except Exception as ex:
            rep['existing_assets_changed_in_worktree'] = f'UNVERIFIED {ex}'
    rep['fails'] = fails
    rep['technical_qa'] = 'PASS' if not fails else 'FAIL'
    rep['third_party_art_qa'] = 'NOT_RUN'; rep['android_device_qa'] = 'NOT_RUN'; rep['production'] = 'NOT_APPLIED'
    (a.out / 'QA_REPORT_70.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
    gif = []
    for img in frames:
        bg = Image.new('RGBA', (96, 128), (164, 184, 150, 255)); bg.alpha_composite(Image.fromarray(img))
        gif.append(bg.convert('RGB').resize((288, 384), Image.NEAREST).convert('P', palette=Image.ADAPTIVE, colors=255))
    gif[0].save(a.out / 'morwen_right_walk_70.gif', save_all=True, append_images=gif[1:], duration=125, loop=0, disposal=2)
    print(json.dumps({'technical_qa': rep['technical_qa'], 'fails': fails, 'easing': {k: v.get('foot_slide_px') for k, v in rep['easing'].items() if isinstance(v, dict)},
                      'contrast': rep['leg_edge_contrast'], 'flicker': rep['flicker_48_upper_rows<42'], 'lag': rep['cloth_one_frame_lag'],
                      'changed': [fr['changed_px_vs_68'] for fr in rep['frames']]}, ensure_ascii=False, indent=1))
    if any('PROTECTED' in x for x in fails): sys.exit(2)


if __name__ == '__main__':
    main()

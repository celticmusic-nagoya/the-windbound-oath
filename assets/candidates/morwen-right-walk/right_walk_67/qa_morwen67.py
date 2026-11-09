#!/usr/bin/env python3
"""MORWEN-PIXEL-67 build + non-destructive QA + previews.
  python3 qa_morwen67.py --source <65B dir> --prev <66 dir> --out <67 dir>
Fails (exit 2) if any protected pixel changed.
"""
import argparse, json, hashlib, base64, sys, math
from pathlib import Path
import numpy as np
from PIL import Image
import build_morwen66 as B
import build_morwen67 as C
from qa_morwen66 import components, HTML


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def is_gold(a):
    r, g, b = (a[..., i].astype(int) for i in range(3))
    return (r > 170) & (g > 90) & (b < 80)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=Path, required=True); ap.add_argument('--prev', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    frames, smalls, fixed, ub, masks, meta = C.build(a.source, a.out)
    fails, rep = [], {'task': 'MORWEN-PIXEL-67', 'base': 'MORWEN-PIXEL-66 gait + 65B F00 protected layers',
                      'source_sha256': sha(a.source / 'morwen_right_walk_00_96x128.png'), 'frames': []}
    prot = fixed['skirt'][:, :, 3] | fixed['torso'][:, :, 3] | fixed['accessories'][:, :, 3]
    sil = []
    for f in range(6):
        e = {'frame': f}
        bob = B.BOB[f]
        for size, img in (('96x128', frames[f]), ('48x64', smalls[f])):
            p = a.out / f'morwen_right_walk_{f:02d}_{size}.png'
            im = Image.open(p); arr = np.array(im)
            ok = im.mode == 'RGBA' and im.size == ((96, 128) if size == '96x128' else (48, 64))
            rgb0 = bool(np.all(arr[arr[:, :, 3] == 0, :3] == 0))
            binary = bool(np.isin(arr[:, :, 3], (0, 255)).all())
            comps = components(arr[:, :, 3] > 0)
            e[size] = {'rgba_size_ok': ok, 'transparent_rgb_zero': rgb0, 'alpha_binary': binary,
                       'largest_component': comps[0], 'stray_components': comps[1:], 'sha256': sha(p)}
            if not (ok and rgb0 and binary): fails.append(f'F{f} {size} format')
            if comps[1:]: fails.append(f'F{f} {size} stray {comps[1:]}')
        # protected layers: exact RGBA after the declared transform (vertical bob only)
        exp = np.zeros_like(frames[f])
        for k in ('skirt', 'torso', 'accessories'):
            C.over(exp, B.shift(fixed[k], 0, bob))
        pm = exp[:, :, 3] > 0
        saved = np.array(Image.open(a.out / f'morwen_right_walk_{f:02d}_96x128.png'))
        saved48 = np.array(Image.open(a.out / f'morwen_right_walk_{f:02d}_48x64.png'))
        mism = int(np.any(exp[pm] != saved[pm], axis=1).sum())
        e48 = exp[1::2, 1::2]; pm48 = e48[:, :, 3] > 0
        mism48 = int(np.any(e48[pm48] != saved48[pm48], axis=1).sum())
        e['protected'] = {'layers': ['skirt', 'torso', 'accessories'], 'pixels_96': int(pm.sum()), 'mismatch_96': mism,
                          'pixels_48': int(pm48.sum()), 'mismatch_48': mism48}
        if mism or mism48: fails.append(f'F{f} PROTECTED CHANGED');
        # skirt / leg separation: in the hip columns there must be no transparent row between skirt and thigh
        legs = meta['frames'][f]
        gaps = []
        for side in ('near', 'far'):
            hx = legs[side]['hip'][0]
            for x in range(int(hx) - 2, int(hx) + 3):
                col = frames[f][:, x, 3] > 0
                top_leg = 87 + bob
                ys = np.where(col[top_leg - 6:top_leg + 10])[0]
                if len(ys) and (np.diff(ys) > 1).any(): gaps.append((side, x))
        e['skirt_leg_gaps'] = gaps
        if gaps: fails.append(f'F{f} skirt/leg gap {gaps}')
        # 48px decoration visibility
        s = smalls[f]
        lower = s[44:64, 22:48]
        e['visibility_48'] = {
            'gold_px_in_legs': int((is_gold(lower) & (lower[:, :, 3] > 0)).sum()),
            'plaid_px': int(((s[38:45, 25:35, 0] > 180) & (s[38:45, 25:35, 2] > 150) & (s[38:45, 25:35, 3] > 0)).sum()),
            'hem_gold_px_left': int((is_gold(s[42:48, 17:27]) & (s[42:48, 17:27, 3] > 0)).sum())}
        v = e['visibility_48']
        if v['gold_px_in_legs'] < 4 or v['plaid_px'] < 4 or v['hem_gold_px_left'] < 4: fails.append(f'F{f} 48 visibility {v}')
        sil.append(frames[f][:, :, 3] > 0)
        rep['frames'].append(e)
    # ground contact & gait identity with 66 (legs must be the same solved poses)
    ground = []
    for f in range(6):
        for side, ph in (('near', f), ('far', (f + 3) % 6)):
            leg = B.solve_leg(B.NEAR_HIP_X if side == 'near' else B.FAR_HIP_X, B.HIP_Y + B.BOB[f], ph)
            lab, _ = B.rasterise_leg(leg); low = int(np.where(lab > 0)[0].max())
            lab48, _ = B.rasterise_leg(leg, 0.5); low48 = int(np.where(lab48 > 0)[0].max())
            exp_low = B.GROUND - B.GAIT[ph]['lift']
            ground.append({'frame': f, 'side': side, 'phase': ph, 'lowest_row': low, 'expected': exp_low, 'lowest_row_48': low48})
            if low != exp_low: fails.append(f'F{f} {side} ground')
            if B.GAIT[ph]['lift'] == 0 and low48 != 61: fails.append(f'F{f} {side} ground48')
    rep['ground_contact'] = ground
    prev_meta = json.loads((a.prev / 'build_meta.json').read_text()) if (a.prev / 'build_meta.json').exists() else None
    if prev_meta:
        same = all(prev_meta['legs'][f][s][k] == meta['frames'][f][s][k] for f in range(6) for s in ('near', 'far') for k in ('hip', 'knee', 'ankle'))
        rep['gait_identical_to_66'] = same
        if not same: fails.append('gait changed vs 66')
    # silhouette change between consecutive frames (upper body must be stable; lower body changes by design)
    def iou(m1, m2):
        return round(float((m1 & m2).sum() / max(1, (m1 | m2).sum())), 3)
    rep['silhouette_iou'] = {f'{i:02d}->{(i + 1) % 6:02d}': {'upper_y<84': iou(np.roll(sil[i], -B.BOB[i], 0)[:84], np.roll(sil[(i + 1) % 6], -B.BOB[(i + 1) % 6], 0)[:84]),
                                                            'lower_y>=88': iou(sil[i][88:], sil[(i + 1) % 6][88:])} for i in range(6)}
    for k, v in rep['silhouette_iou'].items():
        if v['upper_y<84'] < 0.97: fails.append(f'upper silhouette jump {k}')
    rep['layers_z'] = ['cape_back', 'far_leg', 'far_boot', 'near_leg', 'near_boot', 'skirt_left', 'skirt', 'torso', 'accessories', 'per_frame_detail_patch']
    rep['mask_pixels'] = meta['mask_pixels']
    rep['palette_snapped_to_upper_body'] = meta['palette_snapped_to_upper_body']
    rep['frame_art_patches'] = {'96': C.FRAME_ART_PATCHES, '48': C.FRAME_ART_PATCHES_48}
    rep['fails'] = fails
    rep['technical_qa'] = 'PASS' if not fails else 'FAIL'
    rep['art_qa'] = 'SELF_CHECK_ONLY / THIRD_PARTY_REQUIRED'
    rep['android'] = 'NOT_RUN'
    rep['production'] = 'NOT_APPLIED'
    (a.out / 'QA_REPORT.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')

    gif = []
    for img in frames:
        bg = Image.new('RGBA', (96, 128), (164, 184, 150, 255)); bg.alpha_composite(Image.fromarray(img))
        gif.append(bg.convert('RGB').resize((288, 384), Image.NEAREST).convert('P', palette=Image.ADAPTIVE, colors=255))
    gif[0].save(a.out / 'morwen_right_walk_67.gif', save_all=True, append_images=gif[1:], duration=125, loop=0, disposal=2)

    def b64(p): return 'data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode()
    html = HTML.replace('MORWEN-PIXEL-66', 'MORWEN-PIXEL-67').replace('旧版 65B', '前版 66').replace('旧版: 65B', '前版: 66') \
        .replace('新版: 脚・ブーツを歩行周期から再構築。', '新版: 66の歩行構造を維持し、脚・ブーツ・スカート左端を高精細化。')
    html = html.replace('__F96__', json.dumps([b64(a.out / f'morwen_right_walk_{f:02d}_96x128.png') for f in range(6)])) \
        .replace('__F48__', json.dumps([b64(a.out / f'morwen_right_walk_{f:02d}_48x64.png') for f in range(6)])) \
        .replace('__OLD__', json.dumps([b64(a.prev / f'morwen_right_walk_{f:02d}_96x128.png') for f in range(6)]))
    (a.out / 'android_motion_qa.html').write_text(html, encoding='utf-8')
    print(json.dumps({'technical_qa': rep['technical_qa'], 'fails': fails, 'gait_identical_to_66': rep.get('gait_identical_to_66'),
                      'silhouette': rep['silhouette_iou'], 'vis48': [fr['visibility_48'] for fr in rep['frames']]}, indent=1))
    if any('PROTECTED' in x for x in fails):
        sys.exit(2)


if __name__ == '__main__':
    main()

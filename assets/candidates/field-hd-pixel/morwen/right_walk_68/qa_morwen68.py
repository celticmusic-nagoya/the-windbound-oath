#!/usr/bin/env python3
"""MORWEN-PIXEL-68 build + QA + previews.
  python3 qa_morwen68.py --source <65B> --prev <67> --out <68>
Exit 2 if an immutable/protected pixel changed outside a declared secondary-motion footprint.
"""
import argparse, json, hashlib, base64, sys
from pathlib import Path
import numpy as np
from PIL import Image
import build_morwen66 as B
import build_morwen67 as C
import build_morwen68 as D
from qa_morwen66 import components, HTML


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=Path, required=True); ap.add_argument('--prev', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    frames, smalls, uf, ub, masks, U96s, meta = D.build(a.source, a.out)
    pal = meta['palette']
    skin_cols = {tuple(c) for c in pal['skin'] + pal['skin_far']}
    fails, rep = [], {'task': 'MORWEN-PIXEL-68', 'base': 'MORWEN-PIXEL-67 (gait 66, protected layers 65B F00)',
                      'source_sha256': sha(a.source / 'morwen_right_walk_00_96x128.png'), 'frames': []}
    for f in range(6):
        e = {'frame': f}; bob = B.BOB[f]
        saved = {}
        for size in ('96x128', '48x64'):
            p = a.out / f'morwen_right_walk_{f:02d}_{size}.png'
            im = Image.open(p); arr = np.array(im); saved[size] = arr
            ok = im.mode == 'RGBA' and im.size == ((96, 128) if size == '96x128' else (48, 64))
            rgb0 = bool(np.all(arr[arr[:, :, 3] == 0, :3] == 0)); binary = bool(np.isin(arr[:, :, 3], (0, 255)).all())
            comps = components(arr[:, :, 3] > 0)
            e[size] = {'rgba_size_ok': ok, 'transparent_rgb_zero': rgb0, 'alpha_binary': binary, 'stray_components': comps[1:], 'sha256': sha(p)}
            if not (ok and rgb0 and binary): fails.append(f'F{f} {size} format')
            if comps[1:]: fails.append(f'F{f} {size} stray {comps[1:]}')
        img, sm = saved['96x128'], saved['48x64']
        # 1) immutable details: strict
        imm = B.shift(C.masked(uf, masks['immutable_details']), 0, bob); m = imm[:, :, 3] > 0
        bad_imm = int(np.any(imm[m] != img[m], axis=1).sum())
        imm48 = imm[1::2, 1::2]; m48 = imm48[:, :, 3] > 0
        bad_imm48 = int(np.any(imm48[m48] != sm[m48], axis=1).sum())
        # 2) other protected layers (skirt, torso, bag+hand): identical except under declared motion footprints
        U96, foot = U96s[f]
        prot = np.zeros_like(uf)
        for k in ('skirt', 'torso', 'accessories_fixed'):
            C.over(prot, B.shift(C.masked(uf, masks[k]), 0, bob))
        pm = prot[:, :, 3] > 0
        moved = np.zeros(pm.shape, bool)
        for k in ('collar_ribbon', 'cape_front', 'potions', 'mantle'):
            moved |= foot[k]
        diff = pm & np.any(prot != img, axis=2)
        unexplained = int((diff & ~moved).sum()); occluded = int((diff & moved).sum())
        e['protected'] = {'immutable_details_px': int(m.sum()), 'immutable_mismatch_96': bad_imm, 'immutable_mismatch_48': bad_imm48,
                          'other_protected_px': int(pm.sum()), 'covered_by_declared_motion': occluded, 'unexplained_change': unexplained}
        if bad_imm or bad_imm48 or unexplained: fails.append(f'F{f} PROTECTED CHANGED {e["protected"]}')
        # 3) arm + bag relation: hand and bag are in accessories_fixed -> identical relative position
        acc = B.shift(C.masked(uf, masks['accessories_fixed']), 0, bob); am = acc[:, :, 3] > 0
        e['hand_bag_mismatch'] = int(np.any(acc[am] != img[am], axis=1).sum())
        if e['hand_bag_mismatch']: fails.append(f'F{f} hand/bag moved')
        # 4) costume structure: skin band visible between skirt and stocking welt, garter present (near leg)
        lower = img[86:104]
        skin_px = int(sum(1 for px in lower.reshape(-1, 4) if px[3] and tuple(int(v) for v in px[:3]) in skin_cols))
        lower48 = sm[43:52]
        skin48 = int(sum(1 for px in lower48.reshape(-1, 4) if px[3] and tuple(int(v) for v in px[:3]) in skin_cols))
        g = meta['frames'][f]['garter_px_96']
        e['costume'] = {'skin_px_96': skin_px, 'skin_px_48': skin48, 'garter_clip_96': g}
        if not (2 <= skin_px <= 30): fails.append(f'F{f} skin band {skin_px}')
        if skin48 < 1: fails.append(f'F{f} skin band 48 missing (skirt/stocking merge)')
        rep['frames'].append(e)
    # ground + gait identity
    for f in range(6):
        for side, ph in (('near', f), ('far', (f + 3) % 6)):
            leg = B.solve_leg(B.NEAR_HIP_X if side == 'near' else B.FAR_HIP_X, B.HIP_Y + B.BOB[f], ph)
            lab, _ = D.rasterise68(leg); low = int(np.where(lab > 0)[0].max())
            lab48, _ = D.rasterise68(leg, 0.5); low48 = int(np.where(lab48 > 0)[0].max())
            exp = B.GROUND - B.GAIT[ph]['lift']
            if low != exp: fails.append(f'F{f} {side} ground {low}!={exp}')
            if B.GAIT[ph]['lift'] == 0 and low48 != 61: fails.append(f'F{f} {side} ground48 {low48}')
    pm67 = json.loads((a.prev / 'build_meta.json').read_text())
    same = all(pm67['frames'][f][s][k] == meta['frames'][f][s][k] for f in range(6) for s in ('near', 'far') for k in ('hip', 'knee', 'ankle'))
    rep['gait_identical_to_67'] = same
    if not same: fails.append('gait changed')
    # secondary motion loop: per part, offset change between consecutive frames (incl. F05->F00) <= 1 px
    loop = {}
    for n, sm_ in D.SECONDARY_MOTION.items():
        steps = [max(abs(sm_['dx'][(i + 1) % 6] - sm_['dx'][i]), abs(sm_['dy'][(i + 1) % 6] - sm_['dy'][i])) for i in range(6)]
        loop[n] = steps
        if max(steps) > 1: fails.append(f'{n} jumps {steps}')
    rep['secondary_motion_step_px'] = loop
    rep['secondary_motion'] = D.SECONDARY_MOTION
    rep['z_order'] = D.Z
    rep['mask_pixels'] = meta['mask_pixels']
    rep['frame_art_patches'] = {'96': D.FRAME_ART_PATCHES, '48': D.FRAME_ART_PATCHES_48}
    rep['not_animated'] = {'vest_fabric': 'its lower edge overlaps the protected plaid; moving it would cover protected skirt pixels',
                           'chain': 'UNVERIFIED: at 96x128 the chain cannot be separated from the gold stripes of the protected plaid'}
    rep['fails'] = fails
    rep['technical_qa'] = 'PASS' if not fails else 'FAIL'
    rep['art_qa'] = 'SELF_CHECK_ONLY / THIRD_PARTY_REQUIRED'
    rep['android'] = 'NOT_RUN'; rep['production'] = 'NOT_APPLIED'
    (a.out / 'QA_REPORT.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
    gif = []
    for img in frames:
        bg = Image.new('RGBA', (96, 128), (164, 184, 150, 255)); bg.alpha_composite(Image.fromarray(img))
        gif.append(bg.convert('RGB').resize((288, 384), Image.NEAREST).convert('P', palette=Image.ADAPTIVE, colors=255))
    gif[0].save(a.out / 'morwen_right_walk_68.gif', save_all=True, append_images=gif[1:], duration=125, loop=0, disposal=2)

    def b64(p): return 'data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode()
    html = HTML.replace('MORWEN-PIXEL-66', 'MORWEN-PIXEL-68').replace('旧版 65B', '前版 67').replace('旧版: 65B', '前版: 67') \
        .replace('新版: 脚・ブーツを歩行周期から再構築。', '新版: 67の歩行を維持し、ニーソックス構成・脚の造形・衣装の二次動作を追加。')
    html = html.replace('__F96__', json.dumps([b64(a.out / f'morwen_right_walk_{f:02d}_96x128.png') for f in range(6)])) \
        .replace('__F48__', json.dumps([b64(a.out / f'morwen_right_walk_{f:02d}_48x64.png') for f in range(6)])) \
        .replace('__OLD__', json.dumps([b64(a.prev / f'morwen_right_walk_{f:02d}_96x128.png') for f in range(6)]))
    (a.out / 'android_motion_qa.html').write_text(html, encoding='utf-8')
    print(json.dumps({'technical_qa': rep['technical_qa'], 'fails': fails, 'gait_identical_to_67': same,
                      'protected': [fr['protected'] for fr in rep['frames']], 'costume': [fr['costume'] for fr in rep['frames']]}, indent=1))
    if any('PROTECTED' in x for x in fails): sys.exit(2)


if __name__ == '__main__':
    main()

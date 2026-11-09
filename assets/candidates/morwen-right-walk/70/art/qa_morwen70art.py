#!/usr/bin/env python3
"""QA for ART-70A/B/C (reuses build_morwen70art + 68/70 masks).
  python3 qa_morwen70art.py --source <65B> --c70 <70 dir> --out <art dir> [--repo <repo>]
"""
import argparse, json, hashlib, sys
from pathlib import Path
import numpy as np
from PIL import Image
import build_morwen66 as B
import build_morwen67 as C
import build_morwen68 as D
import build_morwen70art as A
from qa_morwen66 import components
from noise70 import isolated


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(d, f, s): return np.array(Image.open(Path(d) / f'morwen_right_walk_{f:02d}_{s}.png').convert('RGBA'))


def main():
    ap = argparse.ArgumentParser()
    for k in ('source', 'c70', 'out'): ap.add_argument('--' + k, type=Path, required=True)
    ap.add_argument('--repo', type=Path)
    a = ap.parse_args()
    ref, _ = B.load_reference(a.source / 'morwen_right_walk_00_96x128.png')
    uf, ub, _ = B.split_layers(ref); masks = D.region_masks(uf, ub)
    yy, xx = np.mgrid[0:B.H, 0:B.W]
    rep = {'task': 'MORWEN-PIXEL-70 ART pass', 'variants': {}, 'scope_note': 'no body/chest motion added; collar/ribbon keep the 68 1-frame-lag cloth motion'}
    fails = []
    for v in ('A', 'B', 'C'):
        d = a.out / f'ART-70{v}'
        A.build(a.source, d, v)
        R = {'frames': []}
        for f in range(6):
            e = {'frame': f}; bob = B.BOB[f]
            for s in ('96x128', '48x64'):
                p = d / f'morwen_right_walk_{f:02d}_{s}.png'; im = Image.open(p); arr = np.array(im)
                ok = im.mode == 'RGBA' and im.size == ((96, 128) if s == '96x128' else (48, 64))
                rgb0 = bool(np.all(arr[arr[:, :, 3] == 0, :3] == 0)); binary = bool(np.isin(arr[:, :, 3], (0, 255)).all())
                stray = components(arr[:, :, 3] > 0)[1:]
                e[s] = {'ok': ok and rgb0 and binary and not stray, 'sha256': sha(p)}
                if not e[s]['ok']: fails.append(f'{v} F{f} {s} format')
            img, i70 = load(d, f, '96x128'), load(a.c70, f, '96x128')
            # protected (immutable + skirt/torso/bag/hand) vs 70 output (same positions)
            prot = np.zeros(img.shape[:2], bool)
            for k in ('immutable_details', 'skirt', 'torso', 'accessories_fixed'):
                prot |= B.shift(np.repeat(masks[k][:, :, None], 4, 2).astype(np.uint8) * 255, 0, bob)[:, :, 3] > 0
            visible70 = prot & np.all(img[:, :, 3:] > 0, axis=2)
            pdiff = visible70 & np.any(img != i70, axis=2)
            imm = B.shift(np.repeat(masks['immutable_details'][:, :, None], 4, 2).astype(np.uint8) * 255, 0, bob)[:, :, 3] > 0
            e['protected_changed_vs_70'] = int(pdiff.sum()); e['immutable_changed_vs_70'] = int((pdiff & imm).sum())
            if v != 'C' and e['protected_changed_vs_70']: fails.append(f'{v} F{f} protected changed')
            dd = np.any(img != i70, axis=2)
            e['changed_vs_70'] = {'total': int(dd.sum()), 'boots_y>=96_x>=40': int((dd & (yy >= 96) & (xx >= 40)).sum()),
                                  'mantle_cape': int((dd & ~prot & ~((yy >= 88) & (xx >= 40))).sum()), 'protected': int(pdiff.sum()),
                                  'changed_48': int(np.any(load(d, f, '48x64') != load(a.c70, f, '48x64'), axis=2).sum())}
            e['isolated_1px'] = {'all': isolated(img), 'mantle': isolated(img, (xx <= 41) & (yy >= 64)),
                                 '70_all': isolated(i70), '70_mantle': isolated(i70, (xx <= 41) & (yy >= 64))}
            mm = (xx <= 41) & (yy >= 64) & (img[:, :, 3] > 0) & A.is_gold(img[:, :, :3])
            e['mantle_gold_distinct_colours'] = int(len(np.unique(img[mm][:, :3], axis=0)))
            R['frames'].append(e)
            if v == 'C':
                vis = img.copy(); vis[..., :3] //= 3; vis[..., 3] = 255; vis[pdiff] = (255, 0, 0, 255)
                Image.fromarray(vis).resize((288, 384), Image.NEAREST).save(d / f'PROPOSAL_DIFF_F{f:02d}.png')
        m70 = json.loads((a.c70 / 'build_meta.json').read_text()); mv = json.loads((d / 'build_meta.json').read_text())
        R['gait_identical_to_70'] = all(m70['frames'][f][s][k] == mv['frames'][f][s][k] for f in range(6) for s in ('near', 'far') for k in ('hip', 'knee', 'ankle'))
        R['secondary_motion_identical_to_70'] = m70['secondary_motion'] == mv['secondary_motion']
        if not (R['gait_identical_to_70'] and R['secondary_motion_identical_to_70']): fails.append(f'{v} motion changed')
        sil = [load(d, f, '96x128')[:, :, 3] > 0 for f in range(6)]
        s70 = [load(a.c70, f, '96x128')[:, :, 3] > 0 for f in range(6)]
        R['silhouette_equal_to_70'] = [bool((sil[f] == s70[f]).all()) for f in range(6)]
        if not all(R['silhouette_equal_to_70']): fails.append(f'{v} silhouette changed')
        R['buckle_96'] = [mv['frames'][f].get('garter_px_96') and None for f in range(6)]
        rep['variants'][f'ART-70{v}'] = R
    if a.repo:
        rep['master_v3_sha256'] = sha(a.repo / 'assets/companions/morwen/master/morwen-full-body-v3.png')
    rep['gold3'] = {k: list(v) for k, v in A.GOLD3.items()}
    rep['fails'] = fails
    rep['technical_qa'] = 'PASS' if not fails else 'FAIL'
    rep['recommended_candidate'] = 'ART-70B (no protected pixel change); ART-70C = proposal for protected areas, needs approval'
    rep['third_party_art_qa'] = 'NOT_RUN'; rep['android_device_qa'] = 'NOT_RUN'
    (a.out / 'QA_REPORT_ART70.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
    for v in ('A', 'B', 'C'):
        R = rep['variants'][f'ART-70{v}']
        print(v, [fr['changed_vs_70'] for fr in R['frames']][:2], [fr['isolated_1px'] for fr in R['frames']][:1],
              [fr['mantle_gold_distinct_colours'] for fr in R['frames']], [fr['immutable_changed_vs_70'] for fr in R['frames']])
    print(rep['technical_qa'], fails)


if __name__ == '__main__':
    main()

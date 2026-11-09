#!/usr/bin/env python3
"""MORWEN-PIXEL-71 QA (adopted 71 + 4 protected-area proposals).
  python3 qa_morwen71.py --source <65B> --b70 <ART-70B dir> --out <71 dir> [--repo <repo>]
"""
import argparse, json, hashlib, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import build_morwen66 as B
import build_morwen68 as D
import build_morwen71 as M
from qa_morwen66 import components
from noise70 import isolated


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(d, f, s): return np.array(Image.open(Path(d) / f'morwen_right_walk_{f:02d}_{s}.png').convert('RGBA'))
def lum(c): return 0.30 * c[..., 0] + 0.59 * c[..., 1] + 0.11 * c[..., 2]


def protected_mask(masks, f, k=1.0):
    m = np.zeros((128, 96), bool)
    for n in ('immutable_details', 'skirt', 'torso', 'accessories_fixed'): m |= masks[n]
    m = np.roll(m, B.BOB[f], 0)
    return m if k >= 1 else m[1::2, 1::2]


def main():
    ap = argparse.ArgumentParser()
    for k in ('source', 'b70', 'out'): ap.add_argument('--' + k, type=Path, required=True)
    ap.add_argument('--repo', type=Path)
    a = ap.parse_args()
    M.build(a.source, a.out)
    for p in M.PROPOSALS: M.build(a.source, a.out / 'proposals' / p, p)
    ref, _ = B.load_reference(a.source / 'morwen_right_walk_00_96x128.png'); uf, ub, _ = B.split_layers(ref); masks = D.region_masks(uf, ub)
    fails, rep = [], {'task': 'MORWEN-PIXEL-71', 'base': 'ART-70B (director: formal candidate, production not approved)'}
    # ---- adopted 71
    fr = []
    for f in range(6):
        e = {'frame': f}
        for s in ('96x128', '48x64'):
            p = a.out / f'morwen_right_walk_{f:02d}_{s}.png'; im = Image.open(p); arr = np.array(im)
            ok = im.mode == 'RGBA' and im.size == ((96, 128) if s == '96x128' else (48, 64)) and bool(np.all(arr[arr[:, :, 3] == 0, :3] == 0)) \
                and bool(np.isin(arr[:, :, 3], (0, 255)).all()) and not components(arr[:, :, 3] > 0)[1:]
            e[s] = {'ok': ok, 'sha256': sha(p)}
            if not ok: fails.append(f'71 F{f} {s} format')
        for s, kk in (('96x128', 1.0), ('48x64', 0.5)):
            x, b = load(a.out, f, s), load(a.b70, f, s)
            pm = protected_mask(masks, f, kk) & (b[:, :, 3] > 0)
            d = np.any(x != b, axis=2)
            e[f'changed_vs_70B_{s}'] = int(d.sum()); e[f'protected_changed_{s}'] = int((d & pm).sum())
            if (d & pm).any(): fails.append(f'71 F{f} {s} protected changed')
            e[f'silhouette_equal_{s}'] = bool(((x[:, :, 3] > 0) == (b[:, :, 3] > 0)).all())
            if not e[f'silhouette_equal_{s}']: fails.append(f'71 F{f} {s} silhouette')
        fr.append(e)
    rep['adopted_71'] = {'frames': fr}
    m70 = json.loads((a.b70 / 'build_meta.json').read_text()); m71 = json.loads((a.out / 'build_meta.json').read_text())
    rep['adopted_71']['gait_and_motion_identical_to_70B'] = (m70['secondary_motion'] == m71['secondary_motion'] and
        all(m70['frames'][f][s][k] == m71['frames'][f][s][k] for f in range(6) for s in ('near', 'far') for k in ('hip', 'knee', 'ankle')))
    if not rep['adopted_71']['gait_and_motion_identical_to_70B']: fails.append('motion changed')
    # ground rows of planted feet (96: row 124 / 48: row 61)
    grounds = []
    for f in range(6):
        x = load(a.out, f, '96x128'); grounds.append(int(np.where(x[:, :, 3].any(1))[0].max()))
    rep['adopted_71']['lowest_row_96'] = grounds
    # loop / flicker: changed pixels between consecutive frames (48, whole sprite) 70B vs 71
    def consec(d, s):
        return [int(np.any(load(d, f, s) != load(d, (f + 1) % 6, s), axis=2).sum()) for f in range(6)]
    rep['adopted_71']['consecutive_change_48'] = {'70B': consec(a.b70, '48x64'), '71': consec(a.out, '48x64')}
    rep['adopted_71']['consecutive_change_96'] = {'70B': consec(a.b70, '96x128'), '71': consec(a.out, '96x128')}
    # backgrounds: leg edge contrast (lower body rows >= 90)
    bgs = {'light': (238, 234, 226), 'dark': (18, 16, 22)}
    if a.repo:
        for k, fn in (('moss', 'ground_moss.png'), ('dirt', 'ground_mossdirt.png')):
            g = np.array(Image.open(a.repo / 'img/field/moss/art' / fn).convert('RGB')).reshape(-1, 3).mean(0); bgs[k] = tuple(int(v) for v in g)
    def contrast(d):
        out = {}
        for n, c in bgs.items():
            vals = []
            for f in range(6):
                im = load(d, f, '96x128'); op = im[:, :, 3] > 0; nb = np.zeros_like(op)
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): nb |= ~np.roll(np.roll(op, dy, 0), dx, 1)
                edge = op & nb; edge[:90] = False
                vals.append(float(np.abs(lum(im[edge][:, :3].astype(float)) - lum(np.array(c, float))).mean()))
            out[n] = round(float(np.mean(vals)), 1)
        return out
    rep['adopted_71']['leg_edge_contrast'] = {'bg_rgb': bgs, '70B': contrast(a.b70), '71': contrast(a.out)}
    rep['adopted_71']['isolated_1px_all'] = {'70B': [isolated(load(a.b70, f, '96x128')) for f in range(6)], '71': [isolated(load(a.out, f, '96x128')) for f in range(6)]}
    # ---- proposals
    props = {}
    for p in M.PROPOSALS:
        d = a.out / 'proposals' / p; pr = {'status': 'PROPOSAL - NOT ADOPTED (changes protected pixels)', 'frames': []}
        allowed = {'HAT_GOLD': None, 'FLOWER': M.box('flower'), 'GLASSES': M.box('glasses'), 'UPPER_GOLD': None}[p]
        for f in range(6):
            x, b = load(d, f, '96x128'), load(a.out, f, '96x128')
            dd = np.any(x != b, axis=2); pm = protected_mask(masks, f)
            ent = {'frame': f, 'changed_96': int(dd.sum()), 'protected_changed_96': int((dd & pm).sum()),
                   'changed_48': int(np.any(load(d, f, '48x64') != load(a.out, f, '48x64'), axis=2).sum())}
            if allowed is not None:
                ent['outside_box'] = int((dd & ~np.roll(allowed, B.BOB[f], 0)).sum())
                if ent['outside_box']: fails.append(f'{p} F{f} changes outside its box')
            if p in ('HAT_GOLD', 'FLOWER', 'GLASSES'):
                ent['outside_immutable'] = int((dd & ~np.roll(masks['immutable_details'], B.BOB[f], 0)).sum())
            pr['frames'].append(ent)
            if f == 0:
                Image.fromarray((dd * 255).astype(np.uint8), 'L').save(d / 'DIFF_MASK_F00.png')
                S = 6; y0 = 0 if p != 'UPPER_GOLD' else 44; y1 = 48 if p != 'UPPER_GOLD' else 92
                sheet = Image.new('RGBA', (96 * S * 3 + 20, (y1 - y0) * S), (40, 40, 48, 255))
                for i, im in enumerate((b, x)):
                    sheet.alpha_composite(Image.fromarray(im[y0:y1]).resize((96 * S, (y1 - y0) * S), Image.NEAREST), (i * (96 * S + 10), 0))
                vis = x[y0:y1].copy(); vis[..., :3] //= 3; vis[..., 3] = 255; vis[dd[y0:y1]] = (255, 40, 40, 255)
                sheet.alpha_composite(Image.fromarray(vis).resize((96 * S, (y1 - y0) * S), Image.NEAREST), (2 * (96 * S + 10), 0))
                sheet.save(d / f'COMPARE_{p}_F00_71_vs_proposal_vs_diff.png')
        props[p] = pr
    rep['proposals'] = props
    # ---- repo: existing assets unchanged
    if a.repo:
        rep['master_v3_sha256'] = sha(a.repo / 'assets/companions/morwen/master/morwen-full-body-v3.png')
        r = subprocess.run(['git', '-C', str(a.repo), 'status', '--porcelain', '--', 'assets/companions', 'img', 'data',
                            'assets/candidates/morwen-right-walk/right_walk_66', 'assets/candidates/morwen-right-walk/right_walk_67',
                            'assets/candidates/morwen-right-walk/right_walk_68', 'assets/candidates/morwen-right-walk/70'], capture_output=True, text=True)
        rep['existing_assets_modified'] = r.stdout.strip() or 'none'
        if r.stdout.strip(): fails.append('existing assets modified')
        rep['art70B_sha256_F00'] = sha(a.repo / 'assets/candidates/morwen-right-walk/70/art/ART-70B/morwen_right_walk_00_96x128.png')
    rep['fails'] = fails; rep['technical_qa'] = 'PASS' if not fails else 'FAIL'
    rep['third_party_art_qa'] = 'NOT_RUN'; rep['android_device_qa'] = 'NOT_RUN'; rep['production'] = 'NOT_APPLIED'
    (a.out / 'QA_REPORT_71.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
    ch = {f'F{f:02d}': [[int(xx), int(yy)] for yy, xx in zip(*np.where(np.any(load(a.out, f, '96x128') != load(a.b70, f, '96x128'), axis=2)))] for f in range(6)}
    (a.out / 'CHANGED_PIXELS_71_vs_70B.json').write_text(json.dumps({'format': '[x,y] 96x128', 'count': {k: len(v) for k, v in ch.items()}, 'pixels': ch}), encoding='utf-8')
    print(rep['technical_qa'], fails)
    print([e['changed_vs_70B_96x128'] for e in fr], [e['changed_vs_70B_48x64'] for e in fr], grounds)
    print(rep['adopted_71']['leg_edge_contrast'])
    print({p: [(x['changed_96'], x['protected_changed_96'], x.get('outside_box')) for x in v['frames'][:1]] for p, v in props.items()})


if __name__ == '__main__':
    main()

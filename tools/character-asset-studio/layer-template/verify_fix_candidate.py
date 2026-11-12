#!/usr/bin/env python3
"""Verify a correction candidate against a protected canon view (read-only).

usage: verify_fix_candidate.py TEMPLATE VIEW CANDIDATE_PNG [--provenance TEXT]
Exit 0 PASS / 1 FAIL / 2 BLOCKED. Never writes image files.
Diff zones come from template.correctionTargets[view].zonesCanonPx ([x0,y0,x1,y1] in canon pixels).
"""
import argparse, hashlib, json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd

RANK = {'FAIL': 3, 'BLOCKED': 2, 'NOT_RUN': 1, 'PASS': 0}
BLUR = 6                    # box-downsample factor that suppresses resampling/edge noise
DIFF_LEVEL = 20             # mean |RGB| difference counted as a real change after blur
OUTSIDE_LIMIT = 0.02        # max share of figure area changed outside the declared target zones
BG_LIMIT = 0.995            # min share of canon background (eroded 3px) that must be alpha 0 in the candidate


def sha(p):
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def run(template_path, view, cand_path, provenance=None, root='.'):
    with open(template_path, encoding='utf-8') as f:
        t = json.load(f)
    checks = []
    add = lambda n, s, d='': checks.append({'name': n, 'status': s, 'detail': d})
    vw = t['views'][view]
    canon_path = os.path.join(root, vw['canonSource']['path'])
    canon_ok = os.path.isfile(canon_path) and sha(canon_path) == vw['canonSource']['sha256']
    add('canon_sha_protected', 'PASS' if canon_ok else 'FAIL', vw['canonSource']['sha256'][:12])
    target = next((c for c in t.get('correctionTargets', []) if c['view'] == view), None)
    if not os.path.isfile(cand_path):
        add('candidate_present', 'BLOCKED', 'not delivered')
        return finish(view, None, checks)
    csha = sha(cand_path)
    add('candidate_present', 'PASS', csha)
    add('candidate_is_not_canon', 'PASS' if csha != vw['canonSource']['sha256'] else 'FAIL')
    add('provenance', 'PASS' if provenance else 'BLOCKED', provenance or 'producer/source not recorded')
    cim = Image.open(cand_path)
    canon = Image.open(canon_path)
    add('mode_rgba', 'PASS' if cim.mode == 'RGBA' else 'FAIL', cim.mode)
    add('size_matches_canon', 'PASS' if cim.size == canon.size else 'FAIL', f'{cim.size} vs canon {canon.size}')
    a = np.asarray(cim.convert('RGBA'))
    al = a[..., 3].astype(int)
    border = int((al[0] > 0).sum() + (al[-1] > 0).sum() + (al[:, 0] > 0).sum() + (al[:, -1] > 0).sum())
    add('border_alpha_zero', 'PASS' if border == 0 else 'FAIL', f'{border} nonzero border px')
    add('real_transparency', 'PASS' if (al == 0).any() else 'FAIL')
    body = al >= 128
    soft = float(((al >= 128) & (al < 255)).sum() / max(body.sum(), 1))
    add('opaque_body', 'PASS' if soft <= 0.05 else 'FAIL', f'{soft:.1%} of body pixels have alpha 128-254')
    if canon.mode == 'RGB':
        cb = np.asarray(canon).max(2) <= 12
        lab, _ = nd.label(cb)
        edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
        bgm = np.isin(lab, list(edge))
    else:
        bgm = np.asarray(canon.convert('RGBA'))[..., 3] == 0
    bgm = nd.binary_erosion(bgm, iterations=3)
    if bgm.shape != al.shape:
        bgm = np.asarray(Image.fromarray(bgm.astype(np.uint8) * 255).resize(cim.size, Image.NEAREST)) > 0
    clear = float((al[bgm] == 0).mean()) if bgm.any() else 0.0
    add('background_transparent', 'PASS' if clear >= BG_LIMIT else 'FAIL', f'{clear:.2%} of canon background is alpha 0 (min {BG_LIMIT:.1%})')
    rows = np.nonzero(body.any(1))[0]
    sy = canon.size[1] / cim.size[1]
    add('ground_row_canon_px', 'NOT_RUN', f'lowest alpha>=128 row {int(rows[-1]) if len(rows) else None} (x{sy:.4f} to canon px); contact compare needs the view_transforms method')
    # aligned diff on the candidate grid, candidate composited over the canon background (black for RGB canon)
    base = canon.convert('RGB').resize(cim.size, Image.LANCZOS)
    bgc = (0, 0, 0, 255) if canon.mode == 'RGB' else (255, 255, 255, 255)
    over = Image.new('RGBA', cim.size, bgc); over.alpha_composite(cim.convert('RGBA'))
    A = np.asarray(base).astype(float); B = np.asarray(over.convert('RGB')).astype(float)
    ga, gb = A.mean(2), B.mean(2)
    F = np.fft.fft2(ga) * np.conj(np.fft.fft2(gb))
    r = np.fft.ifft2(F / (np.abs(F) + 1e-9)).real
    dy, dx = np.unravel_index(r.argmax(), r.shape)
    H, W = ga.shape
    dy = dy if dy < H // 2 else dy - H; dx = dx if dx < W // 2 else dx - W
    B = np.roll(B, (dy, dx), (0, 1))
    s = (W // BLUR, H // BLUR)
    Ab = np.asarray(Image.fromarray(A.astype(np.uint8)).resize(s, Image.BOX)).astype(float)
    Bb = np.asarray(Image.fromarray(B.astype(np.uint8)).resize(s, Image.BOX)).astype(float)
    d = np.abs(Ab - Bb).mean(2)
    fig = (Ab.mean(2) > 15) | (Bb.mean(2) > 15)
    zone = np.zeros_like(fig)
    zones = (target or {}).get('zonesCanonPx')
    if zones and not (target or {}).get('zonesDeclaredBeforeEdit'):
        add('zones_declared_before_edit', 'FAIL', 'allowed zones must be recorded before the edit')
    if not zones:
        add('target_zones', 'BLOCKED', 'zonesCanonPx not defined for this view')
    else:
        kx, ky = s[0] / canon.size[0], s[1] / canon.size[1]
        for x0, y0, x1, y1 in zones:
            zone[int(y0 * ky):int(y1 * ky) + 1, int(x0 * kx):int(x1 * kx) + 1] = True
        out = fig & ~zone
        share = float(((d > DIFF_LEVEL) & out).sum() / max(out.sum(), 1))
        add('changes_inside_target', 'PASS' if (d[zone] > DIFF_LEVEL).any() else 'FAIL', f'mean {d[zone].mean():.1f}')
        add('no_changes_outside_target', 'PASS' if share <= OUTSIDE_LIMIT else 'FAIL',
            f'{share:.1%} of figure outside target changed (limit {OUTSIDE_LIMIT:.0%}); shift ({dx},{dy})')
    for n in ('design_match_human', 'asymmetry_position_human'):
        add(n, 'NOT_RUN', 'human/director review')
    return finish(view, csha, checks)


def finish(view, csha, checks):
    counts = {k: sum(1 for c in checks if c['status'] == k) for k in RANK}
    overall = max((c['status'] for c in checks), key=lambda s: RANK[s])
    return {'schema': 'cas/fix-candidate-qa/05', 'view': view, 'candidateSha256': csha, 'overall': overall,
            'counts': counts, 'adoptionReady': False,
            'thresholds': {'blur': BLUR, 'diffLevel': DIFF_LEVEL, 'outsideLimit': OUTSIDE_LIMIT, 'backgroundClear': BG_LIMIT}, 'checks': checks}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('template'); ap.add_argument('view'); ap.add_argument('candidate')
    ap.add_argument('--provenance')
    a = ap.parse_args()
    r = run(a.template, a.view, a.candidate, a.provenance)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    sys.exit({'PASS': 0, 'FAIL': 1}.get(r['overall'], 2))

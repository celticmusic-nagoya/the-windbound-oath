#!/usr/bin/env python3
"""MORWEN-LAYER-05 template QA. Read-only. Exit 0 PASS / 1 FAIL / 2 BLOCKED-or-NOT_RUN."""
import hashlib, json, os, sys
import numpy as np
from PIL import Image

VIEWS = ['front', 'back', 'left', 'right']
LAYER_IDS = ['L0', 'L1', 'L2', 'L3']
RANK = {'FAIL': 3, 'BLOCKED': 2, 'NOT_RUN': 1, 'PASS': 0}


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def has_mirrored(o):
    if isinstance(o, dict):
        return o.get('mirrored') is True or any(has_mirrored(v) for v in o.values())
    if isinstance(o, list):
        return any(has_mirrored(v) for v in o)
    return False


def check_layer_png(path, want_sha, canvas):
    if not os.path.isfile(path):
        return 'FAIL', 'file missing'
    if want_sha and sha(path) != want_sha:
        return 'FAIL', 'sha256 mismatch'
    im = Image.open(path)
    if list(im.size) != [canvas['width'], canvas['height']]:
        return 'FAIL', f'size {im.size}'
    if im.mode != 'RGBA':
        return 'FAIL', f'mode {im.mode}'
    a = np.asarray(im)[..., 3]
    if not (a == 0).any():
        return 'FAIL', 'no real transparent pixel'
    if a[0].any() or a[-1].any() or a[:, 0].any() or a[:, -1].any():
        return 'FAIL', 'non-transparent border'
    return 'PASS', 'size/RGBA/alpha ok'


def sole_row(path):
    a = np.asarray(Image.open(path))[..., 3]
    rows = np.nonzero((a >= 128).any(axis=1))[0]
    return int(rows[-1]) if len(rows) else None


def run(template_path, root='.'):
    with open(template_path, encoding='utf-8') as f:
        t = json.load(f)
    checks = []
    add = lambda name, status, detail='': checks.append({'name': name, 'status': status, 'detail': detail})
    cv = t.get('canvas', {})
    add('schema', 'PASS' if t.get('schema') == 'cas/layer-template/05' else 'FAIL', t.get('schema'))
    add('canvas', 'PASS' if (cv.get('width'), cv.get('height')) == (1200, 1600) else 'FAIL', f"{cv.get('width')}x{cv.get('height')}")
    add('views_complete', 'PASS' if sorted(t.get('views', {})) == sorted(VIEWS) else 'FAIL')
    ids = [l['id'] for l in t.get('layers', [])]
    bands = [l['zOrderBand'][0] for l in t.get('layers', [])]
    add('layers_L0_L3', 'PASS' if ids == LAYER_IDS and bands == sorted(bands) and len(set(bands)) == 4 else 'FAIL', ','.join(ids))
    add('no_mirroring', 'FAIL' if has_mirrored(t) else 'PASS')
    g = t.get('ground', {})
    gsrc = g.get('source') or {}
    gp = os.path.join(root, gsrc.get('path', ''))
    add('ground_source_sha', 'PASS' if os.path.isfile(gp) and sha(gp) == gsrc.get('sha256') else 'FAIL', gsrc.get('path'))
    for v in VIEWS:
        vw = t['views'].get(v)
        if not vw:
            continue
        cs = vw['canonSource']
        p = os.path.join(root, cs['path'])
        if not os.path.isfile(p):
            add(f'{v}:canon_sha', 'BLOCKED', 'canon file not present')
        else:
            add(f'{v}:canon_sha', 'PASS' if sha(p) == cs['sha256'] else 'FAIL', cs['sha256'][:12])
            im = Image.open(p)
            add(f'{v}:canon_dims', 'PASS' if list(im.size) == cs['size'] and im.mode == cs['mode'] else 'FAIL', f'{im.size} {im.mode}')
        a, b, c, d, tx, ty = vw['canonToCanvas']['matrix']
        add(f'{v}:transform_uniform_no_shear', 'PASS' if a > 0 and abs(a - d) < 1e-9 and b == 0 and c == 0 else 'FAIL', f'scale={a}')
        ca = vw['canonToCanvas'].get('contactAfterTransform')
        ok = ca and abs(ca[0] - g.get('centerX', -1)) <= 1 and abs(ca[1] - g.get('y', -1)) <= 1
        add(f'{v}:ground_contact', 'PASS' if ok else 'FAIL', str(ca))
    for layer in t.get('layers', []):
        for v in VIEWS:
            slot = layer['views'].get(v) or {}
            img = slot.get('image')
            if not img:
                add(f"{layer['id']}:{v}:image", 'BLOCKED', slot.get('reason', 'NOT_DELIVERED'))
                continue
            st, det = check_layer_png(os.path.join(root, img['path']), img.get('sha256'), cv)
            add(f"{layer['id']}:{v}:image", st, det)
            if st == 'PASS' and layer['id'] == 'L0':
                y = sole_row(os.path.join(root, img['path']))
                add(f'L0:{v}:sole_on_ground', 'PASS' if y is not None and abs(y - g['y']) <= 1 else 'FAIL', str(y))
    anchors = t.get('anchors', {})
    add('joint_anchors', 'BLOCKED' if anchors.get('status') == 'UNRESOLVED' else 'NOT_RUN', anchors.get('status'))
    expected = {'front': 'screen-left', 'back': 'screen-right', 'left': 'near (visible)', 'right': 'far (occluded)'}
    verdicts = {'MATCH', 'MISMATCH', 'NOT_VISIBLE_OCCLUSION_POSSIBLE'}
    for it in t.get('asymmetry', []):
        ok = it.get('characterSide') == 'R' and all(it['views'][v]['expected'] == expected[v] for v in VIEWS)
        add(f"asym:{it['id']}:side_rule", 'PASS' if ok else 'FAIL')
        for v in VIEWS:
            e = it['views'][v]
            if e['verdict'] not in verdicts:
                add(f"asym:{it['id']}:{v}", 'FAIL', 'unknown verdict')
            elif e['verdict'] == 'MATCH':
                add(f"asym:{it['id']}:{v}", 'NOT_RUN', 'AI estimate MATCH; human confirmation pending')
            else:
                add(f"asym:{it['id']}:{v}", 'BLOCKED', e['verdict'])
    for name in ('design_match', 'age_appropriate_expression', 'android_device'):
        add(f'human:{name}', 'NOT_RUN')
    counts = {k: sum(1 for c in checks if c['status'] == k) for k in RANK}
    overall = max((c['status'] for c in checks), key=lambda s: RANK[s])
    return {'schema': 'cas/layer-template-qa/05', 'template': template_path, 'overall': overall, 'counts': counts,
            'adoptionReady': False, 'checks': checks}


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'tools/character-asset-studio/layer-template/morwen.layer-template.json'
    r = run(path)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    sys.exit({'PASS': 0, 'FAIL': 1}.get(r['overall'], 2))

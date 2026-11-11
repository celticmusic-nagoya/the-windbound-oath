#!/usr/bin/env python3
"""Read-only package/PNG QA. Does not fix, rescale, mirror or re-encode images."""
import hashlib
import json
from pathlib import Path
import zipfile
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / 'assets/candidates/morwen-walk-asset-07b'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    registry = json.loads((ROOT / 'data/morwen-hd-canonical-v2.json').read_text())
    manifest = json.loads((BASE / 'PRODUCTION_MANIFEST.json').read_text())
    checks = []
    with zipfile.ZipFile(BASE / 'REFERENCE_PACKAGE.zip') as z:
        for direction in ('front', 'left', 'right', 'back'):
            ref = registry['assets']['pixel.' + direction]
            raw = (ROOT / ref['path']).read_bytes()
            packed = z.read('references/' + direction + '.png')
            checks.append({'id': 'source:' + direction, 'status': 'PASS' if sha(raw) == sha(packed) == ref['sha256'] else 'FAIL', 'sha256': sha(packed)})
        checks.append({'id': 'package:manifest', 'status': 'PASS' if json.loads(z.read('PRODUCTION_MANIFEST.json')) == manifest else 'FAIL'})
        checks.append({'id': 'package:pose-spec', 'status': 'PASS' if z.read('POSE_SPEC.md') == (BASE / 'POSE_SPEC.md').read_bytes() else 'FAIL'})
    frames = manifest['frames']
    required = {'frameId', 'direction', 'pose', 'anatomicalFoot', 'contactPhase', 'stanceId', 'timeMs', 'imagePath', 'imageSHA256', 'anchor'}
    checks.append({'id': 'planned-frame-contract', 'status': 'PASS' if len(frames) == 12 and len({f['frameId'] for f in frames}) == 12 and all(required <= set(f) for f in frames) and all(sum(f['direction'] == d for f in frames) == 6 for d in ('left', 'right')) else 'FAIL'})
    checks.append({'id': 'no-inferred-contact', 'status': 'PASS' if all(f['anchor'] is None and f['worldPx'] is None and f['anatomicalFoot'] is None for f in frames) else 'FAIL'})
    pngs = []
    for path in sorted([*BASE.glob('rejected/*.png'), *BASE.glob('candidates/*.png')]):
        with Image.open(path) as im:
            alpha = im.getchannel('A') if im.mode == 'RGBA' else None
            hist = alpha.histogram() if alpha else None
            pngs.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path.read_bytes()), 'size': list(im.size), 'mode': im.mode,
                         'canvasStatus': 'PASS' if im.size == (1200, 1600) else 'FAIL',
                         'binaryAlphaStatus': 'PASS' if hist and sum(hist[1:255]) == 0 and hist[0] > 0 and hist[255] > 0 else 'FAIL',
                         'transparentPixels': hist[0] if hist else 0,
                         'partialAlphaPixels': sum(hist[1:255]) if hist else None})
    for f in frames:
        if f['imagePath'] is not None:
            checks.append({'id': 'candidate-binding:' + f['frameId'], 'status': 'PASS' if sha((ROOT / f['imagePath']).read_bytes()) == f['imageSHA256'] else 'FAIL'})
    return {'packageStatus': 'PASS' if all(c['status'] == 'PASS' for c in checks) else 'FAIL',
            'productionImageStatus': 'FAIL' if any(p['canvasStatus'] == 'FAIL' or p['binaryAlphaStatus'] == 'FAIL' for p in pngs) else 'NOT_RUN',
            'taskStatus': 'BLOCKED', 'adoptionReady': False, 'export06Allowed': False,
            'checks': checks, 'candidatePngs': pngs,
            'notRun': ['12-frame duplicate comparison and full loop', 'measured anchor/contact QA', 'independent design/asymmetry approval', 'right-facing frame production', 'Android hardware']}


if __name__ == '__main__':
    result = main()
    print(json.dumps(result, indent=2))
    raise SystemExit(2 if result['taskStatus'] == 'BLOCKED' else 0)

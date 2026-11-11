#!/usr/bin/env python3
"""Opt-in frame-data generator. Never draws/reuses PNGs or invents poses.

Inputs are an explicit frame plan and optional SHA-pinned measurements for each
actual PNG. Missing source/measurement/root transform remains unknown. Approval
is human evidence, not inferred from a filename, a still, or a successful hash.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pinned(root, ref):
    if not isinstance(ref, dict) or not isinstance(ref.get('path'), str):
        raise ValueError('missing source reference')
    path = (root / ref['path']).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('source must remain inside repository')
    if not path.is_file() or digest(path) != ref.get('sha256'):
        raise ValueError('source missing or SHA mismatch: ' + ref['path'])
    return path


def number(x):
    return isinstance(x, (float, int)) and not isinstance(x, bool) and math.isfinite(x)


def world_point(point, transform):
    """Image px x-right/y-down -> world px via an explicitly supplied transform."""
    if (not isinstance(point, list) or len(point) != 2 or not all(map(number, point))
            or not isinstance(transform, dict)):
        raise ValueError('explicit local point and actor transform required')
    t, s, angle = (transform.get(k) for k in ('translationPx', 'scale', 'rotationDeg'))
    if (not isinstance(t, list) or len(t) != 2 or not all(map(number, t))
            or not number(s) or s <= 0 or not number(angle)):
        raise ValueError('invalid actor transform')
    a = math.radians(angle)
    x, y = point
    out = [t[0] + s * (x * math.cos(a) - y * math.sin(a)),
           t[1] + s * (x * math.sin(a) + y * math.cos(a))]
    if not all(map(number, out)):
        raise ValueError('nonfinite transformed point')
    return out


def generate(plan, root):
    root = Path(root).resolve()
    if plan.get('schema') != 'cas/motion-source-plan/1.0':
        raise ValueError('unexpected plan schema')
    for ref in plan.get('references', []):
        pinned(root, ref)
    tracks = plan.get('tracks')
    if not isinstance(tracks, dict) or set(tracks) != {'left', 'right'}:
        raise ValueError('explicit left and right tracks required')
    rows, seen = [], set()
    for direction, track in tracks.items():
        frames = track.get('frames')
        if not isinstance(frames, list) or len(frames) != 6:
            raise ValueError('six explicit frame slots required per direction')
        for f in frames:
            fid = f.get('id')
            if not isinstance(fid, str) or not fid or fid in seen:
                raise ValueError('unique string frame IDs required')
            seen.add(fid)
            row = {'id': fid, 'direction': direction, 'sourceFrameId': f.get('sourceFrameId'),
                   'timeMs': f.get('timeMs'), 'image': f.get('image'),
                   'plannedPath': f.get('plannedPath'), 'assetStatus': 'NOT_AVAILABLE',
                   'actorTransform': None, 'measurement': f.get('measurement'),
                   'feet': {side: {'phase': None, 'stanceId': None, 'contactPoint': None,
                                  'localPx': None, 'worldPx': None,
                                  'measurementStatus': 'NOT_MEASURED'} for side in ('L', 'R')},
                   'blockers': []}
            if row['timeMs'] is not None and (not number(row['timeMs']) or row['timeMs'] < 0):
                raise ValueError('invalid authored time')
            if f.get('image') is None:
                row['blockers'].append('NO_ACTUAL_FRAME')
            else:
                from PIL import Image
                with Image.open(pinned(root, f['image'])) as image:
                    if image.format != 'PNG':
                        raise ValueError('actual PNG frame required')
                    row['imageSize'] = list(image.size)
                    image.verify()
                # Approval receipt binds this frame ID, direction and exact PNG.
                receipt_ref = f.get('adoptionReceipt')
                if receipt_ref is None:
                    row['assetStatus'] = 'UNAPPROVED_FRAME'
                    row['blockers'].append('NO_FRAME_ADOPTION_RECEIPT')
                else:
                    receipt = json.loads(pinned(root, receipt_ref).read_text())
                    if (receipt.get('status') != 'DIRECTOR_APPROVED'
                            or receipt.get('frameId') != fid
                            or receipt.get('direction') != direction
                            or receipt.get('image') != f['image']
                            or receipt.get('kind') != 'walk-frame'):
                        raise ValueError('adoption receipt does not bind this walk frame')
                    row['assetStatus'] = 'RECEIPT_BOUND_FRAME'
            if f.get('measurement') is None:
                row['blockers'].append('NO_POSE_CONTACT_MEASUREMENT')
            else:
                m = json.loads(pinned(root, f['measurement']).read_text())
                if (m.get('schema') != 'cas/frame-contact-measurement/1.0'
                        or f.get('image') is None or m.get('image') != f['image']
                        or m.get('frameId') != fid or m.get('direction') != direction
                        or m.get('coordinateSystem') != 'imagePx:x-right:y-down:top-left'
                        or m.get('timeMs') != row['timeMs']):
                    raise ValueError('measurement identity or coordinate mismatch')
                feet = m.get('feet', {})
                if set(feet) != {'L', 'R'}:
                    raise ValueError('anatomical L/R measurements required; no near/far inference')
                transform = m.get('actorTransform')
                if transform is None:
                    row['blockers'].append('NO_ACTOR_TRANSFORM')
                else:
                    world_point([0, 0], transform)  # validate; never supply identity by default
                    row['actorTransform'] = transform
                for side in ('L', 'R'):
                    foot = feet[side]
                    if foot.get('jointId') != f"{foot.get('contactPoint')}{side}":
                        raise ValueError('anatomical joint/side mismatch')
                    if foot.get('phase') not in ('stance', 'swing'):
                        raise ValueError('authored phase required')
                    if foot.get('contactPoint') not in ('heel', 'ball', 'toe'):
                        raise ValueError('selected sole point required')
                    if foot['phase'] == 'stance' and (not isinstance(foot.get('stanceId'), str) or not foot['stanceId']):
                        raise ValueError('authored stanceId required')
                    pt = foot.get('localPx')
                    if pt is not None:
                        world_point(pt, {'translationPx': [0, 0], 'scale': 1, 'rotationDeg': 0})
                    row['feet'][side].update({k: foot.get(k) for k in ('phase', 'stanceId', 'contactPoint', 'localPx')})
                    if pt is None:
                        row['blockers'].append('UNMEASURED_' + side)
                    else:
                        row['feet'][side]['measurementStatus'] = 'SOURCE_RECORDED'
                        if transform is not None:
                            row['feet'][side]['worldPx'] = world_point(pt, transform)
            row['status'] = 'BLOCKED' if row['blockers'] else 'EVIDENCE_BOUND'
            rows.append(row)
    # Receipts bind bytes, not human authority; review is a separate gate.
    return {'schema': 'cas/motion-source-data/1.0', 'rigVersion': plan.get('rigVersion'),
            'status': 'BLOCKED' if any(r['blockers'] for r in rows) else 'REVIEW_REQUIRED',
            'adoptionReady': False, 'export06Allowed': False,
            'coordinateSystem': {'local': 'imagePx:x-right:y-down:top-left',
                                 'world': 'worldPx:x-right:y-down',
                                 'formula': 'world = translationPx + scale * R(rotationDeg) * localPx'},
            'frames': rows}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('plan', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[3])
    args = p.parse_args()
    # Output is a new, task-local JSON only; never overwrite assets or prior QA.
    allowed = args.repo_root.resolve() / 'tools/character-asset-studio/qa/morwen-motion-source-05'
    if not args.output.resolve().is_relative_to(allowed) or args.output.suffix != '.json':
        p.error('output must be new task-local QA JSON')
    result = generate(json.loads(args.plan.read_text()), args.repo_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as f:
        f.write(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'status': result['status'], 'frames': len(result['frames']),
                      'output': str(args.output), 'export06Allowed': False}))
    return 2 if result['status'] == 'BLOCKED' else 0


if __name__ == '__main__':
    raise SystemExit(main())

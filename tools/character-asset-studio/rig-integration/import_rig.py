#!/usr/bin/env python3
"""Read-only Layer0-3 intake/pose adapter. No rendering or automatic adoption."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
from PIL import Image

STUDIO = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('source05_intake', STUDIO / 'motion-source/generate_frame_data.py')
source05 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(source05)
sys.path.insert(0, str(STUDIO / 'qa'))
from convert_real_motion_export import convert
from audit_stance_contact import audit_stance

VIEWS = ('front', 'back', 'left', 'right')
LAYERS = ('L0', 'L1', 'L2', 'L3')
RIG_SIZE, SHEET_SIZE = [1200, 1600], [1536, 1024]


def point(p):
    return isinstance(p, list) and len(p) == 2 and all(source05.number(v) for v in p)


def affine(p, m):
    a, b, c, d, tx, ty = m
    return [a*p[0]+c*p[1]+tx, b*p[0]+d*p[1]+ty]


def intake(data, root):
    root = Path(root).resolve()
    issues, layers = [], []
    def need(ok, code):
        if not ok:
            issues.append(code)
    def pinned(ref, label):
        if ref is None:
            issues.append(label + ':MISSING_SOURCE')
            return None
        try:
            return source05.pinned(root, ref)
        except (ValueError, OSError, TypeError) as exc:
            issues.append(label + ':' + str(exc))
            return None
    need(data.get('schema') == 'cas/rig-import/08', 'SCHEMA')
    need(data.get('characterId') == 'morwen', 'CHARACTER')
    need(data.get('rigSize') == RIG_SIZE and data.get('sheetSize') == SHEET_SIZE, 'COORDINATE_SPACES')
    pinned(data.get('rigSource'), 'RIG')
    pinned(data.get('designSource'), 'DESIGN')
    joints = data.get('joints') or {}
    need(isinstance(joints, dict) and bool(joints), 'JOINTS_MISSING')
    if not isinstance(joints, dict):
        joints = {}
    for jid, joint in joints.items():
        need(joint.get('side') in ('L', 'R', None), 'JOINT_SIDE:' + jid)
        need(joint.get('parent') is None or joint['parent'] in joints, 'PARENT:' + jid)
        if jid.endswith(('L', 'R')):
            need(joint.get('side') == jid[-1], 'JOINT_ID_SIDE:' + jid)
        parent_side = joints.get(joint.get('parent'), {}).get('side')
        need(parent_side is None or joint.get('side') == parent_side, 'PARENT_SIDE:' + jid)
        seen, node = set(), jid
        while node in joints:
            if node in seen:
                issues.append('CYCLE:' + jid)
                break
            seen.add(node)
            node = joints[node].get('parent')
    need(sum(j.get('parent') is None for j in joints.values()) == 1, 'SINGLE_ROOT')
    garter = data.get('attachments', {}).get('rightGarter', {})
    need(garter.get('side') == 'R' and joints.get(garter.get('jointId'), {}).get('side') == 'R'
         and garter.get('layerId') in LAYERS, 'RIGHT_GARTER_ANATOMY')
    entries = data.get('layers', [])
    need([l.get('id') for l in entries] == list(LAYERS), 'LAYER_IDS_ORDER')
    z = [l.get('zOrder') for l in entries]
    need(all(source05.number(v) for v in z) and all(a < b for a, b in zip(z, z[1:])), 'DRAW_ORDER')
    for layer in entries:
        lid = layer.get('id')
        need(layer.get('adoptionStatus') != 'NOT_AVAILABLE', 'LAYER_NOT_AVAILABLE:' + str(lid))
        need(layer.get('adoptionStatus') in ('UNAPPROVED_CANDIDATE', 'DIRECTOR_APPROVED', 'NOT_AVAILABLE'), 'ADOPTION_STATUS:' + str(lid))
        need(set(layer.get('views', {})) == set(VIEWS), 'FOUR_VIEWS:' + str(lid))
        for view in VIEWS:
            v = layer.get('views', {}).get(view, {})
            label = f'{lid}:{view}'
            path = pinned(v.get('image'), label)
            need(v.get('mirrored') is False, label + ':MIRROR_NOT_ALLOWED')
            space, matrix, crop = v.get('space'), None, None
            need(space in ('rigPx', 'sheetPx'), label + ':SPACE')
            if space == 'sheetPx':
                mapping = data.get('viewMappings', {}).get(view)
                if not isinstance(mapping, dict):
                    issues.append(label + ':TRANSFORM_UNRESOLVED')
                else:
                    m, c = mapping.get('matrix'), mapping.get('crop')
                    good_m = isinstance(m, list) and len(m) == 6 and all(source05.number(x) for x in m)
                    good_c = (isinstance(c, list) and len(c) == 4 and all(source05.number(x) for x in c)
                              and c[0] >= 0 and c[1] >= 0 and c[2] > 0 and c[3] > 0
                              and c[0]+c[2] <= SHEET_SIZE[0] and c[1]+c[3] <= SHEET_SIZE[1])
                    need(good_m, label + ':MATRIX')
                    need(good_c, label + ':CROP')
                    if good_m:
                        determinant = m[0]*m[3]-m[1]*m[2]
                        need(determinant > 0, label + ':REFLECTION_OR_SINGULAR')
                        if determinant > 0 and good_c:
                            matrix, crop = m, c
            if path:
                try:
                    with Image.open(path) as image:
                        image.load()
                        expected = RIG_SIZE if space == 'rigPx' else SHEET_SIZE
                        need(image.format == 'PNG' and image.mode == 'RGBA' and list(image.size) == expected and v.get('size') == expected, label + ':PNG_DIMENSIONS_RGBA')
                        if image.mode == 'RGBA':
                            need(image.getchannel('A').getextrema()[0] == 0, label + ':NO_TRANSPARENCY')
                except (OSError, ValueError, RuntimeError) as exc:
                    issues.append(label + ':PNG:' + str(exc))
            coords, anchor = v.get('joints', {}), v.get('anchor')
            need(point(anchor), label + ':ANCHOR_UNKNOWN')
            need(set(coords) == set(joints), label + ':JOINT_IDS')
            need(all(point(p) for p in coords.values()), label + ':JOINT_COORDINATES_UNKNOWN')
            if crop is not None:
                need(all(crop[0] <= p[0] <= crop[0]+crop[2] and crop[1] <= p[1] <= crop[1]+crop[3]
                         for p in [anchor, *coords.values()] if point(p)), label + ':POINT_OUTSIDE_CROP')
            def mapped(p):
                if not point(p):
                    return None
                if space == 'rigPx':
                    return list(p)
                if matrix is None:
                    return None
                # Input sheet coordinates are full-sheet, not crop-local.
                return affine([p[0]-crop[0], p[1]-crop[1]], matrix)
            layers.append({'layerId': lid, 'view': view, 'image': v.get('image'),
                           'adoptionStatus': layer.get('adoptionStatus'), 'zOrder': layer.get('zOrder'),
                           'anchorRigPx': mapped(anchor), 'jointsRigPx': {k: mapped(p) for k, p in coords.items()}})
    # Anchors are measurements, not fixed defaults; all layers of a view must agree.
    for view in VIEWS:
        anchors = [l['anchorRigPx'] for l in layers if l['view'] == view]
        need(bool(anchors) and all(a is not None and a == anchors[0] for a in anchors), 'ANCHOR_ALIGNMENT:' + view)
        positions = [l['jointsRigPx'] for l in layers if l['view'] == view]
        need(bool(positions) and all(p == positions[0] for p in positions), 'LAYER_JOINT_ALIGNMENT:' + view)
    return {'status': 'BLOCKED' if issues else 'PASS', 'issues': issues, 'layers': layers,
            'adoptionReady': False, 'productionReady': False}


def integrate(data, plan, root, tolerance_px=2):
    imported = intake(data, root)
    result = {'schema': 'cas/rig-integration-qa/08', 'import': imported, 'status': 'BLOCKED',
              'adoptionReady': False, 'productionReady': False, 'source05': None, 'stanceAudit': None, 'poses': []}
    if imported['status'] != 'PASS':
        return result
    try:
        frames = source05.generate(plan, root)
    except (ValueError, OSError, TypeError) as exc:
        result['issues'] = ['SOURCE05:' + str(exc)]
        return result
    result['source05'] = frames
    if frames['status'] == 'BLOCKED':
        return result
    issues = []
    for direction, track in plan['tracks'].items():
        previous = -1
        for f in track['frames']:
            pose_ref = f.get('poseInput')
            if pose_ref is None:
                issues.append('POSE_INPUT_MISSING:' + f['id'])
                continue
            try:
                pose = json.loads(source05.pinned(Path(root).resolve(), pose_ref).read_text())
            except (ValueError, OSError, TypeError) as exc:
                issues.append('POSE:' + str(exc))
                continue
            src = next(x for x in frames['frames'] if x['id'] == f['id'])
            if not source05.number(f['timeMs']) or f['timeMs'] <= previous:
                issues.append('POSE_TIME:' + f['id'])
            previous = f['timeMs'] if source05.number(f['timeMs']) else previous
            if (pose.get('schema') != 'cas/rig-pose/08' or pose.get('frameId') != f['id']
                    or pose.get('direction') != direction or pose.get('timeMs') != f['timeMs']
                    or pose.get('space') != 'rigPx' or src.get('imageSize') != RIG_SIZE
                    or pose.get('actorTransform') != src['actorTransform']):
                issues.append('POSE_IDENTITY_TRANSFORM:' + f['id'])
            posed = pose.get('joints', {})
            if set(posed) != set(data['joints']) or not all(point(p) for p in posed.values()):
                issues.append('POSE_JOINTS_UNKNOWN:' + f['id'])
            for side in ('L', 'R'):
                foot = src['feet'][side]
                jid = str(foot['contactPoint']) + side
                if data['joints'].get(jid, {}).get('side') != side or posed.get(jid) != foot['localPx']:
                    issues.append('POSE_CONTACT_SIDE:' + f['id'] + ':' + side)
            result['poses'].append({'frameId': f['id'], 'direction': direction, 'source': pose_ref, 'jointsRigPx': posed})
    if issues:
        result['issues'] = issues
        return result
    audits = {}
    for direction in ('left', 'right'):
        export = {'schema': 'cas/real-motion-contact-export/1.0', 'rigVersion': '1.0',
                  'source': data['rigSource'], 'coordinateSystem': {'units': 'worldPx', 'origin': 'actor-world', 'scale': 1}, 'frames': []}
        for f in frames['frames']:
            if f['direction'] == direction:
                export['frames'].append({'id': f['id'], 'timeMs': f['timeMs'], 'actorTransform': f['actorTransform'],
                    'feet': {s: {**f['feet'][s], 'provenance': f['measurement']['path']} for s in ('L', 'R')}})
        stance = convert(export)
        if stance.get('status') == 'BLOCKED':
            result['issues'] = stance['issues']
            return result
        audit = audit_stance(stance, tolerance_px)
        # Preserve PR225 files; its precision fix is absent from this base.
        maxima = [v for v in audit.get('perFootMaxPx', {}).values() if v is not None]
        if maxima and max(maxima) > tolerance_px:
            audit['status'], audit['maxDriftPx'] = 'FAIL', max(maxima)
        audits[direction] = audit
    result['stanceAudit'] = audits
    statuses = {a['status'] for a in audits.values()}
    result['status'] = 'FAIL' if 'FAIL' in statuses else ('BLOCKED' if 'NOT_RUN' in statuses else 'PASS')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('import_json', type=Path)
    p.add_argument('plan_json', type=Path)
    args = p.parse_args()
    result = integrate(json.loads(args.import_json.read_text()), json.loads(args.plan_json.read_text()), STUDIO.parents[1])
    print(json.dumps(result, indent=2))
    return {'PASS': 0, 'FAIL': 1, 'BLOCKED': 2}[result['status']]


if __name__ == '__main__':
    raise SystemExit(main())

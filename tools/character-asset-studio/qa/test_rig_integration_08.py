"""Synthetic-only integration tests; never edits real PNGs or prior PR inputs."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image

STUDIO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rig08', STUDIO / 'rig-integration/import_rig.py')
rig08 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rig08)


class Integration08Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        im = Image.new('RGBA', (1200, 1600), (20, 30, 40, 255))
        im.putpixel((0, 0), (0, 0, 0, 0))
        im.save(self.root / 'synthetic.png')
        self.image = self.ref('synthetic.png')
        self.coords = {'pelvis': [600, 800], 'heelL': [580, 1540], 'heelR': [620, 1540]}
        self.data = {'schema': 'cas/rig-import/08', 'characterId': 'morwen',
                     'rigSource': self.save('rig.json', {'synthetic': True}),
                     'designSource': self.save('design.json', {'synthetic': True}),
                     'rigSize': [1200, 1600], 'sheetSize': [1536, 1024],
                     'joints': {'pelvis': {'parent': None, 'side': None}, 'heelL': {'parent': 'pelvis', 'side': 'L'}, 'heelR': {'parent': 'pelvis', 'side': 'R'}},
                     'attachments': {'rightGarter': {'side': 'R', 'jointId': 'heelR', 'layerId': 'L1'}}, 'viewMappings': {}, 'layers': []}
        for i, layer in enumerate(rig08.LAYERS):
            self.data['layers'].append({'id': layer, 'zOrder': i*10, 'adoptionStatus': 'UNAPPROVED_CANDIDATE',
                'views': {v: {'image': self.image, 'size': [1200, 1600], 'space': 'rigPx', 'mirrored': False, 'anchor': [600, 1540], 'joints': copy.deepcopy(self.coords)} for v in rig08.VIEWS}})
        self.plan = {'schema': 'cas/motion-source-plan/1.0', 'rigVersion': '1.0', 'tracks': {}}
        for direction in ('left', 'right'):
            frames = []
            for i in range(6):
                fid = f'{direction}_{i}'
                actor = {'translationPx': [0, 0], 'rotationDeg': 0, 'scale': 1}
                feet = {side: {'jointId': 'heel'+side, 'phase': 'stance', 'stanceId': side+'0', 'contactPoint': 'heel', 'localPx': self.coords['heel'+side]} for side in ('L', 'R')}
                m = {'schema': 'cas/frame-contact-measurement/1.0', 'image': self.image, 'frameId': fid, 'direction': direction, 'timeMs': i*100,
                     'coordinateSystem': 'imagePx:x-right:y-down:top-left', 'actorTransform': actor, 'feet': feet}
                receipt = {'kind': 'walk-frame', 'status': 'DIRECTOR_APPROVED', 'image': self.image, 'frameId': fid, 'direction': direction}
                pose = {'schema': 'cas/rig-pose/08', 'frameId': fid, 'direction': direction, 'timeMs': i*100, 'space': 'rigPx', 'actorTransform': actor, 'joints': self.coords}
                frames.append({'id': fid, 'timeMs': i*100, 'image': self.image,
                               'measurement': self.save(fid+'-measurement.json', m), 'adoptionReceipt': self.save(fid+'-receipt.json', receipt), 'poseInput': self.save(fid+'-pose.json', pose)})
            self.plan['tracks'][direction] = {'frames': frames}

    def ref(self, name):
        return {'path': name, 'sha256': hashlib.sha256((self.root/name).read_bytes()).hexdigest()}

    def save(self, name, data):
        (self.root/name).write_text(json.dumps(data))
        return self.ref(name)

    def result(self):
        return rig08.integrate(self.data, self.plan, self.root)

    def test_synthetic_pipeline_pass_never_adopts(self):
        r = self.result()
        self.assertEqual(r['status'], 'PASS')
        self.assertEqual(len(r['poses']), 12)
        self.assertEqual(r['stanceAudit']['left']['perFootMaxPx'], {'L': 0.0, 'R': 0.0})
        self.assertFalse(r['productionReady'])
        self.assertFalse(r['adoptionReady'])

    def test_right_garter_cannot_move_to_left(self):
        self.data['attachments']['rightGarter']['jointId'] = 'heelL'
        self.assertIn('RIGHT_GARTER_ANATOMY', self.result()['import']['issues'])

    def test_mirror_forbidden(self):
        self.data['layers'][0]['views']['left']['mirrored'] = True
        self.assertEqual(self.result()['status'], 'BLOCKED')

    def test_sha_mismatch(self):
        self.data['layers'][0]['views']['front']['image'] = {'path': 'synthetic.png', 'sha256': '0'*64}
        self.assertEqual(self.result()['status'], 'BLOCKED')

    def test_missing_joint_coordinate(self):
        self.data['layers'][0]['views']['front']['joints']['heelL'] = None
        r = self.result()
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertIsNone(r['import']['layers'][0]['jointsRigPx']['heelL'])

    def test_drawing_order(self):
        self.data['layers'][2]['zOrder'] = 0
        self.assertIn('DRAW_ORDER', self.result()['import']['issues'])

    def test_parent_cycle(self):
        self.data['joints']['pelvis']['parent'] = 'heelR'
        self.assertEqual(self.result()['status'], 'BLOCKED')

    def test_unknown_sheet_transform(self):
        self.data['layers'][0]['views']['front']['space'] = 'sheetPx'
        r = self.result()
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertIsNone(r['import']['layers'][0]['anchorRigPx'])

    def test_explicit_sheet_conversion(self):
        image = Image.new('RGBA', (1536, 1024), (40, 20, 30, 255))
        image.putpixel((0, 0), (0, 0, 0, 0))
        image.save(self.root/'sheet.png')
        for layer in self.data['layers']:
            v = layer['views']['front']
            v.update(space='sheetPx', image=self.ref('sheet.png'), size=[1536, 1024], anchor=[150, 200],
                     joints={k: [p[0]/2+100, p[1]/2+50] for k, p in self.coords.items()})
            v['anchor'] = [400, 820]
        self.data['viewMappings']['front'] = {'crop': [100, 50, 600, 800], 'matrix': [2, 0, 0, 2, 0, 0]}
        r = rig08.intake(self.data, self.root)
        self.assertEqual(r['status'], 'PASS')
        self.assertEqual(r['layers'][0]['anchorRigPx'], [600, 1540])

    def test_reflection_matrix_blocked(self):
        self.data['layers'][0]['views']['front']['space'] = 'sheetPx'
        self.data['viewMappings']['front'] = {'crop': [0, 0, 500, 800], 'matrix': [-1, 0, 0, 1, 0, 0]}
        self.assertEqual(self.result()['status'], 'BLOCKED')

    def test_pose_left_right_contact_inversion(self):
        f = self.plan['tracks']['left']['frames'][0]
        pose = json.loads((self.root/f['poseInput']['path']).read_text())
        pose['joints']['heelL'], pose['joints']['heelR'] = pose['joints']['heelR'], pose['joints']['heelL']
        f['poseInput'] = self.save('swapped.json', pose)
        self.assertEqual(self.result()['status'], 'BLOCKED')

    def test_missing_actor_transform(self):
        f = self.plan['tracks']['left']['frames'][0]
        m = json.loads((self.root/f['measurement']['path']).read_text())
        m['actorTransform'] = None
        f['measurement'] = self.save('missing-actor.json', m)
        self.assertEqual(self.result()['status'], 'BLOCKED')

    def slide(self, delta):
        f = self.plan['tracks']['left']['frames'][1]
        for field in ('measurement', 'poseInput'):
            d = json.loads((self.root/f[field]['path']).read_text())
            d['actorTransform']['translationPx'][0] += delta
            f[field] = self.save('slide-'+field+'.json', d)
        return self.result()

    def test_actual_synthetic_sliding_fails(self):
        r = self.slide(5)
        self.assertEqual(r['status'], 'FAIL')
        self.assertEqual(r['stanceAudit']['left']['perFootMaxPx']['L'], 5)

    def test_subprecision_drift_fails_without_editing_pr225(self):
        self.assertEqual(self.slide(2.0000001)['status'], 'FAIL')

    def test_pose_missing_stays_blocked(self):
        self.plan['tracks']['left']['frames'][0]['poseInput'] = None
        self.assertEqual(self.result()['status'], 'BLOCKED')


if __name__ == '__main__':
    unittest.main()

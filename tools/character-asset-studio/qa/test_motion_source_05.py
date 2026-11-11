"""Synthetic contract tests; repository plan tests do not claim adopted frames."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

STUDIO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('motion_source05', STUDIO / 'motion-source/generate_frame_data.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class MotionSource05Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.plan = json.loads((STUDIO / 'motion-source/morwen_walk6.source-plan.json').read_text())
        self.plan['references'] = []  # Synthetic fixture has no adopted repository documents.

    def save(self, name, data):
        p = self.root / name
        p.write_text(json.dumps(data))
        return {'path': name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}

    def attach(self, transform=True, approve=True):
        f = self.plan['tracks']['left']['frames'][0]
        # Synthetic PNG, never a production frame or human adoption record.
        from PIL import Image
        image = self.root / 'synthetic.png'
        Image.new('RGBA', (8, 8), (0, 0, 0, 0)).save(image)
        f['image'] = {'path': image.name, 'sha256': hashlib.sha256(image.read_bytes()).hexdigest()}
        f['timeMs'] = 0
        if approve:
            f['adoptionReceipt'] = self.save('receipt.json', {'status': 'DIRECTOR_APPROVED', 'kind': 'walk-frame', 'frameId': f['id'], 'direction': 'left', 'image': f['image']})
        m = {'schema': 'cas/frame-contact-measurement/1.0', 'frameId': f['id'], 'direction': 'left', 'timeMs': 0, 'image': f['image'], 'coordinateSystem': 'imagePx:x-right:y-down:top-left', 'actorTransform': {'translationPx': [100, 200], 'scale': 2, 'rotationDeg': 0} if transform else None, 'feet': {s: {'jointId': 'heel'+s, 'contactPoint': 'heel', 'localPx': [3, 4], 'phase': 'stance', 'stanceId': s+'0'} for s in ('L', 'R')}}
        f['measurement'] = self.save('measurement.json', m)
        return f, m

    def test_current_plan_twelve_unknown_slots(self):
        real_plan = json.loads((STUDIO / 'motion-source/morwen_walk6.source-plan.json').read_text())
        data = module.generate(real_plan, STUDIO.parents[1])
        self.assertEqual(len(data['frames']), 12)
        self.assertEqual(data['status'], 'BLOCKED')
        self.assertFalse(data['export06Allowed'])
        for f in data['frames']:
            self.assertIsNone(f['timeMs'])
            self.assertIsNone(f['actorTransform'])
            for foot in f['feet'].values():
                self.assertIsNone(foot['worldPx'])
                self.assertEqual(foot['measurementStatus'], 'NOT_MEASURED')

    def test_explicit_transform_computes_synthetic_contact(self):
        self.attach()
        f = module.generate(self.plan, self.root)['frames'][0]
        self.assertEqual(f['feet']['L']['worldPx'], [106, 208])
        self.assertEqual(f['assetStatus'], 'RECEIPT_BOUND_FRAME')

    def test_transform_not_defaulted(self):
        self.attach(transform=False)
        f = module.generate(self.plan, self.root)['frames'][0]
        self.assertIsNone(f['feet']['L']['worldPx'])
        self.assertIn('NO_ACTOR_TRANSFORM', f['blockers'])

    def test_rotation_and_scale_coordinate_convention(self):
        p = module.world_point([1, 0], {'translationPx': [10, 20], 'scale': 3, 'rotationDeg': 90})
        self.assertAlmostEqual(p[0], 10)
        self.assertAlmostEqual(p[1], 23)

    def test_missing_measurement_never_uses_ground_marker(self):
        self.plan['ground'] = [600, 1540]
        f = module.generate(self.plan, self.root)['frames'][0]
        self.assertIsNone(f['feet']['L']['worldPx'])

    def test_changed_source_hash_rejected(self):
        f, _ = self.attach()
        (self.root / f['image']['path']).write_text('changed')
        with self.assertRaises(ValueError):
            module.generate(self.plan, self.root)

    def test_no_receipt_does_not_adopt_frame(self):
        self.attach(approve=False)
        f = module.generate(self.plan, self.root)['frames'][0]
        self.assertEqual(f['assetStatus'], 'UNAPPROVED_FRAME')
        self.assertEqual(f['status'], 'BLOCKED')

    def test_left_right_joint_inversion_rejected(self):
        f, m = self.attach()
        m['feet']['L']['jointId'] = 'heelR'
        f['measurement'] = self.save('measurement.json', m)
        with self.assertRaisesRegex(ValueError, 'side mismatch'):
            module.generate(self.plan, self.root)

    def test_measurement_bound_to_frame_image_time(self):
        f, m = self.attach()
        for key, bad in [('frameId', 'other'), ('timeMs', 100), ('direction', 'right')]:
            changed = copy.deepcopy(m)
            changed[key] = bad
            f['measurement'] = self.save('measurement.json', changed)
            with self.assertRaisesRegex(ValueError, 'identity'):
                module.generate(self.plan, self.root)

    def test_unmeasured_contact_remains_null(self):
        f, m = self.attach()
        m['feet']['R']['localPx'] = None
        f['measurement'] = self.save('measurement.json', m)
        out = module.generate(self.plan, self.root)['frames'][0]
        self.assertIsNone(out['feet']['R']['worldPx'])
        self.assertIn('UNMEASURED_R', out['blockers'])

    def test_nonfinite_transform_rejected(self):
        with self.assertRaises(ValueError):
            module.world_point([1, 2], {'translationPx': [0, 0], 'scale': float('nan'), 'rotationDeg': 0})

    def test_duplicate_frame_ids_rejected(self):
        self.plan['tracks']['right']['frames'][0]['id'] = 'left_F1'
        with self.assertRaises(ValueError):
            module.generate(self.plan, self.root)


if __name__ == '__main__':
    unittest.main()

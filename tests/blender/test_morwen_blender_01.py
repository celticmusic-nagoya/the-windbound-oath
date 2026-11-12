import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('morwen_prepare',ROOT/'tools/blender/morwen_blender_01/prepare.py')
prepare=importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class MorwenCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary=tempfile.TemporaryDirectory()
        cls.data=prepare.prepare(Path(cls.temporary.name))

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_adapter_keeps_unmeasured_candidate_status(self):
        self.assertFalse(prepare.validate_candidate(self.data))
        self.assertEqual(len(self.data['facings']),4)
        self.assertEqual(self.data['status'],'PIXEL_REFINED_VISUAL_CANDIDATE_UNREVIEWED')

    def test_rejects_fake_measured_claim(self):
        d=copy.deepcopy(self.data);d['status']='MEASURED_CANDIDATE_UNREVIEWED'
        self.assertTrue(prepare.validate_candidate(d))

    def test_anatomical_sides_differ_front_and_back(self):
        d=copy.deepcopy(self.data)
        p=d['facings']['front']['rig_points_pixels']
        p['shoulder.L'],p['shoulder.R']=p['shoulder.R'],p['shoulder.L']
        self.assertTrue(prepare.validate_candidate(d))

    def test_hidden_joint_must_remain_inferred(self):
        d=copy.deepcopy(self.data)
        d['facings']['right']['anchors']['shoulder.L']['visibility']='VISIBLE_VISUAL_ESTIMATE'
        self.assertTrue(prepare.validate_candidate(d))

    def test_profile_near_side_is_not_screen_side(self):
        d=copy.deepcopy(self.data);d['facings']['left']['near_side']='R'
        self.assertTrue(prepare.validate_candidate(d))

    def test_rejects_nan_and_wrong_aspect(self):
        d=copy.deepcopy(self.data);d['facings']['front']['rig_points_pixels']['pelvis'][0]=float('nan')
        self.assertTrue(prepare.validate_candidate(d))
        d=copy.deepcopy(self.data);d['facings']['front']['dimensions']=[1024,384]
        self.assertTrue(prepare.validate_candidate(d))

    def test_shared_scale_and_projection_aspect(self):
        self.assertEqual(self.data['calibration']['height_spread_px'],1)
        self.assertTrue(self.data['calibration']['shared_pixel_scale'])
        self.assertFalse(self.data['calibration']['image_resizing'])
        for entry in self.data['facings'].values():
            bones=prepare.bone_points(entry['rig_points_pixels'],entry['measured_ground_y'])
            self.assertEqual(len(bones),17)
            self.assertTrue(all(a!=b for a,b in bones.values()))

    def test_source_tampering_is_rejected(self):
        import json
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);receipt=root/'tools/blender/morwen_blender_01/SOURCE_RECEIPT.json'
            receipt.parent.mkdir(parents=True)
            receipt.write_text(json.dumps({'files':[{'path':'source.png','sha256':'0'*64}]}))
            (root/'source.png').write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError,'Source SHA mismatch'):
                prepare.verify_sources(root)


if __name__=='__main__':
    unittest.main()

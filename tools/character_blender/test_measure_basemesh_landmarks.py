#!/usr/bin/env python3
"""No-Blender regression tests for the evidence-gated anatomical measurement calculator."""
import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).with_name("measure_basemesh_landmarks.py")
spec=importlib.util.spec_from_file_location("landmarks",p)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
KEYS=module.KEYS
class LandmarkTests(unittest.TestCase):
    def test_missing_values_remain_blocked(self):
        result=module.analyze({"reviewer_confirmed":False,"landmarks":dict.fromkeys(KEYS)})
        self.assertEqual(result["status"],"BLOCKED_UNCONFIRMED_LANDMARKS")
        self.assertEqual(len(result["missing"]),len(KEYS))
    def test_unreviewed_complete_values_remain_blocked(self):
        result=module.analyze({"reviewer_confirmed":False,"landmarks":{k:0.0 for k in KEYS}})
        self.assertEqual(result["status"],"BLOCKED_UNCONFIRMED_LANDMARKS")
    def test_reviewed_synthetic_geometry(self):
        pts=dict(zip(KEYS,[1.55,1.35,1.27,0.92,0.82,0.70,0.39,0.09,0.0]))
        result=module.analyze({"reviewer_confirmed":True,"landmarks":pts})
        self.assertEqual(result["status"],"PASS_REVIEWER_LANDMARK_MEASUREMENT_ONLY")
        self.assertAlmostEqual(result["head_count"],7.75)
        self.assertTrue(result["head_count_within_target"])
    def test_invalid_head(self):
        pts=dict(zip(KEYS,[1.0,1.0,0.8,0.7,0.6,0.5,0.3,0.1,0.0]))
        result=module.analyze({"reviewer_confirmed":True,"landmarks":pts})
        self.assertEqual(result["status"],"FAIL_INVALID_HEAD_OR_HEIGHT")
if __name__=="__main__":unittest.main()

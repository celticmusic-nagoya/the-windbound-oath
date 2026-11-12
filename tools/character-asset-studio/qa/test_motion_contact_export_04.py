"""Export-04 contract checks. All moving points below are SYNTHETIC tests.

No test here establishes actual animation correctness or provenance authenticity.
"""
import copy
import json
from pathlib import Path
import unittest

from audit_stance_contact import audit_stance
from convert_real_motion_export import convert
from test_validate_real_motion_export import valid
from validate_real_motion_export import validate


class Export04Tests(unittest.TestCase):
    def test_static_v10_rig_is_not_an_animated_contact_export(self):
        path = Path(__file__).resolve().parents[1] / "layer0/morwen-master-v1.0/MASTER_BODY_SPEC.v1.0.candidate.json"
        report = validate(json.loads(path.read_text()))
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("FRAMES", report["issues"])

    def test_missing_source_transform_blocks_conversion(self):
        data = valid()
        del data["frames"][0]["actorTransform"]
        self.assertEqual(convert(data)["status"], "BLOCKED")

    def test_missing_selected_contact_point_blocks(self):
        data = valid()
        del data["frames"][0]["feet"]["L"]["contactPoint"]
        self.assertIn("FRAME_0_L_POINT", validate(data)["issues"])
        self.assertEqual(convert(data)["status"], "BLOCKED")

    def test_swapped_lr_provenance_exposes_authenticity_gap(self):
        # Existing validator is structural only: nonempty strings do not prove
        # anatomical identity. Record this limitation rather than invent evidence.
        data = valid()
        feet = data["frames"][0]["feet"]
        feet["L"]["provenance"], feet["R"]["provenance"] = feet["R"]["provenance"], feet["L"]["provenance"]
        self.assertEqual(validate(data)["status"], "PASS")
        self.assertIn("rig:R", feet["L"]["provenance"])

    def test_synthetic_drift_over_tolerance_reaches_auditor(self):
        data = valid()
        second = copy.deepcopy(data["frames"][0])
        second.update(id="f1", timeMs=100)
        second["feet"]["L"]["worldPx"][0] += 5
        data["frames"].append(second)
        self.assertEqual(validate(data)["status"], "PASS")
        report = audit_stance(convert(data), 2)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["perFootMaxPx"]["L"], 5)

    def test_stance_switch_without_swing_blocks(self):
        data = valid()
        second = copy.deepcopy(data["frames"][0])
        second.update(id="f1", timeMs=100)
        second["feet"]["L"]["stanceId"] = "L1"
        data["frames"].append(second)
        self.assertEqual(convert(data)["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()

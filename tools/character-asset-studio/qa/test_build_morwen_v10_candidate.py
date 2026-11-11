"""Regression tests for non-destructive Morwen v1.0 candidate migration."""
import copy
import unittest
from build_morwen_v10_candidate import build


def fixture():
    return {
        "version": "0.9-articulated",
        "status": "UNAPPROVED_CANDIDATE",
        "anchor": {"px": [600, 1540]},
        "joints3d": {"pelvis": [0, 744, 0], "ground": [0, 1540, 0],
                     "hipL": [50, 744, 0], "hipR": [-50, 744, 0]},
        "kinematicTree": {"ground": "pelvis", "hipL": "pelvis", "hipR": "pelvis"},
        "ageCategory": "minor", "bodyGuidePolicy": "minor_neutral_structure"
    }


class MigrationTests(unittest.TestCase):
    def test_source_immutable_and_coordinates_preserved(self):
        src = fixture()
        before = copy.deepcopy(src)
        out = build(src)
        self.assertEqual(src, before)
        self.assertEqual(out["joints3d"], src["joints3d"])
        self.assertNotIn("ground", out["kinematicTree"])
        self.assertEqual(out["kinematicTree"]["hipL"], "pelvis")

    def test_world_anchor_and_metadata(self):
        out = build(fixture())
        self.assertEqual(out["worldAnchors"]["ground"]["px"], [600, 1540])
        self.assertFalse(out["worldAnchors"]["ground"]["followsRig"])
        self.assertEqual(out["ageYears"], 18)
        self.assertEqual(out["ageCategory"], "adult")
        self.assertEqual(out["finalAdoption"], "NOT_RUN")

    def test_unexpected_source_rejected(self):
        for field, value in (("version", "0.8"), ("status", "APPROVED")):
            with self.subTest(field=field):
                src = fixture()
                src[field] = value
                with self.assertRaises(ValueError):
                    build(src)


if __name__ == "__main__":
    unittest.main()

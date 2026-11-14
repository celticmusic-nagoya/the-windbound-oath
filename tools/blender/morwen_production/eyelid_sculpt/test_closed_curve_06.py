"""Unit checks for the non-canonical EYELID-06 art-target proposal."""
import importlib.util
import json
import math
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "_qa" / "eyelid_retopo_05" / "EYE_TARGETS_05.json"
spec = importlib.util.spec_from_file_location("curve06", HERE / "propose_closed_curve_06.py")
curve = importlib.util.module_from_spec(spec)
spec.loader.exec_module(curve)


class TestCurve06(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(SRC.read_text(encoding="utf-8"))
        cls.target = curve.build_target(cls.source)

    def test_determinism(self):
        self.assertEqual(self.target, curve.build_target(self.source))

    def test_explicitly_not_canon(self):
        self.assertEqual(self.target["status"], "UNREVIEWED_ART_PROPOSAL_NOT_CANON")
        self.assertEqual(self.target["source_sha256"], self.source["source"]["sha256"])

    def test_endpoints_and_sampling(self):
        for side in ("R", "L"):
            pts = self.target["sides"][side]["points"]
            self.assertEqual(len(pts), 33)
            self.assertAlmostEqual(pts[0]["y_px"], self.source["design_coef"][side]["upper_coef"][0])
            self.assertAlmostEqual(pts[-1]["y_px"], self.source["design_coef"][side]["upper_coef"][-1])
            self.assertTrue(all(math.isfinite(p["y_px"]) for p in pts))
            self.assertTrue(all(pts[i]["u"] < pts[i+1]["u"] for i in range(32)))

    def test_reject_invalid_curvature(self):
        for curvature in (-0.1, 2.1):
            with self.assertRaises(ValueError):
                curve.build_target(self.source, curvature_px=curvature)

    def test_reject_invalid_samples(self):
        with self.assertRaises(ValueError):
            curve.build_target(self.source, samples=4)


if __name__ == "__main__":
    unittest.main()

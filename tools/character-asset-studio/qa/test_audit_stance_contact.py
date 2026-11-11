"""Unit tests for the read-only stance-contact auditor."""
import unittest
from audit_stance_contact import audit_stance


def sample(points, side="L"):
    return {"schema": "cas/stance-frames/1.0",
            "frames": [{"id": f"f{i}", "contacts": {side: {"phase": "stance",
                        "worldPx": [x, y]}}} for i, (x, y) in enumerate(points)]}


class ContactTests(unittest.TestCase):
    def test_stable_stance(self):
        result = audit_stance(sample([(100, 200), (101, 200), (101, 201)]), 2)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["stanceSamples"], 3)

    def test_slide_detected(self):
        result = audit_stance(sample([(100, 200), (105, 200)]), 2)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["maxDriftPx"], 5)

    def test_subprecision_slide_cannot_round_to_pass(self):
        result = audit_stance(sample([(0, 0), (2.0000001, 0)]), 2)
        self.assertEqual(result["observations"][-1]["status"], "FAIL")
        self.assertEqual(result["status"], "FAIL")
        self.assertGreater(result["maxDriftPx"], 2)

    def test_exact_tolerance_passes(self):
        self.assertEqual(audit_stance(sample([(0, 0), (2, 0)]), 2)["status"], "PASS")

    def test_new_stance_after_swing_reanchors(self):
        data = sample([(100, 200), (100, 200)])
        data["frames"].insert(1, {"id": "swing", "contacts": {"L": {"phase": "swing"}}})
        data["frames"][2]["contacts"]["L"]["worldPx"] = [200, 200]
        self.assertEqual(audit_stance(data)["status"], "PASS")

    def test_missing_stance_not_run(self):
        self.assertEqual(audit_stance({"schema": "cas/stance-frames/1.0",
                         "frames": [{"contacts": {"L": {"phase": "swing"}}}]})["status"],
                         "NOT_RUN")

    def test_invalid_data_rejected(self):
        with self.assertRaises(ValueError):
            audit_stance(sample([(100, 200), (float("nan"), 200)]))


if __name__ == "__main__":
    unittest.main()

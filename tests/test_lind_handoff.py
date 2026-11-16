import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools/map_blender/validate_lind_handoff.py"
spec = importlib.util.spec_from_file_location("lind_handoff_validator", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def candidate():
    return {
        "schema_version": 1, "lane": "WORLD", "collection": "LIND_TERRAIN",
        "source_image_sha256": mod.SOURCE_SHA,
        "source_commit": "dc17dd4846f35ea1f5dea25168eec9ddb50a3838",
        "generator_version": "test-1", "blender_version": "4.0.2",
        "random_seed": 1001, "art_status": "CANDIDATE",
        "qa_status": {"G1": "BLOCKED", "G2": "NOT_RUN", "G3": "NOT_RUN", "G4": "NOT_RUN"},
        "metric_approval": "BLOCKED", "local_origin": None, "bounding_box_m": None,
        "world_transform": None, "elevation_reference": None,
        "input_hashes": {}, "output_hashes": {}, "dependencies": [], "exclusion_masks": [],
    }


class HandoffContractTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def check(self, d):
        return mod.validate(d, self.root)

    def test_valid_nonmetric_candidate(self):
        self.assertEqual(self.check(candidate()), [])

    def test_reject_wrong_source(self):
        d = candidate()
        d["source_image_sha256"] = "0" * 64
        self.assertTrue(self.check(d))

    def test_reject_wrong_owner(self):
        d = candidate()
        d["collection"] = "LIND_HERO_HOME"
        self.assertTrue(self.check(d))

    def test_reject_fake_g1_pass(self):
        d = candidate()
        d["qa_status"]["G1"] = "PASS"
        self.assertTrue(self.check(d))

    def test_reject_unapproved_metric(self):
        d = candidate()
        d["local_origin"] = [0, 0, 0]
        self.assertTrue(self.check(d))

    def test_reject_traversal(self):
        d = candidate()
        d["output_hashes"] = {"../secrets": "0" * 64}
        self.assertTrue(self.check(d))

    def test_reject_unverified_artifact(self):
        d = candidate()
        d["output_hashes"] = {"render.png": "0" * 64}
        self.assertTrue(self.check(d))

    def test_reject_fake_qa_state(self):
        d = candidate()
        d["qa_status"]["G2"] = "COMPLETE"
        self.assertTrue(self.check(d))


if __name__ == "__main__":
    unittest.main()

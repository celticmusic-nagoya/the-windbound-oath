"""Negative tests for the proposed, non-canonical full-3D interface contract."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools/integration/validate_full3d_interface_v34.py"
spec = importlib.util.spec_from_file_location("full3d_v34", SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def candidate():
    return {
        "contract_version": "v3.4-candidate-1",
        "lane": "WORLD", "asset_id": "lind-terrain-candidate",
        "collection": "LIND_TERRAIN", "status": "candidate",
        "source_commit": "dc17dd4846f35ea1f5dea25168eec9ddb50a3838",
        "source_hashes": {"world": validator.WORLD_SHA},
        "output_hashes": {}, "blender_version": "4.0.2",
        "generator_version": "test-1", "seed": 42,
        "license_provenance": [], "dependencies_on_lanes": [],
        "dependencies": {}, "camera_settings": {}, "render_settings": {},
        "interface_approval": "BLOCKED",
        "qa_gates": {"G1": "BLOCKED", "G2": "NOT_RUN", "G3": "NOT_RUN", "G4": "NOT_RUN"},
        **{key: None for key in validator.UNAPPROVED_FIELDS},
    }


class Full3DInterfaceContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def assert_rejected(self, data):
        self.assertTrue(validator.validate(data, self.root))

    def test_valid_unapproved_candidate(self):
        self.assertEqual(validator.validate(candidate(), self.root), [])

    def test_non_object(self):
        self.assert_rejected([])

    def test_wrong_world_source(self):
        d = candidate()
        d["source_hashes"]["world"] = "0" * 64
        self.assert_rejected(d)

    def test_world_sha_cannot_be_character_source(self):
        d = candidate()
        d["lane"], d["collection"] = "CHARACTER", None
        self.assert_rejected(d)

    def test_character_precedence_is_blocked(self):
        d = candidate()
        d["lane"], d["collection"] = "CHARACTER", None
        d["source_hashes"] = {"morwen": next(iter(validator.CHARACTER_REFERENCES))}
        self.assert_rejected(d)
        d["canon_precedence"] = "BLOCKED"
        self.assertEqual(validator.validate(d, self.root), [])

    def test_cross_lane_collection(self):
        d = candidate()
        d["collection"] = "LIND_HERO_HOME"
        self.assert_rejected(d)

    def test_unapproved_metrics(self):
        d = candidate()
        d["local_origin"] = [0, 0, 0]
        self.assert_rejected(d)

    def test_missing_null(self):
        d = candidate()
        del d["projection_id"]
        self.assert_rejected(d)

    def test_cannot_self_approve_interface(self):
        d = candidate()
        d["interface_approval"] = "APPROVED"
        self.assert_rejected(d)

    def test_fake_g1_pass(self):
        d = candidate()
        d["qa_gates"]["G1"] = "PASS"
        self.assert_rejected(d)

    def test_fake_g2_pass(self):
        d = candidate()
        d["qa_gates"]["G2"] = "PASS"
        self.assert_rejected(d)

    def test_fake_g4_pass(self):
        d = candidate()
        d["qa_gates"]["G4"] = "PASS"
        self.assert_rejected(d)

    def test_approved_asset_status_not_automatically_allowed(self):
        d = candidate()
        d["status"] = "approved"
        self.assert_rejected(d)

    def test_path_traversal(self):
        d = candidate()
        d["output_hashes"] = {"../escape": "0" * 64}
        self.assert_rejected(d)

    def test_symlink_escape(self):
        outside = Path(self.tmp.name).parent / "outside-v34.bin"
        d = candidate()
        d["output_hashes"] = {"link": "0" * 64}
        # An invalid path should fail even when the link is dangling.
        (self.root / "link").symlink_to(outside)
        self.assert_rejected(d)

    def test_missing_output(self):
        d = candidate()
        d["output_hashes"] = {"render.png": "0" * 64}
        self.assert_rejected(d)

    def test_valid_artifact_sha(self):
        (self.root / "render.png").write_bytes(b"candidate")
        d = candidate()
        d["output_hashes"] = {"render.png": hashlib.sha256(b"candidate").hexdigest()}
        self.assertEqual(validator.validate(d, self.root), [])

    def test_invalid_artifact_sha(self):
        (self.root / "render.png").write_bytes(b"candidate")
        d = candidate()
        d["output_hashes"] = {"render.png": "0" * 64}
        self.assert_rejected(d)


if __name__ == "__main__":
    unittest.main()

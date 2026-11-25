"""Negative controls for the non-production 3D handoff contract."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from tools.ai_3d.validate_candidate_handoff import validate


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "model.glb").write_bytes(b"candidate test bytes only")
        self.data = {
            "schema_version": "two-3d-handoff-candidate-v1",
            "lane": "WORLD",
            "status": "candidate",
            "source_commit": "example-commit",
            "source_sha256": "a" * 64,
            "blender_version": "4.0.2",
            "generator_version": "test",
            "random_seed": 0,
            "coordinate_contract": {
                "world_scale_m": None,
                "world_origin": None,
                "camera_projection": None,
                "character_height_m": None,
            },
            "outputs": [{
                "path": "model.glb",
                "sha256": hashlib.sha256(b"candidate test bytes only").hexdigest(),
                "kind": "candidate_glb",
            }],
            "gates": {"G1": "BLOCKED", "G2": "NOT_RUN",
                      "G3": "NOT_RUN", "G4": "NOT_RUN"},
        }

    def check(self):
        path = self.root / "manifest.json"
        path.write_text(json.dumps(self.data), encoding="utf-8")
        return validate(path)

    def test_valid_candidate(self):
        self.assertEqual(self.check(), [])

    def test_rejects_canon_claim(self):
        self.data["status"] = "adopted"
        self.assertTrue(self.check())

    def test_rejects_forged_pass(self):
        self.data["gates"]["G2"] = "PASS"
        self.assertTrue(self.check())

    def test_rejects_unapproved_scale(self):
        self.data["coordinate_contract"]["world_scale_m"] = 1
        self.assertTrue(self.check())

    def test_rejects_hash_mismatch(self):
        self.data["outputs"][0]["sha256"] = "0" * 64
        self.assertTrue(self.check())

    def test_rejects_path_traversal(self):
        self.data["outputs"][0]["path"] = "../outside.glb"
        self.assertTrue(self.check())

    def test_rejects_missing_output(self):
        self.data["outputs"][0]["path"] = "missing.glb"
        self.assertTrue(self.check())


if __name__ == "__main__":
    unittest.main()

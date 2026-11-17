"""Independent unit tests for photo-PBR provenance intake; no real asset downloaded."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from tools.map_blender.lind.validate_photo_pbr_intake import validate

class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.base = b"basecolor-bytes"
        self.rough = b"roughness-bytes"
        (self.root / "base.png").write_bytes(self.base)
        (self.root / "rough.png").write_bytes(self.rough)
        self.m = {
            "asset_status": "candidate",
            "source_url": "https://example.org/asset/1",
            "author": "Example author",
            "license": "CC0",
            "license_evidence_url": "https://example.org/license",
            "capture_location_claim": "unknown",
            "textures": {
                "basecolor": {"path": "base.png", "sha256": hashlib.sha256(self.base).hexdigest(), "color_space": "sRGB"},
                "roughness": {"path": "rough.png", "sha256": hashlib.sha256(self.rough).hexdigest(), "color_space": "Non-Color"}
            }
        }

    def check(self):
        p = self.root / "manifest.json"
        p.write_text(json.dumps(self.m), encoding="utf-8")
        return validate(p)

    def test_valid_candidate_does_not_pass_art(self):
        r = self.check()
        self.assertEqual(r["status"], "INTAKE_PASS_NOT_ART_APPROVED")
        self.assertEqual(r["G2"], "NOT_RUN")

    def test_missing_license_rejected(self):
        self.m["license"] = ""
        self.assertEqual(self.check()["status"], "FAIL")

    def test_irish_provenance_requires_evidence(self):
        self.m["capture_location_claim"] = "Ireland"
        self.assertEqual(self.check()["status"], "FAIL")
        self.m["ireland_provenance_evidence_url"] = "https://example.org/proof"
        self.assertNotEqual(self.check()["status"], "FAIL")

    def test_hash_mismatch_rejected(self):
        self.m["textures"]["basecolor"]["sha256"] = "0" * 64
        self.assertEqual(self.check()["status"], "FAIL")

    def test_traversal_rejected(self):
        self.m["textures"]["basecolor"]["path"] = "../escape.png"
        self.assertEqual(self.check()["status"], "FAIL")

    def test_color_space_rejected(self):
        self.m["textures"]["roughness"]["color_space"] = "sRGB"
        self.assertEqual(self.check()["status"], "FAIL")

    def test_missing_texture_rejected(self):
        (self.root / "rough.png").unlink()
        self.assertEqual(self.check()["status"], "FAIL")

    def test_reject_approved_asset_promotion(self):
        self.m["asset_status"] = "approved"
        self.assertEqual(self.check()["status"], "FAIL")

if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Offline SHA and fail-closed checks for the local raster audit."""
import hashlib
import importlib.util
import pathlib
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("raster_audit", pathlib.Path(__file__).with_name("audit_gsi_raster.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class RasterAuditTests(unittest.TestCase):
    def test_sha256_and_no_canonical_adoption(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "fixture.bin"
            payload = b"not a raster; hash-only test"
            path.write_bytes(payload)
            expected = hashlib.sha256(payload).hexdigest()
            result = mod.audit(path, expected)
            self.assertEqual(result["source_sha256"], expected)
            self.assertTrue(result["sha256_match"])
            self.assertEqual(result["source_size_bytes"], len(payload))
            self.assertFalse(result["canonical_adoption"])
            self.assertEqual(result["qa"], "BLOCKED")
            self.assertEqual(result["source_license"], "UNVERIFIED_PER_TILE")

    def test_hash_mismatch_is_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "fixture.bin"
            path.write_bytes(b"some content")
            result = mod.audit(path, "0" * 64)
            self.assertFalse(result["sha256_match"])
            self.assertEqual(result["qa"], "FAIL_SHA256")

if __name__ == "__main__":
    unittest.main()

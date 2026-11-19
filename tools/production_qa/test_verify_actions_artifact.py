#!/usr/bin/env python3
import hashlib
import tempfile
import unittest
from pathlib import Path
from verify_actions_artifact import verify


class ArtifactVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "view.png").write_bytes(b"fake fixture bytes")
        self.digest = hashlib.sha256(b"fake fixture bytes").hexdigest()
        self.manifest = {"output_contract": "test-four-view-v1",
                         "files": {"view.png": self.digest}}

    def test_valid_bytes(self):
        result = verify(self.root, self.manifest, "test-four-view-v1")
        self.assertTrue(result["local_sha256_verified"])
        self.assertEqual(result["remote_artifact_accessible"], "NOT_VERIFIED")

    def test_modified_bytes(self):
        (self.root / "view.png").write_bytes(b"modified")
        with self.assertRaises(ValueError):
            verify(self.root, self.manifest, "test-four-view-v1")

    def test_wrong_contract(self):
        with self.assertRaises(ValueError):
            verify(self.root, self.manifest, "other")

    def test_missing_file(self):
        (self.root / "view.png").unlink()
        with self.assertRaises(FileNotFoundError):
            verify(self.root, self.manifest, "test-four-view-v1")

    def test_parent_traversal(self):
        with self.assertRaises(ValueError):
            verify(self.root, {"output_contract": "test-four-view-v1",
                               "files": {"../secret": self.digest}}, "test-four-view-v1")

    def test_absolute_path(self):
        with self.assertRaises(ValueError):
            verify(self.root, {"output_contract": "test-four-view-v1",
                               "files": {"/etc/passwd": self.digest}}, "test-four-view-v1")

    def test_symlink_rejected(self):
        (self.root / "alias.png").symlink_to(self.root / "view.png")
        with self.assertRaises(ValueError):
            verify(self.root, {"output_contract": "test-four-view-v1",
                               "files": {"alias.png": self.digest}}, "test-four-view-v1")

    def test_bad_digest(self):
        with self.assertRaises(ValueError):
            verify(self.root, {"output_contract": "test-four-view-v1",
                               "files": {"view.png": "bad"}}, "test-four-view-v1")

    def test_empty_manifest(self):
        with self.assertRaises(ValueError):
            verify(self.root, {"output_contract": "test-four-view-v1", "files": {}},
                   "test-four-view-v1")


if __name__ == "__main__":
    unittest.main()

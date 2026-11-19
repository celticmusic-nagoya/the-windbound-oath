import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path
from tools.ai_3d.audit_artifact_zip import audit_zip


class ArtifactZipAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "artifact.zip"
        self.data = b"actual candidate bytes"
        self.digest = hashlib.sha256(self.data).hexdigest()
        self.manifest = "assets/candidates/route-mat-01/SHA256SUMS"

    def make_zip(self, digest=None, name="method-c-01/render/abutment.blend"):
        with zipfile.ZipFile(self.path, "w") as archive:
            archive.writestr(self.manifest, f"{digest or self.digest}  {name}\n")
            archive.writestr("assets/candidates/route-mat-01/method-c-01/render/abutment.blend", self.data)

    def test_valid_archive(self):
        self.make_zip()
        self.assertEqual(audit_zip(self.path, self.manifest)["matched"], 1)

    def test_wrong_sha(self):
        self.make_zip(digest="0" * 64)
        self.assertEqual(audit_zip(self.path, self.manifest)["status"], "FAIL")

    def test_path_traversal(self):
        self.make_zip(name="../secret")
        self.assertEqual(audit_zip(self.path, self.manifest)["status"], "FAIL")

    def test_missing_entry(self):
        self.make_zip(name="not_present.blend")
        self.assertEqual(audit_zip(self.path, self.manifest)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()

"""Offline regression for streamed artifact reuse; never downloads real artifacts."""
import hashlib
from pathlib import Path
import stat
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import warnings
from zipfile import ZipFile, ZipInfo

import shared_artifact_reuse as reuse


class ArtifactReuseTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.archive = Path(temp.name) / "fixture.zip"
        self.data = b"verified fixture"
        self.manifest = {"output_contract": "views-v1", "files": {
            "views/front.png": hashlib.sha256(self.data).hexdigest()}}
        self.artifact = dict(manifest=self.manifest, zip_sha256="a"*64,
                             artifact_name="views", artifact_id=1)
        self.run_record = dict(run_id=2, head_sha="b"*40, head_branch="branch")
        self.meta = dict(artifact_id=1, head_sha="b"*40, head_branch="branch",
                         expires_at="2099-01-01T00:00:00Z")

    def make(self, entries):
        with ZipFile(self.archive, "w") as z:
            for name, content in entries:
                z.writestr(name, content)

    def verify(self):
        return reuse.verify_zip(self.archive, self.manifest, "views-v1")

    def test_exact_bytes_without_extraction(self):
        self.make([("views/front.png", self.data), ("extra.txt", b"unused")])
        self.assertTrue(self.verify())
        self.assertEqual(list(self.archive.parent.iterdir()), [self.archive])

    def test_modified_and_missing_payload(self):
        for entries in ([("views/front.png", b"wrong")], [("other", self.data)]):
            self.make(entries)
            with self.assertRaises(ValueError):
                self.verify()

    def test_duplicate_entry_rejected(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            self.make([("views/front.png", self.data)]*2)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.verify()

    def test_zip_symlink_rejected(self):
        info = ZipInfo("views/front.png")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        self.make([(info, self.data)])
        with self.assertRaisesRegex(ValueError, "invalid or excessive"):
            self.verify()

    def test_limit_before_decompression(self):
        self.make([("views/front.png", self.data)])
        with patch.object(reuse, "MAX_PAYLOAD", 1), patch.object(ZipFile, "open") as op:
            with self.assertRaisesRegex(ValueError, "excessive"):
                self.verify()
            op.assert_not_called()

    def test_invalid_manifest_never_reaches_network(self):
        for manifest in ({"output_contract":"other","files":self.manifest["files"]},
                         {"output_contract":"views-v1","files":{"../bad":"a"*64}},
                         {"output_contract":"views-v1","files":{"x":"bad"}}):
            with patch.object(reuse, "inspect") as inspect:
                with self.assertRaises(ValueError):
                    reuse.verify_reuse("owner/repo", "token", {**self.artifact,"manifest":manifest},
                                       self.run_record, "views-v1")
                inspect.assert_not_called()

    def test_expired_or_wrong_identity_never_downloads(self):
        for meta in ({**self.meta,"expires_at":"2000-01-01T00:00:00Z"},
                     {**self.meta,"artifact_id":3}):
            with patch.object(reuse,"inspect",return_value=meta), patch.object(reuse,"download") as dl:
                self.assertFalse(reuse.verify_reuse("owner/repo","token",self.artifact,
                                                    self.run_record,"views-v1"))
                dl.assert_not_called()

    def test_live_contract_uses_streamed_verified_bytes(self):
        self.make([("views/front.png", self.data)])
        def download(repo, ident, token, dest, digest):
            dest.write_bytes(self.archive.read_bytes())
        with patch.object(reuse,"inspect",return_value=self.meta), patch.object(reuse,"download",side_effect=download) as dl:
            self.assertTrue(reuse.verify_reuse("owner/repo","token",self.artifact,
                                               self.run_record,"views-v1"))
            dl.assert_called_once()


if __name__ == "__main__":
    unittest.main()

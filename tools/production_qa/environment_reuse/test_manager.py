import tempfile
import unittest
from pathlib import Path

from manager import canonical, inventory, sha, verify


class CacheVerificationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        app = self.root / "app"
        app.mkdir()
        self.binary = app / "blender"
        self.binary.write_bytes(b"unexecuted fixture")
        self.manifest = self.root / "manifest.json"
        self.prov = {"version": "5.3.0"}
        self.manifest.write_bytes(canonical(dict(provenance=self.prov, **inventory(app, 1000))))
        self.trusted = sha(self.manifest)

    def check(self):
        return verify(self.root, self.prov, self.trusted, 1000)

    def test_exact_match(self):
        self.assertEqual(self.check(), self.binary.stat().st_size)

    def test_different_key_and_corrupt_binary(self):
        with self.assertRaises(ValueError):
            verify(self.root, {"version": "5.2.4"}, self.trusted, 1000)
        self.binary.write_bytes(b"changed")
        with self.assertRaises(ValueError):
            self.check()

    def test_missing_or_rewritten_manifest(self):
        self.manifest.unlink()
        with self.assertRaises(ValueError):
            self.check()
        self.manifest.write_bytes(b"{}")
        with self.assertRaises(ValueError):
            self.check()

    def test_escaping_symlink_and_unexpected_path(self):
        extra = self.binary.parent / "extra"
        extra.symlink_to("../manifest.json")
        with self.assertRaises(ValueError):
            self.check()
        extra.unlink()
        (self.root / "extra").mkdir()
        with self.assertRaises(ValueError):
            self.check()

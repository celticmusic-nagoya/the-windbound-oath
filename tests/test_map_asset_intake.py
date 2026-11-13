import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from tools.map_blender.qa_asset_intake import audit

class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/"asset.png").write_bytes(b"fixture")
        self.manifest=self.root/"manifest.json"
        self.entry={"path":"asset.png","sha256":hashlib.sha256(b"fixture").hexdigest(),"license":"CC0-1.0","source_url":"https://example.org/asset"}
    def check(self,entries):
        self.manifest.write_text(json.dumps({"assets":entries}))
        return audit(self.root,self.manifest)
    def test_valid(self):self.assertEqual(self.check([self.entry])["status"],"PASS")
    def test_hash_mismatch(self):self.assertEqual(self.check([{**self.entry,"sha256":"0"*64}])["status"],"FAIL")
    def test_missing_file(self):self.assertEqual(self.check([{**self.entry,"path":"missing.png"}])["status"],"FAIL")
    def test_missing_provenance(self):self.assertEqual(self.check([{**self.entry,"license":""}])["status"],"FAIL")
    def test_path_traversal(self):self.assertEqual(self.check([{**self.entry,"path":"../outside.png"}])["status"],"FAIL")
    def test_duplicate_path(self):
        self.assertEqual(self.check([self.entry,self.entry])["status"],"FAIL")
    def test_invalid_digest_format(self):
        self.assertEqual(self.check([{**self.entry,"sha256":"xyz"}])["status"],"FAIL")
    def test_http_source_rejected(self):
        self.assertEqual(self.check([{**self.entry,"source_url":"http://example.org/asset"}])["status"],"FAIL")
    def test_source_with_credentials_rejected(self):
        self.assertEqual(self.check([{**self.entry,"source_url":"https://user:pass@example.org/asset"}])["status"],"FAIL")
    def test_absolute_path_rejected(self):
        self.assertEqual(self.check([{**self.entry,"path":"/tmp/asset.png"}])["status"],"FAIL")
    def test_backslash_path_rejected(self):
        self.assertEqual(self.check([{**self.entry,"path":"sub\\\\asset.png"}])["status"],"FAIL")
    def test_symlink_escape_rejected(self):
        outside=Path(self.temp.name).parent / ("outside-map-qa-" + self.root.name)
        outside.write_bytes(b"fixture")
        self.addCleanup(lambda: outside.unlink(missing_ok=True))
        (self.root/"linked.png").symlink_to(outside)
        self.assertEqual(self.check([{**self.entry,"path":"linked.png"}])["status"],"FAIL")
    def test_nested_valid_asset(self):
        (self.root/"sub").mkdir()
        (self.root/"sub"/"asset.png").write_bytes(b"fixture")
        self.assertEqual(self.check([{**self.entry,"path":"sub/asset.png"}])["status"],"PASS")
    def test_normalized_duplicate_path(self):
        self.assertEqual(self.check([self.entry,{**self.entry,"path":"./asset.png"}])["status"],"FAIL")
    def test_malformed_https_url(self):
        self.assertEqual(self.check([{**self.entry,"source_url":"https://[invalid/asset"}])["status"],"FAIL")
    def test_bad_manifest(self):
        self.manifest.write_text("broken")
        self.assertEqual(audit(self.root,self.manifest)["status"],"FAIL")
if __name__=="__main__":unittest.main()

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
    def test_bad_manifest(self):
        self.manifest.write_text("broken")
        self.assertEqual(audit(self.root,self.manifest)["status"],"FAIL")
if __name__=="__main__":unittest.main()

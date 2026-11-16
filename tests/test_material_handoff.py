import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from tools.material_pipeline.validate_material_handoff import validate

class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.image = self.root/'stone.png'
        self.image.write_bytes(b'not-a-real-png-but-valid-for-hash-test')
        self.doc = {'schema':'lind.material-handoff.v1','asset_id':'route-stone-a',
                    'reference_sha256':'a'*64,'producer':'Codex','tool_version':'test',
                    'seed':123,'license':'original',
                    'maps':[{'type':'base_color','color_space':'sRGB','path':'stone.png',
                             'sha256':hashlib.sha256(self.image.read_bytes()).hexdigest()}]}
        self.manifest = self.root/'manifest.json'
    def check(self):
        self.manifest.write_text(json.dumps(self.doc))
        return validate(self.manifest,self.root)
    def test_valid(self): self.assertEqual(self.check(),[])
    def test_tampered_file(self):
        self.image.write_bytes(b'tampered')
        self.assertTrue(any('SHA mismatch' in e for e in self.check()))
    def test_traversal(self):
        self.doc['maps'][0]['path']='../escape.png'
        self.assertTrue(any('escapes root' in e for e in self.check()))
    def test_wrong_colorspace(self):
        self.doc['maps'][0]['color_space']='Non-Color'
        self.assertTrue(any('color_space' in e for e in self.check()))
    def test_missing_provenance(self):
        self.doc.pop('license')
        self.assertTrue(any('missing license' in e for e in self.check()))
    def test_missing_file(self):
        self.image.unlink()
        self.assertTrue(any('file missing' in e for e in self.check()))
if __name__=='__main__': unittest.main()

import hashlib, json, tempfile, unittest, zipfile
from pathlib import Path
from pack_review_images import pack, digest, REPO

class ReviewPackTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.source=self.root/'source';self.source.mkdir()
        self.raw=b'\x89PNG\r\n\x1a\nfixture';(self.source/'view.png').write_bytes(self.raw)
        (self.source/'native.blend').write_bytes(b'private')
        self.out=self.root/'out.zip'
        self.spec=dict(repository=REPO,pr=482,head='a'*40,stage='fixture',g2='HOLD',adoption='NOT_ADOPTED',content_reviewed=True,rights_reviewed=True,review_ref='fixture only',rights_note='fixture only',entry_sha256={'view.png':digest(self.raw)})
    def test_exact_local_selection_and_determinism(self):
        a=pack(self.source,self.spec,self.out);b=pack(self.source,self.spec,self.root/'second.zip')
        self.assertEqual(a,b)
        with zipfile.ZipFile(self.out) as z:
            self.assertEqual(set(z.namelist()),{'view.png','receipt.json','SHA256SUMS.txt'});self.assertEqual(z.read('view.png'),self.raw);self.assertIsNone(z.testzip());self.assertFalse(json.loads(z.read('receipt.json'))['publication_authorized_by_tool'])
        self.assertEqual((self.source/'native.blend').read_bytes(),b'private')
    def test_review_and_pins_fail_closed(self):
        for changes in ({'content_reviewed':False},{'rights_reviewed':False},{'rights_note':''},{'head':'bad'},{'entry_sha256':{'view.png':'a'*64}},{'entry_sha256':{'../view.png':digest(self.raw)}},{'entry_sha256':{'native.blend':digest(b'private')}},{'entry_sha256':{'view.png':digest(self.raw),'other.png':digest(self.raw)}}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):pack(self.source,dict(self.spec,**changes),self.out)
        self.assertFalse(self.out.exists())
    def test_no_overwrite(self):
        self.out.write_bytes(b'old')
        with self.assertRaises(ValueError):pack(self.source,self.spec,self.out)
        self.assertEqual(self.out.read_bytes(),b'old')
    def test_symlink_rejected(self):
        (self.source/'link.png').symlink_to(self.source/'view.png')
        with self.assertRaises(ValueError):pack(self.source,dict(self.spec,entry_sha256={'link.png':digest(self.raw)}),self.out)
    def test_archive_identity_and_exact_entry(self):
        archive=self.root/'source.zip'
        with zipfile.ZipFile(archive,'w') as z:z.writestr('view.png',self.raw);z.writestr('native.blend',b'private')
        spec=dict(self.spec,artifact_id=1,run_id=2,archive_bytes=archive.stat().st_size,archive_sha256=digest(archive.read_bytes()))
        with self.assertRaises(ValueError):pack(archive,dict(spec,archive_sha256='a'*64),self.out)
        pack(archive,spec,self.out)
        with zipfile.ZipFile(self.out) as z:self.assertNotIn('native.blend',z.namelist())
    def test_signature(self):
        (self.source/'view.png').write_bytes(b'not image')
        with self.assertRaises(ValueError):pack(self.source,dict(self.spec,entry_sha256={'view.png':digest(b'not image')}),self.out)

if __name__=='__main__':unittest.main()

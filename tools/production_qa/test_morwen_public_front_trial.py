"""Credential-free trial boundary tests, no private inputs in repository."""
import base64,json,unittest,tempfile
from pathlib import Path
from unittest.mock import patch
import morwen_public_front_trial as t
import morwen_public_recovery as r
from test_morwen_public_recovery import archive,fixture
class Test(unittest.TestCase):
    def test_pinned_worker(self):
        raw=b'reviewed fixture';pin=t.git_sha(raw)
        meta={'sha':pin,'size':len(raw),'encoding':'base64','content':base64.b64encode(raw).decode()}
        self.assertEqual(t.pinned_blob(lambda *a:meta,'x','tools/test',pin),raw)
        for field,val in [('sha','0'*40),('size',1),('content','eA=='),('encoding','other')]:
            with self.assertRaises(ValueError):t.pinned_blob(lambda *a:dict(meta,**{field:val}),'x','tools/test',pin)
    def test_release_nested_archive(self):
        native,src=fixture();shot=b'fixture'
        rec=dict(status='READONLY_REOPEN_VERIFIED_NOT_ADOPTED',source_sha256=r.sha(native),source_archive_sha256=r.sha(src),public_run_id='46139309085',source_artifact_id=r.ARTIFACT,screenshots_sha256=r.sha(shot))
        members={'W108-original.zip':src,'reopened-editor.png':shot,'receipt.json':json.dumps(rec).encode()}
        members['SHA256SUMS.json']=json.dumps({k:r.sha(v) for k,v in members.items()}).encode()
        raw=archive(members)
        with patch.multiple(t,REL_SHA=r.sha(raw),REL_BYTES=len(raw)),patch.multiple(r,NATIVE_SHA=r.sha(native),ARCHIVE_SHA=r.sha(src),ARCHIVE_BYTES=len(src)):
            self.assertEqual(t.unpack_release(raw),(src,native))
            with self.assertRaises(ValueError):t.unpack_release(raw[:-1]+b'x')
        members['receipt.json']=b'{}';raw=archive(members)
        with patch.multiple(t,REL_SHA=r.sha(raw),REL_BYTES=len(raw)):
            with self.assertRaises(ValueError):t.unpack_release(raw)
    def test_owner_gate_no_write(self):
        env=dict(DEST_TOKEN='private',GH_TOKEN='public',GITHUB_RUN_ID='1')
        def api(token,method,url):
            self.assertEqual(method,'GET')
            return {'state':'open','head':{'sha':'wrong'}}
        with patch.object(r,'identity'),patch.object(r,'private'),patch.object(r,'check_active'):
            with self.assertRaises(ValueError):t.gate(api,env)
    def test_no_missing_candidate_release(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(r,'publish_private') as pub:
                with self.assertRaises((ValueError,FileNotFoundError)):t.preserve(None,{'RUNNER_TEMP':d},Path(d))
                pub.assert_not_called()
if __name__=='__main__':unittest.main()

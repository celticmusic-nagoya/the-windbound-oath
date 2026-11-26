import copy
import datetime as dt
import hashlib
import pathlib
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
import restore_morwen_artifact_preflight as m
from restore_morwen_preserved import NATIVE_SHA

RUN = dict(id=m.RUN, head_sha=m.REV, head_branch='main', event='workflow_dispatch', status='completed', conclusion='success',run_attempt=1, workflow_id=424712879,path='.github/workflows/morwen-vroid-macos-probe.yml',repository={'id':m.RID},head_repository={'id':m.RID})
ART = dict(id=m.ARTIFACT,name='morwen-isolated-vroid-reopen-review',size_in_bytes=m.ARCHIVE_BYTES,digest='sha256:'+m.ARCHIVE_SHA,expired=False,expires_at='2026-12-02T11:52:56Z',workflow_run=dict(id=m.RUN, repository_id=m.RID, head_repository_id=m.RID,head_branch='main',head_sha=m.REV))
NOW=dt.datetime(2026,11,26,tzinfo=dt.timezone.utc)
class Test(unittest.TestCase):
    def setUp(self):
        self.run=copy.deepcopy(RUN);self.inv=dict(total_count=1,artifacts=[copy.deepcopy(ART)]);self.downloads=[]
    def api(self,path):
        if path==f'{m.BASE}/actions/runs/{m.RUN}':return self.run
        self.assertEqual(path,f'{m.BASE}/actions/runs/{m.RUN}/artifacts?per_page=100');return self.inv
    def download(self,path,cap):
        self.assertEqual(path,f'{m.BASE}/actions/artifacts/{m.ARTIFACT}/zip');self.assertEqual(cap,m.ARCHIVE_BYTES);self.downloads.append(path);return b'fixture'
    def go(self):return m.load(self.api,self.download,NOW)
    def reject(self):
        with self.assertRaises(ValueError):self.go()
        self.assertEqual(self.downloads,[])
    def test_success(self):
        with patch.object(m,'read_native',return_value=b'native') as v:self.assertEqual(self.go(),b'native');v.assert_called_once_with(b'fixture')
    def test_bad_run(self):self.run['conclusion']='failure';self.reject()
    def test_bad_attempt(self):self.run['run_attempt']=2;self.reject()
    def test_wrong_revision(self):self.run['head_sha']='0'*40;self.reject()
    def test_fork(self):self.run['head_repository']['id']=0;self.reject()
    def test_missing(self):self.inv['artifacts']=[];self.inv['total_count']=0;self.reject()
    def test_duplicate(self):self.inv['artifacts']*=2;self.inv['total_count']=2;self.reject()
    def test_pagination(self):self.inv['total_count']=2;self.reject()
    def test_expired(self):self.inv['artifacts'][0]['expired']=True;self.reject()
    def test_expiry_date(self):self.inv['artifacts'][0]['expires_at']='2026-11-01T00:00:00Z';self.reject()
    def test_wrong_digest(self):self.inv['artifacts'][0]['digest']='sha256:'+'0'*64;self.reject()
    def test_wrong_size(self):self.inv['artifacts'][0]['size_in_bytes']+=1;self.reject()
    def test_wrong_artifact_run(self):self.inv['artifacts'][0]['workflow_run']['id']=1;self.reject()
    def test_corrupt(self):
        with self.assertRaises(ValueError):self.go()
        self.assertEqual(len(self.downloads),1)
    def test_download_failure(self):
        with self.assertRaises(TimeoutError):m.load(self.api,lambda *_:(_ for _ in ()).throw(TimeoutError()),NOW)

class Transport(unittest.TestCase):
    def call(self, code, cap=16, timeout=2):
        with tempfile.TemporaryDirectory() as tmp:
            gh=pathlib.Path(tmp)/'gh'
            gh.write_text('#!'+sys.executable+'\n'+code+'\n')
            gh.chmod(0o700)
            with patch.dict(os.environ, {'PATH':tmp+os.pathsep+os.environ.get('PATH','')}):
                return m.bounded_gh('fixture',cap,timeout)
    def test_bounded_success(self):self.assertEqual(self.call("print('ok')"),b'ok\n')
    def test_bounded_limit(self):
        with self.assertRaises(ValueError):self.call("print('x'*100)")
    def test_bounded_timeout(self):
        with self.assertRaises(TimeoutError):self.call('import time; time.sleep(5)',timeout=0.2)
    def test_bounded_failure(self):
        with self.assertRaises(ValueError):self.call("import sys; print('synthetic diagnostic',file=sys.stderr);sys.exit(1)")

if __name__=='__main__':unittest.main()

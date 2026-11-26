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


class FencedRestore(unittest.TestCase):
    def setUp(self):
        import types
        import contextlib
        from unittest.mock import Mock
        import restore_morwen_preserved as restore
        self.r=restore
        self.stack=contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.tmp=self.stack.enter_context(tempfile.TemporaryDirectory())
        self.target=pathlib.Path(self.tmp)/'Morwen-resume.vroid'
        self.data=b'synthetic native fixture'
        self.events=[]
        self.verify=Mock(side_effect=lambda *a:self.events.append('fence'))
        self.private=Mock(return_value=self.data)
        self.load=Mock(side_effect=lambda *a,**kw:self.events.append('artifact') or self.data)
        self.env=dict(GITHUB_REPOSITORY=m.REPO,GITHUB_REF='refs/heads/main',
            GITHUB_EVENT_NAME='workflow_dispatch',GITHUB_RUN_ATTEMPT='1',
            GITHUB_ACTOR_ID='41898282',MORWEN_PRIVATE_TRANSFER_APPROVED='true',
            RUNNER_TEMP=self.tmp,TRANSFER_ASSET='fixture',MORWEN_BOUND_FENCE='fixture',
            GITHUB_SHA='fixture',REQUEST_ID='fixture',GITHUB_RUN_ID='fixture',
            GH_TOKEN='synthetic',DEST_TOKEN='synthetic')
        self.stack.enter_context(patch.dict(os.environ,self.env,clear=True))
        self.stack.enter_context(patch.dict(sys.modules,{
            'release_transport':types.SimpleNamespace(request=Mock()),
            'morwen_transfer_claim':types.SimpleNamespace(verify=self.verify)}))
        self.stack.enter_context(patch.object(restore,'restore',self.private))
        self.stack.enter_context(patch.object(restore,'NATIVE_SHA',hashlib.sha256(self.data).hexdigest()))
        self.stack.enter_context(patch.object(m,'load',self.load))
        prior=os.umask(0o077); self.addCleanup(os.umask,prior)
    def go(self,source='actions_artifact'):
        self.r.main(self.events.append,source=source)
    def test_alternate_uses_same_fences_and_exclusive_save(self):
        self.go()
        self.assertEqual(self.target.read_bytes(),self.data)
        self.assertEqual([e for e in self.events if e in ('fence','artifact')],['fence','artifact','fence','fence'])
        self.private.assert_not_called()
        self.assertEqual(self.target.stat().st_mode & 0o777,0o600)
    def test_default_still_private(self):
        self.r.main()
        self.private.assert_called_once()
        self.load.assert_not_called()
        self.assertEqual(self.target.read_bytes(),self.data)
    def test_unknown_source(self):
        with self.assertRaises(ValueError):self.go('auto')
        self.verify.assert_not_called(); self.load.assert_not_called()
    def test_unapproved_worker(self):
        os.environ['MORWEN_PRIVATE_TRANSFER_APPROVED']='false'
        with self.assertRaises(ValueError):self.go()
        self.verify.assert_not_called(); self.load.assert_not_called()
    def test_missing_private_credential(self):
        del os.environ['DEST_TOKEN']
        with self.assertRaises(ValueError):self.go()
        self.load.assert_not_called()
    def test_missing_artifact_credential(self):
        del os.environ['GH_TOKEN']
        with self.assertRaises(ValueError):self.go()
        self.load.assert_not_called(); self.private.assert_not_called()
    def test_existing_target_untouched(self):
        self.target.write_bytes(b'protected')
        with self.assertRaises(ValueError):self.go()
        self.assertEqual(self.target.read_bytes(),b'protected')
        self.load.assert_not_called()
    def test_no_fallback_on_failure(self):
        self.load.side_effect=TimeoutError('fixture')
        with self.assertRaises(TimeoutError):self.go()
        self.private.assert_not_called(); self.assertFalse(self.target.exists())
    def test_bad_native_rejected_before_save(self):
        self.load.side_effect=None; self.load.return_value=b'bad'
        with self.assertRaises(ValueError):self.go()
        self.assertFalse(self.target.exists()); self.assertEqual(self.verify.call_count,1)
    def test_first_fence_failure(self):
        self.verify.side_effect=ValueError('fixture')
        with self.assertRaises(ValueError):self.go()
        self.load.assert_not_called(); self.assertFalse(self.target.exists())
    def test_second_fence_failure(self):
        self.verify.side_effect=[None,ValueError('fixture')]
        with self.assertRaises(ValueError):self.go()
        self.assertFalse(self.target.exists())
    def test_final_fence_failure_does_not_report_success(self):
        self.verify.side_effect=[None,None,ValueError('fixture')]
        with self.assertRaises(ValueError):self.go()
        self.assertEqual(self.target.read_bytes(),self.data)

if __name__=='__main__':unittest.main()

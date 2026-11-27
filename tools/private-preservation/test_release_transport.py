import json, pathlib, tempfile, unittest
from unittest.mock import Mock, patch
import release_transport as t

class RestTransportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=pathlib.Path(self.tmp.name); self.file=self.root/'123.zip'; self.file.write_bytes(b'zip')
        self.tag='preserved-artifact-123'; self.stages=[]; self.api=Mock(); self.original=Mock()
        self.rest=t.ReleaseTransport(self.original,'dest',self.stages.append,self.api)
        self.create=['release','create',self.tag,str(self.file),'--repo',t.DEST,'--target','a'*40,'--draft','--prerelease','--title',self.tag,'--notes','receipt']
        self.api.side_effect=[dict(id=7,tag_name=self.tag,draft=True),dict(id=8,name='123.zip',state='uploaded',size=3),b'zip',dict(id=7,tag_name=self.tag,draft=False,prerelease=True),b'zip']
    def download(self,name):
        p=self.root/name;p.mkdir(); self.rest('dest',['release','download',self.tag,'--repo',t.DEST,'--pattern','123.zip','--dir',str(p)]);return p/'123.zip'
    def test_full_sequence(self):
        self.rest('dest',self.create);self.assertEqual(self.download('draft').read_bytes(),b'zip')
        self.rest('dest',['release','edit',self.tag,'--repo',t.DEST,'--draft=false','--prerelease']);self.assertEqual(self.download('final').read_bytes(),b'zip')
        self.assertEqual(self.stages,['RELEASE_CREATE','RELEASE_UPLOAD','RELEASE_DRAFT_READBACK','RELEASE_PUBLISH','RELEASE_FINAL_READBACK'])
        self.assertEqual([c.args[1] for c in self.api.call_args_list],['POST','POST','GET','PATCH','GET'])
        self.assertTrue(json.loads(self.api.call_args_list[0].args[3])['draft'])
        self.assertEqual(json.loads(self.api.call_args_list[3].args[3])['make_latest'],'false')
    def test_wrong_token_or_repo_denied(self):
        with self.assertRaises(t.TransportError):self.rest('source',self.create)
        with self.assertRaises(t.TransportError):self.rest('dest',[a if a!=t.DEST else 'public/repo' for a in self.create])
        self.api.assert_not_called()
    def test_upload_failure_never_publishes(self):
        self.api.side_effect=[dict(id=7,tag_name=self.tag,draft=True),t.TransportError(403)]
        with self.assertRaises(t.TransportError) as e:self.rest('dest',self.create)
        self.assertEqual(e.exception.status,403);self.assertEqual(self.api.call_count,2);self.assertNotIn(self.tag,self.rest.records)
    def test_invalid_create_receipt(self):
        self.api.side_effect=[dict(id=7,tag_name='other',draft=True)]
        with self.assertRaises(t.TransportError):self.rest('dest',self.create)
        self.assertEqual(self.api.call_count,1)
    def test_readback_size_rejected(self):
        self.rest('dest',self.create);self.api.side_effect=[b'xx']
        with self.assertRaises(t.TransportError):self.download('draft')
        self.assertFalse((self.root/'draft'/'123.zip').exists())
    def test_read_api_delegates(self):
        self.rest('source',['api','repos/test']);self.original.assert_called_once_with('source',['api','repos/test'],output=None,missing_ok=False)
    def test_wrong_host(self):
        with self.assertRaises(t.TransportError):t.request('token','GET','https://other.example/')
    def test_redirect_strips_token(self):
        import urllib.error
        err=urllib.error.HTTPError('https://api.github.com/x',302,'redirect',{'Location':'https://release-assets.githubusercontent.com/test'},None)
        response=Mock(); response.__enter__=Mock(return_value=response);response.__exit__=Mock(); response.read.return_value=b'zip'
        opener=Mock();opener.open.side_effect=[err,response]
        with patch.object(t.urllib.request,'build_opener',return_value=opener):self.assertEqual(t.request('token','GET','https://api.github.com/x',binary=True,limit=3),b'zip')
        self.assertFalse(opener.open.call_args_list[1].args[0].has_header('Authorization'))
    def test_redirect_wrong_host_denied(self):
        import urllib.error
        err=urllib.error.HTTPError('https://api.github.com/x',302,'redirect',{'Location':'https://other.example/test'},None)
        opener=Mock();opener.open.side_effect=err
        with patch.object(t.urllib.request,'build_opener',return_value=opener):
            with self.assertRaises(t.TransportError):t.request('token','GET','https://api.github.com/x',binary=True)
        self.assertEqual(opener.open.call_count,1)
if __name__=='__main__':unittest.main()

import base64, contextlib, io, json, os, pathlib, tempfile, unittest

IDS = (1001, 1002)
PIN = 'a'*40
from unittest.mock import patch, Mock
import public_preservation_bridge as b

class BridgeTest(unittest.TestCase):
    def test_non_owner_and_wrong_event_never_call_api(self):
        for key in b.EXPECTED:
            with patch.dict(os.environ, dict(b.EXPECTED, **{key:'wrong'}), clear=True), patch.object(b,'api') as api:
                with self.assertRaises(ValueError): b.run()
                api.assert_not_called()

    def test_auto_wrong_context_never_calls_api(self):
        for key in b.AUTO_EXPECTED:
            with patch.dict(os.environ, dict(b.AUTO_EXPECTED, **{key:'wrong'}), clear=True), patch.object(b,'api') as api:
                with self.assertRaises(ValueError): b.run()
                api.assert_not_called()

    def test_checked_in_request_and_invalid_requests(self):
        self.assertIn(b.read_batch_request()['operation'], ('preserve', 'verify_existing'))
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp)/'request.json'
            with self.assertRaises(ValueError): b.read_batch_request(p)
            valid=dict(artifact_ids=list(IDS),reviewed_queue_blob=PIN,operation='preserve')
            p.write_text(json.dumps(valid)); self.assertEqual(b.read_batch_request(p),valid)
            for bad in ({}, dict(valid,artifact_ids=[]), dict(valid,artifact_ids=[1,1]), dict(valid,artifact_ids=[True]), dict(valid,artifact_ids=[14602858760]), dict(valid,artifact_ids=list(range(1,15))), dict(valid,reviewed_queue_blob='wrong'), dict(valid,operation='delete'), dict(valid,other=True)):
                p.write_text(json.dumps(bad))
                with self.assertRaises(ValueError): b.read_batch_request(p)

    def test_auto_missing_request_blocks_before_api(self):
        with patch.dict(os.environ, b.AUTO_EXPECTED, clear=True), patch.object(b,'read_batch_request',side_effect=ValueError('missing')), patch.object(b,'api') as api:
            with self.assertRaises(ValueError): b.run()
            api.assert_not_called()

    def test_auto_push_preserves_only_pinned_reviewed_queue(self):
        rows=[dict(artifact_id=i,rights='APPROVED_PRIVATE_COPY') for i in IDS]
        q=dict(source_repository=b.SOURCE,items=rows)
        ref=dict(ref='refs/heads/main',object=dict(type='commit',sha='a'*40))
        module=Mock(); batch=dict(artifact_ids=list(IDS),reviewed_queue_blob=PIN,operation='preserve')
        with patch.dict(os.environ,dict(b.AUTO_EXPECTED,SOURCE_TOKEN='x',DEST_TOKEN='y'),clear=True), patch.object(b,'read_batch_request',return_value=batch), patch.object(b,'api',side_effect=[dict(full_name=b.DEST,private=True),ref]), patch.object(b,'read_file',side_effect=[b'pass',json.dumps(q).encode()]) as rf, patch.object(b.importlib.util,'module_from_spec',return_value=module), patch.object(b.importlib.util,'spec_from_file_location',return_value=Mock()), patch.object(b,'preflight') as pf:
            b.run()
        rf.assert_called_with('y','a'*40,b.QUEUE,PIN)
        module.require_reviewed_queue.assert_called_once_with(rows,q)
        module.preserve.assert_called_once_with(rows,'x','y','a'*40,public_bridge=True)
        pf.assert_not_called()

    def test_existing_verification_never_calls_preserve(self):
        rows=[dict(artifact_id=i,rights='APPROVED_PRIVATE_COPY') for i in IDS]
        q=dict(source_repository=b.SOURCE,items=rows)
        ref=dict(ref='refs/heads/main',object=dict(type='commit',sha='a'*40))
        module=Mock(); batch=dict(artifact_ids=list(IDS),reviewed_queue_blob=PIN,operation='verify_existing')
        with patch.dict(os.environ,dict(b.AUTO_EXPECTED,SOURCE_TOKEN='x',DEST_TOKEN='y'),clear=True), patch.object(b,'read_batch_request',return_value=batch), patch.object(b,'api',side_effect=[dict(full_name=b.DEST,private=True),ref]), patch.object(b,'read_file',side_effect=[b'pass',json.dumps(q).encode()]), patch.object(b.importlib.util,'module_from_spec',return_value=module), patch.object(b.importlib.util,'spec_from_file_location',return_value=Mock()), patch.object(b,'verify_existing') as verify:
            self.assertEqual(b.run(),'EXISTING_READBACK')
        verify.assert_called_once(); module.preserve.assert_not_called()

    def test_existing_readback_is_get_only_and_digest_guarded(self):
        module=Mock(); item=dict(artifact_id=1001,bytes=3,sha256='a'*64)
        asset=dict(id=7,name='1001.zip',size=3,state='uploaded',digest='sha256:'+item['sha256'])
        release=dict(tag_name='preserved-artifact-1001',draft=False,prerelease=True,assets=[asset])
        with tempfile.TemporaryDirectory() as tmp, patch.object(b,'api',return_value=release), patch.object(b,'rest_request',return_value=b'zip') as get:
            b.verify_existing(module,[item],'dest',pathlib.Path(tmp))
            get.assert_called_once_with('dest','GET','https://api.github.com/repos/'+b.DEST+'/releases/assets/7',binary=True,limit=3)
            self.assertEqual((pathlib.Path(tmp)/'1001.zip').read_bytes(),b'zip')
            module.verify_zip.assert_called_once_with(pathlib.Path(tmp)/'1001.zip',item)
        with tempfile.TemporaryDirectory() as tmp, patch.object(b,'api',return_value=dict(release,assets=[dict(asset,digest='wrong')])), patch.object(b,'rest_request') as get:
            with self.assertRaises(ValueError): b.verify_existing(module,[item],'dest',pathlib.Path(tmp))
            get.assert_not_called()

    def test_missing_and_same_tokens_never_call_api(self):
        for tokens in ({}, {'SOURCE_TOKEN':'x','DEST_TOKEN':'x'}):
            with patch.dict(os.environ, dict(b.EXPECTED, **tokens), clear=True), patch.object(b,'api') as api:
                with self.assertRaises(ValueError): b.run()
                api.assert_not_called()

    def test_public_destination_rejected(self):
        with patch.dict(os.environ, dict(b.EXPECTED,SOURCE_TOKEN='x',DEST_TOKEN='y'), clear=True), patch.object(b,'api',return_value={'full_name':b.DEST,'private':False}) as api:
            with self.assertRaises(ValueError): b.run()
            self.assertEqual(api.call_count,1)

    def test_blob_pinned_and_tamper_rejected(self):
        data=b'print(1)'; sha=b.git_blob(data)
        obj=dict(type='file',path=b.ENGINE,encoding='base64',size=len(data),content=base64.b64encode(data).decode(),sha=sha)
        with patch.object(b,'api',return_value=obj):
            self.assertEqual(b.read_file('x','a'*40,b.ENGINE,sha),data)
            with self.assertRaises(ValueError): b.read_file('x','a'*40,b.ENGINE,'0'*40)
        with patch.object(b,'api',return_value=dict(obj,content=base64.b64encode(b'print(2)').decode())):
            with self.assertRaises(ValueError): b.read_file('x','a'*40,b.ENGINE,sha)

    def test_select_only_reviewed_pilot(self):
        rows=[dict(artifact_id=x,rights='APPROVED_PRIVATE_COPY') for x in (*IDS,42)]
        q=dict(source_repository=b.SOURCE,items=rows)
        self.assertEqual(b.select_pilot(q, IDS),rows[:len(IDS)])
        for bad in (rows[1:],rows+[rows[0]], [dict(rows[0],rights='PENDING'),*rows[1:]]):
            with self.assertRaises(ValueError): b.select_pilot(dict(q,items=bad), IDS)

    def test_private_errors_and_receipts_not_logged(self):
        out=io.StringIO()
        with contextlib.redirect_stdout(out), patch.object(b,'run',side_effect=ValueError('private secret')):
            self.assertEqual(b.main(),1)
        self.assertNotIn('private secret',out.getvalue())
        def success(): print('private receipt')
        out=io.StringIO()
        with contextlib.redirect_stdout(out), patch.object(b,'run',side_effect=success):
            self.assertEqual(b.main(),0)
        self.assertNotIn('private receipt',out.getvalue())

    def test_http_status_only(self):
        failure=Mock(returncode=1,stderr=b'private body and token (HTTP 403)')
        with patch.object(b.subprocess,'run',return_value=failure):
            with self.assertRaises(b.ApiError) as exc: b.api('secret','private endpoint')
            self.assertEqual(exc.exception.status,403)
            self.assertNotIn('secret',str(exc.exception))
        self.assertEqual(b.ApiError(999).status,0)

    def test_absent_only_404(self):
        with patch.object(b,'api',side_effect=b.ApiError(404)):
            self.assertTrue(b.absent('x','tag'))
        with patch.object(b,'api',side_effect=b.ApiError(403)):
            with self.assertRaises(b.ApiError): b.absent('x','tag')
        with patch.object(b,'api',return_value={}):
            self.assertFalse(b.absent('x','tag'))

    def test_preflight_read_only(self):
        module=Mock(); module.gh.return_value=b''
        rows=[dict(artifact_id=i) for i in IDS]
        with tempfile.TemporaryDirectory() as tmp, patch.object(b,'absent',return_value=True), patch.object(b,'api',return_value={}) as api:
            b.preflight(module,rows,'source','dest',pathlib.Path(tmp))
        self.assertEqual(module.verify_zip.call_count,len(IDS))
        self.assertEqual(module.verify_meta.call_count,len(IDS))
        self.assertEqual(api.call_count,2*len(IDS))
        module.preserve.assert_not_called()
        self.assertEqual(module.gh.call_count,1)
        self.assertEqual(module.gh.call_args.args[1][0],'api')

    def test_preflight_existing_release_blocks_before_download(self):
        module=Mock(); module.gh.return_value=f'preserved-artifact-{IDS[0]}'.encode()
        with tempfile.TemporaryDirectory() as tmp, patch.object(b,'api') as api:
            with self.assertRaises(ValueError): b.preflight(module,[dict(artifact_id=IDS[0])],'source','dest',pathlib.Path(tmp))
        api.assert_not_called()
        module.preserve.assert_not_called()

    def test_diagnostic_default_never_preserves(self):
        rows=[dict(artifact_id=i,rights='APPROVED_PRIVATE_COPY') for i in IDS]
        q=dict(source_repository=b.SOURCE,items=rows)
        ref=dict(ref='refs/heads/main',object=dict(type='commit',sha='a'*40))
        module=Mock()
        with patch.dict(os.environ,dict(b.EXPECTED,SOURCE_TOKEN='x',DEST_TOKEN='y'),clear=True), patch.object(b,'read_batch_request',return_value=dict(artifact_ids=list(IDS),reviewed_queue_blob=PIN,operation='preserve')), patch.object(b,'api',side_effect=[dict(full_name=b.DEST,private=True),ref]), patch.object(b,'read_file',side_effect=[b'pass',json.dumps(q).encode()]), patch.object(b.importlib.util,'module_from_spec',return_value=module), patch.object(b.importlib.util,'spec_from_file_location',return_value=Mock()), patch.object(b,'preflight') as pf:
            b.run()
        pf.assert_called_once()
        module.preserve.assert_not_called()

if __name__ == '__main__': unittest.main()

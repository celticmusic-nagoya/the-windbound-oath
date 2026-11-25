import base64, contextlib, io, json, os, unittest
from unittest.mock import patch
import public_preservation_bridge as b

class BridgeTest(unittest.TestCase):
    def test_non_owner_and_wrong_event_never_call_api(self):
        for key in b.EXPECTED:
            with patch.dict(os.environ, dict(b.EXPECTED, **{key:'wrong'}), clear=True), patch.object(b,'api') as api:
                with self.assertRaises(ValueError): b.run()
                api.assert_not_called()

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
        rows=[dict(artifact_id=x,rights='APPROVED_PRIVATE_COPY') for x in (*b.PILOT,42)]
        q=dict(source_repository=b.SOURCE,items=rows)
        self.assertEqual(b.select_pilot(q),rows[:2])
        for bad in (rows[1:],rows+[rows[0]], [dict(rows[0],rights='PENDING'),*rows[1:]]):
            with self.assertRaises(ValueError): b.select_pilot(dict(q,items=bad))

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

if __name__ == '__main__': unittest.main()

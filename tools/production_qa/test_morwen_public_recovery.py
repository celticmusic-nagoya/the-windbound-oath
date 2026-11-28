"""Credential-free negative and positive fixtures for the one recovery adapter."""
import hashlib,io,json,os,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent))
import morwen_public_recovery as m
def archive(entries):
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w') as z:
        for k,v in entries.items():z.writestr(k,v)
    return b.getvalue()
def fixture():
    n=archive({'meta.json':b'{}','v1model/meta.json':b'{}','v1model/data.bin':b'mock','thumbnails/thumbnail.jpg':b'mock'})
    shots={'W108-shot-'+str(i)+'.png':b'fixture'+str(i).encode() for i in range(33)}
    r={'status':'NEW_CUSTOM_FRONT_STRANDS_SAVED_REOPENED_NOT_ADOPTED','save_reopen':True,'candidate_sha256':m.sha(n),'hairs':['Hair '+str(i) for i in range(1,6)],'screenshots':{k:m.sha(v) for k,v in shots.items()}}
    a=archive({m.NATIVE_NAME:n,'W108-receipt.json':json.dumps(r).encode(),**shots})
    return n,a
class Test(unittest.TestCase):
    def test_exact_and_changed_source(self):
        n,a=fixture()
        with patch.multiple(m,NATIVE_SHA=m.sha(n),ARCHIVE_SHA=m.sha(a),ARCHIVE_BYTES=len(a)):
            self.assertEqual(m.extract(a),n)
            with self.assertRaises(ValueError):m.extract(a[:-1]+b'x')
    def test_destination_private_only(self):
        for private in [False,None]:
            with self.assertRaises(ValueError):m.private(lambda *a,**k:{'full_name':m.DEST,'id':1420925740,'private':private},'mock')
        self.assertTrue(m.private(lambda *a,**k:{'full_name':m.DEST,'id':1420925740,'private':True},'mock')['private'])
    def test_unsafe_inventory(self):
        for name in ('../escape','nested/file','a\\b'):
            with self.assertRaises(ValueError):
                with zipfile.ZipFile(io.BytesIO(archive({name:b'x'}))) as z:m.verify_inventory(z)
    def test_actor_and_scope(self):
        env={'GITHUB_REPOSITORY':m.ORIGIN,'GITHUB_REF':'refs/heads/main','GITHUB_EVENT_NAME':'push','GITHUB_ACTOR_ID':'315379131','GITHUB_RUN_ATTEMPT':'1','GITHUB_SHA':'a'*40,'GITHUB_RUN_ID':'1','MORWEN_PRIVATE_TRANSFER_APPROVED':'true','DEST_TOKEN':'mock'}
        m.identity(env)
        for key,val in [('GITHUB_EVENT_NAME','pull_request'),('GITHUB_ACTOR_ID','999'),('GITHUB_REF','refs/heads/other'),('GITHUB_RUN_ATTEMPT','2'),('DEST_TOKEN',''),('MORWEN_PRIVATE_TRANSFER_APPROVED','false')]:
            with self.assertRaises(ValueError):m.identity(dict(env,**{key:val}))
    def test_no_concurrent_writer(self):
        def api(token,method,url):
            return {'total_count':0,'workflow_runs':[]}
        m.check_active(api,'x','y','1')
        def busy(token,method,url):
            return {'total_count':1,'workflow_runs':[{'id':2,'name':'Morwen job','head_branch':'main'}]}
        with patch.object(m.time,'sleep') as sleep:
            with self.assertRaises(ValueError):m.check_active(busy,'x','y','1')
            self.assertEqual(sleep.call_count,2)
    def test_active_check_diagnostic_stages(self):
        for failing,expected in [('private','PRIVATE_ACTIVE_QUEUED'),('public','PUBLIC_ACTIVE_QUEUED')]:
            def api(credential,method,url):
                if credential==failing:raise ValueError('denied')
                return {'total_count':0,'workflow_runs':[]}
            with self.assertRaises(ValueError):m.check_active(api,'private','public','1')
            self.assertEqual(m.STAGE,expected)
    def test_truncated_active_list_rejected(self):
        with patch.object(m.time,'sleep'):
            with self.assertRaises(ValueError):m.check_active(lambda *a:{'total_count':101,'workflow_runs':[]},'x','y','1')
    def test_transient_inventory_requires_complete_rescan(self):
        calls=[]
        def api(token,method,url):
            calls.append((token,url))
            if len(calls)==1:return {'total_count':1,'workflow_runs':[]}
            return {'total_count':0,'workflow_runs':[]}
        with patch.object(m.time,'sleep') as sleep:m.check_active(api,'private','public','1')
        self.assertEqual(len(calls),11);self.assertEqual(calls[0],calls[1]);sleep.assert_called_once_with(30)
    def test_public_self_and_conflict(self):
        def api(token,method,url):
            rows=[{'id':1,'name':'Morwen current','head_branch':'main'}] if token=='public' else []
            return {'total_count':len(rows),'workflow_runs':rows}
        m.check_active(api,'private','public','1')
        with patch.object(m.time,'sleep') as sleep:
            with self.assertRaises(m.ActiveSnapshotBlocked):m.check_active(api,'private','public','2')
            self.assertEqual(sleep.call_count,2)
        self.assertEqual(m.STAGE,'PUBLIC_ACTIVE_CONFLICT')
    def test_incomplete_row_blocks(self):
        with patch.object(m.time,'sleep'):
            with self.assertRaises(m.ActiveSnapshotBlocked):m.check_active(lambda *a:{'total_count':1,'workflow_runs':[{'id':1}]},'x','y','1')
        self.assertEqual(m.STAGE,'PRIVATE_ACTIVE_ROW_INCOMPLETE')
if __name__=='__main__':unittest.main()

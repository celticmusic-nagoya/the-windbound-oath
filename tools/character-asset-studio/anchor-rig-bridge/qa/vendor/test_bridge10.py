import unittest,tempfile,json
from pathlib import Path
from bridge10 import run
from bridge08 import JOINTS,VIEWS

class TestBridge10(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.m=Path(self.t.name)/'m.json';self.f=Path(self.t.name)/'f.json'
    def write(self,m,f):
        self.m.write_text(json.dumps(m));self.f.write_text(json.dumps(f))
    def test_empty_blocks(self):
        self.write({'schema':'cas/anchor-bridge/measurement-02','views':{}},{'schema':'cas/anchor-real-frames/08','synthetic':None,'tracks':{}})
        r,t=run(self.m,self.f);self.assertEqual(r['status'],'BLOCKED');self.assertIsNone(t)
    def test_invalid_provenance_blocks(self):
        self.write({'schema':'cas/anchor-bridge/measurement-02','views':{}},{'schema':'cas/anchor-real-frames/08','synthetic':True,'tracks':{}})
        r,t=run(self.m,self.f);self.assertEqual(r['status'],'BLOCKED')
    def test_no_implicit_pose(self):
        self.write({'schema':'cas/anchor-bridge/measurement-02','views':{v:{j:[192,500] for j in ('heelL','heelR','ballL','ballR','toeL','toeR')} for v in VIEWS}}, {'schema':'cas/anchor-real-frames/08','synthetic':False,'tracks':{v:[] for v in VIEWS}})
        r,t=run(self.m,self.f);self.assertEqual(r['status'],'BLOCKED');self.assertIsNone(t)
    def test_negative_threshold(self):
        self.write({},{});
        with self.assertRaises(ValueError):run(self.m,self.f,-1)
    def test_frame_sha_required(self):
        self.write({'schema':'cas/anchor-bridge/measurement-02','views':{}},{'schema':'cas/anchor-real-frames/08','synthetic':False,'tracks':{'front':[{'source':'measured-real-frame'}]}})
        r,t=run(self.m,self.f);self.assertTrue(any('image SHA-256' in e for e in r['errors']))
if __name__=='__main__':unittest.main()

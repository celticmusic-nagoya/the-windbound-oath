import hashlib,json,pathlib,sys,tempfile,unittest
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from verify_morwen_production_readiness import audit,REQUIRED
class ReadinessTests(unittest.TestCase):
 def fixture(self,root):
  rows=[]
  for name in sorted(REQUIRED):
   payload=name.encode()
   (root/name).write_bytes(payload)
   rows.append({"filename":name,"sha256":hashlib.sha256(payload).hexdigest(),"bytes":len(payload)})
  (root/"MANIFEST.json").write_text(json.dumps({"files":rows}))
 def test_exact_source_set(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp);self.fixture(root)
   self.assertEqual(audit(root)["status"],"PASS")
   self.assertEqual(audit(root)["artistic_qa"],"NOT_RUN")
 def test_tampered_source_blocked(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp);self.fixture(root)
   (root/"LAYER0_FRONT.png").write_bytes(b"tampered")
   self.assertEqual(audit(root)["status"],"BLOCKED")
 def test_missing_source_blocked(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp);self.fixture(root)
   (root/"LAYER0_FRONT.png").unlink()
   self.assertEqual(audit(root)["status"],"BLOCKED")
if __name__=="__main__":unittest.main()

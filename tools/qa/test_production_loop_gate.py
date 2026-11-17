import sys,unittest,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from production_loop_gate import decide
BASE={"gates":{"G1":"PASS","G2":"PASS","G3":"PASS","G4":"PASS"},"source_verified":True,"render_sha256_verified":True,"method_family":"new-sculpt","same_cause_attempts":0,"repair_plan_approved":True,"repair_is_non_destructive":True}
class ProductionLoopGateTests(unittest.TestCase):
 def test_next(self):self.assertEqual(decide(BASE)[0],"NEXT_STAGE")
 def test_missing_evidence(self):
  d={**BASE,"render_sha256_verified":False}
  self.assertEqual(decide(d)[0],"BLOCKED")
 def test_missing_gate(self):
  d={**BASE,"gates":{**BASE["gates"],"G2":"NOT_RUN"}}
  self.assertEqual(decide(d)[0],"BLOCKED")
 def test_first_repair(self):
  d={**BASE,"gates":{**BASE["gates"],"G2":"FAIL"}}
  self.assertEqual(decide(d)[0],"REPAIR_AND_RENDER")
 def test_two_failures_stop(self):
  d={**BASE,"gates":{**BASE["gates"],"G2":"FAIL"},"same_cause_attempts":2}
  self.assertEqual(decide(d)[0],"METHOD_SWITCH_REQUIRED")
 def test_unapproved_repair(self):
  d={**BASE,"gates":{**BASE["gates"],"G3":"FAIL"},"repair_plan_approved":False}
  self.assertEqual(decide(d)[0],"BLOCKED")
 def test_canon_fail(self):
  d={**BASE,"gates":{**BASE["gates"],"G1":"FAIL"}}
  self.assertEqual(decide(d)[0],"BLOCKED")
 def test_device_not_run(self):
  d={**BASE,"gates":{**BASE["gates"],"G4":"NOT_RUN"}}
  self.assertEqual(decide(d)[0],"BLOCKED")
if __name__=="__main__":unittest.main()

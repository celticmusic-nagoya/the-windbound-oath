import copy,json,unittest
from pathlib import Path
from tools.map_blender.lind.validate_cliff_macro_contract import validate

BASE=json.loads(Path("docs/production/lind-cliff-macro-support.contract.v1.json").read_text())
class ContractTest(unittest.TestCase):
 def test_valid_candidate(self):self.assertEqual(validate(BASE),[])
 def test_unapproved_metric(self):
  d=copy.deepcopy(BASE);d["bounding_box_m"]=[10,20,30]
  self.assertTrue(validate(d))
 def test_false_game_ready(self):
  d=copy.deepcopy(BASE);d["qa"]["G3"]="PASS"
  self.assertTrue(validate(d))
 def test_story_jump_not_navmesh(self):
  d=copy.deepcopy(BASE);d["directed_story_edges"][0]["walkable"]=True
  self.assertTrue(validate(d))
 def test_region_semantics(self):
  d=copy.deepcopy(BASE);d["regions"][0]["kind"]="river_cliff"
  self.assertTrue(validate(d))
 def test_scan_not_collision(self):
  d=copy.deepcopy(BASE);d["source_scan_is_collision"]=True
  self.assertTrue(validate(d))
 def test_stop_history(self):
  d=copy.deepcopy(BASE);d["stopped_method_families"]=[]
  self.assertTrue(validate(d))
 def test_canon_sha(self):
  d=copy.deepcopy(BASE);d["source_image_sha256"]="0"*64
  self.assertTrue(validate(d))
if __name__=="__main__":unittest.main()

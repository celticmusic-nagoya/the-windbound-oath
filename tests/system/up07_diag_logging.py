"""Original criteria identity and failure-persistence regression; no browser/game mutations."""
import sys,unittest,tempfile,json,subprocess,gzip
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tests/helpers'))
from up07_probe import load_probe,criterion_contract
class Logging(unittest.TestCase):
 def test_original_criteria_and_selectors_unchanged(self):
  old=subprocess.check_output(['git','show','0494f6452548ea476b4cebbc69d9f41d878d540d:tests/moss/m67_up_production.py'],cwd=R,text=True);self.assertEqual(criterion_contract(old),criterion_contract((R/'tests/moss/m67_up_production.py').read_text()))
 def run_case(self,step=18,dt=60,count=26):
  with tempfile.TemporaryDirectory() as d:
   def ck(n,v):
    if not v:raise AssertionError(n)
   p=load_probe(R,d,ck);urls=p['URLS'];rows=[{'x':250,'y':700-i*step,'t':100+i*dt,'src':urls[i%5],'currentSrc':'http://localhost/'+urls[i%5],'loaded':True,'transform':'translateY(-0.2px)','top':'-34.875px','heading':{'dir':'up','flip':False},'frameScale':dt/(1000/60)} for i in range(count)]
   class Page:
    def evaluate(self,expr):return {'start':{'t':100},'end':{'t':100+(count-1)*dt},'input_keys':['ArrowUp'],'viewport':[960,540]}
   failure=None
   try:p['field_check'](Page(),rows,'unit/route')
   except AssertionError as e:failure=str(e)
   folder=Path(d)/'measurements/unit_route';self.assertTrue((folder/'measurement.json').is_file());self.assertTrue((folder/'measurement.log').is_file());self.assertEqual(len(json.load(gzip.open(folder/'raw.json.gz','rt'))['rows']),count);return json.loads((folder/'measurement.json').read_text()),failure
 def test_pass_is_recorded(self):
  m,f=self.run_case();self.assertTrue(m['cadence_pass']);self.assertIsNone(f)
 def test_time_fail_saved_before_assert(self):
  m,f=self.run_case(dt=90);self.assertFalse(m['cadence_pass']);self.assertIn('median_seconds',m['cadence_reason']);self.assertIn('90world/.300second',f)
 def test_distance_fail_saved_before_assert(self):
  m,f=self.run_case(step=5);self.assertFalse(m['cadence_pass']);self.assertIn('median_distance',m['cadence_reason']);self.assertIn('90world/.300second',f)
 def test_insufficient_samples_not_pass(self):
  m,f=self.run_case(count=5);self.assertFalse(m['cadence_pass']);self.assertEqual(m['cycle_window_count'],0);self.assertIn('cycle_windows',m['cadence_reason']);self.assertIsNotNone(f)
 def test_empty_samples_not_pass_and_preserved(self):
  m,f=self.run_case(count=0);self.assertFalse(m['cadence_pass']);self.assertEqual(m['sampling_count'],0);self.assertIsNotNone(f)
if __name__=='__main__':unittest.main()

"""Synthetic checkpoint tests; expected negative cases are not product failures."""
import unittest,tempfile,sys,json,contextlib,io
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/qa'))
from reqa_checkpoint import instrument,Recorder
class Contract(unittest.TestCase):
 def run_source(self,source):
  with tempfile.TemporaryDirectory() as d:
   code,calls=instrument(source,'synthetic.py');rec=Recorder(d,calls,'synthetic');error=None
   try:
    with contextlib.redirect_stdout(io.StringIO()):exec(code,{'__reqa_checkpoint':rec,'__reqa_unhandled':rec.unhandled,'outpath':d})
   except Exception as e:error=str(e)
   entries=[json.loads(x) for x in (Path(d)/'checkpoints.jsonl').read_text().splitlines()];return entries,error,(Path(d)/'failure.json').exists()
 def test_original_assert_failure_is_saved(self):
  rows,error,saved=self.run_source("def ck(n,v):\n assert v,n\nck('negative',False)\nraise RuntimeError('must not continue')")
  self.assertEqual(error,'negative');self.assertFalse(rows[0]['computed_result']);self.assertTrue(saved)
 def test_collecting_check_stops_first_false(self):
  rows,error,saved=self.run_source("failures=[]\ndef check(ok,label):\n if not ok:failures.append(label)\ncheck(False,'first')\ncheck(True,'must not execute')")
  self.assertEqual(error,'first');self.assertEqual(len(rows),1);self.assertTrue(saved)
 def test_true_original_predicate_unchanged(self):
  rows,error,saved=self.run_source("def ck(name,ok):\n assert ok,name\na=3\nck('pass',a==3)")
  self.assertIsNone(error);self.assertFalse(saved);self.assertTrue(rows[0]['computed_result']);self.assertTrue(any('a==3' in call for call in rows[0]['expected_original_call']))
 def test_exception_is_logged_before_context_closes(self):
  source="from pathlib import Path\nclass C:\n def __enter__(self):return self\n def __exit__(self,*args):\n  assert Path(outpath,'failure.json').exists(),'missing evidence before close'\ndef sync_playwright():return C()\ndef ck(n,v):\n assert v,n\nwith sync_playwright():\n ck('before',True)\n raise RuntimeError('boom')"
  rows,error,saved=self.run_source(source);self.assertEqual(error,'boom');self.assertTrue(saved);self.assertFalse(rows[-1]['computed_result'])
 def test_live_failure_snapshot_saved(self):
  with tempfile.TemporaryDirectory() as d:
   class Page:
    called=False
    def is_closed(self):return False
    def evaluate(self,expression):self.called=True;return {'feet':{'x':1,'y':2},'map':'test'}
   page=Page();code,calls=instrument("def ck(n,v):\n assert v,n\np=page\nSTABLE='JSON.stringify({})'\nck('live failure',False)",'synthetic.py');rec=Recorder(d,calls,'synthetic')
   with self.assertRaises(AssertionError):exec(code,{'page':page,'__reqa_checkpoint':rec})
   first=json.loads(Path(d,'failure.json').read_text());self.assertTrue(page.called);self.assertEqual(first['failure_snapshot']['capture'],'read-only failure snapshot');self.assertTrue(Path(d,first['failure_snapshot']['file']).exists())
   try:raise RuntimeError('secondary')
   except RuntimeError:rec.unhandled({}, {})
   self.assertEqual(json.loads(Path(d,'failure.json').read_text())['name'],'live failure')
 def test_same_line_calls_preserved(self):
  rows,error,saved=self.run_source("def ck(n,v):\n assert v,n\nck('a',True);ck('b',False)")
  self.assertEqual(error,'b');self.assertEqual(len(rows[0]['expected_original_call']),2);self.assertEqual(rows[1]['name'],'b')
 def test_missing_checker_is_error(self):
  with self.assertRaises(RuntimeError):instrument('x=1','empty.py')
if __name__=='__main__':unittest.main()

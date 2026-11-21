import tempfile
import unittest
from pathlib import Path
from session_plan import ready, sha

class PlannerTests(unittest.TestCase):
    def test_resume_budget_invalidation_cycle(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            model=root/'model.vroid'
            model.write_bytes(b'abc')
            face=dict(id='face',deps=[],fingerprint='v1',qualified=True,seconds=20)
            hair=dict(id='hair',deps=['face'],fingerprint='v2',qualified=True,seconds=30)
            completed={'face':dict(path='model.vroid',fingerprint='v1',reopened=True,sha256=sha(model))}
            self.assertEqual(ready([face,hair],completed,root,100,20),['hair'])
            self.assertEqual(ready([face,hair],completed,root,40,20),[])
            model.write_bytes(b'xyz')
            self.assertEqual(ready([face,hair],completed,root,100,20),['face'])
            with self.assertRaises(ValueError):
                ready([dict(face,deps=['hair']),hair],completed,root,100,20)

if __name__=='__main__':
    unittest.main()

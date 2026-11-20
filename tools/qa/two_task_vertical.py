"""Offline vertical slice. Synthetic output only; no production queue mutation."""
import tempfile
import unittest
from pathlib import Path
from two_task_key import task_key
from two_task_shared import transition
from two_task_artifact import digest, verify
from two_task_lock import task_lock

class VerticalSlice(unittest.TestCase):
    def test_generate_once_and_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            state={'schema':'two.shared-queue.v1','revision':0,'tasks':{}}
            spec=dict(asset='synthetic',stage='preview',method='fixture',inputs={'source':'a'*64},toolchain={'python':'b'*64},settings={'qa':'c'*64})
            key=task_key(spec)
            state=transition(state,key,'enqueue','fixture-run')
            state=transition(state,key,'claim','fixture-run')
            self.assertIsNone(transition(state,key,'claim','other-run'))
            with task_lock(root/'locks',key) as acquired:
                self.assertTrue(acquired)
                output=root/'fixture.txt'
                output.write_text('synthetic test output',encoding='utf-8')
                manifest=dict(schema='two.artifact.v1',task_key=key,technical_status='PASS',files={'fixture.txt':digest(output)})
                self.assertTrue(verify(root,manifest,key))
                state=transition(state,key,'done','fixture-run')
            self.assertEqual(state['tasks'][key]['state'],'DONE')
            self.assertIsNone(transition(state,key,'enqueue','other-run'))
            self.assertTrue(verify(root,manifest,key))
            with self.assertRaises(ValueError):
                verify(root,manifest,task_key(dict(spec,stage='final')))
            output.write_text('damaged',encoding='utf-8')
            with self.assertRaises(ValueError):
                verify(root,manifest,key)

if __name__=='__main__':
    unittest.main()

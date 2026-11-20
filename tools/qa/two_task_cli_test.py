"""Exercise actual CLI entrypoint, including negative exit codes."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from two_task_key import task_key

class CliTests(unittest.TestCase):
    def test_cli_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            out=root/'preview.txt'
            out.write_text('synthetic CLI fixture')
            spec=dict(asset='fixture',stage='preview',method='test',inputs={'source':'a'*64},toolchain={'runtime':'b'*64},settings={'qa':'c'*64})
            (root/'spec.json').write_text(json.dumps(spec))
            (root/'qa.json').write_text(json.dumps(dict(task_key=task_key(spec),technical_status='PASS')))
            manifest=root/'manifest.json'
            common=['--root',str(root),'--spec',str(root/'spec.json'),'--manifest',str(manifest)]
            env=dict(os.environ,GITHUB_SHA='d'*40,GITHUB_RUN_ID='1')
            def run(mode,*args):
                return subprocess.run([sys.executable,str(Path(__file__).with_name('two_artifact_cli.py')),mode,*common,*args],env=env,capture_output=True,text=True,timeout=15)
            args=['--output','preview.txt','--qa',str(root/'qa.json')]
            first=run('manifest',*args)
            self.assertEqual(first.returncode,0,first.stderr)
            original=manifest.read_bytes()
            self.assertEqual(run('verify').returncode,0)
            self.assertNotEqual(run('manifest',*args).returncode,0)
            self.assertEqual(manifest.read_bytes(),original)
            out.write_text('corrupted')
            self.assertNotEqual(run('verify').returncode,0)
            (root/'qa.json').write_text(json.dumps(dict(task_key='e'*64,technical_status='PASS')))
            self.assertNotEqual(run('manifest',*args).returncode,0)
            self.assertEqual(manifest.read_bytes(),original)

if __name__=='__main__':
    unittest.main()

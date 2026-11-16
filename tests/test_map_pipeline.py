"""Gate mutation tests: corrupted outputs, failed cache, disabled units and input changes."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('pipeline', Path(__file__).resolve().parents[1] / 'tools/map_pipeline/pipeline.py')
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


class PipelineTest(unittest.TestCase):
    def test_protected_source_and_unit_keys(self):
        self.assertNotEqual(p.fingerprint('WORLD', '4.0.2'), p.fingerprint('ROUTE', '4.0.2'))
        self.assertNotEqual(p.fingerprint('WORLD', '4.0.2'), p.fingerprint('WORLD', '4.3.2'))
        with self.assertRaises(AssertionError):
            p.fingerprint('HOME', '4.0.2')

    def test_changed_configuration_invalidates_key(self):
        baseline = p.fingerprint('WORLD', '4.0.2')
        original = p.digest
        with patch.object(p, 'digest', side_effect=lambda f: 'changed' if str(f).endswith('tasks.json') else original(f)):
            self.assertNotEqual(baseline, p.fingerprint('WORLD', '4.0.2'))

    def test_protected_source_mismatch_blocks(self):
        original = p.digest
        with patch.object(p, 'digest', side_effect=lambda f: 'changed' if str(f).endswith('world.blend') else original(f)):
            with self.assertRaisesRegex(AssertionError, 'protected input'):
                p.fingerprint('WORLD', '4.0.2')

    def test_failed_cache_blocks_without_blender(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            unit = base / 'WORLD'
            unit.mkdir()
            (unit / 'state.json').write_text(json.dumps({'unit': 'WORLD', 'input_sha256': p.fingerprint('WORLD', '4.0.2'), 'status': 'FAIL'}))
            with patch.object(p.subprocess, 'run') as launch:
                with self.assertRaisesRegex(AssertionError, 'unchanged failed'):
                    p.run('WORLD', '4.0.2', base)
                launch.assert_not_called()

    def test_integrity_and_qa_gate(self):
        with tempfile.TemporaryDirectory() as d:
            unit = Path(d)
            (unit / 'qa.json').write_text('{"G3":"PASS"}')
            outputs = {'qa.json': p.digest(unit / 'qa.json')}
            import hashlib
            state = {'unit': 'WORLD', 'input_sha256': 'x', 'status': 'PASS', 'outputs': outputs, 'output_sha256': hashlib.sha256(json.dumps(outputs, sort_keys=True).encode()).hexdigest()}
            (unit / 'state.json').write_text(json.dumps(state))
            p.validate(unit, 'WORLD', 'x')
            (unit / 'qa.json').write_text('{"G3":"FAIL"}')
            with self.assertRaisesRegex(AssertionError, 'cached output SHA'):
                p.validate(unit, 'WORLD', 'x')
            state['outputs']['qa.json'] = p.digest(unit / 'qa.json')
            (unit / 'state.json').write_text(json.dumps(state))
            with self.assertRaises(AssertionError):
                p.validate(unit, 'WORLD', 'x')

    def test_integration_cannot_skip_dependency(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                p.integrate(Path(d), '4.0.2')


if __name__ == '__main__':
    unittest.main()

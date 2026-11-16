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

    def test_production_unit_change_keeps_other_unit_key(self):
        with patch.object(p, 'CONFIG', p.ROOT / 'tools/map_pipeline/production_tasks.json'):
            world = p.fingerprint('WORLD', '4.0.2')
            route = p.fingerprint('ROUTE', '4.0.2')
            original = p.digest
            with patch.object(p, 'digest', side_effect=lambda f: 'changed' if str(f).endswith('production_world.py') else original(f)):
                self.assertNotEqual(world, p.fingerprint('WORLD', '4.0.2'))
                self.assertEqual(route, p.fingerprint('ROUTE', '4.0.2'))

    def test_production_partial_qa_is_not_full_or_art_pass(self):
        with tempfile.TemporaryDirectory() as d:
            unit = Path(d)
            qa = {'G3':'PARTIAL_TESTED_SUBSETS_PASS', 'technical_gate':'PASS', 'G2':'NOT_RUN_IMAGE_REVIEW_REQUIRED'}
            (unit / 'qa.json').write_text(json.dumps(qa))
            outputs = {'qa.json':p.digest(unit / 'qa.json')}
            import hashlib
            state = {'unit':'WORLD','input_sha256':'x','status':'PASS','outputs':outputs,'output_sha256':hashlib.sha256(json.dumps(outputs,sort_keys=True).encode()).hexdigest()}
            (unit / 'state.json').write_text(json.dumps(state))
            p.validate(unit,'WORLD','x')
            self.assertNotEqual(json.loads((unit / 'qa.json').read_text())['G2'], 'PASS')
            qa['technical_gate']='FAIL'
            (unit / 'qa.json').write_text(json.dumps(qa))
            state['outputs']['qa.json']=p.digest(unit / 'qa.json')
            (unit / 'state.json').write_text(json.dumps(state))
            with self.assertRaises(AssertionError):
                p.validate(unit,'WORLD','x')

    def test_configuration_cannot_promote_art_to_pass(self):
        with patch.object(p, 'CONFIG', p.ROOT / 'tools/map_pipeline/production_tasks.json'):
            c = p.config()
            c['units']['WORLD']['art_status'] = 'PASS'
            with patch.object(Path, 'read_text', return_value=json.dumps(c)):
                with self.assertRaisesRegex(AssertionError, 'G2 PASS'):
                    p.config()

    def test_integration_cannot_skip_dependency(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                p.integrate(Path(d), '4.0.2')


if __name__ == '__main__':
    unittest.main()

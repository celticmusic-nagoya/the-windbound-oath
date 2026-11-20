"""Content-addressed task identity, not a lease or adoption decision (stdlib)."""
import hashlib
import json
import re
import unittest


def task_key(spec):
    fields = {'asset', 'stage', 'method', 'inputs', 'toolchain', 'settings'}
    if not isinstance(spec, dict) or set(spec) != fields:
        raise ValueError('invalid task fields')
    for name in ('asset', 'stage', 'method'):
        if not isinstance(spec[name], str) or not spec[name].strip():
            raise ValueError(name)
    for name in ('inputs', 'toolchain', 'settings'):
        if not isinstance(spec[name], dict) or not spec[name]:
            raise ValueError(name)
        for key, value in spec[name].items():
            if not isinstance(key, str) or not key or not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
                raise ValueError(name + ': expected named SHA-256')
    payload = json.dumps({'schema': 'two.task-key.v1', **spec}, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return hashlib.sha256(payload.encode('ascii')).hexdigest()


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.spec = dict(asset='morwen', stage='preview', method='sculpt', inputs={'model': 'a'*64, 'blueprint': 'b'*64}, toolchain={'blender': 'c'*64}, settings={'render': 'd'*64})

    def test_order(self):
        other = dict(reversed(list(self.spec.items())))
        other['inputs'] = dict(reversed(list(other['inputs'].items())))
        self.assertEqual(task_key(self.spec), task_key(other))

    def test_changes(self):
        for name in ('asset', 'stage', 'method', 'inputs', 'toolchain', 'settings'):
            with self.subTest(name=name):
                other = dict(self.spec)
                other[name] = {'changed': 'e'*64} if isinstance(other[name], dict) else 'changed'
                self.assertNotEqual(task_key(self.spec), task_key(other))

    def test_invalid(self):
        for name, value in [('inputs', {}), ('inputs', {'model':'unknown'}), ('asset', ''), ('settings', []), ('toolchain', {'blender':'5.3'})]:
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                task_key(dict(self.spec, **{name:value}))

    def test_extra_or_missing(self):
        with self.assertRaises(ValueError):
            task_key(dict(self.spec, head='extra'))
        with self.assertRaises(ValueError):
            task_key({k:v for k,v in self.spec.items() if k != 'method'})


if __name__ == '__main__':
    unittest.main()

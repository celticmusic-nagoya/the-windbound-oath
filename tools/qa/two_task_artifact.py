"""Verify extracted artifact evidence; never infer adoption or cache availability."""
import hashlib
import re
import tempfile
import unittest
from pathlib import Path, PurePosixPath

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def verify(root, manifest, expected_key):
    if not isinstance(expected_key, str) or not re.fullmatch('[0-9a-f]{64}', expected_key):
        raise ValueError('invalid expected key')
    if not isinstance(manifest, dict) or manifest.get('schema') != 'two.artifact.v1' or manifest.get('task_key') != expected_key or manifest.get('technical_status') != 'PASS':
        raise ValueError('ineligible artifact')
    files = manifest.get('files')
    if not isinstance(files, dict) or not files:
        raise ValueError('empty manifest')
    root = Path(root).resolve(strict=True)
    for name, expected in files.items():
        if not isinstance(name, str) or '\\' in name or not name or not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected):
            raise ValueError('invalid file entry')
        p = PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or p.as_posix() != name or name == '.':
            raise ValueError('unsafe path')
        target = root
        for part in p.parts:
            target = target / part
            if target.is_symlink():
                raise ValueError('symlink')
        if not target.is_file() or digest(target) != expected:
            raise ValueError('missing or corrupt evidence')
    return True

class Tests(unittest.TestCase):
    def test_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / 'preview.png'
            path.write_bytes(b'test fixture, not actual render')
            m = dict(schema='two.artifact.v1', task_key='a'*64, technical_status='PASS', files={'preview.png':digest(path)})
            self.assertTrue(verify(root,m,'a'*64))
            with self.assertRaises(ValueError):
                verify(root,m,'b'*64)
            path.write_bytes(b'corrupt')
            with self.assertRaises(ValueError):
                verify(root,m,'a'*64)
    def test_unsafe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'source').write_bytes(b'x')
            (root/'link').symlink_to(root/'source')
            for name in ('../source','/source','link','./source','missing'):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    verify(root,dict(schema='two.artifact.v1',task_key='a'*64,technical_status='PASS',files={name:'b'*64}),'a'*64)
    def test_failed_or_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            for status, files in [('FAIL',{'x':'b'*64}),('PASS',{})]:
                with self.assertRaises(ValueError):
                    verify(tmp,dict(schema='two.artifact.v1',task_key='a'*64,technical_status=status,files=files),'a'*64)

if __name__ == '__main__':
    unittest.main()

import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from w126_save_adapter import OLD, NEW, POST, adapt

OBSERVER = Path(__file__).with_name('w125_save_return.py').read_bytes()
WORKER = b'#!/bin/bash\nset -euo pipefail\n' + OLD + POST + b'cmp source preserved\nnative_save\nreopen_copy\n'
def sha(b): return hashlib.sha256(b).hexdigest()
class Test(unittest.TestCase):
    def test_exact_delta(self):
        out = adapt(WORKER, sha(WORKER), OBSERVER)
        self.assertEqual(out.replace(NEW, OLD), WORKER)
        self.assertIn(POST, out)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'worker.sh'; p.write_bytes(out)
            subprocess.run(['bash', '-n', str(p)], check=True)
    def test_worker_identity(self):
        with self.assertRaises(ValueError): adapt(WORKER, '0'*64, OBSERVER)
    def test_observer_identity(self):
        with self.assertRaises(ValueError): adapt(WORKER, sha(WORKER), OBSERVER+b' ')
    def reject(self, worker):
        with self.assertRaises(ValueError): adapt(worker, sha(worker), OBSERVER)
    def test_duplicate(self): self.reject(WORKER + OLD)
    def test_missing(self): self.reject(WORKER.replace(OLD, b''))
    def test_changed_guard(self): self.reject(WORKER.replace(POST, b'echo unsafe\n'))
    def test_guard_dislocated(self): self.reject(WORKER.replace(POST, b'echo intervening\n'+POST))
    def test_reopen_missing(self): self.reject(WORKER.replace(b'\nreopen_copy\n', b'\n'))
    def test_reopen_out_of_order(self): self.reject(WORKER.replace(b'native_save\nreopen_copy', b'reopen_copy\nnative_save'))
    def test_already_adapted(self): self.reject(WORKER.replace(OLD, NEW))
if __name__ == '__main__': unittest.main(verbosity=2)

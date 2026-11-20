"""Runner-local exclusive lock; never a distributed lease. POSIX only."""
import contextlib
import fcntl
import os
import re
import tempfile
import unittest
from pathlib import Path

@contextlib.contextmanager
def task_lock(root, key):
    if not isinstance(key, str) or not re.fullmatch('[0-9a-f]{64}', key):
        raise ValueError('invalid task key')
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(root / (key + '.lock'), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
        else:
            yield True
    finally:
        os.close(fd)

class Tests(unittest.TestCase):
    def test_exclusion(self):
        with tempfile.TemporaryDirectory() as root:
            with task_lock(root, 'a'*64) as first:
                self.assertTrue(first)
                with task_lock(root, 'a'*64) as second:
                    self.assertFalse(second)
                with task_lock(root, 'b'*64) as independent:
                    self.assertTrue(independent)
            with task_lock(root, 'a'*64) as resumed:
                self.assertTrue(resumed)
    def test_exception_release(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(RuntimeError):
                with task_lock(root, 'a'*64):
                    raise RuntimeError('interrupted')
            with task_lock(root, 'a'*64) as resumed:
                self.assertTrue(resumed)
    def test_invalid(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                with task_lock(root, '../bad'):
                    pass

if __name__ == '__main__':
    unittest.main()

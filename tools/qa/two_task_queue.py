"""Durable single-host FIFO queue. No cross-runner storage implied."""
import sqlite3
import re
import tempfile
import unittest
from pathlib import Path
from contextlib import closing

class Queue:
    def __init__(self, path):
        self.path = path
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, key TEXT UNIQUE NOT NULL, state TEXT NOT NULL DEFAULT 'READY', owner TEXT)")

    def enqueue(self, key):
        if not isinstance(key, str) or not re.fullmatch('[0-9a-f]{64}', key):
            raise ValueError('invalid key')
        with closing(sqlite3.connect(self.path)) as db, db:
            return db.execute('INSERT OR IGNORE INTO tasks(key) VALUES (?)', (key,)).rowcount == 1

    def claim(self, owner):
        if not isinstance(owner, str) or not owner.strip():
            raise ValueError('invalid owner')
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute("SELECT key FROM tasks WHERE state='READY' ORDER BY id LIMIT 1").fetchone()
            if row:
                db.execute("UPDATE tasks SET state='RUNNING', owner=? WHERE key=?", (owner, row[0]))
                return row[0]
            return None

    def finish(self, key, owner, success):
        if type(success) is not bool:
            raise ValueError('invalid result')
        with closing(sqlite3.connect(self.path)) as db, db:
            return db.execute("UPDATE tasks SET state=? WHERE key=? AND owner=? AND state='RUNNING'", ('DONE' if success else 'BLOCKED',key,owner)).rowcount == 1

class Tests(unittest.TestCase):
    def test_fifo_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'queue.db'
            q = Queue(p)
            self.assertTrue(q.enqueue('a'*64))
            self.assertFalse(q.enqueue('a'*64))
            q.enqueue('b'*64)
            other = Queue(p)
            self.assertEqual(q.claim('one'), 'a'*64)
            self.assertEqual(other.claim('two'), 'b'*64)
            self.assertIsNone(other.claim('three'))
            self.assertFalse(other.finish('a'*64,'two',True))
            self.assertTrue(q.finish('a'*64,'one',True))
            self.assertFalse(q.enqueue('a'*64))
    def test_blocked_not_requeued(self):
        with tempfile.TemporaryDirectory() as tmp:
            q = Queue(Path(tmp)/'queue.db')
            q.enqueue('a'*64)
            q.claim('run-1')
            self.assertTrue(q.finish('a'*64,'run-1',False))
            self.assertIsNone(q.claim('run-2'))
    def test_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            q = Queue(Path(tmp)/'queue.db')
            with self.assertRaises(ValueError):
                q.enqueue('bad')
            with self.assertRaises(ValueError):
                q.claim('')

if __name__ == '__main__':
    unittest.main()

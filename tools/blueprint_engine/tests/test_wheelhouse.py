"""Small offline tests for wheel archive verification (no real downloads)."""
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from blueprint_engine import wheelhouse as w


class WheelhouseTests(unittest.TestCase):
    def records(self, root):
        records = []
        for name in sorted(w.LOCK):
            payload = name.encode()
            filename = w.WHEELS[name]
            (root / filename).write_bytes(payload)
            records.append(dict(name=name, version=w.LOCK[name], filename=filename,
                                sha256=hashlib.sha256(payload).hexdigest(), size=len(payload)))
        return records

    def test_valid_exact_archive_inventory(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            records = self.records(root)
            w.verify_wheels(root, records)
            self.assertTrue(w.lock_key(records).startswith("two-bpy-wheel-v1-"))

    def test_same_size_corruption_rejected(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            records = self.records(root)
            row = records[0]
            (root / row["filename"]).write_bytes(b"x" * row["size"])
            with self.assertRaisesRegex(ValueError, "SHA mismatch"):
                w.verify_wheels(root, records)

    def test_extra_or_symlink_rejected(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            records = self.records(root)
            extra = root / "unexpected"
            extra.write_text("bad")
            with self.assertRaisesRegex(ValueError, "inventory"):
                w.verify_wheels(root, records)
            extra.unlink()
            row = records[0]
            path = root / row["filename"]
            path.unlink()
            path.symlink_to(root / records[1]["filename"])
            with self.assertRaisesRegex(ValueError, "unsafe wheel file"):
                w.verify_wheels(root, records)

    def test_incomplete_or_duplicate_lock_rejected(self):
        with TemporaryDirectory() as d:
            records = self.records(Path(d))
            for bad in (records[:-1], records[:-1] + records[:1]):
                with self.assertRaises(ValueError):
                    w.lock_key(bad)

    def test_upstream_metadata_must_be_exact_and_not_yanked(self):
        name = "bpy"
        row = dict(filename=w.WHEELS[name], yanked=False, packagetype="bdist_wheel",
                   digests={"sha256":"a"*64}, size=100)
        data = dict(info={"version":w.LOCK[name]}, urls=[row])
        self.assertEqual(w.select_record(name, data)["sha256"], "a"*64)
        row["yanked"] = True
        with self.assertRaises(ValueError):
            w.select_record(name, data)

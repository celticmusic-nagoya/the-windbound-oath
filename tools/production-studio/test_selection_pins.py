"""Validate curated Studio selections without downloading private native archives."""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent
HEX = re.compile(r"[0-9a-f]{64}\Z")
HEAD = re.compile(r"[0-9a-f]{40}\Z")


class SelectionPinsTests(unittest.TestCase):
    def test_curated_entries_have_consistent_provenance(self):
        items = json.loads((ROOT / "sync-selection.json").read_text(encoding="utf-8"))
        seen = set()
        for item in items:
            with self.subTest(artifact=item["artifact_id"]):
                self.assertIs(type(item["artifact_id"]), int)
                self.assertIs(type(item["run_id"]), int)
                self.assertGreater(item["artifact_id"], 0)
                self.assertGreater(item["run_id"], 0)
                self.assertRegex(item["head"], HEAD)
                key = (item["run_id"], item["artifact_id"])
                self.assertNotIn(key, seen)
                seen.add(key)
                entries = item["entries"]
                self.assertTrue(entries)
                self.assertEqual(len(entries), len(set(entries)))
                self.assertIn(item["cover"], entries)
                for entry in entries:
                    path = pathlib.PurePosixPath(entry)
                    self.assertFalse(path.is_absolute())
                    self.assertNotIn("..", path.parts)
                    self.assertNotIn("\\", entry)
                    self.assertIn(path.suffix.lower(), {".png", ".jpg", ".jpeg", ".glb", ".vrm"})
                for name, digest in item.get("entry_sha256", {}).items():
                    self.assertIn(name, entries)
                    self.assertRegex(digest, HEX)

    def test_hairharpy_v3_v4_exact_pins(self):
        items = json.loads((ROOT / "sync-selection.json").read_text(encoding="utf-8"))
        by_id = {item["artifact_id"]: item for item in items}
        for artifact_id, count in ((14782219448, 3), (14783679154, 15)):
            with self.subTest(artifact=artifact_id):
                item = by_id[artifact_id]
                self.assertEqual(len(item["entries"]), count)
                self.assertEqual(set(item["entries"]), set(item["entry_sha256"]))
                self.assertIn("隔離検証", item["stage"])
                self.assertIn("github.com/celticmusic-nagoya/the-windbound-oath/pull/474", item["review_ref"])
                self.assertRegex(item["artifact_digest"], re.compile(r"sha256:[0-9a-f]{64}\Z"))
                self.assertTrue(item["expires_at"].endswith("Z"))


if __name__ == "__main__":
    unittest.main()

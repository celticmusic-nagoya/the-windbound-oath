"""Validate curated Studio selections without downloading private native archives."""
import json
import pathlib
import re
import unittest
from artifact_availability import archive_budget

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

    def test_world_wip_images_have_exact_receipts_and_no_native_files(self):
        items = json.loads((ROOT / "sync-selection.json").read_text(encoding="utf-8"))
        receipts = json.loads((ROOT / "publication-approvals.json").read_text(encoding="utf-8"))["entries"]
        by_sha = {r["sha256"]: r for r in receipts}
        self.assertEqual(len(by_sha), len(receipts))
        by_id = {item["artifact_id"]: item for item in items}
        for aid, count in ((15075315647, 5), (15075731907, 7), (15076007596, 18), (14626605689, 8), (14600421099, 1), (15032255249, 2)):
            item = by_id[aid]
            self.assertEqual(item["category"], "world")
            self.assertEqual(len(item["entries"]), count)
            self.assertEqual(set(item["entries"]), set(item["entry_sha256"]))
            self.assertRegex(item["artifact_digest"], re.compile(r"sha256:[0-9a-f]{64}\Z"))
            if aid in {14626605689, 14600421099, 15032255249}:
                self.assertEqual(set(item["entries"]), set(item["entry_subcategories"]))
                self.assertTrue(set(item["entry_subcategories"].values()) <= {"plant", "tree", "forest"})
            for name, sha in item["entry_sha256"].items():
                self.assertTrue(name.endswith(".png"))
                r = by_sha[sha]
                self.assertEqual((r["head"], r["run_id"], r["artifact_id"], r["name"], r["path"]),
                                 (item["head"], item["run_id"], aid, name, "published/" + sha + ".png"))
                self.assertEqual(r["approval_ref"], item["review_ref"])
                self.assertIn("director-approved-studio-work-in-progress-publication", r["approval_ref"])


    def test_cliff_v5_wip_exact_receipts(self):
        items = json.loads((ROOT / "sync-selection.json").read_text(encoding="utf-8"))
        receipts = json.loads((ROOT / "publication-approvals.json").read_text(encoding="utf-8"))["entries"]
        item = next(x for x in items if x["artifact_id"] == 15109973314)
        self.assertEqual(item["run_id"], 45807905449)
        self.assertEqual(item["category"], "cliff")
        self.assertIn("G2 HOLD", item["stage"])
        self.assertEqual(set(item["entries"]), {"candidate.png", "oblique.png"})
        self.assertEqual(set(item["entry_sha256"]), set(item["entries"]))
        self.assertEqual(item["artifact_digest"], "sha256:f4fbd642fdb0a74f0579d2bca5f8bb0643d1aeb50cbbfdfa266c434387638aa3")
        by_sha = {r["sha256"]: r for r in receipts}
        for name, sha in item["entry_sha256"].items():
            receipt = by_sha[sha]
            self.assertEqual((receipt["head"], receipt["run_id"], receipt["artifact_id"], receipt["name"], receipt["path"], receipt["approval_ref"]),
                             (item["head"], item["run_id"], item["artifact_id"], name, "published/" + sha + ".png", item["review_ref"]))


    def test_v82e_large_archive_exact_image_only_exception(self):
        items = json.loads((ROOT / "sync-selection.json").read_text())
        receipts = json.loads((ROOT / "publication-approvals.json").read_text())["entries"]
        item = next(x for x in items if x["artifact_id"] == 15177030518)
        self.assertEqual(archive_budget(item), 139463532)
        self.assertEqual(archive_budget({}), 128*1024*1024)
        self.assertEqual(len(item["entries"]), 6)
        self.assertTrue(all(n.endswith(".png") for n in item["entries"]))
        self.assertEqual(set(item["entries"]), set(item["entry_subcategories"]))
        by_sha = {r["sha256"]: r for r in receipts}
        for name, sha in item["entry_sha256"].items():
            r = by_sha[sha]
            self.assertEqual((r["head"], r["run_id"], r["artifact_id"], r["name"], r["path"], r["approval_ref"]),
                             (item["head"], item["run_id"], item["artifact_id"], name, "published/"+sha+".png", item["review_ref"]))
        for changes in ({"artifact_id":1},{"run_id":2},{"head":"a"*40},{"artifact_digest":"sha256:"+"a"*64},
                        {"exact_archive_bytes":160*1024*1024},{"reuse_retained":False},{"entries":item["entries"]+["native.blend"]},
                        {"entry_sha256":dict(item["entry_sha256"], **{item["entries"][0]:"a"*64})}):
            with self.assertRaises(ValueError):
                archive_budget(dict(item,**changes))

if __name__ == "__main__":
    unittest.main()

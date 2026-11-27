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

    def test_v83_review_only_transport_pins(self):
        items = json.loads((ROOT / "sync-selection.json").read_text())
        item = next(x for x in items if x["artifact_id"] == 15177623362)
        self.assertEqual((item["run_id"], item["head"]), (45953942216, "e91779c99004b69303d0af411fdd4ab8258e206c"))
        self.assertEqual(item["artifact_digest"], "sha256:d205f0aa85b527255c591132681eb9893db3b0644f84f61a4497cbd6e11288bb")
        self.assertEqual(len(item["entries"]), 8)
        self.assertEqual(set(item["entries"]), set(item["entry_sha256"]))
        self.assertTrue(all(n.startswith("v83_") and n.endswith(".png") for n in item["entries"]))
        self.assertEqual(set(item["entry_subcategories"].values()), {"sanctuary"})
        self.assertNotIn("exact_archive_bytes", item)
        self.assertIn("G2 HOLD", item["stage"])
        receipts = {r["sha256"]:r for r in json.loads((ROOT / "publication-approvals.json").read_text())["entries"]}
        for name, sha in item["entry_sha256"].items():
            r = receipts[sha]
            self.assertEqual((r["head"], r["run_id"], r["artifact_id"], r["name"], r["path"], r["approval_ref"]),
                             (item["head"], item["run_id"], item["artifact_id"], name, "published/"+sha+".png", item["review_ref"]))

    def test_v85_review_only_transport_pins(self):
        items = json.loads((ROOT / "sync-selection.json").read_text())
        item = next(x for x in items if x["artifact_id"] == 15179971100)
        self.assertEqual((item["run_id"], item["head"]), (45958764679, "11f64a5cc71e59d1872499b61d3624d36ce85cd1"))
        self.assertEqual(item["artifact_digest"], "sha256:d514e004d533174d515762121ac9e78294127417ac94741327c18a84aebc7662")
        self.assertEqual(item["entry_sha256"], {"v85_A_altar_approach.png":"c42416e53687a38c5691a9a05c010faec5506a7842e4656d00d6ecf02881ae2b","v85_A_altar_front.png":"9faf8719e5052aa669692bd192251e499624e6764da88a75511a73d3ad555f01","v85_A_player_eye.png":"8001813cf2eba3611d66f8bacfdeb2e9922ac126ec656702223745cf9baff557","v85_B_altar_approach.png":"71304ff3c5f7ecfa1512957f76724c563b73ecc1da9a20d38ac1ec652226237e","v85_B_altar_front.png":"d4aaf7fed38334ab4f6150a5495665bb7ea5b8d61bf899cb951e72f9baec8614","v85_B_player_eye.png":"c5e13b64abb399dcd461f55efc84420b1c7267f655731a11564930aa37316a2d","v85_C_altar_approach.png":"06a01383dc07519e41f569e8fdbfa844bb392e68682b869746906d608492d3d2","v85_C_altar_front.png":"b9e7fcc0e3c3aa89c8762f90624e46e7ce9393a22c8e3b728f81031ab015ce1f","v85_C_player_eye.png":"2ee68c25823429604d853bc1b173aae67da709d5f02bfc0a5dd17b122349cde7"})
        self.assertEqual(set(item["entries"]), set(item["entry_sha256"]))
        self.assertEqual(set(item["entry_subcategories"].values()), {"sanctuary"})
        self.assertIn("G2 HOLD", item["stage"])
        self.assertNotIn("exact_archive_bytes", item)
        receipts = {r["sha256"]: r for r in json.loads((ROOT / "publication-approvals.json").read_text())["entries"]}
        for name, sha in item["entry_sha256"].items():
            r = receipts[sha]
            self.assertEqual((r["head"], r["run_id"], r["artifact_id"], r["name"], r["path"], r["approval_ref"]),
                             (item["head"], item["run_id"], item["artifact_id"], name, "published/"+sha+".png", item["review_ref"]))

if __name__ == "__main__":
    unittest.main()

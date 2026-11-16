"""Negative controls for four-view candidate artifacts; synthetic PNG headers only."""
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from verify_morwen_four_views import verify, DIRECTIONS

class FourViewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.report = {"status": "PASS_FOUR_RENDER_FILES_ONLY", "source_unchanged": True,
                       "source_sha256": "a"*64, "source_sha256_after": "a"*64,
                       "canonical_design_match": "BLOCKED", "artistic_qa": "NOT_RUN", "views": []}
        for direction in DIRECTIONS:
            name = "MORWEN_QA_" + direction.upper() + ".png"
            # Header fixture checks evidence structure; not a rendered or valid decoded image.
            raw = b"\x89PNG\r\n\x1a\n" + b"\x00"*8 + (512).to_bytes(4,"big") + (768).to_bytes(4,"big")
            (self.root/name).write_bytes(raw)
            self.report["views"].append({"direction": direction, "filename": name,
                "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                "status": "RENDERED_NOT_ART_REVIEWED"})
        self.save()
    def tearDown(self):
        self.tmp.cleanup()
    def save(self):
        (self.root/"MORWEN_FOUR_VIEW_REPORT.json").write_text(json.dumps(self.report))
    def test_valid_evidence_shape(self):
        self.assertEqual(verify(self.root)["status"], "PASS_FOUR_FILES_ONLY")
    def test_missing_view(self):
        self.report["views"].pop(); self.save()
        self.assertEqual(verify(self.root)["status"], "BLOCKED")
    def test_mutated_png(self):
        (self.root/"MORWEN_QA_FRONT.png").write_bytes(b"bad")
        self.assertEqual(verify(self.root)["status"], "BLOCKED")
    def test_duplicate_direction(self):
        self.report["views"][1]["direction"] = "front"; self.save()
        self.assertEqual(verify(self.root)["status"], "BLOCKED")
    def test_mutated_source(self):
        self.report["source_unchanged"] = False; self.save()
        self.assertEqual(verify(self.root)["status"], "BLOCKED")
    def test_forged_art_approval(self):
        self.report["artistic_qa"] = "PASS"; self.save()
        self.assertEqual(verify(self.root)["status"], "BLOCKED")
    def test_wrong_dimensions(self):
        p=self.root/"MORWEN_QA_FRONT.png"
        raw=p.read_bytes(); raw=raw[:16]+(256).to_bytes(4,"big")+raw[20:]
        p.write_bytes(raw)
        self.report["views"][0]["sha256"]=hashlib.sha256(raw).hexdigest()
        self.save()
        self.assertEqual(verify(self.root)["status"], "BLOCKED")
if __name__ == "__main__":
    unittest.main()

import unittest
from tools.map_blender.validate_agent_request import validate

class RequestValidationTests(unittest.TestCase):
    def test_allowed_claude_dry_run(self):
        self.assertEqual(validate({"agent":"claude","task":"MAP-ASSET-RESEARCH-01","mode":"dry_run"})["agent"],"claude")
    def test_allowed_codex_dry_run(self):
        self.assertEqual(validate({"agent":"codex","task":"MAP-PIPELINE-01","mode":"dry_run"})["agent"],"codex")
    def test_agent_task_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            validate({"agent":"claude","task":"MAP-PIPELINE-01","mode":"dry_run"})
    def test_arbitrary_task_rejected(self):
        with self.assertRaises(ValueError):
            validate({"agent":"codex","task":"RUN-SHELL","mode":"dry_run"})
    def test_extra_keys_rejected(self):
        with self.assertRaises(ValueError):
            validate({"agent":"codex","task":"MAP-PIPELINE-01","mode":"dry_run","command":"rm -rf ."})
    def test_invalid_mode_rejected(self):
        with self.assertRaises(ValueError):
            validate({"agent":"codex","task":"MAP-PIPELINE-01","mode":"unsafe"})
    def test_non_object_rejected(self):
        with self.assertRaises(ValueError):
            validate(["claude","MAP-ASSET-RESEARCH-01"])
if __name__=="__main__":
    unittest.main()

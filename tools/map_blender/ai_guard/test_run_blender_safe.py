import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from run_blender_safe import run

class RunnerTest(unittest.TestCase):
    def test_env_excludes_secrets_and_preserves_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "input.blend"
            source.write_bytes(b"BLENDER-DUMMY")
            proposal = base / "feedback.json"
            proposal.write_text(json.dumps(dict(schema="two-render-patch-v1", asset_id="house",
                method_family="light", root_cause="dark", adjustments={"exposure_delta": 0.1})))
            out = base / "candidate.png"
            def fake_run(command, **kwargs):
                self.assertNotIn("OPENAI_API_KEY", kwargs["env"])
                self.assertNotIn("GITHUB_TOKEN", kwargs["env"])
                self.assertNotIn("PYTHONPATH", kwargs["env"])
                self.assertIn("--disable-autoexec", command)
                out.write_bytes(b"PNG-DUMMY")
                return type("Process", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()
            with patch("run_blender_safe.subprocess.run", side_effect=fake_run):
                report = run("/usr/bin/blender", source, proposal, out)
            self.assertEqual(report["returncode"], 0)
            self.assertEqual(source.read_bytes(), b"BLENDER-DUMMY")
            self.assertTrue((base / "candidate.report.json").exists())

    def test_reject_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "a.blend"
            source.write_bytes(b"source")
            output = base / "out.png"
            output.write_bytes(b"existing")
            with self.assertRaises(FileExistsError):
                run("/usr/bin/blender", source, base / "absent.json", output)

if __name__ == "__main__":
    unittest.main()

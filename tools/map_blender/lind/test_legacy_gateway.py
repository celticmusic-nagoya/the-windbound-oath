from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

GATEWAY = Path(__file__).resolve().parents[1] / "lind_spatial_assemble.py"


class LegacyIsolationTests(unittest.TestCase):
    def test_new_world_call_is_blocked_before_loading_blender_or_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "world.blend"
            result = subprocess.run([sys.executable, str(GATEWAY), "--", "--layout",
                                     "missing.json", "--out", str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("metric spatial contract is not approved", result.stderr)
            self.assertNotIn("No module named", result.stderr)
            self.assertFalse(output.exists())

    def test_explicit_legacy_call_cannot_overwrite_an_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "protected.blend"
            output.write_bytes(b"existing source")
            result = subprocess.run([sys.executable, str(GATEWAY), "--legacy-layout", "--layout",
                                     "missing.json", "--out", str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("refusing to overwrite", result.stderr)
            self.assertEqual(output.read_bytes(), b"existing source")


if __name__ == "__main__":
    unittest.main()

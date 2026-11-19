"""Regression tests for the bounded macro geometry preflight."""
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("build_cliff_macro_support.py").resolve()


class MacroPreflightTest(unittest.TestCase):
    def run_python(self, *args):
        return subprocess.run(
            [sys.executable, *args],
            cwd=SCRIPT.parent,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_production_builder_finishes_with_expected_counts(self):
        result = self.run_python(str(SCRIPT), "--preflight")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("MACRO_PREFLIGHT_PASS vertices=4290 faces=4288", result.stdout)

    def test_memory_limit_is_applied_before_geometry(self):
        result = self.run_python("-c", """
import build_cliff_macro_support as macro
def oversized_geometry():
    return bytearray(600 * 1024 * 1024)
macro.build_geometry = oversized_geometry
raise SystemExit(macro.preflight())
""")
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn("MACRO_PREFLIGHT_MEMORY_LIMIT", result.stderr)

    def test_wrong_counts_fail(self):
        result = self.run_python("-c", """
import build_cliff_macro_support as macro
macro.build_geometry = lambda: ([], [])
raise SystemExit(macro.preflight())
""")
        self.assertEqual(result.returncode, 4, result.stderr)
        self.assertIn("MACRO_PREFLIGHT_COUNTS", result.stderr)


if __name__ == "__main__":
    unittest.main()

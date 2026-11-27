"""Runtime preparation decisions; no network or real installation in unit tests."""
import os
import subprocess
import unittest
from unittest.mock import patch

from blueprint_engine import ensure_runtime as runtime


class RuntimePreparationTests(unittest.TestCase):
    def test_verified_environment_reused_without_pip(self):
        with patch.object(runtime, "check_platform"), patch.object(runtime, "mismatches", return_value={}), patch.object(runtime.subprocess, "run") as run:
            record = runtime.prepare()
            self.assertEqual(record["route"], "REUSED")
            self.assertEqual(record["pip_install_calls"], 0)
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0][1:3], ["-I", "-c"])

    def test_install_exact_wheels_once_then_verify(self):
        with patch.object(runtime, "check_platform"), patch.object(runtime, "mismatches", side_effect=[{"bpy": None}, {}]), patch.object(runtime.subprocess, "run") as run:
            record = runtime.prepare()
            self.assertEqual(record["pip_install_calls"], 1)
            self.assertEqual(run.call_count, 2)
            command = run.call_args_list[0].args[0]
            self.assertIn("--only-binary=:all:", command)
            self.assertIn("--retries", command)
            self.assertEqual(command[command.index("--retries") + 1], "0")
            self.assertEqual(run.call_args_list[0].kwargs["timeout"], 180)
            self.assertTrue(all(f"{k}=={v}" in command for k, v in runtime.LOCK.items()))

    def test_timeout_never_retries(self):
        with patch.object(runtime, "check_platform"), patch.object(runtime, "mismatches", return_value={"bpy": None}), patch.object(runtime.subprocess, "run", side_effect=subprocess.TimeoutExpired("pip", 180)) as run:
            with self.assertRaises(subprocess.TimeoutExpired):
                runtime.prepare()
            run.assert_called_once()

    def test_matching_metadata_bad_runtime_not_reinstalled(self):
        with patch.object(runtime, "check_platform"), patch.object(runtime, "mismatches", return_value={}), patch.object(runtime.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "verify")) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                runtime.prepare()
            run.assert_called_once()

    def test_post_install_version_mismatch_blocks_runtime(self):
        with patch.object(runtime, "check_platform"), patch.object(runtime, "mismatches", side_effect=[{"bpy": None}, {"bpy": "other"}]), patch.object(runtime.subprocess, "run") as run:
            with self.assertRaisesRegex(RuntimeError, "locked versions"):
                runtime.prepare()
            run.assert_called_once()

    def test_child_environment_excludes_transfer_tokens_and_overrides(self):
        with patch.dict(os.environ, {"GH_TOKEN": "test", "HANDOFF_TOKEN": "test",
                                      "PIP_INDEX_URL": "test", "PYTHONPATH": "test", "PATH": "/bin"}, clear=True):
            self.assertEqual(runtime.child_env(), {"PATH": "/bin"})

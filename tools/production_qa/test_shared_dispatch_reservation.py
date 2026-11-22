import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from urllib.parse import parse_qs, urlsplit

from classify_actions_jobs import FIELDS
from shared_asset_lease import assert_owned, release
from shared_dispatch_reservation import reserve


class ReservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        cwd = Path.cwd()
        self.addCleanup(os.chdir, cwd)
        os.chdir(self.temp.name)
        self.git("init", "-q")
        self.git("-c", "user.name=QA", "-c", "user.email=qa@invalid",
                 "commit", "--allow-empty", "-qm", "test")
        self.git("init", "--bare", "-q", "remote.git")
        self.head = self.git("rev-parse", "HEAD")
        self.path = ".github/workflows/qa.yml"
        self.request = {field: "a" * 64 for field in FIELDS}
        self.request.update(asset_id="LIND-HOME", stage="fixture",
                            workflow_path=self.path, branch="branch/qa",
                            head_sha=self.head, prerequisites_verified=True)
        self.runs = []

    def git(self, *args):
        return subprocess.check_output(["git", *args], text=True).strip()

    def get(self, url, token):
        if "/branches/" in url:
            return {"commit": {"sha": self.head}}
        page = int(parse_qs(urlsplit(url).query)["page"][0])
        return {"total_count": len(self.runs),
                "workflow_runs": self.runs if page == 1 else []}

    def reserve(self, ledger=(), **kwargs):
        return reserve("owner/repo", "remote.git", self.request, ledger, {self.path},
                       "fixture-token", get=self.get, **kwargs)

    def test_cas_excludes_second_reservation(self):
        response = self.reserve(writers_migrated=True)
        self.assertEqual(response["decision"], "RESERVED")
        token = response["token"]
        assert_owned("remote.git", "LIND-HOME", token)
        with self.assertRaises(subprocess.CalledProcessError):
            self.reserve(writers_migrated=True)
        release("remote.git", "LIND-HOME", token)

    def test_unmigrated_and_old_writer_stop_before_reservation(self):
        self.assertEqual(self.reserve(writers_migrated=False)["decision"],
                         "BLOCKED_WRITER_MIGRATION")
        self.runs.append(dict(id=10, head_sha="b" * 40, path=self.path,
                              head_branch="other", event="push", status="queued"))
        self.assertEqual(self.reserve(writers_migrated=True)["decision"],
                         "BLOCKED_ACTIVE_WRITER")
        self.assertFalse(self.git("ls-remote", "--refs", "remote.git"))

    def test_success_needs_current_artifact_bytes(self):
        self.runs.append(dict(id=10, head_sha=self.head, path=self.path,
                              head_branch="branch/qa", event="push",
                              status="completed", conclusion="success"))
        old = dict(self.request, status="SUCCESS", run_id=10, artifact={},
                   artifact_accessible=True, artifact_sha256_verified=True,
                   output_contract_verified=True)
        self.assertEqual(self.reserve(writers_migrated=True)["decision"], "REVIEW_REQUIRED")
        self.assertEqual(self.reserve([old], writers_migrated=True,
                                      verify_artifact=lambda *args: False)["decision"],
                         "BLOCKED_ARTIFACT")
        self.assertEqual(self.reserve([old], writers_migrated=True,
                                      verify_artifact=lambda *args: True)["decision"],
                         "REUSE_SUCCESS")
        self.assertFalse(self.git("ls-remote", "--refs", "remote.git"))


if __name__ == "__main__":
    unittest.main()

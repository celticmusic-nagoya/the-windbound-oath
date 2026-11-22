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
                            head_sha=self.head, prerequisites_verified=True,
                            target_id="blanket", dependency_hashes={"native": "b" * 64})
        self.handoff = {key: self.request[key] for key in
                        ("asset_id", "stage", "head_sha", "branch", "workflow_path")}
        self.handoff.update(
            owner="owner", owner_ack_ref="owner-proof", owner_ack_verified=True, verified_by="coordinator",
            recovery_authority="supervisor", recovery_authority_ref="approval-proof",
            native_sha256=self.request["source_sha256"], dependencies=self.request["dependency_hashes"].copy(),
            stopped_writers={self.path: "workflow-ack", "desktop": "desktop-ack"},
            writer_inventory_verified=True,
            design={"sha256": self.request["reference_sha256"], "target_id": "blanket",
                    "tolerances": {"displacement": 0.0}},
        )
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
        kwargs.setdefault("handoff", self.handoff)
        return reserve("owner/repo", "remote.git", self.request, ledger, {self.path},
                       "fixture-token", get=self.get, **kwargs)

    def test_cas_excludes_second_reservation(self):
        response = self.reserve(writers_migrated=True)
        self.assertEqual(response["decision"], "RESERVED")
        self.assertRegex(response["handoff_sha256"], "^[0-9a-f]{64}$")
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

    def test_missing_or_mismatched_handoff_blocks_before_network(self):
        for handoff, issue in (
            (None, "handoff"),
            ({**self.handoff, "asset_id": "LIND-CLIFF"}, "asset_id"),
            ({**self.handoff, "owner_ack_verified": False}, "owner_ack"),
            ({**self.handoff, "head_sha": "0" * 40}, "head_sha"),
            ({**self.handoff, "dependencies": {}}, "dependencies"),
            ({**self.handoff, "stopped_writers": {"desktop": "ack"}}, "stopped_writers"),
            ({**self.handoff, "recovery_authority_ref": ""}, "recovery_authority"),
            ({**self.handoff, "design": {**self.handoff["design"], "tolerances": {"x": True}}},
             "design_tolerances"),
        ):
            with self.subTest(issue=issue):
                def unreachable(*args):
                    self.fail("incomplete readiness reached the network")
                decision = reserve("owner/repo", "remote.git", self.request, [], {self.path},
                                   "fixture-token", writers_migrated=True, handoff=handoff,
                                   get=unreachable)
                self.assertEqual(decision["decision"], "BLOCKED_PRODUCTION_READINESS")
                self.assertIn(issue, decision["missing_or_mismatched"])
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

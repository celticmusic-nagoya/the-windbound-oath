"""Regression for the dispatcher-to-worker lease handoff and checkpoint fence."""
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from session_plan import sha
from shared_asset_lease import acquire, assert_owned, claim_reservation, git, publish_checkpoint, release
from shared_session_controller import run


class FencedSessionTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.addCleanup(os.chdir, Path.cwd())
        os.chdir(temp.name)
        self.root = Path.cwd()
        git("init", "-q")
        git("config", "user.name", "QA")
        git("config", "user.email", "qa@invalid")
        git("init", "--bare", "-q", "isolated.git")
        git("commit", "--allow-empty", "-qm", "dispatch revision")
        self.commit = git("rev-parse", "HEAD")
        self.asset = "LIND-CLIFF"
        self.remote = "isolated.git"
        self.reservation = acquire(self.remote, self.asset, self.commit)
        self.states = {}
        self.previous = None
        self.tokens = [self.reservation]
        self.stages = [
            dict(id="first", deps=[], seconds=10, qualified=True, fingerprint="first"),
            dict(id="second", deps=["first"], seconds=10, qualified=True, fingerprint="second"),
        ]

    def execute(self, stage, token, deadline):
        if stage["id"] == "first":
            self.assertNotEqual(token, self.reservation)
            self.tokens.append(token)
        self.assertEqual(token, self.tokens[-1])
        path = self.root / stage["id"]
        path.write_text(stage["id"])
        return dict(path=path.name, sha256=sha(path), reopened=True,
                    fingerprint=stage["fingerprint"])

    def persist(self, records, token, deadline):
        git("add", *[record["path"] for record in records.values()])
        git("commit", "-qm", "new checkpoint")
        current = git("rev-parse", "HEAD")
        successor = publish_checkpoint(self.remote, self.asset, token, current, self.previous)
        self.previous = current
        self.tokens.append(successor)
        return successor

    def worker(self, commit=None, execute=None, persist=None):
        return run(self.remote, self.asset, commit or self.commit, self.root,
                   self.stages, self.states, execute or self.execute, persist or self.persist,
                   budget=60, reserve=10, reservation=self.reservation, fenced=True)

    def test_rotates_token_for_each_stage_and_releases_latest(self):
        self.assertEqual(self.worker(), ["first", "second"])
        self.assertEqual(len(set(self.tokens)), 4)
        self.assertTrue(set(self.states) == {"first", "second"})
        with self.assertRaisesRegex(RuntimeError, "lease lost"):
            assert_owned(self.remote, self.asset, self.tokens[-1])

    def test_rejects_other_dispatch_revision_before_execution(self):
        with self.assertRaisesRegex(RuntimeError, "lease revision mismatch"):
            self.worker(commit="0" * 40)
        self.assertFalse(self.states)
        assert_owned(self.remote, self.asset, self.reservation)

    def test_only_one_worker_can_claim_the_dispatched_revision(self):
        def claim(_):
            try:
                return claim_reservation(self.remote, self.asset, self.reservation, self.commit)
            except (RuntimeError, subprocess.CalledProcessError):
                return None

        with ThreadPoolExecutor(max_workers=2) as executor:
            winners = [value for value in executor.map(claim, (0, 1)) if value]
        self.assertEqual(len(winners), 1)
        assert_owned(self.remote, self.asset, winners[0])

    def test_interruption_retains_rotated_token_and_first_checkpoint(self):
        def execute(stage, token, deadline):
            if stage["id"] == "second":
                self.assertEqual(token, self.tokens[-1])
                raise RuntimeError("interrupted")
            return self.execute(stage, token, deadline)

        with self.assertRaisesRegex(RuntimeError, "interrupted"):
            self.worker(execute=execute)
        self.assertEqual(set(self.states), {"first"})
        with self.assertRaisesRegex(RuntimeError, "lease lost"):
            release(self.remote, self.asset, self.reservation)
        assert_owned(self.remote, self.asset, self.tokens[-1])

    def test_does_not_accept_unfenced_checkpoint(self):
        with self.assertRaisesRegex(RuntimeError, "publication unconfirmed"):
            self.worker(persist=lambda records, token, deadline: token)
        self.assertFalse(self.states)
        assert_owned(self.remote, self.asset, self.tokens[-1])


if __name__ == "__main__":
    unittest.main()

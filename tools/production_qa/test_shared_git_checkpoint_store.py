import os
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest

from session_plan import sha
from shared_asset_lease import acquire, assert_owned, git, release
from shared_git_checkpoint_store import GitCheckpointStore, restore_checkpoint
from shared_session_controller import run


class GitCheckpointStoreTests(unittest.TestCase):
    def test_controller_restores_only_pending_stage_across_fresh_checkouts(self):
        with TemporaryDirectory() as directory:
            base = Path(directory)
            old = Path.cwd()
            self.addCleanup(os.chdir, old)
            os.chdir(base)
            remote = str(base / "private.git")
            git("init", "--bare", "-q", remote)
            git("init", "-q", "first")
            os.chdir(base / "first")
            self.configure()
            git("commit", "--allow-empty", "-qm", "approved revision")
            anchor = git("rev-parse", "HEAD")
            git("push", remote, f"{anchor}:refs/heads/revision")
            first = dict(id="first", deps=[], seconds=10, qualified=True, fingerprint="first")
            second = dict(id="second", deps=["first"], seconds=75, qualified=True, fingerprint="second",
                          requires_g2_from="first")
            asset = "LIND-HOME"
            records = {}
            root = Path.cwd() / "output"
            root.mkdir()
            calls = []

            def execute(stage, token, deadline):
                calls.append(stage["id"])
                native = root / (stage["id"] + ".blend")
                evidence = root / (stage["id"] + ".json")
                native.write_text(stage["id"])
                evidence.write_text("{}")
                return dict(path=native.name, sha256=sha(native), reopened=True,
                            fingerprint=stage["fingerprint"], files={evidence.name: sha(evidence)})

            store = GitCheckpointStore(remote, asset, root)
            self.assertEqual(run(remote, asset, anchor, root, [first, second], records, execute,
                                 store, budget=60, reserve=10, fenced=True), ["first"])
            checkpoint = store.previous

            os.chdir(base)
            git("clone", "-q", "--branch", "revision", remote, "second")
            os.chdir(base / "second")
            self.configure()
            root = Path.cwd() / "restored"
            deadline = time.monotonic() + 30
            with self.assertRaisesRegex(RuntimeError, "requested revision"):
                restore_checkpoint(remote, asset, "f"*40, root, deadline)
            self.assertFalse(root.exists())
            state = restore_checkpoint(remote, asset, checkpoint, root, deadline)
            self.assertEqual(state, records)
            self.assertEqual((root / "first.json").read_text(), "{}")
            store = GitCheckpointStore(remote, asset, root, previous=checkpoint)
            token = acquire(remote, asset, anchor)
            (root / "damaged.blend").write_text("damaged")
            with self.assertRaisesRegex(ValueError, "SHA mismatch"):
                store({**state, "tampered": {**state["first"], "sha256": "0"*64, "files": {},
                                             "path": "damaged.blend"}}, token,
                      time.monotonic()+30)
            release(remote, asset, token)
            self.assertEqual(run(remote, asset, anchor, root, [first, second], state, execute,
                                 store, budget=95, reserve=10, fenced=True,
                                 verify_g2=lambda stage, digest: digest == "0"*64), [])
            self.assertEqual(run(remote, asset, anchor, root, [first, second], state, execute,
                                 store, budget=95, reserve=10, fenced=True,
                                 verify_g2=lambda stage, digest:
                                 stage == "first" and digest == records["first"]["sha256"]), ["second"])
            self.assertEqual(calls, ["first", "second"])
            self.assertNotEqual(store.previous, checkpoint)
            os.chdir(old)

    def configure(self):
        git("config", "user.name", "QA")
        git("config", "user.email", "qa@invalid")

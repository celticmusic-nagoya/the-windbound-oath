import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from shared_asset_lease import acquire, assert_owned, git, publish_checkpoint, release
from shared_asset_reservation import ref_for
from shared_session_contract import ASSET_KEYS


class CheckpointFenceTests(unittest.TestCase):
    def setUp(self):
        work = TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.addCleanup(os.chdir, Path.cwd())
        os.chdir(work.name)
        git("init", "-q")
        git("config", "user.name", "QA")
        git("config", "user.email", "qa@invalid")
        git("init", "--bare", "-q", "remote.git")
        self.base = self.commit("original")
        self.first = self.commit("first")
        self.second = self.commit("second")

    def commit(self, payload):
        Path("checkpoint").write_text(payload)
        git("add", "checkpoint")
        git("commit", "-qm", payload)
        return git("rev-parse", "HEAD")

    def test_publication_rotates_fence_for_every_registered_key(self):
        for asset in sorted(ASSET_KEYS):
            with self.subTest(asset=asset):
                token = acquire("remote.git", asset, self.base)
                new = publish_checkpoint("remote.git", asset, token, self.first)
                with self.assertRaises(RuntimeError):
                    publish_checkpoint("remote.git", asset, token, self.second, self.first)
                with self.assertRaises(subprocess.CalledProcessError):
                    publish_checkpoint("remote.git", asset, new, self.second)
                assert_owned("remote.git", asset, new)
                final = publish_checkpoint("remote.git", asset, new, self.second, self.first)
                with self.assertRaises(RuntimeError):
                    release("remote.git", asset, new)
                release("remote.git", asset, final)
                suffix = ref_for(asset).rsplit("/", 1)[1]
                self.assertEqual(git("--git-dir=remote.git", "show",
                                     f"refs/heads/two-checkpoint/v1/{suffix}:checkpoint"), "second")

    def test_only_one_of_two_concurrent_publications_succeeds(self):
        asset = "LIND-CLIFF"
        token = acquire("remote.git", asset, self.base)

        def publish(commit):
            try:
                return publish_checkpoint("remote.git", asset, token, commit)
            except (RuntimeError, subprocess.CalledProcessError):
                return None

        with ThreadPoolExecutor(max_workers=2) as workers:
            results = [result for result in workers.map(publish, (self.first, self.second)) if result]
        self.assertEqual(len(results), 1)
        release("remote.git", asset, results[0])


if __name__ == "__main__":
    unittest.main()

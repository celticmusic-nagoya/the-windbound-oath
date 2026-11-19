#!/usr/bin/env python3
import unittest
from collect_actions_snapshot import collect


class SnapshotTests(unittest.TestCase):
    def test_collect_and_dedupe(self):
        def fake(url, token):
            self.assertIn("page=1", url)
            self.assertEqual(token, "read-only-test-token")
            return {"workflow_runs": [
                {"id": 10, "status": "queued", "head_branch": "feature/a"},
                {"id": 10, "status": "queued", "head_branch": "feature/a"},
                {"id": 11, "status": "completed", "conclusion": "success"}]}
        result = collect("celticmusic-nagoya/the-windbound-oath",
                         "read-only-test-token", get=fake)
        self.assertEqual([r["run_id"] for r in result["runs"]], [10, 11])
        self.assertTrue(result["read_only"])

    def test_reject_bad_repo(self):
        with self.assertRaises(ValueError):
            collect("../bad", "token")

    def test_reject_dot_segments_before_network(self):
        for repo in ("./repo", "owner/..", "owner/.", "../bad"):
            with self.subTest(repo=repo):
                def never_called(url, token):
                    self.fail("invalid repository must be rejected before network")
                with self.assertRaises(ValueError):
                    collect(repo, "token", get=never_called)

    def test_reject_missing_token(self):
        with self.assertRaises(ValueError):
            collect("owner/repo", "")

    def test_reject_unbounded_pages(self):
        with self.assertRaises(ValueError):
            collect("owner/repo", "token", pages=100)

    def test_invalid_api_payload(self):
        with self.assertRaises(ValueError):
            collect("owner/repo", "token", get=lambda url, token: {"workflow_runs": None})


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
import unittest
from urllib.parse import parse_qs, urlsplit
from collect_actions_snapshot import collect


class SnapshotTests(unittest.TestCase):
    def complete(self, get):
        return collect("owner/repo", "token", get=get, complete=True)

    def paged(self, runs):
        def get(url, token):
            self.assertEqual(token, "token")
            query = parse_qs(urlsplit(url).query)
            self.assertEqual(set(query), {"per_page", "page"})
            self.assertEqual(query["per_page"], ["100"])
            offset = (int(query["page"][0]) - 1) * 100
            return {"total_count": len(runs), "workflow_runs": runs[offset:offset + 100]}
        return get

    def run_record(self, run_id, event="push"):
        return {"id": run_id, "event": event, "status": "queued",
                "head_sha": "a" * 40, "path": ".github/workflows/qa.yml"}

    def test_complete_across_legacy_page_cap(self):
        runs = [self.run_record(i) for i in range(1, 602)]
        runs[-1]["event"] = "workflow_dispatch"
        snapshot = self.complete(self.paged(runs))
        self.assertTrue(snapshot["complete"])
        self.assertEqual(snapshot["scope"], "repository_all_events")
        self.assertEqual([run["run_id"] for run in snapshot["runs"]], list(range(1, 602)))
        self.assertEqual(snapshot["runs"][-1]["event"], "workflow_dispatch")
        self.assertEqual(snapshot["runs"][-1]["path"], runs[-1]["path"])

    def test_complete_empty_and_failed_are_distinct(self):
        self.assertEqual(self.complete(self.paged([]))["runs"], [])
        def unavailable(url, token):
            raise OSError("Actions unavailable")
        with self.assertRaises(OSError):
            self.complete(unavailable)

    def test_complete_rejects_duplicate_invalid_and_truncated_pages(self):
        duplicate = [self.run_record(i) for i in range(1, 101)]
        for get in (
            self.paged(duplicate + [duplicate[-1]]),
            self.paged([self.run_record(True)]),
            lambda url, token: {"total_count": 101, "workflow_runs": duplicate[:99]},
        ):
            with self.subTest(get=get), self.assertRaises(ValueError):
                self.complete(get)

    def test_complete_rejects_same_count_page_mutation(self):
        requests = 0
        def get(url, token):
            nonlocal requests
            requests += 1
            run = self.run_record(1)
            if requests >= 3:
                run["status"] = "in_progress"
            return self.paged([run])(url, token)
        with self.assertRaisesRegex(ValueError, "changed between traversals"):
            self.complete(get)

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

#!/usr/bin/env python3
import unittest
from inspect_actions_artifact_metadata import inspect

REPO = "celticmusic-nagoya/the-windbound-oath"
RUN = {"id": 123, "repository": {"full_name": REPO}, "status": "completed",
       "conclusion": "success", "head_sha": "a"*40, "head_branch": "feature/test"}
ARTIFACT = {"id": 9, "name": "sculpt-views", "expired": False,
            "size_in_bytes": 200, "workflow_run": {"id": 123}}


def fake(run=RUN, artifacts=None, total=None):
    if artifacts is None:
        artifacts = [ARTIFACT]
    def get(url, token):
        if url.endswith("/actions/runs/123"):
            return run
        if "/artifacts?" in url:
            return {"total_count": len(artifacts) if total is None else total,
                    "artifacts": artifacts}
        raise AssertionError("unexpected URL")
    return get


def check(get):
    return inspect(REPO, 123, "sculpt-views", "dummy-token", get=get)


class MetadataTests(unittest.TestCase):
    def test_matching_metadata_is_not_reusable(self):
        result = check(fake())
        self.assertTrue(result["metadata_accessible"])
        self.assertFalse(result["safe_to_reuse"])
        self.assertFalse(result["artifact_bytes_verified"])

    def test_failed_run(self):
        with self.assertRaises(ValueError):
            check(fake(run={**RUN, "conclusion": "failure"}))

    def test_wrong_repository(self):
        with self.assertRaises(ValueError):
            check(fake(run={**RUN, "repository": {"full_name": "wrong/repo"}}))

    def test_expired(self):
        with self.assertRaises(ValueError):
            check(fake(artifacts=[{**ARTIFACT, "expired": True}]))

    def test_empty(self):
        with self.assertRaises(ValueError):
            check(fake(artifacts=[{**ARTIFACT, "size_in_bytes": 0}]))

    def test_wrong_artifact_run(self):
        with self.assertRaises(ValueError):
            check(fake(artifacts=[{**ARTIFACT, "workflow_run": {"id": 5}}]))

    def test_duplicate_artifact_name(self):
        with self.assertRaises(ValueError):
            check(fake(artifacts=[ARTIFACT, {**ARTIFACT, "id": 10}]))

    def test_no_artifact(self):
        with self.assertRaises(ValueError):
            check(fake(artifacts=[]))

    def test_invalid_run_sha(self):
        with self.assertRaises(ValueError):
            check(fake(run={**RUN, "head_sha": "z"*40}))

    def test_missing_run_branch(self):
        with self.assertRaises(ValueError):
            check(fake(run={**RUN, "head_branch": None}))

    def test_invalid_artifact_id(self):
        with self.assertRaises(ValueError):
            check(fake(artifacts=[{**ARTIFACT, "id": True}]))

    def test_missing_token(self):
        with self.assertRaises(ValueError):
            inspect(REPO, 123, "sculpt-views", "", get=fake())

    def test_invalid_run_id(self):
        with self.assertRaises(ValueError):
            inspect(REPO, True, "sculpt-views", "token", get=fake())


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Pure unit tests; safe to run with repository Actions disabled."""
import unittest
from classify_actions_jobs import classify, fingerprint

BASE = dict(asset_id="morwen", stage="sculpt", source_sha256="a"*64,
            script_sha256="b"*64, config_sha256="c"*64,
            tool_version="Blender 5.2.4", reference_sha256="d"*64,
            output_contract="four-view-blend-v1", prerequisites_verified=True)


class ClassifierTests(unittest.TestCase):
    def test_deterministic_key(self):
        self.assertEqual(fingerprint(BASE), fingerprint(dict(reversed(list(BASE.items())))))

    def test_independent_work(self):
        self.assertEqual(classify(BASE, [])["decision"], "RUN_ELIGIBLE")
        self.assertEqual(classify({**BASE, "asset_id": "lind"}, [{**BASE, "status": "IN_PROGRESS"}])["decision"], "RUN_ELIGIBLE")

    def test_duplicate_active(self):
        self.assertEqual(classify(BASE, [{**BASE, "status": "IN_PROGRESS", "run_id": 3}])["decision"], "REUSE_ACTIVE")

    def test_verified_artifact(self):
        good = {**BASE, "status": "SUCCESS", "artifact_sha256_verified": True,
                "artifact_accessible": True, "output_contract_verified": True}
        self.assertEqual(classify(BASE, [good])["decision"], "REUSE_SUCCESS")
        self.assertEqual(classify(BASE, [{**good, "artifact_accessible": False}])["decision"], "REVIEW_REQUIRED")

    def test_active_conflict_precedes_reuse(self):
        good = {**BASE, "status": "SUCCESS", "artifact_sha256_verified": True,
                "artifact_accessible": True, "output_contract_verified": True}
        for status in ("QUEUED", "IN_PROGRESS"):
            conflict = {**BASE, "script_sha256": "e"*64, "status": status}
            for ledger in ([good, conflict], [conflict, good],
                           [{**BASE, "status": "IN_PROGRESS"}, conflict]):
                self.assertEqual(classify(BASE, ledger)["decision"], "REVIEW_REQUIRED")

    def test_semantic_overlap(self):
        other = {**BASE, "script_sha256": "e"*64, "status": "SUCCESS"}
        self.assertEqual(classify(BASE, [other])["decision"], "REVIEW_REQUIRED")

    def test_prior_failure_requires_review(self):
        self.assertEqual(classify(BASE, [{**BASE, "status": "FAILED"}])["decision"], "REVIEW_REQUIRED")

    def test_missing_dependency(self):
        self.assertEqual(classify({**BASE, "prerequisites_verified": False}, [])["decision"], "BLOCKED")

    def test_missing_identity_rejected(self):
        with self.assertRaises(ValueError):
            classify({k: v for k, v in BASE.items() if k != "source_sha256"}, [])

    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):
            classify(BASE, [{**BASE, "status": "UNKNOWN"}])


if __name__ == "__main__":
    unittest.main()

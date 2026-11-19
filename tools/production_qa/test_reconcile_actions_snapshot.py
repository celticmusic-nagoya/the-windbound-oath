#!/usr/bin/env python3
import unittest
from reconcile_actions_snapshot import reconcile

JOB = dict(asset_id="morwen", stage="sculpt", source_sha256="a"*64,
           script_sha256="b"*64, config_sha256="c"*64,
           tool_version="Blender 5.2.4", reference_sha256="d"*64,
           output_contract="four-view-blend-v1", run_id=42,
           branch="feature/morwen", head_sha="f"*40, status="QUEUED")
RUN = dict(run_id=42, head_branch="feature/morwen", head_sha="f"*40,
           status="queued", conclusion=None)


def check(job=JOB, run=RUN):
    return reconcile([job], {"read_only": True, "runs": [run]})["decisions"][0]["decision"]


class ReconcileTests(unittest.TestCase):
    def test_consistent_queue(self):
        self.assertEqual(check(), "CONSISTENT")

    def test_missing_run_not_absence(self):
        self.assertEqual(reconcile([JOB], {"read_only": True, "runs": []})["review_count"], 1)

    def test_wrong_head(self):
        self.assertEqual(check(run={**RUN, "head_sha": "0"*40}), "REVIEW_REQUIRED")

    def test_wrong_branch(self):
        self.assertEqual(check(run={**RUN, "head_branch": "other"}), "REVIEW_REQUIRED")

    def test_stale_ledger_status(self):
        self.assertEqual(check(job={**JOB, "status": "IN_PROGRESS"}), "REVIEW_REQUIRED")

    def test_success_without_artifact(self):
        self.assertEqual(check(job={**JOB, "status": "SUCCESS"},
                               run={**RUN, "status": "completed", "conclusion": "success"}), "REVIEW_REQUIRED")

    def test_untrusted_ledger_success_flags_do_not_verify_artifact(self):
        job = {**JOB, "status": "SUCCESS", "artifact_sha256_verified": True,
               "artifact_accessible": True, "output_contract_verified": True}
        self.assertEqual(check(job=job, run={**RUN, "status": "completed", "conclusion": "success"}), "REVIEW_REQUIRED")

    def test_duplicate_ledger_run_rejected(self):
        with self.assertRaises(ValueError):
            reconcile([JOB, {**JOB, "asset_id": "lind"}],
                      {"read_only": True, "runs": [RUN]})

    def test_conflicting_duplicate_snapshot_rejected(self):
        with self.assertRaises(ValueError):
            reconcile([JOB], {"read_only": True, "runs": [RUN, {**RUN, "status": "completed"}]})

    def test_unknown_status_rejected(self):
        with self.assertRaises(ValueError):
            check(run={**RUN, "status": "unknown"})


if __name__ == "__main__":
    unittest.main()

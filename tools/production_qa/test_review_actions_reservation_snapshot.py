#!/usr/bin/env python3
import unittest
from datetime import datetime, timezone
from classify_actions_jobs import fingerprint
from reserve_actions_job_ref import PREFIX
from review_actions_reservation_snapshot import review

REQ = dict(asset_id="morwen", stage="sculpt", source_sha256="s",
           script_sha256="t", config_sha256="c", tool_version="5.2.4",
           reference_sha256="r", output_contract="four-view")
KEY = fingerprint(REQ)
RES = {"ref": PREFIX + KEY, "anchor_sha": "a"*40}
LEDGER = {**REQ, "owner_pr": 421, "run_id": 42, "head_sha": "b"*40,
          "branch": "feature/sculpt", "status": "IN_PROGRESS",
          "updated_at": "2026-11-19T05:00:00Z"}
RUN = {"run_id": 42, "head_sha": "b"*40, "head_branch": "feature/sculpt",
       "status": "in_progress", "conclusion": None}
NOW = datetime(2026, 11, 19, 8, tzinfo=timezone.utc)


class SnapshotReviewTests(unittest.TestCase):
    def check(self, runs, entry=LEDGER):
        result = review(REQ, RES, entry, {"read_only": True, "runs": runs}, NOW)
        self.assertFalse(result["dispatch_authorized"])
        self.assertFalse(result["ref_deletion_authorized"])
        self.assertFalse(result["owner_transfer_authorized"])
        return result["decision"]

    def test_exact_active_keeps_reserved(self):
        self.assertEqual(self.check([RUN]), "KEEP_RESERVED")

    def test_missing_run_blocked(self):
        self.assertEqual(self.check([]), "BLOCKED")

    def test_duplicate_run_blocked(self):
        self.assertEqual(self.check([RUN, RUN]), "BLOCKED")

    def test_wrong_branch_blocked(self):
        self.assertEqual(self.check([{**RUN, "head_branch": "main"}]), "BLOCKED")

    def test_wrong_sha_blocked(self):
        self.assertEqual(self.check([{**RUN, "head_sha": "c"*40}]), "BLOCKED")

    def test_nonhex_sha_blocked_even_when_matching(self):
        invalid = "z" * 40
        entry = {**LEDGER, "head_sha": invalid}
        run = {**RUN, "head_sha": invalid}
        self.assertEqual(self.check([run], entry), "BLOCKED")

    def test_uppercase_sha_blocked_even_when_matching(self):
        upper = "A" * 40
        entry = {**LEDGER, "head_sha": upper}
        run = {**RUN, "head_sha": upper}
        self.assertEqual(self.check([run], entry), "BLOCKED")

    def test_terminal_failure_review(self):
        self.assertEqual(self.check([{**RUN, "status": "completed",
                                      "conclusion": "failure"}]), "REVIEW_REQUIRED")

    def test_success_without_proof_review(self):
        self.assertEqual(self.check([{**RUN, "status": "completed",
                                      "conclusion": "success"}]), "REVIEW_REQUIRED")

    def test_untrusted_ledger_flags_not_proof(self):
        entry = {**LEDGER, "status": "SUCCESS",
                 "artifact_sha256_verified": True, "artifact_accessible": True,
                 "output_contract_verified": True}
        self.assertEqual(self.check([{**RUN, "status": "completed",
                                      "conclusion": "success"}], entry), "BLOCKED")

    def test_invalid_snapshot_rejected(self):
        with self.assertRaises(ValueError):
            review(REQ, RES, LEDGER, {"read_only": False, "runs": [RUN]}, NOW)


if __name__ == "__main__":
    unittest.main()

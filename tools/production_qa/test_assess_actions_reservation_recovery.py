#!/usr/bin/env python3
import unittest
from datetime import datetime, timezone, timedelta
from classify_actions_jobs import fingerprint
from reserve_actions_job_ref import PREFIX
from assess_actions_reservation_recovery import assess

REQ = dict(asset_id="morwen", stage="sculpt", source_sha256="s",
           script_sha256="t", config_sha256="c", tool_version="5.2.4",
           reference_sha256="r", output_contract="four-view",
           prerequisites_verified=True)
NOW = datetime(2026, 11, 19, 8, tzinfo=timezone.utc)
KEY = fingerprint(REQ)
RES = {"ref": PREFIX + KEY, "anchor_sha": "a" * 40}
LEDGER = {**REQ, "owner_pr": 421, "run_id": 42, "status": "IN_PROGRESS",
          "updated_at": (NOW - timedelta(hours=6)).isoformat()}
SNAP = {"complete": True, "fingerprint": KEY, "run_id": 42,
        "status": "in_progress", "conclusion": None}


class RecoveryTests(unittest.TestCase):
    def check(self, entry=LEDGER, snapshot=SNAP, reservation=RES):
        result = assess(REQ, reservation, entry, snapshot, NOW)
        self.assertFalse(result["dispatch_authorized"])
        self.assertFalse(result["ref_deletion_authorized"])
        self.assertFalse(result["owner_transfer_authorized"])
        return result

    def test_stale_active_stays_reserved(self):
        self.assertEqual(self.check()["decision"], "KEEP_RESERVED")

    def test_missing_snapshot_is_blocked(self):
        self.assertEqual(self.check(snapshot={})["decision"], "BLOCKED")

    def test_incomplete_snapshot_is_blocked(self):
        self.assertEqual(self.check(snapshot={**SNAP, "complete": False})["decision"], "BLOCKED")

    def test_wrong_run_id_is_blocked(self):
        self.assertEqual(self.check(snapshot={**SNAP, "run_id": 77})["decision"], "BLOCKED")

    def test_wrong_fingerprint_is_blocked(self):
        self.assertEqual(self.check(snapshot={**SNAP, "fingerprint": "0"*64})["decision"], "BLOCKED")

    def test_success_without_artifact_requires_review(self):
        entry = {**LEDGER, "status": "SUCCESS"}
        snap = {**SNAP, "status": "completed", "conclusion": "success"}
        self.assertEqual(self.check(entry=entry, snapshot=snap)["decision"], "REVIEW_REQUIRED")

    def test_verified_success_is_reused(self):
        entry = {**LEDGER, "status": "SUCCESS", "artifact_sha256_verified": True,
                 "artifact_accessible": True, "output_contract_verified": True}
        snap = {**SNAP, "status": "completed", "conclusion": "success"}
        self.assertEqual(self.check(entry=entry, snapshot=snap)["decision"], "REUSE_VERIFIED")

    def test_failed_run_requires_review(self):
        snap = {**SNAP, "status": "completed", "conclusion": "failure"}
        self.assertEqual(self.check(snapshot=snap)["decision"], "REVIEW_REQUIRED")

    def test_wrong_ref_is_rejected(self):
        with self.assertRaises(ValueError):
            self.check(reservation={**RES, "ref": PREFIX + "0"*64})

    def test_missing_owner_is_rejected(self):
        with self.assertRaises(ValueError):
            self.check(entry={**LEDGER, "owner_pr": None})

    def test_future_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            self.check(entry={**LEDGER, "updated_at": (NOW+timedelta(hours=1)).isoformat()})

    def test_ambiguous_completion_is_blocked(self):
        snap = {**SNAP, "status": "completed", "conclusion": None}
        self.assertEqual(self.check(snapshot=snap)["decision"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()

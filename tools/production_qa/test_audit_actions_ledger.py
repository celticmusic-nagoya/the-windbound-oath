#!/usr/bin/env python3
import unittest
from datetime import datetime, timezone
from audit_actions_ledger import audit

NOW = datetime(2026, 11, 19, 12, tzinfo=timezone.utc)
JOB = dict(asset_id="morwen", stage="sculpt", source_sha256="a"*64,
           script_sha256="b"*64, config_sha256="c"*64,
           tool_version="Blender 5.2.4", reference_sha256="d"*64,
           output_contract="four-view-blend-v1", owner_pr=425,
           updated_at="2026-11-19T08:00:00Z")


class LedgerAuditTests(unittest.TestCase):
    def alerts(self, **changes):
        return audit([{**JOB, **changes}], NOW)["alerts"]

    def test_stale_queue(self):
        self.assertIn("QUEUED_STALE", self.alerts(status="QUEUED")[0]["alerts"])

    def test_stale_running(self):
        self.assertIn("RUNNING_STALE", self.alerts(status="IN_PROGRESS")[0]["alerts"])

    def test_missing_artifact(self):
        self.assertIn("ARTIFACT_UNVERIFIED", self.alerts(status="SUCCESS")[0]["alerts"])

    def test_verified_success(self):
        self.assertEqual(self.alerts(status="SUCCESS", artifact_sha256_verified=True,
                                     artifact_accessible=True, output_contract_verified=True), [])

    def test_failed_job(self):
        self.assertIn("FAILED_OR_BLOCKED", self.alerts(status="FAILED")[0]["alerts"])

    def test_owner_inactive(self):
        self.assertIn("OWNER_INACTIVE", self.alerts(status="BLOCKED",
                      updated_at="2026-11-16T00:00:00Z")[0]["alerts"])

    def test_missing_owner(self):
        with self.assertRaises(ValueError):
            audit([{**JOB, "status": "FAILED", "owner_pr": None}], NOW)

    def test_future_timestamp(self):
        with self.assertRaises(ValueError):
            audit([{**JOB, "status": "QUEUED", "updated_at": "2026-11-20T00:00:00Z"}], NOW)

    def test_empty_ledger(self):
        self.assertEqual(audit([], NOW), {"alert_count": 0, "alerts": [], "read_only": True})


if __name__ == "__main__":
    unittest.main()

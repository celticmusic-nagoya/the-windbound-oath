#!/usr/bin/env python3
import unittest
from reserve_actions_job_ref import reserve, inspect_existing_ref, PREFIX
from classify_actions_jobs import fingerprint

SHA = "a" * 40
REQ = dict(asset_id="morwen", stage="sculpt", source_sha256="s",
           script_sha256="t", config_sha256="c", tool_version="5.2.4",
           reference_sha256="r", output_contract="four-view",
           prerequisites_verified=True)


class Conflict(Exception):
    status = 422


class ReservationTests(unittest.TestCase):
    def test_create_once_without_dispatch(self):
        calls = []
        result = reserve(REQ, [], SHA, lambda ref, sha: calls.append((ref, sha)))
        self.assertEqual(result["decision"], "RESERVED_ONLY")
        self.assertEqual(calls, [(PREFIX + fingerprint(REQ), SHA)])
        self.assertFalse(result["dispatch_authorized"])

    def test_identical_active_skips_create(self):
        def never(*args):
            self.fail("should not attempt reservation")
        result = reserve(REQ, [{**REQ, "status": "QUEUED"}], SHA, never)
        self.assertEqual(result["decision"], "REUSE_ACTIVE")

    def test_identical_verified_success_skips_create(self):
        old = {**REQ, "status": "SUCCESS", "artifact_sha256_verified": True,
               "artifact_accessible": True, "output_contract_verified": True}
        result = reserve(REQ, [old], SHA, lambda *_: self.fail("duplicate"))
        self.assertEqual(result["decision"], "REUSE_SUCCESS")

    def test_missing_prerequisites_skips_create(self):
        result = reserve({**REQ, "prerequisites_verified": False}, [],
                         SHA, lambda *_: self.fail("blocked"))
        self.assertEqual(result["decision"], "BLOCKED")

    def test_conflict_is_review_not_success(self):
        def conflict(ref, sha):
            raise Conflict("already exists or validation")
        result = reserve(REQ, [], SHA, conflict)
        self.assertEqual(result["decision"], "REVIEW_REQUIRED")
        self.assertFalse(result["reservation_created"])

    def test_unknown_api_failure_propagates(self):
        def fail(ref, sha):
            raise RuntimeError("network unavailable")
        with self.assertRaises(RuntimeError):
            reserve(REQ, [], SHA, fail)

    def test_reject_noncommit_sha(self):
        with self.assertRaises(ValueError):
            reserve(REQ, [], "main", lambda *_: self.fail("should reject"))

    def test_existing_ref_never_authorizes_dispatch(self):
        key = fingerprint(REQ)
        result = inspect_existing_ref(key, PREFIX + key, SHA)
        self.assertFalse(result["dispatch_authorized"])

    def test_existing_ref_wrong_fingerprint(self):
        with self.assertRaises(ValueError):
            inspect_existing_ref(fingerprint(REQ), PREFIX + "0" * 64, SHA)

    def test_same_asset_different_input_requires_review(self):
        old = {**REQ, "source_sha256": "different", "status": "SUCCESS"}
        result = reserve(REQ, [old], SHA, lambda *_: self.fail("overlap"))
        self.assertEqual(result["decision"], "REVIEW_REQUIRED")


if __name__ == "__main__":
    unittest.main()

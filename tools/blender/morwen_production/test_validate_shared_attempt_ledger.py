import unittest
from validate_shared_attempt_ledger import validate

def record(method="vroid-percent-tweak", family="vroid-local-tweak", outcome="FAIL", stop=""):
    return {
        "task_id": "MORWEN-FIT-01", "asset_id": "morwen-head",
        "defect_id": "face-silhouette", "method_id": method,
        "method_family": family, "source_sha256": "sha256:source-recorded",
        "input_sha256": ["sha256:input-recorded"], "output_sha256": [],
        "canonical_references": ["front:7809.png", "right:7807.png"],
        "visual_defects": ["front silhouette mismatch"],
        "root_cause": "shape", "next_action": "sculpt-retopology",
        "stop_reason": stop,
        "gates": {"G1": "PASS", "G2": "FAIL", "G3": "PASS", "G4": "NOT_RUN"},
        "outcome": outcome,
    }

def ledger(*items):
    return {"schema": "TWO-3D-SHARED-LEDGER-01", "attempts": list(items)}

class SharedLedgerTest(unittest.TestCase):
    def test_second_failure_requires_stop(self):
        self.assertTrue(any("stop_reason" in e for e in validate(ledger(record(), record()))))
    def test_second_failure_with_stop_valid(self):
        self.assertEqual(validate(ledger(record(), record(stop="Switch to sculpt"))), [])
    def test_renamed_method_does_not_reset_count(self):
        errors = validate(ledger(record(), record(method="vroid-tweak-v2", stop="Switch"),
                                 record(method="vroid-tweak-v3", stop="Switch")))
        self.assertTrue(any("already failed twice" in e for e in errors))
    def test_changed_family_allowed(self):
        self.assertEqual(validate(ledger(record(), record(stop="Switch"),
                                         record(method="sculpt", family="sculpt-retopology"))), [])
    def test_missing_reference_rejected(self):
        item = record()
        item["canonical_references"] = []
        self.assertTrue(validate(ledger(item)))

if __name__ == "__main__":
    unittest.main()

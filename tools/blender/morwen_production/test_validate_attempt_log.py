import unittest
from validate_attempt_log import validate

def entry(method="vroid-tweak", status="FAIL"):
    return {
        "asset_id": "morwen-head", "canonical_references": ["7809.png sha256:verified"],
        "method": method, "defect_id": "jaw-silhouette", "attempt_number": 1,
        "hypothesis": "Match frontal jaw", "observed_delta": "Still too wide",
        "failure_category": "geometry", "next_method": "sculpt-retopology",
        "gates": {"G1": "PASS", "G2": status, "G3": "PASS", "G4": "NOT_RUN"}
    }

class TestAntiLoop(unittest.TestCase):
    def test_two_failures_allowed_as_history(self):
        self.assertEqual(validate({"schema": "TWO-3D-ATTEMPT-LOG-01",
                                   "attempts": [entry(), entry()]}), [])
    def test_third_failure_rejected(self):
        errors = validate({"schema": "TWO-3D-ATTEMPT-LOG-01",
                           "attempts": [entry(), entry(), entry()]})
        self.assertTrue(any("anti-loop STOP" in e for e in errors))
    def test_changed_method_allowed(self):
        self.assertEqual(validate({"schema": "TWO-3D-ATTEMPT-LOG-01",
                                   "attempts": [entry(), entry(), entry("sculpt-retopology")]}), [])
    def test_missing_canon_rejected(self):
        bad = entry(); bad["canonical_references"] = []
        self.assertTrue(validate({"schema": "TWO-3D-ATTEMPT-LOG-01", "attempts": [bad]}))

if __name__ == "__main__":
    unittest.main()

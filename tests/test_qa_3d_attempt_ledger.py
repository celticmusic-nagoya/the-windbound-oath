import importlib.util
import pathlib
import unittest

P = pathlib.Path(__file__).resolve().parents[1] / "tools" / "qa_3d_attempt_ledger.py"
spec = importlib.util.spec_from_file_location("ledger", P)
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)

def sample(result="FAIL", method="primitive", aid="a1"):
    return {"attempt_id":aid,"defect_id":"roof","method_id":method,"input_sha256":"a"*64,
            "hypothesis":"change roof structure","evidence":"render.png","result":result,
            "failure_category":"shape","gates":{"G1":"BLOCKED","G2":"FAIL","G3":"PASS","G4":"NOT_RUN"}}

class LedgerTest(unittest.TestCase):
    def doc(self, attempts):
        return {"schema_version":1,"asset_id":"home","attempts":attempts}

    def test_empty_valid(self):
        self.assertEqual(ledger.validate(self.doc([])), [])
    def test_two_failures_allowed(self):
        self.assertEqual(ledger.validate(self.doc([sample(aid="a1"),sample(aid="a2")])), [])
    def test_third_failure_rejected(self):
        errors=ledger.validate(self.doc([sample(aid="a1"),sample(aid="a2"),sample(aid="a3")]))
        self.assertTrue(any("exceeded two" in x for x in errors))
    def test_method_switch_allowed(self):
        self.assertEqual(ledger.validate(self.doc([sample(aid="a1"),sample(aid="a2"),sample(method="sculpt",aid="a3")])), [])
    def test_duplicate_id_rejected(self):
        self.assertTrue(any("duplicate" in x for x in ledger.validate(self.doc([sample(),sample()]))))
    def test_invalid_gate_rejected(self):
        a=sample();a["gates"]["G2"]="GREEN"
        self.assertTrue(ledger.validate(self.doc([a])))

if __name__ == "__main__":
    unittest.main()

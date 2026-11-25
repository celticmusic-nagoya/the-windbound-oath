"""Publication gate offline regression; no network or actual publication."""
import importlib.util
import pathlib
import unittest
spec = importlib.util.spec_from_file_location("publication_gate", pathlib.Path(__file__).with_name("publication-gate.py"))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

def row(c, **kw):
    return dict(sha256=c*64, head="f"*40, name=c+".png", path="published/"+c*64+".png", stage="candidate", **kw)
def manifest(*rows):
    return {"version": 1, "entries": list(rows)}

class PublicationGateTests(unittest.TestCase):
    def test_default_deny_and_history(self):
        old, new = row("a"), row("b")
        delta=gate.approved_candidates(manifest(old), manifest(old,new), manifest())
        self.assertEqual(delta, manifest())
        self.assertEqual(gate.verify(manifest(old),delta,manifest(old)),(1,0))
        with self.assertRaises(ValueError):
            gate.verify(manifest(old),delta,manifest(old,new))
        with self.assertRaises(ValueError):
            gate.verify(manifest(old),delta,manifest())
    def test_exact_approved_receipt(self):
        old,new=row("a"),row("b",run_id=11,artifact_id=12)
        receipt=dict(new,approval_ref="director approval reference")
        delta=gate.approved_candidates(manifest(old),manifest(new),manifest(receipt))
        self.assertEqual(gate.verify(manifest(old),delta,manifest(old,new)),(1,1))
        for changes in ({"head":"e"*40},{"name":"wrong.png"},{"artifact_id":13},{"stage":"internal / preview only"}):
            with self.assertRaises(ValueError):
                gate.approved_candidates(manifest(old),manifest(dict(new,**changes)),manifest(receipt))
        with self.assertRaises(ValueError):
            gate.approved_candidates(manifest(old),manifest(new),manifest(dict(receipt,approval_ref="")))
    def test_existing_metadata_cannot_change(self):
        old=row("a",qa="NOT_RUN")
        with self.assertRaises(ValueError):
            gate.verify(manifest(old),manifest(),manifest(dict(old,qa="PASS")))
        with self.assertRaises(ValueError):
            gate.verify(manifest(old),manifest(),manifest(old,old))

if __name__ == "__main__":
    unittest.main()

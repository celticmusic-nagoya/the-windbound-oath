"""Publication gate offline regression; no network or actual publication."""
import importlib.util
import pathlib
import unittest
from datetime import datetime, timezone
from artifact_availability import recorded_expired_404, retained_receipt_matches
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

class ArtifactAvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,11,27,6,tzinfo=timezone.utc)
        self.item=dict(run_id=11,artifact_id=12,head="f"*40,expires_at="2026-11-27T03:57:02Z",artifact_digest="sha256:"+"a"*64,entries=["b.png"],entry_sha256={"b.png":"b"*64})
        self.stderr="gh: Not Found (HTTP 404)\n"
        self.history=manifest(row("b",run_id=11,artifact_id=12))
    def test_expired_pinned_404_only(self):
        self.assertTrue(recorded_expired_404(self.item,self.stderr,self.now))
        for error in ("gh: HTTP 403","gh: HTTP 500","timeout","gh: Not Found (HTTP 404)\nextra"):
            self.assertFalse(recorded_expired_404(self.item,error,self.now))
        for changes in ({"expires_at":"2026-11-28T00:00:00Z"},{"expires_at":"bad"},{"expires_at":"2026-11-26T00:00:00"},{"entry_sha256":{}},{"entries":["b.png","b.png"]},{"artifact_digest":"bad"}):
            self.assertFalse(recorded_expired_404(dict(self.item,**changes),self.stderr,self.now))
    def test_exact_history_required(self):
        self.assertTrue(retained_receipt_matches(self.item,self.history))
        self.assertFalse(retained_receipt_matches(self.item,manifest()))
        for changes in ({"head":"e"*40},{"artifact_id":13},{"run_id":14},{"name":"wrong.png"},{"sha256":"c"*64}):
            self.assertFalse(retained_receipt_matches(self.item,manifest(dict(self.history["entries"][0],**changes))))
        self.assertFalse(retained_receipt_matches(self.item,manifest(*self.history["entries"],*self.history["entries"])))

if __name__ == "__main__":
    unittest.main()

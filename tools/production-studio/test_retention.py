import unittest
from datetime import datetime, timezone
from retention import select
class RetentionTests(unittest.TestCase):
    def test_selection(self):
        now=datetime(2026,11,22,tzinfo=timezone.utc)
        a=dict(sha256="a",bytes=8,created_at="2026-11-21T00:00:00Z")
        b=dict(sha256="b",bytes=8,created_at="2026-01-01T00:00:00Z",milestone=True)
        c=dict(sha256="c",bytes=8,created_at="2026-01-01T00:00:00Z")
        result=select([a,b,c,dict(a)],now,16)
        self.assertEqual([e["sha256"] for e in result["entries"]],["b","a"])
        self.assertEqual(result["bytes"],16)
        self.assertEqual(len(result["omitted"]),1)
        self.assertTrue(select([b],now,1)["over_budget"])
if __name__=="__main__":
    unittest.main()

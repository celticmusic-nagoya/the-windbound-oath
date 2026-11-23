import io
import json
import unittest
from unittest.mock import patch
from tools.map_blueprint.gsi_coverage_probe import probe

class Response:
    def __init__(self, data): self.data = data
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self, count): return self.data

class CoverageProbeTest(unittest.TestCase):
    def test_intersects(self):
        d = probe(504197, 692173, opener=lambda *a, **kw: Response(b'{"features":[{"attributes":{"OBJECTID":4}}]}'))
        self.assertEqual(d["coverage"], "INTERSECTS")
        self.assertEqual(d["features"][0]["OBJECTID"], 4)
    def test_no_intersection(self):
        d = probe(504197, 692173, opener=lambda *a, **kw: Response(b'{"features":[]}'))
        self.assertEqual(d["coverage"], "NO_INTERSECTION")
    def test_error_is_not_absence(self):
        d = probe(504197, 692173, opener=lambda *a, **kw: Response(b'{"error":{"message":"bad"}}'))
        self.assertEqual(d["coverage"], "NOT_VERIFIED")
    def test_offline(self):
        self.assertEqual(probe(504197,692173,offline=True)["coverage"], "NOT_VERIFIED")
    def test_query_crs(self):
        self.assertIn("inSR=2157",probe(504197,692173,offline=True)["query_url"])

if __name__ == "__main__": unittest.main()

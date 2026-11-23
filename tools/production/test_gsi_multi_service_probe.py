#!/usr/bin/env python3
"""Offline tests: do not access official GSI services."""
import importlib.util
import io
import json
import pathlib
import unittest
from unittest.mock import patch

MODULE = pathlib.Path(__file__).with_name("gsi_multi_service_probe.py")
spec = importlib.util.spec_from_file_location("gsi_multi_service_probe", MODULE)
probe_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe_module)

class Response:
    def __init__(self, obj):
        self.data = io.BytesIO(json.dumps(obj).encode())
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, n):
        return self.data.read(n)

class ProbeTests(unittest.TestCase):
    def query(self, data):
        with patch.object(probe_module.urllib.request, "urlopen", return_value=Response(data)) as mocked:
            result = probe_module.probe("TEST", "https://example.org/query", 504197.0, 692173.0, 2)
            url = mocked.call_args.args[0].full_url
            self.assertIn("inSR=2157", url)
            self.assertIn("esriSpatialRelIntersects", url)
            return result

    def test_intersection(self):
        result = self.query({"features": [{"attributes": {"OBJECTID": 1}}]})
        self.assertEqual(result["coverage"], "INTERSECTS")
        self.assertEqual(result["feature_count"], 1)
        self.assertIsNotNone(result["response_sha256"])
        self.assertEqual(result["tile_download"], "NOT_RUN")

    def test_no_intersection(self):
        result = self.query({"features": []})
        self.assertEqual(result["coverage"], "NO_INTERSECTION")
        self.assertEqual(result["feature_count"], 0)

    def test_arcgis_error(self):
        result = self.query({"error": {"code": 400, "message": "Invalid query"}})
        self.assertEqual(result["coverage"], "NOT_VERIFIED")
        self.assertIn("ArcGIS error", result["error"])

    def test_missing_features(self):
        result = self.query({"other": []})
        self.assertEqual(result["coverage"], "NOT_VERIFIED")
        self.assertIn("missing features", result["error"])

    def test_network_error(self):
        with patch.object(probe_module.urllib.request, "urlopen", side_effect=TimeoutError("timeout")):
            result = probe_module.probe("TEST", "https://example.org/query", 1, 2, 2)
        self.assertEqual(result["coverage"], "NOT_VERIFIED")
        self.assertIn("TimeoutError", result["error"])

if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Offline contract tests for GSI coverage query; never accesses network."""
import contextlib
import importlib.util
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

TARGET = pathlib.Path(__file__).with_name("query_gsi_clare_lidar.py")
spec = importlib.util.spec_from_file_location("gsi_coverage", TARGET)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class CoverageQueryTests(unittest.TestCase):
    def run_query(self, argv):
        calls = []
        def fake(url, params=None):
            calls.append((url, params))
            if url == mod.ROOT:
                return {"layers":[{"id":12,"name":"LiDAR Coverage DTM"}]}
            if url.endswith("/12"):
                return {"objectIdField":"OBJECTID","fields":[{"name":x} for x in
                    ("OBJECTID","COUNTY","DATA_URL","LICENCE","RESOLUTION","OWNER")]}
            if url.endswith("/12/query"):
                return {"features":[{"attributes":{"OBJECTID":4,"COUNTY":"Clare",
                    "DATA_URL":"https://example.invalid/dtm.tif","LICENCE":"CC BY 4.0"}}],
                    "exceededTransferLimit":False}
            raise AssertionError(url)
        with tempfile.TemporaryDirectory() as tmp:
            out = str(pathlib.Path(tmp)/"query.json")
            with patch.object(mod, "get_json", side_effect=fake),patch.object(sys,"argv",["gsi", "--output",out]+argv),contextlib.redirect_stdout(io.StringIO()):
                mod.main()
            return json.loads(pathlib.Path(out).read_text()), calls

    def test_county_filter_and_no_raster_download(self):
        result,calls=self.run_query([])
        self.assertEqual(result["status"],"COMPLETE_QUERY_ONLY")
        self.assertEqual(result["records"][0]["features"][0]["COUNTY"],"Clare")
        self.assertFalse(result["raster_downloaded"])
        self.assertIsNone(result["raster_sha256"])
        self.assertIn("COUNTY LIKE '%Clare%'",calls[-1][1]["where"])

    def test_bbox_is_epsg2157(self):
        result,calls=self.run_query(["--bbox-itm","510000","690000","520000","700000"])
        self.assertEqual(calls[-1][1]["inSR"],"2157")
        self.assertEqual(calls[-1][1]["geometry"],"510000.0,690000.0,520000.0,700000.0")

    def test_empty_features_fail_closed(self):
        original = mod.get_json
        def fake(url, params=None):
            if url == mod.ROOT:
                return {"layers":[{"id":12,"name":"LiDAR Coverage DTM"}]}
            if url.endswith("/12"):
                return {"objectIdField":"OBJECTID","fields":[{"name":"OBJECTID"},{"name":"COUNTY"}]}
            if url.endswith("/12/query"):
                return {"features":[]}
            raise AssertionError(url)
        with tempfile.TemporaryDirectory() as tmp:
            out = str(pathlib.Path(tmp)/"empty.json")
            with patch.object(mod,"get_json",side_effect=fake),patch.object(sys,"argv",["gsi","--output",out]),contextlib.redirect_stdout(io.StringIO()):
                mod.main()
            data = json.loads(pathlib.Path(out).read_text())
            self.assertEqual(data["status"],"PARTIAL")
            self.assertEqual(data["record_count"],0)

    def test_full_page_is_partial(self):
        result,calls=self.run_query(["--limit","1"])
        self.assertEqual(result["status"],"PARTIAL")
        self.assertTrue(result["records"][0]["incomplete"])

    def test_pagination_two_pages(self):
        calls = []
        def fake(url, params=None):
            calls.append((url, dict(params or {})))
            if url == mod.ROOT:
                return {"layers":[{"id":12,"name":"LiDAR Coverage DTM"}]}
            if url.endswith("/12"):
                return {"objectIdField":"OBJECTID","fields":[{"name":"OBJECTID"},{"name":"COUNTY"}]}
            if url.endswith("/12/query"):
                offset = params["resultOffset"]
                if offset == 0:
                    return {"features":[{"attributes":{"OBJECTID":1,"COUNTY":"Clare"}}],
                            "exceededTransferLimit":True}
                if offset == 1:
                    return {"features":[{"attributes":{"OBJECTID":2,"COUNTY":"Clare"}}],
                            "exceededTransferLimit":False}
                return {"features":[]}
            raise AssertionError(url)
        with tempfile.TemporaryDirectory() as tmp:
            out = str(pathlib.Path(tmp)/"paged.json")
            with patch.object(mod,"get_json",side_effect=fake),patch.object(sys,"argv",["gsi","--output",out,"--limit","1"]),contextlib.redirect_stdout(io.StringIO()):
                mod.main()
            data=json.loads(pathlib.Path(out).read_text())
            self.assertEqual(data["status"],"COMPLETE_QUERY_ONLY")
            self.assertEqual(data["record_count"],2)
            self.assertEqual(data["records"][0]["pages"],2)
            self.assertFalse(data["records"][0]["incomplete"])

    def test_invalid_limit_rejected(self):
        with patch.object(sys,"argv",["gsi","--output","unused.json","--limit","0"]),contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as cm: mod.main()
        self.assertEqual(cm.exception.code,2)

    def test_missing_county_field_is_reported(self):
        def fake(url, params=None):
            if url == mod.ROOT:
                return {"layers":[{"id":12,"name":"LiDAR Coverage DTM"}]}
            if url.endswith("/12"):
                return {"fields":[{"name":"OBJECTID"}]}
            raise AssertionError(url)
        with tempfile.TemporaryDirectory() as tmp:
            out = str(pathlib.Path(tmp)/"missing.json")
            with patch.object(mod,"get_json",side_effect=fake),patch.object(sys,"argv",["gsi","--output",out]),contextlib.redirect_stdout(io.StringIO()):
                mod.main()
            data=json.loads(pathlib.Path(out).read_text())
            self.assertEqual(data["status"],"PARTIAL")
            self.assertEqual(data["errors"][0]["error"],"COUNTY_FIELD_MISSING")

    def test_service_error_rejected(self):
        with patch.object(mod,"get_json",return_value={"error":{"message":"Unavailable"}}),patch.object(sys,"argv",["gsi","--output","unused.json"]):
            with self.assertRaises(RuntimeError):
                mod.main()

    def test_invalid_bbox_rejected(self):
        with patch.object(sys,"argv",["gsi","--output","unused.json","--bbox-itm","10","20","9","30"]),contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as cm: mod.main()
        self.assertEqual(cm.exception.code,2)

if __name__=="__main__":
    unittest.main()

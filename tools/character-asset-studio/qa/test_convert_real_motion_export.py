"""Tests for the strict world-contact evidence converter."""
import copy
import unittest
from convert_real_motion_export import convert
from test_validate_real_motion_export import valid


class ConverterTests(unittest.TestCase):
    def test_valid_export_converts(self):
        out = convert(valid())
        self.assertEqual(out["schema"], "cas/stance-frames/1.0")
        self.assertEqual(out["frames"][0]["contacts"]["L"]["worldPx"], [20, 30])
        self.assertEqual(out["frames"][0]["contacts"]["R"]["phase"], "swing")

    def test_missing_world_blocks(self):
        x = valid()
        x["frames"][0]["feet"]["L"]["worldPx"] = None
        self.assertEqual(convert(x)["status"], "BLOCKED")

    def test_missing_mapping_blocks(self):
        x = valid()
        x["frames"][0]["feet"]["near"] = x["frames"][0]["feet"].pop("L")
        self.assertEqual(convert(x)["status"], "BLOCKED")

    def test_stance_id_switch_blocks(self):
        x = valid()
        second = copy.deepcopy(x["frames"][0])
        second["id"] = "f1"
        second["timeMs"] = 100
        second["feet"]["L"]["stanceId"] = "L1"
        x["frames"].append(second)
        self.assertEqual(convert(x)["status"], "BLOCKED")

    def test_replant_after_swing(self):
        x = valid()
        swing = copy.deepcopy(x["frames"][0])
        swing["id"] = "f1"
        swing["timeMs"] = 100
        swing["feet"]["L"] = {"phase": "swing", "provenance": "rig:L"}
        plant = copy.deepcopy(x["frames"][0])
        plant["id"] = "f2"
        plant["timeMs"] = 200
        plant["feet"]["L"]["stanceId"] = "L1"
        x["frames"].extend([swing, plant])
        self.assertEqual(convert(x)["schema"], "cas/stance-frames/1.0")


if __name__ == "__main__":
    unittest.main()

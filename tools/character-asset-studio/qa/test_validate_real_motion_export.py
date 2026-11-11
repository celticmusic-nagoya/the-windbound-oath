"""Unit tests: real contact evidence must fail closed when incomplete."""
import copy
import unittest
from validate_real_motion_export import validate


def valid():
    return {
        "schema": "cas/real-motion-contact-export/1.0", "rigVersion": "1.0",
        "source": {"path": "actual/pose.json", "sha256": "a" * 64},
        "coordinateSystem": {"units": "worldPx", "scale": 1, "origin": "actor-world"},
        "frames": [{"id": "f0", "timeMs": 0,
                    "actorTransform": {"translationPx": [0, 0], "rotationDeg": 0, "scale": 1},
                    "feet": {"L": {"phase": "stance", "stanceId": "L0", "contactPoint": "heel", "worldPx": [20, 30], "provenance": "rig:L:heel"},
                             "R": {"phase": "swing", "provenance": "rig:R:toe"}}}]
    }


class EvidenceValidationTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate(valid())["status"], "PASS")

    def test_null_world_contact_blocks(self):
        x = valid()
        x["frames"][0]["feet"]["L"]["worldPx"] = None
        self.assertEqual(validate(x)["status"], "BLOCKED")

    def test_missing_foot_mapping_blocks(self):
        x = valid()
        x["frames"][0]["feet"]["near"] = x["frames"][0]["feet"].pop("L")
        self.assertEqual(validate(x)["status"], "BLOCKED")

    def test_missing_transform_blocks(self):
        x = valid()
        del x["frames"][0]["actorTransform"]
        self.assertEqual(validate(x)["status"], "BLOCKED")

    def test_inverted_mapping_without_provenance_blocks(self):
        x = valid()
        x["frames"][0]["feet"]["L"]["provenance"] = ""
        self.assertEqual(validate(x)["status"], "BLOCKED")

    def test_unknown_scale_blocks(self):
        x = valid()
        x["coordinateSystem"]["scale"] = "DOCUMENTED_SCALE"
        self.assertEqual(validate(x)["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()

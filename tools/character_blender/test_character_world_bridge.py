"""Negative controls for the candidate-only 3D character/world bridge."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_character_world_bridge import validate

def candidate():
    return {
        "schema_version": "character-world-bridge/v1", "status": "CANDIDATE",
        "character_id": "morwen",
        "character_asset_sha256": "a" * 64, "world_asset_sha256": "b" * 64,
        "coordinate_system": None, "units_per_meter": None,
        "projection": None, "camera": None, "ground_contact": None,
        "shadow": None, "occlusion": None, "animation_states": None,
        "collision": None, "renderer": None,
        "qa": {"G1": "BLOCKED", "G2": "NOT_RUN", "G3": "NOT_RUN", "G4": "NOT_RUN"}
    }

class BridgeTests(unittest.TestCase):
    def test_candidate(self):
        self.assertEqual(validate(candidate()), [])
    def test_rejects_forged_art_pass(self):
        x = candidate(); x["qa"]["G2"] = "PASS"
        self.assertTrue(validate(x))
    def test_rejects_unapproved_scale(self):
        x = candidate(); x["units_per_meter"] = 1.0
        self.assertTrue(validate(x))
    def test_rejects_unapproved_renderer(self):
        x = candidate(); x["renderer"] = "threejs"
        self.assertTrue(validate(x))
    def test_rejects_bad_sha(self):
        x = candidate(); x["world_asset_sha256"] = "bad"
        self.assertTrue(validate(x))
    def test_rejects_missing_gate(self):
        x = candidate(); del x["qa"]["G4"]
        self.assertTrue(validate(x))

if __name__ == "__main__":
    unittest.main()

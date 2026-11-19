import unittest
from validate_patch import validate

BASE = dict(
    schema="two-render-patch-v1",
    asset_id="aidan-house",
    method_family="lighting-v1",
    root_cause="too-dark",
    adjustments={"exposure_delta": 0.1},
)

class GuardTest(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate(BASE)["adjustments"]["exposure_delta"], 0.1)

    def test_clamp(self):
        proposal = {**BASE, "adjustments": {"exposure_delta": 50}}
        self.assertEqual(validate(proposal)["adjustments"]["exposure_delta"], 0.2)

    def test_reject_code(self):
        with self.assertRaises(ValueError):
            validate({**BASE, "execute_python": "import os"})

    def test_reject_geometry(self):
        with self.assertRaises(ValueError):
            validate({**BASE, "adjustments": {"delete_mesh": 1}})

    def test_reject_nan(self):
        with self.assertRaises(ValueError):
            validate({**BASE, "adjustments": {"exposure_delta": float("nan")}})

    def test_reject_many(self):
        keys = ("exposure_delta", "roughness_delta", "light_size_multiplier", "camera_ortho_multiplier")
        with self.assertRaises(ValueError):
            validate({**BASE, "adjustments": {key: 0 for key in keys}})

if __name__ == "__main__":
    unittest.main()

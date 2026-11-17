"""Unit tests for silhouette measurements; no reference files altered."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from PIL import Image
except ImportError:
    Image = None
from measure_morwen_reference_silhouettes import measure

@unittest.skipIf(Image is None, "Pillow not installed")
class SilhouetteTests(unittest.TestCase):
    def test_bounds_and_rows(self):
        img = Image.new("RGBA", (8, 10), (0, 0, 0, 0))
        for x in (2, 3, 4):
            img.putpixel((x, 4), (1, 2, 3, 255))
        img.putpixel((3, 5), (1, 2, 3, 128))
        result = measure(img)
        self.assertEqual(result["nonzero_alpha_bbox_xyxy_exclusive"], [2, 4, 5, 6])
        self.assertEqual(result["silhouette_height_px"], 2)
        self.assertEqual(len(result["row_silhouette_extents"]), 2)
        self.assertEqual(result["anatomical_landmarks"], "NOT_MEASURED")
    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            measure(Image.new("RGBA", (4, 4), (0, 0, 0, 0)))
    def test_rgb_rejected(self):
        with self.assertRaises(ValueError):
            measure(Image.new("RGB", (4, 4)))
if __name__ == "__main__":
    unittest.main()

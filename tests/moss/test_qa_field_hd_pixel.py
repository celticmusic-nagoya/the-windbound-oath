import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[2] / "scripts" / "qa_field_hd_pixel.py"
spec = importlib.util.spec_from_file_location("hd_qa", MODULE)
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)

class CandidateQATests(unittest.TestCase):
    def test_empty_character_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.object(qa, "CANDIDATES", Path(root)):
                with self.assertRaisesRegex(ValueError, "Missing required direction"):
                    qa.validate(Path(root) / "aidan")

    def test_valid_rgba_direction_set(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "aidan"
            directory.mkdir()
            for name in qa.DIRECTIONS:
                im = Image.new("RGBA", (32, 48), (0, 0, 0, 0))
                for x in range(8, 24):
                    for y in range(8, 47):
                        im.putpixel((x, y), (50, 80, 120, 255))
                im.save(directory / (name + ".png"))
            with patch.object(qa, "CANDIDATES", Path(root)):
                result = qa.validate(directory)
            self.assertEqual(len(result["files"]), 4)
            self.assertEqual(result["visual_official_match"], "NOT_RUN")
            self.assertEqual(result["android_physical_device"], "NOT_RUN")

    def test_opaque_images_are_rejected(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "emma"
            directory.mkdir()
            for name in qa.DIRECTIONS:
                Image.new("RGBA", (32, 48), (1, 2, 3, 255)).save(directory / (name + ".png"))
            with patch.object(qa, "CANDIDATES", Path(root)):
                with self.assertRaisesRegex(ValueError, "transparent"):
                    qa.validate(directory)

    def test_outside_candidate_directory_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.object(qa, "CANDIDATES", Path(root) / "allowed"):
                with self.assertRaisesRegex(ValueError, "Only candidate"):
                    qa.validate(Path(root) / "other")

if __name__ == "__main__":
    unittest.main()

import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("tiles", Path(__file__).with_name("resolve_copernicus_public_tiles.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class CopernicusPublicTileTests(unittest.TestCase):
    def test_clare_tile_identifier(self):
        self.assertEqual(mod.tile_name(52, -10), "Copernicus_DSM_COG_10_N52_00_W010_00_DEM")

    def test_available_tile_has_url_but_not_license_approval(self):
        name = mod.tile_name(52, -10)
        result = mod.resolve(name + "/\n", [(52, -10)])[0]
        self.assertTrue(result["published_in_index"])
        self.assertEqual(result["cog_url"], mod.BASE + name + "/" + name + ".tif")
        self.assertFalse(result["canon"])
        self.assertIsNone(result["download_sha256"])

    def test_unreleased_tile_has_no_download_url(self):
        result = mod.resolve("", [(52, -10)])[0]
        self.assertFalse(result["published_in_index"])
        self.assertIsNone(result["cog_url"])

    def test_substring_cannot_certify_tile(self):
        name = mod.tile_name(52, -10)
        self.assertFalse(mod.resolve("INVALID_" + name + "_SUFFIX", [(52, -10)])[0]["published_in_index"])

    def test_canonical_object_path_can_certify_tile(self):
        name = mod.tile_name(52, -10)
        self.assertTrue(mod.resolve(name + "/" + name + ".tif", [(52, -10)])[0]["published_in_index"])

    def test_mismatched_object_name_rejected(self):
        name = mod.tile_name(52, -10)
        self.assertFalse(mod.resolve(name + "/other.tif", [(52, -10)])[0]["published_in_index"])

    def test_invalid_coordinates_rejected(self):
        with self.assertRaises(ValueError):
            mod.tile_name(90, -10)

if __name__ == "__main__":
    unittest.main()

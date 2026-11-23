import importlib.util
import pathlib
import tempfile
import unittest
import numpy as np
import rasterio
from rasterio.transform import from_origin

spec = importlib.util.spec_from_file_location('preflight', pathlib.Path(__file__).with_name('copernicus_dem_preflight.py'))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class RasterPreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = pathlib.Path(self.tmp.name) / 'synthetic.tif'

    def make_raster(self, crs='EPSG:4326', bands=1):
        with rasterio.open(self.path, 'w', driver='GTiff', height=3, width=3,
                count=bands, dtype='float32', crs=crs,
                transform=from_origin(-9.5, 53, 1/3600, 1/3600), nodata=-9999) as ds:
            for b in range(1, bands+1): ds.write(np.ones((3,3), dtype='float32'), b)

    def test_valid_geotiff_remains_blocked_without_license(self):
        self.make_raster()
        result = mod.audit(self.path)
        self.assertEqual(result['qa'], 'BLOCKED')
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['raster']['epsg'], 4326)
        self.assertFalse(result['canonical_adoption'])

    def test_wrong_crs_blocked(self):
        self.make_raster('EPSG:3857')
        self.assertIn('EXPECTED_NATIVE_EPSG4326', mod.audit(self.path)['errors'])

    def test_multiple_bands_blocked(self):
        self.make_raster(bands=2)
        self.assertIn('EXPECTED_SINGLE_BAND', mod.audit(self.path)['errors'])

    def test_hash_mismatch_fails(self):
        self.make_raster()
        result = mod.audit(self.path, '0'*64)
        self.assertEqual(result['qa'], 'FAIL')

    def test_matching_hash_does_not_certify_source(self):
        self.make_raster()
        sha = mod.audit(self.path)['sha256']
        result = mod.audit(self.path, sha)
        self.assertTrue(result['sha_match'])
        self.assertEqual(result['qa'], 'BLOCKED')

    def test_all_nodata_blocked(self):
        self.make_raster()
        with rasterio.open(self.path, 'r+') as ds:
            ds.write(np.full((3, 3), -9999, dtype='float32'), 1)
        result = mod.audit(self.path)
        self.assertIn('NO_FINITE_VALID_ELEVATIONS', result['errors'])
        self.assertEqual(result['raster']['finite_valid_cells'], 0)

    def test_nonfinite_cells_ignored(self):
        self.make_raster()
        with rasterio.open(self.path, 'r+') as ds:
            ds.write(np.array([[1, 2, 3], [4, np.nan, 6], [7, 8, -9999]], dtype='float32'), 1)
        result = mod.audit(self.path)
        self.assertEqual(result['raster']['finite_valid_cells'], 7)
        self.assertEqual(result['raster']['finite_min'], 1.0)
        self.assertEqual(result['raster']['finite_max'], 8.0)

    def test_invalid_raster_blocked(self):
        self.path.write_text('not a raster')
        self.assertTrue(any(e.startswith('RASTER_OPEN_FAILED') for e in mod.audit(self.path)['errors']))

if __name__ == '__main__': unittest.main()

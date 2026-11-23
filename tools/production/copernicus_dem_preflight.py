#!/usr/bin/env python3
"""Fail-closed local GeoTIFF DEM preflight; never asserts source authenticity."""
import argparse
import hashlib
import json
import numpy as np
from pathlib import Path


def audit(path, expected_sha256=None):
    path = Path(path)
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    sha = h.hexdigest()
    result = {'path': str(path), 'sha256': sha, 'bytes': path.stat().st_size,
              'sha_match': None if expected_sha256 is None else sha == expected_sha256.lower(),
              'source_license': 'UNVERIFIED', 'source_authenticity': 'UNVERIFIED',
              'vertical_datum': 'UNVERIFIED_FROM_RASTER', 'canonical_adoption': False,
              'raster': None, 'errors': [], 'qa': 'BLOCKED'}
    if result['sha_match'] is False:
        result['errors'].append('SHA256_MISMATCH')
        result['qa'] = 'FAIL'
    try:
        import rasterio
        with rasterio.open(path) as ds:
            crs = ds.crs.to_epsg() if ds.crs else None
            result['raster'] = {'driver': ds.driver, 'crs': str(ds.crs) if ds.crs else None,
                'epsg': crs, 'width': ds.width, 'height': ds.height,
                'bands': ds.count, 'dtype': list(ds.dtypes), 'nodata': ds.nodata,
                'bounds': list(ds.bounds), 'resolution': list(ds.res),
                'mask_flags': [list(map(str, x)) for x in ds.mask_flag_enums]}
            # Block-wise scan avoids loading a full terrain tile into memory.
            if ds.count == 1:
                valid_count = 0
                finite_min = None
                finite_max = None
                for _, window in ds.block_windows(1):
                    block = ds.read(1, window=window, masked=True)
                    valid = block.compressed()
                    finite = valid[np.isfinite(valid)]
                    valid_count += int(finite.size)
                    if finite.size:
                        lo, hi = float(finite.min()), float(finite.max())
                        finite_min = lo if finite_min is None else min(finite_min, lo)
                        finite_max = hi if finite_max is None else max(finite_max, hi)
                result['raster']['finite_valid_cells'] = valid_count
                result['raster']['finite_min'] = finite_min
                result['raster']['finite_max'] = finite_max
                if valid_count == 0:
                    result['errors'].append('NO_FINITE_VALID_ELEVATIONS')
            if ds.driver != 'GTiff': result['errors'].append('NOT_GEOTIFF')
            if crs != 4326: result['errors'].append('EXPECTED_NATIVE_EPSG4326')
            if ds.count != 1: result['errors'].append('EXPECTED_SINGLE_BAND')
            if not all(t.startswith(('float', 'int', 'uint')) for t in ds.dtypes):
                result['errors'].append('NON_NUMERIC_BAND')
            if ds.width < 2 or ds.height < 2: result['errors'].append('TOO_SMALL')
            if not all(0 < abs(v) <= 1 for v in ds.res):
                result['errors'].append('UNEXPECTED_PIXEL_SIZE_DEGREES')
            if not (-180 <= ds.bounds.left < ds.bounds.right <= 180 and
                    -90 <= ds.bounds.bottom < ds.bounds.top <= 90):
                result['errors'].append('INVALID_WGS84_BOUNDS')
    except (ImportError, OSError, ValueError) as exc:
        result['errors'].append('RASTER_OPEN_FAILED:' + type(exc).__name__)
    if result['errors']:
        result['qa'] = 'FAIL' if 'SHA256_MISMATCH' in result['errors'] else 'BLOCKED'
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('raster')
    p.add_argument('--expected-sha256')
    p.add_argument('--output', required=True)
    args = p.parse_args()
    if args.expected_sha256 and (len(args.expected_sha256) != 64 or
        any(c not in '0123456789abcdefABCDEF' for c in args.expected_sha256)):
        p.error('expected SHA256 must be 64 hex digits')
    result = audit(args.raster, args.expected_sha256)
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'qa': result['qa'], 'errors': result['errors'], 'sha256': result['sha256']}))
    if result['qa'] == 'FAIL': raise SystemExit(2)

if __name__ == '__main__': main()

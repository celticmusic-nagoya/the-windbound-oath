#!/usr/bin/env python3
"""Inspect an already downloaded terrain raster. Read-only; never certifies canon."""
import argparse
import hashlib
import json
from pathlib import Path

def audit(path, expected_sha=None):
    path = Path(path)
    sha = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(chunk)
    actual = sha.hexdigest()
    result = {
        "source_path": str(path), "source_size_bytes": path.stat().st_size,
        "source_sha256": actual, "sha256_match": None if expected_sha is None else actual.lower() == expected_sha.lower(),
        "source_license": "UNVERIFIED_PER_TILE", "vertical_datum": "UNVERIFIED_PER_TILE",
        "raster_metadata": None, "raster_read": "NOT_RUN",
        "source_provenance": "USER_OR_RUNNER_PROVIDED_NOT_AUTHENTICATED",
        "canonical_adoption": False, "qa": "BLOCKED"
    }
    try:
        import rasterio
        with rasterio.open(path) as ds:
            result["raster_metadata"] = {
                "driver": ds.driver, "crs": str(ds.crs) if ds.crs else None,
                "width": ds.width, "height": ds.height, "bands": ds.count,
                "pixel_size": list(ds.res), "bounds": list(ds.bounds),
                "nodata": ds.nodata, "dtype": ds.dtypes[0] if ds.count else None,
                "tags": ds.tags()
            }
            result["raster_read"] = "PASS_METADATA_ONLY"
    except (ImportError, OSError, ValueError) as e:
        result["raster_read"] = "BLOCKED_" + type(e).__name__
    if expected_sha is not None and not result["sha256_match"]:
        result["qa"] = "FAIL_SHA256"
    return result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raster")
    ap.add_argument("--expected-sha256")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    if args.expected_sha256 and (len(args.expected_sha256) != 64 or
                                 any(c not in "0123456789abcdefABCDEF" for c in args.expected_sha256)):
        ap.error("expected SHA-256 must be 64 hex characters")
    result = audit(args.raster, args.expected_sha256)
    Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str)+"\n", encoding="utf-8")
    print(json.dumps({"qa": result["qa"], "sha256": result["source_sha256"],
                      "raster_read": result["raster_read"]}))
    if result["qa"] == "FAIL_SHA256":
        raise SystemExit(2)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""One-shot, noncanonical public COG acquisition. Never runs without explicit invocation.

Uses existing tile resolver and DEM preflight; does not bypass product-license review.
Output is a local, untracked reference raster, NOT a GitHub or game asset.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from urllib.request import urlopen

from resolve_copernicus_public_tiles import INDEX, resolve
from copernicus_dem_preflight import audit

MAX_INDEX = 5_000_000
MAX_RASTER = 250_000_000

def bounded_copy(response, destination, maximum):
    digest = hashlib.sha256()
    total = 0
    with open(destination, "wb") as out:
        while True:
            chunk = response.read(min(1024 * 1024, maximum + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > maximum:
                raise ValueError("REMOTE_FILE_EXCEEDS_SIZE_LIMIT")
            out.write(chunk)
            digest.update(chunk)
    return {"sha256": digest.hexdigest(), "bytes": total}

def acquire(lat, lon, out_dir, opener=urlopen):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with opener(INDEX, timeout=30) as stream:
        raw = stream.read(MAX_INDEX + 1)
    if len(raw) > MAX_INDEX:
        raise ValueError("INDEX_EXCEEDS_SIZE_LIMIT")
    matches = resolve(raw.decode("utf-8"), [(lat, lon)])
    tile = matches[0]
    if not tile["published_in_index"]:
        return {"qa": "BLOCKED_TILE_NOT_LISTED", "tile": tile,
                "index_sha256": hashlib.sha256(raw).hexdigest()}
    # Atomic staging: no partially downloaded file is promoted.
    fd, tmp = tempfile.mkstemp(prefix=".cop_dem_", suffix=".tif", dir=out_dir)
    os.close(fd)
    target = out_dir / (tile["tile_id"] + ".tif")
    try:
        with opener(tile["cog_url"], timeout=60) as stream:
            receipt = bounded_copy(stream, tmp, MAX_RASTER)
        if receipt["bytes"] == 0:
            raise ValueError("EMPTY_RASTER")
        inspection = audit(tmp, receipt["sha256"])
        if inspection["errors"]:
            return {"qa": "BLOCKED_RASTER_INVALID", "tile": tile,
                    "index_sha256": hashlib.sha256(raw).hexdigest(),
                    "receipt": receipt, "inspection": inspection}
        # Same-directory hard link is an atomic no-clobber promotion.
        # os.replace would overwrite a file created after the exists() check.
        try:
            os.link(tmp, target)
        except FileExistsError as exc:
            raise FileExistsError("REFUSE_TO_OVERWRITE_EXISTING_RASTER") from exc
        return {"qa": "BLOCKED_LICENSE_DATUM_CANON",
                "tile": tile, "index_sha256": hashlib.sha256(raw).hexdigest(),
                "receipt": receipt, "raster_path": str(target),
                "inspection": inspection, "canonical_adoption": False}
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lat", type=int, default=52)
    p.add_argument("--lon", type=int, default=-10)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--report", required=True)
    args = p.parse_args()
    result = acquire(args.lat, args.lon, args.out_dir)
    # Never overwrite an existing receipt or a raster via --report.
    with Path(args.report).open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"qa": result["qa"], "tile": result["tile"]["tile_id"]}))

if __name__ == "__main__":
    main()

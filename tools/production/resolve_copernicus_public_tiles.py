#!/usr/bin/env python3
"""Resolve candidate Copernicus GLO-30 Public AWS COG tiles without downloading raster bytes.

Tile presence is verified against the published tileList.txt; a candidate name
alone is NOT evidence that a tile is released or that its licence is accepted.
"""
import argparse
import hashlib
import json
import re
from urllib.request import urlopen

INDEX = "https://copernicus-dem-30m.s3.amazonaws.com/tileList.txt"
BASE = "https://copernicus-dem-30m.s3.amazonaws.com/"
PATTERN = re.compile(r"^Copernicus_DSM_COG_10_[NS][0-9]{2}_00_[EW][0-9]{3}_00_DEM$")

def tile_name(lat, lon):
    if not (-90 <= lat < 90 and -180 <= lon < 180):
        raise ValueError("integer tile coordinates outside valid range")
    return "Copernicus_DSM_COG_10_%s%02d_00_%s%03d_00_DEM" % (
        "N" if lat >= 0 else "S", abs(lat), "E" if lon >= 0 else "W", abs(lon))

def resolve(index_text, coordinates):
    # Accept only exact tile identifiers or canonical directory/object paths.\n    # Substring matching can falsely certify a tile in malformed index text.\n    published = set()\n    for line in index_text.splitlines():\n        item = line.strip().rstrip("/")\n        if not item: continue\n        parts = item.split("/")\n        candidate = parts[0]\n        if PATTERN.fullmatch(candidate) and (\n            len(parts) == 1 or (len(parts) == 2 and parts[1] == candidate + ".tif")\n        ):\n            published.add(candidate)
    result = []
    for lat, lon in coordinates:
        name = tile_name(lat, lon)
        found = name in published
        result.append({"lat_south_deg": lat, "lon_west_deg": lon,
                       "tile_id": name, "published_in_index": found,
                       "cog_url": BASE + name + "/" + name + ".tif" if found else None,
                       "source_license": "PENDING_EXACT_TERMS_REVIEW",
                       "vertical_datum": "PENDING_TILE_METADATA_QA",
                       "download_sha256": None, "canon": False})
    return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    p.add_argument("--index-file", help="offline copy of official tileList.txt")
    p.add_argument("--tile", nargs=2, type=int, action="append", metavar=("LAT", "LON"),
                   help="1-degree tile south/west integer coordinates; repeatable")
    args = p.parse_args()
    coordinates = [tuple(t) for t in args.tile] if args.tile else [(52, -10), (52, -9), (53, -10), (53, -9)]
    if args.index_file:
        with open(args.index_file, "rb") as f: raw = f.read()
        origin = "LOCAL_UNAUTHENTICATED_COPY"
    else:
        with urlopen(INDEX, timeout=25) as response: raw = response.read(5_000_001)
        if len(raw) > 5_000_000: raise ValueError("tile index too large")
        origin = INDEX
    rows = resolve(raw.decode("utf-8"), coordinates)
    report = {"schema": "two.copernicus.public_tile_index.v1", "index_origin": origin,
              "index_sha256": hashlib.sha256(raw).hexdigest(), "tile_count": len(rows),
              "tiles": rows, "qa": "CANDIDATE_INDEX_ONLY", "license_accepted": False,
              "raster_downloaded": False, "G1": "BLOCKED"}
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(json.dumps({"qa": report["qa"], "available_candidates": sum(r["published_in_index"] for r in rows)}))

if __name__ == "__main__": main()

#!/usr/bin/env python3
"""Read-only Irish GSI coverage probe for TWO regional blueprint; no raster download."""
import argparse
import hashlib
import json
import pathlib
import urllib.parse
import urllib.request

SERVICE = "https://gsi.geodata.gov.ie/server/rest/services/Lidar/IE_GSI_LiDAR_Coverage_GSI_DCHG_DP_IE26_ITM/MapServer/0/query"
REFERENCE_ITM = (504197.3660191937, 692173.4071269431)

def query_url(east, north):
    params = {
        "geometry": f"{east:.6f},{north:.6f}",
        "geometryType": "esriGeometryPoint", "inSR": "2157",
        "spatialRel": "esriSpatialRelIntersects", "outFields": "*",
        "returnGeometry": "false", "f": "json"
    }
    return SERVICE + "?" + urllib.parse.urlencode(params)

def probe(east, north, offline=False, opener=urllib.request.urlopen):
    url = query_url(east, north)
    result = {
        "schema": "two.gsi.coverage.probe.v1",
        "query_url": url, "point_itm_m": [east, north],
        "point_role": "REFERENCE_ONLY", "coverage": "NOT_VERIFIED",
        "tile_download": "NOT_RUN", "raster_sha256": None,
        "features": [], "error": None
    }
    if offline:
        result["error"] = "OFFLINE_TEST_ONLY"
        return result
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TWO-region-blueprint/1.0"})
        with opener(req, timeout=25) as response:
            raw = response.read(8_000_001)
        if len(raw) > 8_000_000:
            raise ValueError("oversized service response")
        payload = json.loads(raw)
        if "error" in payload:
            raise ValueError(str(payload["error"]))
        if not isinstance(payload.get("features"), list):
            raise ValueError("missing features list")
        result["response_sha256"] = hashlib.sha256(raw).hexdigest()
        result["features"] = [f.get("attributes", {}) for f in payload["features"]]
        result["coverage"] = "INTERSECTS" if result["features"] else "NO_INTERSECTION"
    except Exception as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)[:300]
    return result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="gsi_coverage_result.json")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--east", type=float, default=REFERENCE_ITM[0])
    ap.add_argument("--north", type=float, default=REFERENCE_ITM[1])
    args = ap.parse_args()
    result = probe(args.east, args.north, args.offline)
    dest = pathlib.Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"coverage": result["coverage"], "features": len(result["features"]), "out": str(dest), "error": result["error"]}, ensure_ascii=False))
    return 0 if result["coverage"] in ("INTERSECTS", "NO_INTERSECTION") else 2

if __name__ == "__main__":
    raise SystemExit(main())

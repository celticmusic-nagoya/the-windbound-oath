#!/usr/bin/env python3
"""Read-only ArcGIS coverage probe. A point intersection is NOT a verified DEM."""
import argparse
import hashlib
import json
import pathlib
import urllib.parse
import urllib.request

SERVICES = {
    "OPW_NASC": "https://gsi.geodata.gov.ie/server/rest/services/Lidar/IE_GSI_LiDAR_Coverage_OPW_NASC_IE26_ITM/MapServer/3/query",
    "TII": "https://gsi.geodata.gov.ie/server/rest/services/Lidar/IE_GSI_LiDAR_Coverage_TII_IE26_ITM/MapServer/0/query",
}

def probe(name, url, x, y, timeout):
    params = {"where": "1=1", "geometry": f"{x},{y}",
              "geometryType": "esriGeometryPoint", "inSR": "2157",
              "spatialRel": "esriSpatialRelIntersects", "outFields": "*",
              "returnGeometry": "false", "f": "json"}
    result = {"service": name, "url": url, "reference_point_itm_m": [x, y],
              "coverage": "NOT_VERIFIED", "feature_count": None,
              "features": [], "response_sha256": None, "error": None,
              "tile_download": "NOT_RUN", "raster_sha256": None}
    try:
        req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params),
                                     headers={"User-Agent": "TWO-region-evidence/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError("response too large")
        result["response_sha256"] = hashlib.sha256(raw).hexdigest()
        data = json.loads(raw)
        if "error" in data:
            raise ValueError("ArcGIS error: " + str(data["error"]))
        if not isinstance(data.get("features"), list):
            raise ValueError("missing features list")
        result["features"] = [f.get("attributes", {}) for f in data["features"]]
        result["feature_count"] = len(result["features"])
        result["coverage"] = "INTERSECTS" if result["feature_count"] else "NO_INTERSECTION"
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--x", type=float, default=504197.3660191937)
    parser.add_argument("--y", type=float, default=692173.4071269431)
    args = parser.parse_args()
    payload = {"schema": "two.region.gsi.multi_service_probe.v1",
               "status": "CANDIDATE_NOT_CANONICAL", "point_role": "REFERENCE_ONLY",
               "results": [probe(name, url, args.x, args.y, args.timeout)
                           for name, url in SERVICES.items()],
               "qa": {"G1": "BLOCKED", "G2": "NOT_RUN",
                      "G3": "NOT_RUN", "G4": "NOT_RUN"}}
    pathlib.Path(args.out).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps({r["service"]: r["coverage"] for r in payload["results"]}))

if __name__ == "__main__":
    main()

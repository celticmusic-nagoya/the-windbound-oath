#!/usr/bin/env python3
"""Read-only GSI LiDAR coverage discovery. No raster downloads or writes to canon."""
import argparse
import json
import pathlib
import urllib.parse
import urllib.request

ROOT = "https://gsi.geodata.gov.ie/server/rest/services/Lidar/IE_GSI_LiDAR_Coverage_GSI_Phase2_IE26_ITM/FeatureServer"

def get_json(url, params=None):
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "TWO-source-audit/1.0"}), timeout=25) as r:
        return json.load(r)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, help="write discovery JSON, not a source raster")
    ap.add_argument("--bbox-itm", nargs=4, type=float, metavar=("XMIN","YMIN","XMAX","YMAX"),
                    help="optional EPSG:2157 bbox; without it only list candidate Clare records")
    ap.add_argument("--limit", type=int, default=500)
    if not 1 <= args.limit <= 1000:
        ap.error("--limit must be between 1 and 1000")
    args = ap.parse_args()
    if args.bbox_itm and not (args.bbox_itm[0] < args.bbox_itm[2] and args.bbox_itm[1] < args.bbox_itm[3]):
        ap.error("bbox must have increasing min/max coordinates")
    service = get_json(ROOT, {"f":"json"})
    layers = service.get("layers", [])
    candidates = [x for x in layers if "DTM" in x.get("name","").upper() or "COVERAGE" in x.get("name","").upper()]
    if not candidates:
        candidates = layers
    report = {"source":ROOT,"bbox_epsg2157":args.bbox_itm,"query_status":"EXECUTED",
              "coverage_is_not_dem":True,"records":[],"errors":[]}
    for layer in candidates:
        lid = layer["id"]
        try:
            meta = get_json(f"{ROOT}/{lid}", {"f":"json"})
            fields = {x["name"] for x in meta.get("fields", [])}
            county = next((x for x in fields if x.upper()=="COUNTY"),None)
            if not county:
                continue
            desired = [x for x in ("OBJECTID","DATA_URL","DATA_NAME","LICENCE","RESOLUTION","DATECAPTUR","LOCATION","COUNTY","OWNER","RMS_ERROR") if x in fields]
            oid = meta.get("objectIdField") or "OBJECTID"
            if oid not in desired and oid in fields: desired.append(oid)
            params = {"f":"json","where":f"{county} LIKE '%Clare%'","outFields":",".join(desired),
                      "returnGeometry":"false","resultRecordCount":min(args.limit,1000)}
            if args.bbox_itm:
                params.update({"geometry":",".join(map(str,args.bbox_itm)),"geometryType":"esriGeometryEnvelope",
                               "inSR":"2157","spatialRel":"esriSpatialRelIntersects"})
            data = get_json(f"{ROOT}/{lid}/query", params)
            if "error" in data:
                raise ValueError(data["error"])
            report["records"].append({"layer_id":lid,"layer_name":layer.get("name"),"fields":desired,
                "features":[x.get("attributes",{}) for x in data.get("features",[])],
                "exceeded_transfer_limit":data.get("exceededTransferLimit",False),
                "page_full":len(data.get("features",[])) >= args.limit})
        except Exception as e:
            report["errors"].append({"layer_id":lid,"error":str(e)})
    report["status"] = "PARTIAL" if report["errors"] or not report["records"] or any(x["exceeded_transfer_limit"] or x["page_full"] for x in report["records"]) else "COMPLETE_QUERY_ONLY"
    report["record_count"] = sum(len(x["features"]) for x in report["records"])
    report["status"] = "PARTIAL" if report["record_count"] == 0 else report["status"]
    report["raster_downloaded"] = False
    report["raster_sha256"] = None
    pathlib.Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"
",encoding="utf-8")
    print(json.dumps({"status":report["status"],"layers":len(report["records"]),"errors":len(report["errors"])},ensure_ascii=False))

if __name__ == "__main__":
    main()

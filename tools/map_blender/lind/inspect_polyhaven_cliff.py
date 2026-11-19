"""Fail-closed official Poly Haven scan metadata intake (no asset download).

Usage: python tools/map_blender/lind/inspect_polyhaven_cliff.py --out out.json
"""
import argparse
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ASSETS=("coastal_cliff_04","coastal_cliff_02")
BASE="https://api.polyhaven.com"

def fetch(path):
    req=urllib.request.Request(BASE+path,headers={"User-Agent":"TWO-LIND-source-intake/1.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=18) as response:
        if response.status!=200:
            raise RuntimeError("Non-200 metadata response")
        return json.load(response)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    a=p.parse_args()
    records=[]
    for asset in ASSETS:
        info=fetch("/info/"+asset)
        files=fetch("/files/"+asset)
        if not isinstance(info,dict) or not isinstance(files,dict) or not files:
            raise RuntimeError("Incomplete official metadata for "+asset)
        records.append({
            "asset":asset,
            "official_url":"https://polyhaven.com/a/"+asset,
            "metadata_endpoint":BASE+"/info/"+asset,
            "files_endpoint":BASE+"/files/"+asset,
            "publisher_license_url":"https://polyhaven.com/license",
            "license_claim":"CC0 (must independently verify publisher terms before adoption)",
            "author":info.get("authors"),
            "categories":info.get("categories"),
            "file_format_keys":sorted(files.keys()),
            "file_metadata":files,
            "source_status":"CANDIDATE_METADATA_ONLY",
            "original_binary_sha256":None,
            "irish_capture_claim":"NOT_ESTABLISHED",
        })
    result={
      "captured_at_utc":datetime.now(timezone.utc).isoformat(),
      "api_origin":BASE,
      "assets":records,
      "G1":"BLOCKED_UNTIL_BINARY_AND_LICENSE_VERIFIED",
      "G2":"NOT_RUN","G3":"NOT_RUN","G4":"NOT_RUN"
    }
    out=Path(a.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("OFFICIAL_METADATA_FETCH_OK",len(records))

if __name__=="__main__":
    main()

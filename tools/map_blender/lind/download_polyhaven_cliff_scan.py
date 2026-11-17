"""Download official Poly Haven glTF scan and dependencies, preserving originals.

Restricted to named CC0 candidate and publisher-owned HTTPS asset URLs.
File size, provider MD5 and computed SHA256 are logged.
"""
import argparse
import hashlib
import json
import shutil
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HOSTS={"api.polyhaven.com","dl.polyhaven.org"}
ASSETS={"coastal_cliff_04","coastal_cliff_02"}
MAX_BYTES=120_000_000

def json_url(url):
    req=urllib.request.Request(url,headers={"User-Agent":"TWO-LIND-CC0-Scan-Intake/1.0"})
    with urllib.request.urlopen(req,timeout=45) as r:
        if r.status!=200: raise RuntimeError("HTTP "+str(r.status))
        return json.load(r)

def check_url(url):
    p=urllib.parse.urlsplit(url)
    if p.scheme!="https" or p.netloc not in HOSTS or p.username or p.password:
        raise RuntimeError("untrusted download host")
    if p.netloc=="dl.polyhaven.org" and not p.path.startswith("/file/ph-assets/Models/"):
        raise RuntimeError("untrusted source path")

def get_file(record,path):
    url=record["url"]
    check_url(url)
    declared=int(record["size"])
    if not 0<declared<=MAX_BYTES: raise RuntimeError("size outside limits")
    md5=hashlib.md5()
    sha=hashlib.sha256()
    total=0
    path.parent.mkdir(parents=True,exist_ok=True)
    req=urllib.request.Request(url,headers={"User-Agent":"TWO-LIND-CC0-Scan-Intake/1.0"})
    with urllib.request.urlopen(req,timeout=120) as r, path.open("wb") as w:
        while True:
            chunk=r.read(1<<20)
            if not chunk: break
            total+=len(chunk)
            if total>declared or total>MAX_BYTES: raise RuntimeError("oversized download")
            md5.update(chunk)
            sha.update(chunk)
            w.write(chunk)
    if total!=declared or md5.hexdigest()!=record["md5"]:
        path.unlink(missing_ok=True)
        raise RuntimeError("provider size/MD5 mismatch: "+path.name)
    return {"url":url,"bytes":total,"publisher_md5":record["md5"],"sha256":sha.hexdigest(),"path":str(path)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--asset",choices=sorted(ASSETS),default="coastal_cliff_04")
    p.add_argument("--out",required=True)
    a=p.parse_args()
    out=Path(a.out).resolve()
    source=out/"sources"/a.asset
    source.mkdir(parents=True,exist_ok=True)
    root="https://api.polyhaven.com"
    info=json_url(root+"/info/"+a.asset)
    files=json_url(root+"/files/"+a.asset)
    gltf=files["gltf"]["1k"]["gltf"]
    records=[(gltf,source/Path(urllib.parse.urlsplit(gltf["url"]).path).name)]
    for subpath,entry in sorted(gltf["include"].items()):
        relative=Path(subpath)
        if relative.is_absolute() or ".." in relative.parts:
            raise RuntimeError("unsafe dependency path")
        records.append((entry,source/relative))
    receipts=[]
    for record,path in records:
        receipts.append(get_file(record,path))
    document={
       "asset_id":a.asset,
       "official_page":"https://polyhaven.com/a/"+a.asset,
       "official_license":"https://polyhaven.com/license",
       "license_declared":"CC0 1.0",
       "authors":info.get("authors",{}),
       "capture_location":"NOT_ESTABLISHED",
       "api_info_url":root+"/info/"+a.asset,
       "api_files_url":root+"/files/"+a.asset,
       "captured_utc":datetime.now(timezone.utc).isoformat(),
       "files":receipts,
       "source_status":"ORIGINALS_CANDIDATE_PROTECTED",
       "G1":"PARTIAL_RIGHTS_PASS_SPATIAL_BLOCKED",
       "G2":"NOT_RUN","G3":"NOT_RUN","G4":"NOT_RUN"
    }
    (out/"source_manifest.json").write_text(json.dumps(document,indent=2)+"\n")
    print("SOURCE_VERIFIED",len(receipts),sum(x["bytes"] for x in receipts))
if __name__=="__main__":
    main()

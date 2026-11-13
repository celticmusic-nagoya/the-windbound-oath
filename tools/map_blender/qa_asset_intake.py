#!/usr/bin/env python3
"""Non-destructive asset intake checks. No Blender dependency or writes to source."""
import argparse, hashlib, json, pathlib, re, sys
from urllib.parse import urlsplit

def audit(root, manifest):
    failures=[];checked=[]
    try: entries=json.loads(manifest.read_text(encoding="utf-8"))["assets"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"status":"FAIL","checked":[],"failures":[f"invalid manifest: {exc}"]}
    if not isinstance(entries,list):return {"status":"FAIL","checked":[],"failures":["assets must be an array"]}
    seen=set()
    for i,item in enumerate(entries):
        if not isinstance(item,dict):failures.append(f"assets[{i}]: not an object");continue
        name=item.get("path");digest=item.get("sha256");license_id=item.get("license");source=item.get("source_url")
        if not all(isinstance(x,str) and x.strip() for x in (name,digest,license_id,source)):
            failures.append(f"assets[{i}]: missing path, sha256, license or source_url");continue
        if pathlib.PurePath(name).is_absolute() or "\\" in name:
            failures.append(f"assets[{i}]: invalid relative path");continue
        if name in seen:
            failures.append(f"assets[{i}]: duplicate asset path {name}");continue
        seen.add(name)
        if not re.fullmatch(r"[0-9a-fA-F]{64}",digest):
            failures.append(f"assets[{i}]: invalid SHA-256 format");continue
        parsed=urlsplit(source)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            failures.append(f"assets[{i}]: source_url must be a public HTTPS URL without credentials");continue
        p=(root/name).resolve()
        if not p.is_relative_to(root.resolve()):failures.append(f"assets[{i}]: path escapes asset root");continue
        if not p.is_file():failures.append(f"assets[{i}]: missing file {name}");continue
        actual=hashlib.sha256(p.read_bytes()).hexdigest()
        if actual.lower()!=digest.lower():failures.append(f"assets[{i}]: hash mismatch {name}");continue
        checked.append(name)
    return {"status":"PASS" if not failures else "FAIL","checked":checked,"failures":failures}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",required=True,type=pathlib.Path)
    parser.add_argument("--manifest",required=True,type=pathlib.Path)
    parser.add_argument("--report",type=pathlib.Path)
    args=parser.parse_args()
    result=audit(args.root,args.manifest)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
    return 0 if result["status"]=="PASS" else 1

if __name__=="__main__":sys.exit(main())

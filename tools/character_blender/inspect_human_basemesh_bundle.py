#!/usr/bin/env python3
"""Read-only CC0 Human Base Meshes ZIP inventory; fail closed on unsafe archive."""
import argparse,hashlib,json,pathlib,sys,zipfile
def inspect(path):
    path=pathlib.Path(path);size=path.stat().st_size
    if size>500_000_000:raise ValueError("archive exceeds 500 MB safety cap")
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    with zipfile.ZipFile(path) as z:
        infos=z.infolist()
        if len(infos)>5000:raise ValueError("too many archive members")
        entries=[];total=0
        for i in infos:
            name=i.filename;parts=pathlib.PurePosixPath(name).parts
            if name.startswith("/") or "\\" in name or ".." in parts or not parts or (i.external_attr>>16)&0o170000==0o120000:
                raise ValueError("unsafe archive member: "+name)
            total+=i.file_size
            if total>2_000_000_000:raise ValueError("uncompressed archive exceeds 2 GB")
            entries.append({"name":name,"bytes":i.file_size,"is_blend":name.lower().endswith(".blend")})
        bad=z.testzip()
        if bad:raise ValueError("ZIP CRC failure: "+bad)
    blend=[e for e in entries if e["is_blend"]]
    return {"status":"PASS_ARCHIVE_ONLY" if blend else "BLOCKED_NO_BLEND","source_sha256":digest,"archive_bytes":size,"uncompressed_bytes":total,"entries":entries,"blend_files":blend,"topology_qa":"NOT_RUN","license_provenance":"OFFICIAL_SOURCE_REVIEWED_SEPARATELY","art_qa":"NOT_RUN","approved_for_production":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("archive");p.add_argument("--output",required=True);a=p.parse_args()
    try:r=inspect(a.archive)
    except Exception as e:r={"status":"BLOCKED","reason":str(e),"approved_for_production":False}
    out=pathlib.Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(r,indent=2)+"\n")
    print(json.dumps({"status":r["status"],"blend_files":len(r.get("blend_files",[]))}))
    return 0 if r["status"]=="PASS_ARCHIVE_ONLY" else 2
if __name__=="__main__":sys.exit(main())

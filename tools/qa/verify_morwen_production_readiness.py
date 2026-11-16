#!/usr/bin/env python3
"""Fail-closed, read-only Morwen full-3D production preflight. No modeling or render."""
import argparse,hashlib,json,pathlib,sys
REQUIRED={"MORWEN_DESIGN_SHEET_APPROVED_SOURCE.jpg","LAYER0_FRONT.png","LAYER0_BACK.png","LAYER0_PROFILE_FACING_RIGHT.png","LAYER0_PROFILE_FACING_LEFT.png"}
def audit(root):
    root=pathlib.Path(root)
    manifest=json.loads((root/"MANIFEST.json").read_text(encoding="utf-8"))
    rows=manifest.get("files",[])
    seen=set();checks=[]
    for row in rows:
        name=row["filename"]
        if name in seen or pathlib.PurePath(name).name!=name:
            raise ValueError("duplicate or unsafe canonical filename")
        seen.add(name);p=root/name
        result={"file":name,"status":"BLOCKED","expected_sha256":row["sha256"]}
        if p.is_file():
            digest=hashlib.sha256(p.read_bytes()).hexdigest()
            result["actual_sha256"]=digest
            result["status"]="PASS" if digest==row["sha256"] and p.stat().st_size==row["bytes"] else "FAIL"
        checks.append(result)
    missing=sorted(REQUIRED-seen)
    status="PASS" if not missing and len(rows)==5 and all(x["status"]=="PASS" for x in checks) else "BLOCKED"
    return {"status":status,"scope":"canonical_source_integrity_only","files":checks,"missing_manifest_entries":missing,"artistic_qa":"NOT_RUN","topology_qa":"NOT_RUN","render_qa":"NOT_RUN","game_qa":"NOT_RUN","basemesh_approval":"BLOCKED","canonical_promotion":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--root",default="assets/canonical/morwen/2026-11-16");p.add_argument("--output",required=True);a=p.parse_args()
    try:report=audit(a.root)
    except Exception as e:report={"status":"BLOCKED","reason":type(e).__name__+": "+str(e),"canonical_promotion":False}
    dest=pathlib.Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"output":str(dest)}))
    return 0 if report["status"]=="PASS" else 2
if __name__=="__main__":sys.exit(main())

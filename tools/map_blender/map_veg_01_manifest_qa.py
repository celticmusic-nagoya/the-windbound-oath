#!/usr/bin/env python3
"""Non-destructive structural audit of a MAP-VEG-01 candidate manifest.
Does not certify art quality or independently reproduce Blender geometry.
"""
import argparse,hashlib,json,pathlib,sys
def main():
 p=argparse.ArgumentParser();p.add_argument("manifest");p.add_argument("--root");a=p.parse_args()
 path=pathlib.Path(a.manifest);root=pathlib.Path(a.root) if a.root else path.parent
 m=json.loads(path.read_text(encoding="utf-8"))
 errors=[]
 for field in ("task_id","candidate_id","blender_version","seed","assets","outputs"):
  if field not in m:errors.append("missing "+field)
 if m.get("task_id")!="MAP-VEG-01":errors.append("wrong task_id")
 if not isinstance(m.get("assets"),list) or not m.get("assets"):errors.append("assets must be nonempty list")
 if not isinstance(m.get("outputs"),list) or not m.get("outputs"):errors.append("outputs must be nonempty list")
 for entry in m.get("outputs",[]):
  rel=entry.get("path","")
  f=(root/rel).resolve()
  if not rel or not f.is_relative_to(root.resolve()):errors.append("invalid output path "+str(rel));continue
  if not f.is_file():errors.append("missing output "+rel);continue
  sha=hashlib.sha256(f.read_bytes()).hexdigest()
  if sha!=entry.get("sha256"):errors.append("hash mismatch "+rel)
 for item in m.get("assets",[]):
  if not item.get("name"):errors.append("asset missing name")
  if not isinstance(item.get("triangles"),int) or item["triangles"]<=0:errors.append("invalid triangle count")
 result={"status":"FAIL" if errors else "PASS","scope":"manifest and output file integrity only","errors":errors}
 print(json.dumps(result,ensure_ascii=False,indent=2))
 return 1 if errors else 0
if __name__=="__main__":sys.exit(main())

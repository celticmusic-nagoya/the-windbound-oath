#!/usr/bin/env python3
"""Import director-approved Morwen REAL V2 candidate ZIP, without overwriting masters.
Usage: python scripts/import_morwen_real_v2_candidate.py /path/to/MORWEN_REAL_CANON_COLOR_SIZE_V2.zip
Requires Pillow. Exit nonzero on mismatched SHA, unexpected files, or existing candidate files.
"""
from pathlib import Path
import hashlib
import io
import json
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/"assets/candidates/morwen/real-canon-v2"
EXPECTED={
 "front":"16c71079231b1a0f7b960a35d1e5cb1e3abfcd092ad22729924ac74c0bb0bca4",
 "right":"55c5ce7ffaf5380eae56a79bae6fc3ddc50c5f7907a236c59bd4850c443823e1",
 "back":"eb39bcbe0155f0b329e42cec1dc159f24d4758e362ad7a5130c14134020cb02c",
 "left":"a4339f30cc7425521672b720aa226c510ec153c4f669b81deb48466a2dacb7e4",
}
def main():
 from PIL import Image
 if len(sys.argv)!=2:
  print("Usage: python scripts/import_morwen_real_v2_candidate.py ZIP",file=sys.stderr);return 2
 archive=Path(sys.argv[1])
 with zipfile.ZipFile(archive) as z:
  records=[]
  staged=[]
  for direction,digest in EXPECTED.items():
   name=f"morwen_real_{direction}_normalized_v2.png"
   data=z.read(name)
   actual=hashlib.sha256(data).hexdigest()
   if actual!=digest: raise ValueError(f"{name}: SHA-256 mismatch")
   with Image.open(io.BytesIO(data)) as img:
    if img.mode!="RGBA" or img.size!=(1200,1600):
     raise ValueError(f"{name}: expected RGBA 1200x1600")
    alpha=img.getchannel("A")
    if not alpha.getbbox():raise ValueError(f"{name}: empty alpha")
    hist=alpha.histogram()
    if sum(hist[128:])==0:raise ValueError(f"{name}: no visible pixels")
   destination=TARGET/name
   if destination.exists():raise FileExistsError(f"Refusing to overwrite {destination}")
   staged.append((destination,data))
   records.append({"direction":direction,"file":name,"sha256":actual})
  if TARGET.exists() and any(TARGET.iterdir()):
   raise FileExistsError(f"Candidate directory not empty: {TARGET}")
  TARGET.mkdir(parents=True,exist_ok=True)
  for destination,data in staged:destination.write_bytes(data)
  (TARGET/"IMPORT_MANIFEST.json").write_text(json.dumps({"status":"CANDIDATE_NOT_PRODUCTION","files":records},indent=2)+"\n",encoding="utf-8")
  print(json.dumps({"status":"IMPORTED_CANDIDATE","files":records},indent=2))
 return 0
if __name__=="__main__":
 try:raise SystemExit(main())
 except (ValueError,FileExistsError,KeyError,zipfile.BadZipFile) as exc:
  print("FAIL:",exc,file=sys.stderr);raise SystemExit(1)

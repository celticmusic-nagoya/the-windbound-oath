"""Fetch and validate CC0 Poly Haven material maps for CI Blender renders.
The material is an evaluation candidate, not an approved game asset.
"""
import json,os,urllib.request,hashlib
from pathlib import Path
ASSET="red_slate_roof_tiles_01"
root=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview"))/"cc0_materials"/ASSET
root.mkdir(parents=True,exist_ok=True)
api="https://api.polyhaven.com/files/"+ASSET
with urllib.request.urlopen(api,timeout=35) as resp:
 data=json.load(resp)
manifest={"asset":ASSET,"source":"https://polyhaven.com/a/"+ASSET,
          "license":"CC0-1.0","maps":{}}
for kind in ("Diffuse","nor_gl","rough"):
 entry=data.get(kind) or data.get(kind.lower()) or data.get(kind.upper())
 if not entry:
  raise RuntimeError("Missing required PBR map: "+kind)
 variants=entry.get("1k") or entry.get("2k")
 if not variants:
  raise RuntimeError("Missing 1k/2k variant: "+kind)
 choice=variants.get("jpg") or variants.get("png")
 if not choice:
  raise RuntimeError("Missing jpg/png map: "+kind)
 url=choice["url"]
 ext="jpg" if "jpg" in variants and choice==variants["jpg"] else "png"
 target=root/(kind+"."+ext)
 with urllib.request.urlopen(url,timeout=100) as resp:
  payload=resp.read()
 if len(payload)<10000:
  raise RuntimeError("Unexpectedly small map: "+kind)
 sha=hashlib.sha256(payload).hexdigest()
 expected=choice.get("md5")
 if expected and hashlib.md5(payload).hexdigest()!=expected:
  raise RuntimeError("Source checksum mismatch: "+kind)
 target.write_bytes(payload)
 manifest["maps"][kind]={"file":str(target),"sha256":sha,"source_url":url}
(root/"manifest.json").write_text(json.dumps(manifest,indent=2))
print("Poly Haven CC0 PBR maps acquired:",", ".join(manifest["maps"]))

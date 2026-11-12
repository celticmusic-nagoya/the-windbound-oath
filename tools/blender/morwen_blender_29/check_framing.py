"""Validate camera framing and alpha before treating candidate renders as art evidence."""
import json
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parents[3]
source=root/"assets/candidates/morwen-blender-26"
out=root/"assets/candidates/morwen-blender-29"
out.mkdir(parents=True,exist_ok=True)
results={}
for name in ("front","left","right","back","three_quarter"):
    p=source/(name+".png")
    im=Image.open(p).convert("RGBA")
    alpha=im.getchannel("A")
    hist=alpha.histogram()
    transparent=hist[0]/(im.width*im.height)
    results[name]={"width":im.width,"height":im.height,
      "transparent_fraction":round(transparent,6),
      "pass":transparent>=0.15}
result={"task":"MORWEN-BLENDER-29","checks":results,
        "art_qa":"BLOCKED" if not all(v["pass"] for v in results.values()) else "NOT_RUN"}
(out/"camera_diagnostics.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result))
if result["art_qa"]=="BLOCKED":raise SystemExit("Camera framing/alpha QA FAIL")

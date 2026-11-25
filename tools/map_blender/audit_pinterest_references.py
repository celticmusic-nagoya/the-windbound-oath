"""Optional Pinterest API read-only audit. Never downloads Pinterest imagery.
Requires PINTEREST_ACCESS_TOKEN stored as GitHub Actions secret.
"""
import json,os,urllib.request,urllib.error
from pathlib import Path
selection=json.loads(Path("tools/map_blender/pinterest_roof_reference_selection.json").read_text())
token=os.environ.get("PINTEREST_ACCESS_TOKEN","")
if not token:
 print("Pinterest live audit: SKIPPED (no Actions secret); curated references remain available")
 raise SystemExit(0)
board=selection["board_id"]
url="https://api.pinterest.com/v5/boards/"+board+"/pins?page_size=100"
found=set()
for page in range(10):
 request=urllib.request.Request(url,headers={"Authorization":"Bearer "+token,"Accept":"application/json"})
 with urllib.request.urlopen(request,timeout=25) as response:
  data=json.load(response)
 for pin in data.get("items",[]):
  found.add(str(pin["id"]))
 bookmark=data.get("bookmark")
 if not bookmark:break
 from urllib.parse import urlencode
 url="https://api.pinterest.com/v5/boards/"+board+"/pins?"+urlencode({"page_size":100,"bookmark":bookmark})
selected={x["pin"].rstrip("/").split("/")[-1] for x in selection["selected"]}
# Saved pins can have a board-specific ID; record coverage rather than mutating source selection.
report={"board_id":board,"selected_count":len(selected),"board_pin_count":len(found),
        "matched_count":len(selected&found),"unmatched":sorted(selected-found),
        "status":"AUDITED","note":"References only, no image download"}
out=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview"))
out.mkdir(parents=True,exist_ok=True)
(out/"pinterest_reference_audit.json").write_text(json.dumps(report,indent=2))
print("Pinterest live read-only audit:",report["matched_count"],"/",len(selected))

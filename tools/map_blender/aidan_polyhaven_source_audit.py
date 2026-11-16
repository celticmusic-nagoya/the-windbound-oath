"""Fetch and validate Poly Haven CC0 source asset metadata without modifying game assets.
Only download if an explicit supported 3D model URL exists in publisher API.
"""
import hashlib,json,os,pathlib,urllib.request,urllib.parse,sys
ASSET="rock_moss_set_01"
ROOT=pathlib.Path(os.environ.get("AIDAN_SOURCE_OUT","/tmp/aidan-source"))
ROOT.mkdir(parents=True,exist_ok=True)
API=f"https://api.polyhaven.com/files/{ASSET}"
record={"asset":ASSET,"publisher":"Poly Haven","publisher_page":f"https://polyhaven.com/a/{ASSET}",
        "license_page":"https://polyhaven.com/license","source_api":API,
        "status":"BLOCKED","model_sha256":None,"files":[]}
def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"TWO-Aidan-CC0-SourceAudit/1.0"})
    with urllib.request.urlopen(req,timeout=40) as response:return response.read()
try:
    data=json.loads(fetch(API))
    (ROOT/"publisher_files.json").write_text(json.dumps(data,indent=2))
    # Poly Haven API model files are grouped by format and resolution; select
    # a glTF/GLB/FBX/OBJ model only, never accidentally download a texture map.
    candidates=[]
    def visit(node,path=()):
        if isinstance(node,dict):
            if isinstance(node.get("url"),str):
                url=node["url"]
                ext=urllib.parse.urlparse(url).path.lower()
                if ext.endswith((".glb",".gltf",".fbx",".obj",".blend",".zip")):
                    candidates.append((path,url,node))
            for k,v in node.items():visit(v,path+(str(k),))
        elif isinstance(node,list):
            for i,v in enumerate(node):visit(v,path+(str(i),))
    visit(data)
    # Prioritize GLB, then BLEND, then FBX/OBJ; smallest size when known.
    rank={".glb":0,".blend":1,".fbx":2,".obj":3,".gltf":4,".zip":5}
    def order(item):
        ext=pathlib.PurePosixPath(urllib.parse.urlparse(item[1]).path).suffix.lower()
        return rank.get(ext,9),int(item[2].get("size",999999999)) if isinstance(item[2].get("size"),int) else 999999999
    candidates.sort(key=order)
    record["candidate_count"]=len(candidates)
    record["candidate_paths"]=["/".join(p) for p,_,_ in candidates[:20]]
    if not candidates:raise RuntimeError("Publisher API returned no supported model download URL")
    path,url,meta=candidates[0]
    raw=fetch(url)
    if len(raw)<1024:raise RuntimeError("Source download too small")
    name=pathlib.PurePosixPath(urllib.parse.urlparse(url).path).name
    if not name or len(name)>100:name="polyhaven_source_model.bin"
    (ROOT/name).write_bytes(raw)
    sha=hashlib.sha256(raw).hexdigest()
    record.update(status="SOURCE_DOWNLOADED_UNVERIFIED_IMPORT",selected_path="/".join(path),
                  model_sha256=sha,model_bytes=len(raw),filename=name)
    record["files"].append({"name":name,"sha256":sha,"bytes":len(raw)})
except Exception as e:
    record["error"]=str(e)
finally:
    (ROOT/"source_audit.json").write_text(json.dumps(record,indent=2))
    print("AIDAN_SOURCE_AUDIT="+json.dumps(record))
# Fail visibly while retaining evidence, never mark an unavailable source PASS.
if record["status"]=="BLOCKED":sys.exit(2)

"""Fetch licensed Poly Haven rock models with immutable provenance and SHA.
Separate study inputs, never replace official source assets.
"""
import argparse,hashlib,json,urllib.request,urllib.parse,pathlib,datetime,posixpath
API="https://api.polyhaven.com/files/"
IDS=("rock_face_01","boulder_01")
def fetch_json(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"TWO-asset-provenance/1.0"}),timeout=35) as r:
  return json.load(r)
def download(url,dest,max_bytes):
 req=urllib.request.Request(url,headers={"User-Agent":"TWO-asset-provenance/1.0"})
 h=hashlib.sha256();size=0
 with urllib.request.urlopen(req,timeout=90) as r,open(dest,"wb") as f:
  while True:
   data=r.read(1024*1024)
   if not data:break
   size+=len(data)
   if size>max_bytes:raise ValueError("Asset exceeds download budget")
   h.update(data);f.write(data)
 return size,h.hexdigest()
def choose(tree):
 candidates=[]
 def walk(node,path=()):
  if isinstance(node,dict):
   if isinstance(node.get("url"),str) and node["url"].startswith("https://"):
    u=node["url"];parts=urllib.parse.urlsplit(u).path.lower()
    if parts.endswith((".glb",".gltf",".blend",".zip")):
     fmt=next((x for x in (".glb",".gltf",".blend",".zip") if parts.endswith(x)),"")
     score=(0 if fmt==".glb" else 1 if fmt==".gltf" else 2 if fmt==".blend" else 3,
            0 if any("1k" in str(k).lower() for k in path) else 1 if any("2k" in str(k).lower() for k in path) else 2,
            len(path))
     candidates.append((score,u,path,node))
   for k,v in node.items():walk(v,path+(k,))
  elif isinstance(node,list):
   for i,v in enumerate(node):walk(v,path+(i,))
 walk(tree)
 if not candidates:return None
 return sorted(candidates,key=lambda x:x[0])[0]
def main():
 p=argparse.ArgumentParser();p.add_argument("--out",required=True);p.add_argument("--max-mb",type=int,default=100);a=p.parse_args()
 out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
 result={"source":"Poly Haven public asset API","license":"CC0 per https://polyhaven.com/license","assets":[],"generated_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
 for ident in IDS:
  item={"id":ident,"asset_page":"https://polyhaven.com/a/"+ident,"status":"NOT_DOWNLOADED"}
  try:
   metadata=fetch_json(API+ident);selected=choose(metadata)
   if not selected:raise ValueError("No supported downloadable model in API response")
   _,url,path,entry=selected
   ext=pathlib.PurePosixPath(urllib.parse.urlsplit(url).path).suffix.lower()
   dest=out/(ident+ext)
   size,digest=download(url,dest,a.max_mb*1024*1024)
   dependencies=[]
   if ext==".gltf":
    model=json.loads(dest.read_text())
    uris=[x["uri"] for group in ("buffers","images") for x in model.get(group,[]) if "uri" in x and not x["uri"].startswith("data:")]
    for uri in sorted(set(uris)):
     parsed=urllib.parse.urlsplit(uri)
     if parsed.scheme or parsed.netloc or uri.startswith("/") or ".." in pathlib.PurePosixPath(parsed.path).parts:raise ValueError("Unsafe glTF dependency URI: "+uri)
     dependency=out/ident/parsed.path
     dependency.parent.mkdir(parents=True,exist_ok=True)
     dep_url=urllib.parse.urljoin(url,uri)
     dep_size,dep_sha=download(dep_url,dependency,a.max_mb*1024*1024)
     dependencies.append({"uri":uri,"file":str(dependency.relative_to(out)),"size_bytes":dep_size,"sha256":dep_sha,"source_url":dep_url})
    # glTF expects dependencies relative to its own directory; put the JSON there too.
    relocated=out/ident/dest.name
    relocated.write_bytes(dest.read_bytes());dest.unlink();dest=relocated
   item.update({"dependencies":dependencies,"status":"DOWNLOADED_UNREVIEWED","file":str(dest.relative_to(out)),"size_bytes":size,"sha256":digest,"api_path":list(map(str,path)),"source_url":url,"declared_api_hash":entry.get("md5"),"license":"CC0","geometry_qa":"NOT_RUN","art_qa":"NOT_RUN"})
  except Exception as e:
   item["status"]="BLOCKED";item["error"]=str(e)
  result["assets"].append(item)
 (out/"source_provenance.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"assets":[{"id":i["id"],"status":i["status"],"size":i.get("size_bytes")} for i in result["assets"]]}))
 assert all(i["status"]=="DOWNLOADED_UNREVIEWED" for i in result["assets"]),"At least one source download failed; review provenance"
if __name__=="__main__":main()

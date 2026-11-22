"""Retain verified gallery copies independently of source artifact expiration."""
import hashlib,json,pathlib,shutil,sys,re
from datetime import datetime,timezone
from retention import select
def merge(old,new,out):
    records=[]
    for root in (old,new):
        f=root/"gallery-manifest.json"
        if not f.exists():continue
        for e in json.loads(f.read_text())["entries"]:
            if not re.fullmatch(r"[a-f0-9]{64}",e["sha256"]) or not re.fullmatch(r"published/"+e["sha256"]+r"\.(png|jpg|jpeg|glb|vrm)",e["path"]):raise ValueError("unsafe manifest")
            p=root/e["path"]
            if not p.is_file() or p.is_symlink() or not 0<e["bytes"]<=64*1024*1024 or p.stat().st_size!=e["bytes"]:raise ValueError("invalid copy")
            with p.open("rb") as stream:
                if hashlib.file_digest(stream,"sha256").hexdigest()!=e["sha256"]:raise ValueError("invalid hash")
            records.append((e,p))
    policy=json.loads(pathlib.Path(__file__).with_name("retention-policy.json").read_text())
    result=select([e for e,p in records],datetime.now(timezone.utc),policy["soft_gallery_budget_bytes"],policy["recent_days"])
    sources={e["path"]:p for e,p in records}
    out.mkdir(parents=True,exist_ok=True)
    for e in result["entries"]:
        dest=out/e["path"];dest.parent.mkdir(exist_ok=True);shutil.copyfile(sources[e["path"]],dest)
    (out/"gallery-manifest.json").write_text(json.dumps({"version":1,"entries":result["entries"]},ensure_ascii=False,indent=2)+"\n")
    print("retained",len(result["entries"]),result["bytes"],"bytes")
if __name__=="__main__":merge(*map(pathlib.Path,sys.argv[1:]))

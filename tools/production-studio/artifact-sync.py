"""Stage explicitly selected entries from downloaded production ZIPs; no publishing."""
import argparse, hashlib, json, pathlib, re, zipfile
MAX_FILE = 64 * 1024 * 1024
MAX_TOTAL = 256 * 1024 * 1024
def stage(spec, source, dest):
    dest.mkdir(parents=True, exist_ok=True)
    records, total = [], 0
    for item in spec:
        run, artifact = item["run_id"], item["artifact_id"]
        if type(run) is not int or type(artifact) is not int or min(run, artifact)<1:
            raise ValueError("invalid provenance ID")
        head = item["head"]
        if not re.fullmatch(r"[0-9a-f]{40}", head):
            raise ValueError("invalid source commit")
        archive = source / f"{artifact}.zip"
        with zipfile.ZipFile(archive) as z:
            for name in item["entries"]:
                p = pathlib.PurePosixPath(name)
                ext = p.suffix.lower()
                if p.is_absolute() or ".." in p.parts or "\\" in name or ext not in {".png",".jpg",".jpeg",".glb",".vrm"}:
                    raise ValueError("entry not permitted")
                info = z.getinfo(name)
                if info.file_size > MAX_FILE or total + info.file_size > MAX_TOTAL:
                    raise ValueError("size budget")
                if info.is_dir() or info.flag_bits & 1:
                    raise ValueError("unsupported entry")
                with z.open(info) as f:
                    data = f.read(MAX_FILE+1)
                if len(data) != info.file_size:
                    raise ValueError("size mismatch")
                if ext == ".png" and not data.startswith(b"\x89PNG\r\n\x1a\n"):
                    raise ValueError("PNG signature")
                if ext in {".jpg",".jpeg"} and not data.startswith(b"\xff\xd8\xff"):
                    raise ValueError("JPEG signature")
                if ext in {".glb",".vrm"}:
                    if len(data)<20 or data[:4]!=b"glTF" or int.from_bytes(data[4:8],"little")!=2 or int.from_bytes(data[8:12],"little")!=len(data):
                        raise ValueError("GLB header")
                    n=int.from_bytes(data[12:16],"little")
                    if n>8*1024*1024 or n+20>len(data) or data[16:20]!=b"JSON":
                        raise ValueError("GLB JSON chunk")
                    meta=json.loads(data[20:20+n])
                    if any("uri" in x for k in ("buffers","images") for x in meta.get(k,[])):
                        raise ValueError("external model resources")
                digest=hashlib.sha256(data).hexdigest()
                filename=digest+ext
                (dest/filename).write_bytes(data)
                total+=len(data)
                records.append(dict(name=name,path="published/"+filename,sha256=digest,bytes=len(data),run_id=run,artifact_id=artifact,head=head,qa="NOT_RUN",adoption="UNDETERMINED"))
    (dest.parent/"gallery-manifest.json").write_text(json.dumps({"version":1,"entries":records},ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("spec",type=pathlib.Path)
    p.add_argument("source",type=pathlib.Path)
    p.add_argument("dest",type=pathlib.Path)
    a=p.parse_args()
    stage(json.loads(a.spec.read_text()),a.source,a.dest)

"""Local immutable native checkpoint publication; remote durability is separate."""
import hashlib, json, os, re, shutil, tempfile, zipfile
from pathlib import Path

def digest(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def publish(source, reopened, root, stage, fingerprint):
    if not re.fullmatch(r'[A-Za-z0-9_-]+',stage) or not re.fullmatch(r'[0-9a-f]{64}',fingerprint): raise ValueError('invalid identity')
    source,reopened,root=map(Path,(source,reopened,root))
    with zipfile.ZipFile(source) as z:
        if z.testzip() is not None or 'v1model/data.bin' not in z.namelist(): raise ValueError('invalid native file')
    h=digest(source)
    if digest(reopened)!=h: raise ValueError('reopened bytes mismatch')
    root.mkdir(parents=True,exist_ok=True)
    dest=root/(stage+'-'+h)
    temp=Path(tempfile.mkdtemp(dir=root))
    try:
        shutil.copyfile(source,temp/'model.vroid')
        if digest(temp/'model.vroid')!=h: raise ValueError('copy mismatch')
        manifest=dict(stage=stage,sha256=h,fingerprint=fingerprint,path=str(dest/'model.vroid'),reopened_bytes_match=True,remote_verified=False)
        (temp/'manifest.json').write_text(json.dumps(manifest,sort_keys=True))
        os.rename(temp,dest)
        return manifest
    finally:
        if temp.exists(): shutil.rmtree(temp)

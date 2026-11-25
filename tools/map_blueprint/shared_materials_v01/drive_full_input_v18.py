"""Read-only, fail-closed transfer of exact approved V15C ZIP. No credential logging."""
import argparse, hashlib, os, re, tempfile, urllib.request, zipfile
from pathlib import Path
ARCHIVE_SHA='ab35c88f7cf53781edf0dd2aec2e75074adb7308abb5b0f40fc1e565c64a7dca'
ARCHIVE_BYTES=45872066
GLB_SHA='09366ffaf5b1f6657b1b9ca158c9681d0d52537a4a90bf94f7ac25ec6f2162f1'
GLB_BYTES=47420560
NAMES={'a3_forest_v15c.glb','import_v15c.py','preflight.json','README.txt'}
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ValueError('Unexpected redirect; refuse to forward token')
def copy_exact(stream,dst,size,digest):
    h=hashlib.sha256();n=0
    with dst.open('xb') as f:
        while True:
            b=stream.read(1024*1024)
            if not b:break
            n+=len(b)
            if n>size:raise ValueError('Byte limit exceeded')
            h.update(b);f.write(b)
    if n!=size or h.hexdigest()!=digest:raise ValueError('Exact-byte lock mismatch')
def extract(archive,dst):
    with zipfile.ZipFile(archive) as z:
        names=z.namelist()
        if len(names)!=len(NAMES) or set(names)!=NAMES or z.testzip() is not None:raise ValueError('Unexpected archive inventory or CRC')
        if z.getinfo('a3_forest_v15c.glb').file_size!=GLB_BYTES:raise ValueError('GLB size mismatch')
        with z.open('a3_forest_v15c.glb') as f:copy_exact(f,dst,GLB_BYTES,GLB_SHA)
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);p.add_argument('--local-archive',type=Path);a=p.parse_args()
    if a.out.exists():raise SystemExit('Refuse overwrite')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=a.out.parent) as tmp:
        archive=Path(tmp)/'input.zip';glb=Path(tmp)/'input.glb'
        if a.local_archive:
            with a.local_archive.open('rb') as f:copy_exact(f,archive,ARCHIVE_BYTES,ARCHIVE_SHA)
        else:
            token=os.environ.get('TWO_DRIVE_ACCESS_TOKEN','');fid=os.environ.get('TWO_DRIVE_FILE_ID','')
            if not token or not re.fullmatch(r'[A-Za-z0-9_-]{10,150}',fid):raise SystemExit('AUTH_CONFIG_MISSING')
            req=urllib.request.Request('https://www.googleapis.com/drive/v3/files/'+fid+'?alt=media',headers={'Authorization':'Bearer '+token})
            try:
                with urllib.request.build_opener(NoRedirect()).open(req,timeout=60) as f:copy_exact(f,archive,ARCHIVE_BYTES,ARCHIVE_SHA)
            except Exception as e:raise SystemExit('DRIVE_READ_FAILED: '+type(e).__name__) from None
        extract(archive,glb)
        os.link(glb,a.out)
    print('V15C_ARCHIVE_AND_GLB_EXACT_SHA_PASS')
if __name__=='__main__':main()

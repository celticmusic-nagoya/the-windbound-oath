"""Read-only candidate intake; no production adoption or scene edits."""
import argparse, hashlib, io, json, os, re, tempfile, urllib.parse, urllib.request, zipfile
from pathlib import Path, PurePosixPath

ROCK_ZIP_SHA = 'e19efb710e8e4ac19ba1e11ffaeb2764aca3b9a547b19058f52fafc42cec71c0'
HOSTS = {'dl.polyhaven.org','ambientcg.com','download.ambientcg.com'}
MAX_FILE = 100 * 1024 * 1024

def digest(b): return hashlib.sha256(b).hexdigest()

def safe_rel(s):
    p=PurePosixPath(s)
    if not s or p.is_absolute() or '\\' in s or any(x in ('..','.') for x in s.split('/')) or ':' in s or not p.name:
        raise ValueError('unsafe path: '+s)
    return p

def validate_row(r):
    safe_rel(r['path'])
    if not re.fullmatch('[0-9a-f]{64}',r['sha256']): raise ValueError('missing SHA256')
    if type(r['bytes']) is not int or not 0 < r['bytes'] <= MAX_FILE: raise ValueError('size outside limit')
    u=urllib.parse.urlsplit(r['url'])
    if u.scheme!='https' or u.hostname not in HOSTS or u.username or u.password or u.port not in (None,443): raise ValueError('source not allowlisted')

def validate_data(r,b):
    validate_row(r)
    if len(b)!=r['bytes'] or digest(b)!=r['sha256']: raise ValueError('pinned bytes mismatch: '+r['path'])
    if r.get('provider_md5') and hashlib.md5(b).hexdigest()!=r['provider_md5']: raise ValueError('provider MD5 mismatch')

def store(root,r,b):
    validate_data(r,b)
    root=Path(root).resolve(); root.mkdir(parents=True,exist_ok=True)
    # Reject symlink ancestors; do not replace a corrupt or different cache file.
    p=root/safe_rel(r['path'])
    if any(q.is_symlink() for q in [p,*p.parents] if q!=root): raise ValueError('symlink path')
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():
        validate_data(r,p.read_bytes()); return 'CACHE_REUSED'
    with tempfile.NamedTemporaryFile(dir=p.parent,delete=False) as f:
        tmp=Path(f.name);f.write(b)
    try:
        os.link(tmp,p) # atomic create, no overwrite
    finally: tmp.unlink(missing_ok=True)
    return 'IMPORTED'

def rock_rows(z):
    prov=json.loads(z.read('source_provenance.json'))
    result=[]
    for a in prov['assets']:
        if a['license']!='CC0': raise ValueError('license not CC0')
        for m in [a,*a['dependencies']]:
            result.append(dict(asset=a['id'],path=m['file'],url=m['source_url'],bytes=m['size_bytes'],sha256=m['sha256']))
    if len(result)!=10 or len({r['path'] for r in result})!=10: raise ValueError('unexpected inventory')
    return result

def import_rock(archive,root):
    raw=Path(archive).read_bytes()
    if digest(raw)!=ROCK_ZIP_SHA: raise ValueError('archive SHA mismatch')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if len(z.namelist())!=len(set(z.namelist())): raise ValueError('duplicate archive members')
        rows=rock_rows(z)
        # Verify all before writing any.
        for r in rows:
            if z.getinfo(r['path']).file_size!=r['bytes']: raise ValueError('member size mismatch')
            validate_data(r,z.read(r['path']))
        return [dict(r,status=store(root,r,z.read(r['path']))) for r in rows]

class PinnedRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        u=urllib.parse.urlsplit(newurl)
        if u.scheme!='https' or u.hostname not in HOSTS or u.username or u.password or u.port not in (None,443): raise ValueError('redirect rejected')
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def fetch_rows(rows,root):
    for r in rows: validate_row(r)
    if len({r['path'] for r in rows})!=len(rows): raise ValueError('duplicate paths')
    result=[]; opener=urllib.request.build_opener(PinnedRedirect())
    for r in rows:
        p=Path(root)/safe_rel(r['path'])
        try:
            if p.exists(): status=store(root,r,p.read_bytes())
            else:
                with opener.open(urllib.request.Request(r['url'],headers={'User-Agent':'TWO-material-cache/1.0'}),timeout=30) as f: b=f.read(r['bytes']+1)
                status=store(root,r,b)
            result.append(dict(r,status=status))
        except Exception as exc:
            result.append(dict(r,status='ERROR',error=f'{type(exc).__name__}: {exc}'))
            # No repeated attempts on the same network/integrity error.
            break
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--report',required=True)
    group=p.add_mutually_exclusive_group(required=True);group.add_argument('--rock-archive');group.add_argument('--catalog')
    p.add_argument('--asset',action='append',default=[]);a=p.parse_args()
    if a.rock_archive: rows=import_rock(a.rock_archive,a.out)
    else:
        q=json.loads(Path(a.catalog).read_text()); selected=set(a.asset)
        if not selected: raise SystemExit('explicit asset list required')
        rows=[r for r in q['locked_files'] if r['asset'] in selected]
        if selected!={r['asset'] for r in rows}: raise SystemExit('unknown/unlocked asset selection')
        rows=fetch_rows(rows,a.out)
    Path(a.report).write_text(json.dumps({'files':rows,'complete':all(r['status']!='ERROR' for r in rows)},indent=2)+'\n')
    return int(any(r['status']=='ERROR' for r in rows))
if __name__=='__main__': raise SystemExit(main())

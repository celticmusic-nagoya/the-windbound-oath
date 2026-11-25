"""Bounded, candidate-only provider metadata intake. No source execution."""
import hashlib, json, re, sys, urllib.request, urllib.parse
from pathlib import Path
from material_cache import safe_rel, store, PinnedRedirect

OUT=Path(sys.argv[1])
REPORT=Path(sys.argv[2])
OP=urllib.request.build_opener(PinnedRedirect())
ROWS=[]
MAX=64*1024*1024
total=0

def get(url, host, cap):
    u=urllib.parse.urlsplit(url)
    if u.scheme!='https' or u.hostname!=host or u.username or u.password or u.port not in (None,443):
        raise ValueError('unexpected source URL')
    with OP.open(urllib.request.Request(url,headers={'User-Agent':'TWO-material-candidate/1.0'}),timeout=40) as f:
        b=f.read(cap+1)
    if len(b)>cap: raise ValueError('size cap')
    return b

def acquire(asset, rel, rec):
    global total
    path=str(safe_rel(asset+'/'+rel))
    n=rec['size']; md5=rec['md5']
    if type(n) is not int or not 0<n<=MAX or total+n>MAX or not re.fullmatch('[0-9a-f]{32}',md5):
        raise ValueError('missing/invalid provider lock or aggregate size cap')
    b=get(rec['url'],'dl.polyhaven.org',n)
    if len(b)!=n or hashlib.md5(b).hexdigest()!=md5: raise ValueError('provider size/md5 mismatch')
    row=dict(asset=asset,path=path,url=rec['url'],bytes=n,provider_md5=md5,sha256=hashlib.sha256(b).hexdigest())
    row['status']=store(OUT,row,b);ROWS.append(row);total+=n
    return b

def metadata(asset):
    b=get('https://api.polyhaven.com/files/'+asset,'api.polyhaven.com',4*1024*1024)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/(asset+'_provider_files.json')).write_bytes(b)
    return json.loads(b)

errors=[]
for asset in ('fern_02','jolcham_oak_bark_01'):
    try:
        q=metadata(asset)
        if asset=='fern_02':
            rec=q['gltf']['1k']['gltf']
            name=Path(urllib.parse.urlsplit(rec['url']).path).name
            b=acquire(asset,name,rec)
            g=json.loads(b)
            deps={x['uri'] for key in ('buffers','images') for x in g.get(key,[]) if 'uri' in x}
            inc=rec['include']
            if deps!=set(inc) or not 1<=len(deps)<=10: raise ValueError('unexpected glTF dependency set')
            for name in sorted(deps):
                safe_rel(name);acquire(asset,name,inc[name])
        else:
            for key in ('Diffuse','nor_gl','arm'):
                rec=q[key]['2k']['jpg']
                name=Path(urllib.parse.urlsplit(rec['url']).path).name
                acquire(asset,name,rec)
    except Exception as e:
        errors.append(dict(asset=asset,error=type(e).__name__+': '+str(e)))
REPORT.write_text(json.dumps(dict(status='CANDIDATE_ONLY',source_license='CC0 (asset pages verified separately)',files=ROWS,errors=errors,total_bytes=total),indent=2)+'\n')
print(REPORT.read_text())
raise SystemExit(bool(errors))

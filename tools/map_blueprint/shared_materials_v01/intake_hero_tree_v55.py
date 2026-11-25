"""Bounded, candidate-only provider metadata intake. No source execution."""
import hashlib, json, re, sys, urllib.request, urllib.parse
from pathlib import Path
from material_cache import safe_rel, store, PinnedRedirect

OUT=Path(sys.argv[1])
REPORT=Path(sys.argv[2])
OP=urllib.request.build_opener(PinnedRedirect())
ROWS=[]
MAX=256*1024*1024
total=0

def get(url, host, cap):
    u=urllib.parse.urlsplit(url)
    if u.scheme!='https' or u.hostname!=host or u.username or u.password or u.port not in (None,443):
        raise ValueError('unexpected source URL')
    with OP.open(urllib.request.Request(url,headers={'User-Agent':'TWO-material-candidate/1.0'}),timeout=90) as f:
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

# Candidate only: a coastal scan, not a canon oak. Preflight complete dependency size before download.
asset='island_tree_01'
errors=[]
try:
    q=metadata(asset)
    rec=q['gltf']['1k']['gltf']
    inc=rec['include']
    locks=[rec]+list(inc.values())
    assert 1<=len(inc)<=32 and all(type(x['size']) is int and x['size']>0 and re.fullmatch('[0-9a-f]{32}',x['md5']) for x in locks)
    assert sum(x['size'] for x in locks)<=MAX, 'provider dependency budget exceeded'
    name=Path(urllib.parse.urlsplit(rec['url']).path).name
    b=acquire(asset,name,rec); g=json.loads(b)
    deps={x['uri'] for k in ('buffers','images') for x in g.get(k,[]) if 'uri' in x}
    assert deps==set(inc), 'provider dependency set mismatch'
    for name in sorted(deps):
        safe_rel(name);acquire(asset,name,inc[name])
    # The external alpha is required when the source basecolor is JPEG.
    # Recover original PNG if a leaf alpha entry is published; do not infer alpha from RGB.
    key=next((k for k in q if re.sub('[^a-z]','',k.lower())=='leavesalpha'),None)
    if key:
        alpha=q[key]['1k'].get('png')
        if alpha:
            name=Path(urllib.parse.urlsplit(alpha['url']).path).name
            acquire(asset,'separate_alpha/'+name,alpha)
    # Metadata-only structure accounting; native import and visual QA later.
    counts=[]
    for m in g.get('meshes',[]):
        for p in m['primitives']:
            mode=p.get('mode',4)
            count=g['accessors'][p.get('indices',p['attributes']['POSITION'])]['count']
            counts.append(dict(mesh=m.get('name'),mode=mode,index_or_vertex_count=count,triangles=count//3 if mode==4 else None))
    (OUT/'structure.json').write_text(json.dumps(dict(meshes=len(g.get('meshes',[])),nodes=len(g.get('nodes',[])),materials=g.get('materials',[]),primitives=counts),indent=2)+'\n')
except Exception as e:
    errors.append(dict(asset=asset,error=type(e).__name__+': '+str(e)))
REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text(json.dumps(dict(status='CANDIDATE_ONLY',source_license='CC0, Poly Haven asset page',files=ROWS,errors=errors,total_bytes=total),indent=2)+'\n')
print(REPORT.read_text())
raise SystemExit(bool(errors))

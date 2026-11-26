"""Use the historical actual M01 archive only as an offline transfer fixture."""
import io
import json
import pathlib
import sys
import tempfile
import zipfile
from pack_transfer import pack
from receive_morwen_transfer import *

raw_archive = pathlib.Path(sys.argv[1]).read_bytes()
assert sha(raw_archive) == 'b50af5d27651c574f5ce30ec7b60bae19cb6fa4640caa7685bb7bbf1e190dde9'
with zipfile.ZipFile(io.BytesIO(raw_archive)) as z, tempfile.TemporaryDirectory() as td:
    assert z.testzip() is None
    root = pathlib.Path(td)
    native = sha(z.read('model.vroid'))
    vrm = z.read('model.vrm')
    assert sha(vrm) == '85d6a94c3d6877cf32b9ea7e7f1fb5ee697f5642028fa7f8f67b3f7d77bca039'
    (root/'Morwen-transfer.vrm').write_bytes(vrm)
    (root/'views').mkdir()
    views = {}
    for name, filename in zip(('front','left4','left8','right4'), ('export-menu.png','vrm-options.png','vrm-metadata.png','vrm-permissions.png')):
        data = z.read(filename)
        (root/'views'/f'{name}.png').write_bytes(data)
        views[name] = sha(data)
    (root/'transfer-receipt.json').write_text(json.dumps(dict(scope='PRIVATE_TRANSFER_CANDIDATE_REVIEW_REQUIRED', native_sha256=native, vrm_structure={'version':'1.0'}, vrm_sha256=sha(vrm), capture_sha256=views)))
    out = root/'package.zip'
    pack(root,out,expected_source=native)
    raw = out.read_bytes()
digest = sha(raw)
revision = 'b'*40
class API:
    def __init__(self, mode='ok'): self.mode=mode; self.calls=[]
    def __call__(self, token, method, url, **kwargs):
        assert token == 'fixture-only' and method == 'GET'
        self.calls.append(url)
        if url == BASE: return {'full_name':DEST,'private':self.mode!='public'}
        if url == BASE+'/releases/tags/morwen-transfer-run-42':
            notes=f'Private candidate, NOT_ADOPTED. Run 42; request 99; source revision {revision}; ZIP SHA256 {digest}.'
            return dict(id=10,tag_name='morwen-transfer-run-42',draft=self.mode=='draft',prerelease=True,body=notes if self.mode!='wrong_request' else notes.replace('request 99','request 98'),assets=[] if self.mode=='missing' else [dict(id=11,name='Morwen-transfer.zip',state='uploaded',size=len(raw),digest='sha256:'+('0'*64 if self.mode=='digest' else digest))])
        assert url == BASE+'/releases/assets/11' and kwargs==dict(binary=True,limit=len(raw))
        return raw[:-1] if self.mode=='truncated' else raw

def invoke(api, source=native, d=digest): return receive(api,'fixture-only','42','99',revision,d,expected_source=source)
a=API(); data, receipt=invoke(a); assert data==vrm and receipt['vrm_sha256']==sha(vrm) and len(a.calls)==3
cases=['exact actual VRM bytes']
for mode in ('public','draft','wrong_request','missing','digest','truncated'):
    a=API(mode)
    try: invoke(a)
    except ValueError: pass
    else: raise AssertionError(mode)
    if mode!='truncated': assert len(a.calls)<3
    cases.append(mode+' rejected')
for name, source, d in [('wrong native',SOURCE,digest),('wrong producer digest',native,'0'*64),('invalid digest',native,'bad')]:
    a=API()
    try: invoke(a,source,d)
    except ValueError: pass
    else: raise AssertionError(name)
    cases.append(name+' rejected')
print(f'{len(cases)}/{len(cases)} PASS',*cases,sep='\n')

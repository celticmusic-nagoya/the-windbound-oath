"""Offline regression using an authenticated historical archive; no network or uploads.
Usage: python test_transfer_private_release.py /path/to/artifact-14627107999.zip
Historical screenshots are packaging fixtures, not angle QA.
"""
import sys, json, zipfile, tempfile, pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent/'private-preservation'))
from pack_transfer import pack
from transfer_private_release import transfer, package, DEST, BASE, sha
from release_transport import TransportError
if len(sys.argv)!=2: raise SystemExit('require authenticated historical archive')
zpath=sys.argv[1]
assert sha(pathlib.Path(zpath).read_bytes())=='b50af5d27651c574f5ce30ec7b60bae19cb6fa4640caa7685bb7bbf1e190dde9'
with zipfile.ZipFile(zpath) as z:
    assert z.testzip() is None
    raw=z.read('model.vrm'); source=sha(z.read('model.vroid'))
    assert sha(raw)=='85d6a94c3d6877cf32b9ea7e7f1fb5ee697f5642028fa7f8f67b3f7d77bca039'
    with tempfile.TemporaryDirectory() as td:
        root=pathlib.Path(td); (root/'views').mkdir(); (root/'Morwen-transfer.vrm').write_bytes(raw)
        files=['export-menu.png','vrm-options.png','vrm-metadata.png','vrm-permissions.png']
        captures={}
        for view,file in zip(('front','left4','left8','right4'),files):
            data=z.read(file); (root/'views'/f'{view}.png').write_bytes(data); captures[view]=sha(data)
        (root/'transfer-receipt.json').write_text(json.dumps(dict(scope='PRIVATE_TRANSFER_CANDIDATE_REVIEW_REQUIRED',native_sha256=source,vrm_structure={'version':'1.0'},vrm_sha256=sha(raw),capture_sha256=captures)))
        target=root/'Morwen-transfer.zip'; pack(root,target,expected_source=source); blob=target.read_bytes()
class API:
    def __init__(self,mode='ok'): self.mode=mode; self.calls=[]; self.raw=None; self.reads=0
    def __call__(self,token,method,url,body=None,content_type='application/json',binary=False,limit=None):
        self.calls.append((method,url)); assert token=='fixture-only'
        if method=='GET' and url==BASE:return {'full_name':DEST,'private':self.mode!='public'}
        if method=='GET' and url==BASE+'/git/ref/heads/main':return {'ref':'refs/heads/main','object':{'type':'commit','sha':'a'*40}}
        if method=='GET' and '/releases?per_page=' in url:return [{'tag_name':'morwen-transfer-run-42','draft':True}] if self.mode=='draft_exists' else []
        if method=='GET' and ('/tags/' in url):
            if self.mode=='exists':return {'id':5}
            raise TransportError(403 if self.mode=='forbidden' else 404)
        if method=='POST' and url==BASE+'/releases':
            assert json.loads(body)['draft']; return {'id':10,'tag_name':'morwen-transfer-run-42','draft':True}
        if method=='POST' and 'uploads.github.com' in url:
            self.raw=body; return {'id':11,'name':'Morwen-transfer.zip','state':'uploaded','size':len(body),'digest':'sha256:'+('0'*64 if self.mode=='bad_asset' else sha(body))}
        if method=='GET' and binary:
            self.reads+=1; return b'bad' if (self.mode=='bad_draft' and self.reads==1) or (self.mode=='bad_final' and self.reads==2) else self.raw
        if method=='PATCH': return {'id':10,'tag_name':'morwen-transfer-run-42','draft':False,'prerelease':True}
        raise AssertionError((method,url))
def invoke(api,data=blob,expected=source):return transfer(data,'fixture-only','42','b'*40,'99',api,expected_source=expected)
cases=[]
a=API(); result=invoke(a); assert result['sha256']==sha(blob) and a.reads==2; cases.append('valid historical package + two byte readbacks')
for mode in ('public','exists','draft_exists','forbidden','bad_asset','bad_draft','bad_final'):
    a=API(mode)
    try:invoke(a)
    except (ValueError,TransportError):pass
    else:raise AssertionError(mode)
    if mode in ('public','exists','draft_exists','forbidden'):assert all(m=='GET' for m,u in a.calls)
    if mode in ('bad_asset','bad_draft'):assert not any(m=='PATCH' for m,u in a.calls)
    cases.append(mode+' rejected')
for name,data,expected in [('truncated',blob[:-8],source),('wrong source',blob,'0'*64)]:
    a=API()
    try:invoke(a,data,expected)
    except (ValueError,zipfile.BadZipFile):pass
    else:raise AssertionError(name)
    assert not a.calls; cases.append(name+' rejected before network')
print(len(cases), '/',len(cases),'PASS',sep=''); print('\n'.join(cases)); print('historical package bytes',len(blob)); print('sha',sha(blob))

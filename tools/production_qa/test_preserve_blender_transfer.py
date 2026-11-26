"""Offline package regression; synthetic .blend/receipts/PNGs, not Blender QA."""
import io, json, pathlib, tempfile, zipfile
from PIL import Image
from preserve_blender_transfer import build, VIEWS, SOURCE, sha, publish_package
from transfer_private_release import BASE, DEST
from release_transport import TransportError

def put(p,d): p.write_text(json.dumps(d))
class API:
    def __init__(self,mode='ok'): self.mode=mode; self.data=None; self.calls=[]; self.reads=0
    def __call__(self,t,m,u,body=None,content_type='application/json',binary=False,limit=None):
        self.calls.append((m,u)); assert t=='fixture-only'
        if m=='GET' and u==BASE: return {'full_name':DEST,'private':self.mode!='public'}
        if m=='GET' and u==BASE+'/git/ref/heads/main': return {'ref':'refs/heads/main','object':{'type':'commit','sha':'a'*40}}
        if m=='GET' and '/releases?per_page=' in u: return [{'tag_name':'morwen-blender-run-42'}] if self.mode=='existing' else []
        if m=='GET' and ('/tags/' in u): raise TransportError(404)
        if m=='POST' and u==BASE+'/releases':
            assert json.loads(body)['tag_name']=='morwen-blender-run-42'
            return {'id':10,'tag_name':'morwen-blender-run-42','draft':True}
        if m=='POST' and u.endswith('/assets?name=Morwen-blender.zip'):
            self.data=body; return {'id':11,'name':'Morwen-blender.zip','state':'uploaded','size':len(body),'digest':'sha256:'+sha(body)}
        if m=='GET' and binary:
            self.reads+=1
            return b'bad' if self.mode=='bad_readback' else self.data
        if m=='PATCH': return {'id':10,'tag_name':'morwen-blender-run-42','draft':False,'prerelease':True}
        raise AssertionError((m,u))
with tempfile.TemporaryDirectory() as td:
    base=pathlib.Path(td); source=base/'input'; root=base/'output'; source.mkdir(0o700); root.mkdir(0o700); (root/'views').mkdir()
    vrm=b'synthetic VRM fixture'; blend=b'synthetic blend fixture (not a real blend)'; rev='b'*40; archive='a'*64
    (source/'Morwen-transfer.vrm').write_bytes(vrm); (root/'Morwen-transfer.blend').write_bytes(blend)
    i=dict(scope='PRIVATE_VRM_INPUT_VERIFIED_NOT_IMPORTED',native_sha256=SOURCE,run_id='42',request_id='99',revision=rev,archive_sha256=archive,vrm_sha256=sha(vrm))
    r=dict(scope='STRUCTURAL_IMPORT_AND_REOPEN_NOT_ART_ACCEPTANCE',blender='5.3.0',addon='4.10.5',vrm_sha256=sha(vrm),blend_sha256=sha(blend),saved_and_reopened={'meshes':{'test':1},'armatures':{'test':1},'images':{'test':1}})
    put(source/'input-receipt.json',i); put(root/'transfer-receipt.json',r)
    for j,v in enumerate(VIEWS): Image.new('RGB',(1024,1024),(j*50,50,50)).save(root/'views'/f'{v}.png')
    def invoke(): return build(source,root,'42','99',rev,archive)
    raw=invoke(); cases=['package exact bytes']
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert len(z.namelist())==len(VIEWS)+4 and z.testzip() is None and z.read('Morwen-transfer.blend')==blend
        assert all(sha(z.read(k))==d for k,d in json.loads(z.read('SHA256SUMS.json')).items())
    def reject(label,fn):
        try: fn()
        except (ValueError,TransportError): cases.append(label); return
        raise AssertionError(label)
    for key,val in [('native_sha256','0'*64),('run_id','43'),('archive_sha256','0'*64)]:
        put(source/'input-receipt.json',dict(i,**{key:val})); reject('wrong '+key,invoke)
    put(source/'input-receipt.json',i)
    for key,val in [('blend_sha256','0'*64),('blender','5.2.4'),('saved_and_reopened',{})]:
        put(root/'transfer-receipt.json',dict(r,**{key:val})); reject('wrong '+key,invoke)
    put(root/'transfer-receipt.json',r)
    path=root/'views'/'minus-y.png'; old=path.read_bytes(); path.write_bytes(old[:-1]); reject('truncated PNG',invoke)
    path.write_bytes((root/'views'/'plus-x.png').read_bytes()); reject('duplicate views',invoke); path.write_bytes(old)
    root.chmod(0o755); reject('nonprivate output',invoke); root.chmod(0o700)
    def publish(a): return publish_package(raw,'fixture-only','42',rev,'99',a,kind='blend')
    a=API(); assert publish(a)['sha256']==sha(raw) and a.reads==2; cases.append('private create-only readback twice')
    for mode in ('public','existing','bad_readback'):
        a=API(mode); reject('transport '+mode,lambda:publish(a)); assert not any(m=='PATCH' for m,u in a.calls)
    print(f'{len(cases)}/{len(cases)} PASS (synthetic package, no Blender execution)',*cases,sep='\n')

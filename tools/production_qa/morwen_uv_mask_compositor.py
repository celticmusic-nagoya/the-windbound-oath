"""Mask-gated material compositor. No inferred UV mapping or native edits."""
import hashlib, io, json, pathlib, sys
import numpy as np
from PIL import Image

W,H=1024,512
EXPECTED={
 'dark':'7b5558f4d6a548cd15e7803161532c8fbad5e98b25ffc49e094ae646a882ae83',
 'plaid':'7287b8aa970aed092a87d6fc89aa09a2419edbf5d37316afae9424c32fc66db3',
 'trim':'22b6e4634d7f0e9f600d52a9180b2ba25fadab43c31979b4674634c7f4251ca4'}
def sha(b): return hashlib.sha256(b).hexdigest()
def require(ok,msg):
    if not ok: raise ValueError(msg)
def load(ref,mode,size,expected=None):
    b=pathlib.Path(ref['path']).read_bytes()
    require(sha(b)==ref['sha256'] and (expected is None or sha(b)==expected),'source SHA mismatch')
    with Image.open(io.BytesIO(b)) as im:
        require(im.format=='PNG' and im.mode==mode and im.size==size,'unexpected image contract')
        return np.array(im)
def compose(spec,out):
    require(spec['scope']=='SYNTHETIC_FIXTURE_ONLY','only test fixtures qualified; real UV use not authorized by this script')
    base=load(spec['base'],'RGBA',(W,H))
    masks={}
    for name in ('dark','plaid','trim'):
        a=load(spec['masks'][name],'L',(W,H)); require(np.all((a==0)|(a==255)),'nonbinary mask'); masks[name]=a==255
    d,p,t=(masks[n] for n in ('dark','plaid','trim')); cloth=d|p
    require(d.any() and p.any() and t.any(),'empty mask')
    require(not np.any(d&p),'cloth overlap'); require(not np.any(t&~cloth),'trim outside cloth')
    require(not np.any(cloth&(base[:,:,3]!=255)),'cloth intersects protected alpha')
    materials={n:load(spec['materials'][n],'RGBA',(W,H if n!='trim' else 128),EXPECTED[n]) for n in EXPECTED}
    require(all(np.all(materials[n][:,:,3]==255) for n in ('dark','plaid')),'cloth material alpha invalid')
    ox,oy=spec['trim_phase_px']; require(type(ox)==int and type(oy)==int and 0<=ox<W and 0<=oy<128,'invalid trim phase')
    yy,xx=np.indices((H,W)); trim=materials['trim'][(yy-oy)%128,(xx-ox)%W]
    require(not np.any(t&(trim[:,:,3]==0)),'trim mask includes transparent source')
    result=base.copy()
    for name,m in [('dark',d),('plaid',p)]: result[m,:3]=materials[name][m,:3]
    alpha=trim[t,3].astype(np.int32)[:,None]; old=result[t,:3].astype(np.int32)
    result[t,:3]=((trim[t,:3].astype(np.int32)*alpha+old*(255-alpha)+127)//255).astype(np.uint8)
    require(np.array_equal(result[:,:,3],base[:,:,3]),'alpha changed')
    require(np.array_equal(result[~cloth],base[~cloth]),'outside changed')
    out=pathlib.Path(out);out.mkdir(exist_ok=False)
    target=out/'fixture-composite.png';Image.fromarray(result).save(target)
    require(np.array_equal(np.array(Image.open(target)),result),'reopen failed')
    receipt={'scope':spec['scope'],'pixels':{n:int(m.sum()) for n,m in masks.items()},'outside_unchanged':True,'alpha_exact':True,'png_sha256':sha(target.read_bytes()),'pixel_sha256':sha(result.tobytes()),'limitations':['Synthetic masks only, not observed garment UV','No native import, model edits or formal adoption']}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
if __name__=='__main__': print(json.dumps(compose(json.loads(pathlib.Path(sys.argv[1]).read_text()),sys.argv[2]),indent=2))

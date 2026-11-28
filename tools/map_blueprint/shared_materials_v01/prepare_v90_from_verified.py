"""Regenerate V90 native material inputs from exact V84/V87 CI artifacts only.
No locally generated V90 ZIP, geometry changes, or external downloads required.
"""
import argparse, hashlib, io, json, struct, zipfile
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

LOCK84='f7cf35f137e67627b43dcc7acd96f0f964783b7452da41a11ebb1e5a4cbcc27b'
LOCK87='311c389daef670bdb39a3dab8bd061fd6e62056397f37880eaa0dfee01c0a081'
LOCK_RECEIPT='4d0e6c82b553b599ae7cfa51cddf781adac4b8ae20193b904a11b575c5812c89'
sha=lambda b:hashlib.sha256(b).hexdigest()
def checked(path,expected):
    with path.open('rb') as f: assert hashlib.file_digest(f,'sha256').hexdigest()==expected,path
    z=zipfile.ZipFile(path);assert z.testzip() is None
    manifest={n.strip().removeprefix('./'):h for h,n in (l.split(None,1) for l in z.read('SHA256SUMS').decode().splitlines())}
    for n,h in manifest.items():assert sha(z.read(n))==h,n
    return z,manifest

def parse(b,lock):
    assert sha(b)==lock
    magic,ver,size=struct.unpack_from('<4sII',b);n,t=struct.unpack_from('<II',b,12)
    assert (magic,ver,size,t)==(b'glTF',2,len(b),0x4e4f534a)
    length,tag=struct.unpack_from('<II',b,20+n);raw=b[28+n:];assert length==len(raw) and tag==0x004e4942
    return json.loads(b[20:20+n]),raw

def view(d,b,i):
    v=d['bufferViews'][i];s=v.get('byteOffset',0);return b[s:s+v['byteLength']]
def image(d,b,i):return view(d,b,d['images'][i]['bufferView'])
def rgb(b):return np.asarray(Image.open(io.BytesIO(b)).convert('RGB')).copy()
def png(a):
    f=io.BytesIO();Image.fromarray(a).save(f,format='PNG');return f.getvalue()
def lin(x):
    x=x.astype(float)/255;return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def srgb(x):return np.rint(np.clip(np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055),0,1)*255).astype(np.uint8)

def main():
    p=argparse.ArgumentParser();p.add_argument('--v84',type=Path,required=True);p.add_argument('--v87',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    assert not a.out.exists(),'refusing to overwrite output directory'
    z84,m84=checked(a.v84,LOCK84);z87,m87=checked(a.v87,LOCK87)
    with z84,z87:
        S,SB=parse(z84.read('v84_sanctuary_dormant.glb'),'47ac77303797e67b1bfe2dd2b67895149ba2d6aec1edef1a0ffcfe31d1050913')
        D,B=parse(z87.read('v87_dormant_inlay.glb'),'70c875b6368dfc056e970f5a93882a667c5cd5bb56e0a2dc1e29fe2817a086f6')
        assert D['meshes']==S['meshes'] and D['nodes']==S['nodes'] and D['accessors']==S['accessors']
        assert all(view(D,B,acc['bufferView'])==view(S,SB,acc['bufferView']) for acc in D['accessors'])
        assert all(not any(m.get('emissiveFactor',[0,0,0])) and 'emissiveTexture' not in m for m in D['materials'])
        nq=json.loads(z87.read('v87_native_qa.json'));assert nq['native_sha']=='7f439b39cc8f7ad1c8702b65b55fa268cd74df1a2ad6720c9d3c73dd0b946222'
        receipt={'source_native_sha256':nq['native_sha'],'source_archive_sha256':LOCK87,'candidate_only':True,'native_bump_distance_local':0.012,'native_bump_strength':0.65,'parts':{},'limits':['Provisional local bump distance, no physical geometry displacement','Original tangent normal input retained; actual Blender render and export not executed locally']}
        outputs={}
        for part,name,c,r,count in [('stele','back',1,2,912),('floor','platform',3,4,7054),('posts','posts',5,6,19102)]:
            maskbytes=z87.read('projection/'+part+'_mask.png');mask=np.asarray(Image.open(io.BytesIO(maskbytes)).convert('L')).astype(float)/255;active=mask>0;assert active.sum()==count
            original=rgb(image(S,SB,c));oldcolor=z87.read('projection/'+part+'_candidate.png');assert oldcolor==image(D,B,c)
            old=rgb(oldcolor);oldrough=z84.read('V84_V81_ruin_'+name+'_roughness.png');a0=rgb(oldrough);a1=rgb(image(D,B,r))
            assert image(D,B,r)==image(S,SB,r) and np.array_equal(a0[:,:,0],a1[:,:,1]) and np.all(a0==a0[:,:,:1])
            assert np.array_equal(old[~active],original[~active])
            new=srgb(lin(original)*(1-mask[...,None]*(1-np.array([.28,.32,.36]))));new[~active]=old[~active]
            rough=a1.copy();rough[...,1]=np.rint(np.clip(a1[...,1]/255+.18*mask,0,1)*255).astype(np.uint8)
            assert np.array_equal(new[~active],old[~active]) and np.array_equal(rough[~active],a1[~active]) and np.array_equal(rough[...,[0,2]],a1[...,[0,2]])
            depth=np.minimum(distance_transform_edt(active)/1.5,1)*mask;hi=np.rint((1-depth)*65535).astype(np.uint16);assert np.all(hi[~active]==65535)
            maps={'color':png(new),'roughness':png(np.repeat(rough[:,:,1:2],3,axis=2)),'height':png(hi)};outfiles={}
            for key,data in maps.items():
                fn=part+'_'+key+'.png';outputs[fn]=data;outfiles[key]={'name':fn,'sha256':sha(data)}
            receipt['parts'][part]={'object':'V81_ruin_'+name,'source_color_sha256':sha(oldcolor),'source_native_roughness_sha256':sha(oldrough),'mask_texels':count,'roughness_green_native_exact':True,'unmasked_exact':True,'maps':outfiles}
        record=(json.dumps(receipt,indent=2)+'\n').encode();assert sha(record)==LOCK_RECEIPT,('receipt differs',sha(record),'check numpy/Pillow/scipy versions')
        outputs['native_input_receipt.json']=record
        a.out.mkdir(parents=True,exist_ok=False)
        for n,b in outputs.items():(a.out/n).write_bytes(b);assert sha((a.out/n).read_bytes())==sha(b)
        print('V90_PORTABLE_INPUTS_PASS',len(outputs),sha(record))
if __name__=='__main__':main()

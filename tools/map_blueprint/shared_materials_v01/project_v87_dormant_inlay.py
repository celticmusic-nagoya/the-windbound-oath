"""V87 portable reconstruction of the measured F2 UV pigment candidate.
Input GLB hashes pinned; nearest stele depths are measured from those exact bytes.
No physical cutting of stone. Retain original base/FX geometries.
"""
import argparse,hashlib,io,json,struct,zipfile
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('base',type=Path);p.add_argument('rune_zip',type=Path);p.add_argument('out',type=Path);args=p.parse_args()
out=args.out;out.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
raw=args.base.read_bytes()
with zipfile.ZipFile(args.rune_zip) as z: fx=z.read('v82_altar_rune_vfx.glb')
assert sha(raw)=='47ac77303797e67b1bfe2dd2b67895149ba2d6aec1edef1a0ffcfe31d1050913'
assert sha(fx)=='f6a9e4e60f10c85fe9dba133c53831ea46c7f2d96d3597dcf70e7c319a062b86'
def parse(b):
    n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),b[28+n:]
def acc(d,blob,i):
    a=d['accessors'][i];v=d['bufferViews'][a['bufferView']];dt={5126:'<f4',5123:'<u2',5125:'<u4'}[a['componentType']];k={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]
    assert v.get('byteStride',np.dtype(dt).itemsize*k)==np.dtype(dt).itemsize*k
    return np.frombuffer(blob,dtype=dt,count=a['count']*k,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(a['count'],k)
def triangles(d,blob,m,uv=False):
    p=m['primitives'][0];ix=acc(d,blob,p['indices']).reshape(-1,3);a=p['attributes'];v=acc(d,blob,a['POSITION']).astype(float)[ix]
    norm=acc(d,blob,a['NORMAL']).astype(float)[ix].mean(1);norm/=np.maximum(np.linalg.norm(norm,axis=1,keepdims=True),1e-12)
    return v,norm,acc(d,blob,a['TEXCOORD_1']).astype(float)[ix] if uv else None
def clip(poly,func):
    out=[]
    for p,q in zip(poly,np.roll(poly,-1,axis=0)):
        a,b=func(p),func(q);ina,inb=a>=-1e-9,b>=-1e-9
        if ina:out.append(p)
        if ina!=inb:out.append(p+(q-p)*(a/(a-b)))
    return np.asarray(out)
def polyarea(p):return abs(np.dot(p[:,0],np.roll(p[:,1],-1))-np.dot(p[:,1],np.roll(p[:,0],-1)))/2
D,B=parse(raw);F,FB=parse(fx)
assert all(not any(k in n for k in ('matrix','translation','rotation','scale')) for n in D['nodes']+F['nodes'])
# Rounded 1e-9 measured F2 distances; original diagnostic SHA b82f232849db4973f4ee82c7ac0c720351741512143e8f878d31c74460a6c288.
ref=[0.054744051,0.055631595,0.051616465,0.052437555,0.049880529,0.050632759,0.048088122,0.048781874,0.000376289,0.035297135,0.053252658,0.054113842,0.05605971,0.056946721,0.057162923,0.058033942,0.058031695,0.05885915,0.058637507,0.059403188,0.05897196,0.059658235,0.059027893,0.059616501,0.058799681,0.059273385,0.058287635,0.058637031,0.057513095,0.057733491,0.056494308,0.056574418,0.055251222,0.055195719,0.053822783,0.053625414,0.052235214,0.051906104,0.050533876,0.050077291,0.048755243,0.048189151,0.046949734,0.046281129,0.045156827,0.044404597,0.043421889,0.042600799,0.041784699,0.040923515,0.040293777,0.03940623,0.038977782,0.038090768,0.037874964,0.037003948,0.037006197,0.036178745,0.036400053,0.035634374,0.03606606,0.035379784,0.036009462,0.035420855,0.036238006,0.035764302,0.036749593,0.036400198,0.03752413,0.037303735,0.03854338,0.03846327,0.039786411,0.039841915,0.04121557,0.041412939,0.04280196,0.043131071,0.044504143,0.044960729,0.04630736,0.046848374,-0.023806497,-0.027967561,-0.02831569,-0.023164478,0.06887675,0.069461836,0.018066671,0.017992118,0.017297022,0.017676222]
qa={}
for mi,fi,name,expected in [(0,0,'stele',912),(1,2,'floor',7054),(2,1,'posts',19102)]:
    st,sn,suv=triangles(D,B,D['meshes'][mi],True);rt,rn,_=triangles(F,FB,F['meshes'][fi]);rc=rt.mean(1);rr=np.linalg.norm(rt-rc[:,None],axis=2).max(1);tree=cKDTree(rc)
    prim=D['meshes'][mi]['primitives'][0];mat=D['materials'][prim['material']];t=mat['pbrMetallicRoughness']['baseColorTexture'];assert t['texCoord']==1
    im=D['images'][D['textures'][t['index']]['source']];view=D['bufferViews'][im['bufferView']];base=B[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]
    img=Image.open(io.BytesIO(base)).convert('RGB');w,h=img.size;assert (w,h)==(1024,1024)
    ss=3;mask=Image.new('L',(w*ss,h*ss));draw=ImageDraw.Draw(mask);projected=set()
    for s,n,u in zip(st,sn,suv):
        center=s.mean(0);rad=np.linalg.norm(s-center,axis=1).max();cand=tree.query_ball_point(center,rad+rr.max()+.07)
        if not cand:continue
        e=s[1:]-s[0];g=e@e.T
        if np.linalg.det(g)<1e-15:continue
        actual=np.cross(e[0],e[1]);actual/=np.linalg.norm(actual);actual*=1 if np.dot(actual,n)>=0 else -1
        if name=='floor' and actual[1]<.8:continue
        for i in cand:
            if abs(np.dot(actual,rn[i]))<=.92:continue
            delta=(rt[i]-s[0])@actual
            if name=='stele':
                if abs(-delta.mean()/np.dot(actual,rn[i])-ref[i])>.012 or np.max(abs(delta))>.085:continue
            elif delta.min()<-.018 or delta.max()>.055:continue
            coords=(rt[i]-s[0])@e.T@np.linalg.inv(g)
            for f in (lambda p:p[0],lambda p:p[1],lambda p:1-p[0]-p[1]):
                coords=clip(coords,f)
                if len(coords)<3:break
            if len(coords)<3 or polyarea(coords)<1e-10:continue
            uv=u[0]+coords@(u[1:]-u[0]);draw.polygon([tuple(p) for p in uv*np.array([w*ss,h*ss])],fill=255);projected.add(i)
    mask=mask.resize((w,h),Image.Resampling.BOX);alpha=np.asarray(mask)/255.
    assert len(projected)==len(rt) and np.count_nonzero(alpha)==expected,(name,len(projected),len(rt),np.count_nonzero(alpha))
    arr=np.asarray(img).astype(float)/255.;lin=np.where(arr<=.04045,arr/12.92,((arr+.055)/1.055)**2.4);new=lin*(1-alpha[:,:,None]*(1-np.array([.51,.56,.60])));rgb=np.where(new<=.0031308,12.92*new,1.055*np.maximum(new,0)**(1/2.4)-.055);rgb=np.round(np.clip(rgb,0,1)*255).astype(np.uint8);rgb[alpha==0]=np.asarray(img)[alpha==0]
    assert np.array_equal(rgb[alpha==0],np.asarray(img)[alpha==0])
    dest=out/(name+'_candidate.png');Image.fromarray(rgb).save(dest)
    mask.save(out/(name+'_mask.png'))
    qa[name]={'source_sha':sha(base),'candidate_sha':sha(dest.read_bytes()),'projected':len(projected),'affected_texels':expected}
    print(name,qa[name],flush=True)
(out/'projection_qa.json').write_text(json.dumps(qa,indent=2))

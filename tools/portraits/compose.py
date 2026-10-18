import cv2,numpy as np,json,os,sys
from lib import *
from regions import REG
from mos import IDS,NM,SRC
K=np.ones((3,3),np.uint8)
def poly(H,W,p):
    m=np.zeros((H,W),np.uint8);cv2.fillPoly(m,[np.array(p,np.int32)],255);return m
def feather(m,s=1.2):
    f=cv2.GaussianBlur(m.astype(np.float32)/255,(0,0),s);f[f<0.01]=0;return f
def skin(b):return (b[...,0]>190)&(b[...,0]>b[...,1])&(b[...,1]>b[...,2])&(b[...,0]-b[...,2]>20)
def compose(ch,i):
    base=load(f'{ch}_master.png');H,W=base.shape[:2];b=base.astype(np.float32)
    s,p=SRC[i];w=load(f'warp/{ch}_{s}{p}.png').astype(np.float32)
    out=b.copy();wt=np.zeros((H,W),np.float32);info={}
    regs={'eyeL':REG[ch]['eyeL'],'eyeR':REG[ch]['eyeR'],'mouth':REG[ch]['mouth']}
    if i in REG[ch].get('cheek',{}):regs['cheek']=REG[ch]['cheek'][i]
    for name,pts in regs.items():
        m=poly(H,W,pts)
        ring=(cv2.dilate(m,K,iterations=12)>0)&~(cv2.dilate(m,K,iterations=3)>0)
        d=np.abs(w[...,:3]-b[...,:3]).max(2)
        ok=ring&skin(b)&(d<26)&(w[...,3]>200)
        off=np.median((b[...,:3]-w[...,:3])[ok],axis=0) if ok.sum()>40 else np.zeros(3)
        off=np.clip(off,-10,10);info[name]=dict(offset=off.round(1).tolist(),ring_px=int(ok.sum()))
        f=feather(m);wc=np.clip(w[...,:3]+off,0,255)
        out[...,:3]=out[...,:3]*(1-f[...,None])+wc*f[...,None];wt=np.maximum(wt,f)
    for k,(c,ax) in enumerate(REG[ch].get('cheek_soft',{}).get(i,[])):
        m=np.zeros((H,W),np.uint8);cv2.ellipse(m,c,ax,0,0,360,255,-1);f=feather(m,5)
        lw=cv2.GaussianBlur(w[...,:3],(0,0),6);lb=cv2.GaussianBlur(b[...,:3],(0,0),6)
        out[...,:3]=np.clip(out[...,:3]+f[...,None]*(lw-lb),0,255);wt=np.maximum(wt,f);info[f'cheek_soft{k}']=True
    res=base.copy();res[...,:3]=np.clip(np.rint(out[...,:3]),0,255).astype(np.uint8);res[wt==0]=base[wt==0]
    return res,wt,info
if __name__=='__main__':
    os.makedirs('out',exist_ok=True);allinfo={}
    for ch in ['fiona','lou']:
        base=Image.open(f'{ch}_master.png');base.save(f'out/{ch}_normal.png',optimize=False) if False else None
        import shutil;shutil.copy(f'{ch}_master.png',f'out/{ch}_normal.png')
        for i,n in zip(IDS,NM):
            if n=='normal':continue
            res,wt,info=compose(ch,i);Image.fromarray(res).save(f'out/{ch}_{n}.png');np.save(f'out/wt_{ch}_{n}.npy',(wt>0));allinfo[f'{ch}_{n}']=info
    json.dump(allinfo,open('out/blend_info.json','w'),indent=1);print('done')

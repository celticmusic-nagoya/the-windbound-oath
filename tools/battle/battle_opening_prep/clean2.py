import numpy as np, pickle, sys, colorsys
from PIL import Image
from scipy import ndimage as ndi
def hsv(rgb):
    r,g,b=[rgb[...,i].astype(np.float32)/255 for i in range(3)];mx=np.max(rgb/255.0,-1);mn=np.min(rgb/255.0,-1);d=mx-mn+1e-6
    h=np.where(mx==r,((g-b)/d)%6,np.where(mx==g,(b-r)/d+2,(r-g)/d+4))*60
    return h,d/(mx+1e-6),mx
def clean(f,protect_magic=False):
    a=f.astype(np.float32);al=a[...,3];rgb=a[...,:3]
    r,g,b=rgb[...,0],rgb[...,1],rgb[...,2]
    green=(g>=r-4)&(g>b+30)          # green / yellow-green light: the nature-magic glow and leaf tones - never touched
    thr,it=(70,3) if protect_magic else (110,2)
    core=al>=thr;keep=ndi.binary_dilation(core,iterations=it)
    if protect_magic:
        gl=(al>0)&green&(al<thr)
        gl=ndi.binary_opening(gl,iterations=1)
        keep=keep|(ndi.binary_dilation(gl,iterations=2)&(al>0)&green)
    lab,n=ndi.label(keep);sz=ndi.sum(keep,lab,range(1,n+1))
    for k,s_ in enumerate(sz):
        if s_<400:keep[lab==k+1]=False
    al2=np.where(keep,al,0)
    soft=np.clip((al2-10)/(thr-10),0,1);al2=np.where(al2<thr,al2*soft,al2)
    if protect_magic: al2=np.where(keep&green&(al<thr),al,al2)
    solid=al>=230;d,(iy,ix)=ndi.distance_transform_edt(~solid,return_indices=True)
    near=a[iy,ix,:3];band=(al2>0)&(al2<230)
    if protect_magic: band&=~green      # only warm (red/yellow/brown) fringe pixels get their colour pulled in
    out_rgb=rgb.copy();out_rgb[band]=near[band]
    out=np.dstack([out_rgb,al2]);out[al2==0]=0
    return np.clip(out,0,255).astype(np.uint8)
if __name__=='__main__':
    w=sys.argv[1];raw=pickle.load(open('%s_raw.pkl'%w,'rb'));out=[clean(f,w=='fiona') for f in raw]
    for i,(r,c) in enumerate(zip(raw,out),1):print(w,i,'px',(r[...,3]>0).sum(),'->',(c[...,3]>0).sum(),'alphasum',int(r[...,3].sum()/255),'->',int(c[...,3].sum()/255))
    pickle.dump(out,open('%s_clean.pkl'%w,'wb'))
    # montage of 6 on dark + white
    H=727;ims=[]
    for c in out:
        ys,xs=np.where(c[...,3]>0);im=Image.fromarray(c).crop((xs.min()-6,0,xs.max()+7,H));ims.append(im)
    for nm,col in (('dark',(18,22,24,255)),('light',(255,255,255,255))):
        W=sum(i.width for i in ims)+10*5;sh=Image.new('RGBA',(W,H),col);x=0
        for im in ims:
            sh.alpha_composite(im,(x,0));x+=im.width+10
        sh.convert('RGB').save('%s_%s.png'%(w,nm))

import numpy as np, pickle, sys, colorsys
from PIL import Image
from scipy import ndimage as ndi
def load(p): return np.array(Image.open(p).convert('RGBA'))
def seam(al,x0,x1,ymin,ymax):
    # min-cost vertical seam through alpha mass between x0..x1 (cost = opacity), returns x per row
    cost=(al[:, x0:x1].astype(np.float32)/255.0)**1+0.002;H,W=cost.shape
    dp=cost.copy();bk=np.zeros((H,W),np.int8)
    for y in range(1,H):
        prev=dp[y-1];l=np.r_[np.inf,prev[:-1]];r=np.r_[prev[1:],np.inf];st=np.stack([l,prev,r]);k=st.argmin(0);dp[y]+=st[k,np.arange(W)];bk[y]=k-1
    x=int(dp[-1].argmin());path=[0]*H
    for y in range(H-1,-1,-1):
        path[y]=x+x0
        x+=int(bk[y,x])
        x=max(0,min(W-1,x))
    return np.array(path)
def split(a,expect,merged_seams=None):
    al=a[...,3];lab,n=ndi.label(al>32);sz=ndi.sum(al>32,lab,range(1,n+1))
    big=[i+1 for i,s in enumerate(sz) if s>2000]
    cx=[np.where(lab==i)[1].mean() for i in big];order=[b for _,b in sorted(zip(cx,big))]
    mask=np.zeros(al.shape,np.int32);k=0;ids=[]
    for b in order:
        k+=1;ids.append(b)
        if merged_seams and k in merged_seams:   # this component holds two frames -> cut it along a seam
            x0,x1=merged_seams[k];ys,xs=np.where(lab==b);sp=seam(al*(lab==b),x0,x1,ys.min(),ys.max())
            X=np.arange(al.shape[1])[None,:];left=(lab==b)&(X<=sp[:,None]);right=(lab==b)&(X>sp[:,None])
            mask[left]=k;k+=1;mask[right]=k
        else:mask[lab==b]=k
    assert k==expect,(k,expect)
    d,(iy,ix)=ndi.distance_transform_edt(mask==0,return_indices=True);near=mask[iy,ix]
    # pixels beyond reach of any body (haze far from the figure) are dropped
    frames=[]
    for f in range(1,expect+1):
        m=(near==f)&(al>0)&(d<=40);out=a.copy();out[~m]=0;frames.append(out)
    return frames
if __name__=='__main__':
    which=sys.argv[1]
    U='/root/.claude/uploads/5a32fd61-13d2-5098-bac0-aa85ac7ead89/'
    if which=='aidan':a=load(U+'f2c9ccd0-image.png');fr=split(a,6,{2:(690,760)})
    else:a=load(U+'42497be7-image.png');fr=split(a,6)
    for i,f in enumerate(fr,1):
        ys,xs=np.where(f[...,3]>32);print(which,i,xs.min(),xs.max(),ys.min(),ys.max(),'w',xs.max()-xs.min(),'h',ys.max()-ys.min())
    pickle.dump(fr,open('v2/%s_raw.pkl'%which,'wb'))

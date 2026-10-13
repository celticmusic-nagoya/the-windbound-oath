import numpy as np,pickle,sys
from PIL import Image
from scipy import ndimage as ndi
U='/root/.claude/uploads/5a32fd61-13d2-5098-bac0-aa85ac7ead89/'
SRC={'aidan_idle':'bbf9cef2','aidan_draw':'b9116c17','fiona_idle':'aa388f94'}
def split(a,expect=6):
    al=a[...,3];lab,n=ndi.label(al>32);sz=ndi.sum(al>32,lab,range(1,n+1))
    big=[i+1 for i,s in enumerate(sz) if s>2000];assert len(big)==expect
    H=a.shape[0];rows=2 if expect==6 and a.shape[1]<2000 else 1
    def key(b):
        ys,xs=np.where(lab==b);return (int(ys.mean()>H/2) if rows==2 else 0,xs.mean())
    order=sorted(big,key=key);mask=np.zeros(al.shape,np.int32)
    for k,b in enumerate(order,1):mask[lab==b]=k
    d,(iy,ix)=ndi.distance_transform_edt(mask==0,return_indices=True);near=mask[iy,ix]
    fr=[]
    for f in range(1,expect+1):
        m=(near==f)&(al>0)&(d<=40);o=a.copy();o[~m]=0;fr.append(o)
    return fr
if __name__=='__main__':
    n=sys.argv[1];a=np.array(Image.open(U+SRC[n]+'-image.png').convert('RGBA'))
    fr=split(a);pickle.dump(fr,open(n+'_raw.pkl','wb'))
    for i,f in enumerate(fr,1):
        ys,xs=np.where(f[...,3]>32);print(n,i,xs.min(),xs.max(),ys.min(),ys.max())

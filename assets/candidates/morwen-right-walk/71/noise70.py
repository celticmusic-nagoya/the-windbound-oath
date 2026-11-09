import numpy as np
from PIL import Image
def isolated(a, region=None, T=38.0):
    h,w=a.shape[:2]; c=a[:,:,:3].astype(float); op=a[:,:,3]>0
    wts=np.array([0.3,0.59,0.11])*3
    def d(dy,dx):
        s=np.roll(np.roll(c,dy,0),dx,1); return np.sqrt(((c-s)**2*wts).sum(2))
    iso=op.copy()
    for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
        nb=np.roll(np.roll(op,dy,0),dx,1); iso&=nb&(d(dy,dx)>T)
    iso[0,:]=iso[-1,:]=iso[:,0]=iso[:,-1]=False
    if region is not None: iso&=region
    return int(iso.sum())

import numpy as np
from PIL import Image
import os
A=os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','..','..','..')),'img/field/characters/aidan/')
Y0=780
def load(n): return np.array(Image.open(A+'aidan_walk_up_%02d.png'%n).convert('RGBA')).astype(float)
def hsv(a):
  rgb=a[...,:3]/255;mx,mn=rgb.max(-1),rgb.min(-1);d=mx-mn+1e-9;r,g,b=rgb[...,0],rgb[...,1],rgb[...,2]
  h=np.where(mx==r,(g-b)/d%6,np.where(mx==g,(b-r)/d+2,(r-g)/d+4))*60;return h,d/(mx+1e-9),mx
def split(a,xlo,xhi,y0=Y0,y1=1240):
  c=(a[y0:y1,xlo:xhi+1,3]/255)*(0.3+a[y0:y1,xlo:xhi+1,:3].mean(-1)/255)+0.02
  H,W=c.shape;acc=c.copy();back=np.zeros((H,W),int)
  for y in range(1,H):
    p=acc[y-1];cand=np.stack([np.r_[np.inf,p[:-1]],p,np.r_[p[1:],np.inf]]);k=cand.argmin(0);acc[y]+=cand[k,np.arange(W)];back[y]=k-1
  x=int(acc[-1].argmin());path=[x]
  for y in range(H-1,0,-1): x+=back[y,x];path.append(x)
  cut=np.full(a.shape[0],(xlo+xhi)//2);cut[y0:y1]=np.array(path[::-1])+xlo;return cut
def legs(a,cut):
  h,s,v=hsv(a);X=np.arange(a.shape[1])[None,:];Y=np.arange(a.shape[0])[:,None]
  trousers=(a[...,3]>24)&(v<0.36)&((h<40)|(h>340))
  boots=(a[...,3]>24)&((((h<40)|(h>340))&(s>0.38))|(v<0.30))
  m=np.where(Y<880,trousers,boots)&(Y>=Y0)&(X>=930)&(X<1200)
  return m&(X<cut[:,None]),m&(X>=cut[:,None])
SPL={1:(1035,1075),2:(1040,1075),3:(1022,1050),4:(1032,1058),5:(1030,1070),6:(1030,1070)}

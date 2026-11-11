import os as _os, sys as _sys
_HERE=_os.path.dirname(_os.path.abspath(__file__))
_PIPE=_os.environ.get('MORWEN72_PIPELINE', _os.path.join(_HERE,'..','..','morwen-right-walk','72'))
_sys.path[:0]=[_HERE,_PIPE]
import numpy as np
from PIL import Image
import sys; pass
import build_morwen66 as B, build_morwen67 as C
from pathlib import Path
H,W=128,96
def refmasks(source=None):
    source=Path(source or _os.environ.get('MORWEN65B_SOURCE','.'))
    ref,_=B.load_reference(source/'morwen_right_walk_00_96x128.png'); uf,ub,_=B.split_layers(ref)
    a=uf; op=a[:,:,3]>0; r,g,b=[a[:,:,i].astype(int) for i in range(3)]
    yy,xx=np.mgrid[0:H,0:W]
    sp=C.split67(uf)
    leather=op&(r>b+35)&(g<r*0.62)&(r<245)&(b<90)
    skin=op&(r>230)&(g>190)&(b>150)
    white=op&(r>220)&(g>210)&(b>210)
    pinkv=op&(r>200)&(b>170)
    bagbox=(xx>=35)&(xx<=55)&(yy>=72)&(yy<=92)
    hand=op&(xx>=43)&(xx<=50)&(yy>=70)&(yy<=79)&(skin|white)
    bag=bagbox&op&~hand&~(pinkv&(xx>=52))
    # keep only pixels that are leather or enclosed dark/gold hardware: take bbox rows where leather exists
    bag=bag&(leather|((r>150)&(g>80)&(b<110))|((r+g+b)<160))
    bag&= (xx<=54)|leather
    strap=op&leather&(xx>=55)&(xx<=66)&(yy>=60)&(yy<=72)
    gold=(r>150)&(g>80)&(b<110)&(r>=g)&(g>b)
    emblem=op&((xx-47)**2/56.0+(yy-55)**2/32.0<=1)&(gold|(r>230)&(g>200)|((r>180)&(g>120)&(b<140)))
    flower=op&(xx>=30)&(xx<=50)&(yy>=11)&(yy<=31)&(pinkv|((r>235)&(g>220)&(b>220))|(gold&(xx>=36)&(xx<=46)&(yy>=16)&(yy<=26)))
    ribbon=op&(xx>=17)&(xx<=40)&(yy>=26)&(yy<=60)&pinkv
    return uf,dict(bag=bag,strap=strap,emblem=emblem,flower=flower,ribbon=ribbon,hand=hand)
if __name__=='__main__':
    uf,m=refmasks()
    cols={'bag':(255,0,0),'strap':(0,255,255),'emblem':(255,255,0),'flower':(0,255,0),'ribbon':(0,120,255),'hand':(255,255,255)}
    vis=uf.copy(); vis[...,:3]//=3; vis[...,3]=255
    for k,c in cols.items(): vis[m[k]]=(*c,255)
    S=7; Image.fromarray(vis).resize((W*S,H*S),Image.NEAREST).save('masks74_overlay.png')
    print({k:int(v.sum()) for k,v in m.items()})

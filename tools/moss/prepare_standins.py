#!/usr/bin/env python3
"""Derive Moss Forest stand-in art from existing Lind field art (no generation).
Outputs img/field/moss/standin/*.png and ground tiles. Real Moss Forest assets later replace these via
img/field/moss/manifest.json (see docs/field/moss-forest-asset-requests.md)."""
from PIL import Image
import numpy as np, os
SRC='img/field/lind/'; OUT='img/field/moss/standin/'; os.makedirs(OUT,exist_ok=True)
def crop(name,out,maxw):
    im=Image.open(SRC+'nature/lind_%s.png'%name).convert('RGBA'); a=np.array(im)[:,:,3]; ys,xs=np.where(a>24)
    im=im.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1)); s=min(1,maxw/im.width)
    im=im.resize((max(1,round(im.width*s)),max(1,round(im.height*s))),Image.LANCZOS); im.save(OUT+out,optimize=True); print(out,im.size)
for n,o,w in [('tree_01','tree.png',320),('bush','bush.png',160),('rock_large','rock_large.png',160),('rock_small','rock_small.png',96),
              ('stump','stump.png',96),('flower_patch','flower.png',64),('grass_tuft','grass.png',64)]: crop(n,o,w)
def seamless(src,out,size=384):
    im=Image.open(SRC+'terrain/'+src).convert('RGB'); w,h=im.size; s=min(w,h)
    im=im.crop(((w-s)//2,(h-s)//2,(w-s)//2+s,(h-s)//2+s)).resize((size,size),Image.LANCZOS); a=np.asarray(im,dtype=np.float32)
    # offset-blend: cross-fade the image with its half-shifted copy using a mask that is 0 at the borders.
    sh=np.roll(np.roll(a,size//2,0),size//2,1); y,x=np.mgrid[0:size,0:size]
    m=np.minimum(np.minimum(x,size-1-x),np.minimum(y,size-1-y))/(size/2); m=np.clip(m*2.0,0,1)[...,None]
    r=a*m+sh*(1-m); Image.fromarray(r.astype(np.uint8)).save(OUT+out,optimize=True); print(out)
seamless('lind_grass.png','ground_grass.png'); seamless('lind_dirt.png','ground_dirt.png')

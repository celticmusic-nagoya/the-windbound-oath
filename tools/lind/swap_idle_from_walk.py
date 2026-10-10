#!/usr/bin/env python3
"""Replace an NPC idle sprite by a chosen walk frame (same canvas) and rewrite <id>_idle bounds.
usage: swap_idle_from_walk.py <frames_dir> <npc_id> [frame_no=1]"""
import os,re,sys,shutil,json
from PIL import Image
import numpy as np
R=os.path.join(os.path.dirname(__file__),'..','..')
d,npc=sys.argv[1],sys.argv[2];n=int(sys.argv[3]) if len(sys.argv)>3 else 1
src=os.path.join(d,'%s_walk_%02d.png'%(npc,n));dst=os.path.join(R,'img/field/lind/npc/villagers/%s_idle.png'%npc)
im=Image.open(src).convert('RGBA');a=np.array(im)[...,3]>16;ys,xs=np.where(a)
b=[im.width,im.height,int(xs.min()),int(ys.min()),int(xs.max()-xs.min()+1),int(ys.max()-ys.min()+1)]
shutil.copy(src,dst)
p=os.path.join(R,'js/field/lind-content-bounds.js');t=open(p).read()
pat=re.compile(r'("%s_idle":\s*)\[[^\]]*\]'%npc)
assert pat.search(t),npc
t=pat.sub(lambda m:m.group(1)+'['+', '.join(map(str,b))+']',t,1);open(p,'w').write(t);print(npc,b)

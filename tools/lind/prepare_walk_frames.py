#!/usr/bin/env python3
"""Install delivered NPC walk frames: 1 frame = 1 transparent RGBA PNG on the idle canvas size.
usage: prepare_walk_frames.py <src_dir_with_exec-*.png> [--write-bounds]
 - verifies RGBA, pads/crops (transparent edge only) to the idle canvas, writes <out>_01.png ...
 - prints/updates LindFieldContentBounds entries (alpha>16 bbox: [W,H,x,y,w,h])"""
import json,os,re,sys
from PIL import Image
import numpy as np
root=os.path.join(os.path.dirname(__file__),'..','..'); man=json.load(open(os.path.join(os.path.dirname(__file__),'walk_frames_manifest.json')))
src=sys.argv[1]; entries={}
for npc,c in man['npcs'].items():
    idle=Image.open(os.path.join(root,c['idle'])).convert('RGBA'); W,H=idle.size
    for n,pref in enumerate(c['frames'],1):
        f=[x for x in os.listdir(src) if x.startswith(pref)][0]; im=Image.open(os.path.join(src,f)).convert('RGBA')
        a=np.array(im)[...,3]
        if im.size[0]>W: assert a[:,W:].max()<=16,'would crop visible pixels (x)'
        if im.size[1]>H: assert a[H:,:].max()<=16,'would crop visible pixels (y)'
        canvas=Image.new('RGBA',(W,H),(0,0,0,0)); canvas.paste(im.crop((0,0,min(W,im.width),min(H,im.height))),(0,0))
        out=os.path.join(root,'%s_%02d.png'%(c['out'],n)); canvas.save(out,optimize=True)
        al=np.array(canvas)[...,3]>16; ys,xs=np.where(al)
        entries['%s_walk_%02d'%(npc,n)]=[W,H,int(xs.min()),int(ys.min()),int(xs.max()-xs.min()+1),int(ys.max()-ys.min()+1)]
        print(npc,n,f[:13],im.size,'->',(W,H),entries['%s_walk_%02d'%(npc,n)])
if '--write-bounds' in sys.argv:
    p=os.path.join(root,'js/field/lind-content-bounds.js'); s=open(p,encoding='utf-8').read()
    for k in list(entries):
        s=re.sub(r',?\n  "%s": \[[^\]]*\]'%k,'',s)
    add=''.join(',\n  "%s": [\n    %s\n  ]'%(k,',\n    '.join(map(str,v))) for k,v in entries.items())
    i=s.rindex('\n};'); s=s[:i]+add+s[i:]; open(p,'w',encoding='utf-8').write(s); print('bounds written',len(entries))

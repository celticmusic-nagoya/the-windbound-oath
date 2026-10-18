import numpy as np,json,hashlib
from PIL import Image
import cv2
from mos import NM
res={}
for ch in ['fiona','lou']:
    m=Image.open(f'{ch}_master.png');ma=np.array(m)
    for n in NM:
        im=Image.open(f'out/{ch}_{n}.png');a=np.array(im)
        d=(a!=ma).any(2);wt=np.load(f'out/wt_{ch}_{n}.npy') if n!='normal' else np.zeros(d.shape,bool)
        wd=cv2.dilate(wt.astype(np.uint8),np.ones((3,3),np.uint8))>0
        res[f'{ch}_{n}']=dict(mode=im.mode,size=im.size,same_size=im.size==m.size,alpha_identical=bool((a[...,3]==ma[...,3]).all()),
          alpha0_rgb_identical=bool((a[ma[...,3]==0][:,:3]==ma[ma[...,3]==0][:,:3]).all()),
          changed_px=int(d.sum()),changed_outside=int((d&~wd).sum()),
          bbox=(lambda ys,xs:[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())] if len(xs) else None)(*np.where(d)),
          sha=hashlib.sha256(open(f'out/{ch}_{n}.png','rb').read()).hexdigest()[:12])
json.dump(res,open('out/verify.json','w'),indent=1)
for k,v in res.items():print(k,v['mode'],v['same_size'],v['alpha_identical'],v['alpha0_rgb_identical'],v['changed_px'],v['changed_outside'],v['bbox'])

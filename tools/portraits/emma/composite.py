import numpy as np, cv2
from PIL import Image
exec(open('build.py').read().split("out={}")[0])
Wf=np.load('warped_final.npy')
Mp=np.dstack([M[:,:,:3]*(M[:,:,3:4]/255.),M[:,:,3:4]])
# smooth face oval (master coords)
m=np.zeros((H,W),np.float32)
cv2.ellipse(m,(600,335),(150,165),-15,0,360,1.0,-1)
m=cv2.GaussianBlur(m,(0,0),14); m=np.clip(m*1.6,0,1)
names=['normal','smile','angry','sad','surprised','worried','determined','relieved']
outs={}
for i,nm in enumerate(names):
    if i==0: outs[nm]=M.astype(np.uint8); continue
    w=Wf[i]; ca=w[:,:,3:4]/255.; crgb=w[:,:,:3]/np.maximum(ca,1e-3)
    mm=(m*(w[:,:,3]/255.))[:,:,None]
    rgb=M[:,:,:3]*(1-mm)+crgb*mm            # straight-alpha blend: outside the oval mm==0 -> exactly the master
    out=np.dstack([np.where(mm>0,np.clip(rgb,0,255),M[:,:,:3]),M[:,:,3:4]]).round().astype(np.uint8)
    out[:,:,:3][mm[:,:,0]==0]=M[:,:,:3][mm[:,:,0]==0].astype(np.uint8)
    outs[nm]=out
    Image.fromarray(out).save(f'cand_{i+1:02d}_{nm}.png')
Image.fromarray(M.astype(np.uint8)).save('cand_01_normal.png')
# contact sheet at native scale (face crop)
crop=lambda o:o[130:620,330:880,:3]*(o[130:620,330:880,3:4]/255.)+ (1-o[130:620,330:880,3:4]/255.)*60
tiles=[np.clip(crop(outs[n]),0,255).astype(np.uint8) for n in names]
Image.fromarray(np.vstack([np.hstack(tiles[:4]),np.hstack(tiles[4:])])).save('contact_composites.jpg',quality=90)
print('ok')

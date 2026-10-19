import numpy as np, cv2, json
from PIL import Image
M=np.array(Image.open('master_COPY.png')).astype(np.float32)
H,W=M.shape[:2]
al=json.load(open('align_sift.json'))
xs={'sheet1':(0,751,1312),'sheet2':(0,686,1312)}
def cellimg(nm):
    sheet='sheet1' if int(nm[1:])<=4 else 'sheet2'
    idx=int(nm[1:])-1; col=idx%2; row=(idx%4)//2
    A=np.array(Image.open(f'{sheet}_COPY_1312x1199.png'))
    y0,y1=(0,611) if row==0 else (611,1199)
    return A[y0:y1, xs[sheet][col]:xs[sheet][col+1]]
def prem_warp(C,T):
    C=C.astype(np.float32); a=C[:,:,3:4]/255.; P=np.dstack([C[:,:,:3]*a,C[:,:,3:4]])
    T=np.array(T,np.float32)
    w=cv2.warpAffine(P,T,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
    return w  # premultiplied rgb, alpha 0..255
def refine(C,T):
    # ECC translation+scale-free refinement on luminance of the stable (non-face) region: use affine
    w=prem_warp(C,T); aw=w[:,:,3]/255.; ref=M[:,:,3]/255.
    g=lambda P,a: cv2.cvtColor(np.clip(P[:,:,:3]/np.maximum(a[:,:,None],1e-3),0,255).astype(np.uint8),cv2.COLOR_RGB2GRAY)
    gm=g(M[:,:,:3]*(ref[:,:,None]),ref).astype(np.float32); gw=g(w,aw).astype(np.float32)
    mask=((aw>.99)&(ref>.99)).astype(np.uint8)
    # restrict to upper-head hair region (stable) to avoid face changes: y 0..330
    mask[330:]=0
    warp=np.eye(2,3,dtype=np.float32)
    try:
        cc,warp=cv2.findTransformECC(gm,gw,warp,cv2.MOTION_TRANSLATION,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,200,1e-6),mask,5)
    except Exception as e: print('ecc fail',e); return w,None
    w2=cv2.warpAffine(w,warp,(W,H),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
    return w2,warp
out={}
for i in range(1,9):
    nm=f'e{i:02d}'; w,wp=refine(cellimg(nm),al[nm]['T']); out[nm]=w
    print(nm,'ecc',None if wp is None else np.round(wp,3).tolist())
np.save('warped.npy',np.stack([out[f'e{i:02d}'] for i in range(1,9)]))
# difference vs master (premultiplied compare on opaque overlap)
mp=np.dstack([M[:,:,:3]*(M[:,:,3:4]/255.),M[:,:,3:4]])
diffs=[]
for i in range(1,9):
    w=out[f'e{i:02d}']; ov=((w[:,:,3]>250)&(M[:,:,3]>250))
    d=np.abs(w[:,:,:3]-mp[:,:,:3]).mean(2)*ov
    diffs.append(cv2.GaussianBlur(d,(0,0),2))
D=np.stack(diffs); np.save('diffs.npy',D)
for i,d in enumerate(D): 
    ys,xs_=np.nonzero(d>40); print('e%02d'%(i+1),'diff>40 px',len(ys),'bbox',(xs_.min(),ys.min(),xs_.max(),ys.max()) if len(ys) else None)

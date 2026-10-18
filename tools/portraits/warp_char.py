import cv2,numpy as np,json,os
from lib import *
CTX={'fiona':[(520,340,670,400),(640,250,700,335)],
     'lou':[(700,470,875,520),(695,520,800,610),(850,470,935,570)]}
SH={'fiona':['fiona_sheet_attach3.png','fiona_sheet_attach4.png'],'lou':['lou_sheet_attach5.png','lou_sheet_attach6.png']}
sift=cv2.SIFT_create(6000);bf=cv2.BFMatcher();info={}
os.makedirs('warp',exist_ok=True)
for ch in ['fiona','lou']:
    base=load(f'{ch}_master.png');H,W=base.shape[:2];gb=cv2.GaussianBlur(gray(base).astype(np.float32),(0,0),1)
    kb,db=sift.detectAndCompute(gray(base),None)
    mask=np.zeros((H,W),np.uint8)
    for x0,y0,x1,y1 in CTX[ch]:mask[y0:y1,x0:x1]=255
    for si,s in enumerate(SH[ch]):
        for pi,(p,o) in enumerate(panels(s)):
            kp,dp=sift.detectAndCompute(gray(p),None)
            mm=[a for a,b in bf.knnMatch(dp,db,k=2) if a.distance<0.75*b.distance]
            src=np.float32([kp[a.queryIdx].pt for a in mm]);dst=np.float32([kb[a.trainIdx].pt for a in mm])
            M,_=cv2.estimateAffinePartial2D(src,dst,ransacReprojThreshold=2.5)
            W0=cv2.warpAffine(p,M,(W,H),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
            gp=cv2.GaussianBlur(gray(W0).astype(np.float32),(0,0),1);wm=np.eye(2,3,dtype=np.float32)
            cc,wm=cv2.findTransformECC(gb,gp,wm,cv2.MOTION_AFFINE,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,300,1e-8),mask,5)
            h=lambda A:np.vstack([A,[0,0,1]])
            comb=(h(cv2.invertAffineTransform(M))@h(wm))[:2]
            Wf=cv2.warpAffine(p,comb,(W,H),flags=cv2.INTER_LANCZOS4|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
            k=f'{ch}_{si}{pi}';Image.fromarray(Wf).save(f'warp/{k}.png');info[k]=dict(sheet=s,panel=pi,cc=round(float(cc),4),M=comb.round(5).tolist());print(k,round(float(cc),3),np.hypot(comb[0,0],comb[0,1]).round(3))
json.dump(info,open('warp_info.json','w'),indent=1)

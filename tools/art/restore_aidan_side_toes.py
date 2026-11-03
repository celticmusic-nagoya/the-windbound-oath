#!/usr/bin/env python3
"""Recover only truncated toe pixels from the already-delivered sword-side sheets.

No new artwork: source registration was fitted on intact head/boot pixels.
Keep every previously visible pixel, the full canvas, scale and anchor unchanged.
Original side6 PNGs remain untouched. Requires Pillow, NumPy and SciPy.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_dilation,distance_transform_edt
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'img/field/characters/aidan/side6';OUT=BASE/'fix01'
# source crop / registered size / target origin reproduce existing registration;
# the larger source sample restores the toe across the old crop plane only.
CONFIG=[
 ('left',2,(443,125,800,896),(512,1104),(893,126),(840,1140,895,1230),893,False),
 ('left',5,(443,125,800,896),(512,1104),(893,126),(840,1140,895,1230),893,True),
 ('left',4,(1187,123,1535,898),(496,1104),(921,126),(810,1135,923,1230),921,True),
 ('right',1,(11,179,402,873),(622,1104),(733,126),(1353,1125,1410,1230),1355,False),
]
INPUT_SHA256 = {'docs/art/delivered/aidan_sword_20261013/sideR.png': '10ea1f0641448eb957fdabe15881391055b9ca1038f4fc5137006a35b28ff992', 'docs/art/delivered/aidan_sword_20261013/sideL.png': '3d0315b4550b1c1e3dabb471a303bfc244ef5f7754bfeeb9eaedd87b3d344f99', 'img/field/characters/aidan/side6/aidan_walk_left_02.png': '6454e74f31ead044ee2871c1b0748f9664e67016411cfb4becb680be8160f2be', 'img/field/characters/aidan/side6/aidan_walk_left_05.png': '65ccbf577b914701feec8ae0d785c12af7a6d993a0f39efdded2cc91bc9d4ced', 'img/field/characters/aidan/side6/aidan_walk_left_04.png': 'ce55f5fb4411744efdd7eb5b2a7bf5c4576cb50910067f6e7db47216057d5231', 'img/field/characters/aidan/side6/aidan_walk_right_01.png': 'd1174c5ab26c15d846c2ce906f4406078e2cf08ef7950159ccf7f6ac462876e2'}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def restore(cfg):
 side,n,box,size,origin,roi,cut,far=cfg;name=f'aidan_walk_{side}_{n:02}.png'
 original=BASE/name;sheet=ROOT/f'docs/art/delivered/aidan_sword_20261013/side{side[0].upper()}.png'
 old=Image.open(original).convert('RGBA');a=np.array(old);src=Image.open(sheet).convert('RGBA');x0,y0,x1,y1=roi
 sx=size[0]/(box[2]-box[0]);sy=size[1]/(box[3]-box[1])
 sample=(box[0]+(x0-origin[0])/sx,box[1]+(y0-origin[1])/sy,box[0]+(x1-origin[0])/sx,box[1]+(y1-origin[1])/sy)
 p=np.array(src.resize((x1-x0,y1-y0),Image.Resampling.LANCZOS,box=sample));existing=a[y0:y1,x0:x1]
 components,_=label(p[:,:,3]>16);touch=np.unique(components[existing[:,:,3]>80]);touch=touch[touch>0]
 mask=binary_dilation(np.isin(components,touch),iterations=2)&(p[:,:,3]>0)&(existing[:,:,3]==0)
 xx=np.arange(x0,x1)[None,:];mask &= xx<cut if side=='left' else xx>=cut
 if far:
  # Same adopted ART-08E far-leg rule, extended to recovered pixels only.
  rgb=p[:,:,:3].astype(int);mn=rgb.min(2);mx=rgb.max(2)
  tone=mask&~(rgb[:,:,1]>rgb[:,:,0]+4)&~((mn>170)&(mx-mn<60))
  px=p[tone,:3].astype(float);p[tone,:3]=np.clip((px*.85+px.mean(1,keepdims=True)*.15)*.66,0,255).astype(np.uint8)
 b=a.copy();b[y0:y1,x0:x1][mask]=p[mask]
 assert old.size==(2048,1280) and mask.any()
 assert np.array_equal(a[a[:,:,3]>0],b[a[:,:,3]>0])
 new=Image.fromarray(b);assert new.getbbox()[1::2]==old.getbbox()[1::2]
 yy,xx=np.unravel_index(np.argmax(distance_transform_edt(mask&(p[:,:,3]>180))),mask.shape)
 info={'original':str(original.relative_to(ROOT)),'original_sha256':sha(original),'sheet':str(sheet.relative_to(ROOT)),'sheet_sha256':sha(sheet),'source_crop':box,'registered_size':size,'origin':origin,'roi':roi,'cut':cut,'far_shading':far,'source_sample':sample,'added_pixels':int(mask.sum()),'before_bounds':old.getbbox(),'after_bounds':new.getbbox(),'existing_visible_pixels_unchanged':True,'probe_pixel':[int(x0+xx),int(y0+yy)],'probe_rgba':b[y0+yy,x0+xx].tolist()}
 return name,new,info

def main():
 for path,want in INPUT_SHA256.items():assert sha(ROOT/path)==want, f'input differs: {path}'
 OUT.mkdir(exist_ok=True);frames={}
 for cfg in CONFIG:
  name,image,info=restore(cfg);image.save(OUT/name,optimize=True);info['sha256']=sha(OUT/name);frames[name]=info;print(name,info['added_pixels'],'recovered pixels')
 manifest={'task':'AIDAN-SIDE-WALK-FIX01','status':'PROVISIONAL_ANDROID_QA','base_main':'12b1dca9433f6c2f2b69c2a63c097ad95fdc5e2b','method':'Registered extraction of existing source toe pixels only; no redraw; existing visible RGBA unchanged','formal_stride':72,'dev_comparison':{'stride':180,'rate':1},'dimensions':[2048,1280],'anchor':[1024,1230],'scale':0.0625,'frames':frames,'protected_original_side6_sha256':{p.name:sha(p) for p in sorted(BASE.glob('*.png'))}}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()

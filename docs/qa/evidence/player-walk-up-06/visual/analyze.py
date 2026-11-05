from pathlib import Path
import argparse,json,hashlib
from PIL import Image,ImageDraw
import numpy as np
from scipy import ndimage as ndi
p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--out',required=True);q=p.parse_args();r=Path(q.repo);out=Path(q.out);out.mkdir(parents=True,exist_ok=True)
b=r/'assets/candidates/player-walk-polish01'; paths={'formal03':r/'img/field/characters/aidan/aidan_walk_up_03.png','PR152':b/'up-05-pushoff-repair/aidan_walk_up_pushoff_candidate.png','PR153':b/'up-06-left-boot-outline/aidan_walk_up_pushoff_candidate_v2.png'}
arr={k:np.array(Image.open(v).convert('RGBA')) for k,v in paths.items()}; mask=np.array(Image.open(b/'up-03-image-edit-kit/proposed_mask.png'))>0;ext=np.array(Image.open(b/'up-06-left-boot-outline/mask_extension_px.png'))>0;added=np.array(Image.open(b/'up-06-left-boot-outline/edit_added_px.png'))>0
C=arr['PR153'];F=arr['formal03'];P=arr['PR152'];df=np.any(C!=F,2);dp=np.any(C!=P,2)
def bbox(m):
 yy,xx=np.where(m);return [int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())] if len(xx) else None
res={'files':{k:{'path':str(v.relative_to(r)),'sha256':hashlib.sha256(v.read_bytes()).hexdigest(),'size':list(Image.open(v).size),'mode':Image.open(v).mode} for k,v in paths.items()},'changed_vs_formal':int(df.sum()),'changed_vs_pr152':int(dp.sum()),'diff152_bbox_inclusive':bbox(dp),'original_mask_pixels':int(mask.sum()),'extension_pixels':int(ext.sum()),'extension_bbox_inclusive':bbox(ext),'extension_coords':[[int(x),int(y)] for y,x in zip(*np.where(ext))],'outside_mask_and_extension_diff':int((df&~(mask|ext)).sum()),'formal_opaque_gt200_outside_original_mask_changed':int((df&~mask&(F[:,:,3]>200)).sum()),'formal_alpha_at_extension_histogram':dict(zip(*[x.tolist() for x in np.unique(F[:,:,3][ext],return_counts=True)])),'outline_added_mask_pixels':int(added.sum()),'all_added_mask_changed_vs152':bool(dp[added].all()),'diff152_not_added':int((dp&~added).sum()),'all_diff152_alpha_new':np.unique(C[:,:,3][dp],return_counts=True)[0].tolist()}
res['holes']={}
for key,a in arr.items():
 res['holes'][key]={}
 for threshold in [24,128,200]:
  op=a[:,:,3]>threshold;holes=ndi.binary_fill_holes(op)&~op
  res['holes'][key][str(threshold)]={'global':int(holes.sum()),'original_mask':int((holes&mask).sum()),'extension':int((holes&ext).sum()),'leg_zone':int(holes[900:1240,900:1260].sum())}
 res['files'][key]['alpha128_bottom']=int(np.where((a[:,:,3]>128).any(1))[0].max())
# independent edge of contiguous boot component row scanned from1040
for key,a in arr.items():
 edges=[]
 for y in range(1015,1114):
  gap=np.flatnonzero(a[y,1040:1100,3]<=200);edges.append(int(1040+(gap[0] if len(gap) else 60)-1))
 res['files'][key]['boot_right_edges_1015_1113']=edges
 res['files'][key]['boot_closing25_max_notch']=int((ndi.minimum_filter1d(ndi.maximum_filter1d(np.array(edges),25),25)-edges).max())
(out/'metrics.json').write_text(json.dumps(res,indent=2))
# all originals/candidates at native crop magnification2 for edge/cloth assessment on black and white
for roi,name in [((960,920,1200,1235),'legs'),((1035,950,1150,1125),'outline-knee')]:
 w,h=roi[2]-roi[0],roi[3]-roi[1];plate=Image.new('RGB',(w*3*2,h*2*2+48),'#bbb');d=ImageDraw.Draw(plate)
 for j,bg in enumerate(['black','white']):
  for i,(key,a) in enumerate(arr.items()):
   im=Image.fromarray(a).crop(roi);base=Image.new('RGBA',im.size,bg);base.alpha_composite(im);base=base.convert('RGB').resize((w*2,h*2),Image.Resampling.NEAREST);plate.paste(base,(i*w*2,j*(h*2+24)+24));d.text((i*w*2+3,j*(h*2+24)+4),key+' / '+bg,fill='black')
 plate.save(out/f'own-{name}-black-white.png')
# field size128x80; also DPR2.625 native205? canvas336x210
plate=Image.new('RGB',(336*3,210*2+48),'#ccc');d=ImageDraw.Draw(plate)
for i,(key,a) in enumerate(arr.items()):
 for j,bg in enumerate(['black','white']):
  im=Image.fromarray(a).resize((336,210),Image.Resampling.LANCZOS);base=Image.new('RGBA',im.size,bg);base.alpha_composite(im);plate.paste(base.convert('RGB'),(i*336,j*234+24));d.text((i*336+2,j*234+4),key+' DPR2.625',fill='black')
plate.save(out/'own-fullcanvas-dpr2625.png')
print(json.dumps({k:v for k,v in res.items() if k not in ['files','extension_coords']},indent=2))

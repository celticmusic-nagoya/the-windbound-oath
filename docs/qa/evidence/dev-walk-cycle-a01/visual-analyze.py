from pathlib import Path
import hashlib,json,numpy as np
from PIL import Image,ImageDraw
import argparse
R=Path(__file__).resolve().parents[4]
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=Path('/tmp/dev-walk-cycle-a01-visual'));O=p.parse_args().out;O.mkdir(parents=True,exist_ok=True)
s=(R/'js/field/aidan-field-assets.js').read_text();m=json.JSONDecoder().raw_decode(s.split('const frames = ',1)[1])[0]
a={};meta=[]
for n in range(1,7):
 key=f'aidan_walk_down_{n:02}';p=R/m[key]['path'].split('?')[0];im=Image.open(p).convert('RGBA');v=np.array(im);a[n]=v
 feet={}
 cols={}
 for name,(x0,x1) in {'viewer_left':(970,1100),'viewer_right':(1100,1230)}.items():
  yy,xx=np.where(v[1100:1230,x0:x1,3]>200);feet[name]={'roi':[x0,1100,x1,1230],'bottom_y':int(yy.max()+1100),'baseline_gap':int(1229-yy.max()-1100)} if len(yy) else None
 for x in range(980,1221,10):
  ys=np.where(v[1050:1230,x,3]>200)[0]
  if len(ys):cols[str(x)]=int(1229-ys.max()-1050)
 meta.append({'column_baseline_gaps_alpha200':cols,'frame':n,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'screen_half_bottoms_alpha200_NOT_foot_specific':feet})
# Compare horizontal shifts using 1D vertical-gradient energy of torso/waist strip, integer offsets +/-30.
# This is robust matching evidence, not an actual physical center-of-mass measurement.
def composite(v):return v[:,:,:3].astype(float)*v[:,:,3:4]/255+(1-v[:,:,3:4]/255)*40
v={n:composite(x) for n,x in a.items()}
shifts={}
ref=v[4][600:880,850:1250]
for n in range(1,7):
 errors=[]
 for dx in range(-30,31):
  # Target image content shifted by dx relative to frame04, compare over same broad region.
  q=v[n][600:880,850+dx:1250+dx]
  errors.append((float(np.mean(np.abs(q-ref))),dx))
 best=min(errors);shifts[n]={'dx_relative_to04':best[1],'mae':best[0]}
# Changes in registered cape regions, including all pixels (clothes/alpha), fixed same coordinates.
# Computation is appearance difference, not a psychophysical flicker judgment.
rois={'cape_left':[620,650,960,1050],'cape_right':[1180,650,1600,1050],'waist':[850,600,1250,880],'boots':[950,950,1240,1230]}
rows=[]
for label,seq in [('six',[1,2,3,4,5,6]),('four',[1,5,2,6])]:
 for i,j in zip(seq,seq[1:]+seq[:1]):
  stats={}
  for key,(x0,y0,x1,y1) in rois.items():stats[key]=float(np.abs(v[i][y0:y1,x0:x1]-v[j][y0:y1,x0:x1]).mean())
  rows.append({'bank':label,'from':i,'to':j,'mae_0_255':stats})
summary={}
for label in ['six','four']:
 rr=[r for r in rows if r['bank']==label];summary[label]={key:{'mean_per_transition':float(np.mean([r['mae_0_255'][key] for r in rr])),'sum_per_cycle':float(sum(r['mae_0_255'][key] for r in rr)),'maximum_transition':float(max(r['mae_0_255'][key] for r in rr))} for key in rois}
result={'base':'e63780543d7ba1719a39a2f68b9924dc6d5b3933','images':meta,'torso_match':shifts,'difference_rois':rois,'transitions':rows,'summary':summary,'limits':'Broad screen-half bottoms may include a neighboring boot and are not anatomical-foot measurements; use declared native columns and visual plates. Pixel differences/alpha-bottom do not prove physical contact, support force, natural timing, or flicker perception. Cape includes nearby clothing. Wrap06to01 native pair is identical in both banks.'}
(O/'measurements.json').write_text(json.dumps(result,indent=2))
# Equal-registration strips; no images modified, only analysis composites.
canvas=Image.new('RGB',(1800,620),(40,46,42));d=ImageDraw.Draw(canvas)
for row,(label,seq) in enumerate([('six',[1,2,3,4,5,6]),('four',[1,5,2,6])]):
 for idx,n in enumerate(seq):
  im=Image.fromarray(a[n]);q=im.crop((800,840,1350,1240));q.thumbnail((285,230));canvas.paste(q,(idx*300+5,row*310+45),q);d.text((idx*300+10,row*310+10),f'{label} slot{idx+1}: PNG{n:02}',fill='white')
canvas.save(O/'six-vs-four-feet.png')
print(json.dumps({'feet':meta,'torso':shifts,'summary':summary},indent=2))

"""Read-only support-boot annotations/render maths; no production/candidate PNG writes."""
from pathlib import Path
import hashlib,json,math
import numpy as np
from PIL import Image,ImageDraw
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/cycle-a02-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import argparse
R=Path(__file__).resolve().parents[4]
ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=Path('/tmp/dev-walk-cycle-a02-support'));O=ap.parse_args().out;O.mkdir(parents=True,exist_ok=True)
s=(R/'js/field/aidan-field-assets.js').read_text();m=json.JSONDecoder().raw_decode(s.split('const frames = ',1)[1])[0]
# Manually declared visual boot ROIs. These are not automatic support-force estimators.
ANNOT={
1:{'roi':[1080,1110,1175,1230],'central_x':[1100,1150],'side':'viewer-right / anatomical-left inferred','phase':'left contact-like'},
5:{'roi':[1090,1110,1180,1230],'central_x':[1100,1170],'side':'viewer-right / anatomical-left inferred','phase':'left support/right passing-like'},
2:{'roi':[1015,1090,1100,1230],'central_x':[1040,1090],'side':'viewer-left / anatomical-right inferred','phase':'right heel-contact-like; NOT_PROVEN'},
6:{'roi':[1025,1100,1120,1230],'central_x':[1040,1100],'side':'viewer-left / anatomical-right inferred','phase':'right support/left passing-like'},
}
rows=[];images={}
for n,a in ANNOT.items():
 path=R/m[f'aidan_walk_down_{n:02}']['path'].split('?')[0];im=Image.open(path).convert('RGBA');v=np.array(im);images[n]=im;row={'frame':n,'source_path':str(path.relative_to(R)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**a,'thresholds':{}}
 x0,y0,x1,y1=a['roi'];cx0,cx1=a['central_x']
 for threshold in [128,200]:
  mask=v[y0:y1,x0:x1,3]>threshold;yy,xx=np.where(mask);maxrow=int(yy.max()+y0);cols=[]
  for x in range(cx0,cx1+1):
   ys=np.where(v[y0:y1,x,3]>threshold)[0]
   if len(ys):cols.append({'x':x,'bottom_edge_y':int(ys.max()+y0+1),'gap_native':int(1230-(ys.max()+y0+1))})
  median=float(np.median([r['gap_native'] for r in cols]));minimum=float(min(r['gap_native'] for r in cols));maximum=float(max(r['gap_native'] for r in cols))
  probe=min(cols,key=lambda z:(abs(z['gap_native']-median),abs(z['x']-(cx0+cx1)/2)))
  # Use actual max covered row, exclusive edge, projected to anchor ground_y1230.
  row['thresholds'][str(threshold)]={'roi_bottom_edge_y':maxrow+1,'roi_ground_gap_native':1230-(maxrow+1),'central_columns':cols,'central_gap_median_native':median,'central_gap_range_native':[minimum,maximum],'marker_native':[probe['x'],probe['bottom_edge_y']],'marker_gap_world':probe['gap_native']*.0625}
 rows.append(row)
# Exact quarter boundaries and wholeframe correction effects. Source shifts/waist are not animated modifications here.
edges=[];seq=[1,5,2,6]
for i,(na,nb) in enumerate(zip(seq,seq[1:]+seq[:1]),1):
 boundary=i/4;p=boundary%1
 for amplitude in [0,.375,1.5]:
  lift=amplitude*abs(math.sin(2*math.pi*p))
  for corr in [False,True]:
   ca=.5 if corr and na==6 else 0;cb=.5 if corr and nb==6 else 0
   e={'from':na,'to':nb,'phase':boundary,'bob_amplitude_world':amplitude,'foot06_shift_on':corr,'continuous_bob_lift_at_edge_world':lift,'wholeframe_transform_before_world':ca-lift,'wholeframe_transform_after_world':cb-lift,'wholeframe_transform_jump_world':cb-ca,'thresholds':{}}
   for t in ['128','200']:
    aa=next(r for r in rows if r['frame']==na)['thresholds'][t]['marker_gap_world'];bb=next(r for r in rows if r['frame']==nb)['thresholds'][t]['marker_gap_world']
    e['thresholds'][t]={'boot_gap_before_world':aa+lift-ca,'boot_gap_after_world':bb+lift-cb,'boot_gap_jump_world':bb-aa+ca-cb}
   edges.append(e)
# Same original boots on common registration/ground. Annotation pixels are comparisons only.
plate=Image.new('RGB',(1280,540),(40,46,42));d=ImageDraw.Draw(plate)
for idx,n in enumerate(seq):
 im=images[n];q=im.crop((960,1030,1240,1260));plate.paste(q,(idx*320+20,50),q);a=ANNOT[n];x0,y0,x1,y1=a['roi'];ox=idx*320+20-960;oy=50-1030
 d.rectangle((x0+ox,y0+oy,x1+ox,y1+oy),outline='#ff7790',width=2);d.line((idx*320,1230+oy,idx*320+319,1230+oy),fill='#ffe38e',width=1);d.text((idx*320+15,10),f'PNG{n:02}: {a["phase"][:24]}',fill='white')
 r=next(r for r in rows if r['frame']==n)
 for j,t in enumerate(['128','200']):
  z=r['thresholds'][t];px,py=z['marker_native'];color=['#75ffff','#72ff79'][j];d.line((px+ox-5,py+oy,px+ox+5,py+oy),fill=color,width=2);d.line((px+ox,py+oy-5,px+ox,py+oy+5),fill=color,width=2)
  d.text((idx*320+10,310+j*35),f'A>{t}: median gap{z["central_gap_median_native"]:g}px',fill=color)
 d.text((idx*320+10,410),a['side'][:35],fill='white')
d.text((10,485),'Native boot ROIs / ground_y1230; markers are alpha-contour probes, NOT physical contact proof.',fill='white');plate.save(O/'support-boot-rois.png')
p=np.linspace(0,1,1001);slots=(p*4).astype(int)%4
fig,axes=plt.subplots(2,2,figsize=(13,8),sharex=True,sharey=True)
for r,t in enumerate(['128','200']):
 for c,corr in enumerate([False,True]):
  ax=axes[r,c];base=np.array([next(z for z in rows if z['frame']==n)['thresholds'][t]['marker_gap_world'] for n in seq]);b=base[slots];shift=np.where(slots==3,.5,0) if corr else 0
  for amp,label in [(0,'bob OFF'),(.375,'bob25%'),(1.5,'bob100%')]:ax.plot(p,b+amp*np.abs(np.sin(2*np.pi*p))-shift,label=label)
  for x in [.25,.5,.75]:ax.axvline(x,color='gray',alpha=.4,linestyle=':')
  ax.axhline(0,color='black',linewidth=.8);ax.set_title(f'alpha>{t}, 06 +8native {"ON" if corr else "OFF"}');ax.set_ylabel('Registered contour gap (world)');ax.set_xlabel('Cycle phase: 01 / 05 / 02 / 06');ax.legend(fontsize=8)
fig.suptitle('Predicted support-boot contour gaps: mathematical render comparison, not force/contact proof');fig.tight_layout();fig.savefig(O/'predicted-foot-gap.png',dpi=150);plt.close(fig)
# Optional +8 shift changes waist/cape along with foot. Compare native same-coordinate texture ROIs.
def comp(im):
 v=np.array(im).astype(float);return v[:,:,:3]*v[:,:,3:4]/255+(1-v[:,:,3:4]/255)*40
shifted=Image.new('RGBA',images[6].size);shifted.alpha_composite(images[6],(0,8))
raw={n:comp(im) for n,im in images.items()};moved=comp(shifted);rois={'cape_left':[620,650,960,1050],'cape_right':[1180,650,1600,1050],'waist':[850,600,1250,880]};cloth=[]
for na,nb in zip(seq,seq[1:]+seq[:1]):
 for corr in [False,True]:
  va=moved if corr and na==6 else raw[na];vb=moved if corr and nb==6 else raw[nb];stats={}
  for k,(x0,y0,x1,y1) in rois.items():stats[k]=float(np.abs(va[y0:y1,x0:x1]-vb[y0:y1,x0:x1]).mean())
  cloth.append({'from':na,'to':nb,'foot06_shift_on':corr,'registered_mae_0_255':stats})
periods=[{'cycle_world':stride,'speed_world_s':300,'seconds':stride/300,'frame_ms':stride/300/4*1000,'max_bob_velocity_world_s':{str(amp):2*math.pi*amp/(stride/300) for amp in [0,.375,1.5]}} for stride in [90,75]]
result={'source_base':'e63780543d7ba1719a39a2f68b9924dc6d5b3933','sequence':seq,'anchor_ground_native':1230,'scale':.0625,'markers':rows,'render_edges':edges,'cloak_waist_offset_comparison':cloth,'periods':periods,'limits':['Manuallydeclared anatomical/support identities inferred frompaintings;02heelcontactnotproved.','Alpha markers probebootcontour only, not heel force or worldground.','Sameframe offset moveshead/waist/cape aswellasfoot;±.5worldcorrectionsteps remain at02to06/06to01.','Continuousbobisnot a per-frameconstant;off25/100percent alteramplitude, not period.','No originalassets, sharedsource, browserorproductionstate modified.']}
(O/'support-analysis.json').write_text(json.dumps(result,indent=2));print(json.dumps({'markers':[{k:v for k,v in x.items() if k!='thresholds'}|{'gaps':{t:z['central_gap_median_native'] for t,z in x['thresholds'].items()}} for x in rows],'periods':periods},indent=2))

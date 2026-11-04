"""Independent PR139 image checks and analysis comparisons; no repository writes."""
from pathlib import Path
import subprocess,json,hashlib,argparse,tempfile
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path,default=Path.cwd());ap.add_argument('--out',type=Path);args=ap.parse_args()
R=Path(subprocess.check_output(['git','-C',str(args.repo),'rev-parse','--show-toplevel'],text=True).strip());O=args.out or Path(tempfile.mkdtemp(prefix='ground01-independent-'));O.mkdir(parents=True,exist_ok=True)
REF='d15aa83ab73e77e505895bea3c89485d3a9254bd';P='assets/candidates/player-walk-polish01/ground-01-aidan-down-06/'
candidate_bytes=subprocess.check_output(['git','show',REF+':'+P+'aidan_walk_down_06_ground_candidate.png'],cwd=R);(O/'aidan_walk_down_06_ground_candidate.png').write_bytes(candidate_bytes)
oldp=R/'img/field/characters/aidan/aidan_walk_down_06.png';a=np.array(Image.open(oldp).convert('RGBA'));b=np.array(Image.open(O/'aidan_walk_down_06_ground_candidate.png').convert('RGBA'));diff=(a!=b).any(2);yy,xx=np.where(diff)
mask_bytes=subprocess.check_output(['git','show',REF+':'+P+'edit_mask.png'],cwd=R);(O/'edit_mask.png').write_bytes(mask_bytes);mask=np.array(Image.open(O/'edit_mask.png').convert('L'))>0
s=(R/'js/field/aidan-field-assets.js').read_text();data=json.JSONDecoder().raw_decode(s.split('const frames = ',1)[1])[0]
ims={n:Image.open(R/data[f'aidan_walk_down_{n:02}']['path'].split('?')[0]).convert('RGBA') for n in [1,5,2,6]};ims['candidate']=Image.fromarray(b)
probes={1:([1080,1110,1175,1230],[1100,1150]),5:([1090,1110,1180,1230],[1100,1170]),2:([1015,1090,1100,1230],[1040,1090]),6:([1025,1100,1120,1230],[1040,1100])}
measure=[]
for name,im in ims.items():
 n=6 if name=='candidate' else name;roi,cx=probes[n];v=np.array(im);x0,y0,x1,y1=roi;row={'frame':name,'roi':roi,'central_x':cx,'thresholds':{}}
 for threshold in [128,200]:
  col=[]
  for x in range(cx[0],cx[1]+1):
   ys=np.where(v[y0:y1,x,3]>threshold)[0]
   if len(ys):col.append({'x':x,'edge_y':int(ys.max()+y0+1),'gap':int(1230-(ys.max()+y0+1))})
  row['thresholds'][str(threshold)]={'median_gap_native':float(np.median([c['gap'] for c in col])),'min_gap_native':min(c['gap'] for c in col),'max_gap_native':max(c['gap'] for c in col),'columns':col}
 measure.append(row)
# Independent lower boot rigid-translation and edit/alpha checks.
components={}
for t in [0,128,200]:
 components[str(t)]={}
 for k,v in [('original',a),('candidate',b)]:
  labs,n=label(v[:,:,3]>t,np.ones((3,3)));sizes=np.bincount(labs.ravel())[1:];components[str(t)][k]={'components':int(n),'components_ge16px':int((sizes>=16).sum())}
checks={'pr139_head':subprocess.check_output(['git','rev-parse',REF],cwd=R,text=True).strip(),'original_sha256':hashlib.sha256(oldp.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(candidate_bytes).hexdigest(),'source_size':list(ims[6].size),'candidate_size':list(ims['candidate'].size),'mode_source':Image.open(oldp).mode,'mode_candidate':Image.open(O/'aidan_walk_down_06_ground_candidate.png').mode,'changed_pixels':int(diff.sum()),'changed_bbox':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],'changes_outside_supplied_mask':int((diff&~mask).sum()),'changes_y_lt1062':int(diff[:1062].sum()),'changes_x_ge1126':int(diff[:,1126:].sum()),'lower_boot_core_roi_target':[1000,1180,1110,1225],'lower_boot_core_shift7_mismatches':int((b[1180:1225,1000:1110]!=a[1173:1218,1000:1110]).any(2).sum()),'alpha_bbox_source':list(ims[6].getbbox()),'alpha_bbox_candidate':list(ims['candidate'].getbbox()),'below_anchor_alpha_nonzero':int((b[1230:,:,3]>0).sum()),'below_anchor_alpha_max':int(b[1230:,:,3].max()),'below_anchor_alpha_gt128':int((b[1230:,:,3]>128).sum()),'connected_components':components}
assert checks['mode_source']==checks['mode_candidate']=='RGBA' and checks['source_size']==checks['candidate_size']==[2048,1280]
assert checks['changed_pixels']==16651 and checks['changes_outside_supplied_mask']==0 and checks['changes_y_lt1062']==0 and checks['lower_boot_core_shift7_mismatches']==0
# Same-register cape and waist ROIs end before edited row; all pairwise differences exactly unchanged.
def comp(im):
 v=np.array(im).astype(float);return v[:,:,:3]*v[:,:,3:4]/255+(1-v[:,:,3:4]/255)*40
vs={n:comp(im) for n,im in ims.items()};rois={'cape_left':[620,650,960,1050],'cape_right':[1180,650,1600,1050],'waist':[850,600,1250,880]};trans=[]
for mode,seq in [('original',[1,5,2,6]),('candidate',[1,5,2,'candidate'])]:
 for na,nb in zip(seq,seq[1:]+seq[:1]):
  stats={}
  for key,(x0,y0,x1,y1) in rois.items():stats[key]=float(np.abs(vs[na][y0:y1,x0:x1]-vs[nb][y0:y1,x0:x1]).mean())
  trans.append({'mode':mode,'from':na,'to':nb,'roi_mae_0_255':stats})
# Full/natural native source frames on fixed black/white compare backgrounds; no deformations.
plate=Image.new('RGB',(2048,1400),(38,44,39));dr=ImageDraw.Draw(plate)
for row,(lab,seq) in enumerate([('original',[1,5,2,6]),('candidate',[1,5,2,'candidate'])]):
 for i,n in enumerate(seq):
  im=ims[n];q=im.crop((960,1030,1240,1260));plate.paste(q,(i*512+50,row*360+45),q);dr.line((i*512+20,row*360+245,i*512+490,row*360+245),fill='#ffe38a',width=1);dr.text((i*512+20,row*360+12),f'{lab}: PNG{n}',fill='white')
# Actualscale0.0625 thumbnails atsameground and gameplaypixelcount, enlarged separately only for view.
for row,mode in enumerate(['original','candidate']):
 for i,n in enumerate([1,5,2,6 if mode=='original' else 'candidate']):
  for dpi,xoff in [(1,20),(2.625,170)]:
   im=ims[n].resize((round(128*dpi),round(80*dpi)),Image.Resampling.LANCZOS);x=i*512+xoff;y=790+row*280;plate.paste(im,(x,y),im);dr.text((x,y-18),f'{mode} DPR{dpi}',fill='white')
plate.save(O/'own-cycle-native-game.png')
#2→06→1 full-body, register/scaleunchanged toview waist/cloth and the localized foot variation.
cv=Image.new('RGB',(1800,720),(45,51,45));draw=ImageDraw.Draw(cv)
for i,n in enumerate([2,6,'candidate',1]):
 q=ims[n].copy();q.thumbnail((430,630));cv.paste(q,(i*450+10,35),q);draw.text((i*450+10,10),str(n),fill='white')
cv.save(O/'own-wrap-fullbody.png')
# Transparency/edge comparison: source andcandidate foot crop same register, whiteandblack.
cv=Image.new('RGB',(1000,680));draw=ImageDraw.Draw(cv)
for r,bg in enumerate([(0,0,0),(255,255,255)]):
 for c,n in enumerate([6,'candidate']):
  tile=Image.new('RGBA',(500,340),bg+(255,));im=ims[n].crop((970,1030,1150,1245)).resize((270,323),Image.Resampling.NEAREST);tile.alpha_composite(im,(110,10));cv.paste(tile.convert('RGB'),(c*500,r*340));draw.text((c*500+8,r*340+8),f'{n}',fill=(160,80,80))
cv.save(O/'own-alpha-edges.png')
result={'checks':checks,'support_boot_probes':measure,'registered_upper_body_transition_rois':rois,'transitions':trans,'limits':['Independent static/native/gameplay-scale imagecomparison; no browserorphysicalAndroid.','Alpha-contour improvement isnotheel-force/groundcontactproof.','Upperbody/waist/cape pixelsidenticalwithin06; originalcrossframeposechangespersist.','Sourcepixelrowbelowanchorsemi-transparentfringeisretained/translated, notentirelyabsent.']}
(O/'independent-image-metrics.json').write_text(json.dumps(result,indent=2));print(json.dumps({'checks':checks,'support_medians':[(r['frame'],{k:v['median_gap_native'] for k,v in r['thresholds'].items()}) for r in measure],'transitions':trans},indent=2))

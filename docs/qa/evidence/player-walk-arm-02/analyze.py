"""Independent read-only A/B/C static image audit for PR144; no author correlation or flow."""
import argparse,json,hashlib,subprocess,tempfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path,default=Path.cwd());ap.add_argument('--out',type=Path);args=ap.parse_args();R=Path(subprocess.check_output(['git','-C',str(args.repo),'rev-parse','--show-toplevel'],text=True).strip());O=args.out or Path(tempfile.mkdtemp(prefix='arm02-independent-'));O.mkdir(parents=True,exist_ok=True)
A=R/'img/field/characters/aidan';B=R/'assets/candidates/player-walk-polish01/arm-01-aidan-down';C=R/'assets/candidates/player-walk-polish01/arm-02-aidan-down';seq=[1,5,2,6]
prod={n:Image.open(A/(f'aidan_walk_down_{n:02}.png' if n!=6 else 'down4/aidan_walk_down_06_ground.png')).convert('RGBA') for n in seq};b142={**prod,**{n:Image.open(B/f'aidan_walk_down_{n:02}_arm_candidate.png').convert('RGBA') for n in [1,2]}};c144={**prod,**{n:Image.open(C/f'aidan_walk_down_{n:02}_arm02_candidate.png').convert('RGBA') for n in [5,2]}};checks=[]
for n in [5,2]:
 p=A/f'aidan_walk_down_{n:02}.png';q=C/f'aidan_walk_down_{n:02}_arm02_candidate.png';a=np.array(prod[n]);b=np.array(c144[n]);df=(a!=b).any(2);yy,xx=np.where(df);core=np.array(Image.open(C/f'edit_core_{n:02}.png').convert('L'))>0;env=np.array(Image.open(C/f'edit_envelope_{n:02}.png').convert('L'))>0
 z={'frame':n,'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'size':list(Image.open(q).size),'mode':Image.open(q).mode,'changed_pixels':int(df.sum()),'changed_bbox_exclusive':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],'outside_core':int((df&~core).sum()),'outside_provided_envelope':int((df&~env).sum()),'provided_envelope_vs_independent_dilation3_diff':int((env!=ndi.binary_dilation(core,iterations=3)).sum()),'outside_independent_core_dilation3':int((df&~ndi.binary_dilation(core,iterations=3)).sum()),'changes_y_lt560':int(df[:560].sum()),'changes_y_ge870':int(df[870:].sum()),'changes_x_lt1150':int(df[:,:1150].sum()),'alpha_changed_pixels':int((a[:,:,3]!=b[:,:,3]).sum()),'alpha_bbox_source':prod[n].getbbox(),'alpha_bbox_candidate':c144[n].getbbox()}
 for label,v in [('source',a),('candidate',b)]:
  m=v[:,:,3]>=200;z['enclosed_holes_'+label]=int((ndi.binary_fill_holes(m)&~m).sum())
 assert z['outside_independent_core_dilation3']==z['outside_provided_envelope']==z['changes_y_lt560']==z['changes_y_ge870']==z['changes_x_lt1150']==0
 checks.append(z)
input_locks=[]
for n in seq:
 p='img/field/characters/aidan/'+(f'aidan_walk_down_{n:02}.png' if n!=6 else 'down4/aidan_walk_down_06_ground.png');baseline=subprocess.check_output(['git','show','74d0401:'+p],cwd=R);current=(R/p).read_bytes();assert baseline==current;input_locks.append({'frame':n,'path':p,'sha256':hashlib.sha256(current).hexdigest(),'main74d0401_identical':True})
for n in [1,2]:
 p='assets/candidates/player-walk-polish01/arm-01-aidan-down/'+f'aidan_walk_down_{n:02}_arm_candidate.png';assert (R/p).read_bytes()==subprocess.check_output(['git','show','01511ee1a8f0b198ef185900b2c0ec010ac20262:'+p],cwd=R)
raw2=np.array(prod[2]);raw6=np.array(prod[6]);c5=np.array(c144[5]);c2=np.array(c144[2]);donor={'C05_glove_roi':[1270,780,1310,805],'C05_vs_A02_shift_minus1_minus1_different_pixels':int((c5[780:805,1270:1310]!=raw2[781:806,1271:1311]).any(2).sum()),'C02_glove_roi':[1290,745,1320,780],'C02_vs_A06_shift7_9_different_pixels':int((c2[745:780,1290:1320]!=raw6[736:771,1283:1313]).any(2).sum())}
def comp(im):
 a=np.array(im).astype(float);return a[:,:,:3]*a[:,:,3:4]/255+(1-a[:,:,3:4]/255)*45
rois={'right_arm_protected':[840,560,1000,800],'left_arm_and_lining':[1200,570,1390,860],'left_glove_region':[1240,710,1360,825],'inner_cape_white_lining':[1300,740,1390,855],'chest_protected':[760,300,1340,500]};trans=[]
for name,bank in [('A',prod),('B',b142),('C',c144)]:
 v={n:comp(im) for n,im in bank.items()}
 for na,nb in zip(seq,seq[1:]+seq[:1]):trans.append({'mode':name,'from':na,'to':nb,'roi_mae_0_255':{k:float(np.abs(v[na][y0:y1,x0:x1]-v[nb][y0:y1,x0:x1]).mean()) for k,(x0,y0,x1,y1) in rois.items()}})
plate=Image.new('RGB',(1680,1740),(43,50,44));draw=ImageDraw.Draw(plate)
for row,(name,bank) in enumerate([('A',prod),('B',b142),('C',c144)]):
 for i,n in enumerate(seq):
  q=bank[n].crop((1130,490,1430,890)).resize((375,500),Image.Resampling.NEAREST);plate.paste(q,(i*420+10,row*580+35),q);draw.text((i*420+10,row*580+8),f'{name} PNG{n:02}',fill='white')
plate.save(O/'own-cycle-arms-ABC.png')
plate=Image.new('RGB',(2048,960),(43,50,44));draw=ImageDraw.Draw(plate)
for row,(name,bank) in enumerate([('A',prod),('B',b142),('C',c144)]):
 for i,n in enumerate(seq):
  for dpi,xoff in [(1,20),(2.625,170)]:
   q=bank[n].resize((round(128*dpi),round(80*dpi)),Image.Resampling.LANCZOS);x=i*512+xoff;y=40+row*310;plate.paste(q,(x,y),q);draw.text((x,y-18),f'{name}{n:02} DPR{dpi}',fill='white')
plate.save(O/'own-game-scale-ABC.png')
# Highlight new05cuff/liningpatch; exactdifference, notnewcharacterart.
plate=Image.new('RGB',(1040,600),(43,50,44));draw=ImageDraw.Draw(plate)
for col,(name,im) in enumerate([('A05',prod[5]),('C05',c144[5])]):
 q=im.crop((1200,700,1370,870)).resize((510,510),Image.Resampling.NEAREST);plate.paste(q,(col*520,35),q);draw.text((col*520+6,8),name,fill='white')
plate.save(O/'own-05-cuff-wrinkle.png')
# Explicit before/after boundaryplates required for each edge, A/B/C at same registration.
for na,nb in zip(seq,seq[1:]+seq[:1]):
 plate=Image.new('RGB',(1280,1200),(43,50,44));draw=ImageDraw.Draw(plate)
 for row,(name,bank) in enumerate([('A production',prod),('B PR142',b142),('C PR144',c144)]):
  for col,n in enumerate([na,nb]):
   q=bank[n].crop((810,520,1430,880));plate.paste(q,(col*640+10,row*400+30),q);draw.text((col*640+12,row*400+6),f'{name}: PNG{n:02} / edge {na:02}->{nb:02}',fill='white')
 plate.save(O/f'own-edge-{na:02}-{nb:02}-ABC.png')
result={'PR144_fixed_head':'95e5563032095790e7a6887c74fa466f44a0bead','sequence':seq,'checks':checks,'production_locks':input_locks,'B142_inputs_unchanged':True,'C01_and_C06_reference_same_production':True,'donor_identity':donor,'transition_rois':rois,'transitions':trans,'limits':['ROIappearancechange isnot handtrajectory/naturalnessscore.','Fourpointnegativecorrelation doesnotprove3Darmphase.','StaticresamplingDPRplates are notactualAndroidscreens.','Actualrootcapturechronologicalinspectionrecordedseparately.','No art/source/runtime changes bythisreviewer.']}
(O/'independent-arm02-metrics.json').write_text(json.dumps(result,indent=2));print(json.dumps({'checks':checks,'donor':donor,'transitions':trans},indent=2))

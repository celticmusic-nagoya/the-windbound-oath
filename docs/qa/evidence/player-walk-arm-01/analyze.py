"""Independent read-only PR142 image scope/transition checks, without author optical-flow/correlation."""
import argparse,json,hashlib,subprocess,tempfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path,default=Path.cwd());ap.add_argument('--out',type=Path);args=ap.parse_args();R=Path(subprocess.check_output(['git','-C',str(args.repo),'rev-parse','--show-toplevel'],text=True).strip());O=args.out or Path(tempfile.mkdtemp(prefix='arm01-independent-'));O.mkdir(parents=True,exist_ok=True)
C=R/'assets/candidates/player-walk-polish01/arm-01-aidan-down';A=R/'img/field/characters/aidan';seq=[1,5,2,6];original={n:Image.open(A/(f'aidan_walk_down_{n:02}.png' if n!=6 else 'down4/aidan_walk_down_06_ground.png')).convert('RGBA') for n in seq};candidate={**original,**{n:Image.open(C/f'aidan_walk_down_{n:02}_arm_candidate.png').convert('RGBA') for n in [1,2]}};checks=[]
for n in [1,2]:
 p=A/f'aidan_walk_down_{n:02}.png';q=C/f'aidan_walk_down_{n:02}_arm_candidate.png';a=np.array(original[n]);b=np.array(candidate[n]);diff=(a!=b).any(2);yy,xx=np.where(diff);mask=np.array(Image.open(C/f'edit_mask_{n:02}.png').convert('L'))>0;allowed=ndi.binary_dilation(mask,iterations=3)
 row={'frame':n,'original_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'size_source':list(Image.open(p).size),'size_candidate':list(Image.open(q).size),'mode_source':Image.open(p).mode,'mode_candidate':Image.open(q).mode,'changed_pixels':int(diff.sum()),'bbox_exclusive':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],'outside_raw_core_mask':int((diff&~mask).sum()),'outside_documented_3px_feather_envelope':int((diff&~allowed).sum()),'heads_lt560_changes':int(diff[:560].sum()),'legs_ge870_changes':int(diff[870:].sum()),'screen_left_and_central_x_lt1150_changes':int(diff[:,:1150].sum()),'alpha_changed_pixels':int((a[:,:,3]!=b[:,:,3]).sum()),'alpha_bounds_source':original[n].getbbox(),'alpha_bounds_candidate':candidate[n].getbbox()}
 for name,v in [('source',a),('candidate',b)]:
  m=v[:,:,3]>=200;row['closed_alpha_hole_pixels_'+name]=int((ndi.binary_fill_holes(m)&~m).sum())
 assert row['outside_documented_3px_feather_envelope']==row['heads_lt560_changes']==row['legs_ge870_changes']==row['screen_left_and_central_x_lt1150_changes']==0
 checks.append(row)
production_input_checks=[]
for n in seq:
 rel='img/field/characters/aidan/'+(f'aidan_walk_down_{n:02}.png' if n!=6 else 'down4/aidan_walk_down_06_ground.png')
 src=R/rel;baseline=subprocess.check_output(['git','show','74d0401:'+rel],cwd=R);current=src.read_bytes();assert current==baseline
 production_input_checks.append({'frame':n,'path':rel,'sha256':hashlib.sha256(current).hexdigest(),'main74d0401_equal':True})
# Exact donor glove identity within separately declared interior patches.
c1=np.array(candidate[1]);c2=np.array(candidate[2]);d2=np.array(original[2]);d6=np.array(original[6]);donor_checks={'candidate01_glove_roi':[1270,750,1320,800],'candidate01_vs_source02_shift_2_minus5_mismatches':int((c1[750:800,1270:1320]!=d2[755:805,1268:1318]).any(2).sum()),'candidate02_glove_roi':[1274,730,1342,793],'candidate02_vs_production06_shift_7_9_mismatches':int((c2[730:793,1274:1342]!=d6[721:784,1267:1335]).any(2).sum())}
def comp(im):
 a=np.array(im).astype(float);return a[:,:,:3]*a[:,:,3:4]/255+(1-a[:,:,3:4]/255)*45
rois={'right_arm_protected':[840,560,1000,800],'left_arm_and_lining':[1200,570,1390,860],'left_glove_region':[1240,710,1360,825],'inner_cape_white_lining':[1300,740,1390,855],'chest_protected':[760,300,1340,500]};trans=[]
for mode,bank in [('production',original),('candidate',candidate)]:
 vs={n:comp(im) for n,im in bank.items()}
 for na,nb in zip(seq,seq[1:]+seq[:1]):
  scores={k:float(np.abs(vs[na][y0:y1,x0:x1]-vs[nb][y0:y1,x0:x1]).mean()) for k,(x0,y0,x1,y1) in rois.items()};trans.append({'mode':mode,'from':na,'to':nb,'registered_rgb_mae_0_255':scores})
# Samecamera, equalregistered analysisfullcycle and armscrop. No candidate/originalfiles modified.
plate=Image.new('RGB',(1680,1200),(44,51,45));draw=ImageDraw.Draw(plate)
for row,(lab,bank) in enumerate([('production',original),('candidate',candidate)]):
 for i,n in enumerate(seq):
  q=bank[n].crop((1130,490,1430,890)).resize((375,500),Image.Resampling.NEAREST);plate.paste(q,(i*420+10,row*600+35),q);draw.text((i*420+10,row*600+8),f'{lab} PNG{n:02}',fill='white')
plate.save(O/'own-cycle-arms.png')
plate=Image.new('RGB',(1800,690),(44,51,45));draw=ImageDraw.Draw(plate)
for i,(lab,im) in enumerate([('06production',original[6]),('01production',original[1]),('01candidate',candidate[1]),('05production',original[5])]):
 q=im.copy();q.thumbnail((430,600));plate.paste(q,(i*450+5,35),q);draw.text((i*450+5,8),lab,fill='white')
plate.save(O/'own-wrap-06-01-05.png')
# Originalcanvas atprodscale.0625, displayphysicalpixelcountillustrationDPR1/2.625, notactualbrowsercapture.
plate=Image.new('RGB',(2048,650),(44,51,45));draw=ImageDraw.Draw(plate)
for row,(lab,bank) in enumerate([('production',original),('candidate',candidate)]):
 for i,n in enumerate(seq):
  for dpi,xoff in [(1,20),(2.625,170)]:
   q=bank[n].resize((round(128*dpi),round(80*dpi)),Image.Resampling.LANCZOS);x=i*512+xoff;y=40+row*300;plate.paste(q,(x,y),q);draw.text((x,y-18),f'{lab}{n:02} DPR{dpi}',fill='white')
plate.save(O/'own-game-scale.png')
result={'pr142_head':'01511ee1a8f0b198ef185900b2c0ec010ac20262','base_main':'74d04011','sequence':seq,'checks':checks,'production_input_checks':production_input_checks,'donor_identity':donor_checks,'transition_rois':rois,'transitions':trans,'limitations':['RegisteredROIappearancechange isnot anatomicalhandtrackingornaturalnessscore.','Four manualsamples andnegativecorrelationcannotestablishphysicalarmphase or3Ddepth.','Donor02toshifted01 and06toshifted02 includeinnercapematerial aswellasarm.','No browser/actualAndroid bythisreviewer.','No original/candidate PNG orsourcefileedit.']}
(O/'independent-arm-metrics.json').write_text(json.dumps(result,indent=2));print(json.dumps({'checks':checks,'donor':donor_checks,'transitions':trans},indent=2))

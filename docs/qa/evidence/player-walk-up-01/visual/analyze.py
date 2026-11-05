"""Independent source/pose inventory for PR147 up bank proposal; read-only art and source."""
import argparse,json,hashlib,subprocess,tempfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path,default=Path.cwd());ap.add_argument('--out',type=Path);args=ap.parse_args();R=Path(subprocess.check_output(['git','-C',str(args.repo),'rev-parse','--show-toplevel'],text=True).strip());O=args.out or Path(tempfile.mkdtemp(prefix='up01-independent-'));O.mkdir(parents=True,exist_ok=True)
s=(R/'js/field/aidan-field-assets.js').read_text();meta=json.JSONDecoder().raw_decode(s.split('const frames = ',1)[1])[0]
ims={};rows=[]
def maxrun(a):
 longest=0;n=0
 for v in a:
  n=n+1 if v else 0;longest=max(longest,n)
 return longest
for n in range(1,7):
 key=f'aidan_walk_up_{n:02}';m=meta[key];p=R/m['path'].split('?')[0];im=Image.open(p);assert im.mode=='RGBA' and im.size==(2048,1280);v=np.array(im);ims[n]=im.convert('RGBA');diffmain=p.read_bytes()!=subprocess.check_output(['git','show','6e28466:'+str(p.relative_to(R))],cwd=R)
 a=v[900:1240,900:1260,3];cuts=[]
 for y in range(1,a.shape[0]-1):
  for dy in [-1,1]:
   q=(a[y]>=128)&(a[y+dy]==0);run=maxrun(q)
   if run>=20:cuts.append({'axis':'horizontal','y':900+y,'neighbor':dy,'run':run})
 for x in range(1,a.shape[1]-1):
  for dx in [-1,1]:
   q=(a[:,x]>=128)&(a[:,x+dx]==0);run=maxrun(q)
   if run>=20:cuts.append({'axis':'vertical','x':900+x,'neighbor':dx,'run':run})
 row={'frame':n,'key':key,'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'same_bytes_as_main6e28466':not diffmain,'size':list(im.size),'anchor':m['anchor'],'scale':m['scale'],'alpha_bounds':im.getchannel('A').getbbox(),'alpha128_lowest_row':int(np.where((v[:,:,3]>128).any(1))[0].max()),'outer_edge_alpha_nonzero':int((v[0,:,3]>0).sum()+(v[-1,:,3]>0).sum()+(v[:,0,3]>0).sum()+(v[:,-1,3]>0).sum()),'hard_alpha128_to_zero_runs_ge20_in_legs':cuts}
 assert not diffmain and m['anchor']==[1024,1230] and m['scale']==.0625;rows.append(row)
def comp(im):
 a=np.array(im).astype(float);return a[:,:,:3]*a[:,:,3:4]/255+(1-a[:,:,3:4]/255)*45
v={n:comp(im) for n,im in ims.items()}
# FFT phase-only registration on upperbody crop; integer and response, not physical pelvis tracking.
ref=v[1][150:600,700:1400].mean(2);ref=(ref-ref.mean())*np.outer(np.hanning(ref.shape[0]),np.hanning(ref.shape[1]));fref=np.fft.fft2(ref);shifts={}
for n in range(1,7):
 q=v[n][150:600,700:1400].mean(2);q=(q-q.mean())*np.outer(np.hanning(q.shape[0]),np.hanning(q.shape[1]));c=fref*np.conj(np.fft.fft2(q));c/=np.maximum(np.abs(c),1e-9);surface=np.abs(np.fft.ifft2(c));dy,dx=np.unravel_index(surface.argmax(),surface.shape);dy=dy-surface.shape[0] if dy>surface.shape[0]/2 else dy;dx=dx-surface.shape[1] if dx>surface.shape[1]/2 else dx
 shifts[n]={'integer_dx_to_align_to01':int(dx),'integer_dy_to_align_to01':int(dy),'peak':float(surface.max())}
rois={'upper_body':[700,150,1400,600],'waist_cape':[700,600,1520,960],'legs':[900,900,1260,1240]};edges=[]
for bank,seq in [('current6',[1,2,3,4,5,6]),('trial4',[3,4,1,6])]:
 for na,nb in zip(seq,seq[1:]+seq[:1]):edges.append({'bank':bank,'from':na,'to':nb,'registered_mae_0_255':{k:float(np.abs(v[na][y0:y1,x0:x1]-v[nb][y0:y1,x0:x1]).mean()) for k,(x0,y0,x1,y1) in rois.items()}})
# Four specifically proposed edges, same registration/nativepixels, body and legs.
for na,nb in [(3,4),(4,1),(1,6),(6,3)]:
 plate=Image.new('RGB',(1320,800),(42,48,43));d=ImageDraw.Draw(plate)
 for col,n in enumerate([na,nb]):
  q=ims[n].crop((800,850,1280,1240));plate.paste(q,(col*660+80,50),q);d.text((col*660+10,10),f'up{n:02} native: edge{na:02}->{nb:02}',fill='white');d.line((col*660+40,430,col*660+620,430),fill='#dfca7a')
  body=ims[n].copy();body.thumbnail((450,280));plate.paste(body,(col*660+100,480),body)
 plate.save(O/f'own-up-edge-{na:02}-{nb:02}.png')
plate=Image.new('RGB',(2048,650),(42,48,43));d=ImageDraw.Draw(plate)
for row,(lab,seq) in enumerate([('current6',[1,2,3,4,5,6]),('trial4',[3,4,1,6])]):
 for i,n in enumerate(seq):
  x=i*330;y=row*300;im=ims[n].resize((128,80),Image.Resampling.LANCZOS);plate.paste(im,(x+10,y+40),im);big=ims[n].resize((336,210),Image.Resampling.LANCZOS);plate.paste(big,(x+10,y+130),big);d.text((x+6,y+8),f'{lab} PNG{n:02}: scale1 andDPR2.625',fill='white')
# SeparateDPRillustration below canoverlap neighboringcells; require no clipped context: nativeplates areprimary.
# Keep compactscale1-only strip unambiguously spaced.
small=Image.new('RGB',(6*160,2*130),(42,48,43));ds=ImageDraw.Draw(small)
for row,(lab,seq) in enumerate([('current6',[1,2,3,4,5,6]),('trial4',[3,4,1,6])]):
 for i,n in enumerate(seq):
  im=ims[n].resize((128,80),Image.Resampling.LANCZOS);small.paste(im,(i*160+10,row*130+30),im);ds.text((i*160+5,row*130+5),f'{lab} {n:02}',fill='white')
small.save(O/'own-up-fieldscale.png')
# Asecondphasecorrelationform withoutHann reproduces broad sourcealignment but responsesmay beweak.
# Explicitlyrecord weak/signedresponses instead of treating them as pelvisgroundtruth.
alignment={};pre={}
for n,im in ims.items():
 aa=np.array(im).astype(np.float32);pre[n]=(aa[:,:,:3].mean(2)*aa[:,:,3]/255)[150:600,700:1400]
r=np.pad(pre[1],((0,0),(0,20)))
for n,q in pre.items():
 z=np.fft.fft2(r)*np.conj(np.fft.fft2(np.pad(q,((0,0),(0,20)))));z/=np.maximum(abs(z),1e-9);cc=np.real(np.fft.ifft2(z));py,px=np.unravel_index(cc.argmax(),cc.shape);patch=np.array([[cc[(py+dy)%cc.shape[0],(px+dx)%cc.shape[1]] for dx in range(-2,3)]for dy in range(-2,3)]);response=float(patch.sum());dy=float((patch*np.arange(-2,3)[:,None]).sum()/response);dx=float((patch*np.arange(-2,3)[None,:]).sum()/response);tx=px+dx;ty=py+dy;tx=tx-cc.shape[1] if tx>cc.shape[1]/2 else tx;ty=ty-cc.shape[0] if ty>cc.shape[0]/2 else ty;alignment[n]={'dx_align_to01':tx,'dy_align_to01':ty,'signed_5x5_peak_response':response,'not_physical_pelvis':True}
result={'PR147_head':'666bcb8e8fccd9e2c1a4efc501c2b0ab7714286b','main':'6e28466','up_originals':rows,'upper_body_registration_to01':shifts,'unwindowed_phase_alignment':alignment,'rois':rois,'edges':edges,'limits':['Rearprojection: lowestimagefootrowdoesnotprovegroundcontact;raisedsolecanprojectlowerthanfarplantedboot.','Phase-onlybodyshift isappearancealignment,not anatomicalpelvis/3Dcenterofmass.','No newposes/render/source/browser/artedits.','No staticmetric certifies naturalness or absenceof worldsliding.']}
(O/'independent-up-metrics.json').write_text(json.dumps(result,indent=2));print(json.dumps({'rows':rows,'shifts':shifts,'edges':edges},indent=2))

"""Targeted source-pixel recovery: topology, untouched visible art and registration."""
from pathlib import Path
import json,hashlib,re
import numpy as np
from PIL import Image
from scipy.ndimage import label
R=Path(__file__).resolve().parents[2];D=R/'img/field/characters/aidan/side6/fix01';m=json.loads((D/'manifest.json').read_text());s=(R/'js/field/aidan-field-assets.js').read_text();frames=json.loads(s.split('const frames = ',1)[1].split(';\n',1)[0]);count=0
def ck(name,ok):
 global count
 print(('PASS ' if ok else 'FAIL ')+name,flush=True);assert ok,name;count+=1
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ck('exact four repaired frames',set(m['frames'])=={'aidan_walk_left_02.png','aidan_walk_left_04.png','aidan_walk_left_05.png','aidan_walk_right_01.png'})
for name,want in m['protected_original_side6_sha256'].items():ck('original protected '+name,sha(D.parent/name)==want)
for side in ['left','right']:
 for n in range(1,7):
  name=f'aidan_walk_{side}_{n:02}.png';meta=frames[Path(name).stem];p=R/meta['path'].split('?')[0];a=np.array(Image.open(p));ck(name+' dimensions/registration',a.shape==(1280,2048,4) and meta['anchor']==[1024,1230] and meta['scale']==.0625 and meta['width']==2048 and meta['height']==1280)
  ck(name+' transparent canvas margin',not a[0,:,3].any() and not a[-1,:,3].any() and not a[:,0,3].any() and not a[:,-1,3].any())
  if name not in m['frames']:
   ck(name+' original reference retained',p==D.parent/name);continue
  info=m['frames'][name];old=np.array(Image.open(R/info['original']));diff=(old!=a).any(2);added=(a[:,:,3]>0)&(old[:,:,3]==0);x0,y0,x1,y1=info['roi'];inside=np.zeros(diff.shape,bool);inside[y0:y1,x0:x1]=True
  ck(name+' source/repair SHA',sha(p)==info['sha256'] and sha(R/info['sheet'])==info['sheet_sha256'] and sha(R/info['original'])==info['original_sha256'])
  ck(name+' every existing visible RGBA unchanged',np.array_equal(old[old[:,:,3]>0],a[old[:,:,3]>0]))
  ck(name+' face/hair/clothes/weapon outside repair untouched',not diff[~inside].any() and np.all(old[diff,3]==0) and int(added.sum())==info['added_pixels'])
  x=info['cut'] if side=='left' else info['cut']-1;neighbor=x-1 if side=='left' else x+1
  before=(old[1080:1230,x,3]>100)&(old[1080:1230,neighbor,3]==0);after=(a[1080:1230,x,3]>100)&(a[1080:1230,neighbor,3]==0)
  ck(name+' actual old cut detected / no guillotine remains',before.sum()>30 and after.sum()==0)
  ck(name+' sole baseline unchanged',Image.fromarray(a).getbbox()[1::2]==Image.fromarray(old).getbbox()[1::2]==(126,1230))
  comp,_=label(a[:,:,3]>16);newlabels=set(np.unique(comp[added&(a[:,:,3]>16)]))-{0};oldlabels=set(np.unique(comp[old[:,:,3]>16]));ck(name+' no disconnected restored fragments',newlabels<=oldlabels)
  px,py=info['probe_pixel'];ck(name+' recovered toe interior',old[py,px,3]==0 and a[py,px,3]>180 and a[py,px].tolist()==info['probe_rgba'])
ck('left02/05 retain identical silhouettes',np.array_equal(np.array(Image.open(D/'aidan_walk_left_02.png'))[:,:,3],np.array(Image.open(D/'aidan_walk_left_05.png'))[:,:,3]))
print('PASS checks',count);print('FAILS 0')

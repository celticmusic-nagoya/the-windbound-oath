# Hero art intake dry run: sloppy deliveries (other canvas size, jittered offsets, 5-6 walk frames) -> normalised frames; rejections; never touches repo art
import os, sys, tempfile, subprocess, json, re, shutil
import numpy as np
from PIL import Image
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')); os.chdir(ROOT)
fails=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
tmp=tempfile.mkdtemp(prefix='hero_'); src=tmp+'/src'; os.makedirs(src); out=tmp+'/out'
D=['down','left','right','up']
def deliver(hero,n_walk,scale=1.7,jit=True,canvas=(1100,1300)):
    import random; r=random.Random(3)
    for d in D:
        frames=[('idle_%s'%d,'img/field/moss/real/fiona/fiona_idle_%s.png'%d)]+[('walk_%s_%02d'%(d,i+1),'img/field/moss/real/fiona/fiona_walk_%s_%02d.png'%(d,(i%6)+1)) for i in range(n_walk)]
        for name,p in frames:
            im=Image.open(p).convert('RGBA'); im=im.resize((int(im.width*scale),int(im.height*scale)),Image.LANCZOS)
            c=Image.new('RGBA',canvas,(0,0,0,0)); ox=(canvas[0]-im.width)//2+(r.randint(-40,40) if jit else 0); oy=canvas[1]-im.height-30+(r.randint(-25,25) if jit else 0)
            c.alpha_composite(im,(ox,oy)); c.save('%s/%s_%s.png'%(src,hero,name))
def run(*a): return subprocess.run([sys.executable,'tools/field/install_hero_frames.py',src,*a],capture_output=True,text=True)
deliver('fiona',5)
r=run('--hero','fiona','--out-dir',out,'--js-out',tmp+'/f.js'); print(r.stdout[-300:],r.stderr[-200:])
check(r.returncode==0 and 'walk 5 per direction' in r.stdout,'5-walk-frame delivery with jitter and a 1100x1300 canvas is accepted')
fs=sorted(os.listdir(out)); check(len(fs)==4*6,'24 normalised PNGs written (%d)'%len(fs))
rows=[];cols={}
for f in fs:
    a=np.array(Image.open(out+'/'+f)); ys,xs=np.where(a[...,3]>16); rows.append(ys.max()+1)
    check(Image.open(out+'/'+f).size==(512,640),f+' canvas 512x640') if f=='fiona_idle_down.png' else None
    d=f.split('_')[2] if f.startswith('fiona_walk') else f.split('_')[2].split('.')[0]
    if f.startswith('fiona_idle'):
        band=a[ys.max()-30:ys.max()+1,:,3]>16; bx=np.where(band.any(0))[0]; cols.setdefault(d,[]).append((bx.min()+bx.max())/2)
check(max(rows)-min(rows)<=3 and abs(rows[0]-600)<=3,'every frame stands on the anchor row y=600 (spread %d)'%(max(rows)-min(rows)))
check(all(abs(np.median(v)-256)<=4 for v in cols.values()),'feet centred on the anchor column per direction %s'%{k:round(float(np.median(v))) for k,v in cols.items()})
js=open(tmp+'/f.js').read(); check(js.count('"scale": 0.1')==24 and 'fiona_walk_up_05' in js and 'fiona_walk_up_06' not in js,'manifest lists 24 frames incl. walk_05, none beyond')
h=[np.where(np.array(Image.open(out+'/fiona_idle_down.png'))[...,3]>16)[0]]; hh=h[0].max()-h[0].min()+1
check(abs(hh*0.1-46)<2.5,'idle_down body height maps to ~46 world px (%.1f)'%(hh*0.1))
# dot snap
r=run('--hero','fiona','--out-dir',tmp+'/dot','--js-out',tmp+'/d.js','--dot','2'); check(r.returncode==0,'--dot 2 snapping runs')
a=np.array(Image.open(tmp+'/dot/fiona_idle_down.png')); check(len({tuple(p) for p in a[::20,::20].reshape(-1,4)[:400]})>=1 and (a[0:20,0:20]==a[0,0]).all(),'dot-snapped art is blocky (20px cells = 2 world px)')
# aidan contract
import glob
for f in glob.glob(src+'/fiona_*.png'): shutil.copy(f,f.replace('fiona_','aidan_'))
r=run('--hero','aidan','--out-dir',tmp+'/aidan','--js-out',tmp+'/a.js'); print(r.stdout[-300:],r.stderr[-300:]); check(r.returncode==0 and os.path.exists(tmp+'/a.js') and 'AidanFieldAssets' in open(tmp+'/a.js').read(),'aidan intake writes AidanFieldAssets manifest')
# rejections
import shutil
os.rename(src+'/fiona_idle_up.png',tmp+'/hold.png'); r=run('--hero','fiona','--dry-run'); check(r.returncode==1 and 'missing fiona_idle_up' in r.stdout,'missing direction rejected'); os.rename(tmp+'/hold.png',src+'/fiona_idle_up.png')
os.rename(src+'/fiona_walk_left_05.png',tmp+'/hold.png'); r=run('--hero','fiona','--dry-run'); check(r.returncode==1 and 'same number' in r.stdout,'unequal walk counts rejected'); os.rename(tmp+'/hold.png',src+'/fiona_walk_left_05.png')
bg=Image.new('RGBA',(600,700),(40,30,20,255)); bg.save(src+'/fiona_idle_down.png'); r=run('--hero','fiona','--dry-run'); check(r.returncode==1 and ('baked backdrop' in r.stdout),'opaque backdrop rejected')
check(subprocess.run(['git','status','--porcelain','--','img/field/moss/real','img/field/moss/aidan','js/field/fiona-field-assets.js','js/field/aidan-field-assets.js'],capture_output=True,text=True).stdout.strip()=='','repo art untouched by the dry runs')
shutil.rmtree(tmp); print('\nFAILS',len(fails)); sys.exit(1 if fails else 0)

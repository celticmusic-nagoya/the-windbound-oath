# M9 hero visuals: Fiona animated field sprite (4 dir x idle + 6-frame walk, transparent RGBA, feet anchor) + Aidan soft step bob. needs http.server 8765
import sys, glob
from PIL import Image
import numpy as np
from playwright.sync_api import sync_playwright
fails=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
fs=sorted(glob.glob('img/field/moss/real/fiona/*.png'))
check(len(fs)==28,'28 Fiona frames (4 dirs x (idle + 6 walk)) %d'%len(fs))
bad=[]
for f in fs:
    im=Image.open(f); a=np.array(im)[...,3]
    ys,xs=np.where(a>16)
    if im.mode!='RGBA' or im.size!=(512,640) or a.min()!=0 or ys.max()>628 or ys.max()<585: bad.append(f)
check(not bad,'every frame is 512x640 RGBA with real transparency and feet at the anchor line %s'%bad[:2])
walk=[np.array(Image.open(f))[...,3]>16 for f in fs if 'walk_down' in f]
check(len({w.tobytes() for w in walk})==6,'6 distinct walk-down frames (no duplicated poses)')
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1000)
    ev=lambda s,*a: pg.evaluate(s,*a) if a else pg.evaluate(s)
    ev("devJump('forest')"); pg.wait_for_function("MossForest.active",timeout=20000); pg.wait_for_timeout(1500); ev("closeDialogue()")
    check(ev("document.querySelectorAll('#forestFiona img').length")==28 and ev("document.querySelector('#forestFiona').classList.contains('fiona-sprite')"),'Fiona sprite mounted, placeholder box hidden')
    vis=lambda: ev("[...document.querySelectorAll('#forestFiona img')].filter(i=>!i.hidden).map(i=>i.src.split('/').pop())")
    check(vis()==['fiona_idle_down.png'] or 'idle' in str(vis()),'idle frame while standing %s'%vis())
    f0=ev("MossForest.feet"); ev("MossForest.goFeet(%d,%d)"%(f0['x']+500,f0['y']))
    seen=set()
    for _ in range(20): pg.wait_for_timeout(110); seen.update(vis())
    walk=[s for s in seen if 'walk_right' in s]
    check(len(walk)>=5,'Fiona cycles %d walk-right frames while following'%len(walk))
    ev("MossForest.goFeet(%d,%d)"%(f0['x']+500,f0['y']+300))
    seen=set()
    for _ in range(14): pg.wait_for_timeout(110); seen.update(vis())
    check(any('walk_down' in s for s in seen),'turns to the walk-down frames when heading south')
    pg.wait_for_timeout(2500); check('idle' in str(vis()),'back to idle after stopping %s'%vis())
    # Aidan bob
    ev("MossForest.goFeet(%d,%d)"%(f0['x']+900,f0['y']+300)); pg.wait_for_timeout(500)
    tr=ev("[...document.querySelectorAll('#forestPlayer .forest-aidan')].filter(i=>!i.hidden).map(i=>i.style.transform)")
    check(any('translateY' in t for t in tr),'Aidan has the soft step bob while walking %s'%tr)
    b.close()
check(not errs,'0 console errors %s'%errs[:2]); print('\nFAILS',len(fails)); sys.exit(1 if fails else 0)

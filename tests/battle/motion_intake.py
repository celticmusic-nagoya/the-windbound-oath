# Battle multi-frame motion intake dry run: fabricates 6 attack frames, installs them with tools/battle/install_motion_frames.py,
# checks frame order / hit event timing / return to rest / still fallback, then restores the manifest and removes the files
# by itself (never git checkout: it must not touch anyone's uncommitted work). Needs http.server 8765.
import os, subprocess, sys, tempfile, shutil, json, time
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')); os.chdir(ROOT)
MAN='img/battle/motion-manifest.json'; MOT='img/battle/characters/aidan/motion'
fails=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
orig=open(MAN,'rb').read(); had=os.path.isdir(MOT); tmp=tempfile.mkdtemp()
try:
    idle=Image.open('img/battle/characters/aidan/aidan_attack.png').convert('RGBA')   # canvas differs per state: attack is 1312x1199
    for i in range(6):
        f=Image.new('RGBA',idle.size,(0,0,0,0)); f.alpha_composite(idle,(i*2,0)); f.save(os.path.join(tmp,'aidan_attack_%02d.png'%(i+1)))
    bad=os.path.join(tmp,'bad'); os.makedirs(bad)
    Image.new('RGBA',(300,300),(255,0,0,255)).save(os.path.join(bad,'aidan_attack_01.png')); Image.new('RGBA',(300,300),(255,0,0,255)).save(os.path.join(bad,'aidan_attack_02.png'))
    r=subprocess.run([sys.executable,'tools/battle/install_motion_frames.py',bad],capture_output=True,text=True); check(r.returncode==1 and 'canvas' in r.stdout,'wrong canvas size is rejected')
    r=subprocess.run([sys.executable,'tools/battle/install_motion_frames.py',tmp,'--ms','100,100,100,100,120,120','--hit','4','--dry-run'],capture_output=True,text=True); check(r.returncode==0 and 'ok' in r.stdout and open(MAN,'rb').read()==orig,'dry-run validates and writes nothing')
    r=subprocess.run([sys.executable,'tools/battle/install_motion_frames.py',tmp,'--ms','100,100,100,100,120,120','--hit','4'],capture_output=True,text=True); check(r.returncode==0 and 'manifest updated' in r.stdout,'install: '+r.stdout.strip().splitlines()[0])
    r=subprocess.run([sys.executable,'tools/battle/install_motion_frames.py',tmp,'--ms','400','--dry-run'],capture_output=True,text=True); check('exceeds the state budget' in r.stdout,'over-long total warns against the 820 ms budget')
    with sync_playwright() as p:
        b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720}); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
        pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1200)
        check(pg.evaluate("BattleMotion.loaded && BattleMotion.has('aidan','attack')"),'runtime picked the manifest up')
        inf=pg.evaluate("BattleMotion.info('aidan','attack')"); check(inf['frames']==6 and inf['totalMs']==640 and inf['hitAtMs']==300,'info: %s'%inf)
        pg.evaluate("window.__hit=[];addEventListener('battle-motion-hit',e=>__hit.push(e.detail));window.__seq=[];window.__t0=performance.now();"
                    "const im=document.querySelector('#bAidan2 img');new MutationObserver(()=>{const n=im.dataset.motionFrame;if(n&&__seq[__seq.length-1]?.[0]!==n)__seq.push([n,Math.round(performance.now()-__t0)])}).observe(im,{attributes:true,attributeFilter:['data-motion-frame']});")
        pg.evaluate("__t0=performance.now();BattleActorState.set('aidan','attack',{battle:'normal',duration:820})"); pg.wait_for_timeout(1100)
        seq=pg.evaluate("__seq"); hit=pg.evaluate("__hit")
        check([s[0] for s in seq]==['1','2','3','4','5','6'],'frames play in order %s'%[s[0] for s in seq])
        check(len(hit)==1 and hit[0]['frame']==4 and abs(hit[0]['at']-300)<=80,'hit event on frame 4 at ~300 ms: %s'%hit)
        check('idle' in pg.evaluate("document.querySelector('#bAidan2 img').getAttribute('src')"),'returns to the idle still after the state duration')
        pg.evaluate("BattleActorState.set('aidan','skill',{battle:'normal',duration:300})"); pg.wait_for_timeout(100)
        check('aidan_skill' in pg.evaluate("document.querySelector('#bAidan2 img').getAttribute('src')") and len(pg.evaluate("__hit"))==1,'a state without frames keeps the still image')
        pg.evaluate("BattleMotion.setVariant('aidan','wooden')"); check(pg.evaluate("BattleMotion.has('aidan','attack')"),'unknown variant falls back to the base motion')
        check(not errs,'0 console errors %s'%errs[:2]); b.close()
finally:
    open(MAN,'wb').write(orig)
    if not had: shutil.rmtree(MOT,ignore_errors=True)
    else:
        for f in os.listdir(MOT):
            if f.startswith('aidan_attack_') : os.remove(os.path.join(MOT,f))
    shutil.rmtree(tmp,ignore_errors=True)
sys.exit(1 if fails else 0)

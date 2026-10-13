"""Aidan sword-draw ('draw') motion: asset sanity, 6-frame one-shot playback, return to idle, attack/skill untouched, dev preview."""
import os,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];fails=[]
def check(ok,name,detail=''):
    print(('ok   ' if ok else 'FAIL ')+name,detail)
    if not ok:fails.append(name)
M=ROOT/'img/battle/characters/aidan/motion'
# ---- assets: same canvas, shared foot line, nothing cut, no stray haze
ims=[Image.open(M/('aidan_draw_%02d.png'%i)).convert('RGBA') for i in range(1,7)]
check(len({i.size for i in ims})==1,'6 frames share one canvas',ims[0].size)
bot=[];edge=[];haze=[];cx=[]
for im in ims:
    a=np.array(im)[...,3];ys,xs=np.where(a>16);bot.append(int(ys.max()));edge.append(bool(xs.min()<=0 or ys.min()<=0 or xs.max()>=im.width-1 or ys.max()>=im.height-1))
    haze.append(int(((a>0)&(a<6)).sum()));low=ys.max()-40;cx.append(float(xs[ys>low].mean()))
check(max(bot)-min(bot)<=3,'foot line unified (max drift <=3px)',bot)
check(not any(edge),'no frame touches the canvas edge (sword / cloak not cut)')
check(max(haze)<900,'no faint halo pixels left (alpha 1..5)',haze)
check(max(cx)-min(cx)<=30,'feet centre stable across frames (<=30 src px)',[round(c) for c in cx])
man=json.load(open(ROOT/'img/battle/motion-manifest.json'))['motions']['aidan']
d=man['draw'];check(d['frames']==6 and sum(d['ms'])==600 and d.get('hold')=='last' and 'hitFrame' not in d,'manifest: 6 frames / 600ms / hold last / no hit event',d)
check(man['attack']['frames']==6 and man['skill']['frames']==7,'attack/skill manifest entries untouched')
with server(8814) as base,sync_playwright() as p:
    b=p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None))
    for vp in [(1280,720),(390,844),(844,390)]:
        pg=b.new_page(viewport={'width':vp[0],'height':vp[1]});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto(base+'/index.html');pg.wait_for_function('window.BattleMotion&&BattleMotion.loaded&&window.BattleActorState');pg.wait_for_timeout(1500)
        pg.evaluate("closeDialogue();devJump('raider')");pg.wait_for_timeout(2200)
        for ctxname,sel in (('raider','#rbAidan img'),('normal','#bAidan2 img')):
            r=pg.evaluate("""async([ctx,sel])=>{const im=document.querySelector(sel),seen=[],t0=performance.now();
              const mo=new MutationObserver(()=>{const f=+im.dataset.motionFrame;if(f&&seen[seen.length-1]?.f!==f)seen.push({f,t:Math.round(performance.now()-t0),src:im.getAttribute('src')})});mo.observe(im,{attributes:true,attributeFilter:['src','data-motion-frame']});
              const ok=BattleActorState.set('aidan','draw',{battle:ctx,duration:600});const mid=BattleActorState.get(ctx);
              await new Promise(r=>setTimeout(r,430));const at430=BattleActorState.get(ctx);
              await new Promise(r=>setTimeout(r,700));mo.disconnect();return {ok,mid,at430,end:BattleActorState.get(ctx),seen,src:im.getAttribute('src')}}""",[ctxname,sel])
            order=[s['f'] for s in r['seen']]
            check(r['ok'] and r['mid']=='draw' and order==[1,2,3,4,5,6],'%s %s: draw plays frames 1..6 once in order'%(vp,ctxname),order)
            ts=[s['t'] for s in r['seen']];last=ts[-1] if ts else 0
            check(450<=last<=620 and r['at430']=='draw' and r['end']=='idle','%s %s: last frame at ~480ms, held, then returns to idle'%(vp,ctxname),(ts,r['at430'],r['end']))
            check(r['seen'] and r['seen'][-1]['f']==6,'%s %s: no loop / no 7th frame'%(vp,ctxname))
        # attack / skill still use their own art after a draw; a draw never runs from them
        r=pg.evaluate("""async()=>{const out={};for(const st of ['attack','skill']){BattleActorState.set('aidan',st,{battle:'raider',duration:820});await new Promise(r=>setTimeout(r,60));out[st]=document.querySelector('#rbAidan img').getAttribute('src').split('/').pop().split('?')[0];await new Promise(r=>setTimeout(r,1300));}return out}""")
        check(r['attack'].startswith('aidan_attack_') and r['skill'].startswith('aidan_skill_'),'%s attack / skill keep their own art, no draw'%(vp,),r)
        # a KO outranks a running draw is not needed here; idle canvas resumes after the draw
        pg.evaluate("BattleActorState.set('aidan','draw',{battle:'raider',duration:600})");pg.wait_for_timeout(1300)
        check(pg.evaluate("BattleActorState.get('raider')")=='idle' and pg.evaluate("BattleIdleMotion.status.actors.some(a=>a.actor==='aidan'&&a.context==='raider'&&a.state==='idle')"),'%s idle motion resumes after the draw'%(vp,))
        check(not errs,'%s no console errors'%(vp,),errs[:2]);pg.close()
    # ---- dev preview page (battle-opening-preview): both characters, step / speed / rest switch
    for vp in [(1100,640),(390,844)]:
        pg=b.new_page(viewport={'width':vp[0],'height':vp[1]});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(base+'/dev/battle-opening-preview.html');pg.wait_for_timeout(700)
        check(pg.evaluate("document.querySelectorAll('#stripA button').length")==6 and pg.evaluate("document.querySelectorAll('#stripF button').length")==6,'%s preview: 6+6 frame buttons'%(vp,))
        pg.click('#next');pg.click('#next');check('3/6' in pg.inner_text('#capA') and '3/6' in pg.inner_text('#capF'),'%s preview: frame step moves both'%(vp,),pg.inner_text('#capA'))
        pg.fill('#spd','2');pg.dispatch_event('#spd','input');pg.click('#play');t=pg.evaluate("new Promise(r=>{const t0=performance.now();const iv=setInterval(()=>{if(document.getElementById('capF').textContent.startsWith('ready 6')){clearInterval(iv);r(performance.now()-t0)}},10)})")
        check(300<=t<=520,'%s preview: speed 2.0x plays Fiona in ~half of 760ms'%(vp,),round(t))
        pg.wait_for_timeout(900);check(pg.inner_text('#capA').startswith('待機'),'%s preview: switches to rest after the motion'%(vp,),pg.inner_text('#capA'))
        check(pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"),'%s preview: no horizontal overflow'%(vp,));check(not errs,'%s preview: no errors'%(vp,),errs[:2]);pg.close()
    b.close()
print('FAILS %d'%len(fails));sys.exit(1 if fails else 0)

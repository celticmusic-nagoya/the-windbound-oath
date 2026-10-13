"""Battle-start opening (Aidan 'draw' + Fiona 'ready'): once per battle start, both contexts, lock safety, return to rest, attack/skill unaffected."""
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
# ---- assets
for actor,state,pref,size in (('aidan','draw','aidan_draw_','aidan'),('fiona','ready','fiona_ready_','fiona')):
    d=ROOT/('img/battle/characters/%s/motion'%actor);ims=[Image.open(d/('%s%02d.png'%(pref,i))).convert('RGBA') for i in range(1,7)]
    check(len({i.size for i in ims})==1,'%s: 6 frames share one canvas'%actor,ims[0].size)
    bots=[];edge=[]
    for im in ims:
        a=np.array(im)[...,3];ys,xs=np.where(a>16);bots.append(int(ys.max()));edge.append(bool(xs.min()<=0 or ys.min()<=0 or xs.max()>=im.width-1 or ys.max()>=im.height-1))
    check(max(bots)-min(bots)<=3,'%s: foot line unified'%actor,bots);check(not any(edge),'%s: nothing touches the canvas edge'%actor)
man=json.load(open(ROOT/'img/battle/motion-manifest.json'))['motions']
check(man['aidan']['draw']['frames']==6 and sum(man['aidan']['draw']['ms'])==600,'manifest aidan draw 6f/600ms');check(man['fiona']['ready']['frames']==6 and sum(man['fiona']['ready']['ms'])<=900,'manifest fiona ready 6f/<=900ms',sum(man['fiona']['ready']['ms']))
check(man['aidan']['attack']['frames']==6 and man['aidan']['skill']['frames']==7,'attack/skill manifests untouched')
START={'normal':"startAttackBattle('attackGob1',100)",'raider':"startRaiderBattle();PrologueCombat.spawn&&0"}
IMG={'normal':{'aidan':'#bAidan2 img','fiona':'#bFiona2 img'},'raider':{'aidan':'#rbAidan img','fiona':'#rbFiona img'}}
JS_TRACE="""([ctx,sel])=>{window.__tr={ev:[],seq:{aidan:[],fiona:[]},busy:[]};const t0=performance.now();
 addEventListener('battle-opening',e=>__tr.ev.push({t:Math.round(performance.now()-t0),d:e.detail}));
 for(const a of ['aidan','fiona']){const im=document.querySelector(sel[a]);new MutationObserver(()=>{const f=+im.dataset.motionFrame;const s=__tr.seq[a];if(f&&s[s.length-1]?.f!==f)s.push({f,t:Math.round(performance.now()-t0),src:im.getAttribute('src')})}).observe(im,{attributes:true,attributeFilter:['src','data-motion-frame']})}
 window.__t0=t0;window.__iv=setInterval(()=>__tr.busy.push([Math.round(performance.now()-t0),BattlePresentation.busy,document.body.classList.contains('battlePresentationBusy')]),30);return 1}"""
with server(8815) as base,sync_playwright() as p:
    b=p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None))
    for vp in [(1280,720),(390,844),(844,390)]:
      for ctx in ('normal','raider'):
        pg=b.new_page(viewport={'width':vp[0],'height':vp[1]});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto(base+'/index.html');pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.PrologueCombat');pg.wait_for_timeout(1800);pg.evaluate("closeDialogue()")
        pg.evaluate(JS_TRACE,[ctx,IMG[ctx]]);pg.evaluate("PrologueProgress&&PrologueProgress.seed&&PrologueProgress.seed(0)");pg.evaluate(START[ctx]);pg.wait_for_timeout(450)
        mid=pg.evaluate("[BattlePresentation.busy,BattleActorState.get(%r),BattleActorState.get(%r,'fiona')]"%(ctx,ctx))
        check(mid[0] is True and mid[1]=='draw' and mid[2]=='ready','%s %s: opening running, input locked at 450ms'%(vp,ctx),mid)
        pg.wait_for_timeout(1100);r=pg.evaluate("clearInterval(__iv)||({ev:__tr.ev,seq:__tr.seq,busy:__tr.busy,a:BattleActorState.get(%r),f:BattleActorState.get(%r,'fiona'),again:BattleOpening.play(%r),busyNow:BattlePresentation.busy,srcF:document.querySelector(%r).getAttribute('src')})"%(ctx,ctx,ctx,IMG[ctx]['fiona']))
        check(len(r['ev'])==1 and set(r['ev'][0]['d']['actors'])=={'aidan','fiona'},'%s %s: exactly one opening event, both actors'%(vp,ctx),r['ev'])
        sa=[s['f'] for s in r['seq']['aidan']];sf=[s['f'] for s in r['seq']['fiona']]
        check(sa==[1,2,3,4,5,6] and sf==[1,2,3,4,5,6],'%s %s: both play frames 1..6 once, in order'%(vp,ctx),(sa,sf))
        lastA=r['seq']['aidan'][-1]['t']-r['seq']['aidan'][0]['t'];lastF=r['seq']['fiona'][-1]['t']-r['seq']['fiona'][0]['t']
        check(430<=lastA<=560 and 640<=lastF<=800,'%s %s: frame timing (aidan last frame ~480ms, fiona ~760ms)'%(vp,ctx),(lastA,lastF))
        un=[x for x in r['busy'] if x[1]];dur=un[-1][0]-un[0][0] if un else 0
        check(800<=dur<=1000 and not r['busyNow'],'%s %s: input lock ~ longer motion (880ms) then released'%(vp,ctx),(dur,r['busyNow']))
        check(r['a']=='idle' and r['f']=='idle' and r['again'] is False and r['srcF'].split('/')[-1].startswith('fiona_battle_idle'),'%s %s: both back at rest (Aidan idle, Fiona still), no double play'%(vp,ctx),(r['a'],r['f'],r['again'],r['srcF']))
        idle=pg.evaluate("BattleIdleMotion.status.actors.some(a=>a.actor==='aidan'&&a.context===%r&&a.state==='idle')"%ctx);check(idle,'%s %s: Aidan idle motion resumes'%(vp,ctx))
        # attack / skill must not trigger an opening
        pg.evaluate("window.__n=0;addEventListener('battle-opening',()=>__n++);BattleActorState.set('aidan','attack',{battle:%r,duration:820});BattleActorState.set('fiona','skill',{battle:%r,duration:700})"%(ctx,ctx));pg.wait_for_timeout(1000)
        check(pg.evaluate("__n")==0,'%s %s: attack/skill never replay the opening'%(vp,ctx))
        check(not errs,'%s %s: no console errors'%(vp,ctx),errs[:2]);pg.close()
    # ---- interruption: cancelling mid-opening releases the lock at once; a restart opens once more
    pg=b.new_page(viewport={'width':1280,'height':720});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(base+'/index.html');pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded');pg.wait_for_timeout(1800);pg.evaluate("closeDialogue();startRaiderBattle()");pg.wait_for_timeout(250)
    pg.evaluate("PrologueCombat.cancel()");pg.wait_for_timeout(60)
    check(pg.evaluate("BattlePresentation.busy")is False and not pg.evaluate("document.body.classList.contains('battlePresentationBusy')"),'interrupt: cancel releases the input lock at once')
    pg.wait_for_timeout(1200);check(pg.evaluate("[BattleActorState.get('raider'),BattleActorState.get('raider','fiona')]")==['idle','idle'],'interrupt: actors still return to rest')
    pg.evaluate("startRaiderBattle()");pg.wait_for_timeout(400);check(pg.evaluate("BattlePresentation.busy")is True,'restart: a new battle start opens again (lock on)');pg.wait_for_timeout(1100)
    check(pg.evaluate("BattlePresentation.busy")is False,'restart: lock released after the opening');check(not errs,'interrupt/restart: no console errors',errs[:2]);pg.close()
    # ---- image load failure: Fiona frames blocked -> opening still ends, lock released, rest pose back
    ctxf=b.new_context(viewport={'width':1280,'height':720});ctxf.route('**/fiona_ready_0*.png',lambda r:r.abort());pg=ctxf.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(base+'/index.html');pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded');pg.wait_for_timeout(1800);pg.evaluate("closeDialogue();startRaiderBattle()");pg.wait_for_timeout(1500)
    check(pg.evaluate("BattlePresentation.busy")is False and pg.evaluate("[BattleActorState.get('raider'),BattleActorState.get('raider','fiona')]")==['idle','idle'],'load failure: lock released and both at rest');check(not errs,'load failure: no uncaught errors',errs[:2]);pg.close()
    # ---- battle exit during the opening does not leave the lock
    pg=b.new_page(viewport={'width':1280,'height':720});pg.goto(base+'/index.html');pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded');pg.wait_for_timeout(1800);pg.evaluate("closeDialogue();startRaiderBattle()");pg.wait_for_timeout(200)
    pg.evaluate("document.querySelector('#raiderBattle').style.display='none';document.body.classList.remove('battleMode','raiderBattleMode');PrologueCombat.cancel()");pg.wait_for_timeout(100)
    check(pg.evaluate("BattlePresentation.busy")is False,'battle exit mid-opening: no lock left');pg.close()
    b.close()
print('FAILS %d'%len(fails));sys.exit(1 if fails else 0)

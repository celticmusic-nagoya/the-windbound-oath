"""Fiona idle v3 - main-thread load investigation (Codex FIV3-RQ-02). Measurement only: it changes no game file and asserts nothing about the game.
Records, on ONE shared time axis and independent of the Fiona state machine: requestAnimationFrame gaps, a 50 ms setTimeout chain, non-buffered longtasks and the cost of every big
CanvasRenderingContext2D.drawImage call. Fiona's idle is switched ON/OFF alternately (ABAB) in the SAME page so browser, screen and time of day are identical.
  RUNTIME=head (default)  the checked-out tree (layered v3 Fiona)
  RUNTIME=main            same tree, but js/assets.js, js/battle-idle-motion.js and Fiona's old 6 idle frames are served from git ref MAIN_REF (the pre-v3 runtime), as Codex did
Env: THROTTLE (1 = off; N = CDP CPU slow-down factor), PHASE_S (20), CYCLES (2), CTX (raider|normal), OUT (json path), MAIN_REF (origin/main), VARIANT (none|scaled_cache|no_smoothing: in-page A/B experiments, never committed to the game)."""
import os,sys,json,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from browser_support import server
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
PHASE=float(os.getenv('PHASE_S','20'));CYCLES=int(os.getenv('CYCLES','2'));CTXN=os.getenv('CTX','raider');RUNTIME=os.getenv('RUNTIME','head');MAIN_REF=os.getenv('MAIN_REF','origin/main');VARIANT=os.getenv('VARIANT','none')
START={'raider':'startRaiderBattle()','normal':'startAttackBattle("attackGob2",100)'}[CTXN]
SEL={'raider':'#rbFiona img','normal':'#bFiona2 img'}[CTXN]
INSTALL="""()=>{const W=window.__probe={t0:performance.now(),raf:[],tmr:[],lt:[],draw:{n:0,sum:0,max:0,big:0},phase:'init',marks:[]};
 let last=performance.now();const tick=t=>{const g=t-last;last=t;W.raf.push([Math.round(t-W.t0),Math.round(g*10)/10,W.phase]);requestAnimationFrame(tick)};requestAnimationFrame(tick);
 let lt=performance.now();const tm=()=>{const n=performance.now(),g=n-lt;lt=n;W.tmr.push([Math.round(n-W.t0),Math.round((g-50)*10)/10,W.phase]);setTimeout(tm,50)};setTimeout(tm,50);
 try{new PerformanceObserver(l=>l.getEntries().forEach(e=>W.lt.push([Math.round(e.startTime-W.t0),Math.round(e.duration),W.phase]))).observe({type:'longtask',buffered:false})}catch(e){}
 const od=CanvasRenderingContext2D.prototype.drawImage;CanvasRenderingContext2D.prototype.drawImage=function(img,...a){const w=img.naturalWidth||img.width||0;const s=performance.now();const r=od.call(this,img,...a);const d=performance.now()-s;
  if(w>=900){const q=W.draw;q.big++;q.n++;q.sum+=d;if(d>q.max)q.max=d;(W.dd=W.dd||[]).push([W.phase,Math.round(d*100)/100])}return r};}"""
EXPERIMENT={
 # A/B experiments applied in-page after the battle started (the game files are untouched): what would the per-draw cost be if ...
 'no_smoothing':"""()=>{const o=Object.getOwnPropertyDescriptor(CanvasRenderingContext2D.prototype,'imageSmoothingQuality');Object.defineProperty(CanvasRenderingContext2D.prototype,'imageSmoothingQuality',{configurable:true,get:o.get,set(v){o.set.call(this,'low')}})}""",
}
def git_show(path):return subprocess.run(['git','show','%s:%s'%(MAIN_REF,path)],cwd=ROOT,capture_output=True,check=True).stdout
def summarize(rows,key,phase):
    v=[r[1] for r in rows if r[2]==phase];
    if not v:return None
    s=sorted(v);n=len(s)
    return {'n':n,'max':s[-1],'p99':s[int(n*0.99)-1 if n>1 else 0],'p50':s[n//2],'over100':sum(1 for x in v if x>100),'over1000':sum(1 for x in v if x>1000)}
with server(8818) as base,sync_playwright() as p:
    b=p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None))
    ctx=b.new_context(viewport={'width':1280,'height':720});pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    if RUNTIME=='main':
        def serve(route):
            u=route.request.url;path=u.split(base+'/',1)[1].split('?')[0]
            try:route.fulfill(status=200,body=git_show(path),content_type='application/javascript' if path.endswith('.js') else 'image/png')
            except Exception as ex:route.continue_()
        for pat in ('**/js/assets.js*','**/js/battle-idle-motion.js*','**/img/battle/characters/fiona/idle/*.png'):ctx.route(pat,serve)
    pg.goto(base+'/index.html',timeout=90000);pg.wait_for_function('window.BattleIdleMotion&&window.BattleActorState',timeout=60000);pg.wait_for_timeout(1500);pg.evaluate("closeDialogue()");pg.wait_for_timeout(300)
    pg.evaluate(START);pg.wait_for_timeout(1500)
    pg.wait_for_function("BattleIdleMotion.status.actors.some(q=>q.actor==='fiona'&&q.context===%r&&q.showing)"%CTXN,timeout=30000)
    pg.evaluate("typeof closeDialogue==='function'&&closeDialogue()");pg.wait_for_function("!['battlePresentationBusy','dialogueOpen','actionCinematic'].some(c=>document.body.classList.contains(c))",timeout=30000);pg.wait_for_timeout(800)
    THR=float(os.getenv('THROTTLE','1'))
    if THR>1:ctx.new_cdp_session(pg).send('Emulation.setCPUThrottlingRate',{'rate':THR})   # emulate a slower CPU (phone-class), applied to this page only
    pg.evaluate(INSTALL)
    if VARIANT in EXPERIMENT:pg.evaluate(EXPERIMENT[VARIANT])
    order=[]
    for c in range(CYCLES):
        for ph,on in (('ON',True),('OFF',False)):
            name='%s%d'%(ph,c);order.append(name)
            pg.evaluate("n=>{__probe.phase=n}",name)
            pg.evaluate("a=>{const s=a[0],on=a[1];if(on)BattleIdleMotion.begin(s,'fiona');else BattleIdleMotion.stop(s)}",[SEL,on]);pg.wait_for_timeout(600)
            pg.evaluate("n=>{__probe.phase=n}",name)   # relabel after the switch settled
            pg.wait_for_timeout(int(PHASE*1000))
            st=pg.evaluate("BattleIdleMotion.status.actors.find(q=>q.actor==='fiona'&&q.context===%r).showing"%CTXN)
            if st!=on:print('WARNING phase',name,'expected showing',on,'got',st)
    data=pg.evaluate("({raf:__probe.raf,tmr:__probe.tmr,lt:__probe.lt,dd:__probe.dd||[],hidden:document.hidden})")
    b.close()
res={'throttle':THR,'runtime':RUNTIME,'variant':VARIANT,'ctx':CTXN,'phase_s':PHASE,'cycles':CYCLES,'errors':errs[:3],'phases':{}}
for n in order:
    dd=[x[1] for x in data['dd'] if x[0]==n]
    res['phases'][n]={'raf_gap_ms':summarize(data['raf'],1,n),'timer_late_ms':summarize(data['tmr'],1,n),
      'longtasks':{'n':sum(1 for x in data['lt'] if x[2]==n),'max_ms':max([x[1] for x in data['lt'] if x[2]==n] or [0]),'sum_ms':sum(x[1] for x in data['lt'] if x[2]==n)},
      'drawImage_big':{'n':len(dd),'mean_ms':round(sum(dd)/len(dd),3) if dd else 0,'max_ms':max(dd) if dd else 0}}
if os.getenv('OUT'):Path(os.getenv('OUT')).write_text(json.dumps({'summary':res,'raw':{k:data[k] for k in ('lt',)}},indent=1))
print(json.dumps(res,indent=1))

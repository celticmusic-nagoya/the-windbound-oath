"""Opening lock (BattlePresentation.hold + BattleMotion run.done) safety: normal completion, stop, replacement, battle end, new battle start,
KO / victory during the opening, single settlement, and a stale run/hold never releasing a newer lock."""
import os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
fails=[]
def check(ok,name,detail=''):
    print(('ok   ' if ok else 'FAIL ')+name,detail)
    if not ok:fails.append(name)
PROBE="""()=>{window.__L={on:null,off:null,ons:0,offs:0};const t0=performance.now();window.__t0=t0;
 new MutationObserver(()=>{const on=document.body.classList.contains('battlePresentationBusy'),n=Math.round(performance.now()-t0);
  if(on&&__L.on===null)__L.on=n;if(on)__L.ons++;if(!on){__L.offs++;__L.off=n}}).observe(document.body,{attributes:true,attributeFilter:['class']});return 1}"""
with server(8818) as base,sync_playwright() as p:
    b=p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None))
    def page(vp=(1280,720)):
        pg=b.new_page(viewport={'width':vp[0],'height':vp[1]});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto(base+'/index.html');pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.PrologueCombat');pg.wait_for_timeout(1500);pg.evaluate('closeDialogue()');pg.evaluate(PROBE);return pg,errs
    START="startAttackBattle('attackGob1',100)"
    # 1 normal completion: lock released at the longer motion's completion, not before the last frame, never early
    pg,errs=page();pg.evaluate(START);pg.wait_for_timeout(2200)
    r=pg.evaluate("({L:__L,busy:BattlePresentation.busy,a:BattleActorState.get('normal'),f:BattleActorState.get('normal','fiona')})")
    check(r['busy'] is False and r['a']=='idle' and r['f']=='idle' and 1195<=r['L']['off']-r['L']['on']<=1320,'normal completion: lock off with the motion, both at rest',r)
    check(r['L']['offs']>=1,'normal completion: lock released exactly through one release',r['L']);pg.close()
    # 2 stop() of one run mid-opening: the other motion still holds the lock to its end; no hang
    pg,errs=page();pg.evaluate(START);pg.wait_for_timeout(300);pg.evaluate("BattleMotion.stop(document.querySelector('#bAidan2 img'))");pg.wait_for_timeout(1600)
    r=pg.evaluate("({L:__L,busy:BattlePresentation.busy})")
    check(r['busy'] is False and r['L']['off'] is not None and r['L']['off']-r['L']['on']>=1195,'stop() of one run: lock still lasts the minimum, then releases (no hang)',r);pg.close()
    # 3 replacement mid-opening (attack replaces draw): old run settles, lock unaffected by the replacement, released at the minimum
    pg,errs=page();pg.evaluate(START);pg.wait_for_timeout(300)
    pg.evaluate("window.__old=BattleActorState.motion('normal');BattleActorState.set('aidan','damage',{battle:'normal',duration:400})");pg.wait_for_timeout(1700)
    r=pg.evaluate("(async()=>({res:await __old.done,L:__L,busy:BattlePresentation.busy,a:BattleActorState.get('normal')}))()")
    check(r['res']['reason']=='replaced' and r['busy'] is False and r['L']['off']-r['L']['on']>=1195 and r['a']=='idle','replacement: old run settled as replaced, lock released once at the minimum',r);pg.close()
    # 4 battle end mid-opening: cancel releases at once; the stale run completion later does not touch a new lock
    pg,errs=page();pg.evaluate(START);pg.wait_for_timeout(400);pg.evaluate("PrologueCombat.cancel()");pg.wait_for_timeout(60)
    check(pg.evaluate("BattlePresentation.busy")is False and not pg.evaluate("document.body.classList.contains('battlePresentationBusy')"),'battle end: lock released at once');
    # 5 new battle start right after the cancel: its own lock must survive the old hold's late release
    pg.evaluate("window.__L.on=null;window.__L.off=null");pg.evaluate("startRaiderBattle()");pg.wait_for_timeout(600);mid=pg.evaluate("BattlePresentation.busy")
    pg.wait_for_timeout(900);after=pg.evaluate("({busy:BattlePresentation.busy,L:__L})")
    check(mid is True,'new battle start after a cancel: lock is on',mid)
    check(after['busy'] is False and after['L']['off']-after['L']['on']>=1195,'new battle: its lock lasts its own full opening (old hold/run did not release it)',after);check(not errs,'end/new-start: no page errors',errs);pg.close()
    # 6 KO during the opening: stays KO, lock still ends on schedule
    pg,errs=page();pg.evaluate(START);pg.wait_for_timeout(300);pg.evaluate("aahp=0;BattleActorState.sync('normal')");pg.wait_for_timeout(1800)
    r=pg.evaluate("({a:BattleActorState.get('normal'),busy:BattlePresentation.busy,L:__L})")
    check(r['a']=='ko' and r['busy'] is False,'KO during the opening: state stays ko, lock released',r);check(not errs,'KO: no page errors',errs);pg.close()
    # 7 victory during the opening is not overwritten by the older run
    pg,errs=page();pg.evaluate(START);pg.wait_for_timeout(300);pg.evaluate("BattleActorState.set('aidan','victory',{battle:'normal'})");pg.wait_for_timeout(1800)
    r=pg.evaluate("({a:BattleActorState.get('normal'),busy:BattlePresentation.busy})")
    check(r['a']=='victory' and r['busy'] is False,'victory during the opening: not overwritten, lock released',r);pg.close()
    # 8 single settlement: every run's done resolves once with a stable result, also through stop after completion
    pg,errs=page()
    r=pg.evaluate("""async()=>{const img=document.querySelector('#bAidan2 img');const run=BattleMotion.start(img,'aidan','attack');let n=0;run.done.then(()=>n++);run.done.then(()=>n++);
      await new Promise(r=>setTimeout(r,200));BattleMotion.stop(img);BattleMotion.stop(img);BattleMotion.start(img,'aidan','attack');await new Promise(r=>setTimeout(r,50));const a=await run.done;
      await new Promise(r=>setTimeout(r,900));return {n,a,again:(await run.done)===a}}""")
    check(r['n']==2 and r['a']['reason']=='stopped' and r['again'],'run.done: resolves once (stop/replace/stop again keep the first result)',r);pg.close()
    b.close()
print('FAILS',fails);sys.exit(1 if fails else 0)

"""INT-01A BattleLoading async generation safety: the late result of a cancelled / timed-out Loading must never change a newer Loading or the battle.
Each scenario fails on the pre-fix code (INT-01 finding: cancelled Loading's asset failure leaked into the next Loading) and passes after."""
import os,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
fails=[]
def check(ok,name,detail=''):
    print(('ok   ' if ok else 'FAIL ')+name,detail)
    if not ok:fails.append(name)
INIT="""(()=>{window.__bl=[];addEventListener('battle-loading',e=>__bl.push(Object.assign({t:Math.round(performance.now())},e.detail)));window.__open=0;addEventListener('battle-opening',()=>__open++);
 window.__failN={};window.__dc={};const dec=HTMLImageElement.prototype.decode;
 HTMLImageElement.prototype.decode=function(){const u=this.src.split('/').slice(-2).join('/').split('?')[0];__dc[u]=(__dc[u]||0)+1;
  for(const k in __failN){if(u.indexOf(k)>=0&&__dc[u]<=__failN[k])return Promise.reject(new DOMException('x','EncodingError'))}return dec.call(this)}})()"""
def fresh(b,vp=(844,390)):
    c=b.new_context(viewport={'width':vp[0],'height':vp[1]},device_scale_factor=2);c.add_init_script(INIT);pg=c.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append('pageerror:'+str(e)));pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' and 'Failed to load resource' not in m.text and 'BattleLoading' not in m.text else None)
    return c,pg,errs
def boot(pg,base):
    pg.goto(base+'/index.html');pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.PrologueCombat&&window.BattleLoading');pg.wait_for_timeout(1200);pg.evaluate('closeDialogue()')
MODE="document.body.classList.contains('raiderBattleMode')?'raider':document.body.classList.contains('normalBattleMode')?'normal':null"
def hold(pg,pattern):
    h=[];pg.route(pattern,lambda r:h.append(r));return h
def pump(pg,held,how,ms,step=60):
    """answer every held request ('404' | 'ok' with the real file) for ms milliseconds (retries create new held requests)"""
    t=time.time()
    while time.time()-t<ms/1000:
        while held:
            r=held.pop(0)
            try:
                if how=='404':r.fulfill(status=404,body='x')
                else:r.continue_()
            except Exception:pass
        pg.wait_for_timeout(step)
def phases(pg):return [e['phase'] for e in pg.evaluate('__bl')]
def wait_idle(pg,limit=12000):
    t=time.time()
    while time.time()-t<limit/1000:
        if not pg.evaluate('BattleLoading.active'):return True
        pg.wait_for_timeout(40)
    return False
GOB='**/enemies/goblin/goblin_battle_idle.png'      # needed by the normal battle only (not by the raider battle)
EXE=os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None
with server(8817) as base,sync_playwright() as p:
    b=p.chromium.launch(executable_path=EXE)
    # S1: A cancelled, A's asset FAILS after the cancel -> B (different battle, healthy assets) must be unaffected
    c,pg,errs=fresh(b);boot(pg,base);h=hold(pg,GOB);pg.evaluate("BattleLoading.setLimits({minMs:2600})")
    pg.evaluate("window.__bl.length=0;window.__open=0;startAttackBattle('northGob1',180)");pg.wait_for_timeout(150);pg.evaluate("startRaiderBattle()")
    pump(pg,h,'404',1800);wait_idle(pg);pg.wait_for_timeout(300)
    L=pg.evaluate("BattleLoading.status.last")
    check(phases(pg)==['start','cancelled','start','ready'],'S1 events: A cancelled, B ready (no fallback)',phases(pg))
    check(L['state']=='ready' and not L['failed'] and not L['fallback'],"S1 A's late asset failure did not leak into B (state/failed/fallback)",{k:L[k] for k in ('state','failed','fallback','reason')})
    check(pg.evaluate(MODE)=='raider' and pg.evaluate('__open')==1,'S1 B started exactly once, A never started',(pg.evaluate(MODE),pg.evaluate('__open')))
    check(not errs,'S1 no browser errors',errs[:2]);c.close()
    # S2: A cancelled, A's assets SUCCEED later -> no double start of B
    c,pg,errs=fresh(b);boot(pg,base);h=hold(pg,GOB);pg.evaluate("BattleLoading.setLimits({minMs:900})")
    pg.evaluate("window.__bl.length=0;window.__open=0;startAttackBattle('northGob1',180)");pg.wait_for_timeout(120);pg.evaluate("startRaiderBattle()")
    pump(pg,h,'ok',800);wait_idle(pg);pg.wait_for_timeout(2500)
    check(phases(pg)==['start','cancelled','start','ready'] and pg.evaluate('__open')==1 and pg.evaluate(MODE)=='raider','S2 A succeeding late starts nothing; B starts once',(phases(pg),pg.evaluate('__open'),pg.evaluate(MODE)))
    check(not pg.evaluate("document.body.classList.contains('normalBattleMode')"),'S2 the cancelled A battle was never entered');c.close()
    # S3: completion order reversed: A's slow asset arrives long AFTER B finished and its battle is running
    c,pg,errs=fresh(b);boot(pg,base);h=hold(pg,GOB)
    pg.evaluate("window.__bl.length=0;window.__open=0;startAttackBattle('northGob1',180)");pg.wait_for_timeout(100);pg.evaluate("startRaiderBattle()")
    wait_idle(pg);pg.wait_for_timeout(1600)
    snap0=pg.evaluate("({m:%s,busy:BattlePresentation.busy,a:BattleActorState.get('raider'),f:BattleActorState.get('raider','fiona'),rbActor:rbActor,st:BattleLoading.status.state,last:BattleLoading.status.last.state})"%MODE)
    pump(pg,h,'404',1500);pg.wait_for_timeout(300)
    snap1=pg.evaluate("({m:%s,busy:BattlePresentation.busy,a:BattleActorState.get('raider'),f:BattleActorState.get('raider','fiona'),rbActor:rbActor,st:BattleLoading.status.state,last:BattleLoading.status.last.state,failed:BattleLoading.status.last.failed})"%MODE)
    check(snap0['m']=='raider' and snap0['last']=='ready' and not snap0['busy'],'S3 B finished first and its battle is running, COMMAND free',snap0)
    check({k:snap1[k] for k in snap0}==snap0 and not snap1['failed'] and phases(pg)==['start','cancelled','start','ready'],"S3 A's late failure afterwards changes nothing (state, busy, actor states, last result, events)",(snap1,phases(pg)));c.close()
    # S4: shared asset retried/failed under A, B joins mid-way: B gets its OWN bounded attempts (A's exhausted budget is not B's verdict)
    c,pg,errs=fresh(b);boot(pg,base);pg.evaluate("window.__failN={'idle_v2/aidan_idle_01':4};window.__dc={}")
    pg.evaluate("window.__bl.length=0;window.__open=0;startAttackBattle('northGob1',180)");pg.wait_for_timeout(1000);pg.evaluate("startRaiderBattle()");wait_idle(pg);pg.wait_for_timeout(2400)
    L=pg.evaluate("BattleLoading.status.last");dc=pg.evaluate("__dc['idle_v2/aidan_idle_01.png']||0")
    check(L['state']=='ready' and not L['failed'],"S4 B joining a failing shared load is judged on its own attempts: ready",{k:L[k] for k in ('state','failed','fallback')})
    check(dc<=9,'S4 decode attempts for the shared frame stay bounded (no loop)',dc)
    vis=pg.evaluate("[...document.querySelectorAll('canvas.battle-idle-canvas')].filter(c=>!c.hidden).length");check(vis>=3 and pg.evaluate(MODE)=='raider','S4 battle B shows its idle canvases',(vis,pg.evaluate(MODE)));c.close()
    # S5: shared asset reuse + retry: A then B (same battle kind after A completes) reuse decoded frames, no duplicate decode/request
    c,pg,errs=fresh(b);boot(pg,base);pg.evaluate("window.__failN={'idle/fiona_idle_03':2};window.__dc={}")
    reqs={};pg.on('request',lambda r:reqs.__setitem__(r.url,reqs.get(r.url,0)+1))
    pg.evaluate("window.__bl.length=0;startRaiderBattle()");wait_idle(pg);pg.wait_for_timeout(1800)
    pg.evaluate("for(const a of ['aidan','fiona','lou','goblin_raider'])BattleActorState.end('raider',a==='aidan'?undefined:a);document.body.classList.remove('battleMode','raiderBattleMode');document.getElementById('raiderBattle').style.display='none'")
    reqs.clear();pg.evaluate("window.__dc={}");pg.evaluate("startRaiderBattle()");wait_idle(pg)
    L=pg.evaluate("BattleLoading.status.last");png=[u for u in reqs if u.endswith('.png')]
    check(L['state']=='ready' and 395<=L['shownMs']<=760,'S5 second Loading of already-prepared assets: ready, minimum time only (no extra delay)',(L['state'],L['shownMs']))
    check(not png and not [k for k,v in pg.evaluate('__dc').items() if v>0 and 'idle' in k],'S5 no image re-requested and no re-decode of the shared frames',(png[:2],pg.evaluate('__dc')));c.close()
    # S6: after the 6 s (here 1.2 s) timeout the old work cannot touch COMMAND / status / the next Loading
    c,pg,errs=fresh(b);boot(pg,base);h=hold(pg,GOB);pg.evaluate("BattleLoading.setLimits({maxMs:1200})")
    pg.evaluate("window.__bl.length=0;window.__open=0;startAttackBattle('northGob1',180)");ok=wait_idle(pg,5000);pg.wait_for_timeout(1700)
    before=pg.evaluate("({failed:BattleLoading.status.last.failed.slice(),busy:BattlePresentation.busy,a:BattleActorState.get('normal'),m:%s,na:normalActor})"%MODE)
    check(ok and phases(pg)==['start','fallback'] and before['m']=='normal' and not before['busy'],'S6 timeout -> fallback, battle running, COMMAND free',before)
    pg.evaluate("BattleActorState.end('normal');BattleActorState.end('normal','fiona');document.body.classList.remove('battleMode','normalBattleMode');document.getElementById('attackBattle').style.display='none'")
    pg.evaluate("BattleLoading.setLimits({minMs:2600,maxMs:6000});window.__bl.length=0;startRaiderBattle()");pg.wait_for_timeout(200)
    pump(pg,h,'404',1500)            # the old, timed-out work fails NOW, in the middle of the new Loading
    wait_idle(pg);pg.wait_for_timeout(300)
    L=pg.evaluate("BattleLoading.status.last")
    check(phases(pg)==['start','ready'] and L['state']=='ready' and not L['failed'],"S6 the timed-out work's late failure did not contaminate the next Loading",{k:L[k] for k in ('state','failed','fallback')})
    if os.getenv('NEG')=='1':pg.evaluate("BattleActorState.end('raider');document.body.classList.remove('battleMode','raiderBattleMode');document.getElementById('raiderBattle').style.display='none'")   # negative control: the next battle is NOT running
    pg.wait_for_timeout(2600)
    check(pg.evaluate(MODE)=='raider' and pg.evaluate('BattlePresentation.busy') is False,'S6 next battle started and its opening has finished (input free)',(pg.evaluate(MODE),pg.evaluate('BattlePresentation.busy')));c.close()
    if os.getenv('NEG_STOP')=='1':print('FAILS',fails);sys.exit(1 if fails else 0)     # negative-control runs stop right after the checked condition
    # S7: no extra delay in the normal, healthy path
    c,pg,errs=fresh(b);boot(pg,base);pg.evaluate("window.__bl.length=0;startAttackBattle('northGob1',180)");wait_idle(pg);L=pg.evaluate("BattleLoading.status.last")
    check(L['state']=='ready' and 395<=L['shownMs']<=1100,'S7 healthy Loading stays at the minimum (no added delay)',L['shownMs']);pg.wait_for_timeout(1800)
    check(not pg.evaluate('BattlePresentation.busy') and pg.evaluate("BattleActorState.get('normal')")=='idle','S7 opening played out, COMMAND free');c.close()
    b.close()
print('FAILS',fails)
sys.exit(1 if fails else 0)

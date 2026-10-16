"""INT-01D BattleLoading safety: (A) ready-notification re-entry / one-shot pass ticket, (C) input lock handed from Loading to Opening,
(B) manifest delay / failure. Every check fails on the INT-01A code (PORT=<server of the old code> shows it) and passes after.
MUT=<name> sabotages the product source ON THE FLY (route rewrite) to prove the checks are not vacuous: see tools/qa/battle_loading_mutation.py.
Checks never use "... or True" style conditions; each one compares a measured value with the expected one."""
import os,sys,time,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
fails=[]
def check(ok,name,detail=''):
    print(('ok   ' if ok else 'FAIL ')+name,detail,flush=True)
    if not ok:fails.append(name)
MUT=os.getenv('MUT','')
MUTS={   # name -> (file, exact old text, new text)
 'nolock':('battle-loading.js',"run.lock = window.BattlePresentation && BattlePresentation.lock ? BattlePresentation.lock('loading#' + run.gen) : null;","run.lock = null;"),
 'notify_first':('battle-loading.js',"    try { resume(); }\n    finally {","    notify(run);\n    try { resume(); }\n    finally {"),
 'double_ready':('battle-loading.js',"    try { resume(); }\n    finally {","    notify(run); run.notified = false;\n    try { resume(); }\n    finally {"),
 'global_pass':('battle-loading.js',"if (pass && pass.kind === kind && pass.key === key) { pass = null; return false; }","if (pass) return false;"),
 'reusable_pass':('battle-loading.js',"if (pass && pass.kind === kind && pass.key === key) { pass = null; return false; }","if (pass && pass.kind === kind && pass.key === key) { return false; }"),
 'early_release':('battle-loading.js',"    try { resume(); }\n    finally { if (pass === ticket) pass = null; releaseLock(run); notify(run); }","    releaseLock(run);\n    try { resume(); }\n    finally { if (pass === ticket) pass = null; notify(run); }"),
 'no_manifest_wait':('battle-loading.js',"let r = await BattleMotion.ensure();","let r = {state: 'ready'};"),
 'silent_manifest_failure':('battle-loading.js',"if (r.state !== 'ready') return {ok: false, failed: ['manifest:' + (r.reason || 'failed')]};","if (r.state !== 'ready') return true;"),
 'played_first':('battle-opening.js',"      if (!window.BattleMotion || !BattleMotion.loaded || !window.BattleActorState) return false;\n      played.set(context, gen);","      played.set(context, gen);\n      if (!window.BattleMotion || !BattleMotion.loaded || !window.BattleActorState) return false;"),
}
INIT="""(()=>{window.__bl=[];window.__open=0;window.__errs=[];
 addEventListener('battle-loading',e=>{const d=e.detail;__bl.push({p:d.phase,gen:d.gen,kind:d.kind,key:d.key,reason:d.reason||null,failed:d.failed||null,
   active:BattleLoading.active,state:BattleLoading.status.state,sgen:BattleLoading.status.gen,mode:document.body.classList.contains('raiderBattleMode')?'raider':document.body.classList.contains('normalBattleMode')?'normal':null,
   busy:BattlePresentation.busy,t:Math.round(performance.now())});if(window.__onLoading)window.__onLoading(d)});
 addEventListener('battle-opening',e=>{__open++;if(window.__onOpening)window.__onOpening(e.detail)});})()"""
MODE="document.body.classList.contains('raiderBattleMode')?'raider':document.body.classList.contains('normalBattleMode')?'normal':null"
def ev(pg,js,default=None):
    try:return pg.evaluate(js)
    except Exception as e:return default
def fresh(b,bypass=False,vp=(844,390)):
    c=b.new_context(viewport={'width':vp[0],'height':vp[1]},device_scale_factor=1)
    if bypass:c.add_init_script("window.WINDBOUND_NO_BATTLE_LOADING=true")
    c.add_init_script(INIT)
    if MUT:
        f,old,new=MUTS[MUT]
        def sab(route):
            src=(ROOT/'js'/f).read_text()
            if old not in src:raise SystemExit('mutation text not found: '+MUT)
            route.fulfill(status=200,content_type='application/javascript',body=src.replace(old,new,1))
        c.route('**/js/'+f+'*',sab)
    pg=c.new_page();pg.errs=[]
    pg.on('pageerror',lambda e:pg.errs.append('pageerror:'+str(e)));pg.on('console',lambda m:pg.errs.append('console:'+m.text) if m.type=='error' and 'Failed to load resource' not in m.text else None)
    return c,pg
class Manifest:
    """holds the first motion-manifest request(s) until release(); mode 'ok' | '404' | 'bad' (unparseable)"""
    def __init__(s,ctx):s.held=[];s.mode=None;ctx.route('**/motion-manifest.json*',s.on)
    def on(s,r):
        if s.mode is None:s.held.append(r)
        else:s.answer(r,s.mode)
    def answer(s,r,mode):
        try:
            if mode=='404':r.fulfill(status=404,body='x')
            elif mode=='bad':r.fulfill(status=200,content_type='application/json',body='{"base":')
            else:r.continue_()
        except Exception:pass
    def release(s,mode='ok'):
        s.mode=mode
        while s.held:s.answer(s.held.pop(0),mode)
def _quiet_close(c):
    for q in [c]+list(c.pages):          # held (never answered) requests are dropped without Playwright's teardown noise
        try:q.unroute_all(behavior='ignoreErrors')
        except Exception:pass
    c.close()
def boot(pg,base,wait_motion=True):
    pg.goto(base+'/index.html');pg.wait_for_function('window.BattleOpening&&window.PrologueCombat&&window.BattleLoading&&window.BattlePresentation')
    if wait_motion:pg.wait_for_function('BattleMotion.manifestState==="ready"||BattleMotion.loaded')
    pg.wait_for_timeout(900);pg.evaluate('closeDialogue()')
def wait_idle(pg,limit=14000):
    t=time.time()
    while time.time()-t<limit/1000:
        if not ev(pg,'BattleLoading.active',True):return True
        pg.wait_for_timeout(40)
    return False
def pump(pg,ms,step=40):
    t=time.time()
    while time.time()-t<ms/1000:pg.wait_for_timeout(step)
def phases(pg):return [e['p'] for e in pg.evaluate('__bl')]
def wait_free(pg,limit=9000):
    t=time.time()
    while time.time()-t<limit/1000:
        if ev(pg,'BattlePresentation.busy',True) is False and not ev(pg,'BattleLoading.active',True):return True
        pg.wait_for_timeout(50)
    return False
EXE=os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None
ONLY=os.getenv('ONLY','')       # e.g. ONLY=A,C to run a subset (mutation runs)
def want(g):return not ONLY or g in ONLY.split(',')
with server(8821) as base,sync_playwright() as p:
    b=p.chromium.launch(executable_path=EXE)
    # ================= A: ready notification =================
    if want('A'):
        # A1: a synchronous 'ready' listener asks for another battle. The notification must see a COMMITTED state (battle already running, Loading finished, input still
        # closed by the opening), the second request is an ordinary new Loading, and nothing starts twice.
        c,pg=fresh(b);boot(pg,base)
        pg.evaluate("""window.__onLoading=d=>{if(d.phase==='ready'&&!window.__again){window.__again=1;startRaiderBattle();
            window.__after={active:BattleLoading.active,state:BattleLoading.status.state,gen:BattleLoading.status.gen}}};startRaiderBattle()""")
        wait_idle(pg);pg.wait_for_timeout(300);wait_idle(pg);pump(pg,2600)
        E=pg.evaluate('__bl');R=[e for e in E if e['p']=='ready']
        check(len(R)==2 and R[0]['gen']==1 and R[1]['gen']==2,'A1 each Loading generation notifies ready exactly once',[(e['p'],e['gen']) for e in E])
        check(R and R[0]['active'] is False and R[0]['state']=='ready' and R[0]['mode']=='raider','A1 at the ready notification the state is committed and the battle is already running',R[:1])
        check(R and R[0]['busy'] is True,'A1 at the ready notification input is still closed (opening took over the lock before Loading released it)',R[:1])
        a=pg.evaluate('window.__after||null')
        check(a is not None and a['active'] is True and a['state']=='preparing' and a['gen']==2,'A1 the start requested from the listener is a normal NEW Loading (not a nested/corrupted one)',a)
        check(phases(pg)==['start','ready','start','ready'],'A1 event order start,ready,start,ready',phases(pg))
        check(pg.evaluate('__open')==2,'A1 one opening per battle (no double start)',pg.evaluate('__open'))
        check(pg.evaluate('BattleLoading.status.runs')==2 and pg.evaluate(MODE)=='raider','A1 two runs, raider battle running',(pg.evaluate('BattleLoading.status.runs'),pg.evaluate(MODE)))
        check(wait_free(pg) and pg.evaluate('BattlePresentation.inputBlockers')==[],'A1 nothing left locked afterwards',ev(pg,'BattlePresentation.inputBlockers'))
        check(not pg.errs,'A1 no browser errors',pg.errs[:2]);_quiet_close(c)
        # A2: while the resumed start function runs (battle-opening fires inside it) another battle is requested: it must NOT borrow the pass ticket.
        for tag,js in (('different battle',"startAttackBattle('northGob1',180)"),('same battle again',"startRaiderBattle()")):
            c,pg=fresh(b);boot(pg,base)
            pg.evaluate("""window.__n=0;window.__onOpening=()=>{if(++__n===1){%s;window.__nest={active:BattleLoading.active,state:BattleLoading.status.state,gen:BattleLoading.status.gen,kind:BattleLoading.status.kind,normal:document.body.classList.contains('normalBattleMode')}}};startRaiderBattle()"""%js)
            wait_idle(pg);pump(pg,300);wait_idle(pg);pump(pg,2600)
            n=pg.evaluate('window.__nest||null')
            check(n is not None and n['active'] is True and n['state']=='preparing' and n['gen']==2,'A2 (%s) a start requested inside the resumed start is a new Loading, it did not pass'%tag,n)
            if tag=='different battle':check(n is not None and n['normal'] is False,'A2 (%s) the other battle did not begin synchronously'%tag,n)
            check(phases(pg).count('ready')==2 and pg.evaluate('__open')==2,'A2 (%s) exactly two battles started, one opening each'%tag,(phases(pg),pg.evaluate('__open')))
            check(not pg.errs,'A2 (%s) no browser errors'%tag,pg.errs[:2]);_quiet_close(c)
        # A3: superseding / cancelling: the old run's notification comes AFTER the new run exists and carries the OLD run's identity; it never starts anything
        c,pg=fresh(b);boot(pg,base)
        pg.evaluate("window.__onLoading=null;startAttackBattle('northGob1',180)");pg.wait_for_timeout(150);pg.evaluate("startRaiderBattle()")
        wait_idle(pg);pump(pg,2500)
        E=pg.evaluate('__bl');cx=[e for e in E if e['p']=='cancelled']
        check(phases(pg)==['start','cancelled','start','ready'],'A3 start,cancelled,start,ready',phases(pg))
        check(len(cx)==1 and cx[0]['gen']==1 and cx[0]['kind']=='normal' and cx[0]['sgen']==2 and cx[0]['active'] is True and cx[0]['state']=='preparing','A3 cancelled notification: old identity, new run already committed',cx)
        check(pg.evaluate(MODE)=='raider' and pg.evaluate('__open')==1,'A3 only the newest request started a battle, once',(pg.evaluate(MODE),pg.evaluate('__open')));_quiet_close(c)
        # A4: explicit cancel: no battle, lock released, one cancelled notification
        c,pg=fresh(b);boot(pg,base)
        pg.evaluate("startRaiderBattle()");pg.wait_for_timeout(200)
        during=pg.evaluate("({blockers:BattlePresentation.inputBlockers,busy:BattlePresentation.busy})")
        pg.evaluate("BattleLoading.cancel('test')");pg.wait_for_timeout(100);after=pg.evaluate("({blockers:BattlePresentation.inputBlockers,busy:BattlePresentation.busy,accept:BattlePresentation.acceptingInput})")
        pump(pg,1500)
        check('loading' in (during['blockers'] or []) and during['busy'] is True,'A4 during Loading the lock/blocker is present',during)
        check(phases(pg)==['start','cancelled'] and pg.evaluate(MODE) is None and pg.evaluate('__open')==0,'A4 cancel: one cancelled event, no battle started later',(phases(pg),pg.evaluate(MODE)))
        check(after['blockers']==[] and after['busy'] is False and after['accept'] is True,'A4 cancel released the lock at once',after);_quiet_close(c)
        # A5: timeout path: fallback notification once, battle starts, lock released
        c,pg=fresh(b);boot(pg,base);h=[];pg.route('**/enemies/goblin/goblin_battle_idle.png*',lambda r:h.append(r))
        pg.evaluate("BattleLoading.setLimits({maxMs:1200});startAttackBattle('northGob1',180)");wait_idle(pg,5000);pump(pg,2400)
        check(phases(pg)==['start','fallback'] and pg.evaluate(MODE)=='normal','A5 timeout -> one fallback notification, battle started',(phases(pg),pg.evaluate(MODE)))
        check(wait_free(pg) and pg.evaluate('BattlePresentation.inputBlockers')==[],'A5 lock released after the fallback battle start',ev(pg,'BattlePresentation.inputBlockers'));_quiet_close(c)
    # ================= C: input lock hand-over =================
    if want('C'):
        # C1: the lock API itself: ownership, idempotent release, cancel() cannot drop it, an old handle cannot release a newer lock
        c,pg=fresh(b);boot(pg,base)
        r=ev(pg,"""(()=>{const o=[];const h1=BattlePresentation.lock('a'),h2=BattlePresentation.lock('b');o.push(BattlePresentation.busy);
          o.push(h1.release());o.push(h1.release());o.push(BattlePresentation.busy);o.push(h2.held);BattlePresentation.cancel();o.push(BattlePresentation.busy);o.push(document.body.classList.contains('battlePresentationBusy'));
          o.push(BattlePresentation.acceptingInput);o.push(h2.release());o.push(BattlePresentation.busy);o.push(document.body.classList.contains('battlePresentationBusy'));o.push(BattlePresentation.acceptingInput);return o})()""")
        check(r==[True,True,False,True,True,True,True,False,True,False,False,True],'C1 lock ownership: idempotent release, old handle cannot free the other, cancel() keeps it, acceptingInput follows',r);_quiet_close(c)
        # C2/C3: Loading and Opening refuse direct commands; Loading release -> Opening hold has no gap; commands work again after the opening
        for kind,start,cmd,chk in (('normal',"startAttackBattle('northGob1',180)","chooseNormalAct('attack','normal_enemy_0')","({a:normalActor,s:BattleActorState.get('normal')})"),
                                   ('raider',"startRaiderBattle()","choosePartyAct('guard')","({a:rbActor,n:rbActs.length,s:BattleActorState.get('raider')})")):
            c,pg=fresh(b);boot(pg,base)
            pg.evaluate("""window.__seq=[];const mo=new MutationObserver(()=>{});mo.observe(document.body,{attributes:true,attributeFilter:['class'],attributeOldValue:true});window.__mo=mo;
              window.__flush=tag=>{for(const r of mo.takeRecords())__seq.push(['rec',(r.oldValue||'').split(/\\s+/).includes('battlePresentationBusy')]);__seq.push([tag,document.body.classList.contains('battlePresentationBusy')])};
              window.__onLoading=d=>__flush('L:'+d.phase);window.__onOpening=()=>__flush('opening');__flush('init')""")
            pg.evaluate("BattleLoading.setLimits({minMs:1200})");pg.evaluate(start);pg.wait_for_timeout(150)
            base0=pg.evaluate(chk);ld=pg.evaluate("({frozen:BattleLoading.frozen,accept:BattlePresentation.acceptingInput,blockers:BattlePresentation.inputBlockers})")
            pg.evaluate(cmd);pg.wait_for_timeout(120);base1=pg.evaluate(chk)
            check(ld['frozen'] is True and ld['accept'] is False and 'loading' in (ld['blockers'] or []),'C2 %s: Loading -> acceptingInput false, blockers name the loading'%kind,ld)
            check(base1==base0,'C2 %s: a direct command during Loading changes nothing'%kind,(base0,base1))
            # wait until the battle runs and the opening hold is active, then try again during the opening
            t=time.time()
            while time.time()-t<8 and pg.evaluate(MODE) is None:pg.wait_for_timeout(5)
            op0=pg.evaluate(chk);ob=pg.evaluate("({busy:BattlePresentation.busy,accept:BattlePresentation.acceptingInput,blockers:BattlePresentation.inputBlockers,loading:BattleLoading.active})")
            pg.evaluate(cmd);pg.wait_for_timeout(120);op1=pg.evaluate(chk)
            check(ob['busy'] is True and ob['accept'] is False and ob['loading'] is False,'C3 %s: after Loading the opening keeps input closed (no gap)'%kind,ob)
            check(op1==op0,'C3 %s: a direct command during the opening changes nothing'%kind,(op0,op1))
            wait_free(pg);pg.evaluate('__flush("end")')
            seq=pg.evaluate('__seq')
            L={s[0]:s[1] for s in seq if s[0] in ('L:start','L:ready','opening')}
            check(L.get('L:start') is True and L.get('opening') is True and L.get('L:ready') is True,'C3 %s: busy is true at Loading start, inside the resumed start (opening) and at the ready notification'%kind,L)
            # no true->false->true dip: after the first true, the only false is the final release (last element)
            first=next((i for i,s in enumerate(seq) if s[1] is True),None);tail=[s[1] for s in seq[first:]] if first is not None else []
            dips=sum(1 for i in range(1,len(tail)) if tail[i-1] is False and tail[i] is True)     # a drop followed by a return = a gap that was re-closed
            check(first is not None and dips==0 and tail[-1] is False,'C3 %s: busy class never drops between Loading and the end of the opening'%kind,tail)
            check(pg.evaluate('BattlePresentation.acceptingInput') is True and pg.evaluate('BattlePresentation.inputBlockers')==[],'C3 %s: after the opening input is accepted again'%kind)
            a0=pg.evaluate(chk);pg.evaluate(cmd);pg.wait_for_timeout(250);a1=pg.evaluate(chk)
            check(a1!=a0,'C4 %s: a command is accepted after the opening (state changed)'%kind,(a0,a1))
            check(not pg.errs,'C %s: no browser errors'%kind,pg.errs[:2]);_quiet_close(c)
        # C5: cancelled A then B: only B's lock exists; A's late end cannot release it; consecutive battles leave nothing behind
        c,pg=fresh(b);boot(pg,base);h=[];pg.route('**/enemies/goblin/goblin_battle_idle.png*',lambda r:h.append(r));pg.evaluate("BattleLoading.setLimits({minMs:2200})")
        pg.evaluate("startAttackBattle('northGob1',180)");pg.wait_for_timeout(150);pg.evaluate("startRaiderBattle()");pg.wait_for_timeout(200)
        bl=pg.evaluate('BattlePresentation.inputBlockers')
        while h:
            try:h.pop(0).fulfill(status=404,body='x')
            except Exception:pass
        pg.wait_for_timeout(300);bl2=pg.evaluate('BattlePresentation.inputBlockers')
        check(bl==['loading','lock:loading#2'] and bl2==bl,"C5 after A is cancelled only B's lock is held, and A's late failure does not touch it",(bl,bl2))
        wait_idle(pg);wait_free(pg)
        check(pg.evaluate('BattlePresentation.inputBlockers')==[] and pg.evaluate(MODE)=='raider','C5 B started; nothing left locked',pg.evaluate('BattlePresentation.inputBlockers'))
        pg.evaluate("BattleActorState.end('raider');BattleActorState.end('raider','fiona');BattleActorState.end('raider','lou');BattleActorState.end('raider','goblin_raider');document.body.classList.remove('battleMode','raiderBattleMode');document.getElementById('raiderBattle').style.display='none'")
        pg.evaluate("window.__bl.length=0;startRaiderBattle()");wait_idle(pg);wait_free(pg)
        check(phases(pg)==['start','ready'] and pg.evaluate('BattlePresentation.inputBlockers')==[],'C5 consecutive battle: normal run, nothing left locked',(phases(pg),pg.evaluate('BattlePresentation.inputBlockers')))
        check(not pg.errs,'C5 no browser errors',pg.errs[:2]);_quiet_close(c)
        # C6: fallback (timeout) still releases and the battle is playable
        c,pg=fresh(b);boot(pg,base);h=[];pg.route('**/enemies/goblin/goblin_battle_idle.png*',lambda r:h.append(r))
        pg.evaluate("BattleLoading.setLimits({maxMs:1000});startAttackBattle('northGob1',180)");wait_idle(pg,5000);wait_free(pg)
        a0=pg.evaluate("normalActor");pg.evaluate("chooseNormalAct('attack','normal_enemy_0')");pg.wait_for_timeout(250);a1=pg.evaluate("normalActor")
        check(phases(pg)==['start','fallback'] and a0!=a1,'C6 fallback battle: lock released, command accepted',(phases(pg),a0,a1));_quiet_close(c)
    # ================= B: manifest =================
    if want('B'):
        def case(delay_ms,mode,start="startRaiderBattle()",setup=None,extra_wait=2600):
            c,pg=fresh(b);m=Manifest(c)
            pg.goto(base+'/index.html');pg.wait_for_function('window.BattleOpening&&window.PrologueCombat&&window.BattleLoading');pg.wait_for_timeout(500);pg.evaluate('closeDialogue()')
            if setup:setup(pg)
            t0=time.time();pg.evaluate(start);rel=False
            while time.time()-t0<12:
                if not rel and time.time()-t0>=delay_ms/1000:m.release(mode);rel=True
                if rel and not ev(pg,'BattleLoading.active',True):break
                pg.wait_for_timeout(30)
            pump(pg,extra_wait);return c,pg,m
        # B1/B2: a delayed manifest that still arrives within Loading: the opening plays (it used to be skipped)
        for ms in (900,3200):
            c,pg,m=case(ms,'ok')
            L=pg.evaluate("BattleLoading.status.last")
            check(L['state']=='ready' and not L['failed'],'B1 manifest delayed %d ms -> Loading ready, no failure'%ms,{k:L[k] for k in ('state','failed','shownMs')})
            check(pg.evaluate('__open')==1 and pg.evaluate(MODE)=='raider','B1 manifest delayed %d ms -> the opening plays exactly once'%ms,(pg.evaluate('__open'),pg.evaluate(MODE)))
            check(L['shownMs']>=ms-250 and L['shownMs']<ms+2600,'B1 Loading waited for the manifest, not much longer (%d ms)'%L['shownMs'])
            check(pg.evaluate('BattlePresentation.inputBlockers')==[] and not pg.errs,'B1 free afterwards, no errors',(pg.evaluate('BattlePresentation.inputBlockers'),pg.errs[:2]));_quiet_close(c)
        # B3/B4: a manifest that FAILS is a recorded failure -> fallback with a reason; the battle still starts; a later Loading tries again
        for mode,why in (('404','http 404'),('bad','parse')):
            c,pg,m=case(200,mode)
            L=pg.evaluate("BattleLoading.status.last")
            check(L['state']=='failed' and L['fallback'] and L['reason']=='manifest' and any(('manifest:'+why)==f for f in L['failed']),'B3 manifest %s -> fallback, reason manifest, failure recorded'%mode,{k:L[k] for k in ('state','reason','failed')})
            check(phases(pg)==['start','fallback'] and pg.evaluate(MODE)=='raider' and pg.evaluate('__open')==0,'B3 manifest %s -> battle still starts (no opening)'%mode,(phases(pg),pg.evaluate(MODE),pg.evaluate('__open')))
            check(wait_free(pg) and pg.evaluate('BattlePresentation.inputBlockers')==[],'B3 manifest %s -> not locked afterwards'%mode)
            st=pg.evaluate("[BattleMotion.manifestState,BattleMotion.manifestError]");check(st[0]=='failed' and why in (st[1] or ''),'B3 manifest state failed with its reason',st)
            if mode=='404':       # next Loading: manifest now fine -> own fresh attempt, opening plays
                pg.evaluate("BattleActorState.end('raider');BattleActorState.end('raider','fiona');BattleActorState.end('raider','lou');BattleActorState.end('raider','goblin_raider');document.body.classList.remove('battleMode','raiderBattleMode');document.getElementById('raiderBattle').style.display='none'")
                m.mode='ok'          # the manifest is healthy again for the next request
                pg.evaluate("window.__bl.length=0;window.__open=0;startRaiderBattle()");wait_idle(pg);pump(pg,2400)
                L=pg.evaluate("BattleLoading.status.last")
                check(L['state']=='ready' and pg.evaluate('__open')==1 and pg.evaluate("BattleMotion.manifestState")=='ready','B3 the next Loading retried the manifest: ready and the opening plays',(L['state'],pg.evaluate('__open')))
            check(not pg.errs,'B3 %s no browser errors'%mode,pg.errs[:2]);_quiet_close(c)
        # B5: a manifest that never answers: the 6 s rule (here 1.5 s) applies, the battle starts without opening; a late answer changes nothing
        c,pg=fresh(b);m=Manifest(c);pg.goto(base+'/index.html');pg.wait_for_function('window.BattleOpening&&window.PrologueCombat&&window.BattleLoading');pg.wait_for_timeout(500);pg.evaluate('closeDialogue()')
        pg.evaluate("BattleLoading.setLimits({maxMs:1500});startRaiderBattle()");t0=time.time();wait_idle(pg,6000);took=time.time()-t0;pump(pg,1800)
        L=pg.evaluate("BattleLoading.status.last");before=pg.evaluate("({m:%s,o:__open,busy:BattlePresentation.busy})"%MODE)
        m.release('ok');pump(pg,1500);after=pg.evaluate("({m:%s,o:__open,busy:BattlePresentation.busy})"%MODE)
        check(L['state']=='failed' and L['reason']=='timeout' and 1.2<took<2.6 and before['m']=='raider' and before['o']==0,'B5 hung manifest: timeout fallback within the limit, battle starts without opening',(L['state'],L['reason'],round(took,2),before))
        check(after==before,"B5 the manifest answering late changes nothing in the running battle",(before,after));_quiet_close(c)
        # B6: cancelled A (waiting for the manifest) and then B: A's manifest wait never starts A or contaminates B
        c,pg=fresh(b);m=Manifest(c);pg.goto(base+'/index.html');pg.wait_for_function('window.BattleOpening&&window.PrologueCombat&&window.BattleLoading');pg.wait_for_timeout(500);pg.evaluate('closeDialogue()')
        pg.evaluate("startAttackBattle('northGob1',180)");pg.wait_for_timeout(200);pg.evaluate("startRaiderBattle()");pg.wait_for_timeout(500);m.release('ok');wait_idle(pg);pump(pg,2500)
        L=pg.evaluate("BattleLoading.status.last")
        check(phases(pg)==['start','cancelled','start','ready'] and L['state']=='ready' and not L['failed'],'B6 A cancelled while waiting for the manifest, B ready',(phases(pg),L['state'],L['failed']))
        check(pg.evaluate(MODE)=='raider' and pg.evaluate('__open')==1,'B6 only B started, with its opening',(pg.evaluate(MODE),pg.evaluate('__open')));_quiet_close(c)
        # B7: no extra wait when the manifest is already loaded (normal path)
        c,pg=fresh(b);boot(pg,base);pg.evaluate("window.__bl.length=0;startAttackBattle('northGob1',180)");wait_idle(pg);L=pg.evaluate("BattleLoading.status.last");pump(pg,2000)
        check(L['state']=='ready' and 395<=L['shownMs']<=1100 and pg.evaluate('__open')==1,'B7 healthy path: minimum display only, opening plays',(L['state'],L['shownMs'],pg.evaluate('__open')));_quiet_close(c)
        # B8: BattleOpening.play consumes its once-per-battle mark only when playback is actually possible (bypass = no Loading, manifest not loaded at battle start)
        c,pg=fresh(b,bypass=True);m=Manifest(c);pg.goto(base+'/index.html');pg.wait_for_function('window.BattleOpening&&window.PrologueCombat&&window.BattleLoading');pg.wait_for_timeout(500);pg.evaluate('closeDialogue()')
        pg.evaluate("startRaiderBattle()");pg.wait_for_timeout(800);o0=pg.evaluate('__open');m.release('ok');pg.wait_for_function('BattleMotion.loaded');pg.wait_for_timeout(600)
        r1=pg.evaluate("BattleOpening.play('raider')");pg.wait_for_timeout(200);r2=pg.evaluate("BattleOpening.play('raider')")
        check(o0==0 and bool(r1) and r2 is False and pg.evaluate('__open')==1,'B8 unavailable play did not use up the battle\'s opening; once playable it plays once, never twice',(o0,r1,r2,pg.evaluate('__open')));_quiet_close(c)
    b.close()
print('FAILS',fails)
sys.exit(1 if fails else 0)

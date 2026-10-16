"""INT-02 adapter contract: BattleAdmissionAdapter connects the REAL BattleLoading / BattleOpening / BattlePresentation / PrologueCombat to the REAL BattleCommandGate.
Every case runs the real battle-start path (Loading enabled) unless it says otherwise. A per-frame recorder samples (adapter phase, gate allowed, Loading frozen/active,
Presentation busy) so "never admitted too early" is measured on every frame, not at a few instants. NEG=<name> runs a negative control (the check must then FAIL)."""
import os,sys,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
fails=[];MUT=os.getenv('MUT','')
MUTS={'startverified':("if (cur.battle && startVerified(cur)) cur.gen = combatGen(); else cur.startFailed = true;","cur.gen = combatGen();"),
      'stale':("cur && cur.n === d.gen && !cur.settled","cur && !cur.settled"),
      'cancel':("if (d.phase === 'cancelled') { cur.cancelled = true; cur.settled = true; }","if (d.phase === 'cancelled') { cur.settled = true; }")}
def mutate(c):
    """negative control: serve a deliberately broken adapter (the matching checks must then FAIL)"""
    if not MUT:return
    src=(Path(__file__).resolve().parents[2]/'js/battle-admission-adapter.js').read_text();a,bb=MUTS[MUT];assert src.count(a)==1,MUT
    c.route('**/battle-admission-adapter.js*',lambda r:r.fulfill(status=200,content_type='application/javascript',body=src.replace(a,bb)))
def check(ok,name,detail=''):
    print(('ok   ' if ok else 'FAIL ')+name,detail)
    if not ok:fails.append(name)
REC="""(()=>{window.__f=[];window.__ev=[];window.__open=0;
 addEventListener('battle-loading',e=>__ev.push(Object.assign({k:'L',t:Math.round(performance.now())},e.detail)));
 addEventListener('battle-opening',e=>{__open++;__ev.push({k:'O',t:Math.round(performance.now()),context:e.detail.context})});
 const mode=()=>document.body.classList.contains('raiderBattleMode')?'raider':document.body.classList.contains('normalBattleMode')?'normal':null;
 (function loop(){const A=window.BattleAdmissionAdapter,G=window.BattleCommandGate;
  if(A&&G&&window.BattleLoading&&window.BattlePresentation&&window.__rec!==false){let p=null,s=null;try{p=A.provider()}catch(e){p={err:String(e)}}
   try{s=G.snapshot(mode()||'normal')}catch(e){s={err:String(e)}}
   __f.push({t:Math.round(performance.now()),ph:p&&p.phase||null,pn:!!p,op:p&&p.opening||null,allowed:!!(s&&s.allowed),reason:s&&s.reason||null,fz:BattleLoading.frozen,act:BattleLoading.active,busy:BattlePresentation.busy,m:mode(),acc:BattlePresentation.acceptingInput})}
  requestAnimationFrame(loop)})()})()"""
def fresh(b,base,init='',vp=(844,390)):
    c=b.new_context(viewport={'width':vp[0],'height':vp[1]},device_scale_factor=1);c.add_init_script(REC+';\n'+init);mutate(c);pg=c.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append('pageerror:'+str(e)));pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' and 'Failed to load resource' not in m.text else None)
    pg.goto(base+'/index.html');pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.PrologueCombat&&window.BattleLoading&&window.BattleAdmissionAdapter');pg.wait_for_timeout(1000);pg.evaluate('closeDialogue()')
    return c,pg,errs
def fresh_no_manifest(b,base,init,vp=(844,390)):
    c=b.new_context(viewport={'width':vp[0],'height':vp[1]},device_scale_factor=1);c.add_init_script(REC+';\n'+init);mutate(c);pg=c.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append('pageerror:'+str(e)));pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' and 'Failed to load resource' not in m.text else None)
    return c,pg,errs
CALL={'normal':"startAttackBattle('northGob1',180)",'raider':"startRaiderBattle()"}
ACT={'normal':"chooseNormalAct('attack','normal_enemy_0')",'raider':"choosePartyAct('guard')"}
OBS={'normal':"({actor:normalActor})",'raider':"({actor:rbActor,acts:rbActs.length})"}
def reset_rec(pg):pg.evaluate('__f.length=0;__ev.length=0;__open=0')
def settle(pg,kind,limit=12000):
    """wait until the battle is in the input state (adapter phase input AND gate allowed) or the limit"""
    t=time.time()
    while time.time()-t<limit/1000:
        if pg.evaluate("(k)=>BattleCommandGate.canInteract(k)",kind):return True
        pg.wait_for_timeout(40)
    return False
def frames(pg):
    pg.wait_for_timeout(150)           # let the per-frame recorder sample the final state too
    return pg.evaluate('__f.slice()')
def early(fr):
    """frames that were admitted although some independent layer said no"""
    return [f for f in fr if f['allowed'] and (f['fz'] or f['act'] or f['busy'] or f['ph']!='input')]
def command_works(pg,kind):
    pg.evaluate("document.body.classList.contains('raiderBattleMode')||0")
    st0=pg.evaluate(OBS[kind]);pg.evaluate(ACT[kind]);pg.wait_for_timeout(300);st1=pg.evaluate(OBS[kind])
    return (st0['actor']=='aidan' and st1['actor']=='fiona')and(kind=='normal' or st1['acts']==st0['acts']+1),(st0,st1)
EXE=os.getenv('PW_CHROMIUM_EXECUTABLE') or None
with server(8831) as base,sync_playwright() as p:
    b=p.chromium.launch(executable_path=EXE)
    # ---- A1: normal and boss start through the real Loading: never admitted early, ordered phases, a real command accepted at the end
    for kind in ('normal','raider'):
        c,pg,errs=fresh(b,base)
        reset_rec(pg);pg.evaluate(CALL[kind]);ok=settle(pg,kind)
        fr=frames(pg);ph=[]
        for f in fr:
            if not ph or ph[-1]!=f['ph']:ph.append(f['ph'])
        check(ok,'A1 %s: reaches the input state through Loading -> Opening'%kind,ph)
        check(not early(fr),'A1 %s: on EVERY frame allowed implies adapter=input and Loading/Presentation idle'%kind,early(fr)[:2])
        i_load=next((i for i,x in enumerate(ph) if x=='loading'),-1);i_op=next((i for i,x in enumerate(ph) if x=='opening'),-1);i_in=next((i for i,x in enumerate(ph) if x=='input'),-1)
        check(0<=i_load<i_op<i_in,'A1 %s: phases are ordered loading -> opening -> input (no phase skipped)'%kind,ph)
        r=pg.evaluate('BattleAdmissionAdapter.request')
        check(r and r['gen'] is not None and r['gen']==pg.evaluate('PrologueCombat.generation') and r['openingSeen'] and r['openingDone'],'A1 %s: generation bound at ready, Opening seen and finished'%kind,r)
        ev=pg.evaluate('__ev.filter(e=>e.k=="L").map(e=>e.phase)');check(ev[:2]==['start','ready'],'A1 %s: real notifications start -> ready'%kind,ev)
        w,d=command_works(pg,kind);check(w,'A1 %s: a real command is accepted and its effect measured'%kind,d)
        check(not errs,'A1 %s: no browser errors'%kind,errs[:2]);c.close()
    # ---- A3: manifest unavailable (404) and hanging (own 5 s limit): Opening skipped, battle continues, COMMAND only after a verified start
    for label,route in (('404',lambda r:r.fulfill(status=404,body='no')),('hang',lambda r:None)):
        c,pg,errs=fresh_no_manifest(b,base,'')
        c.route('**/motion-manifest.json*',route)
        pg.goto(base+'/index.html');pg.wait_for_function('window.PrologueCombat&&window.BattleLoading&&window.BattleAdmissionAdapter');pg.wait_for_timeout(900);pg.evaluate('closeDialogue()')
        reset_rec(pg);pg.evaluate(CALL['normal']);ok=settle(pg,'normal',16000)
        fr=frames(pg);ev=pg.evaluate('__ev.filter(e=>e.k=="L")');r=pg.evaluate('BattleAdmissionAdapter.request');pr=pg.evaluate('BattleAdmissionAdapter.provider()')
        check(ok,'A3 manifest %s: the battle still reaches the input state (Opening skipped, battle continues)'%label)
        fb=[e for e in ev if e['phase']=='fallback']
        # 404 is a recorded manifest failure; a hanging manifest is stopped by whichever limit comes first (the manifest's own 5 s or Loading's 6 s)
        check(len(fb)==1 and fb[0].get('reason') in (('manifest',) if label=='404' else ('manifest','timeout')),'A3 manifest %s: exactly one fallback with the failure reason'%label,[(e['phase'],e.get('reason')) for e in ev])
        check(pg.evaluate('__open')==0,'A3 manifest %s: no Opening was played'%label)
        check(pr and pr['opening']=='skipped' and pr['skipAllowed'] is True and fb and pr['skipReason']=='fallback:'+str(fb[0].get('reason')),'A3 manifest %s: recorded as an approved skip with its exact reason'%label,pr)
        check(not early(fr),'A3 manifest %s: never admitted before the start was verified / while Loading or Presentation was busy'%label,early(fr)[:2])
        w,d=command_works(pg,'normal');check(w,'A3 manifest %s: a real command is accepted after the skip'%label,d);c.close()
    # ---- A4: Opening not played although the manifest is fine (actors hidden): ready (not fallback) + skip reason opening-not-played
    c,pg,errs=fresh(b,base);pg.add_style_tag(content='#bAidan2 img,#bFiona2 img{display:none !important}')
    reset_rec(pg);pg.evaluate(CALL['normal']);ok=settle(pg,'normal');pr=pg.evaluate('BattleAdmissionAdapter.provider()')
    check(ok and pg.evaluate('__open')==0 and pr['opening']=='skipped' and pr['skipReason']=='opening-not-played' and pr['skipAllowed'] is True,'A4 Opening not played (hidden actors): approved skip with fixed reason',pr)
    check(not early(frames(pg)),'A4 never admitted early');c.close()
    # ---- A2: the start function throws. BEFORE the combat generation is added -> failed, COMMAND never opens. AFTER begin -> state is complete and verified, so admitted.
    for label,hook in (('pre-begin',"(()=>{window.__throwHud=true;const o=window.updateNormalPartyHud;window.updateNormalPartyHud=function(){if(window.__throwHud&&BattleLoading.status.state==='ready'){window.__throwHud=false;throw new Error('injected before beginNormal')}return o.apply(this,arguments)}})()"),
                       ('post-begin',"(()=>{window.__throwB=true;const o=window.showBattleBanner;window.showBattleBanner=function(){if(window.__throwB&&!BattleLoading.active){window.__throwB=false;throw new Error('injected after beginNormal')}return o.apply(this,arguments)}})()")):
        c,pg,errs=fresh(b,base);pg.evaluate(hook);reset_rec(pg);pg.evaluate(CALL['normal']);pg.wait_for_timeout(5000)
        fr=frames(pg);ev=pg.evaluate('__ev.filter(e=>e.k=="L").map(e=>e.phase)');r=pg.evaluate('BattleAdmissionAdapter.request');pr=pg.evaluate('BattleAdmissionAdapter.provider()')
        check('ready' in ev or 'fallback' in ev,'A2 %s: Loading still notifies ready although resume() threw (the documented existing behaviour)'%label,ev)
        if label=='pre-begin':
            check(r['startFailed'] is True and r['gen'] is None and pr['phase']=='failed','A2 pre-begin: adapter marks the start failed (generation was not added)',r)
            check(not any(f['allowed'] for f in fr) and not pg.evaluate("BattleCommandGate.canInteract('normal')"),'A2 pre-begin: COMMAND is never admitted (every frame, and now)')
            before=pg.evaluate(OBS['normal']);pg.evaluate(ACT['normal']);pg.wait_for_timeout(250);check(pg.evaluate(OBS['normal'])==before,'A2 pre-begin: a direct command changes nothing',before)
        else:
            w,d=command_works(pg,'normal');check(r['startFailed'] is False and r['gen']==pg.evaluate('PrologueCombat.generation') and w,'A2 post-begin (only the banner/HUD refresh threw): core state complete and verified -> admitted, command works',(r,d))
            check(not early(fr),'A2 post-begin: still never admitted early')
        c.close()
    # ---- A5/A7: replacement, cancel notifications of the OLD request, and stale/forged notifications never touch the current request
    c,pg,errs=fresh(b,base);pg.evaluate('BattleLoading.setLimits({minMs:1500})');reset_rec(pg)
    pg.evaluate(CALL['normal']);pg.wait_for_timeout(150);r1=pg.evaluate('BattleAdmissionAdapter.request')
    pg.evaluate(CALL['raider']);pg.wait_for_timeout(100);r2=pg.evaluate('BattleAdmissionAdapter.request')
    check(r2['rid']!=r1['rid'] and r2['battle']=='raider' and r2['cancelled'] is False,'A5 replacement: the new request owns the ledger and is not marked cancelled by the old run\'s late cancelled',(r1['rid'],r2['rid'],r2['cancelled']))
    pg.evaluate("dispatchEvent(new CustomEvent('battle-loading',{detail:{phase:'ready',kind:'normal',key:'northGob1',gen:%d}}))"%r1['n'])
    pg.evaluate("dispatchEvent(new CustomEvent('battle-loading',{detail:{phase:'cancelled',kind:'normal',key:'northGob1',gen:%d}}))"%r1['n'])
    pg.evaluate("dispatchEvent(new CustomEvent('battle-loading',{detail:{phase:'ready',kind:'raider',key:'raider',gen:99}}))")
    r3=pg.evaluate('BattleAdmissionAdapter.request');check({k:r3[k] for k in ('rid','gen','cancelled','startFailed','settled')}=={k:r2[k] for k in ('rid','gen','cancelled','startFailed','settled')},'A7 forged ready/cancelled for an old or unknown gen leave the current request unchanged',r3)
    ok=settle(pg,'raider');check(ok and pg.evaluate("document.body.classList.contains('raiderBattleMode')"),'A5 the replacing boss battle reaches input',None)
    check(not early(frames(pg)),'A5 never admitted early across the replacement')
    # A11: consecutive battles - a receipt issued in the first battle is dead in the next
    rc=pg.evaluate("window.__rc=BattleCommandGate.issue('raider'),!!window.__rc");check(rc,'A11 receipt issued while the boss battle is in input')
    pg.evaluate(CALL['raider']);pg.wait_for_timeout(120)
    check(pg.evaluate("BattleCommandGate.valid(window.__rc,'raider')")==False and pg.evaluate("BattleCommandGate.commit(window.__rc,{who:'aidan',kind:'guard'})")==False,'A11 consecutive start: the old receipt is invalid and cannot commit (during the new Loading)')
    ok=settle(pg,'raider');check(ok and pg.evaluate("BattleCommandGate.valid(window.__rc,'raider')")==False,'A11 and still invalid after the new battle reaches input (new request id / generation)')
    check(not errs,'A5/A11 no browser errors',errs[:2]);c.close()
    # ---- A6: pagehide during Loading cancels: nothing starts, adapter=cancelled, gate refuses
    c,pg,errs=fresh(b,base);pg.evaluate('BattleLoading.setLimits({minMs:2500})');reset_rec(pg);pg.evaluate(CALL['normal']);pg.wait_for_timeout(200)
    pg.evaluate("dispatchEvent(new Event('pagehide'))");pg.wait_for_timeout(300);pr=pg.evaluate('BattleAdmissionAdapter.provider()');pg.wait_for_timeout(3000)
    check(pr['phase']=='cancelled' and pg.evaluate("document.body.classList.contains('battleMode')")==False and not any(f['allowed'] for f in frames(pg)),'A6 pagehide: cancelled, no battle, never admitted',pr);c.close()
    # ---- A8: RESULT: phase ended, commands refused, the result button still works and returns to a non-battle state; then a second battle works (A11)
    c,pg,errs=fresh(b,base);reset_rec(pg);pg.evaluate("startAttackBattle('mossSlime1',60)");settle(pg,'normal')
    pg.evaluate("PrologueCombat.targets('normal');finishAttackBattle()");pg.wait_for_function("document.body.classList.contains('battleResultMode')",timeout=9000);pg.wait_for_timeout(200)
    pr=pg.evaluate('BattleAdmissionAdapter.provider()');s=pg.evaluate("BattleCommandGate.snapshot('normal')")
    check(pr['phase']=='ended' and s['allowed'] is False and s['reason'] in ('result','no-live-targets'),'A8 RESULT: adapter=ended, gate refuses (reason is the last failing check: result, or no live targets once the enemies are down)',(pr['phase'],s['reason']))
    pg.locator('#resultContinue').click();pg.wait_for_timeout(500)
    check(pg.evaluate("document.body.classList.contains('battleMode')")==False and pg.evaluate("BattleCommandGate.canInteract('normal')")==False,'A8 after RESULT confirm: battle UI closed, no command admitted')
    reset_rec(pg);pg.evaluate("startAttackBattle('mossSlime1',60)");ok=settle(pg,'normal');w,d=command_works(pg,'normal')
    check(ok and w and not early(frames(pg)),'A8/A11 the next battle after RESULT is a fresh request and works',d);check(not errs,'A8 no browser errors',errs[:2]);c.close()
    # ---- A9: Loading bypass (localhost test mode): implicit request keyed on the generation; Opening still blocks; command works after
    c,pg,errs=fresh(b,base,"window.WINDBOUND_NO_BATTLE_LOADING=true")
    check(pg.evaluate('BattleLoading.bypassed')==True,'A9 bypass is on in this context')
    reset_rec(pg);pg.evaluate(CALL['normal']);ok=settle(pg,'normal');pr=pg.evaluate('BattleAdmissionAdapter.provider()');fr=frames(pg)
    check(ok and pr['requestId'].startswith('implicit#') and pg.evaluate('__ev.filter(e=>e.k=="L").length')==0,'A9 bypass: no Loading notifications; implicit request',pr)
    check(not [f for f in fr if f['allowed'] and (f['busy'] or f['ph']!='input')],'A9 bypass: never admitted while Presentation/Opening is busy')
    w,d=command_works(pg,'normal');check(w,'A9 bypass: a real command is accepted',d);c.close()
    # ---- A10: Loading present but no request in the ledger (a "battle" that never went through the gate) is refused
    c,pg,errs=fresh(b,base);pg.evaluate("document.body.classList.add('battleMode','normalBattleMode')")
    s=pg.evaluate("BattleCommandGate.snapshot('normal')");pr=pg.evaluate('BattleAdmissionAdapter.provider()')
    check(pr is None and s['allowed'] is False,'A10 no ledger entry while Loading is enabled: provider=null, gate refuses',(pr,s['reason']));c.close()
    # ---- A12: independence of the layers (negative controls): even a provider that ALWAYS says input cannot open COMMAND during Loading (L1) or Opening (L2)
    c,pg,errs=fresh(b,base);pg.evaluate("BattleLoading.setLimits({minMs:1200})");reset_rec(pg)
    pg.evaluate("""window.__orig=BattleAdmissionAdapter.provider;BattleCommandGate.installAdmissionProvider(()=>{const b=document.body.classList.contains('raiderBattleMode')?'raider':'normal';return {requestId:'naive',battle:b,generation:PrologueCombat.generation,phase:'input',opening:'completed',skipAllowed:false,skipReason:''}})""")
    pg.evaluate(CALL['normal']);settle(pg,'normal');fr=frames(pg)
    check(not [f for f in fr if f['allowed'] and (f['fz'] or f['busy'])],'A12 naive always-input provider: Loading(frozen) and Opening(busy) still refuse on every frame (independent layers)',len(fr))
    check(any(f['fz'] for f in fr) and any(f['busy'] and not f['fz'] for f in fr),'A12 the run really contained a frozen phase and a busy-after-Loading (Opening) phase',(sum(f['fz'] for f in fr),sum(1 for f in fr if f['busy'] and not f['fz'])));c.close()
    b.close()
print('FAILS',fails);sys.exit(1 if fails else 0)

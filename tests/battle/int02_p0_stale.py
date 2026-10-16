"""INT-02-P0: a failed / cancelled start must never come back to life. Real Loading + Opening + adapter + Gate, normal and boss.
 T1 a receipt issued in a good battle is refused after the NEXT battle's start threw (post-begin-ui) - no new receipt can be issued either
 T2 late / duplicate / foreign 'ready' notifications for the failed request (same gen, gen+1, started:true, forged combatGen) change nothing
 T3 cancel during Loading, then a late 'ready' (started:true) for the cancelled gen: still cancelled, never admitted
 T4 a genuine battle after the failure is playable and the old receipt is still refused
 T5 a notification WITHOUT the started flag (old BattleLoading) / started:false is never success (synthetic, on a request opened by a real 'start')"""
import os,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
MODE=os.getenv('MODE','enabled');PORT=int(os.getenv('P0PORT','8843'))
START={'normal':"startAttackBattle('fieldGob3',100)",'raider':'startRaiderBattle()'}
SETUP="""b=>{window.__b=b;window.__choose=b==='normal'?chooseNormalAct:choosePartyAct;window.__acts=()=>b==='normal'?normalActs.length:rbActs.length;}"""
CLEAN="""()=>{try{PrologueCombat.cancel()}catch(e){};try{devResetScreens()}catch(e){};document.body.classList.remove('battleMode','normalBattleMode','raiderBattleMode','raiderFinishing');
 for(const s of ['#attackBattle','#raiderBattle']){const el=document.querySelector(s);if(el)el.style.display='none'};try{BattleLoading.cancel('test-cleanup')}catch(e){}}"""
INJ="""b=>{let fired=false;const un=b==='normal'?'updateAttackBattle':'updateRaider',u=window[un];window[un]=function(...a){if(!fired){fired=true;throw new Error('INJECT post-begin-ui')}return u.apply(this,a)}}"""
fails=[]
def check(ok,name,detail=''):
    print(('ok   ' if ok else 'FAIL ')+name,detail,flush=True)
    if not ok:fails.append(name)
def wait_input(pg,sec=12):
    for _ in range(int(sec*25)):
        if pg.evaluate('BattleCommandGate.canInteract(__b)'):return True
        pg.wait_for_timeout(40)
    return False
ST="()=>({can:!!BattleCommandGate.canInteract(__b),phase:(BattleAdmissionAdapter.provider()||{}).phase||null,gen:PrologueCombat.generation})"
def fire(pg,gen,**kw):
    pg.evaluate("([g,kw])=>dispatchEvent(new CustomEvent('battle-loading',{detail:Object.assign({kind:__b,key:__b,gen:g},kw)}))",[gen,kw]);pg.wait_for_timeout(150)
with server(PORT) as base,sync_playwright() as pw:
    br=pw.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE') or None)
    for b in ['normal','raider']:
        c=br.new_context(viewport={'width':1280,'height':720})
        if MODE=='bypass':c.add_init_script('window.WINDBOUND_NO_BATTLE_LOADING=true;')
        pg=c.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto(base+'/index.html?dev=1');pg.wait_for_function('window.BattleAdmissionAdapter&&window.BattleLoading&&BattleMotion.loaded&&window.BattleUIState');pg.wait_for_timeout(1200)
        pg.evaluate('closeDialogue()');pg.evaluate(SETUP,b)
        # good battle #1 -> a genuine receipt
        pg.evaluate("s=>eval(s)",START[b]);ok1=wait_input(pg);pg.wait_for_timeout(300)
        pg.evaluate("()=>{window.__rc=BattleCommandGate.issue(__b)||null}");rc=pg.evaluate('!!window.__rc')
        check(ok1 and rc,'%s T0 good battle admitted, receipt issued'%b)
        pg.evaluate(CLEAN);pg.wait_for_timeout(400)
        # failing battle #2
        pg.evaluate(INJ,b);pg.evaluate("s=>{try{eval(s)}catch(e){}}",START[b]);pg.wait_for_timeout(3200)
        s=pg.evaluate(ST);check(not s['can'] and s['phase']=='failed','%s T1 failed start: Gate closed, phase failed'%b,s)
        n0=pg.evaluate('__acts()');pg.evaluate("()=>{try{BattleCommandGate.commit(window.__rc,{who:'aidan',kind:'guard',target:'aidan'})}catch(e){}}")
        check(pg.evaluate('__acts()')==n0,'%s T1 old receipt refused after the failed start'%b)
        check(pg.evaluate("()=>{try{return BattleCommandGate.issue(__b)||null}catch(e){return null}}") is None,'%s T1 no new receipt can be issued'%b)
        n0=pg.evaluate('__acts()');pg.evaluate("()=>{try{__choose('guard','aidan')}catch(e){}}");check(pg.evaluate('__acts()')==n0,'%s T1 guard not committed'%b)
        # T2 late / duplicate / foreign notifications
        rq=pg.evaluate('BattleAdmissionAdapter.request') or {'n':0};g=pg.evaluate('PrologueCombat.generation')
        for label,gn,kw in (('same-gen ready started:true',rq['n'],{'phase':'ready','started':True,'combatGen':g}),('same-gen fallback started:true',rq['n'],{'phase':'fallback','reason':'timeout','started':True,'combatGen':g}),
                            ('next-gen ready started:true',rq['n']+1,{'phase':'ready','started':True,'combatGen':g}),('old-gen ready started:true',rq['n']-1,{'phase':'ready','started':True,'combatGen':g})):
            if MODE!='enabled':continue   # bypass has no Loading ledger / notifications
            fire(pg,gn,**kw);s=pg.evaluate(ST);check(not s['can'] and s['phase']=='failed','%s T2 late/duplicate %s ignored'%(b,label),s)
        # T4 genuine battle after the failure
        pg.evaluate(CLEAN);pg.wait_for_timeout(400);pg.evaluate("s=>{try{eval(s)}catch(e){}}",START[b]);ok2=wait_input(pg);pg.wait_for_timeout(300)
        check(ok2,'%s T4 genuine battle after the failure is admitted'%b)
        n0=pg.evaluate('__acts()');pg.evaluate("()=>{try{BattleCommandGate.commit(window.__rc,{who:'aidan',kind:'guard',target:'aidan'})}catch(e){}}")
        check(pg.evaluate('__acts()')==n0,'%s T4 old receipt still refused in the new battle'%b)
        # P0-D: observe the real effect (before: `__acts()>n0 or b=='normal'` was vacuously true for normal). The actor must advance aidan->fiona and, for raider, the queue grows by one.
        ST2="()=>({actor:__b==='normal'?normalActor:rbActor,acts:__acts()})"
        pre=pg.evaluate(ST2);pg.evaluate("()=>{__choose('guard','aidan')}");pg.wait_for_timeout(300);post=pg.evaluate(ST2)
        check(pre['actor']=='aidan' and post['actor']=='fiona' and (b=='normal' or post['acts']==pre['acts']+1),'%s T4 a genuine guard is accepted (observed actor %s->%s, queue %s->%s)'%(b,pre['actor'],post['actor'],pre['acts'],post['acts']))
        # T3 cancel during Loading, then a late ready
        if MODE=='enabled':
            pg.evaluate(CLEAN);pg.wait_for_timeout(400);pg.evaluate('BattleLoading.setLimits({minMs:1500})')
            pg.evaluate("s=>{try{eval(s)}catch(e){}}",START[b]);pg.wait_for_timeout(300)
            check(pg.evaluate('BattleLoading.active'),'%s T3 loading active'%b)
            pg.evaluate("BattleLoading.cancel('race-test')");pg.wait_for_timeout(200)
            rq=pg.evaluate('BattleAdmissionAdapter.request');g=pg.evaluate('PrologueCombat.generation')
            fire(pg,rq['n'],phase='ready',started=True,combatGen=g+1)
            s=pg.evaluate(ST);check(not s['can'] and s['phase'] in ('cancelled','idle',None),'%s T3 cancelled request + late ready stays closed'%b,s)
            pg.wait_for_timeout(2000);s=pg.evaluate(ST);check(not s['can'],'%s T3 still closed after the original timers elapsed'%b,s)
            # T5 flag-less / false notifications on a request opened by a real 'start'
            pg.evaluate(CLEAN);pg.wait_for_timeout(400)
            for label,kw in (('no flag',{}),('started:false',{'started':False,'combatGen':None}),('started:"true" (string)',{'started':'true','combatGen':1}),('started:true without combatGen',{'started':True})):
                pg.evaluate(CLEAN);pg.evaluate("s=>{try{eval(s)}catch(e){}}",START[b]);pg.wait_for_timeout(200)
                n=pg.evaluate('BattleAdmissionAdapter.request.n');pg.evaluate("BattleLoading.cancel('t5')")   # settle the real run so only the synthetic terminal event decides
                pg.evaluate("n=>dispatchEvent(new CustomEvent('battle-loading',{detail:{phase:'start',kind:__b,key:__b,gen:n+100}}))",n)
                fire(pg,n+100,phase='ready',**kw);s=pg.evaluate(ST);check(not s['can'] and s['phase']=='failed','%s T5 ready %s is never success (phase failed)'%(b,label),s)
        check(not errs,'%s no unexpected page errors'%b,errs[:2]);c.close()
    br.close()
print('FAILS',len(fails),fails);sys.exit(1 if fails else 0)

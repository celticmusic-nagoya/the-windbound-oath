"""INT-02-P0: start-failure fault injection (12 cases = 6 injection points x normal/boss), same conditions as Codex INT-02-X U-02.
REAL BattleLoading / BattleOpening / BattleAdmissionAdapter / BattleCommandGate. One public function is made to throw ONCE; 3.2 s later every action route is probed and
nothing may commit. Then a fresh genuine battle must be playable, and the old receipt (if one could be issued) must be refused.
 MODE=enabled|bypass|absent (absent = battle-loading.js not served; bypass = WINDBOUND_NO_BATTLE_LOADING=true, localhost test flag).  Prints one RESULT line per case (parsed by the report tooling)."""
import os,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
MODE=os.getenv('MODE','enabled');PORT=int(os.getenv('P0PORT','8841'));OUT=os.getenv('P0OUT','')
START={'normal':"startAttackBattle('fieldGob3',100)",'raider':'startRaiderBattle()'}
POINTS=['pre-start','mid-start','mode-set','generation-set','opening-notified','post-begin-ui']
SETUP="""b=>{window.__b=b;window.__wrong=0;window.__choose=b==='normal'?chooseNormalAct:choosePartyAct;
window.__open=b==='normal'?openNormalItems:openRaiderItems;window.__toggle=b==='normal'?setNormalCommandDrawer:setRaiderCommandDrawer;
window.__acts=()=>b==='normal'?normalActs.length:rbActs.length;
window.__snap=()=>JSON.stringify({actor:b==='normal'?normalActor:rbActor,acts:b==='normal'?normalActs:rbActs,hp:[aahp,normalFHP,rbHP,rbFHP],mp:[normalFMP,rbFMP],tp:[aatp,rbTP],rune:rbRune,items:battleItems,pose:BattleActorState.get(b),html:document.querySelector('#normalItems').innerHTML});}"""
INJECT="""([P,b])=>{
 let fired=false,n=0;const boom=()=>{fired=true;window.__thrown=(window.__thrown||0)+1;throw new Error('INJECT '+P)};window.__fired=()=>fired;
 const clone=(o,over)=>Object.defineProperties({},Object.assign(Object.getOwnPropertyDescriptors(o),over));
 const sn=b==='normal'?'startAttackBattle':'startRaiderBattle';const orig=window[sn];
 if(P==='pre-start'||P==='mid-start'){const byp=!window.BattleLoading||BattleLoading.bypassed===true;   /* absent/bypass: the start function runs once (no Loading re-entry) */
  window[sn]=function(...a){n++;if(!fired&&(P==='pre-start'?n===1:(byp?n===1:n===2)))boom();return orig.apply(this,a)}}
 if(P==='mode-set'){const o=window.BattleActorState;window.BattleActorState=clone(o,{begin:{value:function(...a){if(!fired)boom();return o.begin.apply(this,a)}}})}
 if(P==='generation-set'){const o=window.PrologueCombat,k=b==='normal'?'beginNormal':'beginRaider';window.PrologueCombat=clone(o,{[k]:{value:function(...a){const r=o[k].apply(this,a);if(!fired)boom();return r}}})}
 if(P==='opening-notified'){const o=window.BattleOpening;window.BattleOpening=clone(o,{play:{value:function(...a){const r=o.play.apply(this,a);if(!fired)boom();return r}}})}
 if(P==='post-begin-ui'){const un=b==='normal'?'updateAttackBattle':'updateRaider',u=window[un];window[un]=function(...a){if(!fired)boom();return u.apply(this,a)}}
}"""
OPS="""()=>{
 const b=__b,g=BattleCommandGate,e=((PrologueCombat.targets(b)||[])[0]||{}).id;
 return [
 ['COMMAND',()=>__toggle(true)],['attack',()=>__choose('atk',e)],['skill',()=>__choose('skill',e)],
 ['magic-heal',()=>__choose('heal','aidan')],['magic-prayer',()=>__choose(b==='normal'?'prayer':'rune',null)],
 ['magic-windbloom',()=>__choose('windbloom',e)],['magic-winddance',()=>__choose('winddance',null)],
 ['item-open',()=>__open()],['guard',()=>__choose('guard','aidan')],
 ['target-open',()=>BattleTargetSelector.open({type:'none',battle:b,onConfirm:()=>__wrong++})],
 ['target-confirm',()=>BattleTargetSelector.confirm(e)],
 ['direct-commit-no-receipt',()=>g.commit(null,{who:'aidan',kind:'guard',target:'aidan'})],
 ['direct-commit-forged-receipt',()=>g.commit(Object.freeze({}),{who:'aidan',kind:'guard',target:'aidan'})],
 ['synthetic-button',()=>document.querySelector(b==='normal'?'#nGuard':'#rbGuard').click()]
 ].map(([route,fn])=>{const before=__snap();let threw=false;try{fn()}catch(x){threw=true}return {route,accepted:before!==__snap()||__wrong>0}});
}"""
STATE="""()=>{const b=__b,g=BattleCommandGate;let p=null,s=null;try{p=BattleAdmissionAdapter.provider()}catch(e){}
 try{s=g.snapshot(b)}catch(e){}
 return {gen:PrologueCombat.generation,phase:p&&p.phase||null,can:!!g.canInteract(b),reason:s&&s.reason||null,thrown:window.__thrown||0,fired:window.__fired()}}"""
CLEAN="""()=>{try{PrologueCombat.cancel()}catch(e){};try{devResetScreens()}catch(e){};document.body.classList.remove('battleMode','normalBattleMode','raiderBattleMode','raiderFinishing');
 for(const s of ['#attackBattle','#raiderBattle']){const el=document.querySelector(s);if(el)el.style.display='none'};try{BattleLoading.cancel('test-cleanup')}catch(e){}}"""
rows=[];fails=[]
def run_case(br,base,b,P):
    c=br.new_context(viewport={'width':1280,'height':720})
    if MODE=='bypass':c.add_init_script('window.WINDBOUND_NO_BATTLE_LOADING=true;')
    if MODE=='absent':c.route('**/battle-loading.js*',lambda r:r.fulfill(status=200,content_type='application/javascript',body='/* absent */'))
    NEG=os.getenv('NEG','')
    if NEG:   # negative controls: serve a deliberately broken file; the matching cases must then FAIL (or, for noflag, nothing may be admitted at all)
        root=Path(__file__).resolve().parents[2]
        def serve(pattern,rel,old,new):
            src=(root/rel).read_text();assert src.count(old)==1,(NEG,old);c.route(pattern,lambda r:r.fulfill(status=200,content_type='application/javascript',body=src.replace(old,new)))
        if NEG=='ignore-flag':serve('**/battle-admission-adapter.js*','js/battle-admission-adapter.js',"const proven = d.started === true && Number.isInteger(d.combatGen) ? d.combatGen : null;","const proven = combatGen();")
        if NEG=='noflag':serve('**/battle-loading.js*','js/battle-loading.js',"started: run.started === true, combatGen: run.started === true ? run.startedCombatGen : null, startReason: run.started === true ? null : (run.startReason || 'not-started')","")
        if NEG=='no-boundary':serve('**/battle-admission-adapter.js*','js/battle-admission-adapter.js',"if (boundary && !(boundary.done && !boundary.reentered && boundary.battle === b && boundary.doneGen === g))","if (false)")
        if NEG=='loading-lies':serve('**/battle-loading.js*','js/battle-loading.js',"started: run.started === true, combatGen: run.started === true ? run.startedCombatGen : null,","started: true, combatGen: window.PrologueCombat ? PrologueCombat.generation : null,")
    pg=c.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(base+'/index.html?dev=1');pg.wait_for_function('window.BattleAdmissionAdapter&&'+('true' if MODE=='absent' else 'window.BattleLoading')+'&&BattleMotion.loaded&&window.BattleUIState');pg.wait_for_timeout(1200)
    pg.evaluate('closeDialogue()');pg.evaluate(SETUP,b);pg.evaluate(INJECT,[P,b])
    pg.evaluate("s=>{try{eval(s)}catch(e){window.__startErr=String(e)}}",START[b]);pg.wait_for_timeout(3200)
    st=pg.evaluate(STATE)
    rc=pg.evaluate("()=>{try{return BattleCommandGate.issue(__b)?1:0}catch(e){return 0}}") if False else None
    # old receipt: issue only if the Gate would give one right now; keep it for the next-battle check
    pg.evaluate("()=>{try{window.__rc=BattleCommandGate.issue(__b)||null}catch(e){window.__rc=null}}");has_rc=pg.evaluate('!!window.__rc')
    a0=pg.evaluate('__acts()')
    ops=pg.evaluate(OPS);acc=[r['route'] for r in ops if r['accepted']]
    pg.evaluate("()=>{if(window.__rc)try{__choose('guard','aidan',window.__rc)}catch(e){}}");a1=pg.evaluate('__acts()')
    # next, genuine battle
    pg.evaluate(CLEAN);pg.wait_for_timeout(400)
    pg.evaluate("s=>{try{eval(s)}catch(e){window.__startErr2=String(e)}}",START[b])
    ok_next=False
    for _ in range(300):
        if pg.evaluate("BattleCommandGate.canInteract(__b)"):ok_next=True;break
        pg.wait_for_timeout(40)
    pg.wait_for_timeout(300)
    old=None
    if has_rc and ok_next:
        n0=pg.evaluate('__acts()');pg.evaluate("()=>{try{BattleCommandGate.commit(window.__rc,{who:'aidan',kind:'guard',target:'aidan'})}catch(e){}}");old=pg.evaluate('__acts()')-n0
    eff=None
    if ok_next:
        s0=pg.evaluate('JSON.parse(__snap())');pg.evaluate("__choose('guard','aidan')");pg.wait_for_timeout(300);s1=pg.evaluate('JSON.parse(__snap())')
        eff=(s0['actor']=='aidan' and s1['actor']=='fiona') and (b=='normal' or len(s1['acts'])==len(s0['acts'])+1)
    r={'mode':MODE,'battle':b,'point':P,'fired':st['fired'],'gen':st['gen'],'phase':st['phase'],'gate_allowed':st['can'],'reason':st['reason'],'receipt_issued':has_rc,
       'accepted_routes':acc,'guard_queue_delta':a1-a0,'commits':len(acc)+(a1-a0),'next_playable':ok_next,'next_guard_effect':eff,'old_receipt_commit_delta':old}
    rows.append(r);c.close();return r
with server(PORT) as base,sync_playwright() as pw:
    br=pw.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE') or None)
    for b in ['normal','raider']:
        for P in POINTS:
            r=run_case(br,base,b,P)
            good=r['fired'] and r['commits']==0 and not r['gate_allowed'] and r['next_playable'] and r['next_guard_effect'] and (r['old_receipt_commit_delta'] in (None,0))
            print(('ok   ' if good else 'FAIL ')+'%s/%s'%(b,P),json.dumps(r,ensure_ascii=False),flush=True)
            if not good:fails.append('%s/%s'%(b,P))
    br.close()
if OUT:Path(OUT).write_text(json.dumps(rows,ensure_ascii=False,indent=1))
print('FAILS',len(fails),fails);sys.exit(1 if fails else 0)

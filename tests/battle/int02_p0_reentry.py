"""INT-02-P0-D: synchronous re-entry fault injection (3 paths x normal/raider = 6 cases), after Codex INT-02-P0-X P0_REENTRY_FINDING.
The real start function is re-entered from inside BattleActorState.begin (inner start completes, generation +1), then the OUTER start continues (generation +1 again) and throws in its
post-begin UI update before reaching its completion statement. Nothing may be admitted for the current generation: guard must not commit, the Gate must refuse, and a fresh genuine
battle must then be playable.  MODE: enabled | bypass (WINDBOUND_NO_BATTLE_LOADING=true) | absent (battle-loading.js not served).  NEG=<name> serves a deliberately broken adapter (must FAIL)."""
import os,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
PORT=int(os.getenv('P0PORT','8845'));OUT=os.getenv('P0OUT','');NEG=os.getenv('NEG','');ROOT=Path(__file__).resolve().parents[2]
MODES=[m for m in os.getenv('MODES','enabled,bypass,absent').split(',') if m]
START={'normal':"startAttackBattle('fieldGob3',100)",'raider':'startRaiderBattle()'}
INJECT="""([b,call])=>{
 window.__audit={reentered:false,threw:false,depth:0,innerGen:null};
 const o=BattleActorState,d=Object.getOwnPropertyDescriptors(o),begin=o.begin;
 d.begin={value:function(...a){if(!__audit.reentered){__audit.reentered=true;__audit.depth++;try{eval(call)}finally{__audit.depth--}__audit.innerGen=PrologueCombat.generation}return begin.apply(this,a)},enumerable:true};
 window.BattleActorState=Object.defineProperties({},d);
 const n=b==='normal'?'updateAttackBattle':'updateRaider',u=window[n];
 window[n]=function(...a){if(__audit.reentered&&__audit.depth===0&&!__audit.threw){__audit.threw=true;throw Error('OUTER_POST_BEGIN_AFTER_REENTRY')}return u.apply(this,a)};
 window.__b=b;window.__choose=b==='normal'?chooseNormalAct:choosePartyAct;window.__acts=()=>b==='normal'?normalActs.length:rbActs.length;
}"""
PROBE="""()=>{const b=__b,g=BattleCommandGate;let p=null,s=null;try{p=BattleAdmissionAdapter.provider()}catch(e){}try{s=g.snapshot(b)}catch(e){}
 const n0=__acts();let rc=null;try{rc=g.issue(b)||null}catch(e){}window.__rc=rc;
 try{__choose('guard','aidan',rc||undefined)}catch(e){}try{__choose('guard','aidan')}catch(e){}
 try{g.commit(null,{who:'aidan',kind:'guard',target:'aidan'})}catch(e){}
 return {audit:__audit,gen:PrologueCombat.generation,phase:p&&p.phase||null,allowed:!!(s&&s.allowed),receipt:!!rc,queueDelta:__acts()-n0}}"""
CLEAN="""()=>{try{PrologueCombat.cancel()}catch(e){};try{devResetScreens()}catch(e){};document.body.classList.remove('battleMode','normalBattleMode','raiderBattleMode','raiderFinishing');
 for(const s of ['#attackBattle','#raiderBattle']){const el=document.querySelector(s);if(el)el.style.display='none'};try{BattleLoading.cancel('test-cleanup')}catch(e){}}"""
rows=[];fails=[]
def run_case(br,base,mode,b):
    c=br.new_context(viewport={'width':1280,'height':720})
    if mode=='bypass':c.add_init_script('window.WINDBOUND_NO_BATTLE_LOADING=true;')
    if mode=='absent':c.route('**/battle-loading.js*',lambda r:r.fulfill(status=200,content_type='application/javascript',body='/* absent */'))
    if NEG:
        def serve(old,new):
            src=(ROOT/'js/battle-admission-adapter.js').read_text();assert src.count(old)==1,(NEG,old)
            c.route('**/battle-admission-adapter.js*',lambda r:r.fulfill(status=200,content_type='application/javascript',body=src.replace(old,new)))
        if NEG=='replace-owner':serve("if (owner && !owner.done && !owner.settled) { owner.reentered = true; return () => { }; }","")           # re-entry replaces the owner again
        if NEG=='done-only':serve("if (boundary && !(boundary.done && !boundary.reentered && boundary.battle === b && boundary.doneGen === g))","if (boundary && !boundary.done)")
        if NEG=='both':   # both layers disabled = the P0-C behaviour (inner boundary replaces the owner, bare done flag is trusted)
            src=(ROOT/'js/battle-admission-adapter.js').read_text()
            for o,n in [("if (owner && !owner.done && !owner.settled) { owner.reentered = true; return () => { }; }",""),("if (boundary && !(boundary.done && !boundary.reentered && boundary.battle === b && boundary.doneGen === g))","if (boundary && !boundary.done)")]:
                assert src.count(o)==1,(NEG,o);src=src.replace(o,n)
            c.route('**/battle-admission-adapter.js*',lambda r:r.fulfill(status=200,content_type='application/javascript',body=src))
    pg=c.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(base+'/index.html?dev=1');pg.wait_for_function('window.BattleAdmissionAdapter&&BattleMotion.loaded&&window.BattleUIState');pg.wait_for_timeout(1200)
    pg.evaluate('closeDialogue()');pg.evaluate(INJECT,[b,START[b]])
    try:pg.evaluate("s=>{eval(s)}",START[b])
    except Exception as e:errs.append(str(e)[:120])
    pg.wait_for_timeout(3500)
    r=pg.evaluate(PROBE)
    pg.evaluate(CLEAN);pg.wait_for_timeout(400)
    pg.evaluate("s=>{try{eval(s)}catch(e){}}",START[b]);ok_next=False
    for _ in range(300):
        if pg.evaluate("BattleCommandGate.canInteract(__b)"):ok_next=True;break
        pg.wait_for_timeout(40)
    pg.wait_for_timeout(300);old=None
    if r['receipt'] and ok_next:
        n0=pg.evaluate('__acts()');pg.evaluate("()=>{try{BattleCommandGate.commit(window.__rc,{who:'aidan',kind:'guard',target:'aidan'})}catch(e){}}");old=pg.evaluate('__acts()')-n0
    row={'mode':mode,'battle':b,'reentered':r['audit']['reentered'],'outerThrew':r['audit']['threw'],'innerGen':r['audit']['innerGen'],'gen':r['gen'],'phase':r['phase'],
         'gate_allowed':r['allowed'],'receipt_issued':r['receipt'],'queue_delta':r['queueDelta'],'next_playable':ok_next,'old_receipt_commit_delta':old}
    rows.append(row);c.close();return row
with server(PORT) as base,sync_playwright() as pw:
    br=pw.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE') or None)
    for mode in MODES:
        for b in ['normal','raider']:
            r=run_case(br,base,mode,b)
            injected=r['reentered'] and r['outerThrew'] and r['gen']==(r['innerGen'] or 0)+1
            good=injected and r['queue_delta']==0 and not r['gate_allowed'] and r['phase']!='input' and not r['receipt_issued'] and r['next_playable'] and (r['old_receipt_commit_delta'] in (None,0))
            print(('ok   ' if good else 'FAIL ')+'%s/%s'%(mode,b),json.dumps(r,ensure_ascii=False),flush=True)
            if not good:fails.append('%s/%s'%(mode,b))
    br.close()
if OUT:Path(OUT).write_text(json.dumps(rows,ensure_ascii=False,indent=1))
print('FAILS',len(fails),fails);sys.exit(1 if fails else 0)

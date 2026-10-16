"""Browser mutation controls. Alter only the response for the new gate module, never files/Claude code.
A control is detected by an independently observable invalid queue change, not by querying the gate's answer.
"""
import os,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
OUT=Path(os.getenv('OUT','/tmp/ui-command-negative'));OUT.mkdir(parents=True,exist_ok=True);results=[];fails=[]
source=(ROOT/'js/battle-command-gate.js').read_text()
mutations={'all-admitted':('allowed:!reason','allowed:true'),'stale-receipt':('r.key===read(b).key','true'),'reentrant-receipt':('!!r&&!r.used&&','!!r&&')}
with server(8832) as base,sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE') or '/usr/bin/chromium')
 for b in ['normal','raider']:
  for case,(needle,replacement) in mutations.items():
   for mutant in [False,True]:
    assert source.count(needle)==1
    c=browser.new_context();pg=c.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)))
    if mutant:
     body=source.replace(needle,replacement)
     pg.route('**/js/battle-command-gate.js',lambda route:route.fulfill(status=200,content_type='application/javascript',body=body))
    pg.goto(base+'/index.html?dev=1');pg.wait_for_function('window.BattleUIState&&BattleMotion.loaded');pg.wait_for_timeout(1200)
    pg.evaluate("closeDialogue();"+("startAttackBattle('fieldGob3',100)" if b=='normal' else 'startRaiderBattle()'));pg.wait_for_function('!BattlePresentation.busy')
    pg.evaluate("b=>{window.__b=b;window.__admission={requestId:'control',battle:b,generation:PrologueCombat.generation,phase:'input',opening:'completed'};BattleCommandGate.installAdmissionProvider(()=>__admission)}",b)
    if case=='all-admitted':
     observed=pg.evaluate("()=>{__admission.phase='loading';BattleCommandGate.refresh();const n=(__b==='normal'?normalActs:rbActs).length;(__b==='normal'?chooseNormalAct:choosePartyAct)('guard','aidan');return ( __b==='normal'?normalActs:rbActs).length-n}")
    elif case=='stale-receipt':
     observed=pg.evaluate("()=>{const r=BattleCommandGate.issue(__b);__admission.phase='opening';BattleCommandGate.refresh();__admission.phase='input';BattleCommandGate.refresh();const n=(__b==='normal'?normalActs:rbActs).length;BattleCommandGate.commit(r,{who:'aidan',kind:'guard',target:'aidan'});return (__b==='normal'?normalActs:rbActs).length-n}")
    else:
     observed=pg.evaluate("()=>{const r=BattleCommandGate.issue(__b),a={who:'aidan',kind:'guard',target:'aidan'},old=BattleActorState;let once=false;window.BattleActorState={...old,set(...args){if(args[1]==='guard'&&!once){once=true;BattleCommandGate.commit(r,a)}return old.set(...args)}};const n=(__b==='normal'?normalActs:rbActs).length;BattleCommandGate.commit(r,a);return (__b==='normal'?normalActs:rbActs).length-n}")
    expected=1 if case=='reentrant-receipt' else 0
    safe=observed==expected;ok=safe if not mutant else not safe
    row={'battle':b,'case':case,'mutant':mutant,'queue_delta':observed,'safe_expected':expected,'pass':ok,'browser_errors':errors};results.append(row);print(('ok ' if ok else 'FAIL ')+str(row),flush=True)
    if not ok or errors:fails.append(row)
    c.close()
 browser.close()
(OUT/'results.json').write_text(json.dumps({'results':results,'fails':fails,'scope':'UI-only module response mutation; invalid behavior intentionally detected'},indent=2)+'\n');print('FAILS',len(fails));sys.exit(bool(fails))

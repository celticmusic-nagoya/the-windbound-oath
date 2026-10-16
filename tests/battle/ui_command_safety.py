"""INT-01D-X: real UI03 commands with an explicitly TEST-ONLY start-admission provider.
No Claude loading/opening implementation is imported. Failure injection is recorded separately.
"""
import os,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
OUT=Path(os.getenv('OUT','/tmp/ui-command-safety'));OUT.mkdir(parents=True,exist_ok=True)
fails=[];checks=[]
def check(ok,name,detail=None):
 print(('ok ' if ok else 'FAIL ')+name,detail or '',flush=True);checks.append({'name':name,'ok':bool(ok),'detail':detail})
 if not ok:fails.append(name)
START={'normal':"startAttackBattle('fieldGob3',100)",'raider':'startRaiderBattle()'}
CAPTURE="""b=>{window.__b=b;window.__wrong=0;window.__choose=b==='normal'?chooseNormalAct:choosePartyAct;
window.__open=b==='normal'?openNormalItems:openRaiderItems;window.__toggle=b==='normal'?setNormalCommandDrawer:setRaiderCommandDrawer;
window.__snap=()=>JSON.stringify({actor:b==='normal'?normalActor:rbActor,acts:b==='normal'?normalActs:rbActs,hp:[aahp,normalFHP,rbHP,rbFHP],mp:[normalFMP,rbFMP],tp:[aatp,rbTP],rune:rbRune,items:battleItems,pose:BattleActorState.get(b),html:document.querySelector('#normalItems').innerHTML});
window.__admission={requestId:'fixture:'+b,battle:b,generation:PrologueCombat.generation,phase:'input',opening:'completed'};
BattleCommandGate.installAdmissionProvider(()=>__admission);
window.BattleLoading={get frozen(){return __admission.phase==='loading'}};
BattleCommandGate.refresh();BattleUIState.sync(b);
}"""
HOLD="""()=>{const old=BattleTargetSelector;window.BattleTargetSelector={...old,get active(){return old.active},get selected(){return old.selected},open(o){if(o.label==='アイテムの対象を選択')window.__late=o.onConfirm;return old.open(o)}};__open();BattleActionTargets.item(__b,'potion');window.__receipt=BattleCommandGate.issue(__b);}"""
OPS="""()=>{
 const b=__b,g=BattleCommandGate,e=PrologueCombat.targets(b)[0].id;
 return [
 ['COMMAND',()=>__toggle(true)],['attack',()=>__choose('atk',e)],['skill',()=>__choose('skill',e)],
 ['magic-heal',()=>__choose('heal','aidan')],['magic-prayer',()=>__choose(b==='normal'?'prayer':'rune',null)],
 ['magic-windbloom',()=>__choose('windbloom',e)],['magic-winddance',()=>__choose('winddance',null)],
 ['item-open',()=>__open()],['guard',()=>__choose('guard','aidan')],
 ['target-open',()=>BattleTargetSelector.open({type:'none',battle:b,onConfirm:()=>__wrong++})],
 ['target-confirm',()=>BattleTargetSelector.confirm(e)],['late-item-callback',()=>__late('aidan')],
 ['direct-commit',()=>g.commit(__receipt,{who:'aidan',kind:'guard',target:'aidan'})],
 ['synthetic-button',()=>document.querySelector(b==='normal'?'#nGuard':'#rbGuard').click()]
 ].map(([route,fn])=>{const before=__snap();fn();return {route,unchanged:before===__snap()&&__wrong===0,view:BattleUIState.snapshot(b).status}});
}"""
with server(8831) as base,sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE') or '/usr/bin/chromium')
 for view,w,h in [('pc',1280,720),('portrait',390,844),('landscape',844,390)]:
  for b in ['normal','raider']:
   c=browser.new_context(viewport={'width':w,'height':h},has_touch=view!='pc',is_mobile=view!='pc');pg=c.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)))
   pg.goto(base+'/index.html?dev=1');pg.wait_for_function('window.BattleUIState&&BattleMotion.loaded');pg.wait_for_timeout(1200)
   r=pg.evaluate("()=>{closeDialogue();"+START[b]+";const n="+('normalActs' if b=='normal' else 'rbActs')+".length;"+('chooseNormalAct' if b=='normal' else 'choosePartyAct')+"('guard','aidan');return {unchanged:"+('normalActs' if b=='normal' else 'rbActs')+".length===n,busy:BattlePresentation.busy}}")
   check(r['busy'] and r['unchanged'],view+'/'+b+' native Opening blocks direct command',r)
   pg.wait_for_function("BattleUIState.snapshot('"+b+"').status==='collapsed'")
   pg.evaluate(CAPTURE,b);name=view+'/'+b
   # The provider is a fixture, NOT a claimed BattlePresentation API.
   for phase in ['loading','prepared','opening-pending','opening','failed','cancelled']:
    pg.evaluate("()=>{__admission.phase='input';__admission.generation=PrologueCombat.generation;BattleCommandGate.refresh();BattleUIState.sync(__b)}")
    pg.evaluate(HOLD)
    pg.evaluate("phase=>{__wrong=0;__admission.phase=phase;BattleCommandGate.refresh();BattleUIState.sync(__b)}",phase)
    rows=pg.evaluate(OPS)
    for row in rows:check(row['unchanged'] and row['view']=='busy',name+'/'+phase+'/'+row['route'],row)
    r=pg.evaluate("()=>{const stock=battleItems.potion;const msg=document.querySelector(__b==='normal'?'#battleMsg2':'#rbMsg'),before=msg.textContent;battleItems.potion=0;document.querySelector(__b==='normal'?'[data-ni=\"potion\"]':'[data-ri=\"potion\"]').click();const same=msg.textContent===before;battleItems.potion=stock;return same}")
    check(r,name+'/'+phase+' stale empty-item click cannot display a message')
    before=pg.evaluate('__snap()');pg.keyboard.press('Enter');pg.keyboard.press('Space');pg.keyboard.press('Escape');pg.mouse.click(w/4,h-30)
    if view!='pc':pg.touchscreen.tap(w/4,h-30)
    check(pg.evaluate('__snap()')==before,name+'/'+phase+' real keyboard/pointer/touch refused')
    pg.set_viewport_size({'width':h,'height':w});pg.wait_for_timeout(50);check(pg.evaluate("BattleUIState.snapshot(__b).status==='busy'"),name+'/'+phase+' rotation retains lock');pg.set_viewport_size({'width':w,'height':h})
   pg.evaluate("()=>{__admission.phase='input';BattleCommandGate.refresh();BattleUIState.sync(__b)}")
   check(pg.evaluate("BattleUIState.snapshot(__b).status==='collapsed'"),name+' release restores COMMAND only')
   # Invalid terminal context, terminal result and provider errors fail closed.
   for field,value in [('generation',-1),('battle','wrong'),('opening','unknown')]:
    pg.evaluate("([field,value])=>{window.__save=__admission[field];__admission[field]=value;BattleCommandGate.refresh()}",[field,value]);before=pg.evaluate('__snap()');pg.evaluate("__choose('guard','aidan')");check(pg.evaluate('__snap()')==before,name+' rejects mismatched '+field);pg.evaluate("field=>{__admission[field]=__save;BattleCommandGate.refresh()}",field)
   # Events are observations, never authorization/start/reset. Duplicates must not collapse a manual view.
   pg.evaluate('__toggle(true)');pg.evaluate("()=>{for(let i=0;i<2;i++)dispatchEvent(new CustomEvent('battle-loading',{detail:{phase:'ready',gen:-1,key:'old'}}))}")
   check(pg.evaluate("BattleUIState.snapshot(__b).status==='commands'"),name+' duplicate stale ready cannot reset/restart UI')
   gen=pg.evaluate('PrologueCombat.generation');before=pg.evaluate('document.querySelectorAll(".battleUIOperations").length');objects=pg.evaluate("window.__owners=[BattleCommandGate,BattleUIState,BattleUIRegions,BattleUIResponsive,InputManager];true")
   for file in ['battle-command-gate','battle-ui-state','battle-ui-regions','battle-ui-responsive','input-manager']:pg.add_script_tag(content=(ROOT/'js'/(file+'.js')).read_text())
   check(pg.evaluate('[BattleCommandGate,BattleUIState,BattleUIRegions,BattleUIResponsive,InputManager].every((x,i)=>x===__owners[i])') and pg.evaluate('PrologueCombat.generation')==gen and pg.evaluate('document.querySelectorAll(".battleUIOperations").length')==before,name+' duplicate bootstrap retains owners and DOM')
   # Stale receipt after an ABA phase change is rejected, even after input resumes.
   pg.evaluate("()=>{window.__old=BattleCommandGate.issue(__b);__admission.phase='opening';BattleCommandGate.refresh();__admission.phase='input';BattleCommandGate.refresh();BattleUIState.sync(__b)}")
   before=pg.evaluate('__snap()');pg.evaluate("BattleCommandGate.commit(__old,{who:'aidan',kind:'guard',target:'aidan'})");check(pg.evaluate('__snap()')==before,name+' old receipt cannot survive blocked-to-input ABA')
   # Authorized fallback skip is explicit; an unapproved skip never unlocks.
   pg.evaluate("()=>{__admission.opening='skipped';BattleCommandGate.refresh()}");check(pg.evaluate('!BattleCommandGate.canInteract(__b)'),name+' unapproved skip locked')
   pg.evaluate("()=>{__admission.skipAllowed=true;__admission.skipReason='fixture still-art fallback';BattleCommandGate.refresh();BattleUIState.sync(__b)}");check(pg.evaluate('BattleCommandGate.canInteract(__b)'),name+' explicit fallback can unlock')
   pg.evaluate("()=>{__admission.opening='completed';BattleCommandGate.refresh();BattleUIState.sync(__b);__toggle(true)}")
   if view=='pc':pg.locator('#nItem' if b=='normal' else '#rbItem').click()
   else:pg.locator('#nItem' if b=='normal' else '#rbItem').tap()
   check(pg.evaluate("BattleUIState.snapshot(__b).status==='items'"),name+' real item control accepted after release')
   pg.locator('[data-ni="close"]' if b=='normal' else '[data-ri="close"]').click();pg.evaluate('window.__once=BattleCommandGate.issue(__b)')
   r=pg.evaluate("()=>{const n=(__b==='normal'?normalActs:rbActs).length;const first=BattleCommandGate.commit(__once,{who:'aidan',kind:'guard',target:'aidan'});const second=BattleCommandGate.commit(__once,{who:'aidan',kind:'guard',target:'aidan'});return {first,second,delta:(__b==='normal'?normalActs:rbActs).length-n}}")
   check(r=={'first':True,'second':False,'delta':1},name+' common commit accepts once only',r)
   pg.evaluate("()=>{__admission.phase='cancelled';document.body.classList.remove('battleMode','normalBattleMode','raiderBattleMode');BattleCommandGate.refresh();BattleUIState.sync()}")
   check(pg.evaluate("!InputManager.state().startsWith('BATTLE')&&BattleUIState.snapshot(__b).status==='inactive'"),name+' cancel scene exit leaves no input lock')
   check(not errors,name+' no browser errors',errors)
   pg.screenshot(path=str(OUT/(view+'-'+b+'-after.png')));c.close()
 browser.close()
(OUT/'results.json').write_text(json.dumps({'checks':checks,'fails':fails,'scope':'UI03-only real browser; Claude start contract is TEST STUB'},ensure_ascii=False,indent=2)+'\n');print('FAILS',len(fails));sys.exit(bool(fails))

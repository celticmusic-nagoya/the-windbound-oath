"""Accepted native command paths and delayed receipt tests; no Claude code loaded."""
import os,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
OUT=Path(os.getenv('OUT','/tmp/ui-command-positive'));OUT.mkdir(parents=True,exist_ok=True);rows=[];fails=[]
def check(ok,name,detail):
 print(('ok ' if ok else 'FAIL ')+name,str(detail),flush=True);rows.append({'name':name,'ok':bool(ok),'detail':detail})
 if not ok:fails.append(name)
with server(8833) as base,sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE') or '/usr/bin/chromium')
 for b in ['normal','raider']:
  for case in ['atk','skill','heal','windbloom','winddance','prayer','guard','item','stale-generation','target-generation','cancelled-target','unbound-provider','missing-bridge','provider-error']:
   c=browser.new_context();pg=c.new_page();pg.goto(base+'/index.html?dev=1');pg.wait_for_function('window.BattleUIState&&BattleMotion.loaded');pg.wait_for_timeout(1200)
   pg.evaluate("closeDialogue();"+("startAttackBattle('fieldGob3',100)" if b=='normal' else 'startRaiderBattle()'));pg.wait_for_function("!BattlePresentation.busy&&BattleUIState.snapshot('"+b+"').status==='collapsed'")
   pg.evaluate('window.__fixtureCase='+json.dumps(case))
   pg.evaluate("b=>{window.__b=b;window.__choose=b==='normal'?chooseNormalAct:choosePartyAct;window.__admission={requestId:'positive',battle:b,generation:PrologueCombat.generation,phase:'input',opening:'completed'};if(__fixtureCase!=='missing-bridge')BattleCommandGate.installAdmissionProvider(()=>__admission);BattleCommandGate.refresh();BattleUIState.sync(b)}",b)
   if case in ['heal','windbloom','winddance','prayer']:
    pg.evaluate("__choose('guard','aidan')")
    if case=='winddance':pg.evaluate("window.WindDance={commandVisible:()=>true,mp:()=>10}")
   if case=='skill':pg.evaluate('aatp=40;rbTP=40')
   r=pg.evaluate("""caseName=>{
 const b=__b,q=()=>b==='normal'?normalActs:rbActs,n=q().length,beforeStock=battleItems.potion,actor=b==='normal'?normalActor:rbActor;
 let expected=1,accepted=null;
 if(caseName==='item'){
  const old=BattleTargetSelector;window.__late=null;window.BattleTargetSelector={...old,get active(){return old.active},get selected(){return old.selected},open(o){__late=o.onConfirm;return old.open(o)}};
  BattleActionTargets.item(b,'potion');BattleTargetSelector.confirm('aidan');__late('aidan');
 }else if(caseName==='stale-generation'){
  expected=0;const receipt=BattleCommandGate.issue(b);PrologueCombat.cancel();__admission.generation=PrologueCombat.generation;BattleCommandGate.refresh();accepted=BattleCommandGate.commit(receipt,{who:actor,kind:'guard',target:actor});
 }else if(caseName==='target-generation'){
  expected=0;const old=BattleTargetSelector;window.BattleTargetSelector={...old,get active(){return old.active},get selected(){return old.selected},open(o){window.__late=o.onConfirm;return old.open(o)}};
  BattleActionTargets.item(b,'potion');PrologueCombat.cancel();__admission.generation=PrologueCombat.generation;BattleCommandGate.refresh();BattleUIState.sync(b);__late('aidan');
 }else if(caseName==='cancelled-target'){
  expected=0;const old=BattleTargetSelector;window.BattleTargetSelector={...old,get active(){return old.active},get selected(){return old.selected},open(o){window.__late=o.onConfirm;return old.open(o)}};
  BattleActionTargets.item(b,'potion');BattleTargetSelector.cancel();__late('aidan');
 }else if(caseName==='missing-bridge'){
  expected=0;window.BattleLoading={frozen:false};__choose('guard','aidan');
 }else if(caseName==='unbound-provider'){
  expected=0;window.BattleLoading={frozen:false};BattleCommandGate.installAdmissionProvider(()=>null);__choose('guard','aidan');
 }else if(caseName==='provider-error'){
  expected=0;BattleCommandGate.installAdmissionProvider(()=>{throw new Error('fixture provider unavailable')});__choose('guard','aidan');
 }else{
  const kind=caseName==='prayer'?(b==='normal'?'prayer':'rune'):caseName;
  const target=['heal','guard'].includes(kind)?actor:['prayer','rune','winddance'].includes(kind)?null:PrologueCombat.targets(b)[0].id;
  __choose(kind,target);
 }
 return {delta:q().length-n,expected,accepted,actions:q().slice(n),stock:battleItems.potion,beforeStock};
 }""",case)
   check(r['delta']==r['expected'],b+'/'+case+' native queue change',r)
   if case=='item':check(r['stock']==r['beforeStock'],b+' item is queued once, not consumed by UI',r)
   c.close()
 browser.close()
(OUT/'results.json').write_text(json.dumps({'rows':rows,'fails':fails},ensure_ascii=False,indent=2)+'\n');print('FAILS',len(fails));sys.exit(bool(fails))

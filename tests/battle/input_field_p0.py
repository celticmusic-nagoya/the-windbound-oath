"""INT-01F-X: unmodified D-X command engine + InputManager P0 fix.
Loading/provider API fixtures only: Claude patches are NOT imported.
P0_INPUT_BEFORE replaces only the served InputManager response for negative control.
"""
import os,sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
OUT=Path(os.getenv('OUT','/tmp/input-field-p0'));OUT.mkdir(parents=True,exist_ok=True)
rows=[];errors=[]
def check(ok,name,detail=None):
 rows.append(dict(name=name,ok=bool(ok),detail=detail));print(('ok ' if ok else 'FAIL ')+name,str(detail or ''),flush=True)
FIELD="""()=>{devResetScreens();closeDialogue();document.body.classList.remove('battleMode','normalBattleMode','raiderBattleMode','battleResultMode');document.querySelector('#battleResult').style.display='none';room='home';ipx=190;ipy=500;itarget=null;forestActive=false;document.querySelector('#inside').style.display='block';document.querySelector('#msg').style.display='none';dressRoom();inCamera();document.activeElement?.blur()}"""
with server(8841) as base,sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE') or '/usr/bin/chromium')
 def page():
  pg=browser.new_page();pg.on('pageerror',lambda e:errors.append(str(e)))
  if os.getenv('P0_INPUT_BEFORE'):pg.route('**/js/input-manager.js*',lambda r:r.fulfill(status=200,content_type='text/javascript',body=Path(os.environ['P0_INPUT_BEFORE']).read_text()))
  pg.goto(base+'/index.html?dev=1');pg.wait_for_function('window.InputManager&&window.BattleUIState&&BattleMotion.loaded');pg.evaluate(FIELD);return pg
 for case in ['baseline','enabled-unbound','bypass-unbound','provider-null','stale-provider','frozen']:
  pg=page();pg.evaluate("""c=>{if(c!=='baseline')window.BattleLoading={active:c==='frozen',frozen:c==='frozen',bypassed:c==='bypass-unbound'};if(c==='provider-null')BattleCommandGate.installAdmissionProvider(()=>null);if(c==='stale-provider')BattleCommandGate.installAdmissionProvider(()=>({requestId:'old',battle:'normal',generation:-1,phase:'opening',opening:'pending'}))}""",case)
  start=pg.evaluate('ipx');pg.keyboard.down('ArrowRight');pg.wait_for_timeout(180);r=pg.evaluate('({state:InputManager.state(),x:ipx,vector:InputManager.heldVector(),allowed:BattleCommandGate.snapshot().allowed})');pg.keyboard.up('ArrowRight')
  blocked=case=='frozen';check(r['state']==('BATTLE_ANIMATION' if blocked else 'FIELD'),case+' classification',r);check((r['x']==start) if blocked else r['x']>start,case+' indoor movement',{'before':start,**r});check(not r['allowed'],case+' no field battle commands')
  # Outdoor path is the actual index.html key handler, not a movement stub.
  pg.evaluate("room='';document.querySelector('#inside').style.display='none';px=1000;py=1010;target=null;camera();")
  before=pg.evaluate('[px,py]');pg.keyboard.press('ArrowRight');after=pg.evaluate('[px,py]');check(after==before if blocked else after!=before,case+' outdoor arrow',{'before':before,'after':after})
  pg.close()
 # Real result rendering + real continue callback, both Loading-module states.
 for bypass in [False,True]:
  pg=page();pg.evaluate("b=>{window.BattleLoading={frozen:false,active:false,bypassed:b};window.__continued=0;showBattleResult(0,0,()=>{__continued++;document.body.classList.remove('battleMode','normalBattleMode','battleResultMode')});document.body.classList.add('battleMode','normalBattleMode','battleResultMode')}",bypass)
  label='result/'+('bypass' if bypass else 'enabled');check(pg.evaluate('InputManager.state()')=='RESULT',label+' recognized ahead of unbound')
  before=pg.evaluate('[ipx,ipy,px,py]');pg.keyboard.down('ArrowRight');pg.keyboard.down('d');pg.wait_for_timeout(80);check(pg.evaluate('[ipx,ipy,px,py]')==before,label+' arrow and WASD cannot move');check(not pg.evaluate("BattleCommandGate.canInteract('normal')"),label+' battle commands rejected')
  pg.keyboard.down('Enter');pg.wait_for_timeout(80);check(pg.evaluate('__continued')==1,label+' real Enter confirms once');check(pg.evaluate('InputManager.state()')=='FIELD',label+' returns to field');pg.keyboard.down('ArrowRight');pg.keyboard.down('d');pg.keyboard.down('Enter');pg.wait_for_timeout(100);check(pg.evaluate('[ipx,ipy,px,py]')==before,label+' held/repeat keys quarantined');check(pg.evaluate('__continued')==1,label+' repeated confirm not replayed')
  pg.keyboard.up('ArrowRight');pg.keyboard.up('d');pg.keyboard.up('Enter');start=pg.evaluate('ipx');pg.keyboard.down('ArrowRight');pg.wait_for_timeout(100);pg.keyboard.up('ArrowRight');check(pg.evaluate('ipx')>start,label+' movement resumes on fresh press')
  # Mouse continue with an arrow held has the same release boundary.
  pg.evaluate("showBattleResult(0,0,()=>{__continued++});document.body.classList.add('battleResultMode')")
  pg.keyboard.down('ArrowLeft');before=pg.evaluate('ipx');pg.locator('#resultContinue').click();pg.wait_for_timeout(100);check(pg.evaluate('__continued')==2 and pg.evaluate('ipx')==before,label+' pointer result and held arrow');pg.keyboard.up('ArrowLeft')
  pg.keyboard.down('ArrowRight');pg.wait_for_timeout(40)
  pg.evaluate("showBattleResult(0,0,()=>{__continued++})");before=pg.evaluate('ipx');pg.locator('#resultContinue').click();pg.wait_for_timeout(100);check(pg.evaluate('ipx')==before,label+' pre-existing field hold cleared by result');pg.keyboard.up('ArrowRight')
  pg.evaluate("showBattleResult(0,0,()=>{__continued++})");n=pg.evaluate('__continued');pg.keyboard.down('Space');pg.wait_for_timeout(70);pg.keyboard.down('Space');pg.keyboard.up('Space');check(pg.evaluate('__continued')==n+1,label+' Space confirms once without keyup replay');pg.close()
 for battle in ['normal','raider']:
  pg=page();start="startAttackBattle('fieldGob3',100)" if battle=='normal' else 'startRaiderBattle()'
  pg.evaluate('closeDialogue();'+start);check(pg.evaluate('BattlePresentation.busy'),battle+' actual nonLoading Opening started');n=pg.evaluate('normalActs.length' if battle=='normal' else 'rbActs.length');choose='chooseNormalAct' if battle=='normal' else 'choosePartyAct';pg.evaluate(choose+"('guard','aidan')");check(pg.evaluate('normalActs.length' if battle=='normal' else 'rbActs.length')==n,battle+' native Opening rejects direct command');pg.wait_for_function('!BattlePresentation.busy')
  pg.evaluate("""b=>{window.__b=b;window.__ad={requestId:'p0:'+b,battle:b,generation:PrologueCombat.generation,phase:'input',opening:'completed'};BattleCommandGate.installAdmissionProvider(()=>__ad);window.BattleLoading={get frozen(){return __ad.phase==='loading'},get bypassed(){return false}};BattleCommandGate.refresh()}""",battle)
  for phase in ['loading','opening','input']:
   pg.evaluate('p=>{__ad.phase=p;BattleCommandGate.refresh()}',phase)
   if phase!='input':
    before=pg.evaluate('JSON.stringify({n:normalActs,r:rbActs,a:normalActor,b:rbActor,items:battleItems})');pg.evaluate(choose+"('guard','aidan')");check(pg.evaluate('JSON.stringify({n:normalActs,r:rbActs,a:normalActor,b:rbActor,items:battleItems})')==before,battle+'/'+phase+' direct command refused');check(pg.evaluate('InputManager.state()')=='BATTLE_ANIMATION',battle+'/'+phase+' keyboard locked')
  pg.evaluate('attackBattleBusy=true' if battle=='normal' else 'rbBusy=true');before=pg.evaluate('normalActs.length' if battle=='normal' else 'rbActs.length');pg.evaluate(choose+"('guard','aidan')");check(pg.evaluate('normalActs.length' if battle=='normal' else 'rbActs.length')==before,battle+' enemy phase rejects');pg.evaluate('attackBattleBusy=false' if battle=='normal' else 'rbBusy=false');pg.evaluate(choose+"('guard','aidan')");check(pg.evaluate('normalActs.length' if battle=='normal' else 'rbActs.length')==before+1,battle+' valid player command accepted')
  # Cancel native combat then stale provider must not prevent field movement.
  pg.evaluate('PrologueCombat.cancel()');pg.evaluate(FIELD);check(pg.evaluate('InputManager.state()')=='FIELD',battle+' cancelled field despite stale provider');pg.evaluate('delete window.BattleLoading');pg.evaluate(start);pg.wait_for_function('!BattlePresentation.busy');pg.evaluate("__ad.generation=PrologueCombat.generation;__ad.phase='input';BattleCommandGate.refresh()");check(pg.evaluate('InputManager.state()')=='BATTLE_COMMAND',battle+' consecutive start unlocks');pg.close()
 check(not errors,'browser errors',errors);browser.close()
fails=[r for r in rows if not r['ok']];(OUT/'results.json').write_text(json.dumps({'scope':'D-X actual UI/engine and native Opening; Loading/provider contract fixtures, not Claude integration','negative_control':bool(os.getenv('P0_INPUT_BEFORE')),'rows':rows,'fails':fails,'errors':errors},ensure_ascii=False,indent=2));print('FAILS',len(fails));sys.exit(bool(fails))

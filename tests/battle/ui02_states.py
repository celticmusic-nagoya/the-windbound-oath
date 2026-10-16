"""Native input-phase UI state transitions on desktop and mobile; no resource reimplementation."""
import sys,os,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
out=Path(os.environ.get('OUT','/tmp/ui02-states'));out.mkdir(parents=True,exist_ok=True);fails=[];rows=[]
def check(v,msg):
 print(('ok ' if v else 'FAIL ')+msg,flush=True)
 if not v:fails.append(msg)
with server(8807) as base,sync_playwright() as p:
 b=p.chromium.launch()
 for view,w,h in [('pc',1280,720),('portrait',390,844),('landscape',844,390)]:
  for battle in ['normal','raider']:
   pg=b.new_page(viewport={'width':w,'height':h},has_touch=view!='pc',is_mobile=view!='pc');errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
   pg.goto(base+'/index.html?dev=1');pg.wait_for_function('window.BattleUIState&&BattleMotion.loaded');pg.wait_for_timeout(1200)
   pg.evaluate('closeDialogue();'+('startAttackBattle("fieldGob3",100)' if battle=='normal' else 'startRaiderBattle()'))
   state=lambda:pg.evaluate('BattleUIState.snapshot("'+battle+'").status')
   pg.wait_for_function('BattleUIState.snapshot("'+battle+'").status==="collapsed"')
   if battle=='raider':pg.evaluate('PrologueCombat.spawn()')
   prefix=view+'/'+battle;toggle='#normalCommandToggle' if battle=='normal' else '#rbCommandToggle';cmd='#normalBattleCmd' if battle=='normal' else '#rbCmd';close='#normalCommandClose' if battle=='normal' else '#rbCommandClose';atk='#nAtk' if battle=='normal' else '#rbAtk';skill='#nSkill' if battle=='normal' else '#rbSkill';guard='#nGuard' if battle=='normal' else '#rbGuard';item='#nItem' if battle=='normal' else '#rbItem';itemClose='[data-ni="close"]' if battle=='normal' else '[data-ri="close"]';potion='[data-ni="potion"]' if battle=='normal' else '[data-ri="potion"]'
   def click(sel):pg.locator(sel).click() if view=='pc' else pg.locator(sel).tap()
   def exclusive(expected):
    shown=[name for name,sel in [('collapsed',toggle),('commands',cmd),('items','#normalItems'),('targets','#battleTargetPanel')] if pg.is_visible(sel)]
    check(state()==expected and shown==([expected] if expected!='busy' else []),prefix+' exclusive '+expected+' '+str(shown))
   exclusive('collapsed');rect=pg.locator(toggle).bounding_box();check(rect['width']>=44 and rect['height']>=44,prefix+' COMMAND tap area >=44px')
   pg.screenshot(path=str(out/(view+'-'+battle+'-collapsed.png')))
   click(toggle);exclusive('commands');pg.evaluate('updateAttackBattle()' if battle=='normal' else 'updateRaider()');exclusive('commands')
   pg.set_viewport_size({'width':h,'height':w});pg.wait_for_timeout(150);exclusive('commands');pg.set_viewport_size({'width':w,'height':h})
   click(close);pg.wait_for_timeout(450);exclusive('collapsed');pg.evaluate('updateAttackBattle()' if battle=='normal' else 'updateRaider()');exclusive('collapsed')
   if view=='pc':pg.keyboard.press('ArrowDown');check(pg.evaluate('document.activeElement.id')==atk[1:],prefix+' keyboard opens and focuses attack')
   else:click(toggle)
   click(atk);exclusive('targets');rect=pg.locator('#battleTargetPanel button').bounding_box();check(rect['width']>=44 and rect['height']>=44,prefix+' target cancel tap area >=44px');pg.screenshot(path=str(out/(view+'-'+battle+'-targets.png')));(pg.keyboard.press('Escape') if view=='pc' else click('#battleTargetPanel button'));exclusive('commands');check(pg.evaluate('document.activeElement.id')==atk[1:],prefix+' target cancel restores attack focus')
   click(item);exclusive('items');pg.screenshot(path=str(out/(view+'-'+battle+'-items.png')));click(itemClose);exclusive('commands');check(pg.evaluate('document.activeElement.id')==item[1:],prefix+' item back restores command focus')
   click(item);stock=pg.evaluate('battleItems.potion');click(potion);exclusive('targets');(pg.keyboard.press('Escape') if view=='pc' else click('#battleTargetPanel button'));exclusive('items');check(pg.evaluate('battleItems.potion')==stock,prefix+' cancelled item target does not consume');check(pg.evaluate('document.activeElement.dataset.ni||document.activeElement.dataset.ri')=='potion',prefix+' item target cancel restores item focus');click(itemClose)
   pg.evaluate('aatp=40;updateAttackBattle()' if battle=='normal' else 'rbTP=40;updateRaider()');click(skill);exclusive('targets');(pg.keyboard.press('Escape') if view=='pc' else click('#battleTargetPanel button'));exclusive('commands');check(pg.evaluate('aatp' if battle=='normal' else 'rbTP')==40,prefix+' cancelled skill target does not consume TP')
   click(guard);pg.wait_for_function(('normalActor' if battle=='normal' else 'rbActor')+'==="fiona"');exclusive('collapsed')
   click(toggle);click(guard);pg.wait_for_function('BattleUIState.snapshot("'+battle+'").status==="busy"');exclusive('busy')
   pg.evaluate('document.querySelector("'+toggle+'").click()');exclusive('busy');pg.wait_for_function('BattleUIState.snapshot("'+battle+'").status==="collapsed"',timeout=40000);exclusive('collapsed')
   # Old request callbacks must not resurrect a chooser in the next encounter.
   click(toggle);pg.evaluate('window.oldUITx=BattleUIState.beginTargets("'+battle+'");window.staleConfirm=0;BattleTargetSelector.open({type:"enemy_single",battle:"'+battle+'",candidates:PrologueCombat.targets("'+battle+'"),onConfirm:v=>BattleUIState.confirmTargets("'+battle+'",oldUITx,()=>staleConfirm++,v),onCancel:()=>BattleUIState.cancelTargets("'+battle+'",oldUITx)});BattleUIState.sync("'+battle+'")')
   pg.evaluate('PrologueCombat.instantKill("'+battle+'")');pg.wait_for_function('document.body.classList.contains("battleResultMode")',timeout=10000);exclusive('busy');pg.locator('#resultContinue').click()
   pg.evaluate('closeDialogue();'+('startAttackBattle("fieldGob1",100)' if battle=='normal' else 'devJump("raider")'));pg.wait_for_function('BattleUIState.snapshot("'+battle+'").status==="collapsed"');pg.wait_for_timeout(500);exclusive('collapsed');check(pg.evaluate('!BattleTargetSelector.active&&!document.querySelector(".battleTargetHit")'),prefix+' next battle has no old target UI')
   pg.evaluate('BattleUIState.cancelTargets("'+battle+'",oldUITx);BattleUIState.confirmTargets("'+battle+'",oldUITx,()=>staleConfirm++,"stale")');exclusive('collapsed');check(pg.evaluate('staleConfirm===0'),prefix+' stale cancel/confirm callbacks ignored');pg.evaluate('rbBusy=true' if battle=='normal' else 'attackBattleBusy=true');check(pg.evaluate('InputManager.state()')=='BATTLE_COMMAND',prefix+' inactive battle busy flag cannot block input');pg.evaluate('rbBusy=false' if battle=='normal' else 'attackBattleBusy=false');click(toggle);click(item);exclusive('items');pg.evaluate('devJump("opening")');pg.wait_for_function('BattleUIState.snapshot("'+battle+'").status==="inactive"');check(pg.is_hidden('#normalItems') and pg.evaluate('!BattleTargetSelector.active'),prefix+' scene exit clears shared item/target UI');check(not errors,prefix+' no page/console errors '+str(errors));rows.append({'view':view,'battle':battle,'errors':errors});pg.close()
 b.close()
(out/'results.json').write_text(json.dumps({'rows':rows,'fails':fails},indent=2));print('FAILS',len(fails));sys.exit(bool(fails))

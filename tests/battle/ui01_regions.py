"""UI-01 ownership compatibility: no combat, timing, motion, or drawer policy changes."""
import sys,os,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
fails=[];rows=[]
def check(ok,label):
 print(('ok ' if ok else 'FAIL ')+label,flush=True)
 if not ok:fails.append(label)
with server(8804) as base,sync_playwright() as p:
 b=p.chromium.launch()
 for mode in ['normal','raider']:
  pg=b.new_page(viewport={'width':390,'height':844},has_touch=True);errors=[];pg.on('pageerror',lambda e:errors.append(str(e)))
  pg.goto(base+'/index.html?dev=1');pg.wait_for_function('window.BattleUIRegions&&BattleMotion.loaded');pg.wait_for_timeout(1200)
  pg.evaluate('closeDialogue();'+('startAttackBattle("fieldGob3",100)' if mode=='normal' else 'startRaiderBattle()'));pg.wait_for_function('!BattlePresentation.busy && '+('!attackBattleBusy' if mode=='normal' else '!rbBusy'))
  if mode=='raider':pg.evaluate('PrologueCombat.spawn();PrologueCombat.spawn()')
  pg.wait_for_function('!document.querySelector("#'+('attackBattle' if mode=='normal' else 'raiderBattle')+' > .prologueEnemy")')
  check(pg.evaluate('''(b)=>{const r=BattleUIRegions.get(b);return ['field','command','actions','log'].every(k=>r[k].dataset.uiRegion===k)&&(b==='normal'?r.field.matches('#attackBattle > .v2BattleStage'):getComputedStyle(r.field).position==='relative')}''',mode),mode+' separate field/log/COMMAND/actions regions')
  check(pg.evaluate('document.querySelector("#normalItems").parentElement===BattleUIRegions.items && document.querySelector("#battleTargetPanel").parentElement===BattleUIRegions.targets'),mode+' independent item and target portals')
  check(pg.evaluate('''()=>{const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);return new Set(ids).size===ids.length}'''),mode+' no duplicate DOM IDs, including training')
  check(pg.evaluate('document.querySelector("#battleBg")===document.querySelector("#attackBattle #battleField").firstElementChild'),mode+' BG remains first child of normal battlefield')
  roster=pg.evaluate('''(b)=>PrologueCombat.enemies[b].map(e=>({id:e.id,key:e.key,hp:e.hp,type:e.type,node:e.node}))''',mode)
  check(pg.evaluate('''(b)=>PrologueCombat.enemies[b].filter(e=>e.extra).every(e=>BattleUIRegions.get(b).extras.contains(document.querySelector('#'+e.unit)))''',mode),mode+' extra enemies belong to field without slot logic')
  toggle='#normalCommandToggle' if mode=='normal' else '#rbCommandToggle';panel='#normalBattleCmd' if mode=='normal' else '#rbCmd';close='#normalCommandClose' if mode=='normal' else '#rbCommandClose'
  pg.locator(toggle).tap();check(pg.is_visible(panel),mode+' legacy COMMAND touch opens');pg.locator(close).tap();check(not pg.is_visible(panel),mode+' legacy close works')
  pg.locator(toggle).tap();pg.locator('#nItem' if mode=='normal' else '#rbItem').tap();check(pg.is_visible('#normalItems'),mode+' legacy item selection opens in its own portal')
  pg.locator('[data-ni="close"]' if mode=='normal' else '[data-ri="close"]').tap();check(not pg.is_visible('#normalItems'),mode+' item return hides the existing list')
  pg.evaluate('BattleTargetSelector.open({type:"enemy_single",battle:"'+mode+'",candidates:PrologueCombat.targets("'+mode+'"),onConfirm:()=>{},onCancel:()=>{}})');pg.wait_for_function('document.querySelectorAll(".battleTargetHit").length>1 && [...document.querySelectorAll(".battleTargetHit")].every(e=>e.parentElement===BattleUIRegions.targets)')
  check(pg.evaluate('BattleTargetSelector.active'),mode+' multiple-target chooser keeps native viewport hitboxes')
  pg.keyboard.press('Escape');check(pg.evaluate('!BattleTargetSelector.active&&!document.querySelector(".battleTargetHit")'),mode+' target cancellation removes hitboxes')
  pg.evaluate(('showBattleBanner' if mode=='normal' else 'showRaiderBattleLog')+'("UI-01ログ検証",1000)')
  check(pg.evaluate('''(b)=>{const l=BattleUIRegions.get(b).log;return l.textContent.includes('UI-01ログ検証')}''',mode),mode+' independent native log displays')
  check(roster==pg.evaluate('''(b)=>PrologueCombat.enemies[b].map(e=>({id:e.id,key:e.key,hp:e.hp,type:e.type,node:e.node}))''',mode),mode+' structural operations leave IDs/HP/roster unchanged')
  pg.evaluate('PrologueCombat.instantKill("'+mode+'")');pg.wait_for_function('document.body.classList.contains("battleResultMode")',timeout=10000);check(pg.is_visible('#resultContinue'),mode+' native KO/victory result completes')
  pg.locator('#resultContinue').click();check(not pg.is_visible('#battleResult'),mode+' result confirmation returns through native handler')
  check(not errors,mode+' no page errors '+str(errors));pg.close()
 # Renamed training containers must keep their existing styling and callbacks.
 pg=b.new_page(viewport={'width':390,'height':844});training_errors=[];pg.on('pageerror',lambda e:training_errors.append(str(e)));pg.goto(base+'/index.html?dev=1');pg.wait_for_function('window.BattleUIRegions');pg.wait_for_timeout(1200)
 pg.evaluate('closeDialogue();storyStage=1;startTraining()')
 check(pg.is_visible('#trainingBattleField') and pg.evaluate('getComputedStyle(document.querySelector("#trainingBattleField")).position==="absolute"'),'training renamed field remains styled and visible')
 pg.locator('#atk').click();pg.wait_for_function('!battleBusy');check(pg.evaluate('dhp===152&&atp===15&&ahp===87'),'training attack still uses its original callback')
 pg.locator('#guard').click();pg.wait_for_function('!battleBusy');check(pg.evaluate('atp===25&&ahp===81'),'training guard still uses its original callback')
 pg.evaluate('atp=30;updateBattle()');pg.locator('#skill').click();pg.wait_for_function('!battleBusy');check(pg.evaluate('dhp===110&&atp===0'),'training skill remains independent from normal legacy commands')
 pg.evaluate('dhp=1;updateBattle()');pg.locator('#atk').click();pg.wait_for_function('storyStage===3');check(not pg.is_visible('#battle'),'training native victory and story return remain intact')
 check(not training_errors,'training no page errors '+str(training_errors));pg.close();b.close()
print('FAILS' ,len(fails));sys.exit(bool(fails))

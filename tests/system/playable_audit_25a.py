"""25A observation probe. Normal NEW GAME route first; isolated seeded diagnostics second.
No product writes, save migrations, teleport, DEV kills or time acceleration in normal-route section.
Run serially via tools/qa/run_all.sh; artifacts go to external QA_OUT.
"""
import json, os, time, traceback
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT=Path(os.environ['QA_OUT']).resolve(); assert not OUT.is_relative_to(Path(__file__).resolve().parents[2]); OUT.mkdir(parents=True,exist_ok=True)
report={'conditions':{'browser':'Chromium headless','hardware':'cloud container; NOT Android hardware','normal_route':'title NEW GAME, actual walk/pathfinder and rendered controls; no seed/teleport/DEV kill'},'checks':[],'errors':[],'http_errors':[],'console_errors':[],'route':[]}
fails=[]
def ck(name,ok,detail=None):
 report['checks'].append({'name':name,'pass':bool(ok),'detail':detail}); print(('ok   ' if ok else 'FAIL ')+name,flush=True)
 if not ok:fails.append(name)
with sync_playwright() as pw:
 b=pw.chromium.launch(); report['conditions']['version']=b.version
 def page(w=390,h=844):
  c=b.new_context(viewport={'width':w,'height':h},is_mobile=w<1000,has_touch=w<1000);p=c.new_page()
  p.on('pageerror',lambda e:report['errors'].append(str(e)))
  p.on('console',lambda m:report['console_errors'].append(m.text) if m.type=='error' else None)
  p.on('response',lambda r:report['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
  p.goto('http://localhost:8765/index.html?title=1');p.get_by_role('button',name='NEW GAME',exact=True).click();p.wait_for_function("LoadCoordinator.phase==='READY'&&MossForest.active&&document.body.classList.contains('dialogueOpen')")
  return c,p
 c,p=page(); ev=p.evaluate
 def snap(label):
  state=ev("({stage:storyStage,map:MossForest.mapId,feet:MossForest.feet,loading:LoadCoordinator.phase,objective:currentObjective})");report['route'].append({'label':label,**state});p.screenshot(path=str(OUT/(label+'.png')));print('STATE',label,json.dumps(state,ensure_ascii=False),flush=True)
 def dismiss():
  if p.locator('#msg').is_visible():p.locator('#msg').click();p.wait_for_timeout(100)
 def walk(x,y,expected=None,timeout=120000):
  old=ev('MossForest.mapId');accepted=ev('([x,y])=>MossForest.goFeet(x,y)',[x,y]);ck('route accepted '+str((x,y)),accepted)
  if not accepted:raise AssertionError('unreachable path target')
  p.wait_for_function("m=>MossForest.mapId!==m||(!MossForest.target&&!MossForest.busy)",arg=old,timeout=timeout)
  if not expected:
   state=ev('({feet:MossForest.feet,outcome:MossForest.status.outcome})');distance=((state['feet']['x']-x)**2+(state['feet']['y']-y)**2)**.5;ck('route arrived '+str((x,y)),distance<30,state)
   if distance>=30:raise AssertionError('walk stopped before destination: '+str(state))
  if expected:p.wait_for_function("m=>MossForest.mapId===m&&MossForest.active&&!MossForest.busy&&!LoadingInput.busy",arg=expected,timeout=30000)
 def worldtap(x,y):
  pt=ev("([x,y])=>{let r=document.querySelector('#forestWorld').getBoundingClientRect(),s=FieldCamera.scale;return [r.left+x*s,r.top+y*s]}",[x,y]);p.touchscreen.tap(*pt);p.wait_for_timeout(300)
 try:
  snap('25a_normal_house');ck('NEW GAME starts at house stage0',ev("storyStage===0&&MossForest.mapId==='rilde_in_aidan'"));dismiss()
  walk(480,629,'rilde_village_01_peace');walk(1880,940);worldtap(1930,885)
  p.wait_for_function('storyStage===1',timeout=20000);snap('25a_normal_fiona');dismiss();walk(2030,935);worldtap(2075,875)
  p.wait_for_function("storyStage===2&&getComputedStyle(document.querySelector('#battle')).display!=='none'",timeout=15000)
  training=[]
  for _ in range(15):
   if ev('storyStage')!=2:break
   p.wait_for_function('!battleBusy||storyStage!==2',timeout=15000)
   if ev('storyStage')!=2:break
   before=ev('({hp:ahp,tp:atp,enemy:dhp})');button='#skill' if before['tp']>=30 else '#atk';p.locator(button).click();p.wait_for_timeout(750);training.append({'before':before,'button':button,'after':ev('({hp:ahp,tp:atp,enemy:dhp})')})
   if ev('dhp')<=0:break
  p.wait_for_function('storyStage===3',timeout=10000);report['training']=training;snap('25a_normal_training_won');ck('actual training UI wins without DEV',ev('storyStage===3&&dhp<=0'));dismiss()
  walk(830,1630,'cliff_moher_01_spiral_ascent');snap('25a_normal_cliff_entry');walk(2400,1500,timeout=240000);walk(2400,1040,timeout=60000);worldtap(2400,960)
  p.wait_for_function('FieldTalk.active',timeout=10000)
  for _ in range(8):
   if p.locator('.talkChoices button').count():break
   dismiss()
  p.locator('.talkChoices button').first.click();p.wait_for_timeout(500)
  end=time.monotonic()+90
  while ev('FieldScene.running') and time.monotonic()<end:
   if p.locator('#msg').is_visible():p.locator('#msg').click()
   p.wait_for_timeout(220)
  for _ in range(24):
   if not p.locator('#returnScene').is_visible():break
   p.locator('#returnScene').click();p.wait_for_timeout(120)
  ck('normal route reaches village attack',ev('storyStage>=5'));snap('25a_normal_attack');report['normal_route_endpoint']=report['route'][-1]
 except Exception as e:
  report['normal_route_exception']=str(e);snap('25a_normal_stopped');ck('normal opening route completed to attack',False,str(e))
 finally:c.close()
 # Seeded diagnostics are deliberately isolated from the continuous route above.
 c,p=page(844,390);ev=p.evaluate;dismiss()
 ev("PrologueProgress.seed(3);storyStage=15;louFound=true;forestStoneSeen=true;syncStoryEquipment();closeDialogue();FieldTalk.setFlag('road_dunvall_open',true);PartyManager.join('liam');FieldTalk.setFlag('liam_joined',true);forestActive=true;document.querySelector('#forestScene').style.display='block';MossForest.enter({map:'royal_capital_02_castle_plaza',spawn:'from_market'})")
 p.wait_for_function("MossForest.mapId==='royal_capital_02_castle_plaza'&&MossForest.active&&!MossForest.busy&&!LoadingInput.busy")
 report['seeded_party']=ev('({active:PartyManager.active,members:PartyManager.members})');snap('25a_seeded_capital')
 report['seeded_exp']=ev("(()=>{const before=JSON.parse(JSON.stringify(PartyManager.members));PartyManager.addExp(13);return {before,after:JSON.parse(JSON.stringify(PartyManager.members))}})()");ck('joined reserve receives full13 EXP',report['seeded_exp']['after']['liam']['exp']-report['seeded_exp']['before']['liam']['exp']==13);ev('saveGrowthData()');raw=ev('localStorage.getItem(SAVE_KEY)');ck('seeded capital SAVE writes a record',bool(raw));c.close()
 # New browser context loads the exact serialized bytes; no SAVE_KEY guessing or migration.
 c,p=page();ev=p.evaluate;dismiss();ev('([k,v])=>localStorage.setItem(k,v)',[p.evaluate('SAVE_KEY'),raw]);restored=ev('SaveContinue.start()');p.wait_for_function("LoadCoordinator.phase==='READY'&&!LoadingInput.busy");report['seeded_cold_restore']={'ok':restored,'map':ev('MossForest.mapId'),'party':ev('({active:PartyManager.active,reserve:PartyManager.reserve,members:PartyManager.members})')};ck('seeded capital/party LOAD restores',restored and ev("MossForest.mapId==='royal_capital_02_castle_plaza'&&PartyManager.members.liam.joined"))
 for w,h in [(390,844),(844,390),(1920,1080)]:
  p.set_viewport_size({'width':w,'height':h});p.wait_for_timeout(300);ck('rotation retains map and input '+str((w,h)),ev("MossForest.active&&!LoadingInput.busy&&MossForest.mapId==='royal_capital_02_castle_plaza'"))
 c.close()
 # Audit existing production interact hooks in a fresh context; not normal-route evidence.
 c,p=page();ev=p.evaluate;dismiss()
 rewards={};report['seeded_rewards']=rewards
 for hook,item,amount in [('rilde_drawer','potion',1),('rilde_pot','gold',3)]:
  before=ev("id=>id==='gold'?gold:Inventory.count(id)",item);ev("h=>RildeVillage.hook({hook:h},MossForest.map)",hook);after=ev("id=>id==='gold'?gold:Inventory.count(id)",item);rewards[hook]={'before':before,'after':after,'expected_delta':amount,'message':p.locator('#msg').inner_text()};ck(hook+' grants advertised reward',after-before==amount,rewards[hook]);dismiss()
 before=ev("Inventory.count('potion')");ev("RildeVillage.hook({hook:'rilde_kid'},MossForest.map)");dismiss();ev("RildeVillage.hook({hook:'rilde_balloon_tree'},MossForest.map)");after=ev("Inventory.count('potion')");rewards['balloon']={'before':before,'after':after,'expected_delta':2,'message':p.locator('#msg').inner_text(),'done':ev('flags.balloonDone')};ck('balloon completion grants advertised2 potions',after-before==2,rewards['balloon']);dismiss()
 ev("RildeVillage.hook({hook:'rilde_catowner'},MossForest.map)");dismiss();ev("RildeVillage.hook({hook:'rilde_cat'},MossForest.map)");dismiss();ev("RildeVillage.hook({hook:'rilde_catowner'},MossForest.map)");rewards['cat']=ev("({done:flags.catDone,itemId:Object.keys(ItemData.items).find(k=>ItemData.items[k].name==='毒消し')||null,items:Inventory.serialize(),consumables:{...battleItems},message:document.querySelector('#msg').textContent})");ck('cat completion grants advertised antidote item',bool(rewards['cat']['itemId']) and ev("id=>Inventory.count(id)>=2",rewards['cat']['itemId']),rewards['cat']);dismiss();c.close()
 # Complete the existing fort final pages and END button, isolated seeded fixture.
 c,p=page();ev=p.evaluate;dismiss();ev('PrologueProgress.seed(3);storyStage=13;startFortFinale()')
 for _ in range(14):
  if not p.locator('#fortScene').is_visible():break
  p.locator('#fortScene').click();p.wait_for_timeout(100)
 ck('fort final pages show existing PROLOGUE END',ev('storyStage===15') and p.locator('#prologueEnd').is_visible());p.locator('#endReturn').click();p.wait_for_function("storyStage===15&&MossForest.mapId.startsWith('fort_dunvall')&&MossForest.active&&!MossForest.busy&&!LoadingInput.busy");report['seeded_end_free_roam']=ev('({stage:storyStage,map:MossForest.mapId})');ck('END returns to live fort free roam',ev('MossForest.active'));c.close()
 # Low-HP injection tests documented current recovery rules, not balanced normal play.
 c,p=page(844,390);ev=p.evaluate;dismiss();ev("storyStage=9;startAttackBattle('mossSlime1',100)");p.wait_for_function("!battleCommandLocked('normal')",timeout=20000)
 ev('aahp=1;normalFHP=1');ev("PrologueCombat.enemyRound('normal')");report['seeded_normal_defeat']=ev('({aidan:aahp,fiona:normalFHP,busy:attackBattleBusy})');ck('normal current low-HP recovery restores commands',ev('aahp>=35&&normalFHP>=32&&!attackBattleBusy'));c.close()
 c,p=page(844,390);ev=p.evaluate;dismiss();ev('storyStage=12;startRaiderBattle()');p.wait_for_function("!battleCommandLocked('raider')",timeout=25000)
 ev('rbHP=1;rbFHP=1');ev("PrologueCombat.enemyRound('raider')");p.wait_for_function("rbHP===120&&rbFHP===105&&!battleCommandLocked('raider')",timeout=25000)
 report['seeded_raider_rematch']=ev('({aidan:rbHP,fiona:rbFHP,boss:rbBoss,busy:rbBusy})');ck('Raider current defeat rule restarts encounter',ev('rbBoss===1250'));c.close();b.close()
ck('no unhandled page errors',not report['errors'],report['errors']);ck('no HTTP failure observed in probe',not report['http_errors'],report['http_errors']);ck('no console errors observed in probe',not report['console_errors'],report['console_errors'])
report['fails']=fails;(OUT/'playable-probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('FAILS',len(fails));raise SystemExit(bool(fails))

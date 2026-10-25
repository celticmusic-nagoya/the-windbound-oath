"""Mandatory cold-title/CONTINUE/ownership browser QA; no title bypass."""
import json,os,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT=Path(os.environ['QA_OUT']);OUT.mkdir(parents=True,exist_ok=True)
BASE=os.environ.get('QA_URL','http://127.0.0.1:8765/index.html').split('?')[0]+'?title=1'
rows=[];errors=[]
def ck(name,ok):
 rows.append({'name':name,'status':'PASS' if ok else 'FAIL'});(OUT/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(('PASS ' if ok else 'FAIL ')+name,flush=True);assert ok,name
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=os.environ.get('PW_CHROMIUM_EXECUTABLE'))
 def page(raw=None,key=None):
  c=b.new_context(viewport={'width':1280,'height':720})
  if raw is not None:c.add_init_script('localStorage.setItem('+json.dumps(key)+','+json.dumps(raw)+')')
  p=c.new_page();p.on('pageerror',lambda e:errors.append(str(e)));p.goto(BASE);p.wait_for_selector('#title-screen',state='visible');return c,p
 def close(p):
  for _ in range(40):
   if p.evaluate("InputManager.state()!=='DIALOGUE'"):return
   p.keyboard.press('Enter');p.wait_for_timeout(100)
  raise RuntimeError('dialogue did not close')
 c,p=page();ck('empty slot disables CONTINUE',p.get_by_role('button',name='CONTINUE',exact=True).is_disabled());p.get_by_role('button',name='NEW GAME',exact=True).click();p.wait_for_function("LoadCoordinator.phase==='READY'&&MossForest.active");close(p)
 ck('NEW GAME reaches actual house and releases title input owner',p.evaluate("MossForest.mapId==='rilde_in_aidan'&&!TitleScreen.active()&&LoadCoordinator.canSave"))
 p.evaluate("RildeVillage.hook({hook:'rilde_drawer'},MossForest.map)");close(p);p.evaluate('saveGrowthData()');key=p.evaluate('SAVE_KEY');raw=p.evaluate('localStorage.getItem(SAVE_KEY)');record=json.loads(raw)
 ck('actual drawer acquisition and explicit unclaimed pot serialized',record['prologue']['legacyEvents']['drawer'] is True and record['prologue']['legacyEvents']['pot'] is False);c.close()
 c,p=page(raw,key);ck('cold valid record enables CONTINUE',p.get_by_role('button',name='CONTINUE',exact=True).is_enabled());p.get_by_role('button',name='CONTINUE',exact=True).click();p.wait_for_function("SaveContinue.phase==='READY'&&LoadCoordinator.phase==='READY'&&MossForest.active");m=record['prologue']['moss'];ck('cold CONTINUE restores exact map/feet',p.evaluate('MossForest.mapId')==m['map'] and p.evaluate('MossForest.feet')=={'x':m['x']+17,'y':m['y']+42})
 ck('cold CONTINUE restores claimed and unclaimed events',p.evaluate('flags.drawer===true&&flags.pot===false'));inventory=p.evaluate('Inventory.serialize()');p.evaluate("RildeVillage.hook({hook:'rilde_drawer'},MossForest.map)");ck('claimed drawer is not awarded twice',inventory==p.evaluate('Inventory.serialize()'));ck('CONTINUE never auto-overwrites source bytes',p.evaluate('localStorage.getItem(SAVE_KEY)')==raw);c.close()
 old=json.loads(raw);old['prologue'].pop('legacyEvents');oldraw=json.dumps(old);c,p=page(oldraw,key);p.get_by_role('button',name='CONTINUE',exact=True).click();p.wait_for_function("SaveContinue.phase==='READY'");ck('old unknown acquisition restricts drawer/pot without rewriting SAVE',p.evaluate('flags.drawer===true&&flags.pot===true') and p.evaluate('localStorage.getItem(SAVE_KEY)')==oldraw);c.close()
 c,p=page('{broken',key);ck('corrupt SAVE remains read-only at title',p.get_by_role('button',name='CONTINUE',exact=True).is_disabled() and p.evaluate('localStorage.getItem(SAVE_KEY)')=='{broken');c.close()
 c,p=page(raw,key);held=[];requests=[]
 def delayed(route):
  requests.append(route.request.url)
  if not held:held.append(route)
  else:route.continue_()
 p.route('**/data/maps/rilde_in_aidan.json',delayed);p.get_by_role('button',name='CONTINUE',exact=True).click();p.wait_for_timeout(150);ck('CONTINUE owns pending map transaction',bool(held) and p.evaluate("SaveContinue.phase==='LOADING'"))
 p.evaluate('TitleScreen.newGame(true)');p.wait_for_function("LoadCoordinator.phase==='READY'&&MossForest.active");held[0].continue_();p.wait_for_timeout(500)
 ck('new NEW GAME invalidates late CONTINUE response and restores unclaimed events',p.evaluate("storyStage===0&&MossForest.mapId==='rilde_in_aidan'&&flags.drawer===false&&flags.pot===false"));ck('race leaves original SAVE bytes untouched',p.evaluate('localStorage.getItem(SAVE_KEY)')==raw);c.close()
 ck('no unhandled page errors',not errors);b.close()
print(str(len(rows))+' core browser assertions PASS')

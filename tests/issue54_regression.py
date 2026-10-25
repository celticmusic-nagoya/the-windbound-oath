"""Isolated Issue54/KI004 QA. Serve repo at QA_URL (default localhost:8859).
QA_OUT must be outside the checkout. Every context has fresh browser storage.
Fixtures are copies of historical evidence, never written back to their sources.
"""
from pathlib import Path
import os,json,copy,traceback
from playwright.sync_api import sync_playwright,TimeoutError
ROOT=Path(__file__).resolve().parents[1];OUT=Path(os.environ['QA_OUT']);OUT.mkdir(parents=True,exist_ok=True)
URL=os.environ.get('QA_URL','http://127.0.0.1:8859/index.html')
S2=json.loads((ROOT/'tests/fixtures/issue54-stage2.json').read_text());S15=json.loads((ROOT/'tests/fixtures/issue54-stage15.json').read_text());rows=[];errors=[];console=[]
STATE="""()=>({phase:LoadCoordinator.phase,stage:storyStage,map:MossForest.mapId,feet:MossForest.feet,active:MossForest.active,busy:MossForest.busy,enterCount:MossForest.enterCount,battle:getComputedStyle(document.querySelector('#battle')).display,end:getComputedStyle(document.querySelector('#prologueEnd')).display,inventory:Inventory.serialize(),equipment:EquipmentManager.serialize(),progress:PrologueProgress.serialize(),members:PartyManager.members,gold,battleItems,ahp,battleBusy})"""
def ck(n,ok,detail=None):
 rows.append({'name':n,'status':'PASS' if ok else 'FAIL','detail':detail});(OUT/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));print(n,rows[-1]['status'],flush=True)
 if not ok:raise AssertionError(n)
def new(b,mobile=False,init=None):
 c=b.new_context(viewport={'width':390 if mobile else 1280,'height':844 if mobile else 720},is_mobile=mobile,has_touch=mobile)
 if init:c.add_init_script(init)
 p=c.new_page();p.on('pageerror',lambda e:errors.append(str(e)));p.on('console',lambda m:m.type=='error' and console.append(m.text));p.goto(URL);p.wait_for_function("LoadCoordinator.phase==='READY'",timeout=30000);p.evaluate('TrainingCheckpoint.ready');close(p);return c,p
def close(p):
 for _ in range(30):
  if p.evaluate('InputManager.state()')!='DIALOGUE':return
  p.keyboard.press('Enter');p.wait_for_timeout(120)
 raise RuntimeError('Dialogue did not settle')
def menu(p,touch=False):
 if not p.locator('#systemMenu').is_visible():
  if touch:p.locator('#menuOpen').tap()
  else:p.keyboard.press('m')
 p.locator('[data-stab="save"]').click()
def put(p,d):p.evaluate('(d)=>localStorage.setItem(SAVE_KEY,JSON.stringify(d))',d)
def load(p,touch=False):
 menu(p,touch);p.locator('#doLoad').tap() if touch else p.locator('#doLoad').click();p.wait_for_function("LoadCoordinator.phase!=='LOADING'")
 if p.evaluate("LoadCoordinator.phase==='READY'"):
  p.locator('#systemClose').tap() if touch else p.locator('#systemClose').click();close(p)
def save(p,touch=False):
 menu(p,touch);p.locator('#doSave').tap() if touch else p.locator('#doSave').click();d=p.evaluate('JSON.parse(localStorage.getItem(SAVE_KEY))');p.locator('#systemClose').click();return d
def snap(p,n):
 d=p.evaluate(STATE);(OUT/(n+'.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2));p.screenshot(path=str(OUT/(n+'.png')));return d
def world(p,x,y):
 pt=p.evaluate("([x,y])=>{const r=document.querySelector('#forestWorld').getBoundingClientRect();return [r.left+x*r.width/MossForest.map.world.width,r.top+y*r.height/MossForest.map.world.height]}",[x,y]);p.mouse.click(*pt)
def train(p):world(p,2075,875);p.wait_for_function("storyStage===2&&document.querySelector('#battle').style.display==='block'")
def win(p):
 for _ in range(8):
  if p.evaluate('storyStage===3'):break
  p.wait_for_function('!battleBusy||storyStage===3')
  if p.evaluate('storyStage===3'):break
  p.locator('#atk').click();p.wait_for_timeout(760)
 p.wait_for_function('storyStage===3');close(p);p.wait_for_function('!MossForest.busy')
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'))
  # Probe LOAD before the startup handler while retaining the original slot.
  init="localStorage.setItem('windbound_oath_v028',"+json.dumps(json.dumps(S2,ensure_ascii=False))+");document.addEventListener('DOMContentLoaded',async()=>{const raw=localStorage.getItem('windbound_oath_v028');window.bootProbe={result:await loadGrowthData(),rawUnchanged:raw===localStorage.getItem('windbound_oath_v028'),stage:storyStage}}, {once:true});"
  c,p=new(b,init=init);probe=p.evaluate('bootProbe');ck('startup_load_guard',probe=={'result':False,'rawUnchanged':True,'stage':0},probe);snap(p,'01_boot_guard');c.close()
  # Normal new-game reach: no injected progress, no DEV jump.
  c,p=new(b);ck('new_game_initial_map',p.evaluate("storyStage===0&&MossForest.mapId==='rilde_in_aidan'"))
  p.keyboard.down('ArrowDown');p.wait_for_function('MossForest.feet.y>=615');p.keyboard.up('ArrowDown');p.keyboard.down('ArrowRight');p.wait_for_function("MossForest.mapId==='rilde_village_01_peace'&&MossForest.active&&!MossForest.busy");p.keyboard.up('ArrowRight')
  for x,y in [(1345,700),(1525,700),(1700,800),(1850,925)]:world(p,x,y);p.wait_for_timeout(150);p.wait_for_function('!MossForest.target');close(p)
  world(p,1930,885);p.wait_for_function('storyStage===1');close(p);ck('normal_play_reaches_stage1',p.evaluate('storyStage===1'))
  save(p);raw=p.evaluate('localStorage.getItem(SAVE_KEY)');train(p);menu(p);p.locator('#doSave').click();ck('training_UI_save_refused_original_kept',raw==p.evaluate('localStorage.getItem(SAVE_KEY)'));snap(p,'02_training_save_refused');p.locator('#systemClose').click()
  p.locator('#atk').click();load(p);before=p.evaluate(STATE);p.wait_for_timeout(2600);after=p.evaluate(STATE);ck('pending_training_action_cancelled',before['stage']==after['stage']==1 and before['ahp']==after['ahp'] and not after['battleBusy']);c.close()
  for i in range(3):
   c,p=new(b);put(p,S2);p.reload();p.wait_for_function("LoadCoordinator.phase==='READY'");p.evaluate('TrainingCheckpoint.ready');close(p);raw=p.evaluate('localStorage.getItem(SAVE_KEY)');n=p.evaluate('MossForest.enterCount');load(p);s=snap(p,f'03_stage2_rescue_{i}')
   ck(f'v2_single_restore_exact_position_{i}',s['stage']==1 and s['map']==S2['prologue']['moss']['map'] and s['feet']=={'x':2075,'y':875} and s['active'] and s['phase']=='READY' and s['enterCount']==n+1,s)
   ck(f'original_save_and_assets_kept_{i}',raw==p.evaluate('localStorage.getItem(SAVE_KEY)') and all(s[k]==S2[k] for k in ['inventory','equipment','members','gold','battleItems']) and s['progress']['subQuests']==S2['prologue']['subQuests'])
   train(p);win(p);ck(f'normal_retry_reaches_stage3_{i}',p.evaluate('storyStage===3'));snap(p,f'04_stage3_{i}');c.close()
  # Both conceptual predicates can match, but exactly one plan kind is selected.
  c,p=new(b);plans=p.evaluate("d=>{const x=TrainingCheckpoint.prepare(d,JSON.stringify(d));return {retry:PrologueProgress.plan(x.data.prologue,x.restoreVillage),early:MossForestStory.canRestoreEarlyMap(x.data.prologue,1),normal:PrologueProgress.plan(x.data.prologue)}}",S2)
  ck('restore_route_exclusion',plans['early'] and plans['retry']['kind']=='TRAINING_RETRY' and plans['normal']['kind']=='FIELD_MAP',plans)
  for name,mutate in [('invalid_map',lambda d:d['prologue']['moss'].update(map='invalid')),('invalid_coordinate',lambda d:d['prologue']['moss'].update(x=-1)),('inconsistent_flags',lambda d:d['prologue'].update(louFound=True)),('v1_stage2',lambda d:d['prologue'].update(version=1))]:
   d=copy.deepcopy(S2);mutate(d);put(p,d);menu(p);raw=p.evaluate('localStorage.getItem(SAVE_KEY)');stage=p.evaluate('storyStage');ok=p.evaluate('loadGrowthData()');ck(name+'_refused_original_kept',ok is False and p.evaluate('storyStage')==stage and raw==p.evaluate('localStorage.getItem(SAVE_KEY)'));p.locator('#systemClose').click()
  c.close()
  # Real failed map response (valid preflight data, corrupt runtime JSON).
  c,p=new(b);put(p,S2);raw=p.evaluate('localStorage.getItem(SAVE_KEY)');n=p.evaluate('MossForest.enterCount');p.route('**/data/maps/rilde_village_01_peace.json',lambda route:route.fulfill(status=200,content_type='application/json',body='{broken'))
  load(p);ck('map_restore_failure_latched',p.evaluate("LoadCoordinator.phase==='FAILED'&&!LoadCoordinator.canSave") and p.locator('#retryLoad').is_visible());p.evaluate('saveGrowthData();eraseGrowthData()');ck('failed_restore_blocks_save_and_erase',raw==p.evaluate('localStorage.getItem(SAVE_KEY)'));snap(p,'05_failure_latched')
  p.unroute('**/data/maps/rilde_village_01_peace.json');p.locator('#retryLoad').click();p.wait_for_function("LoadCoordinator.phase==='READY'");s=snap(p,'06_explicit_retry');ck('explicit_retry_single_restore',s['stage']==1 and s['active'] and s['feet']=={'x':2075,'y':875} and s['enterCount']==n+2 and raw==p.evaluate('localStorage.getItem(SAVE_KEY)'));c.close()
  # An obsolete map response must not mount after a newer explicit request.
  c,p=new(b);held=[];fort=json.loads((ROOT/'data/maps/fort_dunvall_01_courtyard.json').read_text());p.route('**/data/maps/fort_dunvall_01_courtyard.json',lambda route:held.append(route))
  p.evaluate("()=>{window.obsolete=null;MossForest.enter({map:'fort_dunvall_01_courtyard'}).then(()=>obsolete='wrongly applied',()=>obsolete='cancelled')}");p.wait_for_timeout(150);ck('obsolete_request_held',len(held)==1)
  p.evaluate("async()=>{MossForest.cancelPendingEnter();storyStage=1;await MossForest.enter({map:'rilde_village_01_peace',x:2058,y:833,flags:MossForestStory.flagsNow()})}")
  held[0].fulfill(status=200,content_type='application/json',body=json.dumps(fort));p.wait_for_function("obsolete!==null");ck('obsolete_async_response_cannot_overwrite',p.evaluate("obsolete==='cancelled'&&MossForest.mapId==='rilde_village_01_peace'&&MossForest.active"));c.close()
  # KI004 regressions on independent contexts, ordinary save and load buttons.
  for i in range(3):
   c,p=new(b);p.keyboard.down('ArrowRight');p.wait_for_timeout(220);p.keyboard.up('ArrowRight');d=save(p);p.keyboard.down('ArrowLeft');p.wait_for_timeout(220);p.keyboard.up('ArrowLeft');load(p);s=snap(p,f'07_stage0_{i}');m=d['prologue']['moss'];ck(f'KI004_stage0_position_{i}',s['stage']==0 and s['active'] and s['map']==m['map'] and s['feet']=={'x':m['x']+17,'y':m['y']+42});c.close()
   c,p=new(b);put(p,S15);load(p);p.keyboard.down('ArrowRight');p.wait_for_timeout(150);p.keyboard.up('ArrowRight');d=save(p);p.keyboard.down('ArrowLeft');p.wait_for_timeout(150);p.keyboard.up('ArrowLeft');load(p);s=snap(p,f'08_stage15_{i}');m=d['prologue']['moss'];ck(f'KI004_stage15_position_{i}',s['stage']==15 and s['active'] and s['end']=='none' and s['feet']=={'x':m['x']+17,'y':m['y']+42});p.reload();p.wait_for_function("LoadCoordinator.phase==='READY'");close(p);load(p);ck(f'KI004_stage15_reload_{i}',p.evaluate('MossForest.feet')=={'x':m['x']+17,'y':m['y']+42});c.close()
  for battle in ['normal','raider']:
   c,p=new(b);save(p);raw=p.evaluate('localStorage.getItem(SAVE_KEY)');committed=p.evaluate("async b=>{if(b==='normal'){storyStage=6;return await startAttackBattle('attackGob2',100)}else{storyStage=12;return await startRaiderBattle()}}",battle);ck(battle+'_entry_committed',committed is True);p.wait_for_function("b=>!battleCommandLocked(b)",arg=battle);p.evaluate('saveGrowthData()');ck(battle+'_battle_save_refusal',raw==p.evaluate('localStorage.getItem(SAVE_KEY)'))
   p.evaluate("b=>b==='normal'?chooseNormalAct('guard'):choosePartyAct('guard')",battle);ck(battle+'_battle_command_works',p.evaluate("b=>b==='normal'?normalActor==='fiona':rbActor==='fiona'",battle));c.close()
  # Mobile supported field/menu operations. Training overlay MENU is a separate known limitation.
  c,p=new(b,True);put(p,S2);load(p,True);ck('mobile_stage2_load_touch',p.evaluate("storyStage===1&&MossForest.active&&LoadCoordinator.phase==='READY'"));d=save(p,True);p.reload();p.wait_for_function("LoadCoordinator.phase==='READY'");close(p);load(p,True);ck('mobile_normal_save_load_touch',p.evaluate('MossForest.feet')=={'x':d['prologue']['moss']['x']+17,'y':d['prologue']['moss']['y']+42});snap(p,'09_mobile_field')
  p.evaluate('startTraining();TrainingCheckpoint.watchField()');reachable=True
  try:p.locator('#menuOpen').tap(timeout=1200)
  except TimeoutError:reachable=False
  ck('mobile_training_MENU_existing_constraint_recorded',reachable is False,{'expected_existing_overlay_interception':True,'ordinary_MENU_reached':reachable});snap(p,'10_mobile_training_overlay');c.close()
  ck('no_page_or_console_errors',not errors and not console,{'pageerrors':errors,'console_errors':console});b.close()
except Exception:
 (OUT/'STOP.txt').write_text(traceback.format_exc());raise
finally:
 (OUT/'console.json').write_text(json.dumps({'pageerrors':errors,'console_errors':console},ensure_ascii=False,indent=2))

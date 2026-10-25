"""Extra full-round, stage3, and mobile retry regression; outputs outside checkout."""
from pathlib import Path
import os,json,sys
sys.path.insert(0,str(Path(__file__).parent))
# Helpers are kept local: importing the executable regression runner would rerun QA.
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];O=Path(os.environ['QA_OUT']);O.mkdir(parents=True,exist_ok=True);URL=os.environ.get('QA_URL','http://127.0.0.1:8859/index.html');S=json.loads((R/'tests/fixtures/issue54-stage2.json').read_text());rows=[];errs=[];logs=[]
def ck(n,ok,d=None):
 rows.append({'name':n,'status':'PASS' if ok else 'FAIL','detail':d});(O/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));print(n,rows[-1]['status'],flush=True);assert ok,n
def new(b,mobile=False):
 c=b.new_context(viewport={'width':390 if mobile else 1280,'height':844 if mobile else 720},has_touch=mobile,is_mobile=mobile);p=c.new_page();p.on('pageerror',lambda e:errs.append(str(e)));p.on('console',lambda m:m.type=='error' and logs.append(m.text));p.goto(URL);p.wait_for_function("LoadCoordinator.phase==='READY'");p.evaluate('TrainingCheckpoint.ready');p.keyboard.press('Enter');return c,p
def menu(p):p.locator('#menuOpen').click();p.locator('[data-stab="save"]').click()
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium')
 for battle in ['normal','raider']:
  c,p=new(b);p.evaluate("b=>{if(b==='normal'){storyStage=6;startAttackBattle('attackGob2',100)}else{storyStage=12;startRaiderBattle()}}",battle);p.wait_for_function('!BattlePresentation.busy')
  for _ in range(2):
   p.wait_for_function('!BattlePresentation.busy&&!BattleTargetSelector.active');p.evaluate("b=>b==='normal'?chooseNormalAct('guard'):choosePartyAct('guard')",battle)
  p.wait_for_function("b=>b==='normal'?!attackBattleBusy&&PrologueCombat.roundNumber>=2:!rbBusy&&rbRound>=2",arg=battle,timeout=45000)
  ck(battle+'_complete_round',p.evaluate("b=>b==='normal'?aahp>0&&normalFHP>0:rbHP>0&&rbFHP>0",battle));p.screenshot(path=str(O/(battle+'-round.png')));c.close()
 # Stage3 fixture derives only the already-saved stage flag, not a claim of normal reach.
 c,p=new(b);d=json.loads(json.dumps(S));d['prologue']['storyStage']=3;d['prologue']['currentObjective']='フィオナと風見の断崖へ向かおう';p.evaluate('(d)=>localStorage.setItem(SAVE_KEY,JSON.stringify(d))',d);menu(p);p.locator('#doLoad').click();p.wait_for_function("LoadCoordinator.phase==='READY'");p.locator('#systemClose').click();menu(p);p.locator('#doSave').click();raw=p.evaluate('localStorage.getItem(SAVE_KEY)');p.locator('#systemClose').click();p.reload();p.wait_for_function("LoadCoordinator.phase==='READY'");p.keyboard.press('Enter');menu(p);p.locator('#doLoad').click();p.wait_for_function("LoadCoordinator.phase==='READY'");ck('stage3_resave_reload',p.evaluate("storyStage===3&&MossForest.active&&MossForest.feet.x===2075&&MossForest.feet.y===875") and raw==p.evaluate('localStorage.getItem(SAVE_KEY)'));c.close()
 c,p=new(b,True);p.evaluate('(d)=>localStorage.setItem(SAVE_KEY,JSON.stringify(d))',S);raw=p.evaluate('localStorage.getItem(SAVE_KEY)');p.route('**/data/maps/rilde_village_01_peace.json',lambda route:route.fulfill(status=200,content_type='application/json',body='{bad'))
 menu(p);p.locator('#doLoad').tap();p.wait_for_function("LoadCoordinator.phase==='FAILED'");ck('mobile_failure_save_protection',p.evaluate("!LoadCoordinator.canSave") and p.locator('#retryLoad').is_visible());p.evaluate('saveGrowthData()');ck('mobile_failure_original_kept',raw==p.evaluate('localStorage.getItem(SAVE_KEY)'));p.unroute('**/data/maps/rilde_village_01_peace.json');p.locator('#retryLoad').tap();p.wait_for_function("LoadCoordinator.phase==='READY'");ck('mobile_explicit_retry_touch',p.evaluate("storyStage===1&&MossForest.active&&MossForest.feet.x===2075&&MossForest.feet.y===875"));p.screenshot(path=str(O/'mobile-retry.png'));c.close()
 ck('no_errors',not errs and not logs,{'pageerrors':errs,'console_errors':logs});b.close()

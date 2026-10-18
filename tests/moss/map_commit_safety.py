"""Phase 1.1 real browser fault injection; no fixtures/assertions in old tests changed."""
import os,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
OUT=Path(os.environ.get('OUT','/tmp/map-commit-safety'));OUT.mkdir(parents=True,exist_ok=True)
A='moss_forest_01_sunlit_path';B='moss_forest_02_mossy_ravine';fails=[];rows=[]
def check(v,label):
 print(('PASS ' if v else 'FAIL ')+label,flush=True);rows.append({'label':label,'pass':bool(v)})
 if not v:fails.append(label)
def state(pg):return pg.evaluate('''()=>({active:MossForest.active,busy:MossForest.busy,feet:MossForest.feet,map:MossForest.mapId,unsafe:MossForest.unsafeCommit,canSave:MossForest.canSave,request:MossForest.mapRequest})''')
def enter(pg,m):return pg.evaluate('m=>MossForest.enter({map:m}).then(x=>!!x)',m)
def save_blocked(pg,label):
 pg.evaluate('''()=>{renderSystemTab('save');window.beforeSave=localStorage.getItem(SAVE_KEY);window.savedWrites=0;window.originalSet=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k===SAVE_KEY)savedWrites++;return originalSet.call(this,k,v)};saveGrowthData()}''')
 check(pg.evaluate('savedWrites===0&&localStorage.getItem(SAVE_KEY)===beforeSave'),label)
 pg.evaluate('()=>{Storage.prototype.setItem=originalSet}')
with server(8894) as base,sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 def run(name,fn):
  ctx=browser.new_context(viewport={'width':390,'height':844},has_touch=True);pg=ctx.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)))
  if os.environ.get('NEGATIVE_CONTROL'):
   pg.route('**/js/field/moss-forest-runtime.js*',lambda r:r.fulfill(path=str(ROOT.parent/'before-phase11/runtime.js'),content_type='application/javascript'))
   pg.route('**/index.html',lambda r:r.fulfill(path=str(ROOT.parent/'before-phase11/index.html'),content_type='text/html'))
  try:
   pg.goto(base+'/index.html');pg.wait_for_function('window.MossForest?.active&&window.BattleMotion?.loaded',timeout=30000);pg.evaluate('closeDialogue()');fn(pg);check(not errors,name+' no uncaught exceptions')
  except Exception as e:check(False,name+' exception '+str(e))
  finally:ctx.close()
 def fail(pg,kind):
  if kind=='corrupt':
   def corrupt(r):
    data=r.fetch().json();data['props']=None;r.fulfill(json=data)
   pg.route('**/data/maps/'+A+'.json',corrupt)
  else:
   pg.evaluate('''kind=>{window.baseLoader=ForestLoader;window.baseVillage=RildeVillage;if(kind==='mount')window.ForestLoader={...baseLoader,mount(){throw Error('controlled-commit-fault')}};else window.RildeVillage={...baseVillage,onEnter(){throw Error('controlled-aftercommit-fault')}}}''',kind)
  check(not enter(pg,A),kind+' enter reports failure')
 def blocked(pg,label):
  s=state(pg);check(not s['active'] and s['busy'],label+' inactive and busy');save_blocked(pg,label+' refuses persistence')
 def scenario(pg,kind):
  fail(pg,kind);blocked(pg,kind+' initial');old=state(pg)['feet'];pg.evaluate('MossForest.lock(false)');blocked(pg,kind+' unlock');pg.evaluate('MossForest.hide();MossForest.resume()');blocked(pg,kind+' hide/resume')
  pg.keyboard.down('ArrowRight');pg.wait_for_timeout(180);pg.keyboard.up('ArrowRight');check(state(pg)['feet']==old,kind+' keyboard cannot move')
  pg.evaluate('MossForest.teleportFeet(500,500);MossForest.actor("aidan").set(600,600);MossForest.goFeet(700,700)');check(state(pg)['feet']==old,kind+' direct movement blocked')
  pg.evaluate('MossForest.reset();MossForest.lock(false);MossForest.resume()');blocked(pg,kind+' reset alone not recovery')
  pg.unroute_all();pg.evaluate('if(window.baseLoader)window.ForestLoader=baseLoader;if(window.baseVillage)window.RildeVillage=baseVillage')
  check(enter(pg,B),kind+' valid enter recovers');s=state(pg);check(s['active'] and not s['busy'] and s['canSave'],kind+' recovery input and save available')
  pg.evaluate('renderSystemTab("save");saveGrowthData()');check(pg.evaluate('JSON.parse(localStorage.getItem(SAVE_KEY)).prologue.moss.map')==B,kind+' save contains committed destination')
  pg.evaluate('MossForest.lock(true);MossForest.lock(false);MossForest.hide();MossForest.resume()');check(pg.evaluate('MossForest.active&&!MossForest.busy'),kind+' normal unlock/resume preserved')
 for k in ['corrupt','mount','after']:run(k,lambda pg,k=k:scenario(pg,k))
 def stale(pg):
  held=[];pg.route('**/data/maps/'+A+'.json',lambda r:held.append(r));pg.evaluate('()=>{window.oldRequest=MossForest.enter({map:"'+A+'"})}');pg.wait_for_function('MossForest.mapRequest.phase==="loading"');pg.wait_for_timeout(100);check(bool(held),'stale request captured');check(enter(pg,B),'successor ready');s=state(pg);held[0].fulfill(status=503,body='old failure');pg.evaluate('oldRequest');check(state(pg)==s,'stale failure cannot latch or unlock successor')
 run('stale HTTP503',stale)
 def cancelled_commit(pg):
  pg.evaluate("window.originalVillage=RildeVillage;window.RildeVillage={...originalVillage,onEnter(){MossForest.hide()}}")
  check(not enter(pg,A),'onEnter cancellation returns null');pg.evaluate('MossForest.lock(false);MossForest.resume()');blocked(pg,'cancelled completed commit')
  pg.evaluate('window.RildeVillage=originalVillage');check(enter(pg,B),'cancelled commit recovers on new enter')
 run('commit cancellation',cancelled_commit)
 def retry503(pg):
  fail(pg,'mount');pg.evaluate('window.ForestLoader=baseLoader');pg.route('**/data/maps/'+B+'.json',lambda r:r.fulfill(status=503,body='retry failure'))
  check(not enter(pg,B),'failed retry HTTP503 reports null');pg.evaluate('MossForest.lock(false);MossForest.resume()');blocked(pg,'failed retry retains original latch')
 run('failed recovery',retry503)
 def normal_hook(pg):
  pg.evaluate("window.originalVillage=RildeVillage;window.RildeVillage={...originalVillage,onEnter(){MossForest.actor('fiona').set(333,444);window.hookFeet=MossForest.actor('fiona').get()}}")
  check(enter(pg,A),'normal onEnter accepted');check(pg.evaluate('hookFeet.x===333&&hookFeet.y===444'),'normal synchronous onEnter actor placement preserved')
 run('normal placement hook',normal_hook)
 browser.close()
(OUT/'results.json').write_text(json.dumps({'rows':rows,'fails':fails},ensure_ascii=False,indent=2));print('FAILS',len(fails));sys.exit(bool(fails))

"""P1-B: real browser map requests with controlled completion/fault injection.
No balance, save schema, or existing assertions are modified. OUTPUT stays outside checkout.
"""
import sys,os,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
OUT=Path(os.environ.get('OUT','/tmp/map-request-generation'));OUT.mkdir(parents=True,exist_ok=True)
A='moss_forest_01_sunlit_path';B='moss_forest_02_mossy_ravine';C='moss_forest_03_ancient_grove'
rows=[];fails=[]
def check(v,label):
 print(('PASS ' if v else 'FAIL ')+label,flush=True)
 if not v:fails.append(label)
def snapshot(pg):return pg.evaluate('''()=>({request:MossForest.mapRequest,map:MossForest.snapshot(),feet:MossForest.feet,flags:MossForest.flags,active:MossForest.active,busy:MossForest.busy,width:document.querySelector('#forestWorld').style.width,display:document.querySelector('#forestScene').style.display,notice:document.querySelector('#forestToast').textContent})''')
def begin(pg,name,mapid,flags=None):pg.evaluate('''([name,map,flags])=>{window[name]=MossForest.enter({map,flags}).then(x=>({map:x?.id||null}));}''',[name,mapid,flags])
def gate(pg):pg.evaluate('''()=>{window.gates=[];const base=ForestLoader;window.ForestLoader={...base,prepare:async(map,at,opt)=>{await new Promise(resolve=>gates.push({map:map.id,resolve}));return base.prepare(map,at,opt)}}}''')
def wait_gate(pg,n):pg.wait_for_function('(n)=>gates.length>=n',arg=n)
def release(pg,i):pg.evaluate('(i)=>gates[i].resolve()',i)
def ready(pg,mapid):pg.wait_for_function('(m)=>MossForest.mapId===m&&MossForest.active&&!MossForest.busy&&MossForest.mapRequest?.phase==="ready"',arg=mapid,timeout=20000)
with server(8893) as base,sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_BIN','/usr/bin/chromium'),args=['--no-sandbox'])
 def run(name,fn):
  ctx=browser.new_context(viewport={'width':390,'height':844},has_touch=True);pg=ctx.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)))
  try:
   pg.goto(base+'/index.html');pg.wait_for_function('window.MossForest?.active&&window.BattleMotion?.loaded',timeout=30000);pg.wait_for_timeout(500);pg.evaluate('closeDialogue()');before=snapshot(pg);fn(pg,before);check(not errors,name+' no page errors '+str(errors));rows.append({'case':name,'state':snapshot(pg),'errors':errors})
  except Exception as e:check(False,name+' exception '+str(e));rows.append({'case':name,'exception':str(e),'errors':errors})
  finally:ctx.close();(OUT/'results.json').write_text(json.dumps({'rows':rows,'fails':fails},ensure_ascii=False,indent=2))
 def single(pg,old):
  begin(pg,'a',A);ready(pg,A);s=snapshot(pg);sp=pg.evaluate('MossForest.map.spawns.points[MossForest.map.spawns.default]');check(s['feet']=={'x':sp['x'],'y':sp['y']} and s['request']['commitStarted'] and s['request']['commitComplete'],'single map/feet/render/request commit agree');check(s['width']==pg.evaluate('MossForest.map.world.width+"px"'),'single field drawing dimensions match')
 run('single',single)
 def reverse(pg,old,count=3):
  gate(pg)
  for i,m in enumerate([A,B,C][:count]):begin(pg,'p'+str(i),m,{'lc03_stale':i<count-1});wait_gate(pg,i+1)
  release(pg,count-1);ready(pg,[A,B,C][count-1]);valid=snapshot(pg)
  for i in range(count-1):release(pg,i);check(pg.evaluate('n=>window["p"+n]',i)['map'] is None,'obsolete '+str(i)+' returns null')
  check(snapshot(pg)==valid,'reverse '+str(count)+' stale completions leave all current state unchanged')
 run('A-B reverse',lambda pg,s:reverse(pg,s,2));run('A-B-C reverse',reverse)
 def stale503(pg,old):
  held=[];pg.route('**/data/maps/'+A+'.json',lambda r:held.append(r));begin(pg,'a',A)
  until=time.monotonic()+10
  while not held and time.monotonic()<until:pg.wait_for_timeout(20)
  assert held,'request not observed';begin(pg,'b',B);ready(pg,B);valid=snapshot(pg);held[0].fulfill(status=503,body='controlled stale failure');check(pg.evaluate('a')['map'] is None,'old HTTP503 is cancelled');check(snapshot(pg)==valid,'old HTTP503 cannot change notice or input owner')
 run('stale HTTP503',stale503)
 def active503(pg,old):
  pg.route('**/data/maps/'+A+'.json',lambda r:r.fulfill(status=503,body='controlled current failure'));begin(pg,'a',A);check(pg.evaluate('a')['map'] is None,'current HTTP503 reports failure');s=snapshot(pg);check(s['map']==old['map'] and s['active']==old['active'] and s['busy']==old['busy'],'HTTP503 restores exact last valid map/coordinates/control');check('失敗' in s['notice'] and s['request']['phase']=='failed' and not s['request']['commitStarted'],'HTTP503 existing notice/precommit boundary');pg.unroute_all();begin(pg,'retry',A);ready(pg,A);check(pg.evaluate('retry')['map']==A,'current failure retry succeeds with new request')
 run('current HTTP503 retry',active503)
 def beforecommit(pg,old):
  pg.evaluate('const original=ForestLoader;window.ForestLoader={...original,prepare:async()=>{throw Error("precommit-fault")}}');begin(pg,'a',A);pg.evaluate('a');s=snapshot(pg);check(s['map']==old['map'] and s['active'] and not s['busy'] and not s['request']['commitStarted'],'prepare exception restores previous field after fade-out');check(pg.evaluate('document.querySelector("#forestFade").style.opacity')=='0','prepare exception restores prior fade')
 run('before commit exception',beforecommit)
 def midcommit(pg,old):
  pg.evaluate('const original=ForestLoader;window.ForestLoader={...original,mount:()=>{throw Error("commit-fault")}}');begin(pg,'a',A);pg.evaluate('a');s=snapshot(pg);check(s['request']['commitStarted'] and not s['request']['commitComplete'] and not s['active'] and s['busy'],'mid commit exception fails closed without rollback');check(s['map']['map']==A and '停止' in s['notice'],'partial map not guessed back; explicit existing error UI');check(pg.evaluate('''()=>{const e=document.querySelector('#forestToast'),r=e.getBoundingClientRect();return document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)===e}'''),'error toast visible above fade cover')
 run('mid commit exception',midcommit)
 def aftercommit(pg,old):
  pg.evaluate('const original=RildeVillage;window.RildeVillage={...original,onEnter:()=>{throw Error("onEnter-fault")}}');begin(pg,'a',A);pg.evaluate('a');s=snapshot(pg);check(s['request']['commitStarted'] and s['request']['commitComplete'] and s['request']['phase']=='failed' and not s['active'] and s['busy'],'post commit notification exception keeps field stopped')
 run('after commit exception',aftercommit)
 def owner(pg,old):
  gate(pg);begin(pg,'a',A);wait_gate(pg,1);pg.evaluate('MossForest.lock(true)');state=snapshot(pg);release(pg,0);pg.evaluate('a');check(snapshot(pg)==state and state['busy'],'old request cannot release external lock');pg.evaluate('MossForest.lock(false)');check(pg.evaluate('!MossForest.busy'),'lock owner can release itself')
 run('external ownership',owner)
 def same(pg,old):
  gate(pg);begin(pg,'a',old['map']['map']);wait_gate(pg,1);first=pg.evaluate('MossForest.mapRequest.id');begin(pg,'b',old['map']['map']);wait_gate(pg,2);second=pg.evaluate('MossForest.mapRequest.id');release(pg,1);ready(pg,old['map']['map']);valid=snapshot(pg);release(pg,0);pg.evaluate('a');check(first!=second and snapshot(pg)==valid,'same map still uses distinct request IDs')
 run('same map',same)
 def decode(pg,old):
  attempts={};chosen=[]
  def asset(route):
   u=route.request.url
   if '/img/field/moss/' not in u:route.continue_();return
   if not chosen:chosen.append(u)
   if u==chosen[0]:
    attempts[u]=attempts.get(u,0)+1
    if attempts[u]==1:route.fulfill(status=503,body='image failure');return
   route.continue_()
  pg.route('**/*.png',asset);begin(pg,'a',B);ready(pg,B);pg.wait_for_function('ForestLoader.art.images.size>0');until=time.monotonic()+8
  while (not chosen or attempts.get(chosen[0],0)<2) and time.monotonic()<until:pg.wait_for_timeout(50)
  check(bool(chosen) and attempts[chosen[0]]>=2,'real image HTTP503 receives existing decode retry');check(pg.evaluate('MossForest.mapRequest.phase==="ready"'),'image retry preserves valid request completion');before=attempts.get(chosen[0],0) if chosen else 0;pg.evaluate('ForestLoader.prepare(MossForest.map,MossForest.feet)');check(bool(chosen) and attempts[chosen[0]]==before,'successful decoded image cache reused')
 run('decode retry',decode)
 def dev(pg,old):
  gate(pg);begin(pg,'a',A);wait_gate(pg,1);pg.evaluate('devJump("map:dev_monster_arena")');wait_gate(pg,2);release(pg,1);ready(pg,'dev_monster_arena');valid=snapshot(pg);release(pg,0);pg.evaluate('a');check(snapshot(pg)==valid,'DEV map jump supersedes pending map')
 run('DEV map',dev)
 def event(pg,old):
  pg.evaluate('FieldScene.hook("lc03-test",()=>enterWorldMap("'+B+'"));window.eventMap=FieldScene.play({steps:[{call:"lc03-test"}]});void 0');ready(pg,B);check(pg.evaluate('eventMap') is True,'existing event hook map transition completes')
 run('event map',event)
 def battle(pg,old):
  gate(pg);begin(pg,'a',A);wait_gate(pg,1);pg.evaluate('startAttackBattle("fieldGob1",100)');release(pg,0);pg.evaluate('a');check(pg.evaluate('document.body.classList.contains("battleMode")&&MossForest.mapId==="'+old['map']['map']+'"'),'pending map cannot replace normal battle');pg.wait_for_function('!BattlePresentation.busy&&!attackBattleBusy');pg.evaluate('PrologueCombat.instantKill("normal")');pg.wait_for_function('document.body.classList.contains("battleResultMode")',timeout=15000);pg.locator('#resultContinue').click();check(pg.evaluate('MossForest.active&&!MossForest.busy') and pg.evaluate('MossForest.mapId')==old['map']['map'],'native RESULT resumes original field with no inherited map lock')
 run('battle resume',battle)
 def load(pg,old):
  gate(pg);begin(pg,'a',A);wait_gate(pg,1)
  pg.evaluate('''(m)=>{const d=PrologueProgress.serialize();d.storyStage=9;d.version=2;d.moss={map:m,x:100,y:100,opened:[],fired:[]};localStorage.setItem(SAVE_KEY,JSON.stringify({version:30,prologue:d}));loadGrowthData()}''',C);wait_gate(pg,2);release(pg,1);ready(pg,C);valid=snapshot(pg);release(pg,0);pg.evaluate('a');check(snapshot(pg)==valid and pg.evaluate('storyStage')==9,'LOAD owns final map; old request cannot overwrite loaded state')
 run('LOAD request',load)
 def boss(pg,old):
  gate(pg);begin(pg,'a',A);wait_gate(pg,1);pg.evaluate('forestHideScene();startRaiderBattle()');release(pg,0);pg.evaluate('a');check(pg.evaluate('document.body.classList.contains("raiderBattleMode")'),'pending map cannot replace boss');pg.wait_for_function('!BattlePresentation.busy&&!rbBusy');pg.evaluate('PrologueCombat.instantKill("raider")');pg.wait_for_function('document.body.classList.contains("battleResultMode")',timeout=15000);pg.locator('#resultContinue').click();check(pg.is_visible('#aftermathScene'),'native boss result keeps aftermath flow')
 run('boss result',boss)
 def reenter(pg,old):
  pg.evaluate('const original=FieldWeather;window.FieldWeather={...original,configureMap(map){if(map.id==="'+A+'")window.next=enterWorldMap("'+B+'");return original.configureMap(map)}}');begin(pg,'a',A);ready(pg,B);check(pg.evaluate('a')['map'] is None,'synchronous map reentry cancels old commit continuation');check(pg.evaluate('next')['id']==B and pg.evaluate('MossForest.mapRequest.map')==B,'reentrant successor retains request and control')
 run('commit reentry',reenter)
 def sceneexit(pg,old):
  gate(pg);begin(pg,'a',A);wait_gate(pg,1);pg.evaluate('startFortFinale()');release(pg,0);pg.evaluate('a');check(pg.is_visible('#fortScene') and pg.is_hidden('#forestScene'),'pending map cannot re-show field over final scene')
 run('scene exit',sceneexit)
 def release_owner(pg,old):
  gate(pg);begin(pg,'a',A);wait_gate(pg,1);pending=snapshot(pg);pg.evaluate('MossForest.lock(false)');check(snapshot(pg)==pending,'unowned legacy unlock cannot cancel/release current map request');release(pg,0);ready(pg,A);check(pg.evaluate('a')['map']==A,'current map succeeds after stale unlock attempt')
 run('stale unlock',release_owner)
 def stream(pg,old):
  pg.evaluate('const original=ForestLoader;window.ForestLoader={...original,prepare(map,at,opt){if(map.id==="'+A+'")window.streamValid=opt.isCurrent;return original.prepare(map,at,opt)}}');begin(pg,'a',A);ready(pg,A);check(pg.evaluate('streamValid()&&!MossForest.mapRequest.ownsInput'),'background image preparation remains valid after input ownership released');begin(pg,'b',B);check(pg.evaluate('!streamValid()'),'superseded image stream loses validity');ready(pg,B)
 run('background cache ownership',stream)
 def knownload(pg,old):
  pg.locator('#menuOpen').click();pg.locator('[data-stab="save"]').click();pg.locator('#doSave').click();pg.locator('#doLoad').click();pg.locator('#systemClose').click();check(pg.evaluate('!MossForest.active&&document.querySelector("#inside").style.display==="block"'),'known new-village LOAD-P1 retained, not claimed fixed')
 run('known LOAD-P1',knownload)
 browser.close()
print('FAILS',len(fails));sys.exit(bool(fails))

"""AA: real walking with opt-in overlay; report unadopted entity-level gate separately."""
import json,os,sys
from pathlib import Path
from playwright.sync_api import sync_playwright,TimeoutError as PWTimeout
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.qa.browser_support import server
fails=[];errors=[];observed=[]
def ck(c,m):
 print(('ok   ' if c else 'FAIL ')+m,flush=True)
 if not c:fails.append(m)
with server(8796) as base, sync_playwright() as p:
 b=p.chromium.launch(executable_path=os.environ.get('PW_CHROMIUM_EXECUTABLE') or None)
 for proposal in (False,True):
  pg=b.new_page(viewport={'width':844,'height':390});pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
  # Other maps have no overlay: suppress only optional, unrelated overlay probes.
  def specs(r):
   if r.request.url.endswith('/cliff_moher_01_spiral_ascent.json'):r.continue_()
   else:r.fulfill(status=200,content_type='application/json',body='null')
  pg.route('**/data/height-specs/*.json',specs)
  if proposal:
   m=json.loads((ROOT/'data/maps/cliff_moher_01_spiral_ascent.json').read_text())
   for z in m['eventZones']:
    if z['id'] in ('ev_c1_summit','ev_c1_view_bench'):z['level']=2
   pg.route('**/data/maps/cliff_moher_01_spiral_ascent.json',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(m)))
  pg.goto(base+'/index.html?dev=1&legacyVillage=1&feature=heightSpecs');pg.wait_for_timeout(1600)
  pg.evaluate('PrologueProgress.seed(0);Quest.reset();Inventory.reset();MossForest.reset();storyStage=15;closeDialogue();enterMossForest()');pg.wait_for_timeout(2200)
  pg.evaluate('storyStage=3;closeDialogue();MossForestStory.enterCliff()');pg.wait_for_function("MossForest.mapId==='cliff_moher_01_spiral_ascent' && !!MossForest.height",timeout=15000);pg.wait_for_timeout(1000)
  tag='proposal fixture' if proposal else 'on-disk overlay'
  ck(pg.evaluate('MossForest.level')==0,tag+' starts on ground')
  m=pg.evaluate('MossForest.map');pts=next(x['points'] for x in m['terrain']['paths'] if x['id']=='path_spiral')[1:]
  pts+=next(x['points'] for x in m['terrain']['paths'] if x['id']=='path_summit_walk')[1:]
  # Never target connector midpoints: tapping there chooses a floor unlike its entry zone.
  pts=[q for q in pts if not(2290<=q[0]<=2500 and 4443<=q[1]<=4623) and not(2238<=q[0]<=2419 and 2260<=q[1]<=2460)]
  walked=True;levels=[]
  for x,y in pts:
   if not pg.evaluate('([x,y])=>MossForest.goFeet(x,y)',[x,y]):walked=False;break
   try:pg.wait_for_function('([x,y])=>Math.hypot(MossForest.feet.x-x,MossForest.feet.y-y)<18',arg=[x,y],timeout=18000)
   except PWTimeout:
    print('WARN stopped '+str(pg.evaluate('({feet:MossForest.feet,level:MossForest.level})')),flush=True);walked=False;break
   levels.append(pg.evaluate('MossForest.level'))
  ck(walked and set(levels)>={0,1,2},tag+' walks existing spiral 0→1→2 without teleport')
  pg.screenshot(path='/tmp/m27-'+('proposal' if proposal else 'overlay')+'.png')
  pt=pg.evaluate("()=>{const r=document.querySelector('#forestWorld').getBoundingClientRect(),s=FieldCamera.scale;return [r.left+2400*s,r.top+960*s]}")
  pg.mouse.click(*pt);pg.wait_for_timeout(1200)
  # Dynamic hook has to match entity floor. Existing map leaves it at 0.
  talk=pg.evaluate('FieldTalk.active');ck(bool(talk),tag+' bench interaction opens story gate')
  if talk:
   for _ in range(8):
    if pg.locator('.talkChoices button').count():break
    pg.locator('#msg').click();pg.wait_for_timeout(200)
   if pg.locator('.talkChoices button').count():pg.locator('.talkChoices button').first.click()
   for _ in range(200):
    if not pg.evaluate('FieldScene.running'):break
    if pg.evaluate('FieldTalk.active'):pg.locator('#msg').click()
    pg.wait_for_timeout(150)
   ck(pg.evaluate('storyStage') in (4,5) and not pg.evaluate('forestActive'),tag+' sunset→attack sequence completes')
  observed.append({'proposal_fixture':proposal,'walked':walked,'levels':levels,'bench_talk':talk,'stage':pg.evaluate('storyStage')})
  pg.close()
 b.close()
ck(not errors,'no page errors '+str(errors[:3]))
print('OBSERVED '+json.dumps(observed));print('FAILS',len(fails));sys.exit(bool(fails))

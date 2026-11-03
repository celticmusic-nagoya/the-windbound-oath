"""Preview-only stride controls: real UI, image cadence and protected game state."""
import json, os, sys, statistics
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/qa'))
from browser_support import server
OUT=Path(os.getenv('QA_OUT','/tmp/dev-walk-stride'));OUT.mkdir(parents=True,exist_ok=True)
rows=[];errors=[];cadences=[]
def ck(name,ok):
 rows.append({'name':name,'pass':bool(ok)});(OUT/'stride-results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));print(('PASS ' if ok else 'FAIL ')+name,flush=True);assert ok,name
STATE="JSON.stringify({stage:storyStage,flags:PrologueProgress.eventSnapshot(),talk:FieldTalk.serialize(),inventory:Inventory.serialize(),party:PartyManager.members,stock:battleItems,gold,storage:{...localStorage},feet:MossForest.feet,map:MossForest.mapId,movement:FieldMovement.settings})"
SNAP='DevWalkTest.snapshot()'
def boot(p,url):
 p.on('pageerror',lambda e:errors.append(str(e)));p.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);p.on('response',lambda r:errors.append(f'HTTP{r.status} {r.url}') if r.status>=400 else None)
 p.goto(url);p.get_by_role('button',name='NEW GAME',exact=True).click();p.wait_for_function("LoadCoordinator.phase==='READY'&&MossForest.active&&document.body.classList.contains('dialogueOpen')")
 for _ in range(40):
  if p.evaluate("InputManager.state()!=='DIALOGUE'"):break
  p.keyboard.press('Enter');p.wait_for_timeout(80)
 p.wait_for_function("!MossForest.busy&&!LoadingInput.busy&&!document.body.classList.contains('dialogueOpen')")
def open_ui(p):
 p.locator('#devBtn').click();p.locator('#devWalkMotionTest').tap();p.wait_for_function('DevWalkTest.active&&DevWalkTest.snapshot().ready')
 return lambda s:p.locator('#walkMotionTest '+s)
def ready(p):p.wait_for_function('DevWalkTest.snapshot().ready')
with server(8828) as base,sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE') or '/usr/bin/chromium')
 for label,w,h in [('pc',1920,1080),('portrait',390,844),('landscape',844,390)]:
  ctx=b.new_context(viewport={'width':w,'height':h},has_touch=True);p=ctx.new_page();boot(p,base+'/index.html?title=1');before=p.evaluate(STATE);q=open_ui(p);slider=q('[data-walk=stride]')
  ck(label+' initial72 and bounds40/300',p.evaluate(SNAP)['sideStride']==72 and slider.input_value()=='72' and slider.get_attribute('min')=='40' and slider.get_attribute('max')=='300')
  ck(label+' exact four presets',q('[data-stride]').evaluate_all('(xs)=>xs.map(x=>Number(x.dataset.stride))')==[72,120,180,240])
  q('[data-direction=left]').tap();ready(p)
  # Paused phase/image preservation and exact ten-unit keyboard increments.
  q('[data-walk=next]').tap();q('[data-walk=next]').tap();src=q('img').get_attribute('src');slider.press('Home')
  for value in range(40,301,10):
   s=p.evaluate(SNAP);ck(f'{label} range {value}',s['sideStride']==value and s['effectiveStride']==value and slider.input_value()==str(value) and s['index']==2 and q('img').get_attribute('src')==src)
   if value<300:slider.press('ArrowRight')
  slider.press('ArrowRight');ck(label+' upper clamp',p.evaluate(SNAP)['sideStride']==300);slider.press('Home');slider.press('ArrowLeft');ck(label+' lower clamp',p.evaluate(SNAP)['sideStride']==40)
  slider.tap();s=p.evaluate(SNAP);ck(label+' native touch range snaps10',s['sideStride']==170 and s['effectiveStride']==170)
  q('[data-stride="72"]').tap();slider.press('ArrowRight');ck(label+' off-grid72 keyboard goes80',p.evaluate(SNAP)['sideStride']==80);q('[data-stride="72"]').tap();slider.press('ArrowLeft');ck(label+' off-grid72 keyboard goes70',p.evaluate(SNAP)['sideStride']==70)
  for stride in [72,120,180,240]:
   for rate in [.5,1,2]:
    q(f'[data-stride="{stride}"]').tap();q('[data-walk=speed]').select_option(str(rate));s=p.evaluate(SNAP)
    seconds=stride/300/rate
    ck(f'{label} preset{stride} rate{rate} independent',s['sideStride']==stride and s['speed']==rate and q('[data-walk=stride-value]').inner_text()==str(stride) and f'{seconds:.3f}' in q('[data-walk=stride-help]').inner_text() and q(f'[data-stride="{stride}"]').get_attribute('aria-pressed')=='true')
  # Running edits must keep one RAF alive; the next frame uses the new bank period.
  q('[data-walk=speed]').select_option('1');q('[data-walk=play]').tap();p.wait_for_timeout(110)
  for stride in [120,180,240,72]:
   q(f'[data-stride="{stride}"]').tap();s=p.evaluate(SNAP);ck(f'{label} live stride{stride} never pauses',s['playing'] and s['timer'] and s['effectiveStride']==stride)
  q('[data-walk=pause]').tap();s=p.evaluate(SNAP);q('[data-stride="240"]').tap();after=p.evaluate(SNAP)
  ck(label+' paused fractional-cycle preserved',after['index']==s['index'] and abs(after['time']/240-s['time']/s['effectiveStride'])<1e-9)
  # Actual DOM image transitions, independent of the timer/status values.
  if label=='pc':
   for stride,rate in [(120,.5),(240,1),(120,1),(120,2)]:
    q(f'[data-stride="{stride}"]').tap();q('[data-walk=speed]').select_option(str(rate));q('[data-walk=play]').tap()
    data=p.evaluate("""()=>new Promise(resolve=>{const out=[],start=performance.now();let prev;function tick(now){const img=document.querySelector('#walkMotionTest img'),src=img.currentSrc;if(src!==prev){out.push({t:now,src,loaded:img.complete&&img.naturalWidth>0});prev=src}if(now-start<2700)requestAnimationFrame(tick);else resolve(out)}requestAnimationFrame(tick)})""")
    q('[data-walk=pause]').tap();indices=[int(x['src'].split('_')[-1].split('.')[0]) for x in data];wraps=[data[i]['t'] for i in range(1,len(data)) if indices[i]<indices[i-1]];periods=[(c-a)/1000 for a,c in zip(wraps,wraps[1:])];period=statistics.median(periods) if periods else 0;expected=stride/300/rate
    cadences.append({'stride':stride,'rate':rate,'expected_seconds':expected,'observed_median_seconds':period,'frames':data});ck(f'actual PNG cadence {stride}/{rate}',len(periods)>=2 and abs(period-expected)<max(.07,expected*.22) and len(set(indices))>=4 and all(x['loaded'] for x in data))
   (OUT/'stride-cadences.json').write_text(json.dumps(cadences,indent=2))
  q('[data-stride="240"]').tap()
  for direction in ['right','down','up','left']:
   q('[data-direction='+direction+']').tap();ready(p);s=p.evaluate(SNAP);ck(label+' direction '+direction+' retains side-only setting',s['sideStride']==240 and s['effectiveStride']==(240 if direction in ['left','right'] else 90))
  q('[data-walk=idle]').tap();ready(p);ck(label+' idle unchanged',p.evaluate(SNAP)['total']==1 and q('[data-walk=play]').is_disabled())
  q('[data-direction=left]').tap();ready(p);q('[data-walk=actor]').select_option('fiona');ready(p);ck(label+' Fiona unaffected/controls hidden',q('[data-walk=stride-controls]').is_hidden() and p.evaluate(SNAP)['effectiveStride']==90)
  q('[data-walk=group]').select_option('enemy');q('[data-walk=actor]').select_option('goblin');ready(p);ck(label+' goblin unaffected',q('[data-walk=stride-controls]').is_hidden() and p.evaluate(SNAP)['effectiveStride']==48)
  q('[data-walk=group]').select_option('ally');q('[data-walk=actor]').select_option('aidan');ready(p);ck(label+' actor switch retains240',p.evaluate(SNAP)['effectiveStride']==240)
  ck(label+' production stride unchanged',p.evaluate("MossForest.walkStride('aidan','left')===72&&FieldWalkMotion.resolve('ally','aidan','left').stride===72&&MossForest.walkStride('fiona','left')===90"))
  slider.scroll_into_view_if_needed();p.screenshot(path=str(OUT/f'stride-{label}.png'));box=slider.bounding_box();ck(label+' range inside viewport',box['x']>=0 and box['x']+box['width']<=w and box['y']>=0 and box['y']+box['height']<=h)
  p.set_viewport_size({'width':h,'height':w});p.wait_for_timeout(100);ck(label+' rotation retains240',p.evaluate(SNAP)['sideStride']==240)
  q('[data-walk=close]').tap();ck(label+' game/SAVE/settings unchanged',p.evaluate(STATE)==before);ck(label+' no residual timer',not p.evaluate(SNAP)['timer']);q=open_ui(p);ck(label+' temporary memory-only setting retained on reopen',p.evaluate(SNAP)['sideStride']==240);q('[data-walk=close]').tap();ctx.close()
 # Existing URL value seeds the preview; UI edits never write it back to runtime/URL/SAVE.
 for seed in [60,180,20]:
  ctx=b.new_context(viewport={'width':1280,'height':720});p=ctx.new_page();url=base+f'/index.html?title=1&dev=1&aidanSideStride={seed}';boot(p,url);q=open_ui(p);q('[data-direction=left]').click();ready(p);ck('URL seed '+str(seed),p.evaluate(SNAP)['effectiveStride']==max(40,seed) and p.evaluate("MossForest.walkStride('aidan','left')")==seed)
  q('[data-stride="240"]').click();q('[data-walk=close]').click();ck('URL runtime preserved '+str(seed),p.url==url and p.evaluate("MossForest.walkStride('aidan','left')")==seed)
  p.reload();p.get_by_role('button',name='NEW GAME',exact=True).click();p.wait_for_function("LoadCoordinator.phase==='READY'&&MossForest.active&&document.body.classList.contains('dialogueOpen')");# all state is page-local; inspect anew after intro
  for _ in range(40):
   if p.evaluate("InputManager.state()!=='DIALOGUE'"):break
   p.keyboard.press('Enter');p.wait_for_timeout(80)
  p.wait_for_function("!MossForest.busy&&!LoadingInput.busy&&!document.body.classList.contains('dialogueOpen')");q=open_ui(p);ck('reload removes temporary override '+str(seed),p.evaluate(SNAP)['sideStride']==max(40,seed));ctx.close()
 b.close()
ck('no page/console/HTTP errors',not errors)
print('FAILS 0',flush=True)

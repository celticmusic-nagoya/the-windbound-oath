"""DEV-only official down4 sequence vs baseline6: actual decoded frame cadence, UI isolation."""
import os,sys,json,statistics
from pathlib import Path
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/qa'))
from browser_support import server
sys.path.insert(0,str(R/'tests/helpers'))
from walk_bootstrap_network import expected_retarget
O=Path(os.getenv('QA_OUT','/tmp/down-cycle'));O.mkdir(parents=True,exist_ok=True);checks=[];runs=[];errors=[]
def ck(n,x):
 checks.append({'name':n,'pass':bool(x)});(O/'down-results.json').write_text(json.dumps(checks,indent=2));print(('PASS ' if x else 'FAIL ')+n,flush=True);assert x,n
STATE="JSON.stringify({stage:storyStage,flags:PrologueProgress.eventSnapshot(),inventory:Inventory.serialize(),party:PartyManager.members,gold,storage:{...localStorage},feet:MossForest.feet,map:MossForest.mapId,movement:FieldMovement.settings,frames:AidanFieldAssets.frames})"
def ready(p):p.wait_for_function('DevWalkTest.snapshot().ready')
CAPTURE="""()=>new Promise(resolve=>{const rows=[],start=performance.now();let last;function f(t){const i=document.querySelector('#walkMotionTest img');if(i.complete&&i.naturalWidth===2048&&i.currentSrc!==last){last=i.currentSrc;rows.push({t,src:last,requested:i.getAttribute('src'),index:DevWalkTest.snapshot().index,time:DevWalkTest.snapshot().time,top:i.style.top,transform:i.style.transform})}if(t-start<1300)requestAnimationFrame(f);else resolve(rows)}requestAnimationFrame(f)})"""
with server(8833) as base,sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE') or '/usr/bin/chromium')
 for view,w,h in [('pc',1920,1080),('portrait',390,844),('landscape',844,390)]:
  c=b.new_context(viewport={'width':w,'height':h},has_touch=True,record_video_dir=str(O/'video'),record_video_size=({'width':720,'height':405} if w>h else {'width':360,'height':640}));p=c.new_page();failed=[];phase={'dev':False}
  p.on('pageerror',lambda e:errors.append(str(e)));p.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);p.on('response',lambda r:errors.append(f'HTTP{r.status} {r.url}') if r.status>=400 else None)
  p.on('requestfailed',lambda r,ev=failed,ph=phase:ev.append({'url':r.url,'failure':r.failure,'resource_type':r.resource_type,'before_dev':not ph['dev']}))
  p.goto(base+'/index.html?title=1');p.get_by_role('button',name='NEW GAME',exact=True).click();p.wait_for_function("LoadCoordinator.phase==='READY'&&MossForest.active&&document.body.classList.contains('dialogueOpen')")
  for _ in range(40):
   if p.evaluate("InputManager.state()!=='DIALOGUE'"):break
   p.keyboard.press('Enter');p.wait_for_timeout(80)
  p.wait_for_function("!MossForest.busy&&!LoadingInput.busy&&!document.body.classList.contains('dialogueOpen')")
  if failed:
   repl=p.evaluate("()=>{const i=document.querySelector('#raiderSprite img');return {url:i.currentSrc,loaded:i.complete&&i.naturalWidth>0,registered:BattleMotion.frames('goblin_raider','idle').urls.map(u=>new URL(u,location.href).href)}}")
   for e in failed:ck(view+' known decoded startup replacement',expected_retarget(e,urljoin(base+'/','img/battle/enemies/goblin_raider/goblin_raider_battle_idle.png'),repl))
   failed.clear()
  before=p.evaluate(STATE);phase['dev']=True;p.locator('#devBtn').click();p.locator('#devWalkMotionTest').tap();ready(p);q=lambda s:p.locator('#walkMotionTest '+s)
  ck(view+' default actual six90',p.evaluate("DevWalkTest.snapshot().total===6&&DevWalkTest.snapshot().effectiveStride===90&&DevWalkTest.snapshot().downSequence==='six'"))
  for seq,cycles,expected in [('six',[90],[1,2,3,4,5,6]),('four',[60,75,90],[1,5,2,6])]:
   q('[data-walk=down-sequence]').select_option(seq);ready(p)
   if seq=='four':ck(view+' fair initial four90 comparison',p.evaluate('DevWalkTest.snapshot().effectiveStride===90') and q('[data-walk=down-stride]').input_value()=='90')
   for cycle in cycles:
    if seq=='four':q('[data-walk=down-stride]').select_option(str(cycle));ready(p)
    ck(f'{view}/{seq}/{cycle} 1x exact descriptor',p.evaluate('DevWalkTest.snapshot().effectiveStride')==cycle and p.evaluate('DevWalkTest.snapshot().speed')==1)
    for n in expected:
     p.wait_for_function("n=>{const i=document.querySelector('#walkMotionTest img');return i.complete&&i.naturalWidth===2048&&i.currentSrc.includes('_'+String(n).padStart(2,'0')+'.png')}",arg=n)
     if seq=='four':q('.walkStage').screenshot(path=str(O/f'{view}-four-{cycle}-{n:02}.png'))
     q('[data-walk=next]').tap()
    q('[data-walk=play]').tap();rows=p.evaluate(CAPTURE);q('[data-walk=pause]').tap();ids=[int(r['src'].split('_')[-1].split('.')[0]) for r in rows]
    (O/f'{view}-{seq}-{cycle}-raw.json').write_text(json.dumps(rows,indent=2))
    ck(f'{view}/{seq}/{cycle} actual decoded loop order',len(ids)>len(expected)*2 and all(b==expected[(expected.index(a)+1)%len(expected)] for a,b in zip(ids,ids[1:])))
    times=[r['t'] for r in rows if '_01.png' in r['src']];period=statistics.median((b-a)/1000 for a,b in zip(times,times[1:]));ck(f'{view}/{seq}/{cycle} actual period {period:.4f}',abs(period-cycle/300)<.035)
    runs.append({'view':view,'sequence':seq,'cycle':cycle,'period':period,'rows':rows});(O/'down-cadence.json').write_text(json.dumps(runs,indent=2));ck(view+' paused RAF cancelled',not p.evaluate('DevWalkTest.snapshot().timer'))
  # Explicit frame06 correction in native source pixels, independent of bob toggle.
  q('[data-walk=down-stride]').select_option('75');ready(p)
  for _ in range(3):q('[data-walk=next]').tap()
  ready(p);p.wait_for_function("document.querySelector('#walkMotionTest img').currentSrc.includes('_06.png')")
  a=q('img').evaluate('(i)=>({top:parseFloat(i.style.top),width:parseFloat(i.style.width)})');q('.walkStage').screenshot(path=str(O/f'{view}-foot06-off.png'));q('[data-walk=down-foot]').check();q('.walkStage').screenshot(path=str(O/f'{view}-foot06-on.png'));z=q('img').evaluate('(i)=>parseFloat(i.style.top)');ck(view+' correction exactly8nativepx',abs(z-a['top']-a['width']/2048*8)<.001)
  q('[data-walk=down-bob]').uncheck();ready(p);q('[data-walk=next]').tap();q('[data-walk=next]').tap();q('[data-walk=next]').tap();q('.walkStage').screenshot(path=str(O/f'{view}-foot06-bob-off.png'));ck(view+' bob off render stable',q('img').evaluate('(i)=>i.style.transform')=='translateY(0px)');q('[data-walk=down-sequence]').select_option('six');ready(p);ck(view+' baseline controls reflect real bob/no correction',q('[data-walk=down-bob]').is_checked() and q('[data-walk=down-bob]').is_disabled() and not q('[data-walk=down-foot]').is_checked() and q('[data-walk=down-stride]').input_value()=='90');q('[data-walk=down-sequence]').select_option('four');ready(p);ck(view+' trial options restored',not q('[data-walk=down-bob]').is_checked() and q('[data-walk=down-foot]').is_checked());q('[data-walk=down-foot]').uncheck();q('[data-walk=down-bob]').check();ready(p)
  for d,total,stride in [('up',6,90),('left',6,180),('right',6,180)]:
   q('[data-direction='+d+']').tap();ready(p);s=p.evaluate('DevWalkTest.snapshot()');ck(view+' other direction '+d,s['total']==total and s['effectiveStride']==stride and not q('[data-walk=down-controls]').is_visible())
  q('[data-walk=actor]').select_option('fiona');q('[data-direction=down]').tap();ready(p);ck(view+' Fiona unchanged',p.evaluate('DevWalkTest.snapshot().total===4&&DevWalkTest.snapshot().effectiveStride===90') and not q('[data-walk=down-controls]').is_visible())
  q('[data-walk=actor]').select_option('aidan');ready(p);q('[data-walk=down-sequence]').select_option('six');ready(p);ck(view+' baseline reset exact six90',p.evaluate('DevWalkTest.snapshot().total===6&&DevWalkTest.snapshot().effectiveStride===90'))
  ck(view+' no panel horizontal overflow',p.evaluate("(()=>{const p=document.querySelector('.walkPanel');return p.scrollWidth<=p.clientWidth+1})()"))
  p.set_viewport_size({'width':h,'height':w});p.wait_for_timeout(100);ck(view+' rotate layout inside viewport',q('.walkStage').bounding_box()['width']>0)
  q('[data-walk=play]').tap();q('[data-walk=close]').tap();ck(view+' cleanup and protected game state',not p.evaluate('DevWalkTest.snapshot().timer') and p.evaluate(STATE)==before)
  # Field movement remains ordinary keyboard at300 world/s after closing preview.
  f=p.evaluate('MossForest.feet');p.keyboard.down('ArrowRight');p.wait_for_timeout(200);p.keyboard.up('ArrowRight');p.wait_for_timeout(220);after=p.evaluate('MossForest.feet');ck(view+' normal movement resumes at unchanged speed',45<after['x']-f['x']<85 and abs(after['y']-f['y'])<1)
  ck(view+' no unexpected request failures',not failed);video=p.video;c.close();video.save_as(str(O/f'{view}-comparison.webm'))
 # Closed DEV gate does not create UI, listeners or a public API.
 gate=b.new_page();ck('nonDEV gate has no effects',gate.evaluate("""async source=>{window.WINDBOUND_DEV=false;let count=0;const old=window.addEventListener;window.addEventListener=()=>count++;try{eval(source);return !window.DevWalkTest&&count===0&&!document.querySelector('#walkMotionTest')}finally{window.addEventListener=old}}""",(R/'js/dev/walk-test.js').read_text()));gate.close();b.close()
ck('no console/Promise/HTTP errors',not errors);print('FAILS 0')

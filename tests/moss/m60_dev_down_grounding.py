"""12 DEV conditions: actual decoded frame cadence/DOM contour registration and full-frame offsets."""
import os,sys,json,math,statistics,hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/qa'))
from browser_support import server
sys.path.insert(0,str(R/'tests/helpers'))
from walk_bootstrap_network import expected_retarget
O=Path(os.getenv('QA_OUT','/tmp/down-ground'));O.mkdir(parents=True,exist_ok=True)
M=json.loads((R/'tests/fixtures/aidan_down_support.json').read_text());markers={r['frame']:r for r in M['markers']};checks=[];runs=[];errors=[]
def ck(n,x):
 checks.append({'name':n,'pass':bool(x)});(O/'ground-results.json').write_text(json.dumps(checks,indent=2));print(('PASS ' if x else 'FAIL ')+n,flush=True);assert x,n
STATE="JSON.stringify({stage:storyStage,flags:PrologueProgress.eventSnapshot(),inventory:Inventory.serialize(),party:PartyManager.members,gold,storage:{...localStorage},feet:MossForest.feet,map:MossForest.mapId,movement:FieldMovement.settings,frames:AidanFieldAssets.frames})"
CAPTURE="""()=>new Promise(resolve=>{const rows=[],start=performance.now();function f(t){const i=document.querySelector('#walkMotionTest img'),b=i.getBoundingClientRect(),g=document.querySelector('.walkGround').getBoundingClientRect(),s=DevWalkTest.snapshot();if(i.complete&&i.naturalWidth===2048&&i.currentSrc===i.src)rows.push({t,time:s.time,index:s.index,src:i.currentSrc,y:b.y,h:b.height,w:b.width,ground:g.y,top:i.style.top,transform:i.style.transform});if(t-start<1050)requestAnimationFrame(f);else resolve(rows)}requestAnimationFrame(f)})"""
def ready(p):p.wait_for_function('DevWalkTest.snapshot().ready')
for m in markers.values():ck('original marker SHA '+str(m['frame']),hashlib.sha256((R/m['source_path']).read_bytes()).hexdigest()==m['sha256'])
with server(8834) as base,sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE') or '/usr/bin/chromium')
 for view,w,h in [('pc',1920,1080),('portrait',390,844),('landscape',844,390)]:
  c=b.new_context(viewport={'width':w,'height':h},has_touch=True,record_video_dir=str(O/'video'),record_video_size=({'width':640,'height':360} if w>h else {'width':360,'height':640}));p=c.new_page();failed=[];phase={'dev':False}
  p.on('pageerror',lambda e:errors.append(str(e)));p.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);p.on('response',lambda r:errors.append(f'HTTP{r.status} {r.url}') if r.status>=400 else None)
  p.on('requestfailed',lambda r,ev=failed,ph=phase:ev.append({'url':r.url,'failure':r.failure,'resource_type':r.resource_type,'before_dev':not ph['dev']}))
  p.goto(base+'/index.html?title=1');p.get_by_role('button',name='NEW GAME',exact=True).click();p.wait_for_function("LoadCoordinator.phase==='READY'&&MossForest.active&&document.body.classList.contains('dialogueOpen')")
  for _ in range(40):
   if p.evaluate("InputManager.state()!=='DIALOGUE'"):break
   p.keyboard.press('Enter');p.wait_for_timeout(80)
  p.wait_for_function("!MossForest.busy&&!LoadingInput.busy&&!document.body.classList.contains('dialogueOpen')")
  if failed:
   repl=p.evaluate("()=>{const i=document.querySelector('#raiderSprite img');return {url:i.currentSrc,loaded:i.complete&&i.naturalWidth>0,registered:BattleMotion.frames('goblin_raider','idle').urls.map(u=>new URL(u,location.href).href)}}")
   for e in failed:ck(view+' startupdecodedreplacement',expected_retarget(e,urljoin(base+'/','img/battle/enemies/goblin_raider/goblin_raider_battle_idle.png'),repl))
   failed.clear()
  protected=p.evaluate(STATE);phase['dev']=True;p.locator('#devBtn').click();p.locator('#devWalkMotionTest').tap();ready(p);q=lambda s:p.locator('#walkMotionTest '+s)
  q('[data-walk=down-sequence]').select_option('four');ready(p)
  for cycle in [90,75]:
   q('[data-walk=down-stride]').select_option(str(cycle));ready(p)
   for mode,amp in [('on',1),('off',0),('quarter',.25)]:
    q('[data-walk=down-bob]').set_checked(mode!='off');ready(p)
    if mode!='off':q('[data-walk=down-suppress]').set_checked(mode=='quarter');ready(p)
    else:ck(view+' bobOFF disables suppression',q('[data-walk=down-suppress]').is_disabled() and not q('[data-walk=down-suppress]').is_checked())
    for offset in [0,8]:
     q('[data-walk=down-foot]').set_checked(bool(offset));q('[data-walk=down-stride]').select_option(str(cycle));ready(p)
     label=f'{view}-{cycle}-{mode}-{offset}';caption=q('[data-walk=down-condition]').inner_text();ck(label+' effective readable condition',str(cycle) in caption and ('25%' if mode=='quarter' else mode.upper()) in caption)
     # Fixed quarter boundaries isolate the actual official source PNGs; screenshots are raw comparisons only.
     for j,n in enumerate([1,5,2,6]):
      p.wait_for_function("n=>{const i=document.querySelector('#walkMotionTest img');return i.complete&&i.currentSrc.includes('_'+String(n).padStart(2,'0')+'.png')}",arg=n)
      if cycle==90 and (view=='pc' or n==6):q('.walkStage').screenshot(path=str(O/f'{label}-frame{n:02}.png'))
      q('[data-walk=next]').tap()
     q('[data-walk=play]').tap();rows=p.evaluate(CAPTURE);q('[data-walk=pause]').tap();trans=[];order=[];gaps={128:[],200:[]};max_error=0
     for r in rows:
      n=int(r['src'].split('_')[-1].split('.')[0]);r['frame']=n;z=r['h']/1280/.0625;lift=1.5*abs(math.sin(r['time']*300/(cycle/2)*math.pi))*amp;shift=.5 if n==6 and offset else 0;actual_origin=(r['y']+1230/1280*r['h']-r['ground'])/z
      max_error=max(max_error,abs(actual_origin-(shift-lift)));r['origin_world']=actual_origin;r['expected_lift']=lift
      for t in [128,200]:
       native=markers[n]['thresholds'][str(t)]['marker_native'][1];actual=(r['ground']-(r['y']+native/1280*r['h']))/z;expected=(1230-native)*.0625+lift-shift;max_error=max(max_error,abs(actual-expected));r['gap'+str(t)]=actual;gaps[t].append(actual)
      if not trans or trans[-1]['frame']!=n:trans.append(r);order.append(n)
     run={'view':view,'cycle':cycle,'mode':mode,'foot_offset':offset,'rows':rows,'max_projection_error_world':max_error,'gap128_range':[min(gaps[128]),max(gaps[128])],'gap200_range':[min(gaps[200]),max(gaps[200])]};runs.append(run);(O/'ground-runs.json').write_text(json.dumps(runs,separators=(',',':')))
     ck(label+' actualdecoded01-05-02-06',len(order)>8 and all(bb==[1,5,2,6][([1,5,2,6].index(a)+1)%4] for a,bb in zip(order,order[1:])))
     tt=[r['t'] for r in trans if r['frame']==1];period=statistics.median((bb-a)/1000 for a,bb in zip(tt,tt[1:]));run['measured_period']=period;ck(label+' actualperiod',abs(period-cycle/300)<.035)
     ck(label+' contour and wholebody transform measured',max_error<.04);ck(label+' no residualRAF',not p.evaluate('DevWalkTest.snapshot().timer'))
  # Retained private suppression must not leak to baseline or other directions/characters.
  q('[data-walk=down-bob]').check();ready(p);q('[data-walk=down-suppress]').check();ready(p);q('[data-walk=down-sequence]').select_option('six');ready(p)
  ck(view+' baseline6/90 and suppression inactive',p.evaluate('DevWalkTest.snapshot().total===6&&DevWalkTest.snapshot().effectiveStride===90') and q('[data-walk=down-suppress]').is_disabled() and not q('[data-walk=down-suppress]').is_checked())
  for d,stride in [('up',90),('left',180),('right',180)]:
   q('[data-direction='+d+']').tap();ready(p);ck(view+' otherdir '+d,p.evaluate('DevWalkTest.snapshot().effectiveStride')==stride and not q('[data-walk=down-condition]').is_visible())
  q('[data-walk=actor]').select_option('fiona');q('[data-direction=down]').tap();ready(p);ck(view+' Fiona4/90 unchanged',p.evaluate('DevWalkTest.snapshot().total===4&&DevWalkTest.snapshot().effectiveStride===90') and not q('[data-walk=down-controls]').is_visible())
  ck(view+' panel fits',p.evaluate("(()=>{const x=document.querySelector('.walkPanel');return x.scrollWidth<=x.clientWidth+1})()"));q('[data-walk=close]').tap();ck(view+' productionSAVEstateunchanged',p.evaluate(STATE)==protected and not p.evaluate('DevWalkTest.snapshot().timer'))
  ck(view+' no failed requests',not failed);video=p.video;c.close();video.save_as(str(O/f'{view}-matrix.webm'))
 b.close()
(O/'ground-runs.json').write_text(json.dumps(runs,separators=(',',':')));ck('no console/Promise/HTTP errors',not errors);print('FAILS 0')

"""UP07 production path only: no init script, descriptor override, alias or DEV jump."""
import json,os,sys,statistics,hashlib,math,re
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
from PIL import Image
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/qa'));from browser_support import server
sys.path.insert(0,str(R/'tests/helpers'));from walk_bootstrap_network import expected_retarget
from up07_metrics import capture_metrics
O=Path(os.getenv('QA_OUT','/tmp/up07-production'));O.mkdir(parents=True,exist_ok=True);checks=[];runs=[];errors=[]
M=json.loads((R/'img/field/characters/aidan/up5/adopted-walk.json').read_text());URLS=[r['path'] for r in M['files']];KEYS=['aidan_walk_up_pushoff']+['aidan_walk_up_'+str(n).zfill(2) for n in [3,4,1,6]]
def ck(n,v):
 checks.append({'name':n,'pass':bool(v)});(O/'results.json').write_text(json.dumps(checks,indent=2));(O/'runs.json').write_text(json.dumps(runs,indent=2));print(('PASS ' if v else 'FAIL ')+n,flush=True);assert v,n
for row in M['files']:ck('adopted SHA '+row['key'],hashlib.sha256((R/row['path']).read_bytes()).hexdigest()==row['sha256'])
ck('exact approved candidate SHA',M['files'][0]['sha256']=='1bde96684c85739e821e8c7e5e8f07831b8819414569d07d6a3bbb3613e80dfd');im=Image.open(R/URLS[0]);ck('full adopted RGBA canvas/bounds',im.mode=='RGBA' and im.size==(2048,1280) and im.getbbox()==(604,126,1497,1230))
STABLE="JSON.stringify({stage:storyStage,flags:PrologueProgress.eventSnapshot(),inventory:Inventory.serialize(),party:PartyManager.members,gold,movement:FieldMovement.settings,assets:AidanFieldAssets})"
OBS="""()=>{const o=window.__up07={rows:[],id:null,keyEvents:[],keys:new Set(),longTasks:[],start:{t:performance.now(),feet:{...MossForest.feet},timeOrigin:performance.timeOrigin,viewport:[innerWidth,innerHeight],dpr:devicePixelRatio,visibility:document.visibilityState}};
 o.onKey=e=>{if(e.type==='keydown')o.keys.add(e.key);else o.keys.delete(e.key);o.keyEvents.push({type:e.type,key:e.key,repeat:e.repeat,t:performance.now(),feet:{...MossForest.feet}})};addEventListener('keydown',o.onKey,{capture:true,passive:true});addEventListener('keyup',o.onKey,{capture:true,passive:true});
 try{o.po=new PerformanceObserver(list=>o.longTasks.push(...list.getEntries().map(e=>({start:e.startTime,duration:e.duration,name:e.name}))));o.po.observe({entryTypes:['longtask']})}catch(e){o.longTaskUnsupported=String(e)}
 function f(t){const observerStart=performance.now();const i=[...document.querySelectorAll('.forest-aidan')].find(i=>!i.hidden);o.rows.push({t,now:performance.now(),...MossForest.feet,frameScale:FieldMovement.frameScale,heldKeys:[...o.keys],inputState:InputManager.state(),src:i?.dataset.src,currentSrc:i?.currentSrc,loaded:i?.complete&&i?.naturalWidth===2048,transform:i?.style.transform,top:i?.style.top,heading:MossForest.snapshot().facing,observerStart,observerCostMs:performance.now()-observerStart});o.id=requestAnimationFrame(f)}o.id=requestAnimationFrame(f)}"""
def settle(p):p.wait_for_timeout(160)
def go(p,key,cond):
 p.keyboard.down(key)
 try:p.wait_for_function(cond,timeout=8000,polling='raf')
 finally:p.keyboard.up(key)
 settle(p)
def stop(p):return p.evaluate("()=>{const o=__up07;cancelAnimationFrame(o.id);removeEventListener('keydown',o.onKey,true);removeEventListener('keyup',o.onKey,true);if(o.po){o.longTasks.push(...o.po.takeRecords().map(e=>({start:e.startTime,duration:e.duration,name:e.name})));o.po.disconnect()}o.end={t:performance.now(),feet:{...MossForest.feet}};return o.rows}")
def decoded(rows):return all(r['loaded'] and r['currentSrc'].split('?')[0].endswith('/'+r['src'].split('?')[0]) for r in rows)
def transitions(rows):
 out=[]
 for r in rows:
  path=(r['src'] or '').split('?')[0]
  if path not in URLS:continue
  r['frame']=URLS.index(path)
  if not out or out[-1]['frame']!=r['frame']:out.append(r)
 return out

def network(p,failed,base,label):
 if failed:
  repl=p.evaluate("()=>{const i=document.querySelector('#raiderSprite img');return {url:i.currentSrc,loaded:i.complete&&i.naturalWidth>0,registered:BattleMotion.frames('goblin_raider','idle').urls.map(u=>new URL(u,location.href).href)}}")
  for e in failed:ck(label+' exact unused startup retarget',expected_retarget(e,urljoin(base+'/','img/battle/enemies/goblin_raider/goblin_raider_battle_idle.png'),repl))
  failed.clear()

def field_check(p,rows,label):
 moving=[z for a,z in zip(rows,rows[1:]) if z['y']<a['y']-.01 and z['transform'] and (z['src'] or '').split('?')[0] in URLS];tr=transitions(moving)
 cycles=[{'distance':math.hypot(tr[i+5]['x']-tr[i]['x'],tr[i+5]['y']-tr[i]['y']),'seconds':(tr[i+5]['t']-tr[i]['t'])/1000} for i in range(len(tr)-5)]
 context=p.evaluate('()=>({start:__up07.start,end:__up07.end,keyEvents:__up07.keyEvents,longTasks:__up07.longTasks,longTaskUnsupported:__up07.longTaskUnsupported||null})')
 context.update(globals().get('MEASURE_CONTEXT',{}))
 capture_metrics(O/'measurements'/label.replace('/','_'),label,rows,moving,tr,cycles,context)
 ck(label+' five actual decoded sources/order/wrap',set(r['frame'] for r in tr)==set(range(5)) and all(z['frame']==(a['frame']+1)%5 for a,z in zip(tr,tr[1:])) and decoded(moving))
 ck(label+' 90world/.300second measured',len(cycles)>=4 and abs(statistics.median(x['distance'] for x in cycles)-90)<12 and abs(statistics.median(x['seconds'] for x in cycles)-.3)<.08)
 ck(label+' quarter bob/unmirrored/full anchor',all('scaleX' not in r['transform'] and abs(float(re.search(r'translateY\(([-\d.]+)px\)',r['transform'])[1]))<=.386 for r in moving) and len({r['top'] for r in moving})==1)
 return cycles
with server(8847) as base,sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE') or '/usr/bin/chromium')
 for view,w,h in [('pc',960,540),('portrait',390,844),('landscape',844,390)]:
  c=b.new_context(viewport={'width':w,'height':h},has_touch=True,record_video_dir=str(O/'video'),record_video_size={'width':w,'height':h});p=c.new_page();failed=[];phase={'dev':False}
  p.on('pageerror',lambda e:errors.append(str(e)));p.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);p.on('response',lambda r:errors.append(f'HTTP{r.status} {r.url}') if r.status>=400 else None);p.on('requestfailed',lambda r:failed.append({'url':r.url,'failure':r.failure,'resource_type':r.resource_type,'before_dev':not phase['dev']}))
  p.goto(base+'/index.html?title=1');p.get_by_role('button',name='NEW GAME',exact=True).click();p.wait_for_function("LoadCoordinator.phase==='READY'&&MossForest.active&&document.body.classList.contains('dialogueOpen')")
  for _ in range(40):
   if p.evaluate("InputManager.state()!=='DIALOGUE'"):break
   p.keyboard.press('Enter');p.wait_for_timeout(80)
  p.wait_for_function("!MossForest.busy&&!LoadingInput.busy&&!document.body.classList.contains('dialogueOpen')");p.wait_for_function("[...document.querySelectorAll('.forest-aidan')].every(i=>i.complete&&i.naturalWidth>0)");network(p,failed,base,view)
  ck(view+' real production five/order90/bob25',p.evaluate("()=>{const d=FieldWalkMotion.ally('aidan','up');return {keys:d.frames.map(f=>f.key),stride:d.stride,bob:d.bobScale,speed:d.speed()}}")=={'keys':KEYS,'stride':90,'bob':.25,'speed':300})
  ck(view+' no imported fixture or alias',p.evaluate("typeof QAUp06==='undefined'&&typeof DevUpWalkQA==='undefined'&&AidanFieldAssets.frames.aidan_walk_up_02.path.includes('/aidan_walk_up_02.png')&&!document.querySelector('[data-qa=up06-condition]')"));stable=p.evaluate(STABLE);storage=p.evaluate('JSON.stringify({...localStorage})')
  go(p,'ArrowDown','MossForest.feet.y>=370');go(p,'ArrowLeft','MossForest.feet.x<=250');go(p,'ArrowDown','MossForest.feet.y>=620')
  for route,keys in [('straight',['ArrowUp']),('ul',['ArrowUp','ArrowLeft']),('ur',['ArrowUp','ArrowRight'])]:
   if route!='straight':
    go(p,'ArrowDown','MossForest.feet.y>=370');go(p,'ArrowRight' if route=='ul' else 'ArrowLeft','MossForest.feet.x>=820' if route=='ul' else 'MossForest.feet.x<=130');go(p,'ArrowDown','MossForest.feet.y>=550')
   p.evaluate(OBS)
   for k in keys:p.keyboard.down(k)
   try:p.wait_for_function('MossForest.feet.y<=260',timeout=8000,polling='raf')
   finally:
    for k in keys:p.keyboard.up(k)
   rows=stop(p);cycles=field_check(p,rows,view+'/'+route);runs.append({'view':view,'kind':'field','route':route,'cycles':cycles,'rows':rows});settle(p);ck(view+'/'+route+' stop/protected game and SAVE',p.evaluate(STABLE)==stable and p.evaluate('JSON.stringify({...localStorage})')==storage and p.evaluate("[...document.querySelectorAll('.forest-aidan')].find(i=>!i.hidden).style.transform")=="");p.screenshot(path=str(O/f'{view}-{route}-stopped.png'))
  phase['dev']=True;p.locator('#devBtn').click();p.locator('#devWalkMotionTest').tap();q=lambda s:p.locator('#walkMotionTest '+s);p.wait_for_function('DevWalkTest.snapshot().ready');q('[data-direction=up]').tap();p.wait_for_function('DevWalkTest.snapshot().ready');ck(view+' stock DEV reads real production bank',p.evaluate('DevWalkTest.snapshot().total===5&&DevWalkTest.snapshot().effectiveStride===90'))
  for n,url in enumerate(URLS):
   p.wait_for_function("u=>{const i=document.querySelector('#walkMotionTest img');return i.complete&&i.currentSrc===i.src&&i.currentSrc.includes(u)}",arg=url);ck(view+' DEV actual source '+str(n),q('img').get_attribute('src').split('?')[0]==url)
   if n==0:q('.walkStage').screenshot(path=str(O/f'{view}-dev-pushoff.png'))
   q('[data-walk=next]').tap()
  q('[data-walk=play]').tap();p.wait_for_timeout(950);q('[data-walk=close]').tap();ck(view+' stock DEV cleanup',not p.evaluate('DevWalkTest.snapshot().timer'));ck(view+' unchanged progress after DEV',p.evaluate(STABLE)==stable and p.evaluate('JSON.stringify({...localStorage})')==storage)
  # Ordinary SAVE button and document-cold CONTINUE; never write storage or progress directly.
  feet=p.evaluate('MossForest.feet');p.locator('#menuOpen').click();p.locator('#systemMenu [data-stab=save]').click();p.locator('#doSave').click();p.wait_for_function('localStorage.getItem(SAVE_KEY)!==null');raw=p.evaluate('localStorage.getItem(SAVE_KEY)');ck(view+' actual UI SAVE is valid',json.loads(raw)['prologue']['moss']['map']=='rilde_in_aidan');phase['dev']=False;p.reload();p.wait_for_selector('#title-screen',state='visible');ck(view+' saved title enables CONTINUE',p.get_by_role('button',name='CONTINUE',exact=True).is_enabled());p.get_by_role('button',name='CONTINUE',exact=True).click();p.wait_for_function("SaveContinue.phase==='READY'&&LoadCoordinator.phase==='READY'&&MossForest.active");p.wait_for_function("[...document.querySelectorAll('.forest-aidan')].every(i=>i.complete&&i.naturalWidth>0)");network(p,failed,base,view+'/continue')
  ck(view+' CONTINUE exact feet/progress/SAVE',p.evaluate('MossForest.feet')==feet and p.evaluate(STABLE)==stable and p.evaluate('localStorage.getItem(SAVE_KEY)')==raw)
  go(p,'ArrowDown','MossForest.feet.y>=370');go(p,'ArrowLeft','MossForest.feet.x<=250');go(p,'ArrowDown','MossForest.feet.y>=620');p.evaluate(OBS);go(p,'ArrowUp','MossForest.feet.y<=260');rows=stop(p);cycles=field_check(p,rows,view+'/continued-up');runs.append({'view':view,'kind':'field','route':'continued-up','cycles':cycles,'rows':rows});ck(view+' CONTINUE no SAVE rewrite or stale alias',p.evaluate('localStorage.getItem(SAVE_KEY)')==raw and p.evaluate("AidanFieldAssets.frames.aidan_walk_up_02.path.includes('/aidan_walk_up_02.png')"));ck(view+' no failed requests',not failed)
  v=p.video;c.close();v.save_as(str(O/f'{view}-production.webm'))
 b.close()
ck('no console Promise HTTP errors',not errors);print('FAILS 0')

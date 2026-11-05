"""PR153 independent DEV fixture: temporary descriptors only; source JS/banks unchanged."""
import os,sys,json,re,math,statistics,hashlib
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/qa'));from browser_support import server
sys.path.insert(0,str(R/'tests/helpers'));from walk_bootstrap_network import expected_retarget
O=Path(os.getenv('QA_OUT','/tmp/up06-walk'));O.mkdir(parents=True,exist_ok=True);checks=[];runs=[];errors=[]
MODES={'A':([3,4,1,6],.25),'B':([0,3,4,1,6],.25),'C':([1,2,3,4,5,6],.25),'D':([1,2,3,4,5,6],1)}
sys.path.insert(0,str(R/'tests/helpers'));from up06_fixture import INIT,install_controls,field_scale,audit_gates
def ck(n,v):
 checks.append({'name':n,'pass':bool(v)});(O/'up-results.json').write_text(json.dumps(checks,indent=2));(O/'up-runs.json').write_text(json.dumps(runs,indent=2));print(('PASS ' if v else 'FAIL ')+n,flush=True);assert v,n
PROTECT="JSON.stringify({stage:storyStage,flags:PrologueProgress.eventSnapshot(),inventory:Inventory.serialize(),party:PartyManager.members,gold,storage:{...localStorage},movement:FieldMovement.settings,assets:AidanFieldAssets})"
OBS="""()=>{const o=window.__upObserve={rows:[],id:null};function f(t){const p=MossForest.feet,i=[...document.querySelectorAll('.forest-aidan')].find(i=>!i.hidden);o.rows.push({t,...p,src:i?.dataset.src,loaded:i?.complete&&i?.naturalWidth===2048,currentSrc:i?.currentSrc,transform:i?.style.transform,heading:MossForest.snapshot().facing});o.id=requestAnimationFrame(f)}o.id=requestAnimationFrame(f)}"""
CAP="""()=>new Promise(resolve=>{const rows=[],start=performance.now();function f(t){const s=DevWalkTest.snapshot(),i=document.querySelector('#walkMotionTest img'),r=i.getBoundingClientRect(),g=document.querySelector('.walkGround').getBoundingClientRect();if(i.complete&&i.currentSrc===i.src)rows.push({t,index:s.index,time:s.time,src:i.currentSrc,top:r.top,height:r.height,ground:g.top});if(t-start<1050)requestAnimationFrame(f);else resolve(rows)}requestAnimationFrame(f)})"""
def ready(p):p.wait_for_function('DevWalkTest.snapshot().ready')
def stop(p):return p.evaluate('()=>{cancelAnimationFrame(__upObserve.id);return __upObserve.rows}')
def settle(p):p.wait_for_timeout(160)
def go(p,key,condition):
 p.keyboard.down(key)
 try:p.wait_for_function(condition,timeout=8000,polling='raf')
 finally:p.keyboard.up(key)
 settle(p)
def phases(rows):
 trans=[]
 for r in rows:
  m=re.search(r'walk_up_(\d+)\.png',r.get('src') or '')
  if 'pushoff_candidate_v2.png' in (r.get('src') or ''):m=re.match(r'(0)','0')
  if m and r.get('loaded',True):
   r['frame']=int(m[1])
   if not trans or trans[-1]['frame']!=r['frame']:trans.append(r)
 return trans
for gate in audit_gates():ck('fixture gate '+gate['name'],gate['pass'])
with server(8846) as base,sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE') or '/usr/bin/chromium')
 for view,w,h in [('pc',960,540),('portrait',390,844),('landscape',844,390)]:
  c=b.new_context(viewport={'width':w,'height':h},has_touch=True,record_video_dir=str(O/'video'),record_video_size={'width':w,'height':h});c.add_init_script(INIT);p=c.new_page();failed=[];phase={'dev':False}
  p.on('pageerror',lambda e:errors.append(str(e)));p.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);p.on('response',lambda r:errors.append(f'HTTP{r.status} {r.url}') if r.status>=400 else None);p.on('requestfailed',lambda r:failed.append({'url':r.url,'failure':r.failure,'resource_type':r.resource_type,'before_dev':not phase['dev']}))
  p.goto(base+'/index.html?title=1&dev=1&up06QA=1');p.get_by_role('button',name='NEW GAME',exact=True).click();p.wait_for_function("LoadCoordinator.phase==='READY'&&MossForest.active&&document.body.classList.contains('dialogueOpen')")
  for _ in range(40):
   if p.evaluate("InputManager.state()!=='DIALOGUE'"):break
   p.keyboard.press('Enter');p.wait_for_timeout(80)
  p.wait_for_function("!MossForest.busy&&!LoadingInput.busy&&!document.body.classList.contains('dialogueOpen')");p.wait_for_function("[...document.querySelectorAll('.forest-aidan')].every(i=>i.complete&&i.naturalWidth>0)")
  if failed:
   repl=p.evaluate("()=>{const i=document.querySelector('#raiderSprite img');return {url:i.currentSrc,loaded:i.complete&&i.naturalWidth>0,registered:BattleMotion.frames('goblin_raider','idle').urls.map(u=>new URL(u,location.href).href)}}")
   for e in failed:ck(view+' exact startup retarget',expected_retarget(e,urljoin(base+'/','img/battle/enemies/goblin_raider/goblin_raider_battle_idle.png'),repl))
   failed.clear()
  protected=p.evaluate(PROTECT);ck(view+' normal game reset starts production D',p.evaluate("QAUp06.condition==='D'&&MossForest.mapId==='rilde_in_aidan'"));phase['dev']=True
  for mode,(order,amp) in MODES.items():
   p.locator('#devBtn').click();p.locator('#devWalkMotionTest').tap();ready(p);q=lambda s:p.locator('#walkMotionTest '+s);q('[data-direction=up]').tap();ready(p);install_controls(p);q('[data-qa=up06-condition]').select_option(mode);q('[data-direction=up]').tap();ready(p)
   ck(view+mode+' descriptor90/order/bob',p.evaluate("()=>{const d=FieldWalkMotion.ally('aidan','up');return {stride:d.stride,order:d.frames.map(f=>f.url.includes('pushoff_candidate_v2')?0:Number(f.key.slice(-2))),bob:d.bobScale,speed:d.speed()}} ")=={'stride':90,'order':order,'bob':amp,'speed':300})
   for field in [False,True]:
    field_scale(p,field)
    # A paused loop may finish at any phase; use ordinary stepping to reach frame zero.
    for _ in range(len(order)):
     if p.evaluate('DevWalkTest.snapshot().index')==0:break
     q('[data-walk=next]').tap()
    for n in order:
     p.wait_for_function("n=>{const i=document.querySelector('#walkMotionTest img');return i.complete&&i.naturalWidth===2048&&i.currentSrc.includes(n===0?'pushoff_candidate_v2.png':'walk_up_'+String(n).padStart(2,'0')+'.png')}",arg=n)
     if view=='pc':q('.walkStage').screenshot(path=str(O/f'{view}-{mode}-scale{int(field)}-{n:02}.png'))
     q('[data-walk=next]').tap()
    q('[data-walk=play]').tap();rows=p.evaluate(CAP);q('[data-walk=pause]').tap();trans=phases(rows);tt=[r['t'] for r in trans if r['frame']==order[0]];period=statistics.median((y-x)/1000 for x,y in zip(tt,tt[1:]));err=[]
    for r in rows:
     z=r['height']/80;actual=(r['top']+1230/1280*r['height']-r['ground'])/z;expected=-abs(math.sin(r['time']*300/45*math.pi))*1.5*amp;err.append(abs(actual-expected))
    runs.append({'view':view,'mode':mode,'kind':'preview','field_scale':field,'period':period,'bob_error':max(err),'rows':rows});ck(view+mode+str(field)+' decoded cyclic order',len(trans)>10 and all(y['frame']==order[(order.index(x['frame'])+1)%len(order)] for x,y in zip(trans,trans[1:])));ck(view+mode+str(field)+' period and bob',abs(period-.3)<.04 and max(err)<.04);ck(view+mode+str(field)+' spatial scale',not field or all(abs(r['height']-80)<.1 for r in rows))
   q('[data-walk=close]').tap()
   # Clear aisles reached with ordinary keyboard only, no map/flag/HP/position writes.
   go(p,'ArrowDown','MossForest.feet.y>=370');go(p,'ArrowLeft','MossForest.feet.x<=250');go(p,'ArrowDown','MossForest.feet.y>=620')
   for route,keys in [('straight',['ArrowUp']),('ul',['ArrowUp','ArrowLeft']),('ur',['ArrowUp','ArrowRight'])]:
    if route!='straight':
     go(p,'ArrowDown','MossForest.feet.y>=370');go(p,'ArrowRight' if route=='ul' else 'ArrowLeft','MossForest.feet.x>=820' if route=='ul' else 'MossForest.feet.x<=130');go(p,'ArrowDown','MossForest.feet.y>=550')
    origin=p.evaluate('MossForest.feet');p.evaluate(OBS)
    for k in keys:p.keyboard.down(k)
    try:p.wait_for_function('MossForest.feet.y<=260',timeout=8000,polling='raf')
    finally:
     for k in keys:p.keyboard.up(k)
    rows=stop(p);moving=[]
    for a,z in zip(rows,rows[1:]):
     if z['y']<a['y']-.01 and z['transform'] and re.search(r'walk_up_\d+|pushoff_candidate_v2',z['src'] or ''):moving.append(z)
    trans=phases(moving);cycles=[]
    for i in range(len(trans)-len(order)):
     a,z=trans[i],trans[i+len(order)];cycles.append({'distance':math.hypot(z['x']-a['x'],z['y']-a['y']),'seconds':(z['t']-a['t'])/1000})
    runs.append({'view':view,'mode':mode,'kind':'field','route':route,'origin':origin,'cycles':cycles,'rows':rows});ck(view+mode+route+' field decoded order/unmirrored',set(r['frame'] for r in trans)==set(order) and all(z['frame']==order[(order.index(a['frame'])+1)%len(order)] for a,z in zip(trans,trans[1:])) and all('scaleX' not in r['transform'] and r['loaded'] and r['currentSrc'].split('?')[0].endswith('/'+r['src'].split('?')[0]) for r in moving));ck(view+mode+route+' actual90 distance/.300seconds',len(cycles)>=4 and abs(statistics.median(r['distance'] for r in cycles)-90)<12 and abs(statistics.median(r['seconds'] for r in cycles)-.3)<.08);ck(view+mode+route+' bob amplitude',all(abs(float(re.search(r'translateY\(([-\d.]+)px\)',r['transform'])[1]))<=1.5*amp+.011 for r in moving));settle(p);ck(view+mode+route+' stop and game state',p.evaluate(PROTECT)==protected and p.evaluate("[...document.querySelectorAll('.forest-aidan')].find(i=>!i.hidden).style.transform")=="");p.screenshot(path=str(O/f'{view}-{mode}-{route}-stopped.png'))
  ck(view+' fixture other descriptors retain identity',p.evaluate('QAUp06.otherDescriptorsUnchanged()'));ck(view+' other bank unchanged',p.evaluate("(()=>{const d=FieldWalkMotion.ally('aidan','down');return d.frames.length===4&&d.bobScale===.25&&d.frames[1].url.includes('/arm02/')&&FieldWalkMotion.ally('aidan','left').stride===180&&FieldWalkMotion.ally('fiona','up').frames.length===4})()"));ck(view+' no failures',not failed);v=p.video;c.close();v.save_as(str(O/f'{view}-four-conditions.webm'))
 b.close()
ck('no console Promise HTTP errors',not errors);print('FAILS 0')

"""Production180 cadence through normal NEW GAME + keyboard walking, then same DEV frames."""
import json,os,sys,statistics
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/qa'))
from browser_support import server
sys.path.insert(0,str(R/'tests/helpers'))
from walk_bootstrap_network import expected_retarget
from urllib.parse import urljoin
O=Path(os.getenv('QA_OUT','/tmp/aidan-side180'));O.mkdir(parents=True,exist_ok=True)
checks=[];evidence=[];errors=[]
def ck(name,ok):
 checks.append({'name':name,'pass':bool(ok)});(O/'side180-results.json').write_text(json.dumps(checks,indent=2));print(('PASS ' if ok else 'FAIL ')+name,flush=True);assert ok,name
OBS="""()=>{window.__sideObservation={rows:[],id:null};const o=window.__sideObservation;function sample(t){const f=MossForest.feet,i=[...document.querySelectorAll('.forest-aidan')].find(i=>!i.hidden);o.rows.push({t,x:f.x,y:f.y,src:i?.dataset.src,loaded:i?.complete&&i?.naturalWidth>0,transform:i?.style.transform});o.id=requestAnimationFrame(sample)}o.id=requestAnimationFrame(sample)}"""
def stop_observer(p):return p.evaluate('()=>{const o=window.__sideObservation;cancelAnimationFrame(o.id);return o.rows}')
def idle(p):
 p.wait_for_timeout(220);a=p.evaluate('MossForest.feet');p.wait_for_timeout(180)
 ck('stopped feet and bob settle',p.evaluate('MossForest.feet')==a and p.evaluate("[...document.querySelectorAll('.forest-aidan')].find(i=>!i.hidden).style.transform")=="")
def walk(p,key,condition):
 p.keyboard.down(key)
 try:p.wait_for_function(condition,timeout=8000,polling='raf')
 finally:p.keyboard.up(key)
 idle(p)
with server(8832) as base,sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE') or '/usr/bin/chromium')
 for view,w,h in [('pc',1920,1080),('portrait',390,844),('landscape',844,390)]:
  c=b.new_context(viewport={'width':w,'height':h},has_touch=True);p=c.new_page();failed=[];phase={'dev':False}
  p.on('pageerror',lambda e:errors.append(str(e)));p.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);p.on('response',lambda r:errors.append(f'HTTP{r.status} {r.url}') if r.status>=400 else None)
  p.on('requestfailed',lambda r,ev=failed,ph=phase:ev.append({'url':r.url,'failure':r.failure,'resource_type':r.resource_type,'before_dev':not ph['dev']}))
  p.goto(base+'/index.html?title=1');p.get_by_role('button',name='NEW GAME',exact=True).click();p.wait_for_function("LoadCoordinator.phase==='READY'&&MossForest.active&&document.body.classList.contains('dialogueOpen')")
  for _ in range(40):
   if p.evaluate("InputManager.state()!=='DIALOGUE'"):break
   p.keyboard.press('Enter');p.wait_for_timeout(80)
  p.wait_for_function("!MossForest.busy&&!LoadingInput.busy&&!document.body.classList.contains('dialogueOpen')")
  p.wait_for_function("[...document.querySelectorAll('.forest-aidan')].every(i=>i.complete&&i.naturalWidth>0)")
  if failed:
   repl=p.evaluate("()=>{const i=document.querySelector('#raiderSprite img');return {url:i.currentSrc,loaded:i.complete&&i.naturalWidth>0,registered:BattleMotion.frames('goblin_raider','idle').urls.map(u=>new URL(u,location.href).href)}}")
   for e in failed:ck(view+' verified startup replacement',expected_retarget(e,urljoin(base+'/','img/battle/enemies/goblin_raider/goblin_raider_battle_idle.png'),repl))
   failed.clear()
  ck(view+' real normal NEW GAME house',p.evaluate("MossForest.mapId==='rilde_in_aidan'&&storyStage===0&&!DevWalkTest.active"))
  ck(view+' side-only production180',p.evaluate("['left','right'].every(d=>MossForest.walkStride('aidan',d)===180&&FieldWalkMotion.resolve('ally','aidan',d).stride===180)&&['up','down'].every(d=>MossForest.walkStride('aidan',d)===90)&&['up','down','left','right'].every(d=>MossForest.walkStride('fiona',d)===90)"))
  protected=p.evaluate("JSON.stringify({stage:storyStage,flags:PrologueProgress.eventSnapshot(),inventory:Inventory.serialize(),party:PartyManager.members,gold,storage:{...localStorage}})")
  # Clear central horizontal aisle by ordinary keyboard movement. No DEV jumps or game-state writes.
  walk(p,'ArrowDown','MossForest.feet.y>=370');walk(p,'ArrowLeft','MossForest.feet.x<=130')
  field_cycles=[]
  for direction,key,condition in [('right','ArrowRight','MossForest.feet.x>=740'),('left','ArrowLeft','MossForest.feet.x<=130')]:
   p.evaluate(OBS);p.keyboard.down(key)
   try:
    p.wait_for_function("d=>{const i=[...document.querySelectorAll('.forest-aidan')].find(i=>!i.hidden);return i?.dataset.src.includes('walk_'+d+'_03')}",arg=direction,timeout=8000)
    p.screenshot(path=str(O/f'{view}-field-{direction}.png'))
    p.wait_for_function(condition,timeout=8000,polling='raf')
   finally:p.keyboard.up(key)
   rows=stop_observer(p);evidence.append({'view':view,'direction':direction,'rows':rows});(O/'side180-field.json').write_text(json.dumps(evidence,indent=2))
   moving=[r for r in rows if r['src'] and f'walk_{direction}_' in r['src'] and r['transform']]
   transitions=[]
   for r in moving:
    n=int(r['src'].split('_')[-1].split('.')[0]);r['frame']=n
    if not transitions or transitions[-1]['frame']!=n:transitions.append(r)
   ck(view+'/'+direction+' actual six loaded field PNGs',set(r['frame'] for r in transitions)==set(range(1,7)) and all(r['loaded'] for r in moving))
   ck(view+'/'+direction+' forward sequential loop',all(b['frame']==a['frame']%6+1 for a,b in zip(transitions,transitions[1:])))
   # Same-frame returns after six transitions measure the full distance cycle, independent of FPS.
   cycles=[{'distance':abs(transitions[i+6]['x']-transitions[i]['x']),'seconds':(transitions[i+6]['t']-transitions[i]['t'])/1000} for i in range(len(transitions)-6)]
   ck(view+'/'+direction+' full180 world distance cycles',len(cycles)>=6 and all(abs(x['distance']-180)<16 for x in cycles))
   ck(view+'/'+direction+' base300world/s cadence approximately0.6s',abs(statistics.median(x['seconds'] for x in cycles)-.6)<.12)
   field_cycles+=cycles;idle(p)
   # Restart the same direction briefly, reverse to stay away from the wall, and settle.
   reverse='ArrowRight' if direction=='left' else 'ArrowLeft'
   p.keyboard.down(reverse);p.wait_for_timeout(180);p.keyboard.up(reverse);idle(p)
  ck(view+' movement leaves progress/SAVE untouched',p.evaluate("JSON.stringify({stage:storyStage,flags:PrologueProgress.eventSnapshot(),inventory:Inventory.serialize(),party:PartyManager.members,gold,storage:{...localStorage}})")==protected)
  phase['dev']=True;p.locator('#devBtn').click();p.locator('#devWalkMotionTest').tap();p.wait_for_function('DevWalkTest.snapshot().ready');q=lambda s:p.locator('#walkMotionTest '+s)
  q('[data-direction=left]').tap();p.wait_for_function('DevWalkTest.snapshot().ready')
  ck(view+' DEV inherits production180/rate1',p.evaluate('DevWalkTest.snapshot().effectiveStride===180&&DevWalkTest.snapshot().sideStride===180&&DevWalkTest.snapshot().speed===1'))
  q('[data-walk=play]').tap();preview=p.evaluate("""()=>new Promise(resolve=>{const rows=[],start=performance.now();let last;function f(t){const i=document.querySelector('#walkMotionTest img');if(i.complete&&i.currentSrc!==last){last=i.currentSrc;rows.push({t,src:last})}if(t-start<1650)requestAnimationFrame(f);else resolve(rows)}requestAnimationFrame(f)})""");q('[data-walk=pause]').tap()
  ones=[r['t'] for r in preview if 'left_01.png' in r['src']];periods=[(b-a)/1000 for a,b in zip(ones,ones[1:])]
  ck(view+' actual DEV/normal field cycle agreement',bool(periods) and abs(statistics.median(periods)-statistics.median(x['seconds'] for x in field_cycles))<.1)
  q('[data-walk=close]').tap();ck(view+' preview cleanup/no request failures',not p.evaluate('DevWalkTest.snapshot().timer') and not failed);c.close()
 b.close()
ck('no console/Promise/HTTP errors',not errors);print('FAILS 0')

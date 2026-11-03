"""Real DEV180/rate1 images, screen pixels at recovered toes and uninterrupted cycles."""
import os,sys,json,io
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/qa'))
from browser_support import server
sys.path.insert(0,str(R/'tests/helpers'))
from walk_bootstrap_network import expected_retarget
from urllib.parse import urljoin
O=Path(os.getenv('QA_OUT','/tmp/aidan-toes'));O.mkdir(parents=True,exist_ok=True);M=json.loads((R/'img/field/characters/aidan/side6/fix01/manifest.json').read_text());rows=[];errors=[];loops=[]
def ck(name,ok):
 rows.append({'name':name,'pass':bool(ok)});(O/'toe-results.json').write_text(json.dumps(rows,indent=2));print(('PASS ' if ok else 'FAIL ')+name,flush=True);assert ok,name
with server(8831) as base,sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE') or '/usr/bin/chromium')
 for view,w,h in [('pc',1920,1080),('portrait',390,844),('landscape',844,390)]:
  c=b.new_context(viewport={'width':w,'height':h},has_touch=True);p=c.new_page();events=[];phase={'dev':False}
  p.on('pageerror',lambda e:errors.append(str(e)));p.on('console',lambda msg:errors.append(msg.text) if msg.type=='error' else None);p.on('response',lambda r:errors.append(f'HTTP {r.status} {r.url}') if r.status>=400 else None)
  p.on('requestfailed',lambda r,ev=events,ph=phase:ev.append({'url':r.url,'failure':r.failure,'resource_type':r.resource_type,'before_dev':not ph['dev']}))
  p.goto(base+'/index.html?title=1');p.get_by_role('button',name='NEW GAME',exact=True).click();p.wait_for_function("LoadCoordinator.phase==='READY'&&MossForest.active&&document.body.classList.contains('dialogueOpen')")
  for _ in range(40):
   if p.evaluate("InputManager.state()!=='DIALOGUE'"):break
   p.keyboard.press('Enter');p.wait_for_timeout(80)
  p.wait_for_function("!MossForest.busy&&!LoadingInput.busy&&!document.body.classList.contains('dialogueOpen')")
  if events:
   p.wait_for_function("()=>{const i=document.querySelector('#raiderSprite img');return i.complete&&i.naturalWidth>0&&BattleMotion.frames('goblin_raider','idle').urls.some(u=>new URL(u,location.href).href===i.currentSrc)}")
   replacement=p.evaluate("()=>{const i=document.querySelector('#raiderSprite img');return {url:i.currentSrc,loaded:i.complete&&i.naturalWidth>0,registered:BattleMotion.frames('goblin_raider','idle').urls.map(u=>new URL(u,location.href).href)}}")
   for e in events:ck(view+' verified bootstrap retarget',expected_retarget(e,urljoin(base+'/','img/battle/enemies/goblin_raider/goblin_raider_battle_idle.png'),replacement))
   events.clear()
  phase['dev']=True;p.locator('#devBtn').click();p.locator('#devWalkMotionTest').tap();p.wait_for_function('DevWalkTest.snapshot().ready');q=lambda s:p.locator('#walkMotionTest '+s)
  q('[data-stride="180"]').tap();q('[data-walk=speed]').select_option('1');q('[data-walk=background]').select_option('light');q('[data-guide=ground]').uncheck();q('[data-guide=center]').uncheck()
  for side in ['left','right']:
   q('[data-direction='+side+']').tap();p.wait_for_function('DevWalkTest.snapshot().ready')
   ck(view+'/'+side+' preview180 only / game72',p.evaluate("DevWalkTest.snapshot().effectiveStride===180&&DevWalkTest.snapshot().speed===1&&MossForest.walkStride('aidan','left')===72"))
   for n in range(1,7):
    name=f'aidan_walk_{side}_{n:02}.png';p.wait_for_function("n=>{const i=document.querySelector('#walkMotionTest img');return i.complete&&i.naturalWidth===2048&&i.currentSrc.includes(n)}",arg=name);ck(f'{view}/{name} actual image/index',p.evaluate('DevWalkTest.snapshot().index')==n-1)
    if name in M['frames']:
     info=M['frames'][name];x,y=info['probe_pixel'];rect=q('img').bounding_box();stage=q('.walkStage').bounding_box();sx=rect['x']+x/2048*rect['width'];sy=rect['y']+y/1280*rect['height'];ck(f'{view}/{name} toe within stage',stage['x']<sx<stage['x']+stage['width'] and stage['y']<sy<stage['y']+stage['height'])
     shot=p.screenshot();pixel=Image.open(io.BytesIO(shot)).convert('RGB').getpixel((int(sx),int(sy)));ck(f'{view}/{name} recovered toe actually on screen',min(pixel)<225)
     (O/f'{view}-{side}-{n:02}.png').write_bytes(shot)
    q('[data-walk=next]').tap()
   q('[data-walk=play]').tap();data=p.evaluate("""()=>new Promise(resolve=>{const rows=[],t=performance.now();let last;function f(now){const i=document.querySelector('#walkMotionTest img');if(i.complete&&i.naturalWidth>0&&i.currentSrc!==last){last=i.currentSrc;rows.push({t:now,src:last})}if(now-t<1650)requestAnimationFrame(f);else resolve(rows)}requestAnimationFrame(f)})""");q('[data-walk=pause]').tap();ids=[int(x['src'].split('_')[-1].split('.')[0]) for x in data];wraps=sum(ids[i]<ids[i-1] for i in range(1,len(ids)));loops.append({'view':view,'side':side,'frames':data});ck(view+'/'+side+' actual6 frames/continuous wraps',set(ids)==set(range(1,7)) and wraps>=2);ck(view+'/'+side+' pause clears timer',not p.evaluate('DevWalkTest.snapshot().timer'))
   q('[data-walk=play]').tap();p.wait_for_timeout(130);q('[data-walk=pause]').tap();ck(view+'/'+side+' restart retains180',p.evaluate('DevWalkTest.snapshot().effectiveStride')==180)
  for direction in ['up','down','left','right']:
   q('[data-direction='+direction+']').tap();p.wait_for_function('DevWalkTest.snapshot().ready');ck(view+' turn '+direction,p.evaluate('DevWalkTest.snapshot().effectiveStride')==(180 if direction in ['left','right'] else 90))
  q('[data-walk=close]').tap();ck(view+' close releases preview',p.evaluate('!DevWalkTest.active&&!DevWalkTest.snapshot().timer'));ck(view+' no unexpected requests',not events);c.close()
 b.close()
(O/'toe-loops.json').write_text(json.dumps(loops,indent=2));ck('no console/Promise/HTTP errors',not errors);print('FAILS 0')

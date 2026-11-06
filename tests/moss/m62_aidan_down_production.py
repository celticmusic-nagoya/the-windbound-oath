"""Adopted down walk through NEW GAME and ordinary field input, then same DEV bank."""
import json,os,sys,statistics,hashlib,math,re
from pathlib import Path
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
from PIL import Image
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/qa'));from browser_support import server
sys.path.insert(0,str(R/'tests/helpers'));from walk_bootstrap_network import expected_retarget
O=Path(os.getenv('QA_OUT','/tmp/down-production'));O.mkdir(parents=True,exist_ok=True);checks=[];runs=[];errors=[]
def ck(n,v):
 checks.append({'name':n,'pass':bool(v)});(O/'down-production-results.json').write_text(json.dumps(checks,indent=2));print(('PASS ' if v else 'FAIL ')+n,flush=True);assert v,n
M=json.loads((R/'img/field/characters/aidan/down4/adopted-walk.json').read_text());urls=[x['path'] for x in M['files']]
for row in M['files']+[M['preserved_original06']]:ck('adopted/source SHA '+row['path'],hashlib.sha256((R/row['path']).read_bytes()).hexdigest()==row['sha256'])
im=Image.open(R/urls[-1]);ck('full RGBA candidate bounds',im.mode=='RGBA' and im.size==(2048,1280) and list(im.getbbox())==[668,126,1524,1237])
PROTECTED="JSON.stringify({stage:storyStage,flags:PrologueProgress.eventSnapshot(),inventory:Inventory.serialize(),party:PartyManager.members,gold,storage:{...localStorage},movement:FieldMovement.settings})"
OBS="""()=>{const o=window.__downQA={rows:[],id:null};function f(t){const feet=MossForest.feet,i=[...document.querySelectorAll('.forest-aidan')].find(x=>!x.hidden);o.rows.push({t,...feet,src:i?.dataset.src,loaded:i?.complete&&i?.naturalWidth===2048,transform:i?.style.transform,top:i?.style.top});o.id=requestAnimationFrame(f)}o.id=requestAnimationFrame(f)}"""
def stop(p):return p.evaluate('()=>{cancelAnimationFrame(__downQA.id);return __downQA.rows}')
def settle(p):p.wait_for_timeout(230)
with server(8836) as base,sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE') or '/usr/bin/chromium')
 for view,w,h in [('pc',1920,1080),('portrait',390,844),('landscape',844,390)]:
  c=b.new_context(viewport={'width':w,'height':h},has_touch=True,record_video_dir=str(O/'video'),record_video_size={'width':640,'height':360} if w>h else {'width':360,'height':640});p=c.new_page();failed=[];phase={'dev':False}
  p.on('pageerror',lambda e:errors.append(str(e)));p.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);p.on('response',lambda r:errors.append(f'HTTP{r.status} {r.url}') if r.status>=400 else None);p.on('requestfailed',lambda r:failed.append({'url':r.url,'failure':r.failure,'resource_type':r.resource_type,'before_dev':not phase['dev']}))
  p.goto(base+'/index.html?title=1');p.get_by_role('button',name='NEW GAME',exact=True).click();p.wait_for_function("LoadCoordinator.phase==='READY'&&MossForest.active&&document.body.classList.contains('dialogueOpen')")
  for _ in range(40):
   if p.evaluate("InputManager.state()!=='DIALOGUE'"):break
   p.keyboard.press('Enter');p.wait_for_timeout(80)
  p.wait_for_function("!MossForest.busy&&!LoadingInput.busy&&!document.body.classList.contains('dialogueOpen')");p.wait_for_function("[...document.querySelectorAll('.forest-aidan')].every(i=>i.complete&&i.naturalWidth>0)")
  if failed:
   repl=p.evaluate("()=>{const i=document.querySelector('#raiderSprite img');return {url:i.currentSrc,loaded:i.complete&&i.naturalWidth>0,registered:BattleMotion.frames('goblin_raider','idle').urls.map(u=>new URL(u,location.href).href)}}")
   for e in failed:ck(view+' decoded startup retarget',expected_retarget(e,urljoin(base+'/','img/battle/enemies/goblin_raider/goblin_raider_battle_idle.png'),repl))
   failed.clear()
  ck(view+' real NEW GAME and exact metadata',p.evaluate("(()=>{const d=FieldWalkMotion.ally('aidan','down');return MossForest.mapId==='rilde_in_aidan'&&storyStage===0&&!DevWalkTest.active&&d.stride===90&&d.bobScale===.25&&d.speed()===300&&d.frames.map(f=>f.key).join(',')===[1,5,2,6].map(n=>'aidan_walk_down_'+String(n).padStart(2,'0')).join(',')})()"));protected=p.evaluate(PROTECTED)
  origin=p.evaluate('MossForest.feet');p.evaluate(OBS);p.keyboard.down('ArrowDown')
  try:
   p.wait_for_function("()=>{const i=[...document.querySelectorAll('.forest-aidan')].find(i=>!i.hidden);return i?.dataset.src.includes('down4/aidan_walk_down_06_ground')&&!!i.style.transform}",timeout=5000,polling='raf');p.screenshot(path=str(O/f'{view}-field-06.png'))
   p.wait_for_function('MossForest.feet.y>630',timeout=5000,polling='raf');p.wait_for_timeout(450);p.screenshot(path=str(O/f'{view}-field-down.png'))
  finally:p.keyboard.up('ArrowDown')
  rows=stop(p);runs.append({'view':view,'action':'down-through-wall-contact','origin':origin,'rows':rows});moving=[]
  for a,z in zip(rows,rows[1:]):
   if z['y']>a['y']+.01 and z['transform']:
    z['frame']=urls.index(z['src'].split('?')[0]) if z['src'].split('?')[0] in urls else -1;moving.append(z)
  trans=[]
  for r in moving:
   if not trans or trans[-1]['frame']!=r['frame']:trans.append(r)
  ck(view+' actual decoded adopted four field PNGs',set(r['frame'] for r in trans)=={0,1,2,3} and all(r['loaded'] for r in moving));ck(view+' actual01-05-02-repaired06 wrap',len(trans)>8 and all(z['frame']==(a['frame']+1)%4 for a,z in zip(trans,trans[1:])))
  cycles=[{'distance':trans[i+4]['y']-trans[i]['y'],'seconds':(trans[i+4]['t']-trans[i]['t'])/1000} for i in range(len(trans)-4)];ck(view+' cycle90 actual world displacement',len(cycles)>4 and all(abs(r['distance']-90)<12 for r in cycles));ck(view+' measured .300s cycle',abs(statistics.median(r['seconds'] for r in cycles)-.3)<.06)
  bob=[float(re.search(r'translateY\(([-\d.]+)px\)',r['transform'])[1]) for r in moving];ck(view+' actual quarter bob without wholeframe offset',min(bob)>=-.381 and min(bob)<-.30 and max(bob)<=0);ck(view+' no per-frame anchor shifts',len(set(r['top'] for r in moving))==1);bob_error=max(abs(float(re.search(r'translateY\(([-\d.]+)px\)',r['transform'])[1])+abs(math.sin((r['y']-origin['y'])/45*math.pi))*.375) for r in moving);ck(view+' exact production quarter bob wave',bob_error<.011)
  ck(view+' wall collision prevents out of bounds',max(r['y'] for r in rows)<=672 and abs(rows[-1]['y']-rows[-5]['y'])<.01 and not p.evaluate('MossForest.blocked(MossForest.feet.x,MossForest.feet.y)'));settle(p);ck(view+' stop clears bob',p.evaluate("[...document.querySelectorAll('.forest-aidan')].find(i=>!i.hidden).style.transform")=="")
  # Reverse/restart by ordinary keyboard and verify unchanged up bank/bob policy.
  p.evaluate(OBS);p.keyboard.down('ArrowUp');p.wait_for_timeout(800);p.keyboard.up('ArrowUp');up=stop(p);settle(p);runs.append({'view':view,'action':'reverse-up','rows':up});ck(view+' adopted up five/quarter-bob preserved',p.evaluate("FieldWalkMotion.ally('aidan','up').frames.length===5&&FieldWalkMotion.ally('aidan','up').bobScale===.25") and any('walk_up_' in (r['src'] or '') and r['transform'] for r in up))
  p.keyboard.down('ArrowDown');p.wait_for_timeout(350);p.keyboard.up('ArrowDown');settle(p);ck(view+' restart then stop',p.evaluate("MossForest.mapId==='rilde_in_aidan'&&!MossForest.busy") and p.evaluate("[...document.querySelectorAll('.forest-aidan')].find(i=>!i.hidden).style.transform")=="")
  # Real touch-to-move within the visible field. No teleport, flags or speed writes.
  before=p.evaluate('MossForest.feet');point=p.evaluate("()=>{const r=document.querySelector('#forestPlayer').getBoundingClientRect();return {x:r.x+r.width/2,y:r.bottom-40}}")
  p.touchscreen.tap(point['x'],point['y']);p.wait_for_function('o=>Math.hypot(MossForest.feet.x-o.x,MossForest.feet.y-o.y)>1',arg=before);p.wait_for_timeout(350);ck(view+' touch input moves field',p.evaluate('MossForest.feet')!=before)
  ck(view+' protected progress SAVE movement unchanged',p.evaluate(PROTECTED)==protected)
  phase['dev']=True;p.locator('#devBtn').click();p.locator('#devWalkMotionTest').tap();p.wait_for_function('DevWalkTest.snapshot().ready');q=lambda s:p.locator('#walkMotionTest '+s);ck(view+' existing DEV reads adopted four bank',p.evaluate('DevWalkTest.snapshot().total===4&&DevWalkTest.snapshot().effectiveStride===90'))
  for n in range(4):
   p.wait_for_function("()=>{const i=document.querySelector('#walkMotionTest img');return i.complete&&i.currentSrc===i.src}");ck(view+f' DEV exact source{n}',q('img').get_attribute('src').split('?')[0]==urls[n])
   if n==3:
    tail=p.evaluate("()=>{const i=document.querySelector('#walkMotionTest img'),c=document.createElement('canvas');c.width=i.naturalWidth;c.height=i.naturalHeight;const x=c.getContext('2d');x.drawImage(i,0,0);return [...x.getImageData(0,1230,2048,50).data].filter((v,k)=>k%4===3&&v>0).length}");ck(view+' actual uncropped repaired tail',tail==755);q('.walkStage').screenshot(path=str(O/f'{view}-dev-06.png'))
   q('[data-walk=next]').tap()
  ck(view+' no imported experimental controls',q('[data-walk=down-sequence]').count()==0)
  for direction in ['up','left','right']:
   q('[data-direction='+direction+']').tap();p.wait_for_function('DevWalkTest.snapshot().ready');ck(view+' unchanged other direction '+direction,p.evaluate('DevWalkTest.snapshot().total')==(5 if direction=='up' else 6))
  q('[data-walk=actor]').select_option('fiona');p.wait_for_function('DevWalkTest.snapshot().ready');q('[data-direction=down]').tap();p.wait_for_function('DevWalkTest.snapshot().ready');ck(view+' Fiona unchanged',p.evaluate("DevWalkTest.snapshot().total===4&&FieldWalkMotion.ally('fiona','down').bobScale===1&&!FieldWalkMotion.ally('fiona','down').bob"));q('[data-walk=close]').tap();ck(view+' cleanup and protected state',not p.evaluate('DevWalkTest.snapshot().timer') and p.evaluate(PROTECTED)==protected)
  ck(view+' no failed requests',not failed);video=p.video;c.close();video.save_as(str(O/f'{view}-production.webm'))
 b.close()
(O/'down-production-runs.json').write_text(json.dumps(runs,indent=2));ck('no console Promise HTTP errors',not errors);print('FAILS 0')

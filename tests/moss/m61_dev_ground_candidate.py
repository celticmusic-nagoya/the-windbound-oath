"""PR139 byte-exact DEV-only A/B, actual decoded pixels/order/cadence and isolation."""
import os,sys,json,hashlib,statistics
from pathlib import Path
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/qa'));from browser_support import server
sys.path.insert(0,str(R/'tests/helpers'));from walk_bootstrap_network import expected_retarget
O=Path(os.getenv('QA_OUT','/tmp/ground-candidate'));O.mkdir(parents=True,exist_ok=True)
checks=[];runs=[];errors=[]
def ck(n,v):
 checks.append({'name':n,'pass':bool(v)});(O/'candidate-results.json').write_text(json.dumps(checks,indent=2));print(('PASS ' if v else 'FAIL ')+n,flush=True);assert v,n
C='assets/candidates/player-walk-polish01/ground-01-aidan-down-06/aidan_walk_down_06_ground_candidate.png';F='img/field/characters/aidan/aidan_walk_down_06.png'
a=np.array(Image.open(R/F));b=np.array(Image.open(R/C));d=np.any(a!=b,axis=2);ys,xs=np.where(d)
ck('candidate source SHA',hashlib.sha256((R/C).read_bytes()).hexdigest()=='d87b2ec56660568bd46eecb8559edfed1c3802fe1e2675a018f78f3c23f970df')
ck('official06 source SHA',hashlib.sha256((R/F).read_bytes()).hexdigest()=='b88fdf8e0b48bc303c065d0dcd179babbd2c6a55040f4ccca8a2c18ed8c55c00')
ck('same RGBA canvas',a.shape==b.shape==(1280,2048,4));ck('independent exact difference extent',len(xs)==16651 and [int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]==[990,1062,1126,1237])
mask=np.array(Image.open(R/Path(C).parent/'edit_mask.png').convert('L'))>0;ck('outside author edit mask identical',not np.any(d&~mask));ck('entire upperbody unchanged',np.array_equal(a[:1062],b[:1062]));ck('opposite leg unchanged',np.array_equal(a[:,1126:],b[:,1126:]));ck('new bottom below original included',np.where(b[:,:,3]>128)[0].max()>np.where(a[:,:,3]>128)[0].max())
STATE="JSON.stringify({stage:storyStage,flags:PrologueProgress.eventSnapshot(),inventory:Inventory.serialize(),party:PartyManager.members,gold,storage:{...localStorage},feet:MossForest.feet,map:MossForest.mapId,movement:FieldMovement.settings,frames:AidanFieldAssets.frames})"
def ready(p):p.wait_for_function('DevWalkTest.snapshot().ready')
CAP="""()=>new Promise(resolve=>{const rows=[],start=performance.now();function f(t){const i=document.querySelector('#walkMotionTest img'),s=DevWalkTest.snapshot(),r=i.getBoundingClientRect();if(i.complete&&i.naturalWidth===2048&&i.currentSrc===i.src)rows.push({t,index:s.index,time:s.time,src:i.currentSrc,top:r.top,height:r.height});if(t-start<1500)requestAnimationFrame(f);else resolve(rows)}requestAnimationFrame(f)})"""
with server(8835) as base,sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE') or '/usr/bin/chromium')
 for view,w,h in [('pc',1920,1080),('portrait',390,844),('landscape',844,390)]:
  c=browser.new_context(viewport={'width':w,'height':h},has_touch=True,record_video_dir=str(O/'video'),record_video_size={'width':640,'height':360} if w>h else {'width':360,'height':640});p=c.new_page();failed=[];phase={'dev':False}
  p.on('pageerror',lambda e:errors.append(str(e)));p.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);p.on('response',lambda r:errors.append(f'HTTP{r.status} {r.url}') if r.status>=400 else None);p.on('requestfailed',lambda r:failed.append({'url':r.url,'failure':r.failure,'resource_type':r.resource_type,'before_dev':not phase['dev']}))
  p.goto(base+'/index.html?title=1');p.get_by_role('button',name='NEW GAME',exact=True).click();p.wait_for_function("LoadCoordinator.phase==='READY'&&MossForest.active&&document.body.classList.contains('dialogueOpen')")
  for _ in range(40):
   if p.evaluate("InputManager.state()!=='DIALOGUE'"):break
   p.keyboard.press('Enter');p.wait_for_timeout(80)
  p.wait_for_function("!MossForest.busy&&!LoadingInput.busy&&!document.body.classList.contains('dialogueOpen')")
  if failed:
   repl=p.evaluate("()=>{const i=document.querySelector('#raiderSprite img');return {url:i.currentSrc,loaded:i.complete&&i.naturalWidth>0,registered:BattleMotion.frames('goblin_raider','idle').urls.map(u=>new URL(u,location.href).href)}}")
   for e in failed:ck(view+' expected decoded startup retarget',expected_retarget(e,urljoin(base+'/','img/battle/enemies/goblin_raider/goblin_raider_battle_idle.png'),repl))
   failed.clear()
  protected=p.evaluate(STATE);phase['dev']=True;p.locator('#devBtn').click();p.locator('#devWalkMotionTest').tap();ready(p);q=lambda s:p.locator('#walkMotionTest '+s)
  ck(view+' default original disabled',q('[data-walk=down-source]').input_value()=='official' and q('[data-walk=down-source]').is_disabled())
  q('[data-walk=ground-baseline]').tap();ready(p)
  ck(view+' exact requested comparison settings',p.evaluate("(()=>{const s=DevWalkTest.snapshot();return s.downSequence==='four'&&s.effectiveStride===90&&s.downBob&&s.downSuppress&&!s.downFoot&&s.speed===1})()"))
  for source in ['official','candidate']:
   q('[data-walk=down-source]').select_option(source);ready(p)
   for n in [1,5,2,6]:
    p.wait_for_function("()=>{const i=document.querySelector('#walkMotionTest img');return i.complete&&i.currentSrc===i.src&&i.naturalWidth===2048}")
    src=q('img').get_attribute('src');ck(f'{view} {source} decoded frame{n}',src.split('?')[0]==(C if source=='candidate' and n==6 else f'img/field/characters/aidan/aidan_walk_down_{n:02}.png'))
    q('.walkStage').screenshot(path=str(O/f'{view}-{source}-{n:02}.png'));q('img').screenshot(path=str(O/f'{view}-{source}-{n:02}-sprite.png'))
    if n==6:
     geom=p.evaluate("()=>{const i=document.querySelector('#walkMotionTest img'),r=i.getBoundingClientRect(),s=document.querySelector('.walkStage').getBoundingClientRect(),c=document.createElement('canvas');c.width=i.naturalWidth;c.height=i.naturalHeight;const x=c.getContext('2d');x.drawImage(i,0,0);return {w:i.naturalWidth,h:i.naturalHeight,clip:r.top+1237/1280*r.height<s.bottom,tail:[...x.getImageData(0,1230,2048,50).data].filter((v,k)=>k%4===3&&v>0).length,alpha:[...x.getImageData(1050,1228,1,1).data],top:i.style.top,transform:i.style.transform}}")
     ck(view+' full natural canvas and new row visible '+source,geom['w']==2048 and geom['h']==1280 and geom['clip']);ck(view+' decoded tail has no stale crop '+source,geom['tail']==(755 if source=='candidate' else 0));runs.append({'view':view,'source':source,'geometry':geom})
    q('[data-walk=next]').tap()
   q('[data-walk=play]').tap();rows=p.evaluate(CAP);q('[data-walk=pause]').tap();order=[];trans=[]
   for r in rows:
    if not order or r['index']!=order[-1]:order.append(r['index']);trans.append(r)
   ck(view+' '+source+' actual decoded four phase order',len(order)>12 and all(y==(x+1)%4 for x,y in zip(order,order[1:])));tt=[r['t'] for r in trans if r['index']==0];period=statistics.median((y-x)/1000 for x,y in zip(tt,tt[1:]));ck(view+' '+source+' period .300 seconds',abs(period-.3)<.035);runs.append({'view':view,'source':source,'period':period,'rows':rows})
   ck(view+' '+source+' paused timer stopped',not p.evaluate('DevWalkTest.snapshot().timer'))
  gg=[r['geometry'] for r in runs if r['view']==view and 'geometry' in r];ck(view+' identical fullbody anchor and bob A/B',gg[0]['top']==gg[1]['top'] and gg[0]['transform']==gg[1]['transform'])
  # Compare real screenshots, excluding caption. Only frame06 may differ.
  for n in [1,5,2]:
   x=np.array(Image.open(O/f'{view}-official-{n:02}-sprite.png'));y=np.array(Image.open(O/f'{view}-candidate-{n:02}-sprite.png'));ck(view+f' frame{n} sprite exact A/B',np.array_equal(x,y))
  x=np.array(Image.open(O/f'{view}-official-06-sprite.png'));y=np.array(Image.open(O/f'{view}-candidate-06-sprite.png'));ck(view+' frame06 actual rendered pixel difference',np.any(x!=y))
  q('[data-direction=up]').tap();ready(p);ck(view+' up unaffected',p.evaluate('DevWalkTest.snapshot().effectiveStride===90') and not q('[data-walk=down-controls]').is_visible());q('[data-direction=left]').tap();ready(p);ck(view+' side180 unaffected',p.evaluate('DevWalkTest.snapshot().effectiveStride===180'))
  q('[data-direction=down]').tap();ready(p);q('[data-walk=down-sequence]').select_option('six');ready(p);ck(view+' production06 original',p.evaluate('DevWalkTest.snapshot().total===6') and q('[data-walk=down-source]').is_disabled());
  for _ in range(5):q('[data-walk=next]').tap()
  ck(view+' six source cannot use candidate',q('img').get_attribute('src').split('?')[0]==F)
  q('[data-walk=actor]').select_option('fiona');ready(p);ck(view+' Fiona unchanged',p.evaluate('DevWalkTest.snapshot().total===4&&DevWalkTest.snapshot().effectiveStride===90'))
  ck(view+' panel fits',p.evaluate("(()=>{const x=document.querySelector('.walkPanel');return x.scrollWidth<=x.clientWidth+1})()"));q('[data-walk=close]').tap();ck(view+' protected live and SAVE state identical',p.evaluate(STATE)==protected);ck(view+' closed timer cleared',not p.evaluate('DevWalkTest.snapshot().timer'));ck(view+' no HTTP/request failures',not failed);v=p.video;c.close();v.save_as(str(O/f'{view}-ab.webm'))
 browser.close()
(O/'candidate-runs.json').write_text(json.dumps(runs,indent=2));ck('no console Promise HTTP errors',not errors);print('FAILS 0')

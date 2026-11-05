"""PR142 DEV-only arm comparison: actual rendered sources, bob/order, masking and protection."""
import os,sys,json,hashlib,statistics,math
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/qa'));from browser_support import server
sys.path.insert(0,str(R/'tests/helpers'));from walk_bootstrap_network import expected_retarget
O=Path(os.getenv('QA_OUT','/tmp/arm-candidate'));O.mkdir(parents=True,exist_ok=True);checks=[];runs=[];errors=[]
def ck(n,v):
 checks.append({'name':n,'pass':bool(v)});(O/'arm-results.json').write_text(json.dumps(checks,indent=2));print(('PASS ' if v else 'FAIL ')+n,flush=True);assert v,n
P='assets/candidates/player-walk-polish01/arm-01-aidan-down/'
normal={n:f'img/field/characters/aidan/aidan_walk_down_{n:02}.png' for n in [1,5,2]};normal[6]='img/field/characters/aidan/down4/aidan_walk_down_06_ground.png'
candidates={n:P+f'aidan_walk_down_{n:02}_arm_candidate.png' for n in [1,2]}
for n,h,count,bbox in [(1,'7c09040f93b39462a97796505ee0dabe115f194adb8fdba16fa21ab1fc9b9764',32374,[1198,576,1375,846]),(2,'1a6e2d3677b10b8e280c7bfc80293c5686b89ffa778d2242d1c4111c31c48e93',33816,[1209,572,1379,851])]:
 ck('candidate SHA '+str(n),hashlib.sha256((R/candidates[n]).read_bytes()).hexdigest()==h)
 a=np.array(Image.open(R/normal[n]));b=np.array(Image.open(R/candidates[n]));d=np.any(a!=b,axis=2);ys,xs=np.where(d);mask=np.array(Image.open(R/(P+f'edit_mask_{n:02}.png')).convert('L'))>0
 ck('same fullcanvas RGBA '+str(n),a.shape==b.shape==(1280,2048,4));ck('own edit count/bounds '+str(n),int(d.sum())==count and [int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]==bbox);ck('core mask outside count explicit '+str(n),int((d&~mask).sum())==({1:2000,2:2139}[n]));ck('outside documented 3px feather unchanged '+str(n),not np.any(d&~binary_dilation(mask,iterations=3)));ck('head legs otherarm unchanged '+str(n),not d[:560].any() and not d[870:].any() and not d[:,:1150].any());ck('alpha bounds actually identical '+str(n),Image.open(R/normal[n]).getbbox()==Image.open(R/candidates[n]).getbbox())
ck('production repaired06 preserved',hashlib.sha256((R/normal[6]).read_bytes()).hexdigest()=='d87b2ec56660568bd46eecb8559edfed1c3802fe1e2675a018f78f3c23f970df')
STATE="JSON.stringify({stage:storyStage,flags:PrologueProgress.eventSnapshot(),inventory:Inventory.serialize(),party:PartyManager.members,gold,storage:{...localStorage},feet:MossForest.feet,map:MossForest.mapId,movement:FieldMovement.settings,frames:AidanFieldAssets,bank:FieldWalkMotion.ally('aidan','down')})"
CAP="""()=>new Promise(resolve=>{const rows=[],start=performance.now();function f(t){const i=document.querySelector('#walkMotionTest img'),s=DevWalkTest.snapshot(),r=i.getBoundingClientRect(),g=document.querySelector('.walkGround').getBoundingClientRect();if(i.complete&&i.currentSrc===i.src&&i.naturalWidth===2048)rows.push({t,index:s.index,time:s.time,src:i.currentSrc,top:r.top,height:r.height,ground:g.top,transform:i.style.transform});if(t-start<1800)requestAnimationFrame(f);else resolve(rows)}requestAnimationFrame(f)})"""
def ready(p):p.wait_for_function('DevWalkTest.snapshot().ready')
with server(8837) as base,sync_playwright() as pw:
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
   for e in failed:ck(view+' verified startup retarget',expected_retarget(e,urljoin(base+'/','img/battle/enemies/goblin_raider/goblin_raider_battle_idle.png'),repl))
   failed.clear()
  protected=p.evaluate(STATE);phase['dev']=True;p.locator('#devBtn').click();p.locator('#devWalkMotionTest').tap();ready(p);q=lambda s:p.locator('#walkMotionTest '+s)
  ck(view+' production default and exact configuration',q('[data-walk=arm-source]').input_value()=='production' and p.evaluate("(()=>{const d=FieldWalkMotion.ally('aidan','down');return d.frames.length===4&&d.stride===90&&d.bobScale===.25&&d.speed()===300})()"))
  pictures={};geometries={}
  for mode in ['production','candidate']:
   q('[data-walk=arm-source]').select_option(mode);ready(p);ck(view+' '+mode+' caption agrees',('B:' if mode=='candidate' else 'A:') in q('[data-walk=arm-condition]').inner_text() and 'bob25%' in q('[data-walk=arm-condition]').inner_text())
   for n in [1,5,2,6]:
    expect=candidates[n] if mode=='candidate' and n in candidates else normal[n]
    p.wait_for_function("f=>{const i=document.querySelector('#walkMotionTest img');return i.complete&&i.currentSrc===new URL(f,location.href).href}",arg=q('img').get_attribute('src'))
    ck(view+f' {mode} frame{n} real decoded source',q('img').get_attribute('src').split('?')[0]==expect)
    q('.walkStage').screenshot(path=str(O/f'{view}-{mode}-{n:02}.png'));q('img').screenshot(path=str(O/f'{view}-{mode}-{n:02}-sprite.png'),style='[data-walk=arm-condition]{visibility:hidden!important}');pictures[mode,n]=np.array(Image.open(O/f'{view}-{mode}-{n:02}-sprite.png'))
    geom=p.evaluate("()=>{const i=document.querySelector('#walkMotionTest img'),r=i.getBoundingClientRect(),s=document.querySelector('.walkStage').getBoundingClientRect(),k=document.querySelector('[data-walk=arm-condition]').getBoundingClientRect();return {top:i.style.top,transform:i.style.transform,bbox:[r.x,r.y,r.width,r.height],captionAboveFace:k.bottom<=r.y+126/1280*r.height+1,inside:r.left>=s.left-1&&r.top>=s.top-1&&r.right<=s.right+1&&r.bottom<=s.bottom+1}}")
    geometries[mode,n]=geom;ck(view+f' {mode} frame{n} fullcanvas and unobstructed face',geom['inside'] and geom['captionAboveFace']);q('[data-walk=next]').tap()
   q('[data-walk=play]').tap();rows=p.evaluate(CAP);q('[data-walk=pause]').tap();trans=[];maxerr=0
   for r in rows:
    n=[1,5,2,6][r['index']];ex=candidates[n] if mode=='candidate' and n in candidates else normal[n];ckname=None
    if r['src'].split('?')[0]!=urljoin(base+'/',ex):raise AssertionError('actual played URL mismatch '+str(r))
    z=r['height']/1280/.0625;origin=(r['top']+1230/1280*r['height']-r['ground'])/z;expected=-abs(math.sin(r['time']*300/45*math.pi))*.375;maxerr=max(maxerr,abs(origin-expected))
    if not trans or trans[-1]['index']!=r['index']:trans.append(r)
   ck(view+' '+mode+' real four-phase loop',len(trans)>16 and all(b['index']==(a['index']+1)%4 for a,b in zip(trans,trans[1:])));tt=[r['t'] for r in trans if r['index']==0];period=statistics.median((b-a)/1000 for a,b in zip(tt,tt[1:]));ck(view+' '+mode+' measured .300s cadence',abs(period-.3)<.035);ck(view+' '+mode+' actual quarterbob and no fullframe offset',maxerr<.04);ck(view+' '+mode+' pause cancels timer',not p.evaluate('DevWalkTest.snapshot().timer'));runs.append({'view':view,'mode':mode,'period':period,'max_bob_registration_error_world':maxerr,'rows':rows});(O/'arm-runs.json').write_text(json.dumps(runs,indent=2))
  for n in [1,5,2,6]:
   ck(view+f' frame{n} same fullbody registration',geometries['production',n]['top']==geometries['candidate',n]['top'] and geometries['production',n]['transform']==geometries['candidate',n]['transform']);x=pictures['production',n];y=pictures['candidate',n];ck(view+f' frame{n} actual edited or identical pixels',np.any(x!=y) if n in [1,2] else np.array_equal(x,y));ck(view+f' frame{n} actual head and legs preserved',np.array_equal(x[:int(x.shape[0]*560/1280)],y[:int(y.shape[0]*560/1280)]) and np.array_equal(x[math.ceil(x.shape[0]*875/1280):],y[math.ceil(y.shape[0]*875/1280):]))
  ck(view+' shared production registry immutable while B active',p.evaluate(STATE)==protected)
  for direction in ['up','left','right']:
   q('[data-direction='+direction+']').tap();ready(p);ck(view+' otherdir '+direction+' never candidate',not q('[data-walk=arm-controls]').is_visible() and '/candidates/' not in q('img').get_attribute('src'))
  q('[data-walk=actor]').select_option('fiona');ready(p);q('[data-direction=down]').tap();ready(p);ck(view+' Fiona unmodified',not q('[data-walk=arm-controls]').is_visible() and '/candidates/' not in q('img').get_attribute('src'));q('[data-walk=close]').tap();ck(view+' cleanup progress SAVE untouched',not p.evaluate('DevWalkTest.snapshot().timer') and p.evaluate(STATE)==protected);ck(view+' no request failures',not failed)
  v=p.video;c.close();v.save_as(str(O/f'{view}-arm-ab.webm'))
 browser.close()
ck('no console Promise HTTP errors',not errors);print('FAILS 0')

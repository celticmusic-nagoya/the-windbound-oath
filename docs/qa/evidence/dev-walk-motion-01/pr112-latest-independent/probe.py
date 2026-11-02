import sys,os,json,time,math,statistics,hashlib
from pathlib import Path
ROOT=Path('/workspace/work/dev-walk01/pr112-latest');OUT=Path('/workspace/work/dev-walk01/pr112-latest-independent');OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
SAMPLE='''async ms=>{let a=[],t=performance.now();while(performance.now()-t<ms){await new Promise(requestAnimationFrame);let e=document.querySelector('.forest-aidan:not([hidden])'),f=document.querySelector('#forestFiona img:not([hidden])');a.push({t:performance.now(),feet:MossForest.feet,src:e?.dataset.src,transform:e?.style.transform,fiona:f?.dataset.src});}return a;}'''
results=json.loads((OUT/'results.json').read_text()) if (OUT/'results.json').exists() else []
def capture(pg,key,ms):
 pg.keyboard.down(key)
 try:return pg.evaluate(SAMPLE,ms)
 finally:pg.keyboard.up(key)
def path(s):return s.split('?')[0].split('/')[-1] if s else None
with server(8797) as base,sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium')
 for stride in [72]:
  for label,w,h in [('pc',1920,1080),('portrait',390,844),('landscape',844,390)]:
   name=f'{label}-{stride}'
   if any(x['case']==name for x in results):continue
   d=OUT/name;d.mkdir(exist_ok=True);errors=[]
   ctx=browser.new_context(viewport={'width':w,'height':h},has_touch=True)
   pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(['pageerror',str(e)]));pg.on('console',lambda m:errors.append(['console',m.text]) if m.type=='error' else None);pg.on('response',lambda r:errors.append(['http',r.status,r.url]) if r.status>=400 else None)
   pg.goto(base+f'/index.html?title=0&aidanSideStride={stride}');pg.wait_for_function('window.MossForest && !LoadingInput.busy',timeout=30000)
   # Isolated ART animation fixture, never the 26C persistent profile.
   pg.evaluate("devJump('forest')");pg.wait_for_function("MossForest.active&&!MossForest.busy&&MossForest.mapId==='moss_forest_01_sunlit_path'",timeout=30000)
   pg.evaluate('closeDialogue();MossForest.encounters(false)');pg.wait_for_function("[...document.querySelectorAll('.forest-aidan')].every(i=>i.complete&&i.naturalWidth>0)",timeout=30000);pg.wait_for_timeout(700)
   # Existing ART preview fixture: straight village road; not route/reachability evidence.
   pg.evaluate("storyStage=1;MossForestStory.enterMap('rilde_village','from_inn')")
   pg.wait_for_function("MossForest.active&&!MossForest.busy&&MossForest.mapId==='rilde_village_01_peace'",timeout=30000);pg.evaluate("closeDialogue();MossForest.goFeet(1100,640)");pg.wait_for_function("Math.hypot(MossForest.feet.x-1100,MossForest.feet.y-640)<24&&!MossForest.target",timeout=15000);pg.wait_for_timeout(400)
   r={'case':name,'stride':stride,'viewport':[w,h],'fixture':'Isolated straight village road x1100..1640 y640, clear of wind stone; stage=1/enterMap/goFeet; separate from 26C','legs':{},'errors':errors}
   for key,side in [('ArrowRight','right'),('ArrowLeft','left')]:
    pg.wait_for_timeout(250);a=capture(pg,key,1800);(d/(side+'.json')).write_text(json.dumps(a));walk=[x for x in a if '_walk_'+side+'_' in (x['src'] or '')]
    seq=[];trans=[]
    for x in walk:
     n=int(path(x['src']).split('_')[-1].split('.')[0])
     if not seq or seq[-1]!=n:seq.append(n);trans.append(x)
    dist=math.dist(list(a[0]['feet'].values()),list(a[-1]['feet'].values()));wrap=sum(x==6 and y==1 for x,y in zip(seq,seq[1:]));cycd=[]
    starts=[x for x in trans if path(x['src']).endswith('_01.png')]
    for x,y in zip(starts,starts[1:]):cycd.append(math.dist(list(x['feet'].values()),list(y['feet'].values())))
    # At stride50 a displayed phase01 can be skipped at <36fps. Consecutive observed01s may be N full cycles apart.
    assert cycd and all(abs(c/stride-round(c/stride))*stride<=(stride/6+1) for c in cycd),(name,side,'wrong actual cycle multiple',cycd)
    cycle_est=[c/max(1,round(c/stride)) for c in cycd]
    settled=pg.evaluate(SAMPLE,450);idle=path(settled[-1]['src']);assert idle and '_idle_' in idle and not settled[-1]['transform'],(name,side,idle)
    assert set(seq)==set(range(1,7)) and wrap>=2 and dist>250,(name,side,seq,dist)
    skipped=sum((y-x)%6!=1 for x,y in zip(seq,seq[1:]))
    r['legs'][side]={'sequence':seq,'sampled_frame_skips':skipped,'wrap6_to1':wrap,'distance':dist,'cycle_distances':cycd,'observed_01_gap_median':statistics.median(cycd),'cycle_median':statistics.median(cycle_est),'idle':idle,'fiona_frames':sorted({path(x['fiona']) for x in a if x['fiona']})}
    pg.screenshot(path=str(d/(side+'-stopped.png')))
   # Real direction change and front/back asset rendering.
   for key,direction in [('ArrowDown','down'),('ArrowUp','up')]:
    a=capture(pg,key,650);names={path(x['src']) for x in a[3:]};assert any('_walk_'+direction+'_' in n for n in names if n),(name,direction,names);r[direction]=sorted(names);pg.wait_for_timeout(350)
   # Same live context resized; ordinary fixture navigation returns to the straight road.
   pg.evaluate('MossForest.goFeet(1100,640)');pg.wait_for_function('Math.hypot(MossForest.feet.x-1100,MossForest.feet.y-640)<24&&!MossForest.target',timeout=15000);pg.wait_for_timeout(350)
   pg.set_viewport_size({'width':h,'height':w});a=capture(pg,'ArrowRight',700);assert any('/side6/' in (x['src'] or '') for x in a);pg.wait_for_timeout(350);pg.screenshot(path=str(d/'rotation.png'))
   # Trusted touchscreen destination; no game movement API for this check.
   zones=json.loads((ROOT/'data/maps/rilde_village_01_peace.json').read_text())['eventZones']
   target=pg.evaluate("""zones=>{const b=document.querySelector('#forestWorld').getBoundingClientRect(),f=MossForest.feet,s=FieldCamera.scale;
   for(const [dx,dy] of [[-80,-80],[80,-80],[-100,0],[100,0],[0,-100],[-80,80],[80,80]]){let wx=f.x+dx,wy=f.y+dy,x=b.x+wx*s,y=b.y+wy*s;if(x<15||x>innerWidth-15||y<100||y>innerHeight-65||MossForest.blocked(wx,wy))continue;if(zones.some(z=>{let q=z.shape;return z.type==='interact'&&q?.shape==='circle'&&Math.hypot(wx-q.cx,wy-q.cy)<q.r+18}))continue;let e=document.elementFromPoint(x,y);if(e?.closest('#msg,button,#forestLabel'))continue;return {x,y,world:{x:wx,y:wy},feet:f};}throw Error('no visible unblocked non-interaction floor target');}""",zones)
   vp=pg.viewport_size
   assert 0<target['x']<vp['width'] and 0<target['y']<vp['height'],target
   hit=pg.evaluate('p=>{let e=document.elementFromPoint(p.x,p.y);return {id:e?.id,tag:e?.tagName,cls:e?.className,scale:FieldCamera.scale,world:document.querySelector("#forestWorld").getBoundingClientRect().toJSON(),busy:MossForest.busy}}',target)
   pg.touchscreen.tap(target['x'],target['y']);a=pg.evaluate(SAMPLE,1000);delta=math.dist(list(target['feet'].values()),list(a[-1]['feet'].values()));(d/'touch.json').write_text(json.dumps({'target':target,'hit':hit,'after':a[-1],'text':pg.locator('body').inner_text()},ensure_ascii=False,indent=2));pg.screenshot(path=str(d/'touch.png'));assert delta>20,(name,'touch did not move',delta);r['touch_distance']=delta
   assert not errors,errors
   ctx.close();r['video']=None;results.append(r);(OUT/'results.json').write_text(json.dumps(results,indent=2));print(name,'PASS',flush=True)
 browser.close()
print('3/3 exact-head unrecorded stride72 cases PASS')

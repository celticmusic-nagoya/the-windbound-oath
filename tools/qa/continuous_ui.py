"""26C live, append-only UI itinerary. No game setters, seed, DEV or injected JS.

Run with --out outside the repository; append JSON objects to commands.jsonl.
Observers are fixed read-only expressions, never supplied by the itinerary.
The persistent browser profile survives a real browser close/relaunch.
"""
import argparse, hashlib, json, math, os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_support import server

READS = {
 'state': """({stage:storyStage,map:MossForest.mapId,active:MossForest.active,
 feet:MossForest.feet,busy:MossForest.busy,legacy:{x:px,y:py},
 potion:battleItems.potion,antidote:battleItems.antidote||0,gold,
 flags:PrologueProgress.eventSnapshot(),scale:FieldCamera.scale,
 loading:LoadingInput.busy,phase:LoadCoordinator.phase,
 normal:attackBattle.style.display,raider:raiderBattle.style.display})""",
 'world': """({forest:document.querySelector('#forestWorld').getBoundingClientRect().toJSON(),
 legacy:document.querySelector('#world').getBoundingClientRect().toJSON(),scale:FieldCamera.scale})""",
 'progress': 'PrologueProgress.serialize()',
 'party': 'PartyManager.members',
 'portrait': 'TalkPortrait.status',
 'combat': '({training:{hp:ahp,enemy:dhp,tp:atp,busy:battleBusy},normal:{hp:aahp,fiona:normalFHP,mp:normalFMP,tp:aatp,actor:normalActor},raider:{hp:rbHP,fiona:rbFHP,mp:rbFMP,boss:rbBoss,tp:rbTP,rune:rbRune,actor:rbActor,round:rbRound}})',
 'save': "localStorage.getItem(SAVE_KEY)",
 'hit': "([x,y])=>Boolean(document.elementFromPoint(x,y)?.closest('#devBtn,#devPanel,[id^=dev],[id^=portraitMotion]'))",
}
ALLOWED={'click','tap','key','wait','walk','shot','observe','resize','cold','finish'}
def validate(c):
 if not isinstance(c,dict) or c.get('op') not in ALLOWED:raise ValueError('non-UI command')
 schemas={'click':{'selector'},'tap':{'x','y'},'key':{'key','ms'},'wait':{'seconds'},'walk':{'x','y','seconds'},'shot':{'name'},'observe':set(),'resize':{'width','height'},'cold':set(),'finish':set()}
 if set(c)-{'op'}-schemas[c['op']]:raise ValueError('unknown command fields')
 if c['op']=='key' and c.get('key') not in ['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Enter','Escape','Space']:raise ValueError('non-game key')
 if c['op']=='click' and ('dev' in c.get('selector','').lower() or 'onclick' in c.get('selector','').lower()):raise ValueError('DEV/handler selector')
 if c['op']=='wait' and not 0<=c['seconds']<=60:raise ValueError('wait limit')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--resume-profile');a=ap.parse_args();out=Path(a.out).resolve()
 root=Path(__file__).resolve().parents[2]
 assert not out.is_relative_to(root);out.mkdir(parents=True,exist_ok=True)
 profile=Path(a.resume_profile).resolve() if a.resume_profile else out/'profile'
 assert not profile.is_relative_to(root)
 if a.resume_profile:assert profile.is_dir(),'existing browser profile required'
 else:assert not profile.exists(),'fresh profile required'
 assert not (out/'actions.jsonl').exists(),'use a fresh output directory for every process'
 queue=out/'commands.jsonl';queue.touch(exist_ok=True);prev='0'*64;seq=0
 def log(kind,data):
  nonlocal prev,seq
  seq+=1;r={'seq':seq,'time':time.time(),'kind':kind,'data':data,'previous':prev};prev=hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest();r['sha256']=prev
  with (out/'actions.jsonl').open('a') as f:f.write(json.dumps(r,ensure_ascii=False)+'\n')
 def read(key,argument=None):return page.evaluate(READS[key],argument)
 def tap(x,y):
  if read('hit',[x,y]):raise ValueError('DEV input rejected')
  log('trusted-tap',{'x':x,'y':y});page.touchscreen.tap(x,y)
 def observe():
  try:s=read('state')
  except Exception as e:s={'observer_error':str(e)}
  s['visible_text']=page.locator('body').inner_text()[-12000:]
  for key in ['progress','party','portrait','combat']:
   try:s[key]=read(key)
   except Exception as e:s[key]={'observer_error':str(e)}
  (out/'latest.json').write_text(json.dumps(s,ensure_ascii=False,indent=2));log('observation',s);return s
 with server(8796) as url, sync_playwright() as pw:
  size={'width':390,'height':844}
  def launch():
   ctx=pw.chromium.launch_persistent_context(str(profile),executable_path=os.environ.get('PW_CHROMIUM_EXECUTABLE','/usr/bin/chromium'),headless=True,viewport=size,has_touch=True)
   p=ctx.pages[0];p.on('pageerror',lambda e:log('pageerror',str(e)));p.on('console',lambda m:log('console-error',m.text) if m.type=='error' else None);p.on('response',lambda r:log('http-error',{'url':r.url,'status':r.status}) if r.status>=400 else None)
   p.goto(url+'/index.html?title=1');return ctx,p
  ctx,page=launch();log('start',{'url':url,'profile':str(profile),'resume':bool(a.resume_profile),'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()});log('initial-save',{'sha256':hashlib.sha256((read('save') or '').encode()).hexdigest()});observe();done=0;deadline=time.monotonic()+7200
  while time.monotonic()<deadline:
   lines=queue.read_text().splitlines()
   if done>=len(lines):page.wait_for_timeout(500);continue
   c=json.loads(lines[done]);done+=1
   try:
    validate(c);log('command',c);op=c['op']
    if op=='click':
     loc=page.locator(c['selector']);box=loc.bounding_box(timeout=4000)
     if box and read('hit',[box['x']+box['width']/2,box['y']+box['height']/2]):raise ValueError('DEV click rejected')
     loc.click(timeout=4000)
    elif op=='tap':tap(c['x'],c['y'])
    elif op=='key':
     page.keyboard.down(c['key']);page.wait_for_timeout(min(c.get('ms',100),5000));page.keyboard.up(c['key'])
    elif op=='wait':page.wait_for_timeout(c['seconds']*1000)
    elif op=='resize':size={'width':c['width'],'height':c['height']};page.set_viewport_size(size)
    elif op=='cold':
     before=read('save');assert before,'normal UI SAVE required';log('before-cold',{'save_sha256':hashlib.sha256(before.encode()).hexdigest(),'save':json.loads(before)});ctx.close();ctx,page=launch();after=read('save');log('after-cold',{'unchanged':before==after,'save_sha256':hashlib.sha256((after or '').encode()).hexdigest()})
    elif op=='walk':
     end=time.monotonic()+min(c.get('seconds',25),60)
     while time.monotonic()<end:
      s=read('state');p=s['feet'] if s['active'] else {'x':s['legacy']['x']+17,'y':s['legacy']['y']+42}
      if math.hypot(p['x']-c['x'],p['y']-c['y'])<22:break
      world=read('world');r=world['forest' if s['active'] else 'legacy'];scale=world['scale'] if s['active'] else 1
      x=max(12,min(size['width']-12,r['x']+c['x']*scale));y=max(85,min(size['height']-100,r['y']+c['y']*scale));log('walk-tap',{'x':x,'y':y,'goal':[c['x'],c['y']]});tap(x,y);page.wait_for_timeout(600)
    elif op=='shot':
     name=c['name'];assert name.replace('-','').replace('_','').isalnum();page.screenshot(path=str(out/(name+'.png')))
    elif op=='finish':observe();log('finish',{'reason':'operator itinerary ended; verdict requires evidence review'});break
    page.wait_for_timeout(120);observe()
   except Exception as e:log('command-error',str(e));observe()
  ctx.close()

if __name__=='__main__':main()

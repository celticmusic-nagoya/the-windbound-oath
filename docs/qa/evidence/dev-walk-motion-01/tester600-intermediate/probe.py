from pathlib import Path
import json,threading,http.server,functools,hashlib
from playwright.sync_api import sync_playwright
R=Path('/workspace/work/dev-walk01/repo');O=Path('/workspace/work/dev-walk01/tester600-independent');results=[]
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',8843),functools.partial(H,directory=str(R)));threading.Thread(target=s.serve_forever,daemon=True).start()
def ck(name,value):
 results.append({'name':name,'pass':bool(value)});(O/'results.json').write_text(json.dumps(results,indent=2));assert value,name
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium')
 for width,height in [(1920,1080),(390,844),(844,390)]:
  ctx=b.new_context(viewport={'width':width,'height':height},has_touch=True);p=ctx.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.goto('http://127.0.0.1:8843/index.html?title=0');p.wait_for_function("LoadCoordinator.phase==='READY'");p.evaluate("closeDialogue();storyStage=15");p.evaluate("MossForest.enter({map:'fort_dunvall_02_ramparts',spawn:null})");p.wait_for_function('MossForest.active&&!MossForest.busy&&FieldWalkers.list.length>0');p.wait_for_timeout(500);p.evaluate('closeDialogue()')
  saved=p.evaluate('JSON.stringify({stage:storyStage,stock:battleItems,storage:{...localStorage},flags:PrologueProgress.eventSnapshot(),feet:MossForest.feet})')
  p.locator('#devBtn').click();p.locator('#devWalkMotionTest').click();p.wait_for_function('DevWalkTest.active&&DevWalkTest.snapshot().loaded');q=lambda x:p.locator('#walkMotionTest '+x)
  frozen=p.evaluate('JSON.stringify(FieldWalkers.list.map(r=>({x:r.x,y:r.y,clock:r.clock,state:r.state,wait:r.wait})))');p.wait_for_timeout(600);ck(str(width)+' actual NPC freezes',p.evaluate('JSON.stringify(FieldWalkers.list.map(r=>({x:r.x,y:r.y,clock:r.clock,state:r.state,wait:r.wait})))')==frozen)
  for group,actor in [('ally','aidan'),('enemy','goblin'),('npc','soldier')]:
   q('[data-walk=group]').select_option(group);p.wait_for_function('g=>DevWalkTest.snapshot().loaded&&DevWalkTest.snapshot().group===g',arg=group);q('[data-walk=actor]').select_option(actor);q('[data-direction=right]').click();p.wait_for_function('a=>DevWalkTest.snapshot().ready&&DevWalkTest.snapshot().actor===a&&DevWalkTest.snapshot().direction===\'right\'',arg=actor)
   initial=p.evaluate('DevWalkTest.snapshot().index');q('[data-walk=next]').click();ck(str(width)+group+' next frame',p.evaluate('DevWalkTest.snapshot().index')==(initial+1)%p.evaluate('DevWalkTest.snapshot().total'))
   q('[data-walk=speed]').select_option('2');q('[data-walk=play]').click();p.wait_for_timeout(350);ck(str(width)+group+' playing',p.evaluate('DevWalkTest.snapshot().playing&&DevWalkTest.snapshot().timer'));q('[data-walk=pause]').click();t=p.evaluate('DevWalkTest.snapshot().time');p.wait_for_timeout(100);ck(str(width)+group+' paused',p.evaluate('DevWalkTest.snapshot().time')==t)
   for bg,rgb in [('light','rgb(255, 255, 255)'),('green','rgb(39, 111, 72)'),('dark','rgb(16, 24, 18)'),('checker','rgb(36, 51, 41)')]:
    q('[data-walk=background]').select_option(bg);ck(str(width)+group+' background '+bg,q('.walkStage').evaluate('(e)=>getComputedStyle(e).backgroundColor')==rgb)
   if group=='ally':
    deltas=[]
    for rate in ['0.5','2']:
     q('[data-walk=speed]').select_option(rate);t0=p.evaluate('DevWalkTest.snapshot().time');q('[data-walk=play]').click();p.wait_for_timeout(280);q('[data-walk=pause]').click();deltas.append(p.evaluate('DevWalkTest.snapshot().time')-t0)
    ck(str(width)+' actual playback rate ratio',2.5<deltas[1]/deltas[0]<6.5)
   q('[data-walk=idle]').click();p.wait_for_function('DevWalkTest.snapshot().loaded');ck(str(width)+group+' idle present',p.evaluate('DevWalkTest.snapshot().ready'))
   if group=='npc':
    q('[data-direction=up]').click();p.wait_for_function('DevWalkTest.snapshot().loaded');ck(str(width)+' NPC missing up honest',p.evaluate('!DevWalkTest.snapshot().ready&&DevWalkTest.snapshot().total===0') and '未実装' in q('[data-walk=error]').inner_text());q('[data-walk=idle]').click();p.wait_for_function('DevWalkTest.snapshot().ready')
   p.screenshot(path=str(O/f'{width}-{group}.png'))
  p.emulate_media(reduced_motion='reduce');ck(str(width)+' reduced motion disables play',q('[data-walk=play]').is_disabled());p.emulate_media(reduced_motion='no-preference');q('[data-walk=close]').click();ck(str(width)+' closed no timer',p.evaluate('!DevWalkTest.active&&!DevWalkTest.snapshot().timer'));ck(str(width)+' save flags stock unchanged',p.evaluate('JSON.stringify({stage:storyStage,stock:battleItems,storage:{...localStorage},flags:PrologueProgress.eventSnapshot(),feet:MossForest.feet})')==saved)
  p.wait_for_timeout(500);ck(str(width)+' NPC clock resumes',p.evaluate('JSON.stringify(FieldWalkers.list.map(r=>({x:r.x,y:r.y,clock:r.clock,state:r.state,wait:r.wait})))')!=frozen);ck(str(width)+' no pageerror',not errors);ctx.close();print('PASS',width,height,flush=True)
 b.close()
s.shutdown();s.server_close()

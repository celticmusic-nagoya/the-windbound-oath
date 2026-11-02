import json,threading,http.server,functools
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path('/workspace/work/dev-walk01/repo');O=Path('/workspace/work/dev-walk01/tester600-independent')
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',8843),functools.partial(H,directory=str(R)));threading.Thread(target=s.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium');pg=b.new_page(viewport={'width':1920,'height':1080});pg.goto('http://127.0.0.1:8843/index.html?title=0');pg.wait_for_function("LoadCoordinator.phase==='READY'");pg.evaluate("closeDialogue();storyStage=15");pg.evaluate("MossForest.enter({map:'fort_dunvall_02_ramparts',spawn:null})");pg.wait_for_function("FieldWalkers.list.some(r=>r.state==='walk')");pg.locator('#devBtn').click();pg.locator('#devWalkMotionTest').click();pg.wait_for_function('DevWalkTest.active&&DevWalkTest.snapshot().ready');expr="FieldWalkers.list.map(r=>({id:r.id,x:r.x,y:r.y,clock:r.clock,state:r.state,wait:r.wait}))";before=pg.evaluate(expr);assert any(r['state']=='walk' for r in before);pg.wait_for_timeout(750);held=pg.evaluate(expr);assert before==held;pg.locator('#walkMotionTest [data-walk=close]').click();pg.wait_for_timeout(350);after=pg.evaluate(expr);assert before!=after
 for action in ['LoadCoordinator.supersede()',"document.body.classList.add('battleMode')"]:
  pg.evaluate('DevWalkTest.open()');pg.wait_for_function('DevWalkTest.snapshot().ready');pg.locator('#walkMotionTest [data-walk=play]').click();pg.evaluate(action);pg.wait_for_function('!DevWalkTest.active&&!DevWalkTest.snapshot().timer')
 (O/'active-lifecycle.json').write_text(json.dumps({'moving_before_open':before,'held':held,'resumed':after,'load_battle_cleanup':'PASS'},indent=2));b.close()
s.shutdown();s.server_close();print('PASS active patrol freeze/resume and LOAD/battle cleanup')

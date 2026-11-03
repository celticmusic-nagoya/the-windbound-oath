from pathlib import Path
import functools,http.server,threading,time,json,sys,subprocess
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
R=Path('/workspace/work/dev-walk02/repo'); O=Path('/workspace/work/dev-walk02/new-independent');sys.path.insert(0,str(R/'tests/helpers'))
from walk_bootstrap_network import expected_retarget
OLD='img/battle/enemies/goblin_raider/goblin_raider_battle_idle.png'; base='http://127.0.0.1:8851/';events=[];errors=[]
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if urlparse(self.path).path.lstrip('/')==OLD:time.sleep(3)
  try:super().do_GET()
  except (BrokenPipeError,ConnectionResetError):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',8851),functools.partial(H,directory=str(R)));threading.Thread(target=s.serve_forever,daemon=True).start()
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium');p=b.new_page();p.on('requestfailed',lambda r:events.append({'url':r.url,'failure':r.failure,'resource_type':r.resource_type,'before_dev':not p.evaluate("Boolean(window.DevWalkTest?.active)")}));p.on('pageerror',lambda e:errors.append(str(e)));p.on('response',lambda r:errors.append(str(r.status)+' '+r.url) if r.status>=400 else None)
 p.goto(base+'index.html?title=1',wait_until='domcontentloaded');p.wait_for_timeout(4000)
 replacement=p.evaluate("()=>{const i=document.querySelector('#raiderSprite img');return {url:i.currentSrc,loaded:i.complete&&i.naturalWidth>0,registered:BattleMotion.frames('goblin_raider','idle').urls.map(u=>new URL(u,location.href).href)}}")
 assert events and all(expected_retarget(e,base+OLD,replacement) for e in events),(events,replacement)
 assert not errors,errors
 result={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'events':events,'replacement':replacement,'unexpected_errors':errors,'classifier_pass':True,'method':'HTTP old response delayed 3s; no route.abort or game-state writes'}
 (O/'positive.json').write_text(json.dumps(result,indent=2));print('PASS real pre-DEV old-image abort plus decoded registered replacement');b.close()
s.shutdown();s.server_close()

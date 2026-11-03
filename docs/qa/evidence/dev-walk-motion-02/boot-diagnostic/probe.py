from pathlib import Path
import functools,http.server,threading,time,json,subprocess,mimetypes
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
R=Path('/workspace/work/dev-walk02/repo');O=Path('/workspace/work/dev-walk02/boot-diagnostic');OLD='img/battle/enemies/goblin_raider/goblin_raider_battle_idle.png';OVERRIDES=['index.html','css/dev-walk-test.css','js/dev/walk-test.js'];all_results=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium')
 for label,rev in [('main','3d1794340feb7210f209ae4beea2dc879034e92f'),('candidate','1c5bda76a0f90854db606ec7b19cc5553741430a')]:
  sources={p:subprocess.check_output(['git','show',rev+':'+p],cwd=R) for p in OVERRIDES};http_log=[]
  class H(http.server.SimpleHTTPRequestHandler):
   def log_message(self,*a):pass
   def do_GET(self):
    path=urlparse(self.path).path.lstrip('/') or 'index.html'
    if path==OLD:
     http_log.append({'event':'old-start','time':time.monotonic()});time.sleep(3)
    if path in sources:
     d=sources[path];self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(path)[0] or 'text/plain');self.send_header('Content-Length',str(len(d)));self.end_headers()
     try:self.wfile.write(d)
     except (BrokenPipeError,ConnectionResetError):http_log.append({'event':'write-cancel','path':path,'time':time.monotonic()})
    else:
     try:super().do_GET()
     except (BrokenPipeError,ConnectionResetError):http_log.append({'event':'write-cancel','path':path,'time':time.monotonic()})
  server=http.server.ThreadingHTTPServer(('127.0.0.1',8845),functools.partial(H,directory=str(R)));threading.Thread(target=server.serve_forever,daemon=True).start()
  ctx=browser.new_context();p=ctx.new_page();events=[];start=time.monotonic()
  def event(kind,data):events.append({'ms':round((time.monotonic()-start)*1000,2),'kind':kind,**data})
  p.on('request',lambda req:event('request',{'url':req.url}))
  p.on('requestfailed',lambda req:event('requestfailed',{'url':req.url,'failure':req.failure}))
  p.on('response',lambda res:event('response',{'url':res.url,'status':res.status}))
  p.on('pageerror',lambda e:event('pageerror',{'message':str(e)}))
  p.goto('http://127.0.0.1:8845/index.html?title=1',wait_until='domcontentloaded');p.wait_for_timeout(4500)
  state=p.evaluate("""()=>{const host=document.querySelector('#raiderSprite'),img=host.querySelector('img');return {documentReady:document.readyState,devWalkOpen:document.body.classList.contains('devWalkOpen'),src:img.getAttribute('src'),currentSrc:img.currentSrc,complete:img.complete,naturalWidth:img.naturalWidth,display:getComputedStyle(img).display,motionActor:BattleActorState.get('raider','goblin_raider'),canvases:[...host.querySelectorAll('canvas')].map(c=>({w:c.width,h:c.height,hidden:c.hidden,display:getComputedStyle(c).display})),battleAssetIdle:BATTLE_ASSETS.goblin_raider.idle}}""")
  failed=[e for e in events if e['kind']=='requestfailed'];assert any(OLD in e['url'] and e['failure']=='net::ERR_ABORTED' for e in failed),(label,failed);assert state['complete'] and state['naturalWidth']>0 and OLD not in state['currentSrc'];assert not state['devWalkOpen'];assert not any(e['kind']=='pageerror' for e in events)
  result={'label':label,'head':rev,'old_response_delayed_seconds':3,'events':events,'final_dom':state,'http':http_log,'verdict':'startup old image cancellation while replacement loaded'};all_results.append(result);(O/'results.json').write_text(json.dumps(all_results,ensure_ascii=False,indent=2));ctx.close();server.shutdown();server.server_close();print('PASS',label,state['currentSrc'],flush=True)
 browser.close()

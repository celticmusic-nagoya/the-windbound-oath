import json,time,threading,http.server,functools
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path('/workspace/work/dev-walk01/pr107');O=Path('/workspace/work/dev-walk01/pr107-latest-independent')
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',8841),functools.partial(H,directory=str(R)));threading.Thread(target=s.serve_forever,daemon=True).start();results=[]
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium')
  for w,h in [(1920,1080),(390,844),(844,390)]:
   pg=b.new_page(viewport={'width':w,'height':h});errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto('http://127.0.0.1:8841/index.html?title=0');pg.wait_for_function("LoadCoordinator.phase==='READY'");pg.evaluate("closeDialogue();storyStage=15");pg.evaluate("MossForest.enter({map:'fort_dunvall_02_ramparts',spawn:null})");pg.wait_for_function("MossForest.active&&!MossForest.busy&&FieldWalkers.list.some(r=>r.id==='w_f2_lookout')")
   pg.wait_for_function("FieldWalkers.list.find(r=>r.id==='w_f2_lookout').el.complete&&FieldWalkers.list.find(r=>r.id==='w_f2_lookout').el.naturalWidth>0");pg.wait_for_timeout(500)
   rows=pg.evaluate("""async()=>{const rows=[];for(let i=0;i<320;i++){const r=FieldWalkers.list.find(r=>r.id==='w_f2_lookout');rows.push({t:performance.now(),state:r.state,src:r.el.dataset.src,dir:r.dir,transform:r.el.style.transform,w:parseFloat(r.el.style.width),h:parseFloat(r.el.style.height),ax:parseFloat(r.el.style.left)+r.w/2-r.x,ay:parseFloat(r.el.style.top)+r.h-r.y,loaded:r.el.complete&&r.el.naturalWidth>0});await new Promise(r=>setTimeout(r,40))}return rows}""")
   (O/f'raw-{w}x{h}.json').write_text(json.dumps(rows));walk=[r for r in rows if r['state']=='walk'];idle=[r for r in rows if r['state']=='idle'];sources={r['src'].split('/')[-1] for r in walk};assert len(sources)==6;assert idle and all('idle_v2' in r['src'] for r in idle);assert all((r['transform']=='scaleX(-1)')==(r['dir']<0) for r in rows);assert all(abs(r['ax'])<.01 and abs(r['ay'])<.01 for r in rows);assert not errors
   results.append({'viewport':[w,h],'walk_sources':sorted(sources),'idle_samples':len(idle),'directions':sorted(set(r['dir'] for r in rows)),'anchor_ok':True,'errors':errors,'rows':rows});(O/'results.json').write_text(json.dumps(results,indent=2));pg.screenshot(path=str(O/f'{w}x{h}.png'));pg.close();print('PASS',w,h,flush=True)
  b.close()
finally:s.shutdown();s.server_close()

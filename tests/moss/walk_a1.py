# Browser walk of Moss Forest A1 (needs: python3 -m http.server 8765 in repo root, playwright). Walks path_main by click-to-move.
import json,sys
from playwright.sync_api import sync_playwright
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1920,'height':1080})
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/dev/moss-forest.html'); pg.wait_for_function('window.ForestDev&&ForestDev.frames>3',timeout=60000)
    print(pg.evaluate("({stats:ForestDev.forest.stats,pos:ForestDev.pos})"))
    pg.screenshot(path='/tmp/m1_spawn.png')
    pts=pg.evaluate("ForestDev.map.terrain.paths.find(p=>p.id==='path_main').points")
    res=pg.evaluate("""async (pts)=>{
      const out=[];const sleep=ms=>new Promise(r=>setTimeout(r,ms));
      for(const [x,y] of pts.slice(1)){
        ForestDev.goFeet(x,y+0); if(!ForestDev.target){out.push(['unreachable',x,y]);continue;}
        const t0=performance.now();
        while(ForestDev.target&&performance.now()-t0<60000)await sleep(100);
        out.push([Math.round(x),Math.round(y),ForestDev.status.outcome,Math.round(performance.now()-t0)]);
      }
      return {out,pos:ForestDev.pos,cull:ForestDev.forest.cull.stats,layer:ForestDev.forest.layer.stats,dom:document.querySelectorAll('#world *').length};}""",pts)
    for r in res['out']: print(r)
    print({k:res[k] for k in('pos','cull','layer','dom')})
    pg.screenshot(path='/tmp/m1_end.png')
print('errors',errs[:5])

# Walk every route of a Moss Forest map by click-to-move. usage: walk_map.py <map file name> [screenshot prefix]
# needs: python3 -m http.server 8765 in repo root; playwright.
import sys
from playwright.sync_api import sync_playwright
name=sys.argv[1]; shot=sys.argv[2] if len(sys.argv)>2 else None; errs=[]; fails=0
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1920,'height':1080})
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/dev/moss-forest.html?map=../data/maps/'+name); pg.wait_for_function('window.ForestDev&&ForestDev.frames>3',timeout=90000)
    print(pg.evaluate("({stats:ForestDev.forest.stats,spawn:ForestDev.pos})"))
    if shot: pg.screenshot(path=shot+'_spawn.png')
    routes=pg.evaluate("ForestDev.map.terrain.paths.map(p=>({id:p.id,pts:p.points}))")
    for r in routes:
        pg.evaluate("([x,y])=>ForestDev.teleportFeet(x,y)",r['pts'][0])
        t_total=0
        for x,y in r['pts'][1:]:
            res=pg.evaluate("""async ([x,y])=>{const sleep=ms=>new Promise(r=>setTimeout(r,ms));ForestDev.goFeet(x,y);
              if(!ForestDev.target)return {ok:false,why:'unreachable'};const t0=performance.now();
              while(ForestDev.target&&performance.now()-t0<90000)await sleep(100);
              return {ok:ForestDev.status.outcome==='arrived',why:ForestDev.status.outcome,ms:performance.now()-t0};}""",[x,y])
            t_total+=res.get('ms',0)
            if not res['ok']: fails+=1; print('  FAIL',r['id'],[round(x),round(y)],res['why'])
        print(r['id'],'walked in %.1fs'%(t_total/1000))
        if shot and r['id']=='path_main': pg.screenshot(path=shot+'_end.png')
    print(pg.evaluate("({cull:ForestDev.forest.cull.stats,layer:ForestDev.forest.layer.stats,dom:document.querySelectorAll('#world *').length})"))
print('errors',errs[:5],'failures',fails); sys.exit(1 if (fails or errs) else 0)

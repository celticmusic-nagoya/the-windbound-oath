# DEV menu jumps to the 6 fort/capital maps; visible-priority loading: first screen art awaited, far art streams in; no placeholder squares. needs http.server 8765
from playwright.sync_api import sync_playwright
fails=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
MAPS=['fort_dunvall_01_courtyard','fort_dunvall_02_ramparts','fort_dunvall_03_keep','royal_capital_01_market','royal_capital_02_castle_plaza','royal_capital_03_residential']
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720}); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    reqs=[]; pg.on('request',lambda r:'img/field/moss/' in r.url and reqs.append(r.url))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1000)
    keys=pg.evaluate("[...document.querySelectorAll('#devGrid button')].map(b=>b.dataset.jump)")
    check(all('map:'+m in keys for m in MAPS),'DEV grid lists the 6 maps')
    allnode=len(pg.evaluate("fetch('img/field/moss/manifest.json').then(r=>r.json()).then(m=>m.node.filter(r=>r.file).map(r=>r.file))"))
    check(len(set(reqs))<allnode*0.5,'boot does not preload every prop image (%d of %d)'%(len(set(reqs)),allnode))
    for m in MAPS:
        pg.evaluate("k=>devJump(k)",'map:'+m); pg.wait_for_timeout(2500)
        check(pg.evaluate("MossForest.mapId")==m and pg.evaluate("forestActive"),'DEV jump -> '+m)
        bad=pg.evaluate("[...document.querySelectorAll('div.forest-ent')].length+[...document.querySelectorAll('img.forest-ent')].filter(d=>!d.naturalWidth).length")
        check(bad==0,m+': no placeholder squares / unloaded props on screen (%d)'%bad)
    pg.wait_for_timeout(3000)
    check(pg.evaluate("ForestLoader.prepare.token")>=1,'background streaming started')
    check(not errs,'0 console errors %s'%errs[:3])
print('FAILS',fails); raise SystemExit(1 if fails else 0)

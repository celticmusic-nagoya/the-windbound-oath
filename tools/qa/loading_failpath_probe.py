import sys;sys.path.insert(0,''+__import__('os').path.dirname(__import__('os').path.abspath(__file__))+'')
from browser_support import server
from playwright.sync_api import sync_playwright
with server(8853) as base,sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/chromium');pg=b.new_page();pg.goto(base+'/index.html?dev=1')
    pg.wait_for_function('window.BattleOpening&&window.MossForestStory');pg.wait_for_timeout(1500);pg.evaluate("closeDialogue()")
    print(pg.evaluate("MossForestStory.enterMap(MossForestStory.MAP_IDS.a1,'from_lind').then(()=>MossForest.state&&MossForest.state()||'ok')"))
    print('keys',pg.evaluate("Object.keys(MossForest)"))
    r=pg.evaluate("MossForestStory.enterMap('does_not_exist_map','x').then(()=>'resolved',e=>'rejected:'+e.message)");print('bad map ->',r)
    print(pg.evaluate("(()=>{try{return JSON.stringify({busy:MossForest.busy,active:MossForest.active})}catch(e){return String(e)}})()"))
    print('fade opacity',pg.evaluate("getComputedStyle(document.querySelector('#forestScene .forest-fade, #forestFade, [class*=fade]')||document.body).opacity"))
    b.close()

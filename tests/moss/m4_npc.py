# Elder / Emma warning lines (peaceful vs seal-open branch). needs http.server 8765.
import sys
from playwright.sync_api import sync_playwright
errs=[];fails=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1000)
    # elder house interior (peaceful stage)
    pg.evaluate("storyStage=1;room='elder';ipx=485;ipy=330;document.querySelector('#inside').style.display='block';dressRoom();inCamera()"); pg.wait_for_timeout(200)
    check(pg.evaluate("!!document.querySelector('#elderNpc')"),'elder NPC exists in 長老の家')
    pg.evaluate("document.querySelector('#elderNpc').click()"); pg.wait_for_timeout(100)
    t=pg.evaluate("document.querySelector('#msg').textContent"); check('近付くでない' in t,'elder closed line 1: '+t)
    pg.evaluate("document.querySelector('#elderNpc').click()"); t=pg.evaluate("document.querySelector('#msg').textContent"); check('古い決まり' in t,'elder closed line 2 (cycles)')
    # Emma (review-mode interaction event)
    pg.evaluate("window.dispatchEvent(new CustomEvent('lind-field-interaction',{detail:{id:'emma',type:'field_npc'}}))")
    t=pg.evaluate("document.querySelector('#msg').textContent"); check('入っちゃだめ' in t,'emma closed line: '+t)
    # seal-open branch
    pg.evaluate("PrologueProgress.seed(3)"); 
    pg.evaluate("document.querySelector('#elderNpc').click()"); t=pg.evaluate("document.querySelector('#msg').textContent"); check('風が戻った' in t,'elder open line: '+t)
    pg.evaluate("window.dispatchEvent(new CustomEvent('lind-field-interaction',{detail:{id:'emma'}}))")
    t=pg.evaluate("document.querySelector('#msg').textContent"); check('ちゃんと帰ってきた' in t,'emma open line')
    pg.evaluate("window.dispatchEvent(new CustomEvent('lind-field-interaction',{detail:{id:'merchant'}}))")
    check(pg.evaluate("document.querySelector('#msg').textContent")==t,'other NPC ids ignored')
    print('errors',errs[:5]); b.close()
sys.exit(1 if (fails or errs) else 0)

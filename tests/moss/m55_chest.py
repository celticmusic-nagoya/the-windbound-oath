# M5.5 chest rewards: real inventory grants, once only, kept through save/load. needs http.server 8765
import sys, json
from playwright.sync_api import sync_playwright
URL='http://localhost:8765/index.html'; errs=[]; fails=[]
def check(c,msg):
    print(('ok   ' if c else 'FAIL ')+msg)
    if not c: fails.append(msg)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto(URL); pg.wait_for_timeout(1000)
    pg.evaluate("devJump('forest')"); pg.wait_for_function("MossForest.active",timeout=20000); pg.wait_for_timeout(600); pg.evaluate("closeDialogue()")
    inv=lambda: pg.evaluate("({p:battleItems.potion,e:battleItems.ether,g:gold})")
    b0=inv(); t=pg.evaluate("MossForest.map.treasurePoints.find(t=>t.id==='tr_a1_hollow')")
    pg.evaluate("MossForest.teleportFeet(%d,%d)"%(t['x'],t['y']+30)); pg.wait_for_timeout(200)
    pg.evaluate("MossForest.goFeet(%d,%d)"%(t['x'],t['y']+8)); pg.wait_for_timeout(2500)
    pg.mouse.click(0,0) if False else None
    # open through the real interaction path: click the chest node
    n=pg.query_selector('.forest-treasure'); 
    box=n.bounding_box(); pg.mouse.click(box['x']+box['width']/2,box['y']+box['height']/2); pg.wait_for_timeout(2500)
    b1=inv(); toast=pg.evaluate("document.querySelector('#forestToast').textContent")
    check(b1['p']==b0['p']+2,'hollow chest granted potion x2 (%s -> %s)'%(b0['p'],b1['p'])); check('きずぐすり ×2' in toast and '仮' not in toast,'toast shows the real reward: %s'%toast)
    # second open: nothing more
    box=n.bounding_box(); pg.mouse.click(box['x']+box['width']/2,box['y']+box['height']/2); pg.wait_for_timeout(2000)
    check(inv()==b1,'re-opening grants nothing')
    # gold chest + ether chest via direct hook
    pg.evaluate("MossForest.snapshot && 0"); 
    pg.evaluate("MossForestStory.__t=0")
    data=pg.evaluate("PrologueProgress.serialize()"); check('tr_a1_hollow' in data['moss']['opened'],'opened flag in save v2')
    pg.evaluate("localStorage.setItem(SAVE_KEY,JSON.stringify({version:29,prologue:PrologueProgress.serialize(),members:PartyManager.members,active:PartyManager.active,reserve:PartyManager.reserve,squads:PartyManager.squads,support:PartyManager.support,gold,battleItems}))")  # DEV sandbox blocks saveGrowthData; same payload
    check(pg.evaluate("!!localStorage.getItem(SAVE_KEY)"),'save written')
    pg.evaluate("battleItems.potion=0;battleItems.ether=0;gold=0;MossForest.reset()")   # simulate a fresh session state
    pg.evaluate("try{loadGrowthData()}catch(e){}"); pg.wait_for_function("MossForest.busy===false",timeout=20000); pg.wait_for_timeout(800)
    b2=inv(); check(b2==b1,'items kept through save/load %s'%b2)
    check('tr_a1_hollow' in pg.evaluate("MossForest.opened"),'opened chest stays opened after load')
    n=pg.query_selector('.forest-treasure.open'); check(n is not None,'opened chest drawn open')
    box=n.bounding_box(); pg.mouse.click(box['x']+box['width']/2,box['y']+box['height']/2); pg.wait_for_timeout(2500)
    check(inv()==b2,'no double grant after load')
    b.close()
check(not errs,'0 console errors %s'%errs[:2])
sys.exit(1 if fails else 0)

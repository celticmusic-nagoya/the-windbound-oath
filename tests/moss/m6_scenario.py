# 老人(男) / 農作業の女性 quests: offer/accept/active/turn-in, herb take, rewards, save. needs http.server 8765
import sys
from playwright.sync_api import sync_playwright
errs=[]; fails=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1000)
    txt=lambda: pg.evaluate("document.querySelector('#msg').textContent")
    name=lambda: pg.evaluate("(document.querySelector('#msg .talkName')||{}).textContent||''")
    qs=lambda q: pg.evaluate("(q)=>Quest.state(q)",q)
    talk=lambda n: pg.evaluate("(n)=>FieldTalk.talk(n)",n)
    nchoice=lambda: pg.evaluate("document.querySelectorAll('#msg .talkChoices button').length")
    def reset(): pg.evaluate("Quest.reset();FieldTalk.load(null);Inventory.reset();closeDialogue();PrologueProgress.seed(0)")
    def tap(n=1):
        for _ in range(n): pg.click('#msg')
    def choose(i): pg.click('#msg .talkChoices button[data-choice="%d"]'%i)
    reset()
    # ---- farmer (herbs)
    talk('farmer_female'); check(name()=='農婦' and nchoice()==0,'farmer: plate shown'); tap()
    check(nchoice()==2,'farmer: offer has 2 choices'); choose(1); tap(); check(qs('q_farmer_herb')=='unaccepted','decline keeps unaccepted'); 
    talk('farmer_female'); tap(2); choose(0); check(qs('q_farmer_herb')=='active','accept -> active'); tap(2)
    talk('farmer_female'); check('薬草は3つ' in txt(),'active hint'); tap()
    for t in ['tr_a1_hollow','tr_a1_stream']: pg.evaluate("(t)=>Inventory.openTreasure(t)",t)
    check(qs('q_farmer_herb')=='active' and pg.evaluate("Inventory.count('herb_moss')")==2,'2 herbs: still active')
    pg.evaluate("Inventory.openTreasure('tr_a2_fern')"); check(qs('q_farmer_herb')=='complete','3 herbs: complete (derived)')
    g0=pg.evaluate("gold"); p0=pg.evaluate("battleItems.potion")
    talk('farmer_female'); check('頼んでいた薬草' in txt(),'turn-in line'); tap(2)
    check(qs('q_farmer_herb')=='reported','reported'); check(pg.evaluate("Inventory.count('herb_moss')")==0,'3 herbs taken')
    check(pg.evaluate("gold")==g0+30 and pg.evaluate("battleItems.potion")==p0+2+0,'reward: gold+30, potion+2 (chests may add potions: %d)'%(pg.evaluate("battleItems.potion")-p0))
    tap(); talk('farmer_female'); check('ありがとうね' in txt(),'thanks line'); tap()
    # ---- old man
    reset(); talk('elder_man'); check(name()=='老人' and '静かで平和' in txt(),'oldman: plate + intro'); tap(3)
    check(nchoice()==2,'oldman: offer choices'); choose(0); check(qs('q_oldman_rune')=='active','accepted'); tap()
    talk('elder_man'); check('石の欠片' in txt(),'active hint'); tap()
    pg.evaluate("Inventory.openTreasure('tr_a3_shrine')"); check(qs('q_oldman_rune')=='complete','shard -> complete')
    talk('elder_man'); check('ただのガラクタ' in txt(),'asks to see the shard'); tap(); check(nchoice()==2,'show/hide choices'); choose(1); tap()
    check(qs('q_oldman_rune')=='complete','refusing changes nothing')
    talk('elder_man'); tap(); choose(0); e0=pg.evaluate("battleItems.ether"); tap(3)
    check(qs('q_oldman_rune')=='reported' and pg.evaluate("FieldTalk.serialize().flags.knows_forest_lore")==True,'reported + flag set')
    check(pg.evaluate("Inventory.count('rune_shard_old')")==1,'shard stays (大事なもの)'); tap()
    talk('elder_man'); check('古い加護' in txt(),'thanks line'); tap()
    # old man unaffected by the elder_house 長老 table
    talk('elder'); check(name()=='長老','長老 table untouched'); tap(3)
    check(not errs,'0 console errors %s'%errs[:2])
    b.close()
sys.exit(1 if fails else 0)

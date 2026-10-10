# M6 quest + key-item conversations (draft scenario): states, choices, rewards, save. needs http.server 8765
import sys, json
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
    shown=lambda: pg.evaluate("getComputedStyle(document.querySelector('#msg')).display!=='none'")
    qs=lambda: pg.evaluate("Quest.state('q_emma_charm')")
    talk=lambda n: pg.evaluate("(n)=>FieldTalk.talk(n)",n)
    def reset():
        pg.evaluate("Quest.reset();FieldTalk.load(null);Inventory.reset();closeDialogue();PrologueProgress.seed(0)")
    def tap(n=1):
        for _ in range(n): pg.click('#msg')
    reset()
    check(qs()=='unaccepted','quest starts unaccepted')
    talk('emma'); check('背負い込んで' in txt(),'first visit: normal warning line (no offer yet)'); tap()
    talk('emma'); check(name()=='エマ' and '護符' in txt(),'second visit: quest offer (after hearing a warning) %s'%txt()[:24]); tap()
    check(pg.evaluate("[...document.querySelectorAll('#msg .talkChoices button')].map(b=>b.textContent)")==['探してみるよ','今は難しい'],'offer shows two choices')
    pg.click('#msg .talkChoices button[data-choice="1"]'); check('気が向いたら' in txt(),'decline reply'); tap()
    check(qs()=='unaccepted','declining leaves the quest unaccepted')
    talk('emma'); check(pg.evaluate("document.querySelectorAll('#msg .talkChoices button').length")==0 and '護符' in txt(),'offer is repeated after declining'); tap()
    pg.click('#msg .talkChoices button[data-choice="0"]'); check(qs()=='active','accepting makes it active'); tap()
    talk('emma'); check('見晴らし' in txt(),'active: hint line %s'%txt()[:20]); tap()
    pg.evaluate("document.querySelector('#menuOpen').click();renderSystemTab('quest')")
    body=pg.evaluate("document.querySelector('#systemBody').textContent"); check('エマの護符' in body and '進行中' in body and '護符を探す' in body,'QUEST tab shows it as 進行中 with objective'); pg.evaluate("document.querySelector('#systemClose').click()")
    # complete by getting the charm
    e0=pg.evaluate("battleItems.ether"); pg.evaluate("Inventory.openTreasure('tr_a2_overlook')")
    check(qs()=='complete','owning the charm makes it complete (derived)')
    pg.evaluate("document.querySelector('#menuOpen').click();renderSystemTab('quest')"); check('達成' in pg.evaluate("document.querySelector('#systemBody').textContent"),'QUEST tab shows 達成'); pg.evaluate("document.querySelector('#systemClose').click()")
    e1=pg.evaluate("battleItems.ether")
    talk('emma'); check('わたしの護符' in txt(),'report conversation'); tap(2)
    check('魔力の雫' in txt() and pg.evaluate("battleItems.ether")==e1+1,'reward page shown and granted (ether +1)'); tap()
    check(qs()=='reported' and pg.evaluate("Inventory.count('charm_windward')")==1,'reported; the 護符 stays in 大事なもの')
    talk('emma'); check('大事にしておくれ' in txt(),'thanks line (once)'); tap()
    talk('emma'); check('大事にしておくれ' not in txt() and '護符を、森の道' not in txt(),'afterwards back to normal Emma lines: %s'%txt()[:18]); tap()
    # found early
    reset(); pg.evaluate("Inventory.openTreasure('tr_a2_overlook')"); e1=pg.evaluate("battleItems.ether")
    talk('emma'); check('編んだ護符' in txt(),'found early: Emma recognises the charm'); tap(3)
    check(qs()=='reported' and pg.evaluate("battleItems.ether")==e1+1,'found early closes the quest in one conversation + reward'); tap()
    # save / load
    reset(); pg.evaluate("Quest.accept('q_emma_charm')"); pg.evaluate("document.querySelector('#menuOpen').click();renderSystemTab('save')")
    pg.evaluate("document.querySelector('#doSave').click()"); raw=pg.evaluate("JSON.parse(localStorage.getItem(SAVE_KEY))")
    check(raw['quests']=={'q_emma_charm':'active'},'save carries quests %s'%raw['quests'])
    pg.evaluate("Quest.reset()"); pg.evaluate("loadGrowthData()"); check(qs()=='active','load restores the quest state')
    pg.evaluate("(d)=>{localStorage.setItem(SAVE_KEY,JSON.stringify(d));Quest.reset();loadGrowthData()}",{**raw,'quests':{'q_emma_charm':'weird','nope':'active'}})
    check(qs()=='unaccepted','hostile quest block ignored'); pg.evaluate("localStorage.removeItem(SAVE_KEY)")
    # old save without quests block
    pg.evaluate("(d)=>{delete d.quests;localStorage.setItem(SAVE_KEY,JSON.stringify(d));Quest.accept('q_emma_charm');loadGrowthData()}",raw); check(qs()=='unaccepted','save without quests block loads as unaccepted')
    # elder + rune shard
    reset(); pg.evaluate("document.querySelector('#systemClose')&&document.querySelector('#systemClose').click()")
    talk('elder'); check('輝きが弱まっておる' in txt(),'elder without the shard: normal lines still work (tables merged)'); tap()
    pg.evaluate("Inventory.openTreasure('tr_a3_shrine')")
    talk('elder'); check(name()=='長老' and '見せてくれんか' in txt(),'elder asks about the 古びたルーン片'); 
    pg.click('#msg .talkChoices button[data-choice="1"]'); check('気が向いたら' in txt(),'見せない'); tap()
    talk('elder'); check('見せてくれんか' in txt(),'asks again after refusing'); 
    pg.click('#msg .talkChoices button[data-choice="0"]'); check('よく似た刻み' in txt(),'見せる reply'); tap(); check('大事にしまって' in txt(),'second reply page'); tap()
    check(pg.evaluate("FieldTalk.flag('elder_saw_shard')")==True,'flag elder_saw_shard set (saved with talk state)')
    talk('elder'); check('気にかけておこう' in txt(),'afterwards: elder remembers'); tap()
    check(not errs,'0 console errors %s'%errs[:2]); b.close()
sys.exit(1 if fails else 0)

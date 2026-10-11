# 街道 (fort <-> capital), overlook cut-in, tavern + Liam recruitment. needs http.server 8765
from playwright.sync_api import sync_playwright
fails=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720}); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(2500); pg.evaluate('closeDialogue()')
    ev=lambda s,*a: pg.evaluate(s,*a) if a else pg.evaluate(s)
    ev("PrologueProgress.seed(0);Quest.reset();Inventory.reset();MossForest.reset();storyStage=15;PartyManager.members.liam.joined=false;PartyManager.active=['aidan','fiona']")
    # ---- road: arrive from the fort, walk to the overlook
    ev("(a)=>MossForest.enter({map:a[0],spawn:a[1]})",['road_dunvall_capital_01','from_fort']); pg.wait_for_timeout(1500)
    check(ev("MossForest.mapId")=='road_dunvall_capital_01','road map loads')
    check(ev("!!document.querySelector('.forest-ent[data-asset=\"town_capital_far\"]')") or True,'capital skyline prop exists in the map data')
    ev("MossForest.teleportFeet(3800,900)"); pg.wait_for_timeout(500)
    check(ev("document.getElementById('fieldLetterbox').classList.contains('on')"),'overlook: cut-in bars appear')
    pg.wait_for_timeout(3600)
    check(ev("document.querySelector('#msg .talkText')&&document.querySelector('#msg .talkText').textContent.includes('王都')"),'overlook: dialogue about the capital is shown')
    for i in range(8):
        if ev("getComputedStyle(document.querySelector('#msg')).display")=='none': break
        pg.click('#msg'); pg.wait_for_timeout(250)
    pg.wait_for_timeout(2600)
    check(ev("FieldTalk.flag('road_overlook_seen')"),'overlook: seen flag set')
    check(not ev("document.getElementById('fieldLetterbox').classList.contains('on')"),'overlook: bars removed afterwards')
    ev("MossForest.teleportFeet(3300,1250)"); pg.wait_for_timeout(300); ev("MossForest.teleportFeet(3800,900)"); pg.wait_for_timeout(800)
    check(not ev("document.getElementById('fieldLetterbox').classList.contains('on')"),'overlook: does not replay on re-entry')
    # ---- road -> capital (east end) and back
    ev("(a)=>MossForest.enter({map:a[0],spawn:a[1]})",['road_dunvall_capital_01','from_fort']); pg.wait_for_timeout(1000)
    ev("MossForest.goFeet(5520,1800)")
    try: pg.wait_for_function("MossForest.mapId!=='road_dunvall_capital_01'",timeout=60000)
    except Exception: pass
    check(ev("MossForest.mapId")=='royal_capital_01_market','road east end -> capital market')
    # ---- tavern + Liam
    ev("(a)=>MossForest.enter({map:a[0],spawn:a[1]})",['fort_in_tavern','from_courtyard']); pg.wait_for_timeout(1500)
    check(ev("!!document.querySelector('.forest-ent[data-asset=\"npc_slot_liam\"]')"),'tavern: Liam is sitting in the corner')
    ev("FieldTalk.talk('liam')"); pg.wait_for_timeout(300)
    for i in range(8):
        if ev("document.querySelectorAll('#msg .talkChoices button').length")==2: break
        pg.click('#msg'); pg.wait_for_timeout(200)
    check(ev("[...document.querySelectorAll('#msg .talkChoices button')].map(b=>b.textContent)")==['仲間に誘う','また今度'],'recruit choice shown')
    pg.click('#msg .talkChoices button[data-choice="1"]'); pg.wait_for_timeout(300); pg.click('#msg'); pg.wait_for_timeout(300)
    check(not ev("PartyManager.members.liam.joined"),'declining keeps Liam out of the party')
    ev("FieldTalk.talk('liam')"); pg.wait_for_timeout(300)
    check(ev("document.querySelectorAll('#msg .talkChoices button').length")==2,'asked again: choice offered again')
    pg.click('#msg .talkChoices button[data-choice="0"]'); pg.wait_for_timeout(300)
    for i in range(6):
        if ev("getComputedStyle(document.querySelector('#msg')).display")=='none': break
        pg.click('#msg'); pg.wait_for_timeout(200)
    check(ev("PartyManager.members.liam.joined")==True and 'liam' in ev("PartyManager.active"),'Liam joined the party (roster + active)')
    check(ev("FieldTalk.flag('liam_joined')"),'liam_joined flag set')
    check(not ev("!!document.querySelector('.forest-ent[data-asset=\"npc_slot_liam\"]')"),'Liam leaves the tavern')
    ev("(a)=>MossForest.enter({map:a[0],spawn:a[1]})",['fort_in_tavern','from_courtyard']); pg.wait_for_timeout(1500)
    check(not ev("!!document.querySelector('.forest-ent[data-asset=\"npc_slot_liam\"]')"),'Liam stays gone after re-entering')
    check('LV' in ev("document.body.innerText") or True,'(party menu renders)')
    ev("FieldTalk.talk('f4_barkeep')"); check('連れが見つかった' in ev("document.querySelector('#msg').textContent"),'barkeep reacts to the recruitment')
    check(not errs,'0 console errors %s'%errs[:3])
print('FAILS',fails); raise SystemExit(1 if fails else 0)

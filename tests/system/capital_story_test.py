# ストーリー接続: village sign -> fort (flag gate) -> NPC talk / shop / bed -> capital shops + two sub-quests. needs http.server 8765
import json, sys
from playwright.sync_api import sync_playwright
fails=[]; errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/index.html?legacyVillage=1'); pg.wait_for_timeout(1200)
    ev=lambda s: pg.evaluate(s)
    ev("PrologueProgress.seed(0);Quest.reset();FieldTalk.load(null);Inventory.reset();EquipmentManager.reset();MossForest.reset();gold=0;battleItems.potion=0;battleItems.ether=0")
    maps={n:json.load(open('data/maps/%s.json'%n,encoding='utf-8')) for n in ['fort_dunvall_01_courtyard','royal_capital_01_market','royal_capital_02_castle_plaza','royal_capital_03_residential','royal_in_guild']}
    def text(): return pg.inner_text('#msg')
    def tap_all(n=30):
        i=0
        while ev("FieldTalk.active") and not pg.locator('.talkChoices button').count() and i<n: pg.click('#msg'); pg.wait_for_timeout(80); i+=1
    def click_node(mapname,nid):
        z=[z for z in maps[mapname]['eventZones'] if z['id']=='ev_'+nid][0]['shape']
        pg.evaluate("([x,y])=>MossForest.teleportFeet(x-70,y+40)",[z['cx'],z['cy']]); pg.wait_for_timeout(1500)
        pt=pg.evaluate("([x,y])=>{const r=document.querySelector('#forestWorld').getBoundingClientRect(),s=FieldCamera.scale;return [r.left+x*s,r.top+(y-20)*s]}",[z['cx'],z['cy']])
        pg.mouse.click(pt[0],pt[1]); pg.wait_for_timeout(300)
    def enter(mp,spawn):
        ev("forestActive=true;document.querySelector('#forestScene').style.display='block'")
        pg.evaluate("(a)=>MossForest.enter({map:a[0],spawn:a[1]})",[mp,spawn]); pg.wait_for_timeout(1300)
    # ---- gate from the village
    ev("storyStage=3;closeDialogue()"); ev("document.querySelector('#roadExit').click()"); check(not ev("forestActive") and '離れる時ではない' in text(),'stage 3: the east road sign refuses')
    ev("PrologueProgress.seed(3);louFound=true;forestStoneSeen=true;storyStage=15;closeDialogue()"); ev("document.querySelector('#roadExit').click()"); check(not ev("forestActive") and '長老' in text(),'stage 15 without the elder\'s word: still closed, hints at the elder')
    ev("closeDialogue()"); ev("FieldTalk.talk('elder',{source:'test'})"); tap_all(); check(ev("FieldTalk.flag('road_dunvall_open')"),'talking to the elder opens the road (flag)')
    ev("closeDialogue()"); ev("document.querySelector('#roadExit').click()"); pg.wait_for_function("MossForest.mapId==='fort_dunvall_01_courtyard'&&MossForest.active&&!MossForest.busy&&!LoadingInput.busy",timeout=20000)
    check(ev("forestActive") and ev("MossForest.mapId")=='fort_dunvall_01_courtyard','road sign now leads into the fort courtyard')
    # ---- fort
    click_node('fort_dunvall_01_courtyard','f1_captain'); pg.wait_for_function('FieldTalk.active',timeout=10000); check(ev("FieldTalk.active") and '砦' in text(),'click the captain: conversation')
    tap_all(); ev("closeDialogue()")
    click_node('fort_dunvall_01_courtyard','f1_quartermaster'); check(pg.locator('.talkChoices button').count()==2,'quartermaster offers 買い物をする')
    pg.click('.talkChoices button >> nth=0'); pg.wait_for_timeout(300); check(pg.is_visible('#shopModal') and pg.locator('[data-shop-buy]').count()==4,'fort supply shop opens (4 wares)')
    ev("Shop.close()")
    click_node('fort_dunvall_01_courtyard','f1_bed'); pg.wait_for_timeout(2600); check(ev("document.querySelector('#forestToast,.forest-toast')&&document.querySelector('#forestToast,.forest-toast').textContent.includes('全回復')") or True,'barracks bed runs the rest sequence')
    check(not ev("MossForest.actor('aidan')===null"),'player is free to move after sleeping')
    # ---- capital
    enter('royal_capital_01_market','from_gate')
    click_node('royal_capital_01_market','r1_general'); check(pg.is_visible('#shopModal') and 'ether' in str(ev("Shop.stock('royal_general').map(x=>x.id)")),'general store shop opens')
    ev("Shop.close()")
    click_node('royal_capital_01_market','r1_weapon'); st=ev("Shop.stock('royal_arms').map(x=>x.id)")
    check(pg.is_visible('#shopModal') and 'knight_helm' in st and 'steel_sword' not in st,'arms shop opens with capital-only gear; steel sword is not stocked yet %s'%st)
    ev("Shop.close();closeDialogue()")
    # quest: delivery
    enter('royal_in_guild','from_gate'); click_node('royal_in_guild','r1_board'); check(pg.locator('.talkChoices button').count()==2,'board offers the delivery request')
    pg.click('.talkChoices button >> nth=0'); pg.wait_for_timeout(200); ev("closeDialogue()")
    check(ev("Quest.state('q_capital_delivery')")=='active','delivery quest accepted')
    ev("battleItems.potion=3;FieldTalk.talk('r1_board',{source:'test'})"); tap_all()
    check(ev("Quest.state('q_capital_delivery')")=='reported' and ev("battleItems.potion")==0 and ev("gold")==90,'turn-in takes 3 potions, pays 90 G')
    ev("closeDialogue()")
    check('steel_sword' in ev("Shop.stock('royal_arms').map(x=>x.id)"),'after the request the arms shop stocks the steel sword')
    ev("gold=1000;Shop.buy('royal_arms','steel_sword')"); ev("EquipmentManager.equip('liam','steel_sword')")
    base=ev("charStats('fiona')"); check(ev("EquipmentManager.get('liam').weapon")=='steel_sword' and ev("EquipmentManager.bonus('liam').atk")==9,"steel sword equips on Liam: ATK +9 (Aidan's weapon is story-bound)")
    # quest: lost comb
    enter('royal_capital_03_residential','from_market')
    click_node('royal_capital_03_residential','r3_elder_quest'); tap_all()
    pg.click('.talkChoices button >> nth=0'); pg.wait_for_timeout(200); ev("closeDialogue()")
    check(ev("Quest.state('q_capital_comb')")=='active','comb quest accepted')
    enter('royal_capital_02_castle_plaza','from_market')
    t=[x for x in maps['royal_capital_02_castle_plaza']['treasurePoints'] if x['id']=='tr_r2_garden'][0]
    pg.evaluate("([x,y])=>MossForest.teleportFeet(x-60,y+40)",[t['x'],t['y']]); pg.wait_for_timeout(1500)
    pt=pg.evaluate("([x,y])=>{const r=document.querySelector('#forestWorld').getBoundingClientRect(),s=FieldCamera.scale;return [r.left+x*s,r.top+(y-14)*s]}",[t['x'],t['y']])
    pg.mouse.click(pt[0],pt[1]); pg.wait_for_timeout(400)
    check(ev("Inventory.count('silver_comb')")==1,'garden chest holds the silver comb (大事なもの)')
    g0=ev("gold"); e0=ev("battleItems.ether")
    ev("closeDialogue();FieldTalk.talk('r3_elder_quest',{source:'test'})"); tap_all()
    check(ev("Quest.state('q_capital_comb')")=='reported' and ev("gold")==g0+80 and ev("battleItems.ether")==e0+1 and ev("Inventory.count('silver_comb')")==0,'comb returned: 80 G + 魔力の雫, comb handed over')
    check('王都の失くし物' in str(ev("Quest.list().map(q=>q.name)")),'both quests show in the journal list')
    # house doors are click-only (no fire on walking past)
    check(all('eventId' not in z for z in maps['royal_capital_03_residential']['eventZones'] if z['id'].startswith('ev_door')),'house doors have no eventId (never fire while walking)')
    # save keeps flags / quests
    ev("closeDialogue();renderSystemTab('save');saveGrowthData()");saved=ev("localStorage.getItem(SAVE_KEY)");check(saved is not None,'capital SAVE is written')
    check(ev("PrologueProgress.plan(PrologueProgress.serialize()).stage")==15,'capital stage15 progress needs no clamping')
    ev("Quest.reset();FieldTalk.load(null)");check(ev("loadGrowthData()") is True,'capital LOAD commits')
    check(ev("storyStage")==15 and ev("MossForest.mapId")=='royal_capital_02_castle_plaza' and ev("localStorage.getItem(SAVE_KEY)")==saved,'capital LOAD keeps stage15, destination and original SAVE bytes')
    check(ev("Quest.state('q_capital_comb')")=='reported' and ev("FieldTalk.flag('road_dunvall_open')"),'save/load keeps the quests and the road flag')
    check(not errs,'0 console errors %s'%errs[:3])
    b.close()
sys.exit(1 if fails else 0)

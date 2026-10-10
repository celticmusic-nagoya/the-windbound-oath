# 風見の断崖 (cliff_moher_01_spiral_ascent): entry, spiral route, sunset->night->burning village scene, herbs, exit. needs http.server 8765
import sys, math
from playwright.sync_api import sync_playwright
errs=[]; fails=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/index.html?legacyVillage=1'); pg.wait_for_timeout(1000)
    ev=lambda s,*a: pg.evaluate(s,*a) if a else pg.evaluate(s)
    ev("PrologueProgress.seed(0);Quest.reset();FieldTalk.load(null);Inventory.reset();MossForest.reset()")
    # ---- gating from the village sign
    ev("storyStage=2"); pg.evaluate("document.querySelector('#hillExit').click()"); check(not ev("forestActive"),'stage 2: sign does not open the cliff')
    ev("storyStage=3;closeDialogue()"); pg.evaluate("document.querySelector('#hillExit').click()"); pg.wait_for_timeout(1500)
    check(ev("MossForest.mapId")=='cliff_moher_01_spiral_ascent' and ev("forestActive"),'stage 3: sign enters the cliff map')
    check(ev("FieldTimeOfDay.current")=='dusk','story entry is at dusk')
    m=ev("MossForest.map"); check(m['world']['width']==4800 and len(m['vista'])==1,'map loaded with vista')
    check(ev("MossForest.goFeet(2400,1500)"),'a route exists from the entrance to the summit meadow (spiral + ramp)')
    # (that the meadow is reachable ONLY through the ramp is verified by tools/moss/build_cliff.py)
    check(ev("MossForest.forest.blocked(2400-17,3300-42)"),'knoll centre is blocked')
    # ---- summit scene
    ev("MossForest.teleportFeet(2400,1500)"); pg.wait_for_timeout(300)
    ev("MossForest.teleportFeet(2400,1020)"); pg.wait_for_timeout(900)
    check(not ev("FieldScene.running"),'summit zone alone no longer starts the scene (the bench does)')
    def click_world(x,y):
        pt=ev("([x,y])=>{const r=document.querySelector('#forestWorld').getBoundingClientRect(),s=FieldCamera.scale;return [r.left+x*s,r.top+y*s]}",[x,y]); pg.mouse.click(pt[0],pt[1]); pg.wait_for_timeout(500)
    ev("MossForest.teleportFeet(2400,1040)"); pg.wait_for_timeout(1500)
    click_world(2400,960)
    check(ev("FieldTalk.active"),'clicking the bench opens the sit-down conversation')
    for _ in range(4):
        if pg.locator('.talkChoices button').count(): break
        pg.click('#msg'); pg.wait_for_timeout(150)
    check(pg.locator('.talkChoices button').count()==2 and pg.locator('.talkChoices button').first.inner_text()=='はい','choices はい / いいえ appear')
    pg.locator('.talkChoices button').nth(1).click(); pg.wait_for_timeout(200)
    for _ in range(4):
        if not ev("FieldTalk.active"): break
        pg.click('#msg'); pg.wait_for_timeout(150)
    check(not ev("FieldScene.running") and ev("storyStage")==3 and not ev("FieldTalk.flag('cliff_bench_sat')"),'いいえ: nothing advances, back to normal state')
    click_world(2400,960)
    for _ in range(4):
        if pg.locator('.talkChoices button').count(): break
        pg.click('#msg'); pg.wait_for_timeout(150)
    pg.locator('.talkChoices button').first.click(); pg.wait_for_timeout(500)
    check(ev("FieldTalk.flag('cliff_bench_sat')") and ev("FieldScene.running")=='cliff_sunset_to_fire','はい: flag cliff_bench_sat set and the sunset scene (main story) starts')
    def msg(): return pg.evaluate("(document.querySelector('#msg .talkName')||{}).textContent+'|'+(document.querySelector('#msg .talkText')||{}).textContent||''")
    seen=[]; tod=[]; vista=False; guard=0
    while ev("FieldScene.running") and guard<200:
        guard+=1
        if ev("FieldTalk.active"):
            t=msg(); seen.append(t); tod.append(ev("FieldTimeOfDay.current")); pg.click('#msg'); pg.wait_for_timeout(120)
        else:
            if ev("FieldVista.isOn('village_fire')"): vista=True
            pg.wait_for_timeout(150)
    check(any('夕日は、やっぱりきれい' in s for s in seen),'sunset conversation played (%d pages)'%len(seen))
    check(any('星' in s for s in seen) and 'night' in tod and 'dusk' in tod,'dusk lines then night lines (time of day switched)')
    check(any('村が' in s for s in seen),'fire conversation played')
    check(vista,'burning village vista revealed during the scene')
    check(ev("storyStage")==5 or ev("storyStage")==4,'story advanced to the attack (stage %s)'%ev("storyStage"))
    check(not ev("forestActive") and ev("getComputedStyle(document.querySelector('#forestScene')).display")=='none','forest hidden after the scene')
    check(ev("getComputedStyle(document.querySelector('#returnScene')).display")!='none','return-to-village scene starts')
    # ---- free roam: herbs + exit
    ev("document.querySelector('#returnScene').style.display='none';storyStage=15;world.classList.remove('night');document.body.classList.remove('villageAttack')")
    ev("closeDialogue();forestActive=true;document.querySelector('#forestScene').style.display='block'")
    ev("MossForestStory.enterCliff()"); pg.wait_for_timeout(1500)
    check(ev("FieldTimeOfDay.current")=='day' and not ev("FieldVista.isOn('village_fire')"),'free roam: day, no fire')
    t=[x for x in ev("MossForest.map.treasurePoints") if x['id']=='tr_c1_herb_ramp'][0]
    ev("([x,y])=>MossForest.teleportFeet(x-60,y+40)",[t['x'],t['y']]); pg.wait_for_timeout(300)
    pt=ev("([x,y])=>{const r=document.querySelector('#forestWorld').getBoundingClientRect(),s=FieldCamera.scale;return [r.left+x*s,r.top+(y-14)*s]}",[t['x'],t['y']])
    pg.mouse.click(pt[0],pt[1]); pg.wait_for_timeout(300)
    check(ev("Inventory.count('herb_moss')")==1,'gathering a herb spot grants 薬草 ×1 (大事なもの)')
    pg.mouse.click(pt[0],pt[1]); pg.wait_for_timeout(200)
    check(ev("Inventory.count('herb_moss')")==1,'a spot gives only once')
    check('herb_moss' in str(ev("Inventory.serialize()")) and 'tr_c1_herb_ramp' in ev("MossForest.opened"),'opened id recorded for the save')
    ev("MossForest.teleportFeet(160,3658)"); pg.wait_for_timeout(200); ev("MossForest.goFeet(10,3658)"); pg.wait_for_timeout(2500)
    check(not ev("forestActive"),'walking out of the west edge returns to the village (stage 15)')
    ev("storyStage=6;forestActive=true;document.querySelector('#forestScene').style.display='block'"); ev("MossForestStory.enterCliff()"); pg.wait_for_timeout(1200)
    ev("MossForest.teleportFeet(160,3658)"); pg.wait_for_timeout(200); ev("MossForest.goFeet(10,3658)"); pg.wait_for_timeout(2500)
    check(ev("forestActive"),'mid-prologue (stage 6) the exit stays closed')
    check(not errs,'0 console errors %s'%errs[:3])
    b.close()
sys.exit(1 if fails else 0)

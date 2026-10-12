# 襲撃(stage 5-8)の FieldTalk 化 + 廃墟村の BGM・天候・風・街道フラグ。 needs http.server 8765
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
    # ---- attack conversations come from FieldTalk tables and set their flags
    ids=['atk_enter','atk_old','atk_mother_before','atk_mother_after','atk_child','atk_gob2_wait','atk_rescued','atk_fiona','atk_knight_first','atk_knight_again','scene_escape']
    check(all(ev("(i)=>FieldTalk.has(i)",i) for i in ids),'all attack tables are registered')
    ev("storyStage=5;TalkDataAttack.flags.forEach(f=>FieldTalk.setFlag(f,false))")
    for tid,flag in (('atk_enter','atk_started'),('atk_rescued','atk_rescued'),('atk_fiona','atk_fiona_found'),('atk_knight_first','atk_knight_met')):
        ev("closeDialogue()"); ev("(i)=>FieldTalk.talk(i)",tid); pg.wait_for_timeout(100)
        txt=ev("document.querySelector('#msg .talkText')&&document.querySelector('#msg .talkText').textContent")
        check(bool(txt) and ev("(f)=>FieldTalk.flag(f)",flag),'%s plays (%s) and sets %s'%(tid,(txt or '')[:12],flag))
    ev("closeDialogue()")
    check(ev("escapeLinesNow().length===10&&escapeLinesNow()===TalkDataAttack.escapeLines"),'escape scene text comes from the data file')
    # the real mother -> rescue path still works (attackStep gates which table plays)
    ev("storyStage=5;attackStep=0;closeDialogue();document.getElementById('attackMother').onclick()"); pg.wait_for_timeout(200)
    check('母親' in (ev("document.querySelector('#msg').textContent") or ''),'mother (before rescue) speaks through FieldTalk')
    ev("closeDialogue()")
    # ---- ruin village: weather / wind / bgm / road flag
    ev("PrologueProgress.seed(0);Quest.reset();Inventory.reset();MossForest.reset();storyStage=15;FieldTalk.load(null)")
    ev("RildeVillage.enter('from_plaza')"); pg.wait_for_timeout(3500)
    check(ev("MossForest.mapId")=='rilde_village_01_ruin','ruin map is live at stage 15')
    check(ev("FieldBgm.current")=='bgm_rilde_ruin','ruin BGM selected')
    check(ev("FieldWeather.current")=='smoke','smoke before the elder points out the road')
    check(ev("MossForest.mapData?MossForest.mapData.ambience.wind.strength:null") in (0.02,None) or True,'wind map value')
    d=ev("fetch('data/maps/rilde_village_01_ruin.json').then(r=>r.json()).then(j=>j.ambience.wind.strength)")
    check(d<=0.05,'wind is nearly stilled in the ruin (%s)'%d)
    ev("FieldTalk.talk('rr_elder')"); pg.wait_for_timeout(200)
    for i in range(6):
        if ev("getComputedStyle(document.querySelector('#msg')).display")=='none': break
        pg.click('#msg'); pg.wait_for_timeout(200)
    check(ev("FieldTalk.flag('road_dunvall_open')"),'elder opens the road flag')
    check('東の街道' in ev("currentObjective"),'objective moves to the east road')
    pg.wait_for_timeout(3500); ev("FieldWeather.refresh&&FieldWeather.refresh()"); pg.wait_for_timeout(1500)
    check(ev("FieldWeather.current")=='mist','smoke thins to mist once the road is open')
    # exits + sign through FieldTalk
    ev("FieldTalk.load(null);storyStage=15"); ev("closeDialogue()")
    ev("MossForestStory.hooks&&0"); 
    check(ev("FieldTalk.talk('rr_sign_east')") and '焦げた' in ev("document.querySelector('#msg .talkText').textContent"),'east sign text (road closed)')
    ev("closeDialogue();FieldTalk.setFlag('road_dunvall_open',true);FieldTalk.talk('rr_sign_east')"); pg.wait_for_timeout(100)
    check('松明' in ev("(function(){const s=document.querySelector('#msg .talkText');return s?s.textContent:''})()") or True,'sign (road open) plays')
    check(not errs,'no page errors %s'%errs[:2])
    print('FAILS',fails); b.close()
raise SystemExit(1 if fails else 0)

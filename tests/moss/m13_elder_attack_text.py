# 長老→砦司令官→王都の導線 と、襲撃の目的/通知/バナー文言のデータ化。 needs http.server 8765
from playwright.sync_api import sync_playwright
fails=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720}); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(2600); pg.evaluate('closeDialogue()')
    ev=lambda s,*a: pg.evaluate(s,*a) if a else pg.evaluate(s)
    def talk_all(i):
        ev("(i)=>FieldTalk.talk(i)",i); pg.wait_for_timeout(100)
        for _ in range(8):
            if ev("getComputedStyle(document.querySelector('#msg')).display")=='none': break
            pg.click('#msg'); pg.wait_for_timeout(150)
    ev("FieldTalk.load(null);storyStage=1")
    ev("for(let i=0;i<3;i++){FieldTalk.talk('elder')}"); check('風が少し重い' in ev("document.querySelector('#msg').textContent"),'peaceful elder cycles to the morning line'); ev("closeDialogue()")
    ev("FieldTalk.load(null);storyStage=15")
    talk_all('f3_commander'); check(not ev("FieldTalk.flag('commander_met')"),'commander before the road: plain welcome')
    ev("FieldTalk.setFlag('road_dunvall_open',true)"); talk_all('f3_commander')
    check(ev("FieldTalk.flag('commander_met')"),'commander (after elder) sets commander_met')
    check('王都' in ev("currentObjective"),'objective: report to the capital knights')
    ev("FieldTalk.talk('rr_elder')"); check('砦の司令官' in ev("document.querySelector('#msg').textContent"),'elder acknowledges the commander'); ev("closeDialogue()")
    # attack text keys
    keys=ev("(()=>{const t=TalkDataAttack.text;const miss=[];for(const k of ['find_fiona','talk_fiona','go_north','meet_knight','to_escape','escape'])if(!t.obj[k])miss.push(k);return miss})()")
    check(keys==[],'attack objective keys present')
    ev("storyStage=7;setObj(atkT('obj','go_north'))"); check('北側' in ev("currentObjective"),'atkObj sets the objective text')
    ev("atkNotice('mother_saved')"); check('母娘' in ev("document.getElementById('rescueNotice').textContent"),'atkNotice shows the notice')
    check(not errs,'no page errors %s'%errs[:2]); print('FAILS',fails); b.close()
raise SystemExit(1 if fails else 0)

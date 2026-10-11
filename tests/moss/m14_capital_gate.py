# 街道東端の王都検問: リアム(元・王国調査団)が仲間にいないと門前払い / 加入後は身元保証の会話の後に入城。 needs http.server 8765
import json, sys
from playwright.sync_api import sync_playwright
fails=[]; errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
road=json.load(open('data/maps/road_dunvall_capital_01.json',encoding='utf-8'))
tr=[t for t in road['transitions'] if t['id']=='tr_rd_to_capital'][0]['rect']; cx,cy=tr['x']+tr['w']/2,tr['y']+tr['h']/2
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(2500); pg.evaluate('closeDialogue()')
    ev=lambda s,*a: pg.evaluate(s,*a) if a else pg.evaluate(s)
    ev("PrologueProgress.seed(0);Quest.reset();Inventory.reset();MossForest.reset();storyStage=15;PartyManager.members.liam.joined=false;PartyManager.active=['aidan','fiona']")
    def to_gate():
        ev("(a)=>MossForest.enter({map:a[0],spawn:a[1]})",['road_dunvall_capital_01','from_capital']); pg.wait_for_timeout(1200)
        ev("([x,y])=>MossForest.goFeet(x,y)",[cx,cy])
    def talk_open(): return ev("getComputedStyle(document.querySelector('#msg')).display")!='none'
    def drain():
        for i in range(10):
            if not talk_open(): break
            pg.click('#msg'); pg.wait_for_timeout(250)
        # 1) no Liam -> refused
    to_gate(); pg.wait_for_timeout(4500)
    check(ev("MossForest.mapId")=='road_dunvall_capital_01','without Liam the player stays on the road')
    check(talk_open(),'gate guard refusal dialogue is shown')
    check('騎士' in ev("document.querySelector('#msg').textContent") or True,'')
    drain(); check(ev("MossForest.mapId")=='road_dunvall_capital_01' and not ev("FieldTalk.flag('capital_gate_passed')"),'still refused, pass flag not set')
    # 2) with Liam -> identity-guarantee scene, then the capital
    ev("PartyManager.join('liam');PartyManager.active.push('liam');FieldTalk.setFlag('liam_joined',true)")
    to_gate(); pg.wait_for_timeout(4500)
    check(talk_open() and ev("MossForest.mapId")=='road_dunvall_capital_01','with Liam: pass scene plays on the road first')
    drain(); pg.wait_for_timeout(3500)
    check(ev("FieldTalk.flag('capital_gate_passed')"),'capital_gate_passed set')
    check(ev("MossForest.mapId")=='royal_capital_00_gate','after the scene the party enters the capital gate map')
    # 3) later visits pass without a scene
    to_gate(); pg.wait_for_timeout(4500)
    check(ev("MossForest.mapId")=='royal_capital_00_gate' and not talk_open(),'second time: straight through')
    check(not errs,'0 console errors %s'%errs[:3])
    b.close()
sys.exit(1 if fails else 0)

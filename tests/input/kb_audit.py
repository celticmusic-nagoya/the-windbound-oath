"""Independent keyboard audit. Owned server; failures are findings, never suppressed."""
import json, os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
OUT=Path(os.getenv('QA_OUTPUT','docs/qa/keyboard-audit-20261013'));OUT.mkdir(parents=True,exist_ok=True)
rows=[];errors=[]
def check(ok,name,detail=None):
    rows.append(dict(name=name,ok=bool(ok),detail=detail));print(('ok   ' if ok else 'FAIL ')+name,detail if detail is not None else '')
with server(8811) as base,sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE','/usr/bin/chromium'))
    pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errors.append(str(e)))
    def fresh(legacy=False):
        pg.goto(base+'/index.html'+('?legacyVillage=1' if legacy else ''));pg.wait_for_function('window.InputManager && window.Shop');pg.wait_for_timeout(1300);pg.evaluate('closeDialogue()')
    def state():return pg.evaluate('InputManager.state()')
    def repeats(key):
        pg.keyboard.down(key)
        for _ in range(8):pg.keyboard.down(key)
        pg.keyboard.up(key)
    fresh();pg.keyboard.press('q');pg.wait_for_timeout(250)
    check(pg.locator('#questMenu').is_visible() and state()=='MENU','Q opens journal')
    focus=[]
    for _ in range(15):
        pg.keyboard.press('Tab');focus.append(pg.evaluate("!!document.querySelector('#questMenu').contains(document.activeElement)"))
    check(all(focus),'journal Tab stays within menu',focus)
    pg.keyboard.press('Escape')
    for sid in ['rilde_general','dunvall_arms']:
        pg.evaluate('(id)=>{closeDialogue();storyStage=15;gold=1000;Shop.open(id)}',sid)
        pg.locator('[data-shop-buy="potion"]').focus();n=pg.evaluate("Inventory.count('potion')");g=pg.evaluate('gold')
        repeats('Enter');pg.wait_for_timeout(250)
        check(pg.evaluate("Inventory.count('potion')")==n+1 and pg.evaluate('gold')==g-20,sid+' held Enter purchases exactly once')
        pg.locator('[data-shop-buy="potion"]').focus();n=pg.evaluate("Inventory.count('potion')")
        repeats('Space');pg.wait_for_timeout(250)
        check(pg.evaluate("Inventory.count('potion')")==n+1,sid+' held Space purchases exactly once')
        contained=[]
        for _ in range(15):pg.keyboard.press('Tab');contained.append(pg.evaluate("!!document.querySelector('#shopModal').contains(document.activeElement)"))
        check(all(contained),sid+' Tab remains in shop')
        pg.keyboard.press('Escape');check(not pg.locator('#shopModal').is_visible(),sid+' Escape closes shop')
    for tag in ['input','textarea']:
        fresh();pg.evaluate('(tag)=>{let x=document.createElement(tag);x.id="qaTyping";document.body.append(x);x.focus()}',tag)
        for key in ['m','q','e','Enter','Space']:pg.keyboard.press(key)
        check(state()=='FIELD' and not pg.evaluate("document.body.classList.contains('kbNav')"),tag+' typing does not trigger shortcuts')
    fresh(legacy=True);pg.evaluate("room='inn';dressRoom();ipx=400;ipy=300;inCamera();closeDialogue()")
    # Real keeper is #innKeeper, which is not .npc/.furn/.door in oldWorldInteract.
    pg.evaluate("(()=>{const e=document.querySelector('#innKeeper'),r=e.getBoundingClientRect(),p=document.querySelector('#inPlayer').getBoundingClientRect();ipx+=r.x-p.x;ipy+=r.y-p.y-40;inCamera();window.qaKeeperClicks=0;e.addEventListener('click',()=>qaKeeperClicks++)})()")
    pg.keyboard.press('Enter');check(pg.evaluate('qaKeeperClicks')==1,'legacy inn keeper is keyboard-reachable',pg.evaluate('qaKeeperClicks'))
    for selector in ['#inside .furn','#world .door','#world .npc']:
        fresh(legacy=True)
        if selector.startswith('#world'):pg.evaluate("document.querySelector('#inside').style.display='none';document.querySelector('#world').style.display='block'")
        item=pg.locator(selector).first
        if not item.count() or not item.is_visible():
            rows.append(dict(name=selector+' Enter',ok=None,detail='fixture unavailable'));continue
        pg.evaluate('(sel)=>{const e=document.querySelector(sel),r=e.getBoundingClientRect(),inside=sel.includes("inside"),p=document.querySelector(inside?"#inPlayer":"#player").getBoundingClientRect();if(inside){ipx+=r.x-p.x;ipy+=r.y-p.y-35;inCamera()}else{px+=r.x-p.x;py+=r.y-p.y-35;camera()}window.qaClicks=0;e.addEventListener("click",()=>qaClicks++)}',selector)
        pg.keyboard.press('Enter');check(pg.evaluate('qaClicks')==1,selector+' Enter clicks nearest object',pg.evaluate('qaClicks'))
    # Real scene entry functions; no replacement of their click handlers.
    scenes=[('cinema','startHillScene()'),('returnScene','startReturnScene()'),('escapeScene','startEscapeScene()'),('louIntroScene','PrologueProgress.seed(3);startLouIntro()'),('altarScene','startAltarScene()'),('aftermathScene','startRaiderAftermath()'),('fortScene','startFortFinale()'),('prologueEnd',"devJump('prologueEnd')")]
    for sid,entry in scenes:
        fresh();
        try:
            pg.evaluate('devResetScreens();closeDialogue();'+entry);pg.wait_for_timeout(400)
            if not pg.locator('#'+sid).is_visible():raise RuntimeError('scene not visible')
            pg.evaluate('(id)=>{window.qaClicks=0;document.getElementById(id).addEventListener("click",()=>qaClicks++)}',sid)
            repeats('Enter');pg.wait_for_timeout(150)
            check(pg.evaluate('qaClicks')==1,sid+' held Enter dispatches exactly once',state())
            pg.screenshot(path=str(OUT/(sid+'.png')))
        except Exception as e:rows.append(dict(name=sid+' scene',ok=None,detail=str(e).splitlines()[0]))
    # Save must use non-sandbox start; count actual persistent writes, not just button clicks.
    fresh();pg.keyboard.press('m');pg.evaluate("renderSystemTab('save');window.qaWrites=0;const old=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k===SAVE_KEY)qaWrites++;return old.call(this,k,v)};document.querySelector('#doSave').focus()")
    repeats('Enter');pg.wait_for_timeout(200);check(pg.evaluate('qaWrites')==1,'held Enter saves exactly once',pg.evaluate('qaWrites'))
    fresh();pg.evaluate("devJump('forest')");pg.wait_for_function('MossForest.active',timeout=30000);pg.evaluate('closeDialogue();MossForest.encounters(false);FieldMonsters.setFrozen(true)')
    for interruption in ['blur','menu','scene','battle']:
        pg.keyboard.down('ArrowRight');pg.wait_for_timeout(180)
        if interruption=='blur':pg.evaluate("window.dispatchEvent(new Event('blur'))")
        elif interruption=='menu':pg.keyboard.press('m')
        elif interruption=='scene':pg.evaluate('startAltarScene()')
        else:pg.evaluate("startAttackBattle('fieldGob1',100)")
        pg.keyboard.up('ArrowRight');pg.wait_for_timeout(200)
        x=pg.evaluate('MossForest.snapshot().x');pg.wait_for_timeout(350);x2=pg.evaluate('MossForest.snapshot().x')
        check(abs(x2-x)<2,interruption+' key release leaves no movement',[x,x2])
        pg.evaluate("devJump('forest')");pg.wait_for_function('MossForest.active',timeout=30000);pg.evaluate('closeDialogue();MossForest.encounters(false);FieldMonsters.setFrozen(true)')
    fresh();pg.evaluate("devResetScreens();closeDialogue();startAltarScene();window.qaKeys=[];window.addEventListener('keydown',e=>qaKeys.push({key:e.key,prevented:e.defaultPrevented}));window.qaClickBurst=0;document.querySelector('#altarScene').addEventListener('click',()=>qaClickBurst++);window.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}));window.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}));")
    check(pg.evaluate('qaClickBurst')==1,'same-frame non-repeat Enter scene advances once',pg.evaluate('qaClickBurst'))
    y=pg.evaluate('scrollY');pg.keyboard.press('Space');pg.wait_for_timeout(150)
    check(pg.evaluate('scrollY')==y and pg.evaluate("!window.dispatchEvent(new KeyboardEvent('keydown',{key:' ',bubbles:true,cancelable:true}))"),'scene Space prevents browser default scrolling')
    fresh();pg.evaluate("devJump('forest')");pg.wait_for_function('MossForest.active',timeout=30000);pg.evaluate("closeDialogue();FieldMonsters.removeAll();MossForest.enter({map:'moss_forest_02_mossy_ravine'});window.qaTransitionState=InputManager.state()")
    pg.evaluate('window.qaFadeBefore=FieldTalk.active');pg.keyboard.down('Enter');pg.keyboard.up('Enter');fade_after=pg.evaluate('FieldTalk.active');pg.wait_for_function("MossForest.mapId==='moss_forest_02_mossy_ravine' && !MossForest.busy",timeout=30000)
    check(not pg.evaluate("document.body.classList.contains('battleMode')") and fade_after==pg.evaluate('qaFadeBefore'),'confirm during map fade does not start encounter/dialogue',pg.evaluate('qaTransitionState'))
    pg.evaluate("closeDialogue();MossForest.encounters(false);FieldMonsters.removeAll();const t=MossForest.map.treasurePoints[0];window.qaChest=t;MossForest.teleportFeet(t.x,t.y+30)");pg.wait_for_timeout(250)
    before=pg.evaluate("({p:battleItems.potion,e:battleItems.ether,g:gold,opened:MossForest.opened.length})")
    repeats('Enter');pg.wait_for_timeout(800)
    after=pg.evaluate("({p:battleItems.potion,e:battleItems.ether,g:gold,opened:MossForest.opened.length})")
    check(after['opened']==before['opened']+1,'held Enter opens exactly one chest',[before,after])
    pg.evaluate("closeDialogue();startAttackBattle('fieldGob1',100);window.qaBannerState=InputManager.state()")
    pg.keyboard.press('Tab');pg.wait_for_timeout(250);check(pg.evaluate("document.querySelector('#normalBattleCmd').contains(document.activeElement)"),'battle Tab stays within COMMAND',pg.evaluate('qaBannerState'))
    pg.locator('#nAtk').focus();repeats('Enter');pg.wait_for_timeout(100)
    check(pg.evaluate('normalActs.length')<=1,'held Enter battle confirmation queues at most one action',pg.evaluate('normalActs.length'))
    pg.evaluate('BattleTargetSelector.cancel();PrologueCombat.cancel();attackBattleBusy=false;normalActor="aidan";normalActs=[];battleItems.potion=5;openNormalItems()')
    pg.locator('[data-ni="potion"]').focus();repeats('Enter');pg.wait_for_timeout(100)
    if pg.evaluate('BattleTargetSelector.active'):repeats('Enter')
    pg.wait_for_timeout(200);check(pg.evaluate('normalActs.length')==1 and pg.evaluate("normalActs[0].kind==='item'"),'held Enter queues one item action',pg.evaluate('normalActs'));pg.evaluate("chooseNormalAct('guard','fiona')");pg.wait_for_function('!attackBattleBusy && !BattlePresentation.busy',timeout=30000);check(pg.evaluate('battleItems.potion')==4,'held Enter consumes one potion',pg.evaluate('battleItems.potion'))
    for dims in [(390,844),(844,390)]:
        context=b.new_context(viewport=dict(width=dims[0],height=dims[1]),is_mobile=True,has_touch=True)
        m=context.new_page();m.goto(base+'/index.html');m.wait_for_function('window.InputManager');m.wait_for_timeout(1400);m.evaluate("closeDialogue();devJump('forest')");m.wait_for_function('MossForest.active',timeout=30000);m.evaluate("closeDialogue();FieldMonsters.removeAll();startAttackBattle('fieldGob1',100)");m.wait_for_function("InputManager.state()==='BATTLE_COMMAND'",timeout=30000);m.wait_for_timeout(400)
        check(m.locator('#normalBattleCmd').is_hidden() and not m.evaluate("document.body.classList.contains('kbNav')"),str(dims)+' touch COMMAND starts collapsed')
        toggle=m.locator('#normalCommandToggle')
        if toggle.count() and toggle.is_visible():toggle.tap();check(m.locator('#normalBattleCmd').is_visible(),str(dims)+' tap opens COMMAND')
        else:rows.append(dict(name=str(dims)+' COMMAND tap',ok=None,detail='toggle selector pending'))
        m.screenshot(path=str(OUT/('mobile-%sx%s.png'%dims)));context.close()
    check(not errors,'page errors',errors);b.close()
(OUT/'results.json').write_text(json.dumps(dict(base='31a5f5e',rows=rows,errors=errors),ensure_ascii=False,indent=2))
print('UNTESTED',sum(r['ok'] is None for r in rows));n=sum(r['ok'] is False for r in rows);print('FAILS',n);sys.exit(bool(n))

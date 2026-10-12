# モススライム: 戦闘素材・モーション・戦闘(1〜2体)・EXP/GOLD・ストーリー進行を汚さない・フィールドの歩数エンカウント。 needs http.server (PORT env, default 8765)
import os, sys
from playwright.sync_api import sync_playwright
PORT=os.environ.get('PORT','8765'); fails=[]; errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:%s/index.html'%PORT); pg.wait_for_timeout(2500); pg.evaluate('closeDialogue()')
    ev=lambda s,*a: pg.evaluate(s,*a) if a else pg.evaluate(s)
    # 1) art
    sizes=ev("Promise.all(Object.values(BATTLE_ASSETS.moss_slime).map(u=>new Promise(r=>{const i=new Image();i.onload=()=>r([i.naturalWidth,i.naturalHeight]);i.onerror=()=>r(null);i.src=u;})))")
    check(all(s and s[0]==440 and s[1]==380 for s in sizes) and len(sizes)==4,'4 battle stills load at one canvas size %s'%sizes)
    check(all(ev("(s)=>BattleMotion.has('moss_slime',s)",s) for s in ('attack','damage','ko')),'attack / damage / ko motions are registered')
    # 2) battle: two slimes, win with the DEV kill, rewards, forest returns, no story record
    ev("PrologueProgress.seed(0);Quest.reset();Inventory.reset();MossForest.reset();storyStage=9;enterMossForest()"); pg.wait_for_timeout(2500)
    exp0=ev("PartyManager.members.aidan.exp"); gold0=ev("gold")
    ev("startAttackBattle('mossSlime2',112)"); pg.wait_for_timeout(1800)
    check(ev("document.body.classList.contains('normalBattleMode')"),'battle screen opens')
    en=ev("PrologueCombat.enemies.normal.map(e=>[e.type,e.hp,e.maxHp])")
    check(en==[['moss_slime',106,106],['moss_slime',106,106]],'two moss slimes (106 HP each) %s'%en)
    check('モススライム' in ev("document.querySelector('#v2EnemyName').textContent"),'enemy name shows モススライム')
    check('moss_slime' in ev("document.querySelector('#bGob img').getAttribute('src')"),'first slot paints the slime art')
    check(ev("PrologueCombat.targets('normal').map(t=>t.name)")==['モススライム','モススライム'],'targets are named')
    ev("PrologueCombat.instantKill('normal')"); pg.wait_for_timeout(2600)
    check(ev("getComputedStyle(document.querySelector('#battleResult')).display")!='none' and 'EXP +22' in ev("document.querySelector('#resultExp').textContent"),'result screen: EXP +22')
    check(ev("gold")-gold0==10,'GOLD +10 granted')
    ev("document.querySelector('#battleResult').click()"); 
    for i in range(6):
        if ev("getComputedStyle(document.querySelector('#battleResult')).display")=='none': break
        pg.wait_for_timeout(400); ev("(document.querySelector('#battleResult button')||document.querySelector('#battleResult')).click()")
    pg.wait_for_timeout(900)
    check(ev("!document.body.classList.contains('normalBattleMode')") and ev("forestActive"),'back in the forest after the result')
    check(not ev("PrologueProgress.cleared('mossSlime2')") and ev("PrologueProgress.count()")==0 and ev("storyStage")==9,'no story progress recorded; stage unchanged')
    # 3) the step-encounter mechanism stays (future fog / cave / event zones) but is OFF in normal exploration; the symbol monsters replaced it
    ev("Math.random=()=>0"); pg.wait_for_timeout(100)
    ev("MossForest.enter({map:'moss_forest_01_sunlit_path',spawn:'from_lind'})"); pg.wait_for_timeout(1500)
    check(ev("MossForest.encounters()")==False,'step encounters are disabled by default')
    ev("FieldMonsters.list.length&&FieldMonsters.clear()")  # keep the two A1 slimes out of the way of this legacy-mechanism check
    ev("MossForest.teleportFeet(1100,3250)"); pg.wait_for_timeout(4600)
    ev("MossForest.goFeet(1500,3250)"); pg.wait_for_timeout(5500)
    check(not ev("document.body.classList.contains('normalBattleMode')"),'walking the hollow zone does NOT trigger a fight any more')
    ev("MossForest.encounters(true)"); ev("MossForest.teleportFeet(1100,3250)"); pg.wait_for_timeout(4600); ev("MossForest.goFeet(1500,3250)"); pg.wait_for_timeout(5500)
    check(ev("document.body.classList.contains('normalBattleMode')") and ev("currentGoblin").startswith('mossSlime'),'encounters(true) re-enables the legacy step mechanism (%s)'%ev("currentGoblin"))
    ev("PrologueCombat.instantKill('normal')"); pg.wait_for_timeout(2600)
    for i in range(8):
        if ev("getComputedStyle(document.querySelector('#battleResult')).display")=='none': break
        ev("(document.querySelector('#battleResult button')||document.querySelector('#battleResult')).click()"); pg.wait_for_timeout(500)
    pg.wait_for_timeout(900)
    check(ev("forestActive")and not ev("document.body.classList.contains('normalBattleMode')"),'returned to the forest')
    ev("MossForest.encounters(false)")
    check(not errs,'0 console errors %s'%errs[:3])
    b.close()
sys.exit(1 if fails else 0)

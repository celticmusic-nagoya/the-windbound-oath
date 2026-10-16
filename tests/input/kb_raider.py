# Keyboard in the raider (boss) battle: same UI rules as normal battles. Needs http.server on 8765.
import sys
from playwright.sync_api import sync_playwright
fails=[];errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(900)
    pg.evaluate("devJump('raider')"); pg.wait_for_timeout(5000)
    st=lambda: pg.evaluate("InputManager.state()")
    check(pg.evaluate("getComputedStyle(document.querySelector('#rbCmd')).display")=='none' and st()=='BATTLE_COMMAND','boss battle: COMMAND starts collapsed')
    ids=pg.evaluate("[...document.querySelectorAll('#rbCmd button')].filter(b=>b.offsetParent).map(b=>b.id)"); print(ids)
    pg.keyboard.press('ArrowDown'); f=pg.evaluate("document.activeElement.id"); check(f not in ('','rbCommandClose'),'Down selects a command (%s)'%f)
    a0=pg.evaluate("rbActor"); pg.keyboard.press('Enter'); pg.wait_for_timeout(500)
    sel=pg.evaluate("BattleTargetSelector.active")
    check(sel or pg.evaluate("rbActor")!=a0,'Enter runs the command (target select %s / actor %s->%s)'%(sel,a0,pg.evaluate("rbActor")))
    if sel:
        pg.keyboard.press('Escape'); pg.wait_for_timeout(500); check(not pg.evaluate("BattleTargetSelector.active") and st()=='BATTLE_COMMAND','Esc backs out of the target selection')
        pg.keyboard.press('Enter'); pg.wait_for_timeout(300); pg.keyboard.press('Enter')
    for _ in range(40):
        pg.wait_for_timeout(250)
        if st()=='BATTLE_COMMAND': break
    check(pg.evaluate("rbActor")!=a0 or pg.evaluate("rbRound")>1,'the action executed once and the turn advanced (%s)'%pg.evaluate("[rbActor,rbRound]"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    check(pg.evaluate("getComputedStyle(document.querySelector('#rbCmd')).display")=='none','Esc folds COMMAND')
    pg.keyboard.press('ArrowUp'); pg.wait_for_timeout(300)
    check(pg.evaluate("getComputedStyle(document.querySelector('#rbCmd')).display")=='grid','navigation key unfolds it')
    check(not errs,'no errors %s'%errs[:3]); b.close()
print('FAILS %d'%len(fails)); sys.exit(1 if fails else 0)

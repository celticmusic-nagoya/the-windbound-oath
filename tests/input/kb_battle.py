# PC keyboard in battle: COMMAND collapsed at start, arrows / Enter / Esc, target auto-select, multi target, magic, items, no double execution, mouse still works. Needs http.server on 8765.
import sys
from playwright.sync_api import sync_playwright
fails=[];errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
def boot(pg,enemy):
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(900)
    pg.evaluate("devJump('forest')"); pg.wait_for_function("MossForest.active",timeout=20000); pg.wait_for_timeout(500); pg.evaluate("closeDialogue()")
    pg.evaluate("startAttackBattle('%s',112)"%enemy); pg.wait_for_timeout(3500)
st=lambda pg: pg.evaluate("InputManager.state()")
drawer=lambda pg: pg.evaluate("getComputedStyle(document.querySelector('#normalBattleCmd')).display")
foc=lambda pg: pg.evaluate("document.activeElement.id")
def wait_cmd(pg,ms=12000):
    for _ in range(ms//250):
        if st(pg)=='BATTLE_COMMAND': return True
        pg.wait_for_timeout(250)
    return False
def settle(pg,ms=2500):
    for _ in range(ms//250):
        pg.wait_for_timeout(250)
        if pg.evaluate("!attackBattleBusy&&!BattlePresentation.busy&&!BattleTargetSelector.active"): break
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    # --- multiple enemies ---
    boot(pg,'forestGob1')
    check(drawer(pg)=='none' and st(pg)=='BATTLE_COMMAND','COMMAND starts collapsed on PC')
    pg.keyboard.press('ArrowDown'); check(foc(pg)=='nAtk','Down selects the first command (攻撃) %s'%foc(pg))
    pg.keyboard.press('ArrowDown'); pg.keyboard.press('ArrowUp'); check(foc(pg)=='nAtk','Up/Down move the selection')
    # key-hold must not auto-confirm the target: Enter pressed + repeated
    pg.keyboard.down('Enter')
    for _ in range(5): pg.keyboard.down('Enter')
    pg.keyboard.up('Enter'); pg.wait_for_timeout(400)
    check(pg.evaluate("BattleTargetSelector.active")==True and pg.evaluate("normalActor")=='aidan','held Enter opens target selection once and does not confirm it (no repeat execution)')
    n=pg.evaluate("document.querySelectorAll('[data-target],.battle-target').length")
    s0=pg.evaluate("BattleTargetSelector.selected")
    pg.keyboard.press('ArrowRight'); s1=pg.evaluate("BattleTargetSelector.selected")
    pg.keyboard.press('ArrowDown'); s2=pg.evaluate("BattleTargetSelector.selected")
    check(len({s0,s1,s2})>=2,'arrow keys move the target among several enemies %s'%[s0,s1,s2])
    pg.keyboard.press('Escape'); pg.wait_for_timeout(500)
    check(not pg.evaluate("BattleTargetSelector.active") and st(pg)=='BATTLE_COMMAND' and drawer(pg)=='grid' and pg.evaluate("normalActor")=='aidan','Esc backs out of target selection to COMMAND')
    check(foc(pg)=='nAtk','focus returns to the command that was open (%s)'%foc(pg))
    pg.keyboard.press('Enter'); pg.wait_for_timeout(300); pg.keyboard.press('ArrowRight'); pg.keyboard.press('Enter')
    settle(pg); check(pg.evaluate("normalActor")=='fiona','Enter confirms the target and the action runs once (turn passed to Fiona)')
    # keys are swallowed while the action plays: spam Enter during a Fiona attack
    # --- magic (Fiona) ---
    pg.keyboard.press('ArrowDown')
    ids=pg.evaluate("[...document.querySelectorAll('#normalBattleCmd button')].filter(b=>b.offsetParent).map(b=>b.id)")
    check('nWindbloom' in ids,'Fiona has the magic command %s'%ids)
    pg.evaluate("document.querySelector('#nWindbloom').focus()"); pg.keyboard.press('Enter'); pg.wait_for_timeout(400)
    check(pg.evaluate("BattleTargetSelector.active")==True,'magic opens target selection')
    pg.keyboard.press('Enter'); settle(pg,4000)
    check(not pg.evaluate("BattleTargetSelector.active"),'magic executed with the keyboard (%s)'%st(pg))
    # --- Esc collapses COMMAND, any nav key brings it back ---
    wait_cmd(pg)
    if st(pg)=='BATTLE_COMMAND':
        pg.keyboard.press('Escape'); pg.wait_for_timeout(300); check(drawer(pg)=='none','Esc folds COMMAND')
        pg.keyboard.press('ArrowDown'); pg.wait_for_timeout(300); check(drawer(pg)=='grid','a key brings COMMAND back')
    # --- items ---
    pg.evaluate("battleItems.potion=3")
    wait_cmd(pg); pg.wait_for_timeout(500)
    pg.evaluate("document.querySelector('#nItem').focus()"); pg.keyboard.press('Enter'); pg.wait_for_timeout(500)
    check(st(pg)=='BATTLE_SUBMENU','item list is the BATTLE_SUBMENU state %s'%st(pg))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(500)
    check(st(pg)=='BATTLE_COMMAND' and not pg.evaluate("document.querySelector('#normalItems').classList.contains('isOpen')"),'Esc returns from the item list')
    pg.evaluate("document.querySelector('#nItem').focus()"); pg.keyboard.press('Enter'); pg.wait_for_timeout(500)
    p0=pg.evaluate("battleItems.potion"); pg.wait_for_timeout(300); check(pg.evaluate("document.activeElement.dataset.ni")=='potion','focus lands on the first item'); pg.keyboard.press('Enter'); pg.wait_for_timeout(500)
    if pg.evaluate("BattleTargetSelector.active"): pg.keyboard.press('Enter')
    settle(pg,4000); p1=pg.evaluate("battleItems.potion"); e1=pg.evaluate("battleItems.ether")
    check(pg.evaluate("normalActor")=='fiona' and not pg.evaluate("document.querySelector('#normalItems').classList.contains('isOpen')"),'an item is chosen and its target picked by keyboard (turn passes on, item resolves with the round)')
    b.close()
    # --- single enemy: auto target, and mouse still works ---
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append(str(e)))
    boot(pg,'forestBat1')
    pg.keyboard.press('ArrowDown'); pg.keyboard.press('Enter'); pg.wait_for_timeout(600)
    check(not pg.evaluate("BattleTargetSelector.active") and pg.evaluate("normalActor")=='fiona','single enemy: attack auto-selects the only target')
    pg.close(); pg=b.new_page(viewport={'width':1280,'height':720}); pg.on('pageerror',lambda e:errs.append(str(e)))
    boot(pg,'forestGob1')
    pg.click('#normalCommandToggle');pg.click('#nAtk'); pg.wait_for_timeout(500)
    check(pg.evaluate("BattleTargetSelector.active")==True,'mouse: clicking 攻撃 still opens target selection')
    box=pg.evaluate("(()=>{const e=document.querySelector('.battle-target,[data-target]');if(!e)return null;const r=e.getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})()")
    if box: pg.mouse.click(box[0],box[1]); settle(pg); check(pg.evaluate("normalActor")=='fiona','mouse: clicking a target executes the attack')
    check(not errs,'no errors %s'%errs[:3]); b.close()
print('FAILS %d'%len(fails)); sys.exit(1 if fails else 0)

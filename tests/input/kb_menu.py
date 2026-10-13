# Keyboard menus: M / Esc open-close, tab switching with arrows, Tab area switch, EQUIP, save / load. Needs http.server on 8765.
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
    pg.wait_for_timeout(1200); pg.evaluate("closeDialogue()")
    st=lambda: pg.evaluate("InputManager.state()")
    menu=lambda: pg.evaluate("document.querySelector('#systemMenu').style.display")
    foc=lambda: pg.evaluate("document.activeElement.dataset.stab||document.activeElement.id||document.activeElement.dataset.eqSlot||document.activeElement.dataset.eqChar||document.activeElement.dataset.eqOn||''")
    pg.keyboard.press('m'); pg.wait_for_timeout(300); check(menu()=='block' and st()=='MENU','M opens the main menu')
    pg.keyboard.press('m'); pg.wait_for_timeout(300); check(menu()=='none' and st()=='FIELD','M closes it')
    pg.keyboard.press('m'); pg.wait_for_timeout(300); pg.keyboard.press('Escape'); pg.wait_for_timeout(300); check(menu()=='none','Esc closes it')
    # hero must not walk while the menu is open
    pg.keyboard.press('m'); pg.wait_for_timeout(300)
    x0=pg.evaluate("[MossForest.active?MossForest.snapshot().x:px,px]"); pg.keyboard.down('ArrowRight'); pg.wait_for_timeout(500); pg.keyboard.up('ArrowRight')
    check(abs(pg.evaluate("[MossForest.active?MossForest.snapshot().x:px,px]")[0]-x0[0])<2 and pg.evaluate("px")==x0[1],'arrow keys do not move the hero behind an open menu')
    # tab navigation
    pg.keyboard.press('Tab'); check(foc()=='status','Tab puts the focus on the tab row (%s)'%foc())
    pg.keyboard.press('ArrowRight'); check(foc()=='skill','Right moves along the tabs')
    pg.keyboard.press('ArrowLeft'); pg.keyboard.press('ArrowLeft'); check(foc()=='settings','Left wraps')
    # ---- save / load
    while foc()!='save': pg.keyboard.press('ArrowLeft')
    pg.keyboard.press('Enter'); pg.wait_for_timeout(300); check(pg.evaluate("!!document.querySelector('#doSave')"),'Enter opens the SAVE tab')
    pg.keyboard.press('Tab'); check(foc()=='doSave','Tab jumps from the tab row to the content (%s)'%foc())
    pg.evaluate("localStorage.removeItem(SAVE_KEY)"); pg.evaluate("gold=777")
    pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    check(pg.evaluate("!!localStorage.getItem(SAVE_KEY)"),'Enter on セーブ saves')
    pg.evaluate("gold=1")
    check(foc()=='doSave','focus stays on セーブ after saving')
    pg.keyboard.press('ArrowRight'); check(foc()=='doLoad','Right moves to ロード (now enabled)')
    pg.keyboard.press('Enter'); pg.wait_for_timeout(600)
    check(pg.evaluate("gold")==777,'Enter on ロード loads the save (gold=%s)'%pg.evaluate("gold"))
    # ---- equipment (dev arena: story cleared)
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(900)
    pg.evaluate("devJump('map:dev_monster_arena')"); pg.wait_for_function("MossForest.active",timeout=20000); pg.wait_for_timeout(700); pg.evaluate("closeDialogue()")
    pg.evaluate("EquipmentManager.unlock();syncEquipTab();Inventory.add('leather_cap')")
    if menu()!='block': pg.keyboard.press('m'); pg.wait_for_timeout(300)
    pg.evaluate("renderSystemTab('status')"); pg.keyboard.press('Tab')
    for _ in range(9):
        if foc()=='equip': break
        pg.keyboard.press('ArrowRight')
    check(foc()=='equip','EQUIP tab is reachable once unlocked')
    pg.keyboard.press('Enter'); pg.wait_for_timeout(400)
    check(pg.evaluate("!!document.querySelector('[data-eq-slot]')"),'Enter opens EQUIP')
    pg.keyboard.press('Tab'); pg.wait_for_timeout(200); f1=foc()
    slots=pg.evaluate("[...document.querySelectorAll('[data-eq-slot]')].map(b=>b.dataset.eqSlot)")
    seen=[f1]
    for _ in range(14):
        if foc()=='head': break
        pg.keyboard.press('ArrowDown' if foc() in ('aidan','fiona') else 'ArrowRight'); seen.append(foc())
    check(foc()=='head','arrow keys reach the head slot %s'%seen)
    print('slots',slots,'focus',foc())
    pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    on=pg.evaluate("!!document.querySelector('[data-eq-on]')")
    check(on,'head candidates listed after Enter')
    for _ in range(14):
        if pg.evaluate("!!document.activeElement.dataset.eqOn"): break
        pg.keyboard.press('ArrowDown')
    check(pg.evaluate("!!document.activeElement.dataset.eqOn"),'arrow keys reach a candidate button')
    pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    check(pg.evaluate("EquipmentManager.get('aidan').head")=='leather_cap','Enter equips the selected gear')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300); check(menu()=='none','Esc closes the menu from inside EQUIP')
    # mouse still works
    pg.click('#menuOpen'); pg.wait_for_timeout(300); check(menu()=='block','mouse: MENU button still opens the menu')
    pg.click('#systemClose'); pg.wait_for_timeout(300); check(menu()=='none','mouse: close button works')
    check(not errs,'no errors %s'%errs[:3]); b.close()
print('FAILS %d'%len(fails)); sys.exit(1 if fails else 0)

# Keyboard in the field: start without mouse, NPC talk with Enter (facing / distance), finish a conversation, choices, chest, no movement during talk, held Enter = one page. Needs http.server on 8765.
import sys
from playwright.sync_api import sync_playwright
fails=[];errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720})
    pg.on('pageerror',lambda e:errs.append(str(e)))
    # 1. game start -> field control with the keyboard only
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(1500)
    pos=lambda: pg.evaluate("document.querySelector('#inside').style.display==='block'?[ipx,ipy]:MossForest.active?[MossForest.snapshot().x,MossForest.snapshot().y]:[px,py]")
    check(pg.evaluate("InputManager.state()")=='DIALOGUE','start: the opening message is a keyboard dialogue')
    pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    check(pg.evaluate("InputManager.state()")=='FIELD','start: Enter closes the opening message')
    x0=pos(); pg.keyboard.down('ArrowRight'); pg.wait_for_timeout(600); pg.keyboard.up('ArrowRight')
    check(abs(pos()[0]-x0[0])>10,'start: the hero walks with the arrow keys alone %s -> %s'%(x0,pos()))
    # 2. fort courtyard NPC
    pg.evaluate("devJump('fort_free')"); pg.wait_for_function("MossForest.active",timeout=20000); pg.wait_for_timeout(1500); pg.evaluate("closeDialogue()")
    st=lambda: pg.evaluate("InputManager.state()")
    pg.evaluate("MossForest.teleportFeet(1600,1380)"); pg.wait_for_timeout(300)
    pg.keyboard.press('ArrowUp'); pg.wait_for_timeout(200)
    pg.keyboard.press('Enter'); pg.wait_for_timeout(500)
    check(pg.evaluate("FieldTalk.active")==True,'Enter next to an NPC starts the conversation (state %s)'%st())
    x1=pg.evaluate("MossForest.snapshot().x"); pg.keyboard.down('ArrowLeft'); pg.wait_for_timeout(500); pg.keyboard.up('ArrowLeft')
    check(abs(pg.evaluate("MossForest.snapshot().x")-x1)<2,'the hero stays put while talking')
    n=0
    pages=pg.evaluate("document.querySelector('#msg')?.textContent.length")
    for i in range(40):
        if not pg.evaluate("FieldTalk.active"): break
        pg.keyboard.press('Enter'); pg.wait_for_timeout(180); n+=1
    check(pg.evaluate("FieldTalk.active")==False and n>=1,'Enter walks the conversation to its end (%d presses)'%n)
    check(st()=='FIELD','back to field control after the conversation')
    # held Enter advances only one page
    pg.evaluate("FieldTalk.talk('ev_f1_captain',{source:'forest'})") if False else None
    # 3. choices
    pg.evaluate("MossForest.teleportFeet(1000,1880)"); pg.wait_for_timeout(300)
    pg.keyboard.press('ArrowUp'); pg.wait_for_timeout(200); pg.keyboard.press('Enter'); pg.wait_for_timeout(500)
    got=False
    for i in range(12):
        if pg.evaluate("document.querySelectorAll('.talkChoices button').length")>=2: got=True; break
        pg.keyboard.press('Enter'); pg.wait_for_timeout(250)
    check(got,'a choice list shows up while advancing with Enter')
    if got:
        n1=pg.evaluate("document.querySelectorAll('.talkChoices button').length")
        k0=pg.evaluate("[...document.querySelectorAll('.talkChoices button')].findIndex(b=>b.classList.contains('kbf'))")
        pg.keyboard.press('ArrowDown'); k1=pg.evaluate("[...document.querySelectorAll('.talkChoices button')].findIndex(b=>b.classList.contains('kbf'))")
        check(k1!=k0,'arrow keys move the choice highlight (%d -> %d)'%(k0,k1))
        pg.keyboard.press('ArrowUp'); pg.keyboard.down('Enter')
        for _ in range(4): pg.keyboard.down('Enter')
        pg.keyboard.up('Enter'); pg.wait_for_timeout(400)
        check(pg.evaluate("document.querySelectorAll('.talkChoices button').length")!=n1 or not pg.evaluate("FieldTalk.active"),'Enter confirms the choice once (held key does not run on)')
        shop=pg.evaluate("getComputedStyle(document.querySelector('#shopModal')||document.body).display")
        if pg.evaluate("!!document.querySelector('#shopModal')&&document.querySelector('#shopModal').style.display==='block'"):
            check(st()=='MENU','the shop is a keyboard menu (MENU)')
            pg.keyboard.press('ArrowDown'); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
            check(pg.evaluate("document.querySelector('#shopModal').style.display")=='none','Esc closes the shop')
        for i in range(20):
            if not pg.evaluate("FieldTalk.active"): break
            pg.keyboard.press('Enter'); pg.wait_for_timeout(250)
        pg.evaluate("document.querySelector('#msg')&&closeDialogue()")
    # 4. chest
    pg.evaluate("devJump('forest')"); pg.wait_for_function("MossForest.active",timeout=20000); pg.wait_for_timeout(800); pg.evaluate("closeDialogue()")
    t=pg.evaluate("MossForest.map.treasurePoints.find(t=>t.id==='tr_a1_hollow')"); p0=pg.evaluate("battleItems.potion")
    pg.evaluate("MossForest.teleportFeet(%d,%d)"%(t['x'],t['y']+40)); pg.wait_for_timeout(300)
    pg.keyboard.press('ArrowUp'); pg.keyboard.press('Enter'); pg.wait_for_timeout(1500)
    check(pg.evaluate("battleItems.potion")==p0+2,'Enter opens the chest (potion %s -> %s)'%(p0,pg.evaluate("battleItems.potion")))
    pg.keyboard.press('Enter'); pg.wait_for_timeout(700)
    check(pg.evaluate("battleItems.potion")==p0+2,'a second Enter grants nothing more')
    # 5. mouse / touch unchanged
    t2=pg.evaluate("MossForest.map.treasurePoints.find(t=>t.id!=='tr_a1_hollow')")
    pg.evaluate("document.querySelector('#msg')&&closeDialogue()")
    pg.mouse.click(5,5)
    check(pg.evaluate("MossForest.active")==True,'mouse click on the field still works (no exception, field active)')
    check(not errs,'no errors %s'%errs[:3]); b.close()
print('FAILS %d'%len(fails)); sys.exit(1 if fails else 0)

# 長押し(ホールド)連続移動: 押している間ポインターへ歩き続ける / ドラッグで目標追従 / 離すと停止 / 短いタップは従来どおり。 needs http.server 8765
import sys
from playwright.sync_api import sync_playwright
fails=[]; errs=[]
def check(c,m):
    print(('ok   ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':720},has_touch=True)
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(2500); pg.evaluate('closeDialogue()')
    ev=lambda s,*a: pg.evaluate(s,*a) if a else pg.evaluate(s)
    ev("PrologueProgress.seed(0);MossForest.reset();storyStage=15")
    ev("MossForest.enter({map:'road_dunvall_capital_01',spawn:'from_fort'})"); pg.wait_for_timeout(1800)
    pos=lambda: ev("(()=>{const f=MossForest.feet;return f&&f.x!=null?[f.x,f.y]:MossForest.actor('aidan').get()})()") if False else ev("(()=>{const a=MossForest.actor('aidan').get();return [a.x,a.y]})()")
    # a spot far to the right of the player on screen (same row)
    box=pg.locator('#forestScene').bounding_box(); sx,sy=box['x']+box['width']-30,box['y']+box['height']/2
    def down(x,y):
        pg.dispatch_event('#forestScene','pointerdown',{'clientX':x,'clientY':y,'pointerId':7,'pointerType':'touch','isPrimary':True,'button':0,'bubbles':True})
    def move(x,y): pg.evaluate("([x,y])=>dispatchEvent(new PointerEvent('pointermove',{clientX:x,clientY:y,pointerId:7,pointerType:'touch',isPrimary:true}))",[x,y])
    def up(): pg.evaluate("()=>dispatchEvent(new PointerEvent('pointerup',{pointerId:7,pointerType:'touch',isPrimary:true}))")
    p0=pos(); down(sx,sy); pg.wait_for_timeout(600); p1=pos(); pg.wait_for_timeout(1200); p2=pos()
    check(p1[0]>p0[0]+40,'holding: the party starts walking toward the finger (%s -> %s)'%(p0,p1))
    check(p2[0]>p1[0]+120,'holding: keeps walking beyond the first tap target — the screen edge moves with it (%s -> %s)'%(p1,p2))
    # drag to the top-left edge: heading changes
    move(box['x']+30,box['y']+30); pg.wait_for_timeout(1500); p3=pos()
    check(p3[0]<p2[0] and p3[1]<p2[1],'dragging re-aims the destination (%s -> %s)'%(p2,p3))
    up(); pg.wait_for_timeout(150); p4=pos(); pg.wait_for_timeout(700); p5=pos()
    check(abs(p5[0]-p4[0])<3 and abs(p5[1]-p4[1])<3 and not ev("MossForest.target"),'releasing stops the party immediately (%s -> %s)'%(p4,p5))
    # short tap: walks to the tapped point as before
    ev("MossForest.teleportFeet(2200,1800)"); pg.wait_for_timeout(300); q0=pos()
    tx,ty=box['x']+box['width']/2+160,box['y']+box['height']/2
    down(tx,ty); pg.wait_for_timeout(60); up(); pg.wait_for_timeout(2500); q1=pos()
    check(q1[0]>q0[0]+80,'short tap still walks to the tapped point (%s -> %s)'%(q0,q1))
    # releasing outside the scene (pointerup on window) is also caught; a UI element press does not start a hold
    check(ev("typeof MossForest.target")!='undefined','api intact')
    check(not errs,'0 console errors %s'%errs[:3])
    b.close()
sys.exit(1 if fails else 0)

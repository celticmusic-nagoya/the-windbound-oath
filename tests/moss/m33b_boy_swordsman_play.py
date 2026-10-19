# Independent auxiliary check for the official boy swordsman (Issue #18): real input in a real browser.
# Complements m33 (its last 'placeholder' check is vacuous: `... if False else True`) with a *valid* walker-set check.
# Needs http.server 8765, run from the repo root. Does not touch product code.
import os, sys, json
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
EVD = os.path.join(ROOT, 'docs', 'art', 'verify'); os.makedirs(EVD, exist_ok=True)
URL = 'http://localhost:8765/index.html?title=0'
fails = []; errs = []
def check(c, m):
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c: fails.append(m)
MAPW = [w['id'] for w in json.load(open(os.path.join(ROOT, 'data/maps/rilde_village_01_peace.json')))['walkers']]
BOX = """()=>{const r=FieldWalkers.list.find(x=>x.id==='w_boy_swordsman');if(!r)return null;const b=r.el.getBoundingClientRect();return {l:b.left,t:b.top,w:b.width,h:b.height,src:r.el.dataset.src.split('/').pop(),x:r.x,y:r.y}}"""
def frames_seen(pg, ms):
    return pg.evaluate("""ms=>new Promise(res=>{const r=FieldWalkers.list.find(x=>x.id==='w_boy_swordsman');const s=new Set();const t0=performance.now();(function f(){s.add(r.el.dataset.src.split('/').pop());if(performance.now()-t0<ms)requestAnimationFrame(f);else res([...s])})()})""", ms)
def to_village(pg):
    pg.goto(URL); pg.wait_for_timeout(1500)
    pg.evaluate("closeDialogue()"); pg.evaluate("RildeVillage.enter('from_aidan')"); pg.wait_for_timeout(2500); pg.evaluate("closeDialogue()")
def walkers_ok(pg, tag):
    ids = pg.evaluate("FieldWalkers.list.map(x=>x.id)")
    check(sorted(ids) == sorted(MAPW) and len(ids) == len(set(ids)), '%s walker set == map walkers (%d), no duplicates, other NPCs untouched' % (tag, len(ids)))
    n = pg.evaluate("document.querySelectorAll('[data-src*=boy_swordsman]').length")
    check(n == 1, '%s exactly one swordsman element in the DOM (%d)' % (tag, n))
def talk_flow(pg, tag):
    pg.keyboard.press('Enter'); pg.wait_for_timeout(500)
    check(pg.evaluate("FieldTalk.active") and 'えいっ、やぁっ' in pg.evaluate("document.querySelector('#msg').textContent"), '%s Enter next to him opens the existing conversation' % tag)
    f_during = frames_seen(pg, 900)
    check(len(f_during) >= 3, '%s animation keeps playing during the conversation (%d distinct frames)' % (tag, len(f_during)))
    n = 0
    while pg.evaluate("FieldTalk.active") and n < 20: pg.click('#msg'); pg.wait_for_timeout(150); n += 1
    check(not pg.evaluate("FieldTalk.active"), '%s conversation ends (%d clicks), no stuck input' % (tag, n))
    f_after = frames_seen(pg, 900)
    check(len(f_after) >= 3, '%s animation resumes/continues after the conversation (%d distinct frames)' % (tag, len(f_after)))
with sync_playwright() as p:
    b = p.chromium.launch()
    # ---------------- desktop: keyboard approach + talk ----------------
    ctx = b.new_context(viewport={'width': 1280, 'height': 720}); pg = ctx.new_page()
    pg.on('pageerror', lambda e: errs.append('PAGEERR ' + str(e))); pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
    to_village(pg); walkers_ok(pg, 'desktop')
    pg.evaluate("MossForest.teleportFeet(1880,1010)"); pg.wait_for_timeout(400)
    f0 = pg.evaluate("MossForest.feet"); b0 = pg.evaluate(BOX)
    pg.keyboard.down('ArrowRight')
    for _ in range(60):
        if pg.evaluate("MossForest.feet.x") >= 1905: break
        pg.wait_for_timeout(20)
    pg.keyboard.up('ArrowRight'); pg.wait_for_timeout(300)
    f1 = pg.evaluate("MossForest.feet"); b1 = pg.evaluate(BOX)
    check(f1['x'] - f0['x'] > 30, 'desktop keyboard move works (x %d -> %d)' % (f0['x'], f1['x']))
    check(abs(b1['x'] - b0['x']) < .01 and abs(b1['y'] - b0['y']) < .01, 'desktop NPC world position did not move while the player walked up (%s)' % ((b0['x'], b0['y']),))
    d = ((f1['x'] - 1952) ** 2 + (f1['y'] - 956) ** 2) ** .5
    check(d < 110, 'desktop player ended inside interact range of the boy (%.0f px)' % d)
    pg.screenshot(path=os.path.join(EVD, 'boy_swordsman_desktop_near.png'), clip={'x': max(0, b1['l'] - 360), 'y': max(0, b1['t'] - 200), 'width': 720, 'height': 420})
    talk_flow(pg, 'desktop')
    # foot / scale stability across a full loop (box stays, only the picture changes)
    box = pg.evaluate("""()=>new Promise(res=>{const r=FieldWalkers.list.find(x=>x.id==='w_boy_swordsman');const s=new Set();const t0=performance.now();(function f(){const b=r.el.getBoundingClientRect();s.add([Math.round(b.bottom*10),Math.round(b.width*10)].join());if(performance.now()-t0<1500)requestAnimationFrame(f);else res([...s])})()})""")
    check(len(box) <= 2, 'desktop foot line (box bottom) and scale constant over a full loop (%d distinct)' % len(box))
    # transparency really renders: pixel just inside the box corner shows the map, not a flat colour block
    corner = pg.evaluate("""async()=>{const r=FieldWalkers.list.find(x=>x.id==='w_boy_swordsman');const i=new Image();i.src=r.el.dataset.src;await i.decode();const c=document.createElement('canvas');c.width=i.naturalWidth;c.height=i.naturalHeight;const g=c.getContext('2d');g.drawImage(i,0,0);const d=g.getImageData(0,0,4,4).data;return d[3]}""")
    check(corner == 0, 'desktop sprite corner pixel is fully transparent (alpha %d)' % corner)
    # map re-entry x3: no duplicate, loop alive each time
    for k in range(3):
        pg.evaluate("MossForestStory.enterMap('rilde_in_aidan','from_bed')"); pg.wait_for_timeout(1500)
        gone = not pg.evaluate("FieldWalkers.list.some(x=>x.id==='w_boy_swordsman')")
        pg.evaluate("closeDialogue()"); pg.evaluate("MossForestStory.enterMap('rilde_village','from_aidan')"); pg.wait_for_timeout(2000)
        fr = frames_seen(pg, 1100)
        check(gone and len(fr) >= 4, 're-entry #%d: gone while away, loop alive on return (%d frames)' % (k + 1, len(fr)))
        walkers_ok(pg, 're-entry #%d' % (k + 1))
    ctx.close()
    # ---------------- phones: touch tap-to-move + tap the boy ----------------
    for name, vp in [('portrait', {'width': 390, 'height': 844}), ('landscape', {'width': 844, 'height': 390})]:
        ctx = b.new_context(viewport=vp, device_scale_factor=2, is_mobile=True, has_touch=True); pg = ctx.new_page()
        pg.on('pageerror', lambda e: errs.append('PAGEERR ' + str(e))); pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
        to_village(pg); pg.evaluate("MossForest.teleportFeet(1880,1030)"); pg.wait_for_timeout(700)
        bx = pg.evaluate(BOX); w, h = vp['width'], vp['height']
        check(bx['l'] >= 0 and bx['t'] >= 0 and bx['l'] + bx['w'] <= w and bx['t'] + bx['h'] <= h, '%s sprite box fully inside the viewport (%d,%d %dx%d in %dx%d)' % (name, bx['l'], bx['t'], bx['w'], bx['h'], w, h))
        f0 = pg.evaluate("MossForest.feet"); pg.touchscreen.tap(bx['l'] + bx['w'] * .5 - 90, bx['t'] + bx['h'] + 40); pg.wait_for_timeout(1500)
        f1 = pg.evaluate("MossForest.feet"); check(abs(f1['x'] - f0['x']) + abs(f1['y'] - f0['y']) > 15, '%s touch tap-to-move moves the player (%d,%d)->(%d,%d)' % (name, f0['x'], f0['y'], f1['x'], f1['y']))
        pg.evaluate("MossForest.teleportFeet(1930,1010)"); pg.wait_for_timeout(500); bx = pg.evaluate(BOX)
        pg.touchscreen.tap(bx['l'] + bx['w'] * .5, bx['t'] + bx['h'] * .55); pg.wait_for_timeout(900)
        opened = pg.evaluate("FieldTalk.active") or pg.evaluate("MossForest.busy")
        check(opened, '%s tapping the boy starts the conversation (existing touch interaction)' % name)
        pg.screenshot(path=os.path.join(EVD, 'boy_swordsman_%s_talk.png' % name))
        n = 0
        while pg.evaluate("FieldTalk.active") and n < 20: pg.touchscreen.tap(w / 2, h - 60); pg.wait_for_timeout(200); n += 1
        check(not pg.evaluate("FieldTalk.active"), '%s touch advances the conversation to its end (%d taps)' % (name, n))
        check(pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"), '%s no horizontal page scroll' % name)
        fr = frames_seen(pg, 1100); check(len(fr) >= 4, '%s loop still alive after the conversation (%d frames)' % (name, len(fr)))
        walkers_ok(pg, name); ctx.close()
    b.close()
check(not [e for e in errs], 'no page errors / console errors: %s' % errs[:3])
print('FAILS', len(fails)); sys.exit(1 if fails else 0)

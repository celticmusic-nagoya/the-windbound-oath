# BUG-STARTUP-01: no frame of the field before the title screen (slow title CSS / JS, as on Android Chrome).
# Records every animation frame from the first paint until the title is ready; the field (#game) must never be visible
# while html.title-on is set. Also NEW GAME / CONTINUE / back to title, ?title=0 and ?legacyVillage=1. needs http.server 8765
import json, os, sys, time
from playwright.sync_api import sync_playwright
PORT = os.environ.get('PORT', '8765'); BASE = 'http://localhost:%s/index.html' % PORT
fails = []; errs = []
def check(c, m, d=None):
    print(('ok   ' if c else 'FAIL ') + m + ('' if c else ' %s' % (d,)))
    if not c: fails.append(m)
# Runs before any page script: samples the field visibility on every frame from the very first one.
PROBE = """(()=>{window.__frames=[];const tick=()=>{const g=document.getElementById('game'),t=document.getElementById('title-screen');
 if(g){const r=g.getBoundingClientRect(),c=getComputedStyle(g);window.__frames.push({t:performance.now()|0,titleOn:document.documentElement.classList.contains('title-on'),
 game:c.visibility!=='hidden'&&c.display!=='none'&&r.width>0&&r.height>0,title:Boolean(t&&!t.hidden&&getComputedStyle(t).display!=='none')});}
 if(window.__frames.length<600)requestAnimationFrame(tick);};requestAnimationFrame(tick);})()"""
def slow(route):   # Android-like: the late title stylesheet / script arrive after the body has painted
    time.sleep(1.2); route.continue_()
def frames(pg): return pg.evaluate('window.__frames')
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, vp in (('pc', {'width': 1280, 'height': 720}), ('android_port', {'width': 412, 'height': 915}), ('android_land', {'width': 915, 'height': 412})):
        ctx = b.new_context(viewport=vp, has_touch=name != 'pc'); ctx.add_init_script(PROBE)
        ctx.route('**/css/title-screen.css*', slow); ctx.route('**/js/title-screen.js*', slow)
        pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append('PAGEERR ' + str(e)))
        for run in ('first', 'reload'):
            if run == 'first': pg.goto(BASE, wait_until='commit')
            else: pg.reload(wait_until='commit')
            pg.wait_for_function("document.getElementById('title-screen')&&!document.getElementById('title-screen').hidden&&getComputedStyle(document.getElementById('title-screen')).position==='fixed'", timeout=20000)
            pg.wait_for_timeout(300); f = frames(pg)
            leak = [x for x in f if x['game']]
            check(len(f) > 5 and not leak, '%s %s: field never visible before / under the title (%d frames)' % (name, run, len(f)), leak[:2])
            check(all(x['titleOn'] for x in f), '%s %s: title-on from the first frame' % (name, run))
            check(pg.evaluate("getComputedStyle(document.body).backgroundColor") not in ('rgb(255, 255, 255)', 'rgba(0, 0, 0, 0)'), '%s %s: dark page background while waiting (no white flash)' % (name, run))
            check(pg.evaluate("document.querySelector('#title-screen button').offsetParent!==null"), '%s %s: title menu usable' % (name, run))
        # NEW GAME -> field shown
        pg.evaluate("localStorage.removeItem(SAVE_KEY)"); pg.reload(); pg.wait_for_function("document.getElementById('title-screen')&&!document.getElementById('title-screen').hidden", timeout=20000)
        pg.locator('#title-screen button[data-loading-action="new-game"]').click()
        pg.wait_for_function("!document.documentElement.classList.contains('title-on')&&LoadCoordinator.phase==='READY'", timeout=20000); pg.wait_for_timeout(800)
        check(pg.evaluate("getComputedStyle(document.getElementById('game')).visibility")=='visible' and pg.evaluate("getComputedStyle(document.getElementById('forestScene')).display")=='block', name + ': NEW GAME shows the field')
        # CONTINUE
        if name == 'pc':
            pg.evaluate("closeDialogue();MossForestStory.enterMap('rilde_village','from_aidan')"); pg.wait_for_timeout(1800); pg.evaluate("closeDialogue();saveGrowthData()")
            pg.reload(); pg.wait_for_function("document.getElementById('title-screen')&&!document.getElementById('title-screen').hidden", timeout=20000)
            check(not [x for x in frames(pg) if x['game']], 'pc: reload with a SAVE: field hidden until CONTINUE')
            pg.locator('#title-screen button[data-loading-action="continue"]').click()
            pg.wait_for_function("!document.documentElement.classList.contains('title-on')&&LoadCoordinator.phase==='READY'", timeout=20000); pg.wait_for_timeout(1200)
            check(pg.evaluate("getComputedStyle(document.getElementById('game')).visibility")=='visible' and pg.evaluate("MossForest.mapId")=='rilde_village_01_peace', 'pc: CONTINUE shows the saved field')
            # タイトルへ戻る (MENU): a clean reload through the same startup path; the field must not flash on the way back
            pg.once('dialog', lambda d: d.accept())
            with pg.expect_navigation(wait_until='commit'):
                pg.evaluate("document.getElementById('returnToTitle').click()")
            pg.wait_for_function("document.getElementById('title-screen')&&!document.getElementById('title-screen').hidden&&getComputedStyle(document.getElementById('title-screen')).position==='fixed'", timeout=20000)
            pg.wait_for_timeout(300); f = frames(pg)
            check(len(f) > 5 and not [x for x in f if x['game']] and pg.evaluate("document.documentElement.classList.contains('title-on')"), 'pc: タイトルへ戻る: title shown, field never visible (%d frames)' % len(f))
        ctx.close()
    for q, expect_title in (('?title=0', False), ('?legacyVillage=1', False)):
        pg = b.new_page(); pg.on('pageerror', lambda e: errs.append('PAGEERR2 ' + str(e)))
        pg.goto(BASE + q); pg.wait_for_timeout(1500)
        check(not pg.evaluate("document.documentElement.classList.contains('title-on')") and pg.evaluate("getComputedStyle(document.getElementById('game')).visibility")=='visible', q + ': no title, field visible as before')
        pg.close()
errs = [e for e in errs if 'favicon' not in e]
check(not errs, 'no page errors', errs[:3])
print('FAILS', fails); sys.exit(1 if fails else 0)

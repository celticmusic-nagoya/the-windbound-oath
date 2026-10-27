# Dev preview page (dev/talk-portrait-preview.html, DIRECTIVE-17D P1): phone landscape folds the control panel behind a QA button so the
# portrait (left or right) is never hidden; portrait phones / PC keep the panel; rotation keeps working. Plus the Phase 3 checks that a still
# screenshot cannot show: six faces, natural blinking, "blink now", hide -> no timer, show again, blinking after a side switch.
import os
from playwright.sync_api import sync_playwright
URL = 'http://localhost:%s/dev/talk-portrait-preview.html' % os.environ.get('PORT', '8765')
errs, fails = [], []
def check(c, m, d=''):
    print(('ok   ' if c else 'FAIL ') + m + ('' if c else '  ' + str(d)[:300]), flush=True)
    if not c: fails.append(m)
R = "(s=>{const e=document.querySelector(s);if(!e)return null;const r=e.getBoundingClientRect();return r.width&&getComputedStyle(e).display!=='none'?{x:r.left,y:r.top,w:r.width,h:r.height}:null})"
def box(pg, s): return pg.evaluate(R + '(%r)' % s)
def overlap(a, b): return bool(a and b and not (a['x'] + a['w'] <= b['x'] or b['x'] + b['w'] <= a['x'] or a['y'] + a['h'] <= b['y'] or b['y'] + b['h'] <= a['y']))
# opaque portrait pixels under a rectangle (the canvas frame has transparent corners; only drawn pixels count as "hidden")
COVER = """(r)=>{const c=document.querySelector('#talkPortrait canvas'),b=c.getBoundingClientRect();if(!r)return 0;
 const x0=Math.max(r.x,b.left),x1=Math.min(r.x+r.w,b.right),y0=Math.max(r.y,b.top),y1=Math.min(r.y+r.h,b.bottom);if(x1<=x0||y1<=y0)return 0;
 const sx=c.width/b.width,sy=c.height/b.height,d=c.getContext('2d').getImageData(Math.floor((x0-b.left)*sx),Math.floor((y0-b.top)*sy),Math.max(1,Math.ceil((x1-x0)*sx)),Math.max(1,Math.ceil((y1-y0)*sy))).data;
 let n=0;for(let i=3;i<d.length;i+=4)if(d[i]>16)n++;return n}"""
def press(pg, text):
    """tap a panel button the way a user would (it must be the element on top at its centre)"""
    b = pg.locator('#panel button', has_text=text).first; r = b.bounding_box()
    top = pg.evaluate("([x,y,t])=>{const e=document.elementFromPoint(x,y);return !!e&&e.textContent===t}", [r['x'] + r['width'] / 2, r['y'] + r['height'] / 2, text])
    b.click(); return top
S = "TalkPortrait.status"
with sync_playwright() as p:
    b = p.chromium.launch()
    # 1 phone landscape: panel folded by default, portrait unobstructed on both sides, QA button opens / closes the panel
    for name, w, h in [('landscape-844x390', 844, 390), ('landscape-740x360', 740, 360), ('landscape-667x375', 667, 375)]:
        ctx = b.new_context(viewport={'width': w, 'height': h}, is_mobile=True, has_touch=True); pg = ctx.new_page()
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(URL); pg.wait_for_function("TalkPortrait.status.visible", timeout=10000)
        qa, panel = box(pg, '#qaToggle'), box(pg, '#panel')
        check(qa is not None and panel is None and pg.get_attribute('#qaToggle', 'aria-expanded') == 'false', f'{name}: QA button shown, panel closed by default', (qa, panel))
        check(qa and qa['w'] >= 44 and qa['h'] >= 40 and qa['x'] + qa['w'] <= w and qa['y'] >= 0, f'{name}: QA button touch-size, inside the screen (top-right)', qa)
        for side in ('left', 'right'):
            if side == 'right':
                pg.click('#qaToggle'); press(pg, '右'); pg.click('#qaToggle'); pg.wait_for_timeout(600)
            tp = box(pg, '#talkPortrait')
            hid = pg.evaluate(COVER, box(pg, '#qaToggle'))
            check(tp and pg.evaluate(S)['side'] == side and hid == 0 and box(pg, '#panel') is None, f'{name}: {side} portrait not covered by the QA button (no drawn pixel under it) or the panel', (tp, box(pg, '#qaToggle'), hid))
        pg.click('#qaToggle'); panel = box(pg, '#panel')
        check(panel is not None and pg.get_attribute('#qaToggle', 'aria-expanded') == 'true' and panel['y'] + panel['h'] <= h + .5 and panel['x'] >= 0, f'{name}: QA opens the panel inside the screen', panel)
        check(press(pg, '驚き') and pg.wait_for_function("TalkPortrait.status.face==='surprised'", timeout=5000) is not None, f'{name}: panel buttons usable while open')
        pg.click('#qaToggle'); check(box(pg, '#panel') is None, f'{name}: QA closes the panel again')
        pg.screenshot(path=os.path.join(os.environ.get('QA_OUT', '/tmp'), f'm43_{name}.png')) if os.environ.get('QA_OUT') else None
        ctx.close()
    # 2 rotation: landscape (closed) -> portrait (panel as before, no QA button) -> landscape (still works)
    ctx = b.new_context(viewport={'width': 844, 'height': 390}, is_mobile=True, has_touch=True); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(URL); pg.wait_for_function("TalkPortrait.status.visible", timeout=10000)
    pg.set_viewport_size({'width': 390, 'height': 844}); pg.wait_for_timeout(400)
    panel, tp = box(pg, '#panel'), box(pg, '#talkPortrait')
    check(box(pg, '#qaToggle') is None and panel is not None and not overlap(panel, tp) and not overlap(panel, box(pg, '#msg')), 'rotate to portrait: panel shown as before, QA button hidden, nothing over the portrait / text', (panel, tp))
    check(press(pg, '微笑み') and pg.wait_for_function("TalkPortrait.status.face==='smile'", timeout=5000) is not None, 'portrait: panel buttons usable')
    pg.set_viewport_size({'width': 844, 'height': 390}); pg.wait_for_timeout(400)
    check(box(pg, '#qaToggle') is not None and box(pg, '#panel') is None and pg.evaluate(S)['visible'], 'rotate back to landscape: panel folded, portrait still shown')
    pg.click('#qaToggle'); check(box(pg, '#panel') is not None, 'landscape after rotation: QA button still opens the panel'); pg.click('#qaToggle'); ctx.close()
    # 3 PC: unchanged (panel always shown, no QA button)
    ctx = b.new_context(viewport={'width': 1280, 'height': 720}); pg = ctx.new_page(); pg.goto(URL); pg.wait_for_function("TalkPortrait.status.visible", timeout=10000)
    check(box(pg, '#qaToggle') is None and box(pg, '#panel') is not None and not overlap(box(pg, '#panel'), box(pg, '#talkPortrait')), 'PC: panel as before, not over the portrait'); ctx.close()
    # 4 Phase 3 behaviour through the preview's own controls (portrait phone, panel visible)
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(URL); pg.wait_for_function("TalkPortrait.status.visible&&TalkPortrait.status.blinkReady", timeout=10000)
    seen = []
    for label, f in [('通常', 'normal'), ('微笑み', 'smile'), ('怒り', 'angry'), ('困り顔', 'worried'), ('伏し目', 'sad'), ('驚き', 'surprised')]:
        press(pg, label)
        try: pg.wait_for_function("f=>{const s=TalkPortrait.status;return s.face===f&&s.visible&&s.blinkReady&&s.eye===0}", arg=f, timeout=5000); seen.append(f)
        except Exception: pass
    check(seen == ['normal', 'smile', 'angry', 'worried', 'sad', 'surprised'], 'six faces shown through the preview buttons', seen)
    pg.evaluate("window.__m=0;window.__t=setInterval(()=>{window.__m=Math.max(window.__m,TalkPortrait.status.eye)},5)")
    try: pg.wait_for_function("window.__m>0", timeout=7500); nat = True
    except Exception: nat = False
    check(nat, 'a natural blink happens within 7.5 s (3-6 s gap)')
    pg.wait_for_function("TalkPortrait.status.eye===0"); pg.evaluate("window.__m=0"); press(pg, '今すぐ瞬き')
    try: pg.wait_for_function("window.__m===4&&TalkPortrait.status.eye===0", timeout=2000); now = True
    except Exception: now = False
    check(now, '"今すぐ瞬き" blinks at once (reaches fully closed, back to open)')
    press(pg, '隠す'); pg.wait_for_timeout(200); s = pg.evaluate(S)
    check(not s['visible'] and s['blink'] is None and 'timers 0' in pg.text_content('#status'), '"隠す": portrait gone, active blink timers 0 (status line too)', (s, pg.text_content('#status')))
    press(pg, '再表示')
    try: pg.wait_for_function("(()=>{const s=TalkPortrait.status;return s.visible&&s.blink&&s.blink.timers===1})()", timeout=5000); back = True
    except Exception: back = False
    check(back, '"再表示": portrait back, one blink timer')
    press(pg, '右'); pg.wait_for_function("TalkPortrait.status.side==='right'&&TalkPortrait.status.visible&&TalkPortrait.status.blink&&TalkPortrait.status.blink.timers===1", timeout=5000)
    pg.evaluate("window.__m=0")
    try: pg.wait_for_function("window.__m>0", timeout=7500); r_nat = True
    except Exception: r_nat = False
    pg.wait_for_function("TalkPortrait.status.eye===0"); pg.evaluate("window.__m=0"); press(pg, '今すぐ瞬き')
    try: pg.wait_for_function("window.__m===4", timeout=2000); r_now = True
    except Exception: r_now = False
    check(r_nat and r_now, 'after switching to the right: natural blink and "今すぐ瞬き" still work', (r_nat, r_now))
    ctx.close(); b.close()
check(not errs, 'no page errors', errs[:3])
print('FAILS', len(fails)); raise SystemExit(1 if fails else 0)

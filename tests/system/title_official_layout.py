"""TITLE-04 official title: layered art, real HTML controls, responsive/rotation/safe-area layout and existing title flows.
Screenshots are written to QA_OUT when it is set (outside the checkout)."""
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
ROOT = Path(__file__).resolve().parents[2]; fails = []
OUT = Path(os.environ['QA_OUT']).resolve() if os.environ.get('QA_OUT') else None
if OUT: assert not OUT.is_relative_to(ROOT), 'QA_OUT must be outside the checkout'; OUT.mkdir(parents=True, exist_ok=True)
def check(ok, name, detail=''):
    print(('ok   ' if ok else 'FAIL ') + name, detail if not ok else '')
    if not ok: fails.append(name)
# Approved artwork (TITLE-04 package): exact bytes, transparency where required.
SHA = {'background-landscape.png': '4d89ff88c67e54ec4676132c7fdfe2331265a69dcb910654c918db9a1a3a1eca', 'background-portrait.png': '5921d4906b74a2a1947783e242ed753dd2514f06d4cbfe58551cbfe3580d2275',
       'aidan-portrait.png': '0dd61691bde190605a175b3c222e36bb52fd151831c85297f01b1108d3a374a6', 'logo.png': 'e2135143a3500554ee63a08f8bcf1c0b3f302884680cb082d5018a5c92e8a87d'}
import hashlib
for name, digest in SHA.items():
    check(hashlib.sha256((ROOT / 'img/title' / name).read_bytes()).hexdigest() == digest, 'asset bytes unchanged: ' + name)
# Title hero since 2026-10-27: approved Aidan back view v2 (1152x1536 = the previous 1024x1536 figure frame + 64px transparent margin each side).
HERO = ROOT / 'assets/images/characters/aidan_back_v2.png'; HERO_W, HERO_PAD = 1152, 64
check(hashlib.sha256(HERO.read_bytes()).hexdigest() == '763648ab515a07d48100fa8991286374ce60761a08466cc71bbfbcc1894a9160', 'asset bytes unchanged: aidan_back_v2.png')
alpha = np.array(Image.open(HERO).convert('RGBA'))[..., 3] > 32
for path in (HERO, ROOT / 'img/title/logo.png'):
    a = np.array(Image.open(path).convert('RGBA'))[..., 3]
    check(a.min() == 0 and (a == 0).mean() > .2, path.name + ': real alpha transparency (not a baked checkerboard)')
VIEWPORTS = [('pc-1920x1080', 1920, 1080, False), ('pc-1280x720', 1280, 720, False), ('tablet-landscape-1024x768', 1024, 768, True), ('tablet-portrait-768x1024', 768, 1024, True),
             ('android-portrait-360x800', 360, 800, True), ('android-portrait-412x915', 412, 915, True), ('tall-portrait-360x780', 360, 780, True), ('small-portrait-320x568', 320, 568, True), ('tablet-portrait-820x1180', 820, 1180, True),
             ('phone-portrait-390x844', 390, 844, True), ('phone-portrait-360x640', 360, 640, True), ('phone-landscape-844x390', 844, 390, True), ('phone-landscape-667x375', 667, 375, True), ('ultrawide-2560x1080', 2560, 1080, False)]
GEO = """()=>{const box=e=>{if(!e||e.hidden||getComputedStyle(e).display==='none')return null;const b=e.getBoundingClientRect();return {x:b.left,y:b.top,w:b.width,h:b.height}};
 const q=s=>document.querySelector('#title-screen '+s),hero=q('.title-hero'),logo=q('.title-logo img');
 return {vw:innerWidth,vh:innerHeight,hero:box(hero),fg:box(q('.title-foreground')),logo:box(logo),msg:(()=>{const m=q('.title-message');if(!m)return null;const r=document.createRange();r.selectNodeContents(m);const b=r.getBoundingClientRect();return b.width?{x:b.left,y:b.top,w:b.width,h:b.height}:null})(),buttons:[...document.querySelectorAll('#title-screen .title-menu button')].map(b=>({t:b.textContent,...box(b)})),
  ratio:{hero:hero&&box(hero)?box(hero).w/box(hero).h:null,logo:box(logo)?box(logo).w/box(logo).h:null},
  bg:(getComputedStyle(q('.title-backdrop')).backgroundImage.match(/background-(landscape|portrait)/)||[])[1],
  imgs:[...document.querySelectorAll('#title-screen img')].map(i=>i.complete&&i.naturalWidth>0),
  baked:[...document.querySelectorAll('#title-screen img')].every(i=>!i.closest('button')),
  extra:[...document.querySelectorAll('#title-screen button')].map(b=>b.textContent).filter(t=>/OPTION|GALLERY/i.test(t)),
  pad:getComputedStyle(document.getElementById('title-screen')).paddingTop}}"""
def inside(r, g): return r is None or (r['x'] >= -0.5 and r['y'] >= -0.5 and r['x'] + r['w'] <= g['vw'] + .5 and r['y'] + r['h'] <= g['vh'] + .5)
def overlap(a, b): return bool(a and b and not (a['x'] + a['w'] <= b['x'] or b['x'] + b['w'] <= a['x'] or a['y'] + a['h'] <= b['y'] or b['y'] + b['h'] <= a['y']))
def frame(b):
    # the 2:3 figure frame inside the hero image (drops the transparent side margins)
    return b and {'x': b['x'] + b['w'] * HERO_PAD / HERO_W, 'y': b['y'], 'w': b['w'] * (HERO_W - 2 * HERO_PAD) / HERO_W, 'h': b['h']}
def hero_pixels(g, r):
    # Opaque Aidan pixels covered by a UI rectangle (bounding boxes alone include transparent margins).
    h = g['hero_box']
    if not h or not r: return 0
    x0, x1, y0, y1 = max(r['x'], h['x']), min(r['x'] + r['w'], h['x'] + h['w']), max(r['y'], h['y']), min(r['y'] + r['h'], h['y'] + h['h'])
    if x1 <= x0 or y1 <= y0: return 0
    H, W = alpha.shape; sx, sy = W / h['w'], H / h['h']
    return int(alpha[int((y0 - h['y']) * sy):int((y1 - h['y']) * sy) + 1, int((x0 - h['x']) * sx):int((x1 - h['x']) * sx) + 1].sum())
def layout(pg, name, landscape):
    pg.wait_for_function("[...document.querySelectorAll('#title-screen img')].every(i=>i.complete)"); pg.wait_for_timeout(150)
    g = pg.evaluate(GEO)
    g['hero_box'] = g['hero']; g['hero'] = frame(g['hero'])
    if g['hero']: g['ratio']['hero'] = g['hero']['w'] / g['hero']['h']; g['ratio']['hero_img'] = g['hero_box']['w'] / g['hero_box']['h']
    check(all(g['imgs']), f'{name}: art layers loaded')
    check(g['bg'] == ('landscape' if landscape else 'portrait'), f'{name}: {"landscape" if landscape else "portrait"} background', g['bg'])
    # TITLE-05: Aidan is shown in both orientations, bottom-left, feet on the bottom edge, head below the logo.
    h = g['hero']
    check(h is not None and h['x'] >= 0 and abs(h['y'] + h['h'] - g['vh']) < 1.5 and h['y'] >= (g['logo']['y'] + g['logo']['h'] if not landscape else -1) and h['x'] + h['w'] / 2 < g['vw'] / 2, f'{name}: Aidan bottom-left, uncropped, below the logo', h)
    if not landscape:
        # TITLE-05B: phones target 35-40% of the height (small phones may shrink for safety); tablets ~46%.
        share = h['h'] / g['vh']
        if g['vw'] < 600: check(.35 <= share <= .41 or (g['vw'] < 360 and share >= .24), f'{name}: portrait Aidan 35-40% of the height', round(share, 3))
        else: check(share >= .40, f'{name}: tablet portrait Aidan size', round(share, 3))
    check(pg.evaluate("[...document.querySelectorAll('#title-screen .title-menu button')].every(b=>{const r=b.getBoundingClientRect();return document.elementFromPoint(r.left+r.width/2,r.top+r.height/2)===b})"), f'{name}: buttons receive taps (not covered by art layers)')
    if g['hero']: check(abs(g['ratio']['hero_img'] - HERO_W / 1536) < .005 and abs(g['ratio']['hero'] - 1024 / 1536) < .005, f'{name}: Aidan aspect ratio kept', g['ratio'])
    check(abs(g['ratio']['logo'] - 2048 / 728) < .01, f'{name}: logo aspect ratio kept', g['ratio'])
    check(inside(g['logo'], g) and all(inside(b, g) for b in g['buttons']), f'{name}: logo and buttons fully inside the viewport', g)
    check(not any(overlap(g['logo'], b) for b in g['buttons']) and not overlap(*g['buttons'][:2]), f'{name}: logo and buttons do not overlap', g)
    check(all(hero_pixels(g, r) == 0 for r in [g['logo'], g['msg']] + g['buttons']), f'{name}: no UI (logo, buttons, status text) over Aidan', [hero_pixels(g, r) for r in [g['logo'], g['msg']] + g['buttons']])
    check([b['t'] for b in g['buttons']] == ['NEW GAME', 'CONTINUE'] and all(b['h'] >= 44 for b in g['buttons']) and g['baked'] and not g['extra'], f'{name}: real NEW GAME / CONTINUE buttons only, touch-size, OPTIONS/GALLERY absent', g['buttons'])
    # Title foreground (meadow PNG, 2026-10-27): spans both boot soles (back view v2: x 556-1084 of 1152 px) and stays off the logo / buttons.
    f, hb = g['fg'], g['hero_box']
    check(f is not None and hb is not None and f['x'] <= hb['x'] + hb['w'] * 556 / HERO_W and f['x'] + f['w'] >= hb['x'] + hb['w'] * 1084 / HERO_W and f['y'] <= hb['y'] + hb['h'] * 1460 / 1536,
          f'{name}: meadow foreground under both boots', (f, hb))
    check(not any(overlap(f, r) for r in [g['logo']] + g['buttons']), f'{name}: meadow foreground off the logo and buttons', f)
    if OUT: pg.screenshot(path=str(OUT / (name + '.png')))
    return g
with server(8817) as base, sync_playwright() as p:
    b = p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None))
    url = base + '/index.html?title=1'
    errors = []
    for name, w, h, touch in VIEWPORTS:
        c = b.new_context(viewport={'width': w, 'height': h}, has_touch=touch, is_mobile=touch); pg = c.new_page(); pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.goto(url); pg.wait_for_selector('#title-screen', state='visible'); layout(pg, name, w > h); c.close()
    # status text present (an unreadable SAVE gives the longest title message): it must not cover Aidan either
    for name, w, h in [('status-portrait-320x568', 320, 568), ('status-portrait-360x800', 360, 800), ('status-portrait-390x844', 390, 844), ('status-portrait-412x915', 412, 915), ('status-landscape-844x390', 844, 390)]:
        c = b.new_context(viewport={'width': w, 'height': h}, has_touch=True, is_mobile=True); c.add_init_script("try{localStorage.setItem('windbound_oath_v028','{}')}catch(e){}")
        pg = c.new_page(); pg.on('pageerror', lambda e: errors.append(str(e))); pg.goto(url); pg.wait_for_selector('#title-screen', state='visible')
        g = layout(pg, name, w > h); check(g['msg'] is not None and inside(g['msg'], g), f'{name}: status text shown inside the viewport', g['msg']); c.close()
    # rotation on the same page: portrait -> landscape -> portrait relayouts without reload
    c = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True); pg = c.new_page(); pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.goto(url); pg.wait_for_selector('#title-screen', state='visible'); layout(pg, 'rotate-0-portrait', False)
    pg.set_viewport_size({'width': 844, 'height': 390}); layout(pg, 'rotate-1-landscape', True)
    pg.set_viewport_size({'width': 390, 'height': 844}); layout(pg, 'rotate-2-portrait', False); c.close()
    # safe area: notch-style insets are honoured (CSS env() emulated through the custom properties)
    c = b.new_context(viewport={'width': 844, 'height': 390}, has_touch=True, is_mobile=True); pg = c.new_page()
    pg.goto(url); pg.wait_for_selector('#title-screen', state='visible')
    pg.add_style_tag(content='html body #title-screen{--safe-t:20px;--safe-r:44px;--safe-b:21px;--safe-l:44px}'); g = layout(pg, 'safe-area-landscape', True)
    check(g['hero']['x'] >= 44 and all(bt['x'] + bt['w'] <= g['vw'] - 44 and bt['y'] + bt['h'] <= g['vh'] - 21 for bt in g['buttons']), 'safe-area: Aidan and buttons stay clear of insets', g); c.close()
    # flows: no SAVE -> CONTINUE disabled; NEW GAME starts the actual opening and releases title input
    c = b.new_context(viewport={'width': 1280, 'height': 720}); pg = c.new_page(); pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.goto(url); pg.wait_for_selector('#title-screen', state='visible')
    check(pg.get_by_role('button', name='CONTINUE', exact=True).is_disabled() and pg.evaluate('LoadingInput.busy'), 'no SAVE: CONTINUE disabled, title owns input')
    pg.keyboard.press('ArrowRight'); pg.keyboard.press('m'); check(pg.evaluate("TitleScreen.active()&&InputManager.state()!=='MENU'"), 'title: game keys do not reach the field or menu')
    pg.get_by_role('button', name='NEW GAME', exact=True).click(); pg.wait_for_function("LoadCoordinator.phase==='READY'&&MossForest.active", timeout=20000)
    check(pg.evaluate("!TitleScreen.active()&&MossForest.mapId==='rilde_in_aidan'&&!document.documentElement.classList.contains('title-on')&&getComputedStyle(document.getElementById('title-screen')).display==='none'"), 'NEW GAME: actual opening, title hidden')
    pg.evaluate("closeDialogue();renderSystemTab('save');saveGrowthData()"); raw = pg.evaluate('localStorage.getItem(SAVE_KEY)'); check(raw is not None, 'SAVE written from the field')
    # CONTINUE: same SAVE restored, bytes unchanged
    pg.goto(url); pg.wait_for_selector('#title-screen', state='visible'); pg.wait_for_function("!document.querySelector('[data-loading-action=continue]').disabled")
    pg.get_by_role('button', name='CONTINUE', exact=True).click(); pg.wait_for_function("LoadCoordinator.phase==='READY'&&!TitleScreen.active()&&!LoadingInput.busy", timeout=20000)
    m = json.loads(raw)['prologue']['moss']
    check(pg.evaluate("[MossForest.mapId,MossForest.feet.x,MossForest.feet.y]") == [m['map'], m['x'] + 17, m['y'] + 42] and pg.evaluate('localStorage.getItem(SAVE_KEY)') == raw, 'CONTINUE: saved map/position restored, SAVE bytes unchanged')
    # NEW GAME with an existing SAVE (TITLE-05B): modal confirmation dialog; the menu never grows extra buttons
    pg.goto(url); pg.wait_for_selector('#title-screen', state='visible')
    check(pg.locator('#title-screen button:visible').all_inner_texts() == ['NEW GAME', 'CONTINUE'], 'normal title shows only NEW GAME and CONTINUE')
    pg.get_by_role('button', name='NEW GAME', exact=True).click()
    dlg = pg.get_by_role('alertdialog')
    check(dlg.is_visible() and dlg.get_attribute('aria-modal') == 'true' and '新しく始めますか？ セーブデータは削除されません。' in dlg.inner_text()
          and dlg.get_by_role('button').all_inner_texts() == ['はじめる', 'キャンセル'] and pg.locator('#title-screen .title-menu button').count() == 2, 'existing SAVE: modal dialog with はじめる / キャンセル, menu unchanged')
    check(pg.evaluate("[...document.querySelectorAll('#title-screen .title-menu button')].every(b=>b.disabled)") and pg.evaluate("document.activeElement.textContent") == 'キャンセル', 'dialog: background buttons disabled, focus moved into the dialog')
    hit = pg.evaluate("(()=>{const r=document.querySelector('[data-loading-action=new-game]').getBoundingClientRect();return document.elementFromPoint(r.left+r.width/2,r.top+r.height/2).closest('.title-confirm')!==null})()")
    pg.mouse.click(*pg.evaluate("(()=>{const r=document.querySelector('[data-loading-action=continue]').getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]})()"))
    check(hit and pg.evaluate('TitleScreen.active()') and dlg.is_visible(), 'dialog: taps on the background menu are blocked by the overlay')
    tabs = []
    for _ in range(4): pg.keyboard.press('Tab'); tabs.append(pg.evaluate('document.activeElement.textContent'))
    check(set(tabs) == {'はじめる', 'キャンセル'}, 'dialog: Tab focus stays inside the dialog', tabs)
    pg.set_viewport_size({'width': 390, 'height': 844}); pg.wait_for_timeout(150)
    check(all(inside(r, {'vw': 390, 'vh': 844}) for r in pg.evaluate("[...document.querySelectorAll('.title-confirm p,.title-confirm button')].map(e=>{const b=e.getBoundingClientRect();return {x:b.left,y:b.top,w:b.width,h:b.height}})")), 'dialog: stays inside the viewport after rotation')
    pg.set_viewport_size({'width': 1280, 'height': 720})
    pg.get_by_role('button', name='キャンセル', exact=True).click()
    check(pg.locator('.title-confirm').count() == 0 and pg.evaluate("document.activeElement.textContent") == 'NEW GAME' and pg.evaluate('TitleScreen.active()') and pg.evaluate('localStorage.getItem(SAVE_KEY)') == raw
          and pg.locator('#title-screen button:visible').all_inner_texts() == ['NEW GAME', 'CONTINUE'] and not pg.evaluate("document.querySelector('[data-loading-action=continue]').disabled"), 'cancel: back to the two buttons, focus on NEW GAME, SAVE untouched')
    # keyboard: Tab cycles only enabled title buttons; Enter on NEW GAME opens the dialog again
    pg.keyboard.press('Tab'); f1 = pg.evaluate('document.activeElement.textContent'); pg.keyboard.press('Tab'); f2 = pg.evaluate('document.activeElement.textContent')
    check({f1, f2} == {'NEW GAME', 'CONTINUE'}, 'keyboard Tab moves between NEW GAME and CONTINUE', (f1, f2))
    pg.evaluate("document.querySelector('[data-loading-action=new-game]').focus()"); pg.keyboard.press('Enter'); check(pg.get_by_role('alertdialog').is_visible(), 'keyboard Enter on NEW GAME opens the dialog')
    # はじめる: repeated activation starts exactly one new game; the SAVE is not erased
    gen0 = pg.evaluate('LoadCoordinator.generation'); enter0 = pg.evaluate('MossForest.enterCount')
    pg.evaluate("(()=>{const y=document.querySelector('[data-loading-action=confirm-new]');y.click();y.click();y.click()})()")
    pg.wait_for_function("LoadCoordinator.phase==='READY'&&MossForest.active&&!TitleScreen.active()", timeout=20000)
    pg.wait_for_timeout(600)
    check(pg.evaluate('LoadCoordinator.generation') - gen0 == 1 and pg.evaluate('MossForest.enterCount') - enter0 == 1 and pg.evaluate("MossForest.mapId") == 'rilde_in_aidan' and pg.evaluate('localStorage.getItem(SAVE_KEY)') == raw, 'はじめる: one new game start despite repeated presses, SAVE kept')
    c.close()
    # no SAVE: NEW GAME starts at once without any dialog (also checked above); here assert no dialog was created
    c = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True); pg = c.new_page()
    pg.goto(url); pg.wait_for_selector('#title-screen', state='visible'); pg.get_by_role('button', name='NEW GAME', exact=True).tap()
    pg.wait_for_function("LoadCoordinator.phase==='READY'&&MossForest.active", timeout=20000)
    check(pg.locator('.title-confirm').count() == 0 and not pg.evaluate('TitleScreen.active()'), 'no SAVE (touch): NEW GAME starts directly, no dialog'); c.close()
    # logo failure: text fallback, buttons still usable
    c = b.new_context(viewport={'width': 1280, 'height': 720}); c.route('**/img/title/logo.png', lambda r: r.abort()); pg = c.new_page()
    pg.goto(url); pg.wait_for_selector('#title-screen', state='visible'); pg.wait_for_function("document.querySelector('#title-screen .title-logo').classList.contains('title-logo-failed')")
    check(pg.locator('#title-screen .title-logo-text').is_visible() and pg.get_by_role('button', name='NEW GAME', exact=True).is_enabled(), 'logo load failure: text title shown, NEW GAME usable'); c.close()
    check(not errors, 'no page errors', errors[:3])
    b.close()
print('FAILS', len(fails)); sys.exit(1 if fails else 0)

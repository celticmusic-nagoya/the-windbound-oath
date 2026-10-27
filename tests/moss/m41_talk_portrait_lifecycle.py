# TalkPortrait lifecycle / async / layout regression (Issue #16: F-L-01 owner leftovers, F-L-02 async mis-display, F-L-03 css cache, F-L-04 frame).
# Ported from tests/moss/m31_talk_portrait_lifecycle.py (feature/asset-emma-01 @ f4456a82) to the common system (Phase 3): Fiona -> aidan, Lou -> 'test2'
# (a test-only registry entry that shows the same adopted images under another URL, so its requests can be held / failed independently).
# needs a static server on $PORT (default 8765) serving the tree under test; $STALE_CSS = main's css/style.css (for the css-cache fault injection).
# Runs unmodified against both the pre-fix and the fixed tree: the pre-fix tree is expected to FAIL the F-L cases (that is the reproduction).
import os, sys, json
from playwright.sync_api import sync_playwright
PORT = os.environ.get('PORT', '8765'); URL = 'http://localhost:%s/index.html' % PORT
STALE_CSS = os.environ.get('STALE_CSS', ''); OLD_CSS_V = '20261012c'   # main's css url; STALE_CSS = a copy of main's css/style.css (optional: the F3 fault injection is skipped without it)
errs = []; fails = []
def check(c, m):
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c: fails.append(m)
def T(i, lines): return {"npc": i, "entries": [{"id": i + "_e", "priority": 5, "when": {}, "mode": "cycle", "lines": lines}]}
FIONA = T('p_fiona', [{"char": "aidan", "face": "smile", "pages": ["フィオナ「こんにちは。」", "フィオナ「二枚目。」"]}])
F2L = T('p_f2l', [{"pages": [{"speaker": "フィオナ", "text": "「まずはフィオナ。」", "char": "aidan", "face": "smile"}, {"speaker": "ルー", "text": "「次はルー。」", "char": "test2", "face": "surprised"}, {"speaker": "ルー", "text": "「最後。」"}]}])
LOU = T('p_lou', [{"char": "test2", "face": "angry", "pages": ["ルー「ルーだよ。」"]}])
PLAIN = T('p_plain', [{"pages": ["案内人「立ち絵なしの会話。」"]}])
CHOICE = T('p_choice', [{"char": "aidan", "face": "worried", "pages": ["フィオナ「選んでね。」"], "choice": {"options": [{"label": "はい", "reply": "フィオナ「ありがとう。」", "set": {"p_yes": True}}, {"label": "いいえ", "reply": "フィオナ「そう。」"}]}}])
FAST = T('p_fast', [{"pages": [{"speaker": "A", "text": "「1」", "char": "aidan", "face": "smile"}, {"speaker": "A", "text": "「2」", "char": "test2", "face": "angry"}, {"speaker": "A", "text": "「3」", "char": "aidan", "face": "sad"}, {"speaker": "A", "text": "「4」", "char": "test2", "face": "worried"}, {"speaker": "A", "text": "「5」", "char": "aidan", "face": "angry"}, {"speaker": "A", "text": "「6」", "char": "test2", "face": "normal"}, {"speaker": "A", "text": "「7」", "char": "aidan", "face": "surprised"}, {"speaker": "A", "text": "「8」", "char": "test2", "face": "smile"}]}])
TABLES = [FIONA, F2L, LOU, PLAIN, CHOICE, FAST]
STATE = """(()=>{const e=document.getElementById('talkPortrait'),c=window.TalkPortrait.current,s=window.TalkPortrait.status;
  const vis=!!e&&!e.hidden&&getComputedStyle(e).display!=='none'&&e.getBoundingClientRect().width>0&&!!e.querySelector('canvas');
  return {vis,cur:c?c.char+'/'+c.face:null,owner:window.TalkPortrait.owner===undefined?'n/a':window.TalkPortrait.owner,imgs:e?e.querySelectorAll('canvas').length:0,src:c?c.char:'',timers:s.blink?s.blink.timers:0}})()"""
TEST2 = """PortraitRegistry.has('test2')||PortraitRegistry.define('test2',{name:'T2',src:{w:1024,h:1536},base:'assets/images/characters/portraits/aidan/',file:f=>'aidan_'+f+'.png?t2',
  crop:{x:290,y:0,w:700,h:700},faces:['normal','smile','angry','worried','sad','surprised']})"""
def boot(b, w=1280, h=720, touch=False, held=None):
    ctx = b.new_context(viewport={'width': w, 'height': h}, has_touch=touch, is_mobile=False); pg = ctx.new_page()
    pg.on('pageerror', lambda e: errs.append('PAGEERR ' + str(e))); pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
    if held is not None: pg.route('**/assets/images/characters/portraits/**', held)
    pg.goto(URL); pg.wait_for_timeout(2500); pg.evaluate('closeDialogue()'); pg.evaluate(TEST2)
    for t in TABLES: pg.evaluate("(t)=>FieldTalk.loadTable(t)", t)
    return ctx, pg
st = lambda pg: pg.evaluate(STATE)
def settle(pg, ms=600): pg.wait_for_timeout(ms)
def wait_vis(pg, cur, ms=6000):
    for _ in range(ms // 100):
        s = st(pg)
        if s['vis'] and s['cur'] == cur: return s
        pg.wait_for_timeout(100)
    return st(pg)
endcount = lambda pg: pg.evaluate("window.__ends||0")
def spy_end(pg): pg.evaluate("window.__ends=0;addEventListener('field-talk-end',()=>window.__ends++)")
def gone(s): return (not s['vis']) and s['cur'] is None   # nothing visible AND no remembered portrait (a css-hidden but still-owned portrait is the F-L-01 defect)

with sync_playwright() as p:
    b = p.chromium.launch()
    # ================= A. lifecycle (F-L-01) =================
    ctx, pg = boot(b); spy_end(pg)
    pg.evaluate("FieldTalk.talk('p_fiona')"); s = wait_vis(pg, 'aidan/smile')
    check(s['vis'] and s['cur'] == 'aidan/smile', 'A1 precondition: portrait really visible before generic close: %s' % s)
    pg.evaluate("closeDialogue()"); settle(pg); s = st(pg); check(gone(s), 'A1 generic closeDialogue() revokes the portrait: %s' % s)
    pg.evaluate("say('既存のsay経路')"); settle(pg); s = st(pg); check(gone(s) and 'say' in pg.evaluate("document.querySelector('#msg').textContent"), 'A1 legacy say() after generic close shows NO old portrait: %s' % s)
    check(endcount(pg) == 0, 'A1 no field-talk-end was fired by the generic close (story events untouched)')
    pg.evaluate("closeDialogue()")
    # say() replaces a live portrait conversation without closing
    pg.evaluate("FieldTalk.talk('p_fiona')"); wait_vis(pg, 'aidan/smile'); pg.evaluate("say('置き換え')"); settle(pg); s = st(pg)
    check(gone(s), 'A2 say() replacing a live portrait conversation revokes it: %s' % s); pg.evaluate("closeDialogue()")
    # FieldTalk.load
    pg.evaluate("FieldTalk.talk('p_fiona')"); s = wait_vis(pg, 'aidan/smile'); check(s['vis'], 'A3 precondition: visible before FieldTalk.load')
    flags0 = pg.evaluate("JSON.stringify(FieldTalk.serialize())"); ends0 = endcount(pg)
    pg.evaluate("FieldTalk.load({})"); settle(pg); s = st(pg); check(gone(s), 'A3 FieldTalk.load() discards the previous conversation portrait: %s' % s)
    check(endcount(pg) == ends0, 'A3 FieldTalk.load() did not dispatch field-talk-end')
    pg.evaluate("say('LOAD後のsay')"); settle(pg); check(gone(st(pg)), 'A3 say() after LOAD shows no old portrait'); pg.evaluate("closeDialogue()")
    pg.evaluate("(d)=>FieldTalk.load(JSON.parse(d))", flags0)
    # raw battleMode (no closeDialogue involved)
    pg.evaluate("FieldTalk.talk('p_fiona')"); s = wait_vis(pg, 'aidan/smile'); check(s['vis'], 'A5 precondition: visible before battleMode is set')
    pg.evaluate("document.body.classList.add('battleMode')"); settle(pg); s = st(pg); check(gone(s), 'A5 battleMode revokes the portrait itself (not only hides it by css): %s' % s)
    pg.evaluate("document.body.classList.remove('battleMode')"); settle(pg); pg.evaluate("say('戦闘後')"); settle(pg); check(gone(st(pg)), 'A5 leaving battleMode + say() does not resurrect it'); pg.evaluate("closeDialogue()")
    ctx.close()
    # real SAVE -> real LOAD (no DEV sandbox: the sandbox blocks saveGrowthData)
    ctx, pg = boot(b); spy_end(pg)
    pg.evaluate("document.querySelector('#menuOpen').click();renderSystemTab('save')"); pg.evaluate("document.querySelector('#doSave').click()")
    check(pg.evaluate("!!localStorage.getItem(SAVE_KEY)"), 'A4 real SAVE (menu button) wrote the save'); pg.evaluate("document.querySelector('#systemClose').click()")
    pg.evaluate("FieldTalk.talk('p_fiona')"); s = wait_vis(pg, 'aidan/smile'); check(s['vis'], 'A4 precondition: visible before real LOAD'); ends0 = endcount(pg)
    ok_load = pg.evaluate("loadGrowthData()"); check(ok_load is True, 'A4 real loadGrowthData() succeeded (returned %s)' % ok_load); pg.wait_for_timeout(900); s = st(pg)
    check(gone(s), 'A4 real SAVE -> real LOAD leaves no portrait: %s' % s); check(endcount(pg) == ends0, 'A4 LOAD fired no field-talk-end')
    pg.evaluate("document.querySelector('#systemClose').click();say('実LOAD後のsay')"); settle(pg); check(gone(st(pg)), 'A4 say() after real LOAD shows no old portrait')
    pg.evaluate("closeDialogue()"); ctx.close()
    # normal battle (real start, real RESULT)
    def to_result(pg, kind):
        pg.evaluate("PrologueCombat.instantKill('%s')" % kind); pg.wait_for_function("getComputedStyle(document.querySelector('#battleResult')).display==='grid'", timeout=60000); pg.wait_for_timeout(500)
        pg.locator('#resultContinue').click(); pg.wait_for_timeout(1500)
    ctx, pg = boot(b)
    pg.evaluate("devJump('forest')"); pg.wait_for_function("MossForest.active", timeout=20000); pg.wait_for_timeout(600); pg.evaluate("closeDialogue()")
    for t in TABLES: pg.evaluate("(t)=>FieldTalk.loadTable(t)", t)
    pg.evaluate("FieldTalk.talk('p_fiona')"); s = wait_vis(pg, 'aidan/smile'); check(s['vis'], 'A6 precondition: portrait really visible before the NORMAL battle starts: %s' % s)
    pg.evaluate("startAttackBattle('forestGob1',112)"); pg.wait_for_timeout(3500)
    check(pg.evaluate("document.body.classList.contains('battleMode')"), 'A6 normal battle really started'); check(gone(st(pg)), 'A6 portrait revoked during the normal battle: %s' % st(pg))
    to_result(pg, 'normal')
    pg.evaluate("say('通常戦RESULT後のsay')"); settle(pg); s = st(pg); check(gone(s), 'A6 after normal battle RESULT + say(): no old portrait: %s' % s); pg.evaluate("closeDialogue()"); ctx.close()
    # boss (raider) battle
    ctx, pg = boot(b)
    pg.evaluate("devJump('forest')"); pg.wait_for_function("MossForest.active", timeout=20000); pg.wait_for_timeout(600); pg.evaluate("closeDialogue()")
    for t in TABLES: pg.evaluate("(t)=>FieldTalk.loadTable(t)", t)
    pg.evaluate("FieldTalk.talk('p_fiona')"); s = wait_vis(pg, 'aidan/smile'); check(s['vis'], 'A7 precondition: portrait really visible before the BOSS battle starts: %s' % s)
    pg.evaluate("startRaiderBattle()"); pg.wait_for_timeout(2500)
    check(pg.evaluate("document.body.classList.contains('raiderBattleMode')"), 'A7 boss battle really started'); check(gone(st(pg)), 'A7 portrait revoked during the boss battle: %s' % st(pg))
    to_result(pg, 'raider')
    pg.evaluate("say('ボス戦RESULT後のsay')"); settle(pg); s = st(pg); check(gone(s), 'A7 after boss RESULT + say(): no old portrait: %s' % s); pg.evaluate("closeDialogue()")
    ctx.close()
    # repeated start / end
    ctx, pg = boot(b); spy_end(pg); ok = True; detail = []
    for i in range(7):
        pg.evaluate("FieldTalk.talk('%s')" % ('p_fiona' if i % 2 == 0 else 'p_lou')); want = 'aidan/smile' if i % 2 == 0 else 'test2/angry'
        s = wait_vis(pg, want); ok &= s['vis'] and s['cur'] == want and s['imgs'] == 1
        pages = 2 if i % 2 == 0 else 1
        for _ in range(pages): pg.click('#msg'); pg.wait_for_timeout(120)
        pg.wait_for_timeout(250); s2 = st(pg); ok &= gone(s2); detail.append((want, s['vis'], s2['vis']))
        if i == 3: pg.evaluate("say('途中の既存say')"); settle(pg, 200); ok &= gone(st(pg)); pg.evaluate("closeDialogue()")
    check(ok, 'A8 7 consecutive start/end cycles (alternating characters): correct portrait each time, gone after each end, 1 <img> max: %s' % detail)
    check(endcount(pg) == 7, 'A8 field-talk-end fired exactly once per real conversation (7), none extra: %s' % endcount(pg))
    ctx.close()
    # ================= B. async (F-L-02) =================
    held = []; gate = {'lou': False}
    def handler(route, *_):
        if gate['lou'] and '?t2' in route.request.url: held.append(route)
        else: route.continue_()
    ctx, pg = boot(b, held=handler); spy_end(pg)
    def release(mode='ok'):
        rs = list(held); held.clear()
        for r in rs:
            try: (r.continue_() if mode == 'ok' else r.abort())
            except Exception as e: print('release', e)
    # B1 Fiona -> Lou with the Lou image delayed
    gate['lou'] = True; pg.evaluate("FieldTalk.talk('p_f2l')"); s = wait_vis(pg, 'aidan/smile'); check(s['vis'], 'B1 precondition: Fiona visible, Lou request not yet answered')
    pg.click('#msg'); pg.wait_for_timeout(700); s = st(pg); txt = pg.evaluate("document.querySelector('#msg').textContent")
    check('次はルー' in txt and len(held) >= 1, 'B1 Lou page is on screen while the Lou image is still pending (held=%d)' % len(held))
    check(not s['vis'] and s['cur'] is None, 'B1 Fiona is NOT shown with Lou\'s line while Lou loads: %s' % s)
    pg.click('#msg'); pg.wait_for_timeout(300); check('最後' in pg.evaluate("document.querySelector('#msg').textContent"), 'B1 page advance is not blocked by the pending image')
    gate['lou'] = False; release('ok'); s = wait_vis(pg, 'test2/normal', 3000); check(s['vis'] and s['cur'] == 'test2/normal' and s['src'] == 'test2', 'B1 when the Lou image arrives it is shown for the page that is current now (3rd page: Lou inherited, no face -> normal): %s' % s)
    pg.click('#msg'); settle(pg, 300); check(gone(st(pg)), 'B1 conversation end hides it')
    # B2 Lou loading -> conversation ends -> old request completes (success)
    ctx.close(); held.clear(); gate['lou'] = True
    ctx, pg = boot(b, held=handler); spy_end(pg)
    pg.evaluate("FieldTalk.talk('p_lou')"); pg.wait_for_timeout(500); check(len(held) >= 1 and gone(st(pg)), 'B2 precondition: Lou request pending, nothing shown yet: held=%d %s' % (len(held), st(pg)))
    pg.click('#msg'); settle(pg, 300); check(endcount(pg) == 1, 'B2 conversation ended while loading')
    gate['lou'] = False; release('ok'); settle(pg, 900); s = st(pg); check(gone(s), 'B2 late SUCCESS of an ended conversation\'s image changes nothing: %s' % s)
    pg.evaluate("say('終了後の既存say')"); settle(pg); check(gone(st(pg)), 'B2 and a following say() still shows no portrait'); pg.evaluate("closeDialogue()")
    # B3 Lou loading -> a different conversation starts
    ctx.close(); held.clear(); gate['lou'] = True
    ctx, pg = boot(b, held=handler)
    pg.evaluate("FieldTalk.talk('p_lou')"); pg.wait_for_timeout(500); pg.evaluate("FieldTalk.talk('p_plain')"); pg.wait_for_timeout(300)
    gate['lou'] = False; release('ok'); settle(pg, 900); s = st(pg); check(gone(s) and '立ち絵なし' in pg.evaluate("document.querySelector('#msg').textContent"), 'B3 Lou pending -> plain conversation starts -> late Lou image never appears on it: %s' % s)
    pg.evaluate("closeDialogue()"); ctx.close(); held.clear(); gate['lou'] = True
    ctx, pg = boot(b, held=handler)
    pg.evaluate("FieldTalk.talk('p_lou')"); pg.wait_for_timeout(500); pg.evaluate("FieldTalk.talk('p_fiona')"); s = wait_vis(pg, 'aidan/smile')
    gate['lou'] = False; release('ok'); settle(pg, 900); s = st(pg); check(s['vis'] and s['cur'] == 'aidan/smile', 'B3 Lou pending -> Fiona conversation starts -> late Lou image does not replace Fiona: %s' % s)
    # B4 late FAILURE of an old request
    pg.evaluate("closeDialogue()"); ctx.close(); held.clear(); gate['lou'] = True
    ctx, pg = boot(b, held=handler); spy_end(pg)
    pg.evaluate("FieldTalk.talk('p_lou')"); pg.wait_for_timeout(500); pg.click('#msg'); settle(pg, 200)
    pg.evaluate("FieldTalk.talk('p_plain')"); gate['lou'] = False; release('abort'); settle(pg, 900); s = st(pg)
    check(gone(s) and '立ち絵なし' in pg.evaluate("document.querySelector('#msg').textContent"), 'B4 late FAILURE (and its normal fallback) of an old request changes nothing: %s' % s)
    # B5 old fallback request completes after the conversation ended
    pg.evaluate("closeDialogue()"); ctx.close(); held.clear(); gate['lou'] = True
    ctx, pg = boot(b, held=handler)
    pg.evaluate("FieldTalk.talk('p_lou')"); pg.wait_for_timeout(500); first = list(held); held.clear()
    for r in first: r.abort()                       # lou_angry fails -> fallback to lou_normal is requested (and held)
    pg.wait_for_timeout(500); check(len(held) >= 1, 'B5 precondition: the normal-fallback request is pending: held=%d' % len(held))
    pg.click('#msg'); settle(pg, 300); gate['lou'] = False; release('ok'); settle(pg, 900); s = st(pg); check(gone(s), 'B5 old fallback completing after the end changes nothing: %s' % s)
    # B6 rapid page flipping (no waits between taps)
    pg.evaluate("closeDialogue()"); ctx.close(); held.clear(); gate['lou'] = False
    ctx, pg = boot(b, held=handler); spy_end(pg)
    pg.evaluate("FieldTalk.talk('p_fast')"); wait_vis(pg, 'aidan/smile')
    pg.evaluate("for(let i=0;i<7;i++)document.querySelector('#msg').click()"); pg.wait_for_timeout(1500); s = st(pg); txt = pg.evaluate("document.querySelector('#msg').textContent")
    check('8' in txt and s['vis'] and s['cur'] == 'test2/smile' and s['imgs'] == 1 and s['timers'] <= 1, 'B6 7 taps in one frame: the last page\'s portrait (test2/smile) and nothing else, at most one blink timer: %s' % s)
    pg.evaluate("document.querySelector('#msg').click()"); settle(pg, 300); check(gone(st(pg)) and endcount(pg) == 1, 'B6 final tap ends it cleanly')
    # B7 every intermediate state matches its page (sampled after each settle)
    pg.evaluate("FieldTalk.talk('p_fast')"); exp = ['aidan/smile', 'test2/angry', 'aidan/sad', 'test2/worried', 'aidan/angry', 'test2/normal', 'aidan/surprised', 'test2/smile']; bad = []
    for i, e in enumerate(exp):
        s = wait_vis(pg, e, 4000)
        if not (s['vis'] and s['cur'] == e): bad.append((i, e, s['cur']))
        if i < len(exp) - 1: pg.click('#msg'); pg.wait_for_timeout(30)
    check(not bad, 'B7 fast paging (30ms between taps) always settles on the current page\'s portrait: %s' % bad)
    pg.evaluate("closeDialogue()"); ctx.close()
    # ================= C. display / input / css cache =================
    VPS = {'phone_portrait': (390, 844), 'phone_landscape': (844, 390), 'small_phone': (360, 640), 'tablet_portrait': (768, 1024), 'tablet_landscape': (1024, 768), 'pc': (1440, 900)}
    ctx, pg = boot(b)
    gaps = {}
    for name, (w, h) in VPS.items():
        pg.set_viewport_size({'width': w, 'height': h})
        res = {}
        for ch, tid, want in (('aidan', 'p_fiona', 'aidan/smile'), ('test2', 'p_lou', 'test2/angry')):
            pg.evaluate("FieldTalk.talk('%s')" % tid); wait_vis(pg, want); pg.wait_for_timeout(300)
            g = pg.evaluate("(()=>{const e=document.getElementById('talkPortrait'),i=e.querySelector('canvas'),a=e.getBoundingClientRect(),c=i.getBoundingClientRect(),m=document.getElementById('msg').getBoundingClientRect();return {box:[a.left,a.top,a.right,a.bottom,a.width,a.height],img:[c.width,c.height],msgTop:m.top,msgBottom:m.bottom,iw:innerWidth,ih:innerHeight,pe:getComputedStyle(e).pointerEvents}})()")
            res[ch] = g; b_ = g['box']
            check(b_[0] >= -1 and b_[2] <= g['iw'] + 1 and b_[1] >= -1 and b_[3] <= g['ih'] + 1, 'C1 %s/%s: frame inside the viewport %s' % (name, ch, [round(x) for x in b_]))
            check(b_[3] <= g['msgTop'] + 6, 'C2 %s/%s: frame never overlaps the dialogue text box (bottom %d <= msg top %d)' % (name, ch, b_[3], g['msgTop']))
            check(g['pe'] == 'none' and b_[5] >= min(g['ih'] * 0.2, 150), 'C3 %s/%s: pointer-events none, reasonable height %d' % (name, ch, b_[5]))
            check(abs(b_[4] / b_[5] - 1) < 0.015 and abs(g['img'][0] - b_[4]) <= 1 and abs(g['img'][1] - b_[5]) <= 1, 'D1 %s/%s: frame keeps the crop aspect (%.3f) and the canvas fills it exactly' % (name, ch, b_[4] / b_[5]))
            pg.evaluate("closeDialogue()")
        gl, gf = res['test2'], res['aidan']
        gaps[name] = (gl['msgTop'] - gl['box'][3], gf['msgTop'] - gf['box'][3])
        check(abs(gaps[name][0] - gaps[name][1]) <= 3 and gaps[name][0] <= 10, 'D2 %s: frame-bottom to msg gap is the same for both characters and small: %s' % (name, [round(x, 1) for x in gaps[name]]))
        pg.screenshot(path='/tmp/p2_shot_%s.png' % name) if False else None
    ctx.close()
    # choices by touch
    ctx, pg = boot(b, 390, 844, touch=True)
    pg.evaluate("FieldTalk.talk('p_choice')"); wait_vis(pg, 'aidan/worried'); pg.wait_for_timeout(300)
    r = pg.evaluate("(()=>{const bt=document.querySelector('#msg .talkChoices button'),a=bt.getBoundingClientRect(),x=a.left+a.width/2,y=a.top+a.height/2,top=document.elementFromPoint(x,y);return {x,y,hit:top===bt||bt.contains(top),tag:top&&top.id||top&&top.tagName}})()")
    check(r['hit'], 'C4 the choice button is what a touch at its centre reaches (portrait does not intercept): %s' % r)
    pg.touchscreen.tap(r['x'], r['y']); pg.wait_for_timeout(400)
    check(pg.evaluate("!!FieldTalk.serialize().flags.p_yes") and 'ありがとう' in pg.evaluate("document.querySelector('#msg').textContent"), 'C4 touch on はい selected it (flag set, reply shown) with the portrait on screen')
    pg.locator('#msg').tap(); pg.wait_for_timeout(500); check(gone(st(pg)), 'C4 tapping through the reply ends it and hides the portrait'); ctx.close()
    # css cache (F-L-03)
    stale = open(STALE_CSS, encoding='utf-8').read() if STALE_CSS else ''; reqs = []
    def css_h(route, *_):
        u = route.request.url; reqs.append(u)
        if 'css/style.css' in u and ('v=' + OLD_CSS_V) in u: return route.fulfill(status=200, content_type='text/css', body=stale)   # a browser still holding main's css for the old URL
        route.continue_()
    ctx = b.new_context(viewport={'width': 390, 'height': 844}); pg = ctx.new_page(); pg.route('**/*.css*', css_h)
    pg.on('pageerror', lambda e: errs.append('PAGEERR ' + str(e))); pg.goto(URL); pg.wait_for_timeout(2500); pg.evaluate('closeDialogue()')
    for t in TABLES: pg.evaluate("(t)=>FieldTalk.loadTable(t)", t)
    href = pg.evaluate("document.querySelector('link[href*=\"css/style.css\"]').getAttribute('href')")
    check(('v=' + OLD_CSS_V) not in href, 'F3a index.html no longer references main\'s css version (%s)' % href)
    check(not any('css/style.css' in u and ('v=' + OLD_CSS_V) in u for u in reqs), 'F3a no request used the old css URL, so an old cached css cannot be applied')
    pg.evaluate("FieldTalk.talk('p_fiona')"); wait_vis(pg, 'aidan/smile'); pos = pg.evaluate("getComputedStyle(document.getElementById('talkPortrait')).position"); ar = pg.evaluate("document.getElementById('talkPortrait').getBoundingClientRect().bottom<=document.getElementById('msg').getBoundingClientRect().top+6")
    check(pos == 'fixed' and ar, 'F3b with the stale-main-css injection armed, the new URL still gets the portrait css (position=%s, above msg=%s)' % (pos, ar))
    pg.evaluate("closeDialogue()")
    # fault injection: pretend the page still pointed at the old URL -> stale css applies -> portrait css missing (documents what the version bump prevents)
    pg.evaluate("(v)=>{const l=document.querySelector('link[href*=\"css/style.css\"]');l.href='css/style.css?v='+v}", OLD_CSS_V); pg.wait_for_timeout(800)
    pos2 = pg.evaluate("getComputedStyle(document.getElementById('talkPortrait')||document.body).position")
    check(not stale or pos2 != 'fixed', 'F3c fault injection works: the OLD css url yields no portrait rule (position=%s) => the bump is what makes the new css load' % pos2)
    ctx.close()
    check(not [e for e in errs if 'ERR_FAILED' not in e and 'ERR_ABORTED' not in e and 'Failed to load resource' not in e], 'Z no unexpected page errors: %s' % [e for e in errs if 'ERR_FAILED' not in e and 'ERR_ABORTED' not in e and 'Failed to load resource' not in e][:3])
    b.close()
print('FAILS', len(fails)); sys.exit(1 if fails else 0)

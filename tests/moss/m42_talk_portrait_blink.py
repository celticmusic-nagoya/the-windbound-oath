# TalkPortrait blink (common system, Phase 3): timing in the real game, one timer, no stale overlays, cleanup on every way a conversation can end,
# hidden page, reduced motion, still portraits. Covers the directive's 10-2 list (blink in every face, mid-blink face / speaker change, mid-blink end).
import os
from playwright.sync_api import sync_playwright
URL = 'http://localhost:%s/index.html' % os.environ.get('PORT', '8765')
errs = []; fails = []
def check(c, m):
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c: fails.append(m)
FACES = ['normal', 'smile', 'angry', 'worried', 'sad', 'surprised']
TEST2 = """PortraitRegistry.has('test2')||PortraitRegistry.define('test2',{name:'T2',src:{w:1024,h:1536},base:'assets/images/characters/portraits/aidan/',file:f=>'aidan_'+f+'.png?t2',
  crop:{x:290,y:0,w:700,h:700},faces:['normal','smile','angry','worried','sad','surprised']})"""   # a still portrait (no blink entry)
def T(i, lines): return {"npc": i, "entries": [{"id": i + "_e", "priority": 5, "when": {}, "mode": "cycle", "lines": lines}]}
TABLES = [T('b_faces', [{"char": "aidan", "face": "normal", "pages": [{"speaker": "エイダン", "text": "「%s」" % f, "face": f} for f in FACES]}]),
          T('b_swap', [{"pages": [{"speaker": "エイダン", "text": "「1」", "char": "aidan", "face": "normal"}, {"speaker": "T2", "text": "「2」", "char": "test2", "face": "smile"}, {"speaker": "エイダン", "text": "「3」", "char": "aidan", "face": "sad"}]}]),
          T('b_one', [{"char": "aidan", "face": "smile", "pages": ["エイダン「一枚。」"]}])]
# blink trace: every state the renderer draws, with time (wraps the canvas data-eye attribute)
TRACE = """window.__eye=[];new MutationObserver(()=>{const e=document.getElementById('talkPortrait');if(e)window.__eye.push([performance.now(),+(e.dataset.eye||0),e.dataset.face||''])}).observe(document.body,{subtree:true,attributes:true,attributeFilter:['data-eye']})"""
S = "TalkPortrait.status"
def boot(b, reduced=False, w=1280, h=720):
    ctx = b.new_context(viewport={'width': w, 'height': h}, reduced_motion='reduce' if reduced else 'no-preference'); pg = ctx.new_page()
    pg.on('pageerror', lambda e: errs.append('PAGEERR ' + str(e))); pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
    pg.goto(URL); pg.wait_for_timeout(2500); pg.evaluate('closeDialogue()'); pg.evaluate(TEST2)
    for t in TABLES: pg.evaluate("(t)=>FieldTalk.loadTable(t)", t)
    pg.evaluate(TRACE); return ctx, pg
def blinks(trace):
    """split the trace into blinks: sequences of states starting from 1 after 0"""
    out, curb = [], None
    for t, s, f in trace:
        if s == 1 and (curb is None or curb[-1][1] == 0): curb = [(t, s, f)]; out.append(curb)
        elif curb is not None: curb.append((t, s, f))
    return out
with sync_playwright() as p:
    b = p.chromium.launch()
    # 1 natural blinking in the real game: sequence, duration, gaps, one timer, every face
    ctx, pg = boot(b)
    pg.evaluate("FieldTalk.talk('b_one')"); pg.wait_for_timeout(600)
    s = pg.evaluate(S); check(s['visible'] and s['blinkReady'] and s['blink']['running'] and s['blink']['timers'] == 1, '1a portrait shown, blink controller running with exactly one timer: %s' % s)
    pg.evaluate("window.__eye=[]"); pg.wait_for_timeout(19500)
    tr = pg.evaluate("window.__eye"); bl = [x for x in blinks(tr) if x[-1][1] == 0]
    seqs = {tuple(s for _, s, _ in x) for x in bl}
    check(len(bl) >= 3 and seqs == {(1, 2, 3, 4, 3, 2, 1, 0)}, '1b %d natural blinks in 19.5 s, every one 30->60->85->100->85->60->30 %%->open: %s' % (len(bl), seqs))
    durs = [round(x[-1][0] - x[0][0]) for x in bl]; check(all(230 <= d <= 330 for d in durs), '1c each blink lasts ~260 ms: %s' % durs)
    gaps = [round(bl[i][0][0] - bl[i - 1][-1][0]) for i in range(1, len(bl))]; check(all(2900 <= g <= 6200 for g in gaps), '1d gaps between blinks 3-6 s: %s' % gaps)
    check(pg.evaluate(S)['blink']['timers'] == 1, '1e still exactly one timer after many blinks')
    pg.click('#msg'); pg.wait_for_timeout(300); check(pg.evaluate(S)['blink'] is None and not pg.evaluate(S)['visible'], '1f conversation end: portrait gone, no blink controller')
    # every face blinks (forced blink on each page)
    pg.evaluate("FieldTalk.talk('b_faces')"); pg.wait_for_timeout(600); ok = []
    for i, f in enumerate(FACES):
        # wait for the forced blink to finish (back to open) instead of a fixed 400 ms: under CPU load the 260 ms blink can run late
        # and only after this page's face is on screen with its overlays loaded (the first load can exceed 600 ms under load)
        try: pg.wait_for_function("(f)=>{const s=TalkPortrait.status;return s.visible&&s.face===f&&s.blinkReady&&s.blink&&s.blink.timers===1}", arg=f, timeout=5000)
        except Exception: pass
        pg.evaluate("window.__eye=[]"); pg.evaluate("TalkPortrait.blinkNow()")
        try: pg.wait_for_function("window.__eye.length>=8&&window.__eye[window.__eye.length-1][1]===0", timeout=2000)
        except Exception: pass
        pg.wait_for_timeout(50)
        tr = pg.evaluate("window.__eye"); ok.append((f, [s for _, s, _ in tr], {x for _, _, x in tr}))
        if i < len(FACES) - 1: pg.click('#msg'); pg.wait_for_timeout(600)
    check(all(st == [1, 2, 3, 4, 3, 2, 1, 0] and fs == {f} for f, st, fs in ok), '1g each of the six faces blinks with its own overlays: %s' % [(f, st, sorted(fs)) for f, st, fs in ok])
    pg.evaluate("closeDialogue()"); pg.wait_for_timeout(300)
    # 2 mid-blink expression change: the blink stops, the new face appears open, no old overlay is drawn on it, one timer
    pg.evaluate("FieldTalk.talk('b_faces')"); pg.wait_for_timeout(600)
    pg.evaluate("window.__eye=[]"); pg.evaluate("TalkPortrait.blinkNow()"); pg.wait_for_timeout(75)   # ~state 3
    mid = pg.evaluate(S)['eye']; pg.click('#msg'); pg.wait_for_timeout(700); s = pg.evaluate(S); tr = pg.evaluate("window.__eye")
    after = [x for x in tr if x[2] == 'smile']
    check(mid in (2, 3, 4) and s['face'] == 'smile' and s['eye'] == 0 and all(x[1] == 0 for x in after), '2a mid-blink (state %s) face change -> smile shown open, never with an overlay: %s' % (mid, after[:4]))
    check(s['blink'] and s['blink']['timers'] == 1 and s['blink']['state'] == 0, '2b a fresh schedule for the new face, one timer: %s' % s['blink'])
    pg.evaluate("closeDialogue()")
    # 3 mid-blink speaker change: Aidan -> still portrait (test2) -> Aidan
    pg.evaluate("FieldTalk.talk('b_swap')"); pg.wait_for_timeout(600); pg.evaluate("TalkPortrait.blinkNow()"); pg.wait_for_timeout(75)
    pg.click('#msg'); pg.wait_for_timeout(700); s = pg.evaluate(S)
    check(s['char'] == 'test2' and s['eye'] == 0 and s['blink'] is None and not s['blinkReady'], '3a mid-blink speaker change to a character without blink: still portrait, no timer: %s' % s)
    pg.wait_for_timeout(6500); check(pg.evaluate(S)['eye'] == 0 and pg.evaluate(S)['blink'] is None, '3b the still portrait never blinks (6.5 s)')
    pg.click('#msg'); pg.wait_for_timeout(700); s = pg.evaluate(S); check(s['char'] == 'aidan' and s['face'] == 'sad' and s['blink'] and s['blink']['timers'] == 1, '3c back to Aidan: blinking again, one timer: %s' % s)
    # 4 mid-blink end / cancel / revoke / LOAD / battle: no timer left, nothing drawn afterwards
    def mid_blink_then(action, label):
        pg.evaluate("closeDialogue()"); pg.evaluate("FieldTalk.talk('b_one')"); pg.wait_for_timeout(600); pg.evaluate("TalkPortrait.blinkNow()"); pg.wait_for_timeout(75)
        pg.evaluate(action); pg.wait_for_timeout(300); pg.evaluate("window.__eye=[]"); pg.wait_for_timeout(6500)
        s = pg.evaluate(S); check(not s['visible'] and s['blink'] is None and pg.evaluate("window.__eye.length") == 0, '4 %s mid-blink: portrait gone, no blink timer, nothing drawn for 6.5 s: %s' % (label, s))
    mid_blink_then("document.querySelector('#msg').click()", 'conversation end (last page)')
    mid_blink_then("FieldTalk.cancel()", 'FieldTalk.cancel()')
    mid_blink_then("closeDialogue()", 'generic closeDialogue()')
    mid_blink_then("FieldTalk.load(FieldTalk.serialize())", 'FieldTalk.load() (LOAD)')
    mid_blink_then("document.body.classList.add('battleMode')", 'battle start (battleMode)'); pg.evaluate("document.body.classList.remove('battleMode')")
    mid_blink_then("say('既存のsay')", 'say() replacing the conversation'); pg.evaluate("closeDialogue()")
    # 5 repeated conversations never stack timers
    for i in range(6): pg.evaluate("FieldTalk.talk('b_one')"); pg.wait_for_timeout(250); pg.click('#msg'); pg.wait_for_timeout(150)
    pg.evaluate("FieldTalk.talk('b_one')"); pg.wait_for_timeout(500); s = pg.evaluate(S); check(s['blink']['timers'] == 1, '5 after 7 conversations: exactly one blink timer: %s' % s['blink'])
    # 6 hidden page: no drawing while hidden, resumes after
    pg.evaluate("Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});document.dispatchEvent(new Event('visibilitychange'))"); pg.evaluate("window.__eye=[]")
    pg.wait_for_timeout(7000); s = pg.evaluate(S); check(s['blink'] is None and pg.evaluate("window.__eye.length") == 0 and s['eye'] == 0, '6a hidden page: blink stopped, nothing drawn for 7 s: %s' % s)
    pg.evaluate("Object.defineProperty(document,'hidden',{configurable:true,get:()=>false});document.dispatchEvent(new Event('visibilitychange'))"); pg.wait_for_timeout(200)
    check(pg.evaluate(S)['blink']['timers'] == 1, '6b visible again: blinking resumes with one timer')
    pg.evaluate("closeDialogue()"); ctx.close()
    # 7 reduced motion: portrait shown open, never blinks
    ctx, pg = boot(b, reduced=True)
    pg.evaluate("FieldTalk.talk('b_one')"); pg.wait_for_timeout(600); pg.evaluate("window.__eye=[]"); pg.wait_for_timeout(7000); s = pg.evaluate(S)
    check(s['visible'] and s['reduced'] and s['blink'] is None and pg.evaluate("window.__eye.length") == 0, '7 prefers-reduced-motion: portrait shown, no blinking for 7 s: %s' % s)
    pg.evaluate("closeDialogue()"); ctx.close()
    # 8 an event/story scene taking the screen revokes the portrait (no overlap with event CGs)
    ctx, pg = boot(b)
    pg.evaluate("FieldTalk.talk('b_one')"); pg.wait_for_timeout(600)
    pg.evaluate("const e=document.getElementById('altarScene');e&&(e.style.display='block')"); pg.wait_for_timeout(300); s = pg.evaluate(S)
    has = pg.evaluate("!!document.getElementById('altarScene')")
    check((not has) or (not s['visible'] and s['blink'] is None), '8 a story scene (altarScene, where event CGs are drawn) opening revokes the portrait: present=%s %s' % (has, s))
    pg.evaluate("const e=document.getElementById('altarScene');e&&(e.style.display='none')"); ctx.close()
    errs[:] = [e for e in errs if 'ERR_FAILED' not in e and 'Failed to load resource' not in e]
    check(not errs, 'no page errors / console errors: %s' % errs[:3])
    b.close()
print('FAILS', len(fails)); raise SystemExit(1 if fails else 0)

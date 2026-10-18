# Issue #16 re-QA: a late startup opening line vs. a test conversation. needs http.server 8765.
# A: opening delayed 4.5 s (simulated slow machine) lands on a running Fiona conversation -> P2 must revoke the portrait (no stale Fiona, owner null).
# B: after the opening has been shown the same conversation is stable (precondition gate used by tests/support/run_python_ready.py).
from playwright.sync_api import sync_playwright
fails = []; errs = []
def check(c, m):
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c: fails.append(m)
TABLE = {"npc": "t_race", "entries": [{"id": "t_r1", "priority": 10, "when": {}, "mode": "cycle", "lines": [{"char": "fiona", "face": "smile", "pages": ["フィオナ「こんにちは。」", "フィオナ「二つ目。」"]}]}]}
INIT = """(()=>{const st=window.setTimeout;window.setTimeout=function(f,d,...a){if(d===350&&typeof f==='function'&&String(f).includes('\\u671d\\u306e\\u98a8'))d=350+4500;return st.call(window,f,d,...a)};
window.__openingSeen=false;const mo=()=>{const m=document.getElementById('msg');if(!m){requestAnimationFrame(mo);return}new MutationObserver(()=>{if((m.textContent||'').includes('\\u671d\\u306e\\u98a8'))window.__openingSeen=true}).observe(m,{childList:true,subtree:true,characterData:true})};mo()})();"""
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1280, 'height': 720})
    pg.on('pageerror', lambda e: errs.append('PAGEERR ' + str(e)))
    st = lambda: pg.evaluate("(()=>{const e=document.getElementById('talkPortrait');if(!e)return {vis:false,char:''};const cs=getComputedStyle(e);return {vis:cs.display!=='none'&&!e.hidden,char:e.dataset.char||''}})()")
    txt = lambda: pg.evaluate("document.querySelector('#msg').textContent||''")
    pg.add_init_script(INIT); pg.goto('http://localhost:8765/index.html'); pg.wait_for_timeout(2500)
    check(not pg.evaluate('window.__openingSeen'), 'A setup: the delayed opening has not arrived yet')
    pg.evaluate('closeDialogue()'); pg.evaluate("FieldTalk.loadTable(%s)" % __import__('json').dumps(TABLE)); pg.evaluate("FieldTalk.talk('t_race')"); pg.wait_for_timeout(500)
    s = st(); check(s['vis'] and s['char'] == 'fiona' and 'こんにちは' in txt(), 'A: Fiona conversation + portrait are up before the opening arrives: %s' % s)
    pg.wait_for_function('window.__openingSeen===true', timeout=20000); pg.wait_for_timeout(400)
    s = st(); check('朝の風' in txt() and not s['vis'], 'A: late opening replaces the line and the Fiona portrait is revoked (no stale portrait): %s' % s)
    check(not pg.evaluate("(()=>{const e=document.getElementById('talkPortrait');return !!e&&!!e.querySelector('img')&&getComputedStyle(e).display!=='none'})()"), 'A: no portrait image left visible')
    # B: gated start
    pg.reload(); pg.wait_for_function('window.__openingSeen===true', timeout=30000); pg.wait_for_timeout(150)
    pg.evaluate('closeDialogue()'); pg.evaluate("FieldTalk.loadTable(%s)" % __import__('json').dumps(TABLE)); pg.evaluate("FieldTalk.talk('t_race')"); pg.wait_for_timeout(2500)
    s = st(); check(s['vis'] and s['char'] == 'fiona' and 'こんにちは' in txt(), 'B: after the opening was shown the conversation + portrait stay stable for 2.5 s: %s' % s)
    check(not [e for e in errs if 'PAGEERR' in e], 'no page errors %s' % errs[:2])
    b.close()
print('FAILS', len(fails)); import sys; sys.exit(1 if fails else 0)

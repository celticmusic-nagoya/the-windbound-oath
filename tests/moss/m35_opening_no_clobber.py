# STARTUP-RACE (#20): the delayed startup opening line must not replace a conversation that is already running. needs http.server 8765.
# A: opening delayed +4.5 s (simulated slow machine); a conversation started before it arrives keeps its text until the player advances it.
# B: with no conversation running the opening line is still spoken (behaviour unchanged).
import json, sys
from playwright.sync_api import sync_playwright
fails = []
def check(c, m):
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c: fails.append(m)
TABLE = {"npc": "t_nc", "entries": [{"id": "t_n1", "priority": 10, "when": {}, "mode": "cycle", "lines": [{"pages": ["テスト「ひとつめ。」", "テスト「ふたつめ。」"]}]}]}
INIT = """(()=>{const st=window.setTimeout;window.setTimeout=function(f,d,...a){if(d===350&&typeof f==='function'&&String(f).includes('\\u671d\\u306e\\u98a8'))d=350+4500;return st.call(window,f,d,...a)}})();"""
def boot(b, late):
    pg = b.new_page(viewport={'width': 1280, 'height': 720}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    if late: pg.add_init_script(INIT)
    pg.goto('http://localhost:8765/index.html'); return pg, errs
with sync_playwright() as p:
    b = p.chromium.launch()
    pg, errs = boot(b, True); pg.wait_for_function("MossForest.mapId==='rilde_in_aidan'&&MossForest.busy===false", timeout=30000)
    txt = lambda: pg.evaluate("document.querySelector('#msg').textContent||''")
    pg.evaluate("FieldTalk.loadTable(%s)" % json.dumps(TABLE)); pg.evaluate("FieldTalk.talk('t_nc')"); pg.wait_for_timeout(400)
    check('ひとつめ' in txt() and pg.evaluate('FieldTalk.active'), 'A: test conversation is running before the delayed opening fires')
    pg.wait_for_timeout(6000)
    check('ひとつめ' in txt() and '朝の風' not in txt() and pg.evaluate('FieldTalk.active'), 'A: the late opening did not replace the running conversation: %s' % txt()[:20])
    pg.click('#msg'); pg.wait_for_timeout(300)
    check('ふたつめ' in txt(), 'A: the conversation still advances normally')
    check(not errs, 'A: no page errors %s' % errs[:2]); pg.close()
    pg, errs = boot(b, False); pg.wait_for_function("document.querySelector('#msg').textContent.includes('朝の風')", timeout=30000)
    check('朝の風' in txt() if False else pg.evaluate("document.querySelector('#msg').textContent").find('朝の風') >= 0, 'B: with no conversation the opening line is spoken as before')
    check(not errs, 'B: no page errors %s' % errs[:2]); b.close()
print('FAILS', len(fails)); sys.exit(1 if fails else 0)

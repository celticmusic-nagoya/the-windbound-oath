"""T16: Lou-only faint badge / motion / recovery display at PC, portrait and landscape (no overlap, inside the viewport, KO frames then hold, resting pose restored).
Screenshots -> docs/battle/qa/lou-faint-20261019/. DEV setScript drives the draws; no game number is changed."""
import os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
OUT = ROOT / 'docs/battle/qa/lou-faint-20261019'; OUT.mkdir(parents=True, exist_ok=True)
fails = []
def check(ok, name, d=''):
    print(('ok   ' if ok else 'FAIL ') + name, d, flush=True)
    if not ok: fails.append(name)
IDLE = "!document.body.classList.contains('battlePresentationBusy')&&!document.body.classList.contains('dialogueOpen')&&!document.body.classList.contains('actionCinematic')"
def settle(pg, n=60):
    for _ in range(n):
        if pg.evaluate("document.body.classList.contains('dialogueOpen')"): pg.evaluate("closeDialogue()")
        if pg.evaluate(IDLE): return
        pg.wait_for_timeout(400)
def rnd(pg, queued):
    pg.evaluate("q=>{rbHP=120;rbFHP=105;rbQueued=q;rbRound=1;window.__done=false;rbEnemyParty().then(()=>window.__done=true)}", queued)
    for _ in range(80):
        if pg.evaluate("document.body.classList.contains('dialogueOpen')"): pg.evaluate("closeDialogue()")
        if pg.evaluate("window.__done"): break
        pg.wait_for_timeout(400)
    settle(pg)
RECT = """()=>{const r=e=>{const b=e.getBoundingClientRect();return {l:b.left,t:b.top,r:b.right,b:b.bottom,w:b.width,h:b.height}};
 const tag=document.querySelector('#rbLou .louFaintTag'),lou=document.querySelector('#rbLou');
 const ovl=[...document.querySelectorAll('#rbParty .partyCard,#rbEnemyHud,.rbNearHud')].filter(e=>e.offsetParent!==null).map(e=>[e.id||e.className,r(e)]);
 return {tag:r(tag),lou:r(lou),vw:innerWidth,vh:innerHeight,ovl,disp:getComputedStyle(tag).display,img:document.querySelector('#rbLou img').src.split('/').pop()}}"""
def stable(pg):
    # Lou's idle drift / KO frame settle: measure only once her rect stopped moving (pre-existing motion, not part of the faint feature)
    last = None
    for _ in range(40):
        r = pg.evaluate("()=>{const b=document.querySelector('#rbLou').getBoundingClientRect();return [Math.round(b.left),Math.round(b.top)].join()}")
        if r == last: return True
        last = r; pg.wait_for_timeout(250)
    return False
def inter(a, b): return max(0, min(a['r'], b['r']) - max(a['l'], b['l'])) * max(0, min(a['b'], b['b']) - max(a['t'], b['t']))
with server(8852) as base, sync_playwright() as p:
    b = p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or None))
    for vp, tag in [((1280, 720), 'pc'), ((390, 844), 'portrait'), ((844, 390), 'landscape')]:
        pg = b.new_page(viewport={'width': vp[0], 'height': vp[1]}); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(base + '/index.html?dev=1'); pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.PrologueCombat&&window.BattleLouFaint'); pg.wait_for_timeout(1000); pg.evaluate("closeDialogue()")
        pg.evaluate("PrologueProgress.seed(0);startRaiderBattle()"); pg.wait_for_timeout(300); settle(pg); pg.wait_for_timeout(300)
        pg.evaluate("BattleLouFaint.reset();BattleLouFaint.setScript([0.1,0.1])")
        check(pg.evaluate("getComputedStyle(document.querySelector('#rbLou .louFaintTag')).display") == 'none', '%s badge hidden before faint' % tag)
        pg.screenshot(path=str(OUT / ('%s_1_before.png' % tag)))
        rnd(pg, True); pg.wait_for_timeout(900); check(stable(pg), '%s Lou rect settled' % tag)
        r = pg.evaluate(RECT)
        t = r['tag']
        check(r['disp'] != 'none' and t['w'] > 0, '%s badge visible' % tag, r['disp'])
        check(t['l'] >= 0 and t['t'] >= 0 and t['r'] <= r['vw'] and t['b'] <= r['vh'], '%s badge inside viewport' % tag, t)
        hit = [(n, inter(t, o)) for n, o in r['ovl'] if inter(t, o) > 4]
        check(not hit, '%s badge does not overlap party cards / HUDs' % tag, hit)
        check(r['img'] == 'lou_ko_06.png', '%s Lou holds KO final frame (existing asset)' % tag, r['img'])
        pg.screenshot(path=str(OUT / ('%s_2_fainted.png' % tag)))
        # recover: R+1 then R+2 (script 0.1 < 0.5 -> wakes)
        rnd(pg, False); rnd(pg, False)
        pg.wait_for_timeout(900); r = pg.evaluate(RECT)
        check(r['disp'] == 'none' and not pg.evaluate("BattleLouFaint.fainted"), '%s badge hidden after recovery' % tag, r['disp'])
        check(r['img'].startswith('lou_') and 'ko' not in r['img'], '%s resting pose restored' % tag, r['img'])
        pg.screenshot(path=str(OUT / ('%s_3_recovered.png' % tag)))
        check(not errs, '%s no page errors' % tag, errs[:2]); pg.close()
    b.close()
print('FAILS', len(fails)); sys.exit(1 if fails else 0)

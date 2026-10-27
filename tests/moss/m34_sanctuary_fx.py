"""MOSS-02: Moss Forest map effects layer (js/field/forest-effects.js).
Seal fx follows the seal flag, the seal collision is unchanged, depth/culling/disable switch/reduced motion behave.
Screenshots go to QA_OUT when set (outside the checkout)."""
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; fails = []
OUT = Path(os.environ['QA_OUT']).resolve() if os.environ.get('QA_OUT') else None
if OUT: assert not OUT.is_relative_to(ROOT), 'QA_OUT must be outside the checkout'; OUT.mkdir(parents=True, exist_ok=True)
def check(ok, name, detail=''):
    print(('ok   ' if ok else 'FAIL ') + name, detail if not ok else '')
    if not ok: fails.append(name)
A3 = 'moss_forest_03_ancient_grove'
FX = "[...document.querySelectorAll('.forest-fx')].map(d=>({id:d.dataset.fx,hidden:d.hidden,z:+d.style.zIndex,imgs:d.querySelectorAll('img').length,anim:getComputedStyle(d.querySelector('img')||d).animationName}))"
def boot(pg, base, query=''):
    pg.goto(base + '/index.html?title=0' + query); pg.wait_for_function("LoadCoordinator.phase==='READY'"); pg.wait_for_timeout(900); pg.evaluate('closeDialogue()')
    pg.evaluate("PrologueProgress.seed(0);storyStage=10;forestActive=true;document.querySelector('#forestScene').style.display='block'")
def enter(pg, mp, x, y):
    if pg.evaluate('MossForest.mapId') != mp:
        pg.evaluate("m=>MossForest.enter({map:m,flags:MossForestStory.flagsNow()})", mp); pg.wait_for_function("MossForest.active&&!MossForest.busy", timeout=30000)
    pg.evaluate("([x,y])=>MossForest.teleportFeet(x,y)", [x, y]); pg.wait_for_timeout(700); pg.evaluate('closeDialogue()')
def fx(pg): return {f['id']: f for f in pg.evaluate(FX)}
with server(8818) as base, sync_playwright() as p:
    b = p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None))
    errors = []
    pg = b.new_page(viewport={'width': 1280, 'height': 720}); pg.on('pageerror', lambda e: errors.append(str(e)))
    boot(pg, base)
    m = json.loads((ROOT / 'data/maps' / (A3 + '.json')).read_text())
    seal_rect = next(b_ for b_ in m['collision']['blockers'] if b_['id'] == 'cb_a3_seal')['rects'][0]
    sx, sy = seal_rect[0] + seal_rect[2] / 2, seal_rect[1] + seal_rect[3] / 2
    # ---- closed seal: fx shown (corrupted tint), collision blocks, the player in front draws over the fx
    enter(pg, A3, 3910, 3420); f = fx(pg)
    check('fx_seal' in f and not f['fx_seal']['hidden'] and f['fx_seal']['imgs'] == 4 and f['fx_seal']['anim'] == 'forest-fx-frame', 'closed seal: fx_seal shown with the 4 delivered frames animating', f.get('fx_seal'))
    check(pg.evaluate("document.querySelector('#forestWorld').classList.contains('forest-seal-corrupted')"), 'closed seal while corrupted: fx carries the corrupted tint')
    check(pg.evaluate("([x,y])=>MossForest.blocked(x,y)", [sx, sy]) is True, 'closed seal: barrier still blocks (collision unchanged)')
    check(pg.evaluate("+document.querySelector('#forestPlayer').style.zIndex") > f['fx_seal']['z'], 'depth: Aidan south of the barrier draws in front of the seal fx', (pg.evaluate("+document.querySelector('#forestPlayer').style.zIndex"), f['fx_seal']['z']))
    check(pg.evaluate("[...document.querySelectorAll('.forest-fx')].every(d=>getComputedStyle(d).pointerEvents==='none')"), 'effects never take pointer input')
    if OUT: pg.screenshot(path=str(OUT / 'a3_seal_closed.png'))
    # ---- open: fx leaves with the existing 1s opening, collision opens, no fx left behind
    pg.evaluate("PrologueProgress.seed(3);MossForest.setFlag('moss_a3_seal_open',true);MossForest.syncSymbols()"); pg.wait_for_timeout(250)
    check(pg.evaluate("document.querySelector('[data-fx=fx_seal]').classList.contains('fx-ending')"), 'opening: seal fx fades out with the seal')
    pg.wait_for_timeout(1300); f = fx(pg)
    check(f['fx_seal']['hidden'] and not pg.evaluate("document.querySelector('#forestWorld').classList.contains('forest-seal-corrupted')"), 'open seal: fx hidden and tint cleared', f['fx_seal'])
    check(pg.evaluate("([x,y])=>MossForest.blocked(x,y)", [sx, sy]) is False, 'open seal: barrier passable (collision unchanged)')
    if OUT: pg.screenshot(path=str(OUT / 'a3_seal_open.png'))
    # ---- re-entering the map with the seal already open never recreates the seal fx
    enter(pg, 'moss_forest_02_mossy_ravine', 5000, 4000); enter(pg, A3, 3910, 3420); f = fx(pg)
    check('fx_seal' in f and f['fx_seal']['hidden'], 're-entry with the seal open: fx stays hidden', f.get('fx_seal'))
    # ---- sanctuary glows / light (data-driven), depth classes
    enter(pg, A3, 4600, 3100); f = fx(pg)
    check(all(k in f and not f[k]['hidden'] for k in ('fx_light_center', 'fx_spring_glow', 'fx_lou_glow')), 'sanctuary: light shaft, spring glow and Lou glow shown', list(f))
    check(f['fx_light_center']['z'] >= 100000 and f['fx_lou_glow']['z'] < 100000, 'depth: light above actors, standing glow sorted by y', f)
    if OUT: pg.screenshot(path=str(OUT / 'a3_sanctuary.png'))
    pg.evaluate("MossForest.setFlag('moss_a3_lou_rescued',true)"); pg.wait_for_timeout(1200)
    check(fx(pg)['fx_lou_glow']['hidden'], 'Lou glow follows its when-flag (moss_a3_lou_rescued)')
    pg.evaluate("MossForest.setFlag('moss_a3_lou_rescued',false)")
    enter(pg, A3, 3375, 6260); f = fx(pg)
    check(all(k in f and f[k]['z'] == 1 for k in ('fx_rune_glow_n', 'fx_rune_glow_s')), 'threshold rune glows on the ground layer', f)
    # ---- culling: far from the sanctuary there are no sanctuary fx nodes
    enter(pg, A3, 800, 6300); f = fx(pg)
    check(not any(k in f for k in ('fx_seal', 'fx_light_center', 'fx_spring_glow')), 'culling: off-screen effects have no DOM node', list(f))
    # ---- A2 effects without a renderer are skipped exactly as before
    enter(pg, 'moss_forest_02_mossy_ravine', 1150, 3700)
    check(not pg.evaluate("document.querySelector('[data-fx=fx_a2_fall],[data-fx=fx_a2_pool_mist],[data-fx=fx_a2_arch_shade]')"), 'unsupported A2 effects are not drawn')
    check(not errors, 'no page errors', errors[:3]); pg.close()
    # ---- ?forestFx=0 disables the layer; reduced motion keeps effects static
    pg = b.new_page(viewport={'width': 1280, 'height': 720}); boot(pg, base, '&forestFx=0'); enter(pg, A3, 3910, 3420)
    check(pg.evaluate("document.querySelectorAll('.forest-fx').length") == 0 and pg.evaluate("([x,y])=>MossForest.blocked(x,y)", [sx, sy]) is True, '?forestFx=0: no effect nodes, seal still blocks'); pg.close()
    c = b.new_context(viewport={'width': 1280, 'height': 720}, reduced_motion='reduce'); pg = c.new_page(); boot(pg, base); enter(pg, A3, 3910, 3420)
    check(pg.evaluate("getComputedStyle(document.querySelector('[data-fx=fx_seal] img')).animationName") == 'none', 'prefers-reduced-motion: seal frames do not animate'); c.close()
    b.close()
print('FAILS', len(fails)); sys.exit(1 if fails else 0)

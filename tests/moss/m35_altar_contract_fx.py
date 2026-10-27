"""Issue #70: official altar v1 + contract FX in #altarScene.
- the CSS placeholder altar is replaced by the two official PNGs (unmodified, same box = same size and coordinates)
- the FX is hidden until Aidan grips the hilt, then fades in, holds and fades out; it is reset when the scene ends
- the scenario lines, the contract result (oathBound / oath sword) and the raider hand-off are unchanged
- the whole altar box (incl. the light beam) stays inside the screen in portrait and landscape
- the FX changes no screen pixel outside its own non-transparent footprint (no haze / rectangle on the real scene)
Runs with ?eventCg=0 so the pixel check isolates the FX (event CGs, incl. CG4 after the FX, are covered by m36_event_cg.py).
Screenshots and timing go to QA_OUT when set (outside the checkout)."""
import hashlib, json, os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
import numpy as np
from PIL import Image
import io
from scipy import ndimage as ndi
ROOT = Path(__file__).resolve().parents[2]; fails = []
OUT = Path(os.environ['QA_OUT']).resolve() if os.environ.get('QA_OUT') else None
if OUT: assert not OUT.is_relative_to(ROOT), 'QA_OUT must be outside the checkout'; OUT.mkdir(parents=True, exist_ok=True)
def check(ok, name, detail=''):
    print(('ok   ' if ok else 'FAIL ') + name, detail if not ok else '')
    if not ok: fails.append(name)
ALTAR = 'assets/images/environments/moss_ancient_altar_idle_v1.png'
FX = 'assets/images/effects/moss_ancient_altar_contract_fx_v1.png'
SHA = {ALTAR: '86334929fa35673aec62a29818d7850e4694106893c12f6b6fa37b97028d1855',
       FX: '8424bbd7933d956924f3b3f96a7daf81563e2279699857e0cc6d1fb248b23df0'}
for p, h in SHA.items():
    check(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h, 'official image unmodified: ' + p)
VIEWS = {'portrait_360x800': (360, 800), 'portrait_390x844': (390, 844), 'portrait_412x915': (412, 915), 'portrait_320x568': (320, 568),
         'tablet_768x1024': (768, 1024), 'landscape_844x390': (844, 390), 'landscape_915x412': (915, 412),
         'landscape_1280x720': (1280, 720), 'landscape_1920x1080': (1920, 1080)}
RECTS = """(()=>{const r=e=>{const b=document.querySelector(e).getBoundingClientRect();return [b.left,b.top,b.right,b.bottom]};
 return {box:r('#altarArt'),base:r('#altarArtBase'),fx:r('#altarContractFx'),text:r('#altarText'),vw:innerWidth,vh:innerHeight}})()"""
FXOP = "+getComputedStyle(document.querySelector('#altarContractFx')).opacity"
fx_alpha = np.array(Image.open(ROOT / FX))[..., 3]
timing = {}
with server(8819) as base, sync_playwright() as p:
    b = p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None))
    for view, (w, h) in VIEWS.items():
        errors = []
        ctx = b.new_context(viewport={'width': w, 'height': h}, is_mobile=w < h or h < 500, has_touch=True)
        pg = ctx.new_page(); pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.goto(base + '/index.html?title=0&eventCg=0'); pg.wait_for_function("LoadCoordinator.phase==='READY'"); pg.wait_for_timeout(600); pg.evaluate('closeDialogue()')
        check(pg.evaluate("!document.querySelector('#altarArtBase').getAttribute('src')"), f'[{view}] altar art is not fetched before the scene')
        pg.evaluate("PrologueProgress.seed(3);giveStarterSword();devResetScreens();closeDialogue();startAltarScene()")
        pg.wait_for_function("document.querySelector('#altarArtBase').classList.contains('ready')&&document.querySelector('#altarContractFx').classList.contains('ready')", timeout=15000)
        nat = pg.evaluate("[...document.querySelectorAll('#altarArt img')].map(i=>[i.getAttribute('src'),i.naturalWidth,i.naturalHeight])")
        check(nat == [[ALTAR, 1536, 1024], [FX, 1536, 1024]], f'[{view}] official altar + FX loaded at 1536x1024', nat)
        check(not pg.evaluate("document.querySelector('#altarRing')||document.querySelector('#altarStone')"), f'[{view}] CSS placeholder altar removed')
        R = pg.evaluate(RECTS)
        check(R['base'] == R['fx'] == R['box'], f'[{view}] altar and FX share the same box', R)
        bx = R['box']
        check(bx[0] >= 0 and bx[1] >= 0 and bx[2] <= R['vw'] + .5 and bx[3] <= R['vh'] + .5, f'[{view}] whole altar + beam inside the screen', R)
        check(abs((bx[2] - bx[0]) / (bx[3] - bx[1]) - 1.5) < .01, f'[{view}] 3:2 aspect kept')
        check(pg.evaluate(FXOP) == 0 and pg.evaluate("AltarArt.phase") == 'idle', f'[{view}] FX hidden at scene start')
        pg.wait_for_timeout(700)
        if OUT: pg.screenshot(path=str(OUT / f'{view}_01_scene_start.png'))
        lines = pg.evaluate("altarLines"); grip = next(i for i, l in enumerate(lines) if l.startswith('エイダンが柄を握る'))
        for i in range(1, grip):
            pg.evaluate("document.querySelector('#altarScene').click()")
            if pg.evaluate(FXOP) != 0: break
        check(pg.evaluate(FXOP) == 0 and pg.evaluate("altarIndex") == grip - 1, f'[{view}] FX never shown before the grip line')
        check(pg.evaluate("oathBound") is False, f'[{view}] not bound before the grip line')
        t0 = time.time(); pg.evaluate("document.querySelector('#altarScene').click()")
        check(pg.evaluate("document.querySelector('#altarText').textContent") == lines[grip], f'[{view}] grip line text unchanged')
        check(pg.evaluate("oathBound") is True and pg.evaluate("EquipmentManager.get('aidan').weapon") == 'oath_sword', f'[{view}] contract result unchanged (oathBound, oath sword)')
        samples = []; hold_png = None
        for _ in range(28):
            samples.append((round(time.time() - t0, 2), pg.evaluate("AltarArt.phase"), round(pg.evaluate(FXOP), 2)))
            if hold_png is None and samples[-1][1] == 'hold' and samples[-1][0] > 1.4:
                hold_png = pg.screenshot()
                if OUT: (OUT / f'{view}_02_contract_fx.png').write_bytes(hold_png)
            pg.wait_for_timeout(200)
        timing[view] = samples
        ph = [s[1] for s in samples]
        check(ph[0] == 'in' and 'hold' in ph and 'out' in ph and ph[-1] == 'idle', f'[{view}] FX fades in -> holds -> fades out -> idle', ph)
        check(max(s[2] for s in samples) >= .8 and samples[-1][2] == 0, f'[{view}] FX visible during the contract, gone afterwards', samples)
        check(any(s[1] == 'in' and .1 < s[2] < .9 for s in samples) and any(s[1] == 'out' and .1 < s[2] < .9 for s in samples), f'[{view}] FX fades (no hard cut) in and out', samples)
        # haze check on the real scene: hold vs. after (same line, same state) differ only inside the FX footprint
        after_png = pg.screenshot()
        if OUT: (OUT / f'{view}_03_after_fx.png').write_bytes(after_png)
        check(hold_png is not None, f'[{view}] hold frame captured')
        if hold_png is not None:
            after = np.array(Image.open(io.BytesIO(after_png)).convert('RGB')).astype(int)
            hold = np.array(Image.open(io.BytesIO(hold_png)).convert('RGB')).astype(int)
            diff = np.abs(after - hold).max(-1) > 3
            sx, sy = diff.shape[1] / R['vw'], diff.shape[0] / R['vh']
            l, t, r_, b_ = round(bx[0] * sx), round(bx[1] * sy), round(bx[2] * sx), round(bx[3] * sy)
            fp = np.array(Image.fromarray((fx_alpha > 0).astype(np.uint8) * 255).resize((r_ - l, b_ - t), Image.BILINEAR)) > 0
            foot = np.zeros(diff.shape, bool); foot[t:t + fp.shape[0], l:l + fp.shape[1]] = fp[:diff.shape[0] - t, :diff.shape[1] - l]
            foot = ndi.binary_dilation(foot, iterations=2)
            outside = int((diff & ~foot).sum())
            if outside and OUT:
                ys, xs = np.nonzero(diff & ~foot); (OUT / f'{view}_outside.json').write_text(json.dumps({'css_box': R['box'], 'dpr_scale': [sx, sy], 'px': list(zip(xs.tolist(), ys.tolist()))[:80], 'delta': [int(np.abs(after - hold)[y, x].max()) for y, x in zip(ys[:80], xs[:80])]}))
            out_max = int(np.abs(after - hold).max(-1)[~foot].max())
            # the original haze touched the whole canvas; allow only resampling noise at the footprint edge (<=0.01% of the screen, <=8/255)
            check(outside <= diff.size // 10000 and out_max <= 8 and diff.sum() > 500, f'[{view}] FX changes no pixel outside its footprint (no haze/rectangle)', {'changed': int(diff.sum()), 'outside': outside, 'outside_max_delta': out_max})
        # finish the scene: FX reset, raider battle starts as before
        while pg.evaluate("document.querySelector('#altarScene').style.display") == 'block':
            pg.evaluate("document.querySelector('#altarScene').click()")
        try: pg.wait_for_function("document.querySelector('#raiderBattle').style.display==='block'", timeout=20000)
        except Exception: pass
        endst = pg.evaluate("({phase:AltarArt.phase,raider:document.querySelector('#raiderBattle').style.display,altar:document.querySelector('#altarScene').style.display,body:document.body.className})")
        check(endst['phase'] == 'idle' and endst['raider'] == 'block', f'[{view}] scene end: FX reset, raider battle starts', endst)
        check(not errors, f'[{view}] no page errors', errors[:3]); ctx.close()
    # a quick replay never shows a stale FX
    ctx = b.new_context(viewport={'width': 1280, 'height': 720}); pg = ctx.new_page()
    pg.goto(base + '/index.html?title=0&eventCg=0'); pg.wait_for_function("LoadCoordinator.phase==='READY'"); pg.wait_for_timeout(500); pg.evaluate('closeDialogue()')
    pg.evaluate("PrologueProgress.seed(3);giveStarterSword();devResetScreens();closeDialogue();startAltarScene();AltarArt.contract()"); pg.wait_for_timeout(300)
    pg.evaluate("startAltarScene()"); pg.wait_for_timeout(1200)
    check(pg.evaluate("AltarArt.phase") == 'idle' and pg.evaluate(FXOP) == 0, 'restarting the scene clears a running FX')
    ctx.close()
    b.close()
if OUT: (OUT / 'fx_timing.json').write_text(json.dumps(timing, indent=1))
print('FAILS', len(fails)); sys.exit(1 if fails else 0)

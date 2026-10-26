"""Issue #51: real pointer/touch/keyboard on PC, portrait and landscape, both encounters.
Run with QA_OUT outside the checkout; requires Playwright + Chromium and loopback sockets.
"""
import os, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ['QA_OUT']).resolve()
assert not OUT.is_relative_to(ROOT), 'QA_OUT must be outside the checkout'
OUT.mkdir(parents=True, exist_ok=True)
rows, errors = [], []
def ck(name, ok):
    rows.append({'name': name, 'status': 'PASS' if ok else 'FAIL'})
    (OUT / 'results.json').write_text(json.dumps(rows, indent=2))
    assert ok, name
with server(8891) as base, sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH', '/usr/bin/chromium'))
    for label, width, height, touch in [('pc',1280,720,False),('portrait',390,844,True),('landscape',844,390,True)]:
        for mode in ['normal','raider']:
            context = b.new_context(viewport={'width':width,'height':height}, has_touch=touch, is_mobile=touch)
            p = context.new_page(); p.on('pageerror', lambda e: errors.append(str(e)))
            p.goto(base + '/index.html'); p.wait_for_function("LoadCoordinator.phase==='READY'")
            committed=p.evaluate("async mode=>{closeDialogue();if(mode==='normal'){storyStage=6;PrologueProgress.seed(0);return await startAttackBattle('attackGob2',100)}storyStage=12;return await startRaiderBattle()}",mode)
            ck(f'{label}/{mode}: entry committed',committed is True)
            p.wait_for_function('m=>!battleCommandLocked(m)',arg=mode);p.evaluate('closeDialogue()')
            toggle, panel, action = ('#normalCommandToggle','#normalBattleCmd','#nAtk') if mode=='normal' else ('#rbCommandToggle','#rbCmd','#rbAtk')
            setter = 'setNormalCommandDrawer' if mode=='normal' else 'setRaiderCommandDrawer'
            actor = 'normalActor' if mode=='normal' else 'rbActor'
            if label=='pc':
                # A programmatic close is deliberately reopened by InputManager's PC poll.
                p.evaluate(f'{setter}(false)');p.wait_for_function('(s)=>!document.querySelector(s).hidden',arg=panel)
                ck(f'{label}/{mode}: PC default auto-open observed',p.locator(panel).is_visible())
                # Use the actual close control to set the sticky manual-fold policy.
                p.locator('#normalCommandClose' if mode=='normal' else '#rbCommandClose').click()
                p.locator(toggle).wait_for(state='visible')
            for opened in [False, True]:
                # Same manual-fold contract as the Claude rescue patch, on every iteration.
                p.evaluate("c=>document.querySelector(c).click()", '#normalCommandClose' if mode=='normal' else '#rbCommandClose')
                rect = p.locator(toggle).bounding_box()
                assert rect, toggle
                # A bare assignment returns the hold Promise and evaluate() waits until it unlocks.
                p.evaluate(f'()=>{{{setter}({str(opened).lower()});window.__lock=BattlePresentation.hold(10000);}}')
                p.wait_for_function('(s)=>document.querySelector(s).disabled', arg=toggle)
                before = p.evaluate(actor)
                x, y = rect['x']+rect['width']/2, rect['y']+rect['height']/2
                p.touchscreen.tap(x,y) if touch else p.mouse.click(x,y)
                for key in ['ArrowDown','Enter','Space','Tab']:
                    p.keyboard.press(key)
                # Synthetic calls also must respect the same gate.
                p.evaluate(f"{setter}(true);document.querySelector('{action}').click()")
                state = p.evaluate("([panel,toggle])=>({hidden:getComputedStyle(document.querySelector(panel)).display==='none',inert:document.querySelector(panel).inert,disabled:document.querySelector(toggle).disabled})", [panel,toggle])
                ck(f'{label}/{mode}/{opened}: locked, no accepted action', all(state.values()) and p.evaluate(actor)==before and not p.evaluate('BattleTargetSelector.active'))
                # Observe release at the same microtask boundary and the next rendering callback.
                latency = p.evaluate("async(s)=>{BattlePresentation.cancel();await Promise.resolve();return new Promise(resolve=>requestAnimationFrame(()=>resolve(!document.querySelector(s).disabled))) }", toggle)
                ck(f'{label}/{mode}/{opened}: enabled by first frame', latency)
                p.evaluate(f'{setter}(true)')
                ck(f'{label}/{mode}/{opened}: usable drawer', p.locator(panel).is_visible() and not p.evaluate('(s)=>document.querySelector(s).inert', panel))
            p.screenshot(path=str(OUT/f'{label}-{mode}.png'))
            # A guard is accepted normally after release (no damage/balance assumptions).
            p.evaluate("chooseNormalAct('guard')" if mode=='normal' else "choosePartyAct('guard')")
            ck(f'{label}/{mode}: action after unlock', p.evaluate(actor)=='fiona')
            context.close()
    ck('no page errors', not errors)
    b.close()

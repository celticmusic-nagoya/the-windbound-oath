"""DIRECTIVE-18B: production bench interaction -> sunset dialogue, no injected talk table.
The existing cliff regression covers the full sunset/night/fire progression.
"""
import os, json, hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ['QA_OUT']) if os.environ.get('QA_OUT') else None
if OUT: OUT.mkdir(parents=True, exist_ok=True)
fails = []
def check(ok, label, detail=None):
    print(('ok   ' if ok else 'FAIL ') + label, '' if ok else detail, flush=True)
    if not ok: fails.append(label)

asset_root = ROOT / 'assets/images/characters/portraits/aidan'
ledger = (asset_root / 'SHA256SUMS').read_text().splitlines()
pngs = [line.split(maxsplit=1) for line in ledger if line.strip()]
check(len(pngs) == 54 and all(hashlib.sha256((asset_root / f.lstrip('*')).read_bytes()).hexdigest() == digest for digest, f in pngs), '54 adopted PNG hashes unchanged')

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width':390,'height':844}, has_touch=True)
    pg = ctx.new_page(); errors = []
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.goto('http://localhost:%s/index.html?title=0' % os.environ.get('PORT','8765'))
    pg.wait_for_function("LoadCoordinator.phase==='READY'")
    # Training is already complete; enter the ordinary cliff route, then click its real bench.
    pg.evaluate("closeDialogue();storyStage=3;document.querySelector('#hillExit').click()")
    pg.wait_for_function("MossForest.mapId==='cliff_moher_01_spiral_ascent'&&MossForest.active&&!MossForest.busy&&!LoadingInput.busy", timeout=30000)
    check(pg.evaluate('MossForest.goFeet(2400,1500)'), 'normal cliff entrance has a walkable route to the summit')
    pg.evaluate('MossForest.teleportFeet(2400,1040)');pg.wait_for_timeout(1500)
    point = pg.evaluate("()=>{const r=document.querySelector('#forestWorld').getBoundingClientRect(),s=FieldCamera.scale;return [r.left+2400*s,r.top+960*s]}")
    pg.touchscreen.tap(*point)
    pg.wait_for_function('FieldTalk.active')
    for _ in range(2): pg.locator('#msg').tap()
    pg.locator('.talkChoices button').first.tap()
    pg.wait_for_function("FieldScene.running==='cliff_sunset_to_fire'&&!!document.querySelector('#msg .talkText')&&document.querySelector('#msg .talkText').textContent.includes('間に合ったね')")
    check(pg.evaluate("FieldTalk.flag('cliff_bench_sat')&&storyStage===3"), 'real bench choice starts existing story scene without early stage advance')
    for _ in range(2): pg.locator('#msg').tap()
    pg.wait_for_function("TalkPortrait.status.visible&&TalkPortrait.status.face==='smile'&&TalkPortrait.status.blinkReady")
    check(pg.locator('#msg .talkName').inner_text() == 'エイダン' and '訓練のあとに' in pg.locator('#msg .talkText').inner_text(), 'Aidan appears on his original first sunset line')
    s = pg.evaluate('TalkPortrait.status')
    check(s['char']=='aidan' and s['side']=='left' and s['blink']['timers']==1 and 2900 <= s['blink']['nextAt']-pg.evaluate('Date.now()') <= 6000, 'adopted smile with one natural 3–6 second blink timer', s)
    pg.evaluate("window.eyes=[];new MutationObserver(()=>{const e=document.querySelector('#talkPortrait');window.eyes.push([performance.now(),+e.dataset.eye])}).observe(document.querySelector('#talkPortrait'),{attributes:true,attributeFilter:['data-eye']})")
    pg.wait_for_function("window.eyes.some(x=>x[1]===4)", timeout=7000)
    if OUT: pg.screenshot(path=str(OUT/'story_natural_blink.png'))
    pg.wait_for_function("window.eyes.length>=8&&TalkPortrait.status.eye===0")
    trace = pg.evaluate('window.eyes')
    check([x[1] for x in trace[:8]]==[1,2,3,4,3,2,1,0] and 230 <= trace[7][0]-trace[0][0] <= 400, 'real story natural blink completes its ~260ms sequence', trace)
    for w,h in [(390,844),(360,800),(412,915),(844,390),(915,412),(1920,1080)]:
        pg.set_viewport_size({'width':w,'height':h});pg.wait_for_timeout(250)
        g=pg.evaluate("""()=>{const e=document.querySelector('#talkPortrait'),r=e.getBoundingClientRect(),m=document.querySelector('#msg'),t=m.getBoundingClientRect();return {visible:TalkPortrait.status.visible,left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height,textTop:t.top,pointer:getComputedStyle(e).pointerEvents,textFits:m.scrollHeight<=t.height+1,crop:[e.querySelector('canvas').width,e.querySelector('canvas').height]}}""")
        check(g['visible'] and g['left']>=-1 and g['top']>=-1 and g['right']<=w+1 and g['bottom']<=g['textTop'] and g['height']>80 and g['pointer']=='none' and g['textFits'] and g['crop']==[800,760], f'{w}x{h}: portrait above dialogue, inside viewport, original crop, input unobstructed',g)
        check(pg.evaluate("document.querySelectorAll('.event-cg-item.on').length===0"), f'{w}x{h}: no event CG overlap')
        if OUT: pg.screenshot(path=str(OUT/f'story_smile_{w}x{h}.png'))
    pg.locator('#msg').tap();pg.wait_for_timeout(100)
    check(not pg.evaluate('TalkPortrait.status.visible') and pg.evaluate('TalkPortrait.status.blink') is None, 'Fiona page hides Aidan and stops timer')
    pg.locator('#msg').tap();pg.locator('#msg').tap()
    pg.wait_for_function("TalkPortrait.status.visible&&TalkPortrait.status.face==='normal'&&TalkPortrait.status.blinkReady")
    check('守れるくらいには強くなりたい' in pg.locator('#msg .talkText').inner_text(), 'second original Aidan line uses normal expression')
    if OUT: pg.screenshot(path=str(OUT/'story_normal.png'))
    pg.locator('#msg').tap();pg.locator('#msg').tap();pg.locator('#msg').tap()
    pg.wait_for_timeout(300)
    check(not pg.evaluate('TalkPortrait.status.visible') and pg.evaluate('TalkPortrait.status.blink') is None, 'sunset conversation ends with no portrait or timer')
    check(not errors, 'no page errors', errors)
    ctx.close();b.close()
print('FAILS',len(fails))
raise SystemExit(1 if fails else 0)

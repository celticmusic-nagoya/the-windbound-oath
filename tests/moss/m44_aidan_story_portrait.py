"""DIRECTIVE-18B: production bench interaction -> sunset dialogue, no injected talk table.
The existing cliff regression covers the full sunset/night/fire progression.
"""
import os, json, hashlib, base64, io
from PIL import Image, ImageChops
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

def natural_pixels(pg, face):
    pg.evaluate("""()=>{const e=document.querySelector('#talkPortrait'),c=e.querySelector('canvas');window.eyeFrames=[{state:0,png:c.toDataURL()}];window.eyeObserver=new MutationObserver(()=>eyeFrames.push({state:+e.dataset.eye,png:c.toDataURL()}));eyeObserver.observe(e,{attributes:true,attributeFilter:['data-eye']})}""")
    pg.wait_for_function("eyeFrames.filter(x=>x.state===0).length>=4", timeout=24000)
    frames=pg.evaluate('eyeFrames');pg.evaluate('eyeObserver.disconnect()')
    source=Image.open(asset_root/f'aidan_{face}.png').convert('RGBA')
    correct=True; changed=True
    for item in frames:
        actual=Image.open(io.BytesIO(base64.b64decode(item['png'].split(',')[1]))).convert('RGB')
        expected=source.copy()
        if item['state']:
            for eye,xy in [('L',(570,268)),('R',(672,314))]:
                expected.alpha_composite(Image.open(asset_root/'blink'/f"{face}_{eye}_s{item['state']}.png").convert('RGBA'),xy)
        expected=expected.crop((190,0,990,760)).convert('RGB')
        for box in [(380,268,464,320),(482,314,526,350)]:
            correct &= ImageChops.difference(actual.crop(box),expected.crop(box)).getbbox() is None
            original=source.crop((box[0]+190,box[1],box[2]+190,box[3])).convert('RGB')
            changed &= (ImageChops.difference(actual.crop(box),original).getbbox() is not None)==bool(item['state'])
        if OUT and item['state'] in (0,2,4):actual.save(OUT/f'story_{face}_actual_eye{item["state"]}.png')
    check(correct and changed and [f['state'] for f in frames[1:25]]==[1,2,3,4,3,2,1,0]*3, face+': three natural blinks, BOTH eye pixels match adopted open/half/closed frames')

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
    natural_pixels(pg, 'smile')
    for w,h in [(390,844),(360,800),(412,915),(844,390),(915,412),(1920,1080)]:
        pg.set_viewport_size({'width':w,'height':h});pg.wait_for_timeout(250)
        g=pg.evaluate("""()=>{const e=document.querySelector('#talkPortrait'),r=e.getBoundingClientRect(),m=document.querySelector('#msg'),t=m.getBoundingClientRect();return {visible:TalkPortrait.status.visible,left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height,textTop:t.top,pointer:getComputedStyle(e).pointerEvents,textFits:m.scrollHeight<=t.height+1,crop:[e.querySelector('canvas').width,e.querySelector('canvas').height]}}""")
        check(g['visible'] and g['left']>=-1 and g['top']>=-1 and g['right']<=w+1 and g['bottom']<=g['textTop'] and g['height']>80 and g['pointer']=='none' and g['textFits'] and g['crop']==[800,760], f'{w}x{h}: portrait above dialogue, inside viewport, original crop, input unobstructed',g)
        check(pg.evaluate("document.querySelectorAll('.event-cg-item.on').length===0"), f'{w}x{h}: no event CG overlap')
        if OUT: pg.screenshot(path=str(OUT/f'story_smile_{w}x{h}.png'))
    pg.locator('#msg').tap();pg.wait_for_timeout(100)
    check(pg.evaluate("TalkPortrait.status.visible&&TalkPortrait.status.char==='fiona'&&TalkPortrait.status.face==='smile'&&TalkPortrait.status.blink===null&&!TalkPortrait.status.blinkReady"), 'Fiona warmth page replaces Aidan with adopted static smile (24A)')
    pg.locator('#msg').tap();pg.locator('#msg').tap()
    pg.wait_for_function("TalkPortrait.status.visible&&TalkPortrait.status.face==='normal'&&TalkPortrait.status.blinkReady")
    check('守れるくらいには強くなりたい' in pg.locator('#msg .talkText').inner_text(), 'second original Aidan line uses normal expression')
    natural_pixels(pg, 'normal')
    if OUT: pg.screenshot(path=str(OUT/'story_normal.png'))
    pg.locator('#msg').tap();pg.locator('#msg').tap();pg.locator('#msg').tap()
    pg.wait_for_timeout(300)
    check(not pg.evaluate('TalkPortrait.status.visible') and pg.evaluate('TalkPortrait.status.blink') is None, 'sunset conversation ends with no portrait or timer')
    check(not errors, 'no page errors', errors)
    ctx.close();b.close()
print('FAILS',len(fails))
raise SystemExit(1 if fails else 0)

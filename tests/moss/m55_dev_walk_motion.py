"""DEV walk inspector: real UI, image pixels, shared policy and lifecycle."""
import json
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/qa'))
from browser_support import server
OUT = Path(os.getenv('QA_OUT', '/tmp/dev-walk-qa')); OUT.mkdir(parents=True, exist_ok=True)
rows = []; errors = []
def ck(name, ok):
    rows.append({'name': name, 'pass': bool(ok)})
    (OUT / 'walk-results.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    print(('PASS ' if ok else 'FAIL ') + name, flush=True)
    assert ok, name
SNAP = 'DevWalkTest.snapshot()'
SAVE = "JSON.stringify({stage:storyStage,flags:PrologueProgress.eventSnapshot(),talk:FieldTalk.serialize(),inventory:Inventory.serialize(),party:PartyManager.members,stock:battleItems,gold,storage:{...localStorage},feet:MossForest.feet,map:MossForest.mapId})"
PIXELS = """async()=>{const e=document.querySelector('#walkMotionTest img'),c=document.createElement('canvas');c.width=c.height=96;c.getContext('2d').drawImage(e,0,0,96,96);const a=c.getContext('2d').getImageData(0,0,96,96).data;let min=255,max=0;for(let i=3;i<a.length;i+=4){min=Math.min(min,a[i]);max=Math.max(max,a[i])}const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',a))].map(x=>x.toString(16).padStart(2,'0')).join('');return {hash,min,max};}"""
with server(8801) as base, sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE') or '/usr/bin/chromium')
    for label, width, height in [('pc',1920,1080),('portrait',390,844),('landscape',844,390)]:
        ctx = browser.new_context(viewport={'width':width,'height':height}, has_touch=True)
        p = ctx.new_page(); p.on('pageerror',lambda e:errors.append(str(e)))
        p.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
        p.on('response',lambda r: errors.append(f'HTTP {r.status} {r.url}') if r.status>=400 else None)
        p.on('requestfailed',lambda r:errors.append(f'REQUEST {r.url}: {r.failure}'))
        p.goto(base+'/index.html?title=1')
        p.get_by_role('button',name='NEW GAME',exact=True).click()
        p.wait_for_function("LoadCoordinator.phase==='READY'&&MossForest.active&&document.body.classList.contains('dialogueOpen')")
        for _ in range(40):
            if p.evaluate("InputManager.state()!=='DIALOGUE'"): break
            p.keyboard.press('Enter'); p.wait_for_timeout(80)
        p.wait_for_function("!MossForest.busy&&!LoadingInput.busy&&!document.body.classList.contains('dialogueOpen')")
        before = p.evaluate(SAVE)
        p.locator('#devBtn').click(); p.locator('#devWalkMotionTest').tap()
        p.wait_for_function('DevWalkTest.active&&DevWalkTest.snapshot().ready')
        ck(label+' actual DEV entry opens',p.locator('#walkMotionTest').is_visible())
        q = lambda s:p.locator('#walkMotionTest '+s)
        def ready(group=None, actor=None, direction=None):
            p.wait_for_function("a=>{const s=DevWalkTest.snapshot();return s.loaded&&(!a[0]||s.group===a[0])&&(!a[1]||s.actor===a[1])&&(!a[2]||s.direction===a[2])}",arg=[group,actor,direction])
        total = 0
        for group in ['ally','enemy','npc']:
            q('[data-walk=group]').select_option(group); ready(group=group)
            actors = p.evaluate("g=>FieldWalkMotion.catalog(g).map(a=>a.id)",group)
            ck(label+' '+group+' selector matches game catalog',q('[data-walk=actor] option').count()==len(actors))
            for actor in actors:
                q('[data-walk=actor]').select_option(actor); ready(group,actor)
                for direction in ['idle','down','up','left','right']:
                    q('[data-walk=idle]' if direction=='idle' else '[data-direction='+direction+']').tap(); ready(group,actor,None if direction=='idle' else direction)
                    frames = p.evaluate("a=>FieldWalkMotion.resolve(...a)?.frames.map(f=>({url:f.url,width:f.width,height:f.height,native:f.native}))??null",[group,actor,'down' if direction=='idle' else direction,'idle' if direction=='idle' else 'walk'])
                    if frames is None:
                        ck(f'{label}/{actor}/{direction} missing without substitute',q('[data-walk=error]').inner_text().startswith('未実装') and q('[data-walk=count]').inner_text()=='0 / 0' and q('img').is_hidden() and q('img').get_attribute('src') is None and q('[data-walk=play]').is_disabled() and not p.evaluate(SNAP)['timer'])
                        continue
                    seen = set()
                    for index, frame in enumerate(frames):
                        p.wait_for_function("f=>{const e=document.querySelector('#walkMotionTest img');return e.complete&&(f.native===false?e.naturalWidth>0:e.naturalWidth===f.width)&&e.currentSrc===new URL(f.url,location.href).href}",arg=frame)
                        s = p.evaluate(SNAP); ck(f'{label}/{actor}/{direction}/{index+1} source/count',s['index']==index and s['total']==len(frames) and q('[data-walk=count]').inner_text()==f'{index+1} / {len(frames)}')
                        px = p.evaluate(PIXELS); seen.add(px['hash']); ck(f'{label}/{actor}/{direction}/{index+1} actual alpha',px['min']==0 and px['max']>0)
                        inside = p.evaluate("()=>{const r=document.querySelector('#walkMotionTest img').getBoundingClientRect(),a=document.querySelector('#walkMotionTest .walkStage').getBoundingClientRect();return r.left>=a.left-1&&r.top>=a.top-1&&r.right<=a.right+1&&r.bottom<=a.bottom+1}")
                        ck(f'{label}/{actor}/{direction}/{index+1} image inside stage',inside)
                        q('[data-walk=next]').tap()
                    ck(f'{label}/{actor}/{direction} pixels change and loop wraps',(len(frames)==1 or len(seen)>1) and p.evaluate(SNAP)['index']==0)
                    q('[data-walk=prev]').tap(); ck(f'{label}/{actor}/{direction} backwards wrap',p.evaluate(SNAP)['index']==len(frames)-1)
                    total += len(frames)
        for bg in ['light','green','dark','checker']:
            q('[data-walk=background]').select_option(bg)
            ck(label+' background '+bg, q('[data-guide=checker]').is_checked()==(bg=='checker'))
        # Clock rate, actual loop, pause, optional guides and rotation.
        q('[data-walk=group]').select_option('ally'); ready(group='ally')
        q('[data-walk=actor]').select_option('aidan'); ready(actor='aidan')
        q('[data-direction=down]').tap(); ready(direction='down')
        for speed in [.5,1,2]:
            q('[data-walk=speed]').select_option(str(speed).rstrip('0').rstrip('.') if speed!=.5 else '0.5')
            q('[data-walk=play]').tap()
            start = p.evaluate('({s:DevWalkTest.snapshot(),now:performance.now()})'); p.wait_for_timeout(550)
            end = p.evaluate('({s:DevWalkTest.snapshot(),now:performance.now()})')
            rate = (end['s']['time']-start['s']['time'])*1000/(end['now']-start['now'])
            ck(f'{label} playback {speed}x',end['s']['playing'] and speed*.65<rate<speed*1.35)
            q('[data-walk=pause]').tap(); frozen = p.evaluate(SNAP); p.wait_for_timeout(150)
            ck(label+' pause cancels RAF and holds frame',not frozen['timer'] and p.evaluate(SNAP)['time']==frozen['time'])
        for guide, selector in [('checker','.walkStage'),('ground','.walkGround'),('center','.walkCenter')]:
            q('[data-guide='+guide+']').uncheck()
            ck(label+' '+guide+' off',not q(selector).is_visible() if guide!='checker' else 'checker' not in q(selector).get_attribute('class'))
            q('[data-guide='+guide+']').check()
        p.screenshot(path=str(OUT/f'walk-{label}.jpg'),type='jpeg',quality=85)
        q('[data-walk=fold]').tap(); ck(label+' controls collapse',not q('.walkPanel').is_visible()); q('[data-walk=fold]').tap()
        index = p.evaluate(SNAP)['index']; p.set_viewport_size({'width':height,'height':width}); p.wait_for_timeout(250)
        ck(label+' rotation keeps paused frame',p.evaluate(SNAP)['index']==index and not p.evaluate(SNAP)['timer'])
        p.emulate_media(reduced_motion='reduce')
        p.wait_for_function("document.querySelector('#walkMotionTest [data-walk=play]').disabled")
        ck(label+' reduced-motion blocks loop',q('[data-walk=play]').is_disabled() and not p.evaluate(SNAP)['timer'])
        q('[data-walk=next]').tap(); ck(label+' reduced-motion permits stepping',p.evaluate(SNAP)['index']==(index+1)%p.evaluate(SNAP)['total'])
        p.emulate_media(reduced_motion='no-preference')
        p.wait_for_function("!document.querySelector('#walkMotionTest [data-walk=play]').disabled")
        q('.walkStage').focus(); p.keyboard.down('w'); p.wait_for_timeout(100); p.keyboard.up('w')
        q('[data-walk=close]').tap()
        ck(label+' closing releases all DEV state',p.evaluate('!DevWalkTest.active&&!DevWalkTest.snapshot().timer&&!document.body.classList.contains("devWalkOpen")'))
        ck(label+' SAVE/party/flags/player unchanged',p.evaluate(SAVE)==before)
        # Existing invalidation boundary used by LOAD, and battle cleanup.
        p.evaluate('DevWalkTest.open()'); ready(); q('[data-walk=play]').tap(); p.evaluate('LoadCoordinator.supersede()')
        ck(label+' load invalidation cancels loop',p.evaluate('!DevWalkTest.active&&!DevWalkTest.snapshot().timer'))
        p.evaluate('DevWalkTest.open()'); ready(); q('[data-walk=play]').tap(); p.evaluate("document.body.classList.add('battleMode')")
        p.wait_for_function('!DevWalkTest.active'); ck(label+' battle invalidation cancels loop',not p.evaluate(SNAP)['timer']); p.evaluate("document.body.classList.remove('battleMode')")
        print('PASS ',label,'frames checked',total,flush=True)
        ctx.close()
    browser.close()
ck('no application errors',not errors)
print('FAILS 0')

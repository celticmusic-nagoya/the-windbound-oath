"""Actual 20-frame renderer/pixel/viewport checks in the existing DEV arena.

AI records are deterministic test fixtures; this is not route reachability QA.
SAVE/CONTINUE is covered separately by the unchanged lifecycle regression.
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/qa'))
from browser_support import server

OUT = Path(os.getenv('QA_OUT', '/tmp/goblin-field20-qa'))
OUT.mkdir(parents=True, exist_ok=True)
manifest = json.loads((ROOT / 'img/field/monsters/goblin/manifest.json').read_text())
expected = {}
for entry in manifest['frames']:
    data = Image.open(ROOT / entry['path']).convert('RGBA').tobytes()
    opaque = b''.join(data[i:i+4] for i in range(0, len(data), 4) if data[i+3] == 255)
    expected[Path(entry['path']).name] = hashlib.sha256(opaque).hexdigest()

READ = """async()=>{const m=FieldMonsters.list[0],e=m?.el;if(!e?.complete||!e.naturalWidth)return null;
const src=new URL(e.currentSrc||e.src).pathname.split('/').pop(),c=document.createElement('canvas');c.width=c.height=320;c.getContext('2d').drawImage(e,0,0);
const pixels=c.getContext('2d').getImageData(0,0,320,320).data,a=[];for(let i=0;i<pixels.length;i+=4)if(pixels[i+3]===255)a.push(...pixels.slice(i,i+4));
const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new Uint8Array(a)))].map(n=>n.toString(16).padStart(2,'0')).join('');
const r=e.getBoundingClientRect();return {src,hash,box:r.toJSON(),transform:e.style.transform,x:m.x,y:m.y,heading:m.facing};}"""
errors = []
results = []
with server(8799) as base, sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE') or '/usr/bin/chromium')
    for label, w, h in [('pc', 1920, 1080), ('portrait', 390, 844), ('landscape', 844, 390)]:
        context = browser.new_context(viewport={'width': w, 'height': h}, has_touch=True)
        page = context.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        page.on('response', lambda r: errors.append(f'HTTP {r.status} {r.url}') if r.status >= 400 else None)
        page.goto(base + '/index.html?title=0')
        page.wait_for_function('window.MossForest && !LoadingInput.busy')
        page.evaluate("devJump('forest')")
        page.wait_for_function('MossForest.active&&!MossForest.busy')
        page.wait_for_timeout(800)
        page.evaluate("closeDialogue();MossForest.enter({map:'dev_monster_arena'});")
        page.wait_for_function("MossForest.active&&!MossForest.busy&&MossForest.mapId==='dev_monster_arena'")
        page.wait_for_timeout(500)
        page.evaluate("closeDialogue();FieldMonsters.removeAll();const f=MossForest.feet;FieldMonsters.add({id:'qa20',type:'goblin',x:f.x,y:f.y-100,tune:{detect:0,touch:0}});FieldMonsters.list[0].wait=999")
        page.evaluate("Promise.all(FieldMonsters.list[0].frames.map(s=>{const e=new Image();e.src=s;return e.decode()}))")
        seen_all = set()
        for direction, dx, dy in [('idle', 0, 0), ('down', 0, 1), ('right', 1, 0), ('up', 0, -1), ('left', -1, 0)]:
            page.evaluate("a=>{const m=FieldMonsters.list[0],f=MossForest.feet;m.x=f.x;m.y=f.y-100;m.home=[m.x,m.y];m.state='wander';m.sub=a[0]==='idle'?'rest':'walk';m.wait=999;m.goal=[m.x+a[1]*120,m.y+a[2]*120];m.travel=0;m.animMoving=false;}", [direction, dx, dy])
            seen = set()
            deadline = time.monotonic() + 4
            while time.monotonic() < deadline and len(seen) < 4:
                r = page.evaluate(READ)
                if r:
                    token = 'idle_' if direction == 'idle' else f'walk_{direction}_'
                    if token in r['src']:
                        assert r['hash'] == expected[r['src']], (label, direction, 'actual image pixels differ', r)
                        assert 'scaleX' not in r['transform'], r
                        b = r['box']
                        assert b['x'] >= 0 and b['y'] >= 0 and b['right'] <= w and b['bottom'] <= h, (label, r)
                        seen.add(r['src'])
                page.wait_for_timeout(25)
            assert len(seen) == 4, (label, direction, seen)
            seen_all |= seen
            if direction in ['idle', 'right', 'left']:
                page.screenshot(path=str(OUT / f'goblin20-{label}-{direction}.jpg'), type='jpeg', quality=85)
        assert len(seen_all) == 20
        page.evaluate('FieldMonsters.setFrozen(true)')
        before = page.evaluate('FieldMonsters.list[0].animTime')
        page.wait_for_timeout(300)
        assert before == page.evaluate('FieldMonsters.list[0].animTime')
        page.evaluate("FieldMonsters.setFrozen(false);FieldMonsters.removeAll();const p=MossForest.feet;FieldMonsters.add({id:'qa-contact',type:'goblin',x:p.x+1,y:p.y+1})")
        page.wait_for_function("document.body.classList.contains('normalBattleMode')", timeout=10000)
        assert page.evaluate("FieldMonsters.list[0].type==='goblin'&&FieldMonsters.list[0].state==='engaged'")
        page.evaluate('FieldMonsters.clear()')
        assert page.evaluate('FieldMonsters.list.length') == 0
        results.append({'viewport': label, 'frames': sorted(seen_all), 'actual_opaque_pixel_hashes': 'PASS', 'freeze_clear': 'PASS', 'default_goblin_contact_battle': 'PASS'})
        print('ok  ', label, '20 actual frames/pixels, unclipped, freeze/clear, default contact battle')
        context.close()
    browser.close()
assert not errors, errors
(OUT / 'goblin20-results.json').write_text(json.dumps(results, indent=2))
print('FAILS 0')

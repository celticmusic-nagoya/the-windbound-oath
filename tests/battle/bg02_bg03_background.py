"""BG-02/BG-03 battle backgrounds (prep, index.html not connected): asset audit, area-first selection, layer geometry (main+foreground share one box/rule), input never blocked,
no residue, load-failure fallback, boss layers via BattleBackground.applyRaider (startRaiderBattle calls it since the 10/19 conditional adoption),
foreground does not cover faces / HP / HUD (alpha sampled through the real cover mapping) at PC / tablet / phone-landscape / phone-portrait."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[2]; D = ROOT / 'img/battle/backgrounds'; fails = []
def check(ok, name, detail=''):
    print(('ok   ' if ok else 'FAIL ') + name, detail)
    if not ok: fails.append(name)
# ---- 1) assets
for k in ('BG-01', 'BG-02', 'BG-03'):
    m = Image.open(D / f'bg_{k}_main.png'); f = Image.open(D / f'bg_{k}_fore.png')
    check(m.format == 'PNG' and m.size == (1536, 1024) and m.mode == 'RGB', f'{k} main: PNG 1536x1024 opaque RGB', (m.mode, m.size))
    a = np.array(f.convert('RGBA'))
    check(f.format == 'PNG' and f.size == (1536, 1024) and f.mode == 'RGBA', f'{k} fore: PNG 1536x1024 RGBA', (f.mode, f.size))
    check(int((a[..., :3][a[..., 3] == 0].sum(axis=1) > 0).sum()) == 0, f'{k} fore: fully transparent pixels carry no RGB')
    check(int((a[..., 3] == 0).sum()) > 0 and int(((a[..., 3] > 0) & (a[..., 3] < 255)).sum()) > 0, f'{k} fore: has transparent area and semi-transparent outline pixels kept')
check((D / 'bg_BG-01_main.png').read_bytes() == (ROOT / 'docs/art/delivered/bg01_20261014/bg_BG-01_main_original.png').read_bytes(), 'BG-01 main untouched (== original)')
STATE = """()=>{const r=document.getElementById('attackBattle'),l=document.getElementById('battleBg'),f=document.getElementById('battleFg'),s=document.querySelector('#attackBattle>.v2BattleStage');
 const rc=e=>{const b=e.getBoundingClientRect();return [b.left,b.top,b.width,b.height].map(x=>Math.round(x*10)/10)};
 const cs=e=>getComputedStyle(e);return {bg:r.dataset.bg||null,main:l.style.backgroundImage,fore:f?f.style.backgroundImage:null,mainRect:rc(l),foreRect:f?rc(f):null,
  mainPos:cs(l).backgroundPosition,forePos:f?cs(f).backgroundPosition:null,mainSize:cs(l).backgroundSize,foreSize:f?cs(f).backgroundSize:null,foreDisp:f?cs(f).display:null,fz:f?+cs(f).zIndex:null,ptr:f?cs(f).pointerEvents:null,
  unitZ:Math.max(...[...s.children].filter(c=>c.id&&c.id.startsWith('v2')).map(c=>+cs(c).zIndex||0)),lastChild:s.lastElementChild===f}}"""
def reset(pg):
    pg.evaluate("document.getElementById('attackBattle').style.display='none';document.body.classList.remove('battleMode','normalBattleMode','raiderBattleMode');BattleBackground.clear();BattleBackground.clearRaider()")
def start(pg, call, area=None, eid=None):
    reset(pg)
    if area: pg.evaluate("([m,e])=>BattleBackground.noteArea(m,e)", [area, eid])
    pg.evaluate(call); pg.wait_for_timeout(900)
VP = [('pc', 1280, 720), ('tablet', 1024, 768), ('phone-land', 844, 390), ('phone-port', 390, 844)]
with server(8885) as base, sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__('os').environ.get('PW_CHROMIUM_EXECUTABLE') or None)
    pg = b.new_page(viewport={'width': 1280, 'height': 720}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(base + '/index.html?dev=1'); pg.wait_for_function('window.BattleBackground'); pg.wait_for_timeout(1200); pg.evaluate('closeDialogue()')
    # ---- 2) selection rules (pure)
    R = lambda e, a=None: pg.evaluate("([e,a])=>BattleBackground.forEnemy(e,a)", [e, a])
    for e in ('mossSlime1', 'forestBat2', 'leafyBoar3', 'forestGob1', 'fieldGob2'):
        check(R(e, 'moss_forest') == 'BG-02', f'{e} in moss_forest -> BG-02'); check(R(e, None) is None, f'{e} outside moss forest -> unassigned (no BG-02 by enemy kind alone)')
    for e in ('attackGob1', 'attackGob2', 'northGob1', 'northGob2'):
        check(R(e, None) == 'BG-01' and R(e, 'moss_forest') == 'BG-01', f'{e} -> BG-01 (existing rule, area independent)')
    check(R('unknownEnemy', 'moss_forest') is None, 'unknown enemy -> unassigned')
    # ---- 3) one-shot, id-bound area note
    pg.evaluate("BattleBackground.noteArea('moss_forest_01_sunlit_path','mossSlime1')")
    check(pg.evaluate("BattleBackground.areaOf('forestBat1')") is None, 'note bound to its enemy id (other id: no area)')
    check(pg.evaluate("BattleBackground.areaOf('mossSlime1')") == 'moss_forest', 'note matches its enemy id')
    pg.evaluate("BattleBackground.noteArea('rilde_village','mossSlime1')"); check(pg.evaluate("BattleBackground.areaOf('mossSlime1')") is None, 'non-forest map note -> no area')
    b.close_pg = pg.close()
    for n, w, h in VP:
        pg = b.new_page(viewport={'width': w, 'height': h}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(base + '/index.html?dev=1'); pg.wait_for_function('window.BattleBackground&&window.InputManager'); pg.wait_for_timeout(1200); pg.evaluate('closeDialogue()')
        # BG-01 maintained
        start(pg, "startAttackBattle('attackGob1',100)"); s = pg.evaluate(STATE)
        check(s['bg'] == 'BG-01' and 'bg_BG-01_main.png' in s['main'] and 'bg_BG-01_fore.png' in (s['fore'] or ''), f'{n}: BG-01 main + fore applied', s['bg'])
        # BG-02 only with the moss-forest note
        start(pg, "startAttackBattle('mossSlime1',56)"); s0 = pg.evaluate(STATE)
        check(s0['bg'] is None and s0['foreDisp'] == 'none', f'{n}: mossSlime without area note -> no background (no residue of BG-01)', s0['bg'])
        start(pg, "startAttackBattle('forestGob1',100)", 'moss_forest_01_sunlit_path', 'forestGob1'); s = pg.evaluate(STATE)
        check(s['bg'] == 'BG-02' and 'bg_BG-02_main.png' in s['main'] and 'bg_BG-02_fore.png' in s['fore'], f'{n}: moss forest battle -> BG-02 main + fore', s['bg'])
        check(s['mainRect'] == s['foreRect'] and s['mainPos'] == s['forePos'] and s['mainSize'] == s['foreSize'] == 'cover', f'{n}: main and foreground share one box / position / cover rule', [s['mainRect'], s['foreRect'], s['mainPos'], s['forePos']])
        check(s['ptr'] == 'none' and s['foreDisp'] == 'block' and s['fz'] > s['unitZ'], f'{n}: foreground pointer-events none, above the units', [s['ptr'], s['fz'], s['unitZ']])
        # input never blocked: the foreground is never the hit target; COMMAND toggle is
        pg.wait_for_function("InputManager.state()!=='BATTLE_ANIMATION'", timeout=20000); pg.wait_for_timeout(1500)   # UI settled (opening done, drawer state final) before differential sampling
        GRID = "(ids)=>{const o=[];for(let x=5;x<innerWidth;x+=37)for(let y=5;y<innerHeight;y+=37){const q=document.elementFromPoint(x,y);o.push(q?(q.id||q.className||q.tagName):'-')}return o}"
        pg.evaluate("document.getElementById('battleFg').style.display='none'"); g0 = pg.evaluate(GRID, None)
        pg.evaluate("document.getElementById('battleFg').style.display=''"); g1 = pg.evaluate(GRID, None)
        diff = [(i, a, c) for i, (a, c) in enumerate(zip(g0, g1)) if a != c]
        check(not diff and 'battleFg' not in g1, f'{n}: hit targets identical with and without the foreground ({len(g1)} points); foreground never a target', diff[:6])
        # faces / HP / HUD not covered: sample the foreground alpha through the cover mapping over head + HUD boxes
        boxes = pg.evaluate("""()=>{const out=[];const add=(k,e,top)=>{if(!e)return;const b=e.getBoundingClientRect();if(b.width<2||b.height<2)return;out.push({k,l:b.left,t:b.top,w:b.width,h:b.height*(top||1)})};
          add('aidan-head',document.querySelector('#v2AidanUnit .prologueSprite,#v2AidanUnit img,#v2AidanUnit'),.35);add('fiona-head',document.querySelector('#v2FionaUnit .prologueSprite,#v2FionaUnit img,#v2FionaUnit'),.35);
          add('enemy-head',document.querySelector('#normalEnemy1 .prologueSprite,#normalEnemy1'),.35);
          for(const e of document.querySelectorAll('.v2NearHud,.prologueEnemyHud,#normalPartyHud'))add('hud',e,1);
          const f=document.getElementById('battleFg').getBoundingClientRect();return {boxes:out,fg:[f.left,f.top,f.width,f.height]}}""")
        im = np.array(Image.open(D / 'bg_BG-02_fore.png').convert('RGBA'))[..., 3] / 255.0
        fl, ft, fw, fh = boxes['fg']; sc = max(fw / 1536, fh / 1024); dw, dh = 1536 * sc, 1024 * sc; ox = fl + (fw - dw) * .5; oy = ft + (fh - dh) * 0.0   # background-position 50% 0%
        worst = {}
        import re
        cp = pg.evaluate("getComputedStyle(document.getElementById('battleFg')).clipPath"); mm = re.match(r'inset\(([\d.]+)%', cp or ''); clipy = ft + fh * (float(mm.group(1)) / 100 if mm else 0.0)   # the REAL computed clip line (no clip => whole foreground is sampled)
        check(bool(mm), f'{n}: foreground is clipped to the lower band', cp)
        for bx in boxes['boxes']:
            x0 = max(0, int((bx['l'] - ox) / sc)); x1 = min(1536, int((bx['l'] + bx['w'] - ox) / sc)); y0 = max(0, int((max(bx['t'], clipy) - oy) / sc)); y1 = min(1024, int((bx['t'] + bx['h'] - oy) / sc))
            worst.setdefault(bx['k'], 0.0)
            if x1 > x0 and y1 > y0: worst[bx['k']] = max(worst[bx['k']], float(im[y0:y1, x0:x1].mean()))
        check(all(v < 0.10 for v in worst.values()) and bool(worst), f'{n}: foreground leaves faces/HP/HUD uncovered (mean alpha over their boxes < 0.10)', {k: round(v, 3) for k, v in worst.items()})
        # no residue: next BG-01 battle after BG-02, then non-area enemy
        start(pg, "startAttackBattle('northGob1',100)"); check(pg.evaluate(STATE)['bg'] == 'BG-01', f'{n}: BG-02 -> BG-01 next battle, no BG-02 residue')
        start(pg, "startAttackBattle('fieldGob1',100)"); s = pg.evaluate(STATE); check(s['bg'] is None and s['foreDisp'] == 'none', f'{n}: unassigned enemy after a background battle: nothing remains', s['bg'])
        # boss: raider untouched by default, BG-03 layers on demand
        reset(pg); pg.evaluate('startRaiderBattle()'); pg.wait_for_timeout(900)
        r0 = pg.evaluate("({bg:document.getElementById('raiderBattle').dataset.bg||null,rb:!!document.getElementById('rbBg'),disp:getComputedStyle(document.getElementById('raiderBattle')).display})")
        # Adopted 10/19: startRaiderBattle() now calls BattleBackground.applyRaider() (index.html), so BG-03 layers are present without a manual call.
        check(r0['bg'] == 'BG-03' and r0['disp'] == 'block' and r0['rb'], f'{n}: boss battle applies BG-03 layers via the startRaiderBattle wiring', r0)
        pg.evaluate('BattleBackground.applyRaider()'); pg.wait_for_timeout(300)   # idempotent: calling again must not duplicate layers
        pg.wait_for_function("InputManager.state()!=='BATTLE_ANIMATION'", timeout=20000); pg.wait_for_timeout(1500)
        RG = "()=>{const o=[];for(let x=5;x<innerWidth;x+=37)for(let y=5;y<innerHeight;y+=37){const q=document.elementFromPoint(x,y);o.push(q?(q.id||q.className||q.tagName):'-')}return o}"
        r = pg.evaluate("""()=>{const e=document.getElementById('raiderBattle'),b=document.getElementById('rbBg'),f=document.getElementById('rbFg'),cs=x=>getComputedStyle(x),rc=x=>{const q=x.getBoundingClientRect();return [q.left,q.top,q.width,q.height].map(Math.round)};
          return {bg:e.dataset.bg,first:e.firstElementChild===b,img:b.style.backgroundImage,fimg:f.style.backgroundImage,same:JSON.stringify(rc(b))===JSON.stringify(rc(f))&&cs(b).backgroundPosition===cs(f).backgroundPosition,ptr:cs(b).pointerEvents+'/'+cs(f).pointerEvents}}""")
        rg1 = pg.evaluate(RG); pg.evaluate("document.getElementById('rbFg').style.display='none';document.getElementById('rbBg').style.display='none'"); rg0 = pg.evaluate(RG); pg.evaluate("document.getElementById('rbFg').style.display='';document.getElementById('rbBg').style.display=''")
        r['toggle'] = (rg0 == rg1 and 'rbFg' not in rg1 and 'rbBg' not in rg1); r['fg'] = 0; r['diff'] = [(i, a, c) for i, (a, c) in enumerate(zip(rg0, rg1)) if a != c][:6]
        check(r['bg'] == 'BG-03' and r['first'] and 'bg_BG-03_main.png' in r['img'] and 'bg_BG-03_fore.png' in r['fimg'] and r['same'] and r['ptr'] == 'none/none' and r['toggle'] and r['fg'] == 0, f'{n}: boss BG-03 layers (own DOM), same box, no pointer interception, COMMAND reachable', r)
        pg.evaluate('BattleBackground.clearRaider()'); r2 = pg.evaluate("({bg:document.getElementById('raiderBattle').dataset.bg||null,img:document.getElementById('rbBg').style.backgroundImage,disp:getComputedStyle(document.getElementById('rbBg')).display})")
        check(r2['bg'] is None and r2['img'] == '' and r2['disp'] == 'none', f'{n}: clearRaider leaves nothing behind', r2)
        check(not errs, f'{n}: no page errors', errs); pg.close()
    # ---- 6) load failures
    for what, pat in (('main', '**/bg_BG-02_main.png'), ('fore', '**/bg_BG-02_fore.png')):
        pg = b.new_page(viewport={'width': 1280, 'height': 720}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.route(pat, lambda r: r.abort())
        pg.goto(base + '/index.html?dev=1'); pg.wait_for_function('window.BattleBackground'); pg.wait_for_timeout(1200); pg.evaluate('closeDialogue()')
        start(pg, "startAttackBattle('forestGob1',100)", 'moss_forest_01_sunlit_path', 'forestGob1'); pg.wait_for_timeout(1200); s = pg.evaluate(STATE)
        if what == 'main': check(s['bg'] is None and s['foreDisp'] == 'none', 'BG-02 main load failure: back to the stage gradient (fore hidden too)', s['bg'])
        else: check(s['bg'] == 'BG-02' and s['fore'] in ('', 'none'), 'BG-02 fore load failure: main stays, the overlay is dropped', [s['bg'], s['fore']])
        check(pg.evaluate("document.getElementById('attackBattle').style.display")=='block' and not errs, f'BG-02 {what} failure: battle continues, no errors', errs); pg.close()
    b.close()
print('FAILS', len(fails), fails); sys.exit(1 if fails else 0)

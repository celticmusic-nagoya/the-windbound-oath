"""Issue #70: event CGs (js/event-cg.js) in the Lou first-meeting scene and the altar scene, and 風の舞 after learning.
Real flow: A3 sanctuary -> Lou intro (zone) -> altar (trigger zone) -> raider battle. Per line the visible CG must match:
  louIntroLines 3-5 lou_first | altarLines 14-16 cg01, 18-20 cg02, 21-23 cg03, 32-35 cg04 (cg04 starts with the FX fade-out).
Also: each CG once, scenario/flags unchanged, touch + keyboard, rapid clicks, load failure, ?eventCg=0, save/continue, raider
oath sword at the raider battle, 風の舞 unusable before / usable after learning (normal + raider battle),
CG framing on 10 viewports. Screenshots / timings go to QA_OUT when set (outside the checkout)."""
import hashlib, json, os, sys, time
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
EV = 'assets/images/events/'
SHA = {'moss_lou_first_meeting_cg_v1.png': '960ac2335348195e68cf06094228cbdf272fd55a1137b037d340a5b65c3c79bf',
       'moss_altar_cg01_father_sword_break_v1.png': '94ed1387d2268a783b57e2147292b82b6c7fc01268e861190205aec4078fb2c7',
       'moss_altar_cg02_wind_dance_first_v1.png': 'e695a27c81f9c65f4999549fd41dec44670a171833f0036fffa03d88dcd7f4c3',
       'moss_altar_cg03_lou_stall_v1.png': '28138ecc2ee022c2bb85b5cde4af0d034ada5289dd20182a24ba882a067e988c',
       'moss_altar_cg04_oath_contract_v1.png': '0e8963dc3afe3c192d71bb761c609fccfe7273a98a00c91ac27c23ee0a68d92a'}
for f, h in SHA.items():
    check(hashlib.sha256((ROOT / EV / f).read_bytes()).hexdigest() == h, 'official CG unmodified: ' + f)
# New adopted files must match the delivery ledger exactly; old PNG hashes above remain regression-checked.
ADOPTED = json.loads((ROOT / 'img/events/adopted-cg.json').read_text())['scenes']
from PIL import Image
for key, pair in ADOPTED.items():
    for orientation, delivery in pair.items():
        f = ROOT / 'img/events' / delivery['file']
        with Image.open(f) as im:
            im.load()
            check(im.format == 'PNG' and im.size == (delivery['width'], delivery['height']) and
                  abs(im.width / im.height / (16/9 if orientation == 'landscape' else 9/16) - 1) < .001 and
                  hashlib.sha256(f.read_bytes()).hexdigest() == delivery['sha256'], f'{key} {orientation}: adopted delivery bytes / dimensions / ratio')
EXPECT_ALTAR = {**{i: 'altar_cg01' for i in (14, 15, 16)}, **{i: 'altar_cg02' for i in (18, 19, 20)},
                **{i: 'altar_cg03' for i in (21, 22, 23)}, **{i: 'altar_cg04' for i in (32, 33, 34, 35)}}
EXPECT_LOU = {3: 'lou_first', 4: 'lou_first', 5: 'lou_first'}
A3 = 'moss_forest_03_ancient_grove'
DBG = "k=>EventCG.debug(k)"
timing = {}

def boot(b, w, h, query='', touch=False, block=False):
    ctx = b.new_context(viewport={'width': w, 'height': h}, is_mobile=touch, has_touch=touch)
    pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('response', lambda response: errs.append('CG HTTP '+str(response.status)+' '+response.url) if '/img/events/' in response.url and response.status>=400 else None)
    if block: pg.route('**/img/events/*.png', lambda r: r.abort())
    pg.goto(base + '/index.html?title=0' + query); pg.wait_for_function("LoadCoordinator.phase==='READY'"); pg.wait_for_timeout(700); pg.evaluate('closeDialogue()')
    return ctx, pg, errs

def advance(pg, scene, mode):
    if mode == 'touch': vp = pg.viewport_size; pg.touchscreen.tap(vp['width'] * .5, vp['height'] * .45)
    elif mode == 'key': pg.keyboard.press('Enter')
    else: pg.evaluate("s=>document.getElementById(s).click()", scene)

def on(pg, key):
    d = pg.evaluate(DBG, key); return (d or {}).get('on', [])

def to_sanctuary(pg):
    pg.evaluate("PrologueProgress.seed(3);storyStage=10;forestActive=true;louFound=false;giveStarterSword();document.querySelector('#forestScene').style.display='block'")
    pg.evaluate("m=>MossForest.enter({map:m,flags:Object.assign(MossForestStory.flagsNow(),{moss_a3_seal_open:true})})", A3)
    pg.wait_for_function("MossForest.active&&!MossForest.busy", timeout=30000); pg.wait_for_timeout(500); pg.evaluate('closeDialogue()')

def play_real_flow(pg, mode, tag, shots=None):
    """A3 -> Lou intro -> altar -> raider battle. Returns per-line CG lists."""
    to_sanctuary(pg)
    pg.evaluate("MossForest.setFlag('moss_a3_seal_open',true)")
    pg.evaluate("([x,y])=>MossForest.teleportFeet(x,y)", [4395, 2900]); pg.wait_for_timeout(600)
    if pg.evaluate("document.querySelector('#louIntroScene').style.display") != 'block': pg.evaluate("MossForest.interactNearest()")
    pg.wait_for_function("document.querySelector('#louIntroScene').style.display==='block'", timeout=10000)
    check(True, f'[{tag}] Lou intro starts from its A3 zone')
    lou = {0: on(pg, 'louIntro')}; L = pg.evaluate("louIntroLines.length")
    for i in range(1, L):
        advance(pg, 'louIntroScene', mode); pg.wait_for_timeout(700)
        lou[i] = on(pg, 'louIntro')
        if shots is not None and i == 3: shots['lou'] = pg.screenshot()
    shown = pg.evaluate(DBG, 'louIntro')
    advance(pg, 'louIntroScene', mode); pg.wait_for_function("MossForest.active", timeout=10000)
    check(all(lou[i] == ([EXPECT_LOU[i]] if i in EXPECT_LOU else []) for i in lou), f'[{tag}] Lou CG on lines 3-5 only', lou)
    check(shown and shown['shown'] == {'lou_first': 1}, f'[{tag}] Lou CG shown exactly once', shown)
    check(pg.evaluate("louFound") is True and pg.evaluate("storyStage") == 11 and pg.evaluate("MossForest.flags.moss_a3_lou_found") is True, f'[{tag}] Lou intro result unchanged (louFound, stage 11, flag)')
    check(pg.evaluate("document.querySelectorAll('#louIntroScene .event-cg-item').length") == 0, f'[{tag}] Lou CG released when the scene ends')
    pg.evaluate("closeDialogue()"); pg.evaluate("([x,y])=>MossForest.teleportFeet(x,y)", [4750, 3070])
    pg.wait_for_function("document.querySelector('#altarScene').style.display==='block'", timeout=15000)
    check(pg.evaluate("MossForest.active") is False, f'[{tag}] altar scene starts from its A3 trigger, forest paused')
    pg.wait_for_function("['altar_cg01','altar_cg02','altar_cg03','altar_cg04'].every(k=>EventCG.debug('altar').status[k]==='ready')", timeout=30000)
    lines = pg.evaluate("altarLines"); grip = next(i for i, l in enumerate(lines) if l.startswith('エイダンが柄を握る'))
    alt = {0: on(pg, 'altar')}; t = {}
    for i in range(1, len(lines)):
        advance(pg, 'altarScene', mode)
        if i == grip:
            t0 = time.time(); seq = []
            while time.time() - t0 < 6.5:
                seq.append((round(time.time() - t0, 2), pg.evaluate("AltarArt.phase"), on(pg, 'altar'),
                            round(pg.evaluate("(()=>{const e=document.querySelector('#altarScene [data-cg=altar_cg04]');return e?+getComputedStyle(e).opacity:0})()"), 2),
                            round(pg.evaluate("+getComputedStyle(document.querySelector('#altarContractFx')).opacity"), 2)))
                if shots is not None and 'fx' not in shots and seq[-1][1] == 'hold' and seq[-1][0] > 1.5: shots['fx'] = pg.screenshot()
                pg.wait_for_timeout(150)
            t['grip'] = seq
            alt[i] = on(pg, 'altar')
            if shots is not None: shots['cg4'] = pg.screenshot()
        else:
            pg.wait_for_timeout(650); alt[i] = on(pg, 'altar')
            if shots is not None and i in (14, 18, 21): shots[{14: 'cg1', 18: 'cg2', 21: 'cg3'}[i]] = pg.screenshot()
        if i == 13: check(pg.evaluate("EquipmentManager.get('aidan').weapon") == 'father_sword', f'[{tag}] father sword held until the break line')
        if i == 14: check(pg.evaluate("EquipmentManager.get('aidan').weapon") is None, f'[{tag}] father sword broken on line 14 (unarmed until the contract)')
        if i == 19: check(pg.evaluate("WindDance.learned()") is False, f'[{tag}] 風の舞 not learned before its first cast')
        if i == 20: check(pg.evaluate("WindDance.learned()") is True, f'[{tag}] 風の舞 learned on its first cast (line 20)')
        if i == grip - 1: check(pg.evaluate("oathBound") is False and pg.evaluate("AltarArt.phase") == 'idle', f'[{tag}] no contract / FX before the grip line')
    shown = pg.evaluate(DBG, 'altar')
    check(all(alt[i] == ([EXPECT_ALTAR[i]] if i in EXPECT_ALTAR else []) for i in alt), f'[{tag}] altar CGs on 14-16 / 18-20 / 21-23 / 32-35 only',
          {i: v for i, v in alt.items() if v != ([EXPECT_ALTAR[i]] if i in EXPECT_ALTAR else [])})
    check(shown['shown'] == {'altar_cg01': 1, 'altar_cg02': 1, 'altar_cg03': 1, 'altar_cg04': 1}, f'[{tag}] each altar CG shown exactly once', shown)
    g = t['grip']; out_t = next((s[0] for s in g if s[1] == 'out'), None); cg4_t = next((s[0] for s in g if 'altar_cg04' in s[2]), None)
    check(out_t is not None and cg4_t is not None and abs(cg4_t - out_t) <= .35 and 3.2 <= out_t <= 3.9, f'[{tag}] CG4 starts with the FX fade-out (~3.5 s after the grip)', (out_t, cg4_t))
    check(any(s[3] > .1 and s[3] < .9 for s in g) and g[-1][3] >= .99, f'[{tag}] CG4 fades in (no hard cut) and stays', [s[3] for s in g])
    check(all(s[2] == [] for s in g if s[0] < (out_t or 0) - .2), f'[{tag}] CG4 not shown while the FX rises/holds')
    check(pg.evaluate("oathBound") is True and pg.evaluate("EquipmentManager.get('aidan').weapon") == 'oath_sword', f'[{tag}] contract result unchanged')
    timing[tag] = g
    advance(pg, 'altarScene', mode)
    pg.wait_for_function("document.querySelector('#raiderBattle').style.display==='block'", timeout=30000)
    check(pg.evaluate("document.querySelectorAll('#altarScene .event-cg-item').length") == 0 and pg.evaluate("AltarArt.phase") == 'idle', f'[{tag}] scene end: CGs released, FX reset')
    check(pg.evaluate("EquipmentManager.get('aidan').weapon") == 'oath_sword', f'[{tag}] raider battle starts with the oath sword')
    return lines

def raider_ready(pg):
    pg.wait_for_function("document.querySelector('#raiderBattle').style.display==='block'&&!rbBusy&&!battleCommandLocked('raider')", timeout=30000)

with server(8820) as base, sync_playwright() as p:
    b = p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None))
    # ---- ranges resolve to the approved lines
    ctx, pg, errs = boot(b, 1280, 720)
    r = {k: [(c['cg'], c['a'], c['b']) for c in pg.evaluate("k=>EventCG.ranges(k)", k)] for k in ('louIntro', 'altar')}
    check(r['louIntro'] == [('lou_first', 3, 5)], 'Lou CG cue = louIntroLines 3-5', r)
    check(r['altar'] == [('altar_cg01', 14, 16), ('altar_cg02', 18, 20), ('altar_cg03', 21, 23), ('altar_cg04', 32, 35)], 'altar CG cues = 14-16 / 18-20 / 21-23 / 32-35', r)
    L = pg.evaluate("altarLines")
    check(len(L) == 37 and not any('裂け目' in l or '落ちて' in l for l in L), 'altar script unchanged in length, no "sword falls into the rift" beat')
    ctx.close()
    # ---- real flow: portrait touch and landscape keyboard
    for tag, (w, h), mode in (('portrait_touch_390x844', (390, 844), 'touch'), ('landscape_key_1280x720', (1280, 720), 'key')):
        ctx, pg, errs = boot(b, w, h, touch=(mode == 'touch'))
        shots = {}
        play_real_flow(pg, mode, tag, shots)
        if OUT:
            for k, v in shots.items(): (OUT / f'{tag}_{k}.png').write_bytes(v)
        # raider battle: 風の舞 usable (learned), cast through the command path
        raider_ready(pg)
        pg.evaluate("choosePartyAct('guard','aidan')"); pg.wait_for_timeout(200)
        check(pg.evaluate("rbActor") == 'fiona' and pg.evaluate("!document.querySelector('#rbWindDance').hidden"), f'[{tag}] raider battle: 風の舞 command shown for Fiona after learning')
        mp0 = pg.evaluate("rbFMP"); pg.evaluate("choosePartyAct('winddance','party')")
        pg.wait_for_function("!rbBusy", timeout=40000)
        eva = pg.evaluate("BattleStatus.list('raider','aidan').filter(e=>e.type==='eva_up').map(e=>e.magnitude)")
        check(pg.evaluate("rbFMP") == mp0 - 10 and eva == [0.15], f'[{tag}] raider battle: 風の舞 costs MP10 and gives +15pt evasion', (mp0, pg.evaluate("rbFMP"), eva))
        # NOTE defeat -> retry is not covered here: on main the retry after a raider defeat is refused by the battle-loading gate
        # (body.battleMode still set) and the battle soft-locks (pre-existing, reported separately; battle code is out of scope).
        # win -> aftermath -> save -> load
        raider_ready(pg); pg.evaluate("PrologueCombat.instantKill('raider')")
        pg.wait_for_function("getComputedStyle(document.querySelector('#battleResult')).display!=='none'", timeout=30000)
        pg.evaluate("document.querySelector('#resultContinue').click()"); pg.wait_for_timeout(800)
        check(pg.evaluate("storyStage") == 13, f'[{tag}] victory -> aftermath (stage 13)')
        check(not errs, f'[{tag}] no page errors', errs[:3]); ctx.close()
    # ---- save / continue around the events
    ctx, pg, errs = boot(b, 844, 390, touch=True)
    to_sanctuary(pg)
    pg.evaluate("startLouIntro()")
    for _ in range(8): pg.evaluate("document.querySelector('#louIntroScene').style.display==='block'&&document.querySelector('#louIntroScene').click()")
    pg.wait_for_function("MossForest.active&&!MossForest.busy", timeout=10000); pg.evaluate("closeDialogue()")
    pg.evaluate("localStorage.removeItem(SAVE_KEY);renderSystemTab('save');saveGrowthData()")
    saved = pg.evaluate("localStorage.getItem(SAVE_KEY)!==null")
    check(saved, 'save after the Lou intro (A3 field, stage 11) works')
    pg.evaluate("loadGrowthData()"); pg.wait_for_function("MossForest.active&&!MossForest.busy", timeout=30000); pg.evaluate("closeDialogue()")
    check(pg.evaluate("storyStage") == 11 and pg.evaluate("louFound") is True and pg.evaluate("WindDance.learned()") is False, 'load at stage 11: Lou found, 風の舞 not yet learned')
    pg.evaluate("([x,y])=>MossForest.teleportFeet(x,y)", [4750, 3070])
    pg.wait_for_function("document.querySelector('#altarScene').style.display==='block'", timeout=15000)
    for _ in range(14): pg.evaluate("document.querySelector('#altarScene').click()")
    pg.wait_for_timeout(1200)
    check(on(pg, 'altar') == ['altar_cg01'] and pg.evaluate(DBG, 'altar')['shown'] == {'altar_cg01': 1}, 'after load: altar replays, CG1 shown once at line 14')
    # the menu (and so SAVE) cannot be reached during the altar scene: the scene covers the MENU button and swallows M
    # (saveGrowthData() itself does not refuse here when called directly - pre-existing, not reachable by the player)
    pg.keyboard.press('m'); pg.wait_for_timeout(300)
    covered = pg.evaluate("(()=>{const r=document.querySelector('#menuOpen').getBoundingClientRect();const e=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return !e||e.id!=='menuOpen'})()")
    check(covered and pg.evaluate("getComputedStyle(document.querySelector('#systemMenu')).display") == 'none', 'altar scene: MENU button covered and M key does not open the menu (no mid-scene save via UI)')
    check(not errs, 'save/continue: no page errors', errs[:3]); ctx.close()
    # ---- rapid input: 37 clicks without waiting, and fast advance after the grip
    ctx, pg, errs = boot(b, 390, 844, touch=True)
    pg.evaluate("PrologueProgress.seed(3);giveStarterSword();devResetScreens();closeDialogue();startAltarScene()")
    pg.evaluate("for(let i=0;i<37;i++)document.querySelector('#altarScene').click()")
    pg.wait_for_function("document.querySelector('#raiderBattle').style.display==='block'", timeout=30000)
    check(pg.evaluate("document.querySelectorAll('.event-cg-item.on').length") == 0 and pg.evaluate("AltarArt.phase") == 'idle' and pg.evaluate("EquipmentManager.get('aidan').weapon") == 'oath_sword',
          'rapid 37 clicks: scene ends cleanly, no CG left, FX reset, oath sword equipped')
    pg.wait_for_timeout(4500)
    check(pg.evaluate("document.querySelectorAll('.event-cg-item').length") == 0, 'rapid clicks: a late FX fade-out does not bring back CG4')
    pg.evaluate("devResetScreens();closeDialogue();startAltarScene()")
    pg.wait_for_function("EventCG.debug('altar').status.altar_cg04==='ready'", timeout=30000)
    pg.evaluate("for(let i=0;i<32;i++)document.querySelector('#altarScene').click()")
    pg.wait_for_timeout(300); pg.evaluate("document.querySelector('#altarScene').click()")   # line 33 right after the grip
    check(on(pg, 'altar') == [], 'fast advance to line 33: CG4 waits for the FX fade-out')
    pg.wait_for_timeout(3800)
    check(on(pg, 'altar') == ['altar_cg04'], 'fast advance to line 33: CG4 appears with the FX fade-out')
    pg.evaluate("devResetScreens();closeDialogue();startAltarScene()")
    pg.wait_for_function("EventCG.debug('altar').status.altar_cg04==='ready'", timeout=30000)
    pg.evaluate("for(let i=0;i<36;i++)document.querySelector('#altarScene').click()")   # line 36 before 3.5 s
    pg.wait_for_timeout(5600)
    check(on(pg, 'altar') == [] and pg.evaluate(DBG, 'altar')['shown'].get('altar_cg04', 0) == 0 and pg.evaluate("AltarArt.phase") == 'idle',
          'skip to line 36 before the fade-out: CG4 not shown, FX completes and resets')
    pg.evaluate("devResetScreens();closeDialogue();startAltarScene()")
    check(pg.evaluate(DBG, 'altar')['shown'] == {} and on(pg, 'altar') == [], 'replay starts clean (no stale CG)')
    check(not errs, 'rapid input: no page errors', errs[:3]); ctx.close()
    # ---- load failure: CG requests aborted -> scenes still advance, nothing shown
    ctx, pg, errs = boot(b, 844, 390, block=True)
    pg.evaluate("PrologueProgress.seed(3);giveStarterSword();devResetScreens();closeDialogue();startAltarScene()")
    pg.wait_for_function("Object.values(EventCG.debug('altar').status).every(s=>s==='failed')", timeout=15000)
    seen = []
    for i in range(1, 37): pg.evaluate("document.querySelector('#altarScene').click()"); seen += on(pg, 'altar')
    pg.wait_for_timeout(4500); seen += on(pg, 'altar')
    pg.evaluate("document.querySelector('#altarScene').click()")
    pg.wait_for_function("document.querySelector('#raiderBattle').style.display==='block'", timeout=30000)
    check(seen == [] and pg.evaluate("EquipmentManager.get('aidan').weapon") == 'oath_sword', 'CG load failure: no CG, event completes, raider battle starts')
    check(not errs, 'load failure: no page errors', errs[:3]); ctx.close()
    # ---- ?eventCg=0 disables the layer
    ctx, pg, errs = boot(b, 844, 390, query='&eventCg=0')
    pg.evaluate("PrologueProgress.seed(3);giveStarterSword();devResetScreens();closeDialogue();startAltarScene()")
    for i in range(14): pg.evaluate("document.querySelector('#altarScene').click()")
    check(pg.evaluate("document.querySelectorAll('.event-cg').length") == 0, '?eventCg=0: no CG layer'); ctx.close()
    # ---- 風の舞: not usable before learning; usable in a normal battle after learning
    ctx, pg, errs = boot(b, 844, 390)
    pg.evaluate("PrologueProgress.seed(3);delete PartyManager.members.fiona.learned;startAttackBattle('fieldGob1',100)"); pg.wait_for_timeout(1500)
    pg.evaluate("normalActor='fiona';updateNormalCommands()")
    check(pg.evaluate("WindDance.learned()") is False and pg.evaluate("document.querySelector('#nWindDance').hidden") is True, 'normal battle before learning: 風の舞 hidden')
    pg.evaluate("WindDance.learn();normalActor='fiona';updateNormalCommands()")
    check(pg.evaluate("!document.querySelector('#nWindDance').hidden"), 'normal battle after learning: 風の舞 shown (default build)')
    ctx.close()
    ctx, pg, errs = boot(b, 844, 390, query='&windDance=off')
    pg.evaluate("WindDance.learn()"); check(pg.evaluate("WindDance.commandVisible()") is False, '?windDance=off rollback switch hides the command'); ctx.close()
    # ---- framing on 10 viewports: CG area above the text box, inside the screen, focus regions visible
    NEED = {'lou_first': (.40, .78), 'altar_cg01': (.28, .50), 'altar_cg02': (.38, .52), 'altar_cg03': (.28, .60), 'altar_cg04': (.40, .66)}
    VIEWS = {'portrait_320x568': (320, 568), 'portrait_360x800': (360, 800), 'portrait_390x844': (390, 844), 'portrait_412x915': (412, 915),
             'tablet_768x1024': (768, 1024), 'landscape_667x375': (667, 375), 'landscape_844x390': (844, 390), 'landscape_915x412': (915, 412), 'landscape_1280x720': (1280, 720), 'landscape_1920x1080': (1920, 1080)}
    GEOM = """k=>{const e=document.querySelector('.event-cg-item.on');if(!e)return null;const f=e.querySelector('.event-cg-frame').getBoundingClientRect(),
      i=[...e.querySelectorAll('.event-cg-img')].find(im=>getComputedStyle(im).display!=='none'),t=document.querySelector(k==='louIntro'?'#louIntroText':'#altarText').getBoundingClientRect(),cs=getComputedStyle(i);
      return {f:[f.left,f.top,f.right,f.bottom],text_top:t.top,vw:innerWidth,vh:innerHeight,fit:cs.objectFit,pos:cs.objectPosition,nw:i.naturalWidth,nh:i.naturalHeight,
       src:i.getAttribute('src'),visible:e.querySelectorAll('img').length&&[...e.querySelectorAll('img')].filter(im=>getComputedStyle(im).display!=='none').length,backs:e.querySelectorAll('img').length,mask:getComputedStyle(e.querySelector('.event-cg-frame')).maskImage||getComputedStyle(e.querySelector('.event-cg-frame')).webkitMaskImage||'none',
       dev:['devBtn','devBuildIndicator'].map(id=>{const d=document.getElementById(id);return !!d&&getComputedStyle(d).display!=='none'})}}"""
    import io
    from PIL import Image
    def seams(png, g):
        """visual check on the real screenshot: margins are dark (no copy of the CG behind it) and no hard step at the CG edges"""
        im = Image.open(io.BytesIO(png)).convert('L'); sx = im.width / g['vw']; sy = im.height / g['vh']
        fl, ft, fr, fb = [round(v) for v in g['f']]; top_txt = g['text_top']; res = {}
        def col(x, y0, y1):
            x = max(0, min(im.width - 1, int(x * sx))); vals = [im.getpixel((x, int(y * sy))) for y in range(int(y0), int(y1), 3)]; return sum(vals) / max(1, len(vals))
        def row(y, x0, x1):
            y = max(0, min(im.height - 1, int(y * sy))); vals = [im.getpixel((int(x * sx), y)) for x in range(int(x0), int(x1), 3)]; return sum(vals) / max(1, len(vals))
        y0, y1 = max(ft, 0) + 4, min(fb, top_txt) - 4
        if fl > 8:   # side margins (landscape)
            res['margin'] = max(col(fl / 2, y0, y1), col((fr + g['vw']) / 2, y0, y1))
            res['step'] = max(abs(col(fl + 1, y0, y1) - col(fl - 2, y0, y1)), abs(col(fr - 2, y0, y1) - col(fr + 1, y0, y1)))
        if ft > 8:   # top / bottom margins (portrait)
            res['margin'] = max(res.get('margin', 0), row(ft / 2, 4, g['vw'] - 4))
            res['step'] = max(res.get('step', 0), abs(row(ft + 1, 4, g['vw'] - 4) - row(ft - 2, 4, g['vw'] - 4)))
        return res
    for view, (w, h) in VIEWS.items():
        ctx, pg, errs = boot(b, w, h, touch=w < h or h < 500)
        pg.evaluate("PrologueProgress.seed(3);giveStarterSword();devResetScreens();closeDialogue();startLouIntro()")
        pg.wait_for_function("EventCG.debug('louIntro').status.lou_first==='ready'", timeout=30000)
        for _ in range(3): pg.evaluate("document.querySelector('#louIntroScene').click()")
        pg.wait_for_timeout(900); geo = {'lou_first': pg.evaluate(GEOM, 'louIntro')}; shots = {'lou_first': pg.screenshot()}
        if OUT: pg.screenshot(path=str(OUT / f'{view}_lou.png'))
        for _ in range(5): pg.evaluate("document.querySelector('#louIntroScene').style.display==='block'&&document.querySelector('#louIntroScene').click()")
        pg.evaluate("devResetScreens();closeDialogue();startAltarScene()")
        pg.wait_for_function("['altar_cg01','altar_cg02','altar_cg03','altar_cg04'].every(k=>EventCG.debug('altar').status[k]==='ready')", timeout=30000)
        idx = 0
        for target, key in ((14, 'altar_cg01'), (18, 'altar_cg02'), (21, 'altar_cg03'), (32, 'altar_cg04')):
            while idx < target: pg.evaluate("document.querySelector('#altarScene').click()"); idx += 1
            pg.wait_for_timeout(5200 if key == 'altar_cg04' else 900)
            geo[key] = pg.evaluate(GEOM, 'altar'); shots[key] = pg.screenshot()
            if OUT: pg.screenshot(path=str(OUT / f'{view}_{key}.png'))
        for key, g in geo.items():
            if not g: check(False, f'[{view}] {key} visible'); continue
            fl, ft, fr, fb = g['f']
            fw, fh = fr - fl, fb - ft
            if w < h:   # portrait: the CG box ends above the text box
                inside = fl >= -.5 and ft >= -.5 and fr <= g['vw'] + .5 and fb <= g['vh'] + .5 and fb <= g['text_top'] + 1
            else:       # Complete landscape delivery above dialogue; no hidden sword / hands under text.
                inside = fl >= -.5 and ft >= -.5 and fr <= g['vw'] + .5 and fb <= g['text_top'] + 1
            expected = ADOPTED[key]['portrait' if w < h else 'landscape']
            check(g['src'] == 'img/events/' + expected['file'] and (g['nw'],g['nh']) == (expected['width'],expected['height']) and g['fit']=='contain' and abs(fw/fh - g['nw']/g['nh']) < .01, f'[{view}] {key}: correct orientation, complete image, no distortion', g)
            check(g['backs'] == 2 and g['visible'] == 1 and 'gradient' in g['mask'] and not any(g['dev']), f'[{view}] {key}: one visible orientation (no enlarged copy behind), feathered edges, DEV button hidden',
                  {'imgs': g['backs'], 'mask': g['mask'][:60], 'dev': g['dev']})
            v = seams(shots[key], g)
            check(v.get('margin', 0) < 40 and v.get('step', 0) < 18, f'[{view}] {key}: screenshot - dark margins, no hard edge line at the CG border', {k: round(x, 1) for k, x in v.items()})
            if g['fit'] == 'cover':
                vis = min(1, fw / (g['nw'] * fh / g['nh'])); focus = float(g['pos'].split('%')[0]) / 100; x0 = focus * (1 - vis); rng = (x0, x0 + vis)
            else:
                rng = (0, 1)
            need = NEED[key]
            check(inside and rng[0] <= need[0] + 1e-6 and rng[1] >= need[1] - 1e-6, f'[{view}] {key}: inside the screen, as large as allowed (portrait: above the text), key region visible',
                  {'frame': [round(v) for v in g['f']], 'text_top': round(g['text_top']), 'fit': g['fit'], 'visible_x': [round(v, 3) for v in rng]})
            if w < h: check(fh >= .38 * h, f'[{view}] {key}: portrait CG not shrunk (frame {round(fh)} px of {h})')
        check(not errs, f'[{view}] no page errors', errs[:3]); ctx.close()
    # Rotate every CG while it is active. Both decoded deliveries remain attached: no request, blank or stale variant on rotation.
    for key in ADOPTED:
        ctx, pg, errs = boot(b, 390, 844, touch=True)
        scene = 'louIntro' if key == 'lou_first' else 'altar'
        pg.evaluate("k=>{PrologueProgress.seed(3);giveStarterSword();devResetScreens();closeDialogue();if(k==='louIntro')startLouIntro();else startAltarScene()}", scene)
        pg.wait_for_function("([s,k])=>EventCG.debug(s).status[k]==='ready'", arg=[scene,key])
        target = {'lou_first':3,'altar_cg01':14,'altar_cg02':18,'altar_cg03':21,'altar_cg04':32}[key]
        for _ in range(target): pg.evaluate("s=>document.getElementById(s+'Scene').click()", scene)
        pg.wait_for_timeout(5200 if key == 'altar_cg04' else 700)
        requests=[]; pg.on('request',lambda req: requests.append(req.url) if '/img/events/' in req.url else None)
        for vw,vh in ((844,390),(390,844),(915,412),(360,640)):
            pg.set_viewport_size({'width':vw,'height':vh})
            # No network/decode wait: after one frame the already loaded orientation must be visible.
            pg.evaluate("()=>new Promise(r=>requestAnimationFrame(()=>r()))")
            g=pg.evaluate(GEOM,scene); orientation='portrait' if vw < vh else 'landscape'
            check(g and g['visible']==1 and g['src']=='img/events/'+ADOPTED[key][orientation]['file'] and g['nw']>0 and not any(g['dev']) and g['f'][3]<=g['text_top']+1,
                  f'{key}: rotation {vw}x{vh} immediately shows correct full CG above text, DEV hidden',g)
        check(not requests,f'{key}: rotation needs no new image request',requests)
        for _ in range(40): pg.evaluate("s=>{const e=document.getElementById(s+'Scene');if(e.style.display==='block')e.click()}",scene)
        pg.wait_for_timeout(800)
        check(not pg.evaluate("document.body.classList.contains('eventCgOn')") and pg.evaluate("document.querySelectorAll('.event-cg-item').length")==0,
              f'{key}: scene end clears CG marker and releases both images')
        check(not errs,f'{key}: rotation no page errors',errs[:3]);ctx.close()
    b.close()
if OUT: (OUT / 'cg4_fx_timing.json').write_text(json.dumps(timing, indent=1, ensure_ascii=False))
print('FAILS', len(fails)); sys.exit(1 if fails else 0)

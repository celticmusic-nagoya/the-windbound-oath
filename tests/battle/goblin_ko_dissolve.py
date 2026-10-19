"""Goblin / tainted goblin KO dissolve (6 delivered frames each) driven by the existing BattleMotion manifest (hold:'hide').
Order: HP 0 -> KO state -> dissolve frames 1..6 in order, once -> sprite hidden after the last frame -> Victory. No re-action while dissolving,
Victory/KO race does not cut it, nothing stale after stop/next battle. PC + phone portrait + phone landscape. Logic/damage/difficulty untouched."""
import os, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
ROOT = Path(__file__).resolve().parents[2]; fails = []
def check(ok, name, detail=''):
    print(('ok   ' if ok else 'FAIL ') + name, detail, flush=True)
    if not ok: fails.append(name)
man = json.load(open(ROOT / 'img/battle/motion-manifest.json'))['motions']
for actor in ('goblin', 'tainted_goblin'):
    d = man[actor]['ko']; ims = [Image.open(ROOT / 'img/battle/enemies' / actor / ('goblin_ko_dissolve_%02d.png' % i)).convert('RGBA') for i in range(1, 7)]
    check(d['frames'] == 6 and d['hold'] == 'hide' and len(d['ms']) == 6, '%s manifest: 6 frames, hold hide' % actor, sum(d['ms']))
    check(len({i.size for i in ims}) == 1 and all(np.array(i)[..., 3].min() == 0 for i in ims), '%s frames share one canvas, transparent surround' % actor, ims[0].size)
    check(all(np.array(i)[..., 3].max() > 200 for i in ims), '%s frames all carry visible content' % actor)
check(man['moss_slime']['ko']['hold'] == 'last' and man['leafy_boar']['ko']['hold'] == 'last' and 'attack' not in man['goblin'] and 'attack' not in man['tainted_goblin'], 'other enemies / other states untouched (slime, boar ko = hold last; goblin has ko only)')
TRACE = """()=>{const im=document.querySelector('#bGob img');window.__k={seq:[],end:[],t0:performance.now(),errs:[]};
 const push=()=>{const f=+im.dataset.motionFrame;if(f&&__k.seq[__k.seq.length-1]?.f!==f)__k.seq.push({f,t:Math.round(performance.now()-__k.t0)})};
 new MutationObserver(push).observe(im,{attributes:true,attributeFilter:['data-motion-frame','src']});
 addEventListener('battle-motion-end',e=>__k.end.push({t:Math.round(performance.now()-__k.t0),d:e.detail}));return 1}"""
SNAP = "()=>{const im=document.querySelector('#bGob img');const b=document.querySelector('#bGob');const ims=PrologueCombat.enemies.normal.map(e=>document.querySelector(e.node+' img'));return {n:ims.length,hid:ims.map(i=>getComputedStyle(i).visibility==='hidden'),allHidden:ims.every(i=>getComputedStyle(i).visibility==='hidden'),stage:getComputedStyle(document.querySelector('#attackBattle')).display,vis:getComputedStyle(im).visibility,gone:im.dataset.motionGone||null,boxDisp:getComputedStyle(b).display,hidden:b.hidden,st:BattleActorState.get('normal','enemy_0'),k:window.__k&&{seq:__k.seq,end:__k.end}}}"
with server(8826) as base, sync_playwright() as p:
    b = p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None))
    for vp in [(1280, 720), (390, 844), (844, 390)]:
        for mode in ('natural', 'race'):
            pg = b.new_page(viewport={'width': vp[0], 'height': vp[1]}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.goto(base + '/index.html?dev=1'); pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.PrologueCombat'); pg.wait_for_timeout(1500); pg.evaluate("closeDialogue()")
            tag = '%s %s' % (vp, mode)
            pg.evaluate("PrologueProgress.seed(0);startAttackBattle('attackGob1',100)"); pg.wait_for_timeout(2600)
            if mode == 'natural': pg.evaluate("PrologueCombat.enemies.normal[0].hp=1;PrologueCombat.sync('normal')")   # test setup only: leave the enemy 1 HP so a real attack finishes it
            pre = pg.evaluate(SNAP)
            check(pre['vis'] == 'visible' and pre['st'] == 'idle', '%s: enemy visible and idle before the blow' % tag, pre['st'])
            pg.evaluate(TRACE)
            if mode == 'natural': pg.evaluate("chooseNormalAct('attack','normal_enemy_0')")
            else: pg.evaluate("PrologueCombat.instantKill('normal')")
            # wait for KO state
            pg.wait_for_function("BattleActorState.get('normal','enemy_0')==='ko'", timeout=9000)
            re = pg.evaluate("BattleActorState.set('enemy_0','attack',{battle:'normal',duration:500})")
            check(re is False, '%s: a KO enemy cannot be put back into an action state (no re-action while dissolving)' % tag)
            pg.wait_for_timeout(450); mid = pg.evaluate(SNAP)
            check(mid['st'] == 'ko' and mid['vis'] == 'visible' and mid['gone'] is None, '%s: mid-dissolve still visible' % tag, [s['f'] for s in mid['k']['seq']])
            pg.wait_for_timeout(1000); aft = pg.evaluate(SNAP); frs = [s['f'] for s in aft['k']['seq']]
            check(frs == [1, 2, 3, 4, 5, 6], '%s: dissolve plays frames 1..6 in order, exactly once' % tag, frs)
            exp = 1 if mode == 'natural' else aft['n']
            check(len(aft['k']['end']) == exp and all(e['d']['actor'] in ('tainted_goblin', 'goblin') for e in aft['k']['end']) and aft['hid'][0] and aft['vis'] == 'hidden' and aft['gone'] == '1' and (mode != 'natural' or not aft['hid'][1]), '%s: after the last frame the dead enemy sprite is hidden (%d of %d), one end event each' % (tag, exp, aft['n']), aft['k']['end'])
            span = frs and (aft['k']['end'][0]['t'] - aft['k']['seq'][0]['t'])
            check(950 <= span <= 1300, '%s: dissolve duration ~1050 ms (from manifest ms)' % tag, span)
            check(aft['stage'] != 'none', '%s: the battle stage is still up when the dissolve ends' % tag)
            if mode == 'natural':
                # partial KO: the survivor keeps fighting, nothing else is hidden; then the real finishing blow ends the battle
                pg.wait_for_function('!attackBattleBusy&&!BattlePresentation.busy', timeout=20000)
                mid2 = pg.evaluate(SNAP)
                check(mid2['stage'] != 'none' and mid2['hid'] == [True, False], '%s: after the first KO the other goblin is still visible and the battle continues' % tag, mid2['hid'])
                pg.evaluate("PrologueCombat.enemies.normal[1].hp=1;PrologueCombat.sync('normal')"); pg.evaluate("chooseNormalAct('attack','normal_enemy_1')")
                pg.wait_for_function("BattleActorState.get('normal','enemy_1')==='ko'", timeout=9000); pg.wait_for_timeout(1500)
                fin = pg.evaluate(SNAP); check(fin['hid'] == [True, True] and fin['stage'] != 'none', '%s: second goblin dissolved and hidden before the Victory teardown' % tag, fin['hid'])
            pg.wait_for_timeout(3200); end = pg.evaluate(SNAP)
            check(end['stage'] == 'none', '%s: Victory flow then tears the stage down as before (after the dissolve)' % tag)
            check(len(end['k']['seq']) >= 6, '%s: Victory did not cut the dissolve (all 6 frames were shown)' % tag, len(end['k']['seq']))
            check(not errs, '%s: no page errors' % tag, errs[:2]); pg.close()
    # stale timer / restore: stop mid-dissolve, then a new battle shows the enemy normally
    pg = b.new_page(viewport={'width': 1280, 'height': 720}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(base + '/index.html?dev=1'); pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.PrologueCombat'); pg.wait_for_timeout(1500); pg.evaluate("closeDialogue()")
    pg.evaluate("PrologueProgress.seed(0);startAttackBattle('attackGob1',100)"); pg.wait_for_timeout(2600); pg.evaluate(TRACE)
    pg.evaluate("(()=>{const im=document.querySelector('#bGob img');BattleMotion.start(im,'tainted_goblin','ko')})()"); pg.wait_for_timeout(400)
    pg.evaluate("BattleMotion.stop(document.querySelector('#bGob img'))"); pg.wait_for_timeout(1600); s = pg.evaluate(SNAP)
    check(s['vis'] == 'visible' and s['gone'] is None and s['k']['end'] == [], 'stop() mid-dissolve leaves no stale timer: nothing hidden, no end event later')
    pg.evaluate("(()=>{const im=document.querySelector('#bGob img');BattleMotion.start(im,'tainted_goblin','ko')})()"); pg.wait_for_timeout(1500); s = pg.evaluate(SNAP)
    check(s['gone'] == '1' and s['vis'] == 'hidden', 'dissolve to completion hides the sprite')
    pg.evaluate("BattleActorState.begin('normal','enemy_0')"); pg.wait_for_timeout(300); s = pg.evaluate(SNAP)
    check(s['vis'] == 'visible' and s['gone'] is None and s['st'] == 'idle', 'next battle begin(): the hidden sprite is restored to idle (no resurrection bug, no stuck hidden)', s['st'])
    check(not errs, 'no page errors (restore flow)', errs[:2]); pg.close()
    # plain goblin actor (prepared adapter): motion machinery on a scratch image
    pg = b.new_page(viewport={'width': 1280, 'height': 720}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(base + '/index.html'); pg.wait_for_function('BattleMotion.loaded'); pg.wait_for_timeout(500)
    r = pg.evaluate("""()=>new Promise(res=>{const im=document.createElement('img');document.body.appendChild(im);const s=[];let l=0;const t0=performance.now();BattleMotion.start(im,'goblin','ko');
      (function f(){const n=+im.dataset.motionFrame;if(n&&n!==l){s.push(n);l=n}if(performance.now()-t0<1500)requestAnimationFrame(f);else res({s,vis:getComputedStyle(im).visibility,src:im.src.split('/').slice(-2).join('/')})})()})""")
    check(r['s'] == [1, 2, 3, 4, 5, 6] and r['vis'] == 'hidden', 'plain goblin: frames 1..6 then hidden', r)
    check(not errs, 'plain goblin: no page errors', errs[:2]); pg.close(); b.close()
print('FAILS', len(fails)); sys.exit(1 if fails else 0)

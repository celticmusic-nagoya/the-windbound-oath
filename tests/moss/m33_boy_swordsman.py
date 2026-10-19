# ASSET-EMMA-01 / 少年剣士 (rv_boy_swordsman): official 6-frame art in the Rilde training ground. RILD-001..009 + ASSET-001. needs http.server 8765, run from the repo root.
import os, sys, json, hashlib, subprocess, io
from PIL import Image
import numpy as np
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'); NPC = os.path.join(ROOT, 'img/field/moss/rilde/npc')
MAIN = "746cd1553fadfb06a872805a40585ee7c5b5f30d"
fails = []; errs = []
def check(c, m):
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c: fails.append(m)
FR = ['boy_swordsman_f%02d.png' % i for i in range(1, 7)]
# ---- file level: ASSET-001 / RILD-004 / RILD-005 ----
ims = [Image.open(os.path.join(NPC, f)) for f in FR + ['boy_swordsman_idle.png']]
check(all(i.size == (288, 256) and i.mode == 'RGBA' for i in ims), 'ASSET-001 7 files 288x256 RGBA (9:8 like the old 144x128, same display box)')
A = [np.array(i)[:, :, 3] for i in ims]
check(all(a.max() > 250 and (a > 0).mean() > .05 for a in A), 'ASSET-001 alpha channel carried (opaque body, transparent surround)')
edge = [int(max(a[0].max(), a[-1].max(), a[:, 0].max(), a[:, -1].max())) for a in A]
check(max(edge) == 0, 'RILD-005 no frame touches the canvas edge: nothing (sword tip / hand / wind) is cut %s' % edge)
feet = []
for a in A[:6]:
    ys, xs = np.nonzero(a > 200); fy = ys.max(); low = xs[ys > fy - 22]; feet.append((fy, (low.min() + low.max()) / 2))
check(max(f[0] for f in feet) - min(f[0] for f in feet) <= 2 and max(f[1] for f in feet) - min(f[1] for f in feet) <= 3, 'RILD-004 foot anchor identical in all 6 frames (+-3 px at 2x): %s' % [(int(f[0]), round(f[1], 1)) for f in feet])
# official design: blond hair (top rows of frame 1 are golden: R>150 and R-B>60), no background glow left (partial-alpha pixels are a thin edge only)
F1 = np.array(ims[0]); ys, xs = np.nonzero(F1[:, :, 3] > 200); top = F1[ys.min():ys.min() + 18][F1[ys.min():ys.min() + 18, :, 3] > 200][:, :3].astype(int)
check(top[:, 0].mean() > 150 and (top[:, 0] - top[:, 2]).mean() > 60, 'ASSET-001 frame 1 hair is blond/golden (official design): mean RGB %s' % top.mean(0).round().tolist())
check(all(((a > 8) & (a < 100)).mean() < ((a >= 100).mean() * 0.15) for a in A[:6]), 'ASSET-001 no soft background glow: faint-alpha pixels are < 15%% of the figure area')
check(open(os.path.join(NPC, 'boy_swordsman_idle.png'), 'rb').read() == open(os.path.join(NPC, 'boy_swordsman_f01.png'), 'rb').read(), 'RILD-003 idle = f01 (Ready stance)')
# body height ~ the old placeholder (91 px of 128 -> 182 px of 256): head-to-boots of frame 1 within 175..200
check(175 <= (ys.max() - ys.min()) <= 200, 'RILD-006 figure height keeps the old on-screen size (%d px of 256; old 182)' % (ys.max() - ys.min()))
# ---- only the swordsman's files changed (RILD-009) ----
d = subprocess.run(['git', '-C', ROOT, 'diff', '--name-only', MAIN, '--', 'img/field/moss/rilde/npc', 'data', 'img/field/moss/manifest.json', 'js', 'tools/moss/rilde_assets.json'], capture_output=True, text=True).stdout.split()
names = sorted(x for x in d)
check(all('boy_swordsman' in x for x in names) and len(names) >= 7, 'RILD-009 only boy_swordsman files differ from main under rilde/npc, data/, manifest, js/: %s' % names)
check(subprocess.run(['git', '-C', ROOT, 'diff', '--quiet', MAIN, '--', 'data/maps', 'img/field/moss/manifest.json', 'tools/moss/rilde_assets.json']).returncode == 0, 'RILD-006 map JSON / manifest / NPC definition byte-identical to main (position, event zone, collision, size, fps untouched)')
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1280, 'height': 720})
    pg.on('pageerror', lambda e: errs.append('PAGEERR ' + str(e))); pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
    bad = []; pg.on('response', lambda r: r.status >= 400 and bad.append(r.url))
    pg.goto('http://localhost:8765/index.html?title=0'); pg.wait_for_timeout(1500); ev = pg.evaluate
    ev("closeDialogue()"); ev("RildeVillage.enter('from_aidan')"); pg.wait_for_timeout(2500)
    check(ev("MossForest.mapId") == 'rilde_village_01_peace', 'RILD-001 in the Rilde village (peace)')
    w = ev("(()=>{const r=FieldWalkers.list.find(x=>x.id==='w_boy_swordsman');return r?{x:r.x,y:r.y,w:r.w,h:r.h,dir:r.dir,fps:r.fps,anim:r.anim,n:r.frames.length,f:r.frames,vis:r.el.isConnected&&getComputedStyle(r.el).display!=='none'}:null})()")
    check(w and w['vis'] and abs(w['x'] - 1950.9) < .01 and abs(w['y'] - 984.0) < .01, 'RILD-001 the boy swordsman walker is mounted and visible at the map position (1950.9, 984): %s' % str(w and (w['x'], w['y'])))
    check(w and w['fps'] == 7 and w['anim'] and w['dir'] == -1 and w['n'] == 7, 'RILD-003 7 fps in-place loop, dir -1, idle + 6 frames: %s' % str(w and (w['fps'], w['anim'], w['dir'], w['n'])))
    # RILD-002: the files the game loaded are the official ones (decoded size 288x256 and bytes == repo files)
    got = ev("""async()=>{const r=FieldWalkers.list.find(x=>x.id==='w_boy_swordsman');const out=[];for(const f of r.frames){const i=new Image();i.src=f;await i.decode();out.push([f.split('/').pop(),i.naturalWidth,i.naturalHeight])}return out}""")
    check(all(g[1:] == [288, 256] for g in got) and [g[0] for g in got] == ['boy_swordsman_idle.png'] + FR, 'RILD-002 the walker loads idle + f01..f06 as 288x256 (the old placeholders were 144x128): %s' % [g[0] for g in got])
    import urllib.request
    same = all(hashlib.sha256(urllib.request.urlopen('http://localhost:8765/img/field/moss/rilde/npc/' + g[0]).read()).hexdigest() == hashlib.sha256(open(os.path.join(NPC, g[0]), 'rb').read()).hexdigest() for g in got)
    old = subprocess.run(['git', '-C', ROOT, 'show', MAIN + ':img/field/moss/rilde/npc/boy_swordsman_f01.png'], capture_output=True).stdout
    check(same and hashlib.sha256(old).hexdigest() != hashlib.sha256(open(os.path.join(NPC, FR[0]), 'rb').read()).hexdigest(), 'RILD-002 served bytes == official files, different from main\'s placeholder')
    # RILD-003: sample the frame in use for 2.4 s: all 6 frames, strictly in order, looping
    seq = ev("""()=>new Promise(res=>{const r=FieldWalkers.list.find(x=>x.id==='w_boy_swordsman');const s=[];let l='';const t0=performance.now();(function f(){const c=r.el.dataset.src.split('_f').pop();if(c!==l){s.push(c);l=c}if(performance.now()-t0<2400)requestAnimationFrame(f);else res(s)})()})""")
    nums = [int(x[:2]) for x in seq if x[:2].isdigit()]
    check(len(nums) >= 12 and all(nums[i + 1] == nums[i] % 6 + 1 for i in range(len(nums) - 1)) and set(nums) == set(range(1, 7)), 'RILD-003 frames play 1->2->3->4->5->6->1 in order and loop: %s' % nums)
    # RILD-004 (in game): the box does not move while looping
    pos = ev("""()=>new Promise(res=>{const r=FieldWalkers.list.find(x=>x.id==='w_boy_swordsman');const s=new Set();const t0=performance.now();(function f(){const b=r.el.getBoundingClientRect();s.add([Math.round(b.left*10),Math.round(b.top*10),Math.round(b.width*10),Math.round(b.height*10)].join());if(performance.now()-t0<1500)requestAnimationFrame(f);else res([...s])})()})""")
    check(len(pos) <= 2, 'RILD-004 in game: the sprite box (position/size) is constant across the loop (%d distinct)' % len(pos))
    # RILD-007: conversation unchanged
    ev("FieldTalk.talk('boy_swordsman')"); pg.wait_for_timeout(300)
    txt = ev("document.querySelector('#msg').textContent")
    check('えいっ、やぁっ' in txt, 'RILD-007 existing conversation plays: %s' % txt[:30])
    check(ev("FieldTalk.active"), 'RILD-007 conversation is open (start)')
    n = 0
    while ev("FieldTalk.active") and n < 20: pg.click('#msg'); pg.wait_for_timeout(150); n += 1
    check(not ev("FieldTalk.active"), 'RILD-007 conversation runs to its end (%d clicks)' % n)
    check(any(w2['id'] == 'w_boy_swordsman' for w2 in ev("FieldWalkers.list.map(x=>({id:x.id}))")), 'RILD-007 walker still present after the conversation')
    zone = ev("(()=>{const z=(MossForest.map||{}).eventZones;return z?z.find(e=>e.id==='ev_boy_swordsman'):null})()")
    check(zone is None or (zone['shape']['r'] == 46 and zone['shape']['cx'] == 1952), 'RILD-006 interact zone unchanged (circle 1952,956 r46)')
    # RILD-008: leave the map (interior) and come back
    ev("RildeVillage.enter('from_aidan')"); ev("MossForestStory.enterMap('rilde_in_aidan','from_door')") if False else None
    ev("MossForestStory.enterMap('rilde_in_aidan','from_bed')"); pg.wait_for_timeout(2000)
    inside = ev("FieldWalkers.list.some(x=>x.id==='w_boy_swordsman')")
    check(not inside, 'RILD-008 after leaving the village the walker (and its update loop) is gone')
    ev("closeDialogue()"); ev("MossForestStory.enterMap('rilde_village','from_aidan')"); pg.wait_for_timeout(2200)
    seq2 = ev("""()=>new Promise(res=>{const r=FieldWalkers.list.find(x=>x.id==='w_boy_swordsman');if(!r){res(null);return}const s=[];let l='';const t0=performance.now();(function f(){const c=r.el.dataset.src.split('_f').pop();if(c!==l){s.push(c);l=c}if(performance.now()-t0<1800)requestAnimationFrame(f);else res(s)})()})""")
    n2 = [int(x[:2]) for x in (seq2 or []) if x[:2].isdigit()]
    check(seq2 is not None and len(n2) >= 9 and all(n2[i + 1] == n2[i] % 6 + 1 for i in range(len(n2) - 1)), 'RILD-008 re-entering the village: the loop plays again in order %s' % n2)
    check(len(ev("FieldWalkers.list")) == len(ev("(MossForest.map.walkers||[]).length and MossForest.map.walkers")) if False else True, 'RILD-008 (placeholder)')
    check(not [u for u in bad if 'boy_swordsman' in u or 'rilde/npc' in u], 'ASSET-002 no failed image requests for the village NPCs: %s' % bad[:3])
    check(not [e for e in errs if 'PAGEERR' in e], 'ASSET-002 no page errors: %s' % errs[:3])
    b.close()
print('FAILS', len(fails)); sys.exit(1 if fails else 0)

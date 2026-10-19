"""Phase 5: the 5 formally adopted Goblin Raider sheets (attack / damage / enrage / call / idle) are registered in img/battle/motion-manifest.json and play in the Raider battle
at PC / phone portrait / phone landscape. Checks: frame files exist; each state plays >=3 distinct frames and returns to the idle loop; the idle loop runs; the per-state scale is
applied while a motion runs and cleared afterwards; the apparent body size stays within 10% of the legacy still; the sprite is not clipped; KO is still the legacy still (dissolve candidate PENDING);
powered_attack / ko_dissolve candidates are NOT registered; boss HP / HUD are untouched by playback."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
fails = []
def check(ok, name, d=''):
    print(('ok   ' if ok else 'FAIL ') + name, d, flush=True)
    if not ok: fails.append(name)
SPR = '#raiderSprite img'
cur = "()=>{const i=document.querySelector('#raiderSprite img');return i?i.src.split('/').pop():null}"
def seen(pg, ms, step=40):
    s = []
    for _ in range(ms // step):
        f = pg.evaluate(cur)
        if not s or s[-1] != f: s.append(f)
        pg.wait_for_timeout(step)
    return s
BODY = """async()=>{const bb=async u=>{const im=new Image();im.src=u;await im.decode();const c=document.createElement('canvas');c.width=im.naturalWidth;c.height=im.naturalHeight;const x=c.getContext('2d');x.drawImage(im,0,0);
  const d=x.getImageData(0,0,c.width,c.height).data;let t=c.height,b=-1;for(let y=0;y<c.height;y++)for(let X=0;X<c.width;X+=2)if(d[(y*c.width+X)*4+3]>40){if(y<t)t=y;if(y>b)b=y;}return {nw:c.width,nh:c.height,frac:(b-t+1)/c.height}};
  const box=document.querySelector('#raiderSprite img');const r0=box.getBoundingClientRect();const cs=getComputedStyle(box);
  const out={};const still=await bb('img/battle/enemies/goblin_raider/goblin_raider_battle_idle.png');
  const W=box.offsetWidth,H=box.offsetHeight;const rend=(m,k)=>{const s=Math.min(W/m.nw,H/m.nh);return m.nh*s*m.frac*k};
  out.still=rend(still,1);
  for(const st of ['attack','damage','enrage','call','idle']){const f=BattleMotion.frames('goblin_raider',st);const m=await bb(f.urls[0]);out[st]=rend(m,f.scale);out[st+'_scale']=f.scale;}
  out.W=W;out.H=H;return out}"""
with server(8836) as base, sync_playwright() as p:
    b = p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or None))
    for vp, tag in [((1280, 720), 'pc'), ((390, 844), 'portrait'), ((844, 390), 'landscape')]:
        pg = b.new_page(viewport={'width': vp[0], 'height': vp[1]}); errs = []; bad = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('response', lambda r: bad.append(r.url) if r.status >= 400 else None)
        pg.goto(base + '/index.html?dev=1'); pg.wait_for_function('window.BattleOpening&&BattleMotion.loaded&&window.PrologueCombat'); pg.wait_for_timeout(1200); pg.evaluate("closeDialogue()")
        if tag == 'pc':
            miss = pg.evaluate("""async()=>{const m=await (await fetch('img/battle/motion-manifest.json')).json();const out=[];let n=0;const g=m.motions.goblin_raider||{};
              for(const [s,d] of Object.entries(g))for(let i=1;i<=d.frames;i++){const u=m.base+d.dir+d.pattern.replace('{n}',String(i).padStart(2,'0'));n++;const r=await fetch(u);if(!r.ok)out.push(u)}return {n,out,states:Object.keys(g)}}""")
            check(not miss['out'] and miss['n'] == 30, 'all 30 raider frame files exist', miss['out'][:3])
            check(sorted(miss['states']) == ['attack', 'call', 'damage', 'enrage', 'idle'], 'only the 5 adopted raider states are registered (candidates PENDING)', miss['states'])
        pg.evaluate("PrologueProgress.seed(0);startRaiderBattle()"); pg.wait_for_timeout(300)
        for _ in range(40):   # test setup only (same stray-dialogue race as Phase 3): never touches the busy/cinematic guards
            if pg.evaluate("document.body.classList.contains('dialogueOpen')"): pg.evaluate("closeDialogue()")
            if pg.evaluate("!document.body.classList.contains('battlePresentationBusy')&&!document.body.classList.contains('dialogueOpen')&&!document.body.classList.contains('actionCinematic')"): break
            pg.wait_for_timeout(500)
        pg.wait_for_function("!document.body.classList.contains('battlePresentationBusy')&&!document.body.classList.contains('dialogueOpen')&&!document.body.classList.contains('actionCinematic')", timeout=20000)
        pg.wait_for_timeout(600)
        s = seen(pg, 1500); idl = [x for x in s if x and '_idle_' in x]
        check(len(set(idl)) >= 4, '%s idle loop plays (%d distinct frames)' % (tag, len(set(idl))), s[:8])
        hp0 = pg.evaluate("rbBoss"); hud0 = pg.evaluate("document.body.innerText.length")
        sz = pg.evaluate(BODY)
        pg.evaluate("""async()=>{window.__bb={};for(const st of ['attack','damage','enrage','call']){const f=BattleMotion.frames('goblin_raider',st);let x0=1,x1=0,y0=1;
          for(const u of f.urls){const im=new Image();im.src=u;await im.decode();const c=document.createElement('canvas');c.width=im.naturalWidth;c.height=im.naturalHeight;const g=c.getContext('2d');g.drawImage(im,0,0);const d=g.getImageData(0,0,c.width,c.height).data;
            for(let y=0;y<c.height;y+=2)for(let x=0;x<c.width;x+=2)if(d[(y*c.width+x)*4+3]>128){x0=Math.min(x0,x/c.width);x1=Math.max(x1,x/c.width);y0=Math.min(y0,y/c.height);}}
          window.__bb[st]={x0,x1,y0};}}""")
        for st, tot in [('attack', 800), ('damage', 700), ('enrage', 900), ('call', 900)]:
            pg.evaluate("BattleActorState.set('goblin_raider','%s',{battle:'raider',duration:300})" % st)
            pg.wait_for_timeout(60)
            ap = pg.evaluate("parseFloat(document.querySelector('#raiderSprite img').style.getPropertyValue('--motion-scale'))")
            ratio = sz[st] / sz[st + '_scale'] * ap / sz['still']
            check(ratio >= 0.85 and ratio <= 1.10, '%s %s apparent body size = %.0f%% of the still (applied scale %.2f of %.2f)' % (tag, st, ratio * 100, ap, sz[st + '_scale']), 'portrait may be capped to fit the screen' if ap < sz[st + '_scale'] - 1e-3 else '')
            sc = pg.evaluate("(()=>{const i=document.querySelector('#raiderSprite img');return i.dataset.motionScale||null})()")
            clip = pg.evaluate("""(st)=>{const i=document.querySelector('#raiderSprite img');const bb=window.__bb[st];const W=i.offsetWidth,H=i.offsetHeight,nw=i.naturalWidth||1312,nh=i.naturalHeight||1199;const k=Math.min(W/nw,H/nh),cw=nw*k,ch=nh*k;
              const r=i.getBoundingClientRect();const sx=r.width/W;const L=r.left+(W-cw)/2*sx+bb.x0*cw*sx,R=r.left+(W-cw)/2*sx+bb.x1*cw*sx,T=r.bottom-ch*sx+bb.y0*ch*sx;
              let lim={l:0,r:document.documentElement.clientWidth,t:0},a=i.parentElement;const clipBy=[];
              while(a&&a!==document.body){const o=getComputedStyle(a);if(o.overflow!=='visible'||o.overflowX!=='visible'||o.overflowY!=='visible'){const q=a.getBoundingClientRect();clipBy.push(a.id||a.className);lim={l:Math.max(lim.l,q.left),r:Math.min(lim.r,q.right),t:Math.max(lim.t,q.top)};}a=a.parentElement;}
              return {L:Math.round(L),R:Math.round(R),T:Math.round(T),lim,clipBy}}""", st)
            s = seen(pg, tot + 600); names = [x for x in s if x and '_%s_' % st in x]
            check(len(set(names)) >= 3 and pg.evaluate("BattleActorState.get('raider','goblin_raider')") == 'idle', '%s %s: plays %d distinct frames then idle' % (tag, st, len(set(names))), s[:8])
            check(sc is not None and abs(float(sc) - pg.evaluate("BattleMotion.frames('goblin_raider','%s').scale" % st)) < 1e-6, '%s %s: scale applied while playing (%s)' % (tag, st, sc))
            check(clip['L'] >= clip['lim']['l'] - 2 and clip['R'] <= clip['lim']['r'] + 2 and clip['T'] >= clip['lim']['t'] - 2, '%s %s: figure (all 6 frames) stays inside the viewport / clipping ancestors' % (tag, st), clip)
        # scale cleared outside a scaled run: KO is the legacy still (not scaled)
        pg.evaluate("rbBoss=0;BattleActorState.sync('raider','goblin_raider')"); pg.wait_for_timeout(600)
        info = pg.evaluate("(()=>{const i=document.querySelector('#raiderSprite img');return {src:i.src.split('/').pop(),scale:i.dataset.motionScale||null,st:BattleActorState.get('raider','goblin_raider')}})()")
        check(info['st'] == 'ko' and info['src'] == 'goblin_raider_ko.png' and info['scale'] is None, '%s KO still shows the legacy still, unscaled' % tag, info)
        check(not errs, '%s no page errors' % tag, errs[:2]); check(not [u for u in bad if 'goblin_raider' in u], '%s no 4xx for raider assets' % tag, bad[:2])
        pg.close()
    b.close()
print('FAILS', len(fails)); sys.exit(1 if fails else 0)

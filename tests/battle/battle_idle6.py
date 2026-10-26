"""Aidan / Fiona 6-frame idle loops: asset sanity, per-frame durations, draw6->idle1 continuity, registration in normal+raider battles, state hand-off."""
import os,sys,re,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];fails=[];timing=[]
def check(ok,name,detail=''):
    print(('ok   ' if ok else 'FAIL ')+name,detail)
    if not ok:fails.append(name)
C=ROOT/'img/battle/characters'
def frames(d,pat):return [Image.open(C/d/(pat%i)).convert('RGBA') for i in range(1,7)]
sets={'aidan idle':frames('aidan/idle_v2','aidan_idle_%02d.png'),'fiona idle':frames('fiona/idle','fiona_idle_%02d.png'),'aidan draw':frames('aidan/motion','aidan_draw_%02d.png')}
for n,ims in sets.items():
    check(len(ims)==6 and len({i.size for i in ims})==1,n+': 6 frames, one canvas',ims[0].size)
    bot=[];edge=False;hidden=0;haze=[];fx=[]
    for im in ims:
        arr=np.array(im);a=arr[...,3];ys,xs=np.where(a>16);bot.append(int(ys.max()))
        edge|=bool(xs.min()<=0 or ys.min()<=0 or xs.max()>=im.width-1 or ys.max()>=im.height-1)
        hidden+=int((arr[a==0][:,:3]!=0).sum());haze.append(int(((a>0)&(a<6)).sum()));hi=np.where(a>=128);fx.append(float(hi[1][hi[0]>hi[0].max()-45].mean()))
    check(max(bot)-min(bot)<=2,n+': feet baseline unified',bot);check(not edge,n+': nothing touches canvas edge')
    check(hidden==0,n+': RGB zeroed under alpha 0');check(max(haze)<900 or n.startswith('fiona'),n+': no faint halo (fiona soft glow/hair exempt)',haze);check(max(fx)-min(fx)<=2.5,n+': feet centre stable',[round(x,1) for x in fx])
# fiona glow kept (frame 5 has green light, more than neighbours)
def green(im):
    a=np.array(im).astype(int);m=(a[...,3]>20)&(a[...,1]>a[...,0]+10)&(a[...,1]>a[...,2]+40);return int(m.sum())
g=[green(i) for i in sets['fiona idle']];check(g[4]==max(g) and g[4]>g[3]*1.3,'fiona frame5 green magic preserved',g)
# body height continuity: draw6 vs idle1 at display scale (158 box, width-limited)
def disp_h(im):
    a=np.array(im)[...,3];ys,xs=np.where(a>16);return (ys.max()-ys.min())*min(158/im.width,198/im.height)
r=disp_h(sets['aidan draw'][5])/disp_h(sets['aidan idle'][0]);check(abs(r-1)<=0.03,'aidan draw6 / idle1 display body height within 3%',round(r,3))
js=(ROOT/'js/assets.js').read_text()
check('ms:Object.freeze([220,180,220,160,110,260])' in js and 'ms:Object.freeze([260,220,240,180,300,260])' in js,'assets.js durations as specified')
check((ROOT/'img/battle/characters/aidan/idle/aidan_idle_00.png').exists() and 'aidan_breathe_v1' in js,'previous 4-frame idle kept as backup')
with server(8816) as base,sync_playwright() as p:
    b=p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None))
    pg=b.new_page(viewport={'width':1280,'height':720});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(base+'/index.html');pg.wait_for_function('window.BattleIdleMotion&&window.BattleActorState');pg.wait_for_timeout(1800)
    pg.evaluate("closeDialogue()");pg.wait_for_timeout(300)
    reg=pg.evaluate("BattleIdleMotion.status.actors.filter(a=>a.actor==='fiona'||a.actor==='aidan').map(a=>a.context+':'+a.actor)")
    check({'normal:fiona','raider:fiona','normal:aidan','raider:aidan'}<=set(reg),'idle loops registered for both actors in both battles',reg)
    for ctx,start,sel in (('normal','startAttackBattle("attackGob1",100)',{'aidan':'#bAidan2','fiona':'#bFiona2'}),('raider','startRaiderBattle()',{'aidan':'#rbAidan','fiona':'#rbFiona'})):
        if ctx=='raider':
            # Each encounter starts from a fresh page; nested battle entry is forbidden.
            pg.close();pg=b.new_page(viewport={'width':1280,'height':720});pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(base+'/index.html');pg.evaluate('closeDialogue()')
        check(pg.evaluate(start) is True,ctx+': battle entry committed')
        pg.wait_for_function("InputManager.state()==='BATTLE_COMMAND'")
        pg.wait_for_function("ctx=>{const actors=BattleIdleMotion.status.actors.filter(a=>a.context===ctx&&['aidan','fiona'].includes(a.actor));return actors.length===2&&actors.every(a=>a.showing)}",arg=ctx)
        # Pre-decode does not warm every canvas texture. Observe every delivered frame first.
        warm=pg.evaluate("""async ctx=>{const seen={aidan:new Set(),fiona:new Set()},t0=performance.now();
          return await new Promise(resolve=>{const tick=t=>{for(const a of BattleIdleMotion.status.actors)if(a.context===ctx&&seen[a.actor]&&a.showing)seen[a.actor].add(a.frame);
            if(Object.values(seen).every(s=>s.size===6)||t-t0>20000)resolve(Object.fromEntries(Object.entries(seen).map(([k,v])=>[k,[...v]])));else requestAnimationFrame(tick)};requestAnimationFrame(tick)})}""",ctx)
        check(all(sorted(v)==list(range(6)) for v in warm.values()),ctx+': all six idle canvas frames rendered before duration sampling',warm)
        res=pg.evaluate("""async(ctx)=>{const seen={aidan:[],fiona:[]},gaps=[],t0=performance.now();let last=t0;
          await new Promise(res=>{const tick=t=>{gaps.push(t-last);last=t;for(const a of BattleIdleMotion.status.actors)if(a.context===ctx&&seen[a.actor]&&a.showing){const s=seen[a.actor];if(!s.length||s[s.length-1].f!==a.frame)s.push({f:a.frame,t:t-t0})}
            if(t-t0<3600)requestAnimationFrame(tick);else res()};requestAnimationFrame(tick)});return {seen,gaps}}""",ctx)
        timing.append({'context':ctx,'samples':res});res=res['seen']
        if os.environ.get('QA_OUT'):(Path(os.environ['QA_OUT'])/'idle-timing.json').write_text(json.dumps(timing,indent=2))
        for who,want in (('aidan',[220,180,220,160,110,260]),('fiona',[260,220,240,180,300,260])):
            s=res[who];order=[x['f'] for x in s];ok=len(s)>=7 and all(order[i+1]==(order[i]+1)%6 for i in range(len(order)-1))
            check(ok,'%s %s: frames cycle 1..6 in order'%(ctx,who),order[:8])
            durs=[round(s[i+1]['t']-s[i]['t']) for i in range(1,len(s)-1)];exp=[want[x['f']] for x in s[1:-1]]   # first sample is a partial frame
            check(all(abs(d-e)<=45 for d,e in zip(durs,exp)),'%s %s: per-frame durations match (±45ms)'%(ctx,who),list(zip(durs,exp))[:7])
        # state hand-off: attack hides the idle canvas, return restores it
        pg.evaluate("BattleActorState.set('aidan','attack',{battle:%r,duration:500})"%ctx);pg.wait_for_timeout(120)
        mid=pg.evaluate("(()=>{const a=BattleIdleMotion.status.actors.find(a=>a.context===%r&&a.actor==='aidan');return a.showing})()"%ctx)
        pg.wait_for_timeout(1200)
        back=pg.evaluate("(()=>{const a=BattleIdleMotion.status.actors.find(a=>a.context===%r&&a.actor==='aidan');return a.showing})()"%ctx)
        check(mid is False and back is True,ctx+': attack hides idle canvas and idle resumes after',(mid,back))
        pg.evaluate("devJump&&0")
    check(not errs,'no page errors',errs[:3])
    pg2=b.new_page(viewport={'width':1280,'height':720});pg2.goto(base+'/dev/battle-idle-preview.html');pg2.wait_for_timeout(800)
    ok=pg2.evaluate("[...document.images].filter(i=>i.id&&(!i.complete||i.naturalWidth===0)).map(i=>i.id+':'+i.src)")
    check(ok==[],'dev preview page: all images load',ok);b.close()
print('FAILS',fails);sys.exit(1 if fails else 0)

# A3 seal gimmick test (dev harness, click-to-move). usage: seal_a3.py   (needs python3 -m http.server 8765 in repo root)
import sys
from playwright.sync_api import sync_playwright
URL='http://localhost:8765/dev/moss-forest.html?map=../data/maps/moss_forest_03_ancient_grove.json'
errs=[]; fails=[]
def check(c,msg):
    print(('ok   ' if c else 'FAIL ')+msg)
    if not c: fails.append(msg)
GO="""async ([x,y])=>{const sleep=ms=>new Promise(r=>setTimeout(r,ms));ForestDev.goFeet(x,y);
  if(!ForestDev.target)return {ok:false,why:'unreachable'};const t0=performance.now();
  while(ForestDev.target&&performance.now()-t0<120000)await sleep(100);
  return {ok:ForestDev.status.outcome==='arrived',why:ForestDev.status.outcome};}"""
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1920,'height':1080})
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto(URL); pg.wait_for_function('window.ForestDev&&ForestDev.frames>3',timeout=90000)
    def tp(x,y): pg.evaluate("([x,y])=>ForestDev.teleportFeet(x,y)",[x,y])
    def go(x,y): return pg.evaluate(GO,[x,y])
    def dom(): return pg.evaluate("document.querySelectorAll('#world *').length")
    M=pg.evaluate("ForestDev.map")
    paths={p['id']:p['points'] for p in M['terrain']['paths']}
    tre={t['id']:(t['x'],t['y']) for t in M['treasurePoints']}
    rest=[(z['id'],z['shape']) for z in M['eventZones'] if z['type']=='rest']
    # ---- closed
    check(pg.evaluate("ForestDev.flags.moss_a3_seal_open")==False,'seal starts closed'); check(pg.evaluate("ForestDev.sealNodes")==1,'seal visual present')
    tp(*paths['path_main'][0]); ok=True
    for pt in paths['path_main'][1:-1]:
        r=go(*pt); ok&=r['ok']
    check(ok,'closed: path_main reachable up to the throat')
    r=go(3900,3250); check(not r['ok'],'closed: inner point (3900,3250) not reachable (%s)'%r['why'])
    pos=pg.evaluate("ForestDev.pos"); check(pos['fy']>3289,'closed: stopped south of seal (fy=%d)'%pos['fy'])
    tp(3900,3300)
    for name in ['tr_a3_hollowlog']:
        r=go(*tre[name]); check(not r['ok'],'closed: %s unreachable'%name)
    # clip probe: walk keys-free hard push north through the seal rect
    tp(3910,3300); pg.evaluate("ForestDev.goFeet(3910,3200)"); pg.wait_for_timeout(1500)
    check(pg.evaluate("ForestDev.pos.fy")>3289,'closed: no wall clip pushing north (fy=%d)'%pg.evaluate("ForestDev.pos.fy"))
    # ---- open
    pg.evaluate("ForestDev.setFlag('moss_a3_seal_open',true)")
    check(pg.evaluate("ForestDev.sealNodes")==0,'open: seal visual removed')
    for pid,pts in paths.items():
        tp(*pts[0]); bad=[]
        for pt in pts[1:]:
            r=go(*pt)
            if not r['ok']: bad.append((pt,r['why']))
        check(not bad,'open: %s walked %s'%(pid,bad))
    for k,(x,y) in tre.items():
        tp(840,6490); r=go(x,y); check(r['ok'],'open: treasure %s reachable (%s)'%(k,r['why']))
    for k,sh in rest:
        tp(840,6490); r=go(sh['x']+sh['w']/2,sh['y']+sh['h']/2); check(r['ok'],'open: rest %s reachable (%s)'%(k,r['why']))
    tp(3900,3300); r=go(3900,3250); check(r['ok'],'open: passes the seal point')
    # ---- toggle stress
    d0=dom(); 
    for i in range(60):
        pg.evaluate("ForestDev.setFlag('moss_a3_seal_open',%s)"%('false' if i%2==0 else 'true'))
    pg.evaluate("ForestDev.setFlag('moss_a3_seal_open',true)"); pg.wait_for_timeout(300)
    d1=dom(); check(abs(d1-d0)<=40,'toggle x60: DOM nodes %d -> %d'%(d0,d1)); check(pg.evaluate("ForestDev.sealNodes")==0,'toggle: no seal node leak')
    pg.evaluate("ForestDev.setFlag('moss_a3_seal_open',false)"); tp(3910,3300); pg.evaluate("ForestDev.goFeet(3910,3200)"); pg.wait_for_timeout(1500)
    check(pg.evaluate("ForestDev.pos.fy")>3289,'re-closed: blocked again')
    # ---- symbol-driven open
    pg.goto(URL); pg.wait_for_function('window.ForestDev&&ForestDev.frames>3',timeout=90000)
    for i in range(3):
        sy=pg.evaluate("ForestDev.map.story.prologue.symbols[%d]"%i); tp(sy['x']-200,sy['y']); r=go(sy['x'],sy['y']); pg.wait_for_timeout(300)
        check(r['ok'],'symbol %d reached (%s)'%(i,r['why']))
    check(pg.evaluate("ForestDev.flags.moss_a3_seal_open"),'3 symbols defeated -> seal opens')
    # ---- budget
    tp(3900,3250); pg.wait_for_timeout(300)
    st=pg.evaluate("ForestDev.forest.cull.stats"); check(st['peak']<=800,'peak live nodes %d <= 800'%st['peak'])
print('errors',errs[:5]); 
sys.exit(1 if (fails or errs) else 0)

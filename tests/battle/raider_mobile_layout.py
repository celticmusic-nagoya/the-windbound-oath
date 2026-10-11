"""Real viewport geometry and touch regression, including Android browser chrome."""
import os,sys
from playwright.sync_api import sync_playwright
errors=[];http_errors=[];console_errors=[]
def check(ok,msg):
 print(('PASS ' if ok else 'FAIL ')+msg,flush=True)
 if not ok:raise AssertionError(msg)
def boxes(pg):
 return pg.evaluate('''()=>Object.fromEntries(['#rbAidan','#rbFiona','.rbNearA','.rbNearF','#rbLou','#raiderSprite','#rbEnemyHud','#raiderAdd1','#raiderAdd2'].map(s=>{const e=document.querySelector(s),r=e.getBoundingClientRect();return [s,{x:r.x,y:r.y,w:r.width,h:r.height}]}))''')
def inside(r,w,h):return r['x']>=-1 and r['y']>=-1 and r['x']+r['w']<=w+1 and r['y']+r['h']<=h+1
def overlap(a,b):return min(a['x']+a['w'],b['x']+b['w'])>max(a['x'],b['x'])+1 and min(a['y']+a['h'],b['y']+b['h'])>max(a['y'],b['y'])+1
with sync_playwright() as p:
 opts={};exe=os.environ.get('PW_CHROMIUM_EXECUTABLE')
 if exe:opts['executable_path']=exe
 b=p.chromium.launch(**opts)
 for w,h in [(360,640),(390,844),(844,390),(844,260),(1280,720),(1920,1080)]:
  ctx=b.new_context(viewport={'width':w,'height':h},has_touch=True,device_scale_factor=2)
  pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('response',lambda r:http_errors.append(r.url) if r.status>=400 else None);pg.on('console',lambda m:console_errors.append(m.text) if m.type=='error' else None)
  pg.goto('http://localhost:8765/index.html');pg.wait_for_timeout(2800);pg.evaluate('closeDialogue();startRaiderBattle();PrologueCombat.spawn();PrologueCombat.spawn();hideRaiderBattleLog()');pg.wait_for_timeout(300)
  r=boxes(pg);mobile=w<h or h<=520
  check(pg.evaluate('rbBoss===1250 && rbPhase()===1'),f'{w}x{h} boss HP/phase baseline')
  if mobile:
   check(all(inside(v,w,h) for v in r.values()),f'{w}x{h} actors/HUDs/add slots within viewport')
   check(not overlap(r['#raiderAdd1'],r['#raiderAdd2']),f'{w}x{h} reinforcements separated')
   for ally in ['#rbAidan','#rbFiona','.rbNearA','.rbNearF']:
    check(all(not overlap(r[ally],r[e]) for e in ['#raiderSprite','#raiderAdd1','#raiderAdd2']),f'{w}x{h} {ally} clear of enemies')
  if w==1280:
   check(abs(r['#raiderSprite']['w']-537.6)<1 and abs(r['#raiderSprite']['h']-504)<1,'PC giant boss dimensions unchanged')
  pg.locator('#rbCommandToggle').tap();check(pg.locator('#rbCmd').is_visible(),'COMMAND opens by touch');pg.locator('#rbCommandClose').tap();check(not pg.locator('#rbCmd').is_visible(),'COMMAND closes by touch')
  # Resizing a running battle must recompute inline HUD positions, not retain old offscreen ones.
  if mobile:
   nw,nh=(844,260) if w<h else (390,844);pg.set_viewport_size({'width':nw,'height':nh});pg.wait_for_timeout(300)
   check(all(inside(v,nw,nh) for v in boxes(pg).values()),'orientation change keeps layout in viewport')
   pg.set_viewport_size({'width':w,'height':h});pg.wait_for_timeout(300)
  pg.screenshot(path=f'/tmp/raider-layout-{w}-{h}.png')
  # Existing actions are executed through the battle flow (rather than a synthetic CSS class).
  if w==390:
   pg.evaluate("choosePartyAct('attack','raider_enemy_0');choosePartyAct('attack','raider_enemy_0')")
   pg.wait_for_function('!rbBusy && rbActor==="aidan"',timeout=30000)
   check(pg.evaluate('rbBoss<1250 && rbHP>0 && rbFHP>0'),'Aidan/Fiona attacks and enemy round complete')
   pg.evaluate("rbTP=50;choosePartyAct('skill','raider_enemy_0');choosePartyAct('guard',null)")
   pg.wait_for_function('!rbBusy && rbActor==="aidan"',timeout=30000)
   check(pg.evaluate('rbTP<50 && rbBoss>0'),'一閃 and guard complete')
  pg.evaluate("PrologueCombat.instantKill('raider')")
  pg.wait_for_timeout(3000)
  check(pg.evaluate('rbBoss===0'),'DEV kill sets boss KO')
  check('ko' in pg.locator('#raiderSprite img').get_attribute('src'),'boss KO artwork applied')
  check(pg.evaluate('document.body.classList.contains("battleResultMode")'),'Victory result shown')
  ctx.close()
 b.close()
check(not errors,'JS exceptions: '+str(errors));check(not http_errors,'HTTP errors: '+str(http_errors));check(not console_errors,'console errors: '+str(console_errors))

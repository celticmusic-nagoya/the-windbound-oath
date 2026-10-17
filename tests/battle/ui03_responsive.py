"""UI-03 geometry and operation checks; real DOM, all requested viewports."""
import sys,os,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
out=Path(os.environ.get('OUT','/tmp/ui03-responsive'));out.mkdir(parents=True,exist_ok=True)
fails=[];rows=[]
def check(ok,name):
 print(('ok ' if ok else 'FAIL ')+name,flush=True)
 if not ok:fails.append(name)
with server(8806) as base,sync_playwright() as p:
 b=p.chromium.launch()
 for w,h in [(360,640),(360,800),(390,844),(412,915),(800,360),(844,390),(915,412),(1280,720),(1920,1080)]:
  for mode in ['normal','raider']:
   name=f'{w}x{h}/{mode}';pg=b.new_page(viewport={'width':w,'height':h},has_touch=w<1024);errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(base+'/index.html?dev=1');pg.wait_for_function('BattleMotion.loaded&&window.BattleUIResponsive');pg.wait_for_timeout(1200)
   pg.evaluate('devJump("forest")' if mode=='normal' else 'devJump("raider")')
   if mode=='normal':pg.wait_for_function('MossForest.active');pg.wait_for_timeout(500);pg.evaluate('closeDialogue();FieldMonsters.removeAll();startAttackBattle("fieldGob3",100)')
   pg.wait_for_function('!BattlePresentation.busy&&'+('!attackBattleBusy' if mode=='normal' else '!rbBusy'))
   if mode=='raider':pg.evaluate('PrologueCombat.spawn()')
   pg.emulate_media(reduced_motion='reduce');pg.evaluate('BattleLouFlight.stop()');pg.wait_for_timeout(150)
   measurements=[];baseline=None
   for state in ['collapsed','commands','items','targets']:
    if state=='commands':pg.locator('#normalCommandToggle' if mode=='normal' else '#rbCommandToggle').click()
    if state=='items':pg.locator('#nItem' if mode=='normal' else '#rbItem').click()
    if state=='targets':pg.locator('[data-ni="potion"]' if mode=='normal' else '[data-ri="potion"]').click()
    pg.wait_for_timeout(100)
    if state=='targets':
     check(pg.evaluate('''()=>{const a=[...document.querySelectorAll('.ui3TargetSelected')];return a.length===1&&a[0].dataset.ui3TargetId===BattleTargetSelector.selected}'''),name+' target list matches one field actor')
     pg.keyboard.press('ArrowRight');pg.wait_for_timeout(100)
     check(pg.evaluate('''()=>{const a=[...document.querySelectorAll('.ui3TargetSelected')];return a.length===1&&a[0].dataset.ui3TargetId===BattleTargetSelector.selected}'''),name+' keyboard target change updates field marker')
    data=pg.evaluate('''b=>{const regions=BattleUIRegions.get(b),box=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}},field=box(regions.field),controls=box(regions.operations),log=box(regions.log);const overlap=(a,c)=>Math.max(0,Math.min(a.x+a.w,c.x+c.w)-Math.max(a.x,c.x))*Math.max(0,Math.min(a.y+a.h,c.y+c.h)-Math.max(a.y,c.y));const ids=b==='normal'?['bAidan2','bFiona2','bGob']:['rbAidan','rbFiona','raiderSprite'];const actors=ids.map(id=>({id,...box(document.getElementById(id))}));const buttons=[...regions.operations.querySelectorAll('button')].filter(e=>getComputedStyle(e).visibility==='visible'&&e.getBoundingClientRect().width&&e.getBoundingClientRect().height).map(e=>({id:e.id||e.textContent,...box(e)}));const huds=[...regions.field.querySelectorAll('.v2NearHud,.rbNearHud,.prologueEnemyHud,#rbEnemyHud')].filter(e=>getComputedStyle(e).display!=='none'&&getComputedStyle(e).visibility!=='hidden').map(box);return {field,controls,log,actors,huds,buttons,overlap:overlap(field,controls),state:BattleUIState.snapshot(b).status,horizontal:document.documentElement.scrollWidth>innerWidth,viewport:innerHeight,root:box(regions.root),view:box(BattleUIState.snapshot(b).status==='collapsed'?regions.command:BattleUIState.snapshot(b).status==='commands'?regions.actions:BattleUIState.snapshot(b).status==='items'?BattleUIRegions.items:BattleUIRegions.targets)}}''',mode)
    check(data['state']==state,name+'/'+state+' state')
    check(data['overlap']==0,name+'/'+state+' field/control no overlap')
    check(not data['horizontal'],name+'/'+state+' no horizontal page scroll')
    check(data['log']['y']+data['log']['h']<=data['view']['y']+.5,name+'/'+state+' log separate from operation view')
    check(data['root']['h']<=h+.5,name+'/'+state+' root fits viewport')
    check(all(x['w']>=44 and x['h']>=44 for x in data['buttons']),name+'/'+state+' 44px buttons')
    check(all(a['x']>=data['field']['x']-1 and a['y']>=data['field']['y']-1 and a['x']+a['w']<=data['field']['x']+data['field']['w']+1 and a['y']+a['h']<=data['field']['y']+data['field']['h']+1 for a in data['actors']),name+'/'+state+' major actor boxes inside field')
    check(all(a['x']>=data['field']['x']-1 and a['y']>=data['field']['y']-1 and a['x']+a['w']<=data['field']['x']+data['field']['w']+1 and a['y']+a['h']<=data['field']['y']+data['field']['h']+1 for a in data['huds']),name+'/'+state+' visible HUD boxes inside field')
    if mode=='raider' and w>=1280 and state=='collapsed':
     check(pg.evaluate('''()=>document.getElementById('rbLou').getBoundingClientRect().right+BattleLouFlight.tune.rangeX<=document.getElementById('raiderSprite').getBoundingClientRect().left-12'''),name+' Lou anchor reserves native flight range left of the large boss')
    if baseline:check(data['field']==baseline,name+'/'+state+' field stable')
    baseline=data['field'];measurements.append(data);pg.screenshot(path=str(out/f'{w}x{h}-{mode}-{state}.png'))
   pg.keyboard.press('Escape');pg.wait_for_timeout(50);check(not pg.locator('.ui3TargetSelected').count(),name+' cancel clears field target marker');check(pg.evaluate('BattleUIState.snapshot("'+mode+'").status==="items"'),name+' target cancel returns items')
   pg.locator('[data-ni="close"]' if mode=='normal' else '[data-ri="close"]').click();check(pg.evaluate('BattleUIState.snapshot("'+mode+'").status==="commands"'),name+' item return restores commands')
   pg.set_viewport_size({'width':h,'height':w});pg.wait_for_timeout(200);check(pg.evaluate('BattleUIState.snapshot("'+mode+'").status==="commands"'),name+' rotation retains commands')
   pg.set_viewport_size({'width':w,'height':h});pg.wait_for_timeout(150)
   # Test inset handling explicitly; emulator env(safe-area-inset-*) is otherwise zero.
   pg.evaluate('''b=>{const r=BattleUIRegions.get(b).root;r.style.setProperty('--battle-safe-top','20px');r.style.setProperty('--battle-safe-bottom','24px');r.style.setProperty('--battle-safe-left','12px');r.style.setProperty('--battle-safe-right','12px')}''',mode);pg.wait_for_timeout(150)
   check(pg.evaluate('''b=>{const r=BattleUIRegions.get(b),f=r.field.getBoundingClientRect(),c=r.operations.getBoundingClientRect();return Math.min(f.left,c.left)>=12&&Math.max(f.right,c.right)<=innerWidth-12&&Math.min(f.top,c.top)>=20&&Math.max(f.bottom,c.bottom)<=innerHeight-24+.5}''',mode),name+' simulated safe insets respected')
   pg.evaluate('''b=>{BattleUIRegions.get(b).operations.querySelectorAll('button').forEach(e=>e.style.setProperty('font-size','24px','important'))}''',mode)
   pg.locator('#nItem' if mode=='normal' else '#rbItem').click();pg.locator('[data-ni="close"]' if mode=='normal' else '[data-ri="close"]').click();check(pg.evaluate('BattleUIState.snapshot("'+mode+'").status==="commands"'),name+' enlarged button text remains scrollable and operable')
   check(not errors,name+' no page errors '+str(errors));rows.append(dict(size=[w,h],battle=mode,measurements=measurements,errors=errors));(out/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));pg.close()
 b.close()
print('FAILS',len(fails));sys.exit(bool(fails))

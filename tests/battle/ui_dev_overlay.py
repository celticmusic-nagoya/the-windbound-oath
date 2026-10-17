"""Real touch hit-testing for floating DEV controls, plus native battle exit/reset."""
import json, os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
out=Path(os.environ.get('OUT','/tmp/ui-dev-overlay'));out.mkdir(parents=True,exist_ok=True)
fails=[];rows=[]
def check(ok,name):
 print(('ok ' if ok else 'FAIL ')+name,flush=True)
 if not ok:fails.append(name)
def probe(pg,selector,name):
 el=pg.locator(selector);el.scroll_into_view_if_needed();box=el.bounding_box();assert box
 points=[(box['x']+x*box['width'],box['y']+y*box['height']) for x,y in [(0.05,0.1),(0.5,0.1),(0.95,0.1),(0.5,0.5),(0.05,0.9),(0.95,0.9)]]
 pg.evaluate('''selector=>{window.__tapHits=[];window.__tapProbe=e=>{const hit=e.target.closest(selector);__tapHits.push({ok:!!hit,target:e.target.id||e.target.tagName,type:e.type});e.preventDefault();e.stopImmediatePropagation()};window.__probeBlock=e=>{e.preventDefault();e.stopImmediatePropagation()};addEventListener('pointerdown',__tapProbe,true);addEventListener('click',__probeBlock,true)}''',selector)
 try:
  for x,y in points:pg.touchscreen.tap(x,y)
  hits=pg.evaluate('__tapHits');check(len(hits)==len(points)and all(x['ok'] for x in hits),name+' real pointerdown reaches intended control '+json.dumps(hits))
 finally:pg.evaluate("removeEventListener('pointerdown',__tapProbe,true);removeEventListener('click',__probeBlock,true)")
 return hits
with server(8808) as base,sync_playwright() as p:
 b=p.chromium.launch()
 for w,h in [(360,800),(390,844),(412,915),(800,360),(844,390),(915,412)]:
  for battle in ['normal','raider']:
   name=f'{w}x{h}/{battle}';pg=b.new_page(viewport={'width':w,'height':h},has_touch=True,is_mobile=True);errors=[];pg.on('pageerror',lambda e:errors.append(str(e)))
   pg.goto(base+'/index.html?dev=1');pg.wait_for_function('window.BattleUIState&&BattleMotion.loaded');pg.wait_for_timeout(1200)
   pg.evaluate('devJump("forest")');pg.wait_for_function('MossForest.active');pg.wait_for_timeout(350);pg.evaluate('closeDialogue();FieldMonsters.removeAll()')
   check(pg.is_visible('#devBtn'),name+' DEV visible before battle')
   # Existing field DEV panel is still reached by a real tap.
   pg.locator('#devBtn').tap();check(pg.is_visible('#devPanel'),name+' field DEV panel opens');pg.locator('#devClose').tap()
   pg.evaluate('startAttackBattle("fieldGob3",100)'if battle=='normal'else'startRaiderBattle()');pg.wait_for_function('BattleUIState.snapshot("'+battle+'").status==="collapsed"')
   if battle=='raider':pg.evaluate('PrologueCombat.spawn()')
   check(pg.evaluate('BattleLouFlight.running') if battle=='raider'else pg.evaluate("BattleIdleMotion.status.actors.some(x=>x.actor==='aidan'&&x.showing)"),name+' native flight/idle motion active')
   toggle='#normalCommandToggle'if battle=='normal'else'#rbCommandToggle';close='#normalCommandClose'if battle=='normal'else'#rbCommandClose';item='#nItem'if battle=='normal'else'#rbItem';potion='[data-ni="potion"]'if battle=='normal'else'[data-ri="potion"]';back='[data-ni="close"]'if battle=='normal'else'[data-ri="close"]';hits={}
   for state,selector in [('collapsed',toggle),('commands',close),('items',back),('targets','#battleTargetPanel button')]:
    if state=='commands':pg.locator(toggle).tap()
    if state=='items':pg.locator(item).tap()
    if state=='targets':pg.locator(potion).tap()
    check(pg.evaluate('BattleUIState.snapshot("'+battle+'").status')==state,name+'/'+state+' expected UI state')
    check(pg.is_hidden('#devBtn'),name+'/'+state+' DEV is hidden')
    hits[state]=probe(pg,selector,name+'/'+state)
    if state in ['collapsed','commands']:pg.screenshot(path=str(out/f'{w}x{h}-{battle}-{state}.png'))
   # Native touch cancellation and return (not a programmatic callback).
   try:pg.locator('#battleTargetPanel button').tap(timeout=1500)
   except Exception:check(False,name+' target cancel accepts real tap');pg.keyboard.press('Escape')
   check(pg.evaluate('BattleUIState.snapshot("'+battle+'").status==="items"'),name+' tap cancel returns items');pg.locator(back).tap();check(pg.evaluate('BattleUIState.snapshot("'+battle+'").status==="commands"'),name+' tap return restores commands')
   pg.set_viewport_size({'width':h,'height':w});pg.wait_for_timeout(180);check(pg.is_hidden('#devBtn'),name+' DEV hidden after rotation');probe(pg,close,name+'/rotation');pg.set_viewport_size({'width':w,'height':h});pg.wait_for_timeout(150)
   # Preserve the existing in-command QA kill route while hiding the floating menu.
   pg.locator('#nDevKill'if battle=='normal'else'#rbDevKill').tap();pg.wait_for_function('document.body.classList.contains("battleResultMode")',timeout=10000)
   check(pg.is_hidden('#devBtn'),name+' DEV stays hidden through RESULT');probe(pg,'#resultContinue',name+'/result');pg.locator('#resultContinue').tap();pg.wait_for_function('!document.body.classList.contains("battleMode")')
   check(pg.is_visible('#devBtn'),name+' DEV visibility restored on native battle exit');pg.locator('#devBtn').tap();check(pg.is_visible('#devPanel'),name+' restored DEV panel accepts tap');pg.locator('#devClose').tap()
   # Existing developmentMode gate must still hide DEV outside battle when OFF.
   pg.evaluate('document.body.classList.remove("developmentMode")');check(pg.is_hidden('#devBtn'),name+' DEV OFF remains hidden after battle');pg.evaluate('document.body.classList.add("developmentMode")');check(pg.is_visible('#devBtn'),name+' DEV ON restores existing field rule')
   pg.evaluate('devJump("forest");closeDialogue();FieldMonsters.removeAll();'+('startAttackBattle("fieldGob3",100)'if battle=='normal'else'startRaiderBattle()'));pg.wait_for_function('BattleUIState.snapshot("'+battle+'").status==="collapsed"');check(pg.is_hidden('#devBtn'),name+' repeated battle keeps DEV hidden')
   pg.evaluate('devJump("forest")');pg.wait_for_function('!document.body.classList.contains("battleMode")');check(pg.is_visible('#devBtn'),name+' DEV cancel/reset restores field rule');check(not errors,name+' no page errors '+str(errors));rows.append({'size':[w,h],'battle':battle,'hits':hits,'errors':errors});(out/'results.json').write_text(json.dumps({'rows':rows,'fails':fails},indent=2));pg.close()
 b.close()
print('FAILS',len(fails));sys.exit(bool(fails))

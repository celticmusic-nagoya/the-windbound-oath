import json,os,sys,hashlib,urllib.request,urllib.parse,subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path('/workspace/work/dev-walk01');O=R/'public-smoke';O.mkdir(exist_ok=True);proof=json.loads((R/'pages-proof.json').read_text());assert proof['pass'];commit=proof['main'];base=proof['url'];checks=[];errors=[]
def ck(name,value):
 checks.append({'name':name,'pass':bool(value)});print(('PASS ' if value else 'FAIL ')+name,flush=True);assert value,name
with sync_playwright() as pw:
 proxy_url=urllib.parse.urlsplit(os.environ['HTTPS_PROXY']);proxy={'server':f'{proxy_url.scheme}://{proxy_url.hostname}:{proxy_url.port}'}
 if proxy_url.username:proxy.update(username=urllib.parse.unquote(proxy_url.username),password=urllib.parse.unquote(proxy_url.password or ''))
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',proxy=proxy);ctx=b.new_context(viewport={'width':1920,'height':1080},has_touch=True);p=ctx.new_page();p.on('pageerror',lambda e:errors.append(str(e)));p.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);p.on('response',lambda r:errors.append(f'HTTP{r.status} {r.url}') if r.status>=400 else None);p.on('requestfailed',lambda r:errors.append(f'REQUEST {r.url} {r.failure}'))
 p.goto(base+'?title=1&qa='+commit,timeout=60000);p.get_by_role('button',name='NEW GAME',exact=True).click();p.wait_for_function("LoadCoordinator.phase==='READY'&&MossForest.active&&document.body.classList.contains('dialogueOpen')",timeout=60000)
 for _ in range(40):
  if p.evaluate("InputManager.state()!=='DIALOGUE'"):break
  p.keyboard.press('Enter');p.wait_for_timeout(80)
 p.wait_for_function("!MossForest.busy&&!LoadingInput.busy&&!document.body.classList.contains('dialogueOpen')")
 p.locator('#devBtn').click();p.locator('#devWalkMotionTest').tap();p.wait_for_function('DevWalkTest.active&&DevWalkTest.snapshot().ready')
 q=lambda s:p.locator('#walkMotionTest '+s)
 ck('public DEV entry',q('[data-walk=group] option').count()==3)
 ck('live catalog2/4/25',p.evaluate("['ally','enemy','npc'].map(g=>FieldWalkMotion.catalog(g).length)")==[2,4,25])
 q('[data-direction=left]').tap();p.wait_for_function("DevWalkTest.snapshot().direction==='left'&&DevWalkTest.snapshot().ready")
 ck('Aidan sixframes/production72',p.evaluate("FieldWalkMotion.resolve('ally','aidan','left').frames.length===6&&FieldWalkMotion.resolve('ally','aidan','left').stride===72&&MossForest.walkStride('aidan','left')===72") and '周期 72' in q('[data-walk=policy]').inner_text())
 ck('public adopted side6', '/side6/' in q('img').get_attribute('src'))
 q('[data-walk=group]').select_option('npc');q('[data-walk=actor]').select_option('soldier');q('[data-direction=right]').tap();p.wait_for_function("DevWalkTest.snapshot().actor==='soldier'&&DevWalkTest.snapshot().direction==='right'&&DevWalkTest.snapshot().ready")
 ck('public soldier sixv2',p.evaluate('DevWalkTest.snapshot().total')==6 and 'npc_soldier_walk_v2_' in q('img').get_attribute('src'))
 q('[data-direction=up]').tap();p.wait_for_function('DevWalkTest.snapshot().loaded&&!DevWalkTest.snapshot().ready')
 ck('missing direction honest',q('img').is_hidden() and q('img').get_attribute('src') is None and q('[data-walk=count]').inner_text()=='0 / 0')
 q('[data-walk=group]').select_option('enemy');q('[data-walk=actor]').select_option('goblin');q('[data-direction=down]').tap();p.wait_for_function("DevWalkTest.snapshot().actor==='goblin'&&DevWalkTest.snapshot().direction==='down'&&DevWalkTest.snapshot().ready")
 ck('public goblin down',p.evaluate('DevWalkTest.snapshot().total')==4 and 'goblin_walk_down_' in q('img').get_attribute('src'))
 for name,w,h in [('pc',1920,1080),('portrait',390,844),('landscape',844,390)]:
  p.set_viewport_size({'width':w,'height':h});p.wait_for_timeout(200);ck(name+' visible stage',q('.walkStage').is_visible());p.screenshot(path=str(O/(name+'.png')))
 q('[data-walk=play]').tap();p.wait_for_timeout(450);q('[data-walk=pause]').tap();ck('public loop/pause',not p.evaluate('DevWalkTest.snapshot().timer'))
 q('[data-walk=close]').tap();ck('public close/input release',p.evaluate('!DevWalkTest.active&&!document.body.classList.contains("devWalkOpen")'))
 ck('no console/Promise/HTTP/request errors',not errors);(O/'results.json').write_text(json.dumps({'main':commit,'checks':checks,'errors':errors,'physical_android':'NOT_RUN'},indent=2));ctx.close();b.close()

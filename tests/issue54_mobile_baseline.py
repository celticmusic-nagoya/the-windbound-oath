"""Compare the known mobile training MENU obstruction against the fixed baseline.
BASELINE_URL must serve an unmodified baseline checkout. No fixture file is changed.
"""
from pathlib import Path
import os,json
from playwright.sync_api import sync_playwright,TimeoutError
OUT=Path(os.environ['QA_OUT']);OUT.mkdir(parents=True,exist_ok=True);rows=[];errors=[]
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'))
 for name,url in [('baseline',os.environ.get('BASELINE_URL','http://127.0.0.1:8860/index.html')),('candidate',os.environ.get('QA_URL','http://127.0.0.1:8859/index.html'))]:
  c=b.new_context(viewport={'width':390,'height':844},has_touch=True,is_mobile=True);p=c.new_page();p.on('pageerror',lambda e:errors.append(str(e)));p.goto(url)
  p.wait_for_function("MossForest.active&&!MossForest.busy&&InputManager.state()==='DIALOGUE'")
  if name=='candidate':p.wait_for_function("LoadCoordinator.phase==='READY'")
  p.keyboard.press('Enter');p.evaluate('storyStage=1;startTraining();MossForest.lock(true)')
  reached=True
  try:p.locator('#menuOpen').tap(timeout=1500)
  except TimeoutError:reached=False
  p.screenshot(path=str(OUT/(name+'-mobile-training-menu.png')));rows.append({'source':name,'ordinary_MENU_reached':reached,'preparation':'runtime stage1/startTraining fixture; not normal progression'})
  c.close()
 assert rows[0]['ordinary_MENU_reached'] is False and rows[1]['ordinary_MENU_reached'] is False
 assert not errors
 (OUT/'comparison.json').write_text(json.dumps({'status':'PASS','meaning':'existing MENU obstruction is present in both baseline and candidate; not introduced or fixed by this patch','observations':rows,'pageerrors':errors},ensure_ascii=False,indent=2));print('PASS: baseline and candidate both obstruct mobile MENU during training')
 b.close()

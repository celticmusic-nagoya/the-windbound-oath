"""Keep legitimate ending routing and the legacy stage2 refusal contract."""
from pathlib import Path
import os,json
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];O=Path(os.environ['QA_OUT']);O.mkdir(parents=True,exist_ok=True);rows=[];errors=[]
def ck(n,ok,d=None):
 rows.append({'name':n,'status':'PASS' if ok else 'FAIL','detail':d});(O/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));print(n,rows[-1]['status'],flush=True);assert ok,n
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium');p=b.new_page();p.on('pageerror',lambda e:errors.append(str(e)));p.goto(os.environ.get('QA_URL','http://127.0.0.1:8859/index.html'));p.wait_for_function("LoadCoordinator.phase==='READY'");p.evaluate('TrainingCheckpoint.ready');p.keyboard.press('Enter')
 old=json.loads((R/'tests/fixtures/issue54-stage2.json').read_text());old['version']=29;old['prologue']['version']=1;old['prologue'].pop('moss');old['prologue']['position'].update(fpx=900,fpy=700);old['prologue']['forestChests']={'fChest1':False,'fChest2':False,'fChest3':False}
 p.evaluate('(d)=>{localStorage.setItem(SAVE_KEY,JSON.stringify(d));renderSystemTab("save")}',old);raw=p.evaluate('localStorage.getItem(SAVE_KEY)');ok=p.evaluate('loadGrowthData()');ck('legacy_v1_shape_refused_and_preserved',ok is False and raw==p.evaluate('localStorage.getItem(SAVE_KEY)') and '旧形式v1' in p.locator('#saveMsg').inner_text())
 late=json.loads((R/'tests/fixtures/issue54-stage15.json').read_text());late['prologue']['version']=1;late['prologue'].pop('moss');late['prologue']['storyStage']=14;p.evaluate('(d)=>{localStorage.setItem(SAVE_KEY,JSON.stringify(d));return loadGrowthData()}',late);p.wait_for_selector('#fortScene',state='visible')
 for _ in range(20):
  if p.locator('#prologueEnd').is_visible():break
  p.locator('#fortScene').click(position={'x':640,'y':350});p.wait_for_timeout(150)
 ck('legitimate_PROLOGUE_END_preserved',p.evaluate("storyStage===15&&getComputedStyle(document.querySelector('#prologueEnd')).display==='grid'&&!MossForest.active"));p.screenshot(path=str(O/'legitimate-ending.png'))
 data=p.evaluate('PrologueProgress.serialize()');ck('ending_not_saved_as_free_roam',data['moss']['map'] is None)
 end=json.loads((R/'tests/fixtures/issue54-stage15.json').read_text());end['prologue']=data;p.evaluate('(d)=>{localStorage.setItem(SAVE_KEY,JSON.stringify(d));return loadGrowthData()}',end);ck('null_map_ending_load_remains_ending',p.evaluate("storyStage===15&&!MossForest.active&&getComputedStyle(document.querySelector('#prologueEnd')).display==='grid'"));ck('ending_pageerrors',not errors,errors);b.close()

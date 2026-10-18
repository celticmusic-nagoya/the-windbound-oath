"""Shared real-browser setup for the two Phase 1.2 boundary suites."""
import os,sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/qa'))
from playwright.sync_api import sync_playwright
from browser_support import server
A='moss_forest_01_sunlit_path';B='moss_forest_02_mossy_ravine'
class Suite:
 def __init__(self,name):self.name=name;self.rows=[];self.fail=[];self.out=Path(os.environ.get('OUT','/tmp/'+name));self.out.mkdir(parents=True,exist_ok=True)
 def check(self,value,label):
  self.rows.append({'label':label,'pass':bool(value)});print(('PASS ' if value else 'FAIL ')+label,flush=True)
  if not value:self.fail.append(label)
 def run(self,cases,port):
  with server(port) as base,sync_playwright() as p:
   b=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_BIN','/usr/bin/chromium'),args=['--no-sandbox'])
   for name,fn in cases:
    if os.environ.get('CASE_FILTER') and name!=os.environ['CASE_FILTER']:continue
    c=b.new_context(viewport={'width':390,'height':844},has_touch=True);pg=c.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)))
    if os.environ.get('NEGATIVE_CONTROL'):
     for path in ['index.html','js/field/moss-forest-runtime.js','js/field/moss-forest-story.js','js/prologue-progress.js']:
      pg.route('**/'+path+'*',lambda r,_request,path=path:r.fulfill(path=str(ROOT.parent/'before-phase12'/path),content_type='text/html' if path.endswith('.html') else 'application/javascript'))
    try:
     pg.goto(base+'/index.html');pg.wait_for_function('window.MossForest?.active&&window.BattleMotion?.loaded',timeout=30000);pg.evaluate('closeDialogue()');fn(pg,self.check);self.check(not errors,name+' no uncaught errors '+str(errors))
    except Exception as e:self.check(False,name+' exception '+str(e))
    finally:c.close()
   b.close()
  (self.out/'results.json').write_text(json.dumps({'rows':self.rows,'fails':self.fail},ensure_ascii=False,indent=2));print('FAILS',len(self.fail));sys.exit(bool(self.fail))
def state(p):return p.evaluate('''()=>({active:MossForest.active,busy:MossForest.busy,unsafe:MossForest.unsafeCommit,save:MossForest.canSave,blocked:!!MossForest.restoreBlocked,map:MossForest.mapId,feet:MossForest.feet,request:MossForest.mapRequest,notice:document.querySelector('#notice')?.textContent})''')
def enter(p,m):return p.evaluate('m=>MossForest.enter({map:m}).then(x=>!!x)',m)
def fail_map(p):
 p.evaluate('window.baseLoader=ForestLoader;window.ForestLoader={...baseLoader,mount(){throw Error("controlled-midcommit")}}');enter(p,A);p.evaluate('window.ForestLoader=baseLoader')
def save(p):p.evaluate("renderSystemTab('save');saveGrowthData()")
def stored(p):return p.evaluate('localStorage.getItem(SAVE_KEY)')
def assert_stopped(p,ck,label):
 s=state(p);ck(not s['active'] and s['busy'] and s['unsafe'] and not s['save'],label+' latch/input/save blocked');old=stored(p);save(p);ck(stored(p)==old,label+' persistence unchanged')

"""26B: exact approved source delta, real production rewards, repeats, revisit and SAVE compatibility."""
import hashlib,json,os,subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];OUT=Path(os.environ['QA_OUT']).resolve();assert not OUT.is_relative_to(ROOT);OUT.mkdir(parents=True,exist_ok=True)
BASE='ad4a3d679987a540fc0248c9b5bfd0e8c43a15a3';fails=[];results=[];errors=[]
def ck(ok,name,detail=None):
 print(('ok   ' if ok else 'FAIL ')+name,'' if ok else detail,flush=True);results.append({'name':name,'pass':bool(ok),'detail':detail})
 if not ok:fails.append(name)
def original(file):return subprocess.check_output(['git','show',BASE+':'+file],cwd=ROOT,text=True)
def undo(text,before,after):
 assert text.count(before)==1,'approved delta missing/ambiguous: '+before
 return text.replace(before,after,1)
h=(ROOT/'index.html').read_text()
for before,after in [('Inventory.grant({potion:1});flags.drawer=true;','flags.drawer=true;'),('Inventory.grant({gold:3});flags.pot=true;','flags.pot=true;'),('Inventory.grant({antidote:2});flags.catDone=true;','flags.catDone=true;'),('Inventory.grant({potion:2});flags.balloonDone=true;','flags.balloonDone=true;'),("  // Missing optional item keys in an older SAVE mean zero, not the current session's stock.\n  if(!Object.prototype.hasOwnProperty.call(d.battleItems||{},'antidote'))delete battleItems.antidote;\n",''),('js/field/rilde-village.js?v=20261101rewards26b','js/field/rilde-village.js?v=20261031phase5expressions'),('js/data/item-data.js?v=20261101rewards26b','js/data/item-data.js')]:h=undo(h,before,after)
ck(h==original('index.html'),'exact index delta: only4grants/missing-item default/cache; every original word/condition unchanged')
r=(ROOT/'js/field/rilde-village.js').read_text()
for before,after in [('Inventory.grant({potion:1}); flags.drawer = true;','flags.drawer = true;'),('Inventory.grant({gold:3}); flags.pot = true;','flags.pot = true;'),("    if (typeof battleItems !== 'undefined') delete battleItems.antidote;\n",'')]:r=undo(r,before,after)
ck(r==original('js/field/rilde-village.js'),'exact field delta: only2grants/new optional stock reset')
d=undo((ROOT/'js/data/item-data.js').read_text(),"    antidote:      {name:'毒消し', kind:'consumable', desc:'現在は使用できない。'},\n",'');ck(d==original('js/data/item-data.js'),'only antidote holding definition added; existing item/treasure data immutable')
changes=subprocess.check_output(['git','diff','--name-only',BASE,'HEAD','--','index.html','js','css','data','img','assets','dev'],cwd=ROOT,text=True).splitlines();ck(set(changes)=={'index.html','js/data/item-data.js','js/field/rilde-village.js'},'all other production/portrait/battle/save-schema files unchanged',changes)
stock_js="({potion:Inventory.count('potion'),gold,antidote:Inventory.count('antidote')})"
flags_js='PrologueProgress.eventSnapshot()'
with sync_playwright() as pw:
 browser=pw.chromium.launch()
 def page(view,saved=None):
  w,h=view;c=browser.new_context(viewport={'width':w,'height':h},has_touch=True,is_mobile=w<1000)
  if saved:c.add_init_script('localStorage.setItem('+json.dumps(saved[0])+','+json.dumps(saved[1])+')')
  p=c.new_page();p.on('pageerror',lambda e:errors.append(str(e)));p.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
  p.goto('http://localhost:'+os.environ.get('PORT','8765')+'/index.html?title=1');p.get_by_role('button',name='CONTINUE' if saved else 'NEW GAME',exact=True).click();p.wait_for_function("LoadCoordinator.phase==='READY'&&MossForest.active&&!LoadingInput.busy")
  if not saved:p.wait_for_function("document.body.classList.contains('dialogueOpen')")
  return c,p
 for view in [(390,844),(844,390),(1920,1080)]:
  c,p=page(view);ev=p.evaluate;tag=str(view)
  def close():
   if p.locator('#msg').is_visible():p.locator('#msg').click()
  def hook(name):ev("h=>RildeVillage.hook({hook:'rilde_'+h},MossForest.map)",name);close()
  def legacy(name):
   ev("""id=>{room='home';document.querySelector('#inside').style.display='block';dressRoom();const el=document.getElementById(id),s=getComputedStyle(el);ipx=parseFloat(s.left);ipy=parseFloat(s.top);inCamera();if(!near(el))throw Error('legacy proximity fixture failed');el.onclick();document.querySelector('#inside').style.display='none';}""",name);close()
  def claim(n,old=False):
   if n in [0,1]:legacy(['drawer','pot'][n]) if old else hook(['drawer','pot'][n])
   elif n==2:hook('kid');hook('balloon_tree')
   else:hook('catowner');hook('cat');hook('catowner')
  def unchanged_repeats(expected):
   for i in range(4):claim(i)
   ck(ev(stock_js)==expected,tag+' completed event revisit grants nothing',ev(stock_js))
  close();initial=ev(stock_js);ck(initial=={'potion':4,'gold':0,'antidote':0},tag+' initial stock')
  hook('balloon_tree');hook('cat');ck(ev(stock_js)==initial and not ev('flags.balloonDone||flags.catFound'),tag+' no reward before acceptance')
  expected=dict(initial)
  for i,(item,amount,flag) in enumerate([('potion',1,'drawer'),('gold',3,'pot'),('potion',2,'balloonDone'),('antidote',2,'catDone')]):
   before=ev(stock_js);claim(i,old=view[0]==844);expected[item]+=amount;after=ev(stock_js);ck(after==expected and ev('f=>flags[f]',flag),tag+' R0'+str(i+1)+' exact reward delta and own flag',{'before':before,'after':after,'expected':expected.copy()});claim(i);ck(ev(stock_js)==expected,tag+' R0'+str(i+1)+' repeat delta0');
   if i<2:legacy(['drawer','pot'][i]);hook(['drawer','pot'][i]);ck(ev(stock_js)==expected,tag+' old/new house entry share the same once flag')
  ev("renderSystemTab('items')");ck('毒消し' in p.locator('#systemBody').inner_text() and '現在は使用できない' in p.locator('#systemBody').inner_text(),tag+' item UI lists held antidote without use/effect');ev("document.querySelector('#systemMenu').style.display='none'")
  ev('saveGrowthData()');key=ev('SAVE_KEY');raw=ev('localStorage.getItem(SAVE_KEY)');record=json.loads(raw);saved_flags=ev(flags_js);ck(record['version']==30 and record['battleItems']['antidote']==2 and record['prologue']['legacyEvents']['catDone'],tag+' existing v30 dictionary/flags store reward')
  ev('battleItems.potion=1;battleItems.antidote=9;gold=0');ck(ev('loadGrowthData()') is True,tag+' in-game LOAD succeeds');ck(ev(stock_js)==expected and ev(flags_js)==saved_flags and ev('localStorage.getItem(SAVE_KEY)')==raw,tag+' exact stock/flags restored without rewriting SAVE');unchanged_repeats(expected);c.close()
  c,p=page(view,(key,raw));ev=p.evaluate;close();ck(ev(stock_js)==expected and ev(flags_js)==saved_flags and ev('localStorage.getItem(SAVE_KEY)')==raw,tag+' cold title CONTINUE restores stock/once flags exactly');unchanged_repeats(expected)
  ev("MossForestStory.enterMap('rilde_village_01_peace','from_aidan')");p.wait_for_function('MossForest.active&&!MossForest.busy&&!LoadingInput.busy');ev("MossForestStory.enterMap('rilde_in_aidan','from_bed')");p.wait_for_function('MossForest.active&&!MossForest.busy&&!LoadingInput.busy');unchanged_repeats(expected)
  for history in ['explicit-done','old-missing-history']:
   old=json.loads(raw);old['battleItems'].pop('antidote',None);old['battleItems']['potion']=4;old['gold']=0
   if history=='old-missing-history':old['prologue'].pop('legacyEvents',None)
   oldraw=json.dumps(old,ensure_ascii=False);ev('r=>localStorage.setItem(SAVE_KEY,r)',oldraw);ev('battleItems.antidote=9');ck(ev('loadGrowthData()') is True,tag+' '+history+' LOAD succeeds');zero={'potion':4,'gold':0,'antidote':0};ck(ev(stock_js)==zero and ev('flags.catDone&&flags.balloonDone&&flags.drawer&&flags.pot'),tag+' '+history+' no compensation or completed-flag reset');unchanged_repeats(zero);ck(ev('localStorage.getItem(SAVE_KEY)')==oldraw,tag+' old SAVE bytes remain unchanged')
  ev('battleItems.antidote=9');ck(ev('TitleScreen.newGame(true)') is True,tag+' same-tab NEW GAME succeeds');ck(ev("Inventory.count('antidote')===0&&!flags.catDone") and ev('localStorage.getItem(SAVE_KEY)')==oldraw,tag+' new optional stock resets; existing SAVE untouched');c.close()
 browser.close()
ck(not errors,'no browser errors',errors)
(OUT/'early-rewards.json').write_text(json.dumps({'checks':results,'errors':errors,'fails':fails},ensure_ascii=False,indent=2)+'\n');print('FAILS',len(fails));raise SystemExit(bool(fails))

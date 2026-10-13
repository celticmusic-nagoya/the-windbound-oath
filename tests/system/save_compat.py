"""Historical save shapes and malformed data; keep failures visible."""
import copy,json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
OUT=Path('docs/qa/save-compat-20261013');OUT.mkdir(parents=True,exist_ok=True)
rows=[];errors=[];fixtures={}
SNAP="""(()=>({stage:storyStage,gold,battleItems,member:PartyManager.members.aidan,active:PartyManager.active,reserve:PartyManager.reserve,support:PartyManager.support,equipment:EquipmentManager.serialize(),inventory:Inventory.serialize(),quests:Quest.serialize(),talk:FieldTalk.serialize(),moss:MossForest.snapshot()}))()"""
def check(ok,name,detail=None):
 rows.append(dict(name=name,ok=bool(ok),detail=detail));print(('ok   ' if ok else 'FAIL ')+name,detail if detail is not None else '',flush=True)
with server(8832) as base,sync_playwright() as p:
 b=p.chromium.launch(**({'executable_path':os.environ.get('PW_CHROMIUM_EXECUTABLE','/usr/bin/chromium')} if os.environ.get('PW_CHROMIUM_EXECUTABLE') or Path('/usr/bin/chromium').exists() else {}));pg=b.new_page(viewport={'width':1000,'height':640});pg.on('pageerror',lambda e:errors.append(str(e)))
 def fresh():
  pg.goto(base+'/index.html');pg.wait_for_function('window.MossForest && MossForest.active && !MossForest.busy',timeout=30000);pg.wait_for_timeout(400);pg.evaluate('closeDialogue();renderSystemTab("save")')
 def load(data,raw=False):
  text=data if raw else json.dumps(data,ensure_ascii=False)
  result=pg.evaluate("s=>{localStorage.setItem(SAVE_KEY,s);return loadGrowthData()}",text)
  pg.wait_for_function('!MossForest.busy',timeout=30000);pg.wait_for_timeout(400)
  return result,pg.evaluate(SNAP)
 fresh();default=pg.evaluate(SNAP)
 pg.evaluate("enterMossForest()");pg.wait_for_function("MossForest.active && MossForest.mapId==='moss_forest_01_sunlit_path' && !MossForest.busy",timeout=30000);pg.wait_for_timeout(600);pg.evaluate("closeDialogue();PartyManager.members.aidan.level=4;PartyManager.members.aidan.exp=17;gold=321;battleItems.potion=7;Inventory.add('leather_cap');EquipmentManager.equip('aidan','leather_cap');Quest.accept('q_emma_charm');FieldTalk.setFlag('mm_marker',true);renderSystemTab('save');saveGrowthData()")
 canonical=json.loads(pg.evaluate('localStorage.getItem(SAVE_KEY)'))
 historical={28:'e0bd8d6',29:'8c0b0de',30:'fd79182'}
 for version in range(26,31):
  d=copy.deepcopy(canonical);d['version']=version
  if version<=28:
   for key in ['inventory','equipment','quests','talk','prologue']:d.pop(key,None)
  elif version==29:
   for key in ['inventory','equipment','quests','talk']:d.pop(key,None)
   d['prologue']['version']=1;d['prologue'].pop('moss',None);d['prologue']['forestChests']={'fChest1':False,'fChest2':True,'fChest3':False};d['prologue']['position'].update(fpx=40,fpy=100)
  fixtures['v'+str(version)]=dict(source=historical.get(version,'synthetic minimal old-version probe; historical serializer unavailable'),data=d)
  fresh();result,state=load(d);check(result,'v%s loads'%version,result)
  check(state['member']['level']==4 and state['gold']==321 and state['battleItems']['potion']==7,'v%s keeps growth/gold/items'%version)
  check(state['support']['joined'] is False,'v%s Lou flag preserved'%version)
  if version<=28:check(not state['quests'] and not state['talk']['flags'] and not state['inventory']['key'] and state['equipment']['state']['aidan'].get('weapon')=='father_sword','v%s missing fields default'%version)
  elif version==29:check(state['inventory']['key'].get('charm_windward')==1,'v29 legacy forestChests reconciles charm')
  else:
   check(state['equipment']['state']['aidan'].get('head')=='leather_cap' and state['quests'].get('q_emma_charm')=='active' and state['talk']['flags'].get('mm_marker') is True,'v30 equipment/quests/talk preserved')
   check(abs(state['moss']['x']-d['prologue']['moss']['x'])<=1 and abs(state['moss']['y']-d['prologue']['moss']['y'])<=1,'v30 plain-map position preserved',[state['moss'],d['prologue']['moss']])
  check(json.loads(pg.evaluate('localStorage.getItem(SAVE_KEY)'))==d,'v%s original not overwritten by load'%version)
  pg.evaluate('closeDialogue();renderSystemTab("save");saveGrowthData()');before=json.loads(pg.evaluate('localStorage.getItem(SAVE_KEY)'));load(before);pg.evaluate('closeDialogue();renderSystemTab("save");saveGrowthData()');after=json.loads(pg.evaluate('localStorage.getItem(SAVE_KEY)'))
  check(before==after and after['version']==30,'v%s -> v30 roundtrip equals normalized save'%version)
 fresh();d=copy.deepcopy(canonical);d['equipment']['state']['aidan'].update(weapon='wooden_sword',accessory='emma_charm');d['inventory']['gear']={'wooden_sword':2};fixtures['v30-single-accessory-wooden']=dict(source='equipment_test.py legacy fixture pattern',data=d);result,state=load(d);check(result and state['equipment']['state']['aidan'].get('weapon')=='father_sword' and state['equipment']['state']['aidan'].get('accessory1')=='emma_charm' and state['inventory']['gear'].get('father_sword')==2,'v30 wooden/single-accessory migration',state)
 # Malformed data, fresh page for each case. Unknown keys are ignored; wrong types must not poison live state.
 bad=[('broken-json','{broken',True),('null',None,False),('number-root',5,False),('array-root',[],False)]
 mutations=[('unknown-keys',lambda d:d.update(unknown={'x':1})),('bad-level',lambda d:d['members']['aidan'].update(level='bad')),('numeric-level',lambda d:d['members']['aidan'].update(level='4')),('negative-gold',lambda d:d.update(gold=-4)),('bad-potion',lambda d:d['battleItems'].update(potion='many')),('bad-support',lambda d:d['support'].update(joined='false')),('unknown-active',lambda d:d.update(active=['ghost'])),('bad-gold',lambda d:d.update(gold='bad'))]
 for name,fn in mutations:
  d=copy.deepcopy(canonical);fn(d);bad.append((name,d,False))
 for name,d,raw in bad:
  fresh();result,state=load(d,raw);fixtures[name]=dict(data=d,raw=raw);problems=[]
  if name in ['broken-json','null','number-root','array-root'] and (state['member']['level']!=default['member']['level'] or state['gold']!=default['gold'] or state['battleItems']!=default['battleItems'] or state['support']['joined'] is not False):problems.append('invalid root did not retain safe defaults')
  if not isinstance(state['member'].get('level'),(int,float)) or isinstance(state['member'].get('level'),bool) or not 1<=state['member']['level']<=50:problems.append('invalid member level retained')
  if not isinstance(state['gold'],(int,float)) or state['gold']<0:problems.append('invalid/negative gold retained')
  if not isinstance(state['battleItems'].get('potion'),int) or state['battleItems']['potion']<0:problems.append('invalid item count retained')
  if not isinstance(state['support'].get('joined'),bool):problems.append('non-boolean joined retained')
  if any(x not in canonical['members'] for x in state['active']):problems.append('unknown active member retained')
  check(not problems,'malformed '+name,dict(result=result,problems=problems,state=state))
 # Warm load omissions: load a marked state, then an old save missing those fields.
 fresh();d=copy.deepcopy(canonical);d['support']['joined']=True;load(d);legacy=copy.deepcopy(fixtures['v28']['data']);legacy.pop('support',None);legacy.pop('members',None);result,state=load(legacy)
 check(state['support']['joined'] is False and state['member']['level']==default['member']['level'],'missing fields warm-load defaults',state)
 # Height save (DEV map, no DEV jump). Record unsupported-map fallback separately.
 fresh();pg.evaluate("storyStage=9;MossForest.enter({map:'dev_height_proto',spawn:'deck',level:1})");pg.wait_for_function("MossForest.active && MossForest.mapId==='dev_height_proto' && !MossForest.busy",timeout=30000);pg.evaluate('closeDialogue();renderSystemTab("save");saveGrowthData()');d=json.loads(pg.evaluate('localStorage.getItem(SAVE_KEY)'));result,state=load(d)
 check(state['moss'].get('map')==d['prologue']['moss']['map'] and state['moss'].get('level')==1,'DEV height map/level roundtrip',dict(saved=d['prologue']['moss'],loaded=state['moss']))
 check(not errors,'uncaught page errors',errors);b.close()
(OUT/'fixtures.json').write_text(json.dumps(fixtures,ensure_ascii=False,indent=2));(OUT/'results.json').write_text(json.dumps(dict(introduced_base='f0fe968',source_head=os.getenv('QA_SOURCE_HEAD',os.getenv('GITHUB_SHA')),rows=rows,errors=errors),ensure_ascii=False,indent=2));n=sum(not r['ok'] for r in rows);print('FAILS',n);sys.exit(bool(n))

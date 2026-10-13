"""Lou gate through public story functions (no devJump), then malformed load paths."""
import copy,json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
OUT=Path('docs/qa/lou-story-gate-20261013');OUT.mkdir(parents=True,exist_ok=True)
rows=[];timeline=[];errors=[]
def check(ok,name,detail=None):
 rows.append(dict(name=name,ok=bool(ok),detail=detail));print(('ok   ' if ok else 'FAIL ')+name,detail or '',flush=True)
with server(8833) as base,sync_playwright() as p:
 b=p.chromium.launch(**({'executable_path':os.environ.get('PW_CHROMIUM_EXECUTABLE','/usr/bin/chromium')} if os.environ.get('PW_CHROMIUM_EXECUTABLE') or Path('/usr/bin/chromium').exists() else {}));pg=b.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True);pg.on('pageerror',lambda e:errors.append(str(e)))
 pg.goto(base+'/index.html');pg.wait_for_function('window.MossForest && MossForest.active && !MossForest.busy',timeout=30000);pg.wait_for_timeout(400);pg.evaluate('closeDialogue()')
 def snap(label):
  s=pg.evaluate("(()=>({stage:storyStage,joined:PartyManager.support.joined,map:MossForest.mapId,interior:!!MossForest.map?.story?.interior,battle:document.body.classList.contains('battleMode'),active:MossForest.active,classes:document.body.className}))()")
  im=pg.locator('#forestLou img:not([hidden])');s.update(label=label,visible=bool(im.count() and im.is_visible()));timeline.append(s);return s
 def map_enter(mid):
  pg.evaluate('id=>MossForest.enter({map:id})',mid);pg.wait_for_function('id=>MossForest.active&&!MossForest.busy&&MossForest.mapId===id',arg=mid,timeout=30000);pg.wait_for_timeout(300);pg.evaluate('closeDialogue();FieldMonsters.setFrozen(true)')
 s=snap('new-game');check(not s['joined'] and not s['visible'],'new game before rescue hidden',s)
 pg.evaluate('enterMossForest()');pg.wait_for_function("MossForest.active && MossForest.mapId==='moss_forest_01_sunlit_path' && !MossForest.busy",timeout=30000);pg.wait_for_timeout(600);pg.evaluate('closeDialogue();FieldMonsters.setFrozen(true)');s=snap('forest-entry');check(not s['visible'],'forest arrival before rescue hidden',s)
 map_enter('moss_forest_03_ancient_grove')
 for n in range(1,4):
  pg.evaluate('id=>PrologueProgress.defeat(id)','forestGob'+str(n));pg.wait_for_timeout(200);s=snap('corruption-'+str(n));check(not s['visible'],'corruption %s does not recruit Lou'%n,s)
 pg.evaluate('startLouIntro()');pg.wait_for_function("document.querySelector('#louIntroScene').style.display==='block'")
 while pg.locator('#louIntroScene').is_visible():pg.locator('#louIntroScene').click();pg.wait_for_timeout(30)
 pg.wait_for_timeout(300);s=snap('lou-intro-ended');check(s['stage']==11 and not s['joined'] and not s['visible'],'meeting Lou does not yet recruit field support',s)
 pg.evaluate('forestHideScene();startAltarScene()')
 for _ in range(pg.evaluate('altarLines.length')):pg.locator('#altarScene').click();pg.wait_for_timeout(30)
 pg.wait_for_function("document.body.classList.contains('raiderBattleMode')");s=snap('raider');check(not s['joined'] and not s['visible'],'altar and Raider not yet joined',s)
 pg.evaluate("PrologueCombat.instantKill('raider')");pg.wait_for_function("InputManager.state()==='RESULT'",timeout=30000);pg.locator('#resultContinue').click();pg.wait_for_timeout(200);s=snap('aftermath-start');check(s['stage']==13 and not s['joined'],'join waits for aftermath completion',s)
 while pg.locator('#aftermathScene').is_visible() and not pg.evaluate('PartyManager.support.joined'):pg.locator('#aftermathScene').click();pg.wait_for_timeout(30)
 s=snap('join-committed');check(s['stage']==14 and s['joined'] is True,'aftermath commits join exactly at stage14',s)
 pg.wait_for_function("document.querySelector('#fortScene').style.display==='block'",timeout=10000)
 while pg.locator('#fortScene').is_visible():pg.locator('#fortScene').click();pg.wait_for_timeout(30)
 pg.evaluate('RildeVillage.afterPrologue()');pg.wait_for_function("MossForest.active && !MossForest.busy && MossForest.mapId.startsWith('fort_')",timeout=30000);pg.wait_for_timeout(400);pg.evaluate('closeDialogue()');s=snap('free-roam');check(s['visible'] and s['joined'] is True,'post-story outdoor follower visible',s);pg.screenshot(path=str(OUT/'post-story.png'))
 pg.evaluate('renderSystemTab("save");saveGrowthData()');saved=json.loads(pg.evaluate('localStorage.getItem(SAVE_KEY)'));pg.evaluate('loadGrowthData()');pg.evaluate('RildeVillage.afterPrologue()');pg.wait_for_function('MossForest.active&&!MossForest.busy');pg.wait_for_timeout(400);s=snap('loaded-free-roam');check(s['visible'],'post-story load and public field reentry visible',s)
 map_enter('rilde_in_house_01');s=snap('interior');check(not s['visible'] and s['joined'],'interior suppresses joined follower',s)
 map_enter('road_dunvall_capital_01');pg.evaluate("startAttackBattle('fieldGob1',100)");s=snap('normal-battle');check(not s['visible'],'normal battle hides field follower',s);pg.evaluate("PrologueCombat.instantKill('normal')");pg.wait_for_function("InputManager.state()==='RESULT'",timeout=30000);pg.locator('#resultContinue').click();pg.wait_for_timeout(500);s=snap('normal-return');check(s['visible'],'battle return shows joined follower',s)
 # Edge paths: valid later state -> old early save with missing support; and wrong-type joined.
 fixture=json.loads(Path('docs/qa/save-compat-20261013/fixtures.json').read_text())['v29']['data'];early=copy.deepcopy(fixture);early.pop('support',None)
 pg.evaluate('s=>{localStorage.setItem(SAVE_KEY,JSON.stringify(s));loadGrowthData()}',early);pg.wait_for_function("MossForest.active&&!MossForest.busy&&MossForest.mapId==='moss_forest_01_sunlit_path'");pg.wait_for_timeout(500);pg.evaluate('closeDialogue()');s=snap('missing-support-early-load');check(not s['visible'],'missing support early save must not inherit recruited Lou',s);pg.screenshot(path=str(OUT/'early-missing-support.png'))
 early['support']={'id':'lou','joined':'false','fairyBlessing':1};pg.evaluate('s=>{localStorage.setItem(SAVE_KEY,JSON.stringify(s));loadGrowthData()}',early);pg.wait_for_function('!MossForest.busy');pg.wait_for_timeout(500);pg.evaluate('closeDialogue()');s=snap('string-false-early-load');check(not s['visible'],'string false joined must not display before rescue',s);pg.screenshot(path=str(OUT/'early-string-false.png'))
 check(not errors,'page errors',errors);b.close()
(OUT/'results.json').write_text(json.dumps(dict(introduced_base='f0fe968',source_head=os.getenv('QA_SOURCE_HEAD',os.getenv('GITHUB_SHA')),rows=rows,timeline=timeline,errors=errors,note='No devJump. Public progression calls, direct corruption victory registration, battle instantKill to exercise real finish callbacks; not full movement/combat playthrough.'),ensure_ascii=False,indent=2));n=sum(not x['ok'] for x in rows);print('FAILS',n);sys.exit(bool(n))

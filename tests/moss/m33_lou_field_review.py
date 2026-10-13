"""Lou follower review with original / proposal image routing; no asset adoption."""
import json,os,sys,subprocess,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
OUT=Path('docs/qa/lou-field-20261013');OUT.mkdir(parents=True,exist_ok=True)
_proposal_tmp=None
if os.getenv('LOU_PROPOSAL'):
    PROPOSAL=Path(os.environ['LOU_PROPOSAL'])
else:
    _proposal_tmp=tempfile.TemporaryDirectory(prefix='codex-lou-proposal-')
    PROPOSAL=Path(_proposal_tmp.name)
    subprocess.run([sys.executable,str(Path(__file__).resolve().parents[2]/'tools/field/make_lou_field_frames.py'),'--output',str(PROPOSAL)],check=True)
rows=[];measurements=[];errors=[]
def check(ok,name,detail=None):
    rows.append(dict(name=name,ok=bool(ok),detail=detail));print(('ok   ' if ok else 'FAIL ')+name,detail or '')
METER="""secs=>new Promise(resolve=>{let last=performance.now(),end=last+secs*1000,dt=[];function f(now){dt.push(now-last);last=now;if(now<end)requestAnimationFrame(f);else{dt.shift();dt.sort((a,b)=>a-b);resolve({n:dt.length,mean:dt.reduce((a,b)=>a+b,0)/dt.length,p99:dt[Math.floor(dt.length*.99)]})}}requestAnimationFrame(f)})"""
GEOM="""(()=>{let l=document.querySelector('#forestLou'),f=document.querySelector('#forestFiona'),a=document.querySelector('#forestPlayer'),im=[...l.querySelectorAll('img')].find(i=>!i.hidden);return {visible:getComputedStyle(l).display!=='none',left:parseFloat(l.style.left),top:parseFloat(l.style.top),lift:l.style.transform,fionaLift:f.style.transform,frame:[...l.querySelectorAll('img')].indexOf(im),rect:im?JSON.parse(JSON.stringify(im.getBoundingClientRect())):null,a:JSON.parse(JSON.stringify(a.getBoundingClientRect())),f:JSON.parse(JSON.stringify(f.getBoundingClientRect()))}})()"""
with server(8812) as base,sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE','/usr/bin/chromium'))
    for view,dims in [('pc',(1280,720)),('portrait',(390,844)),('landscape',(844,390))]:
        for variant in ['original','proposal','hidden']:
            context=b.new_context(viewport={'width':dims[0],'height':dims[1]},is_mobile=view!='pc',has_touch=view!='pc')
            if variant=='proposal':
                context.route('**/lou_idle_*.png*',lambda route:route.fulfill(path=str(PROPOSAL/Path(route.request.url.split('?')[0]).name),content_type='image/png'))
            pg=context.new_page();pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(base+'/index.html?feature=heightSpecs');pg.wait_for_function('window.MossForest && window.BATTLE_IDLE_ASSETS');pg.wait_for_timeout(1400)
            pg.evaluate("closeDialogue();storyStage=15;enterMossForest()");pg.wait_for_function('MossForest.active',timeout=30000);pg.evaluate('closeDialogue();MossForest.encounters(false);FieldMonsters.removeAll();PartyManager.support.joined=false');pg.wait_for_timeout(250)
            check(not pg.evaluate(GEOM)['visible'],view+'/'+variant+' hidden before join')
            pg.evaluate('PartyManager.support.joined=true');pg.wait_for_timeout(500);g=pg.evaluate(GEOM)
            check(g['visible'],view+'/'+variant+' visible after join')
            pg.wait_for_function("[...document.querySelectorAll('#forestLou img')].every(i=>i.complete&&i.naturalWidth)",timeout=20000)
            if variant=='original':
                timeline=pg.evaluate("""()=>new Promise(r=>{let out=[],end=performance.now()+1200;function f(n){let e=document.querySelector('#forestLou');out.push({t:n,x:parseFloat(e.style.left),y:parseFloat(e.style.top),frame:[...e.querySelectorAll('img')].findIndex(i=>!i.hidden)});if(n<end)requestAnimationFrame(f);else r(out)}requestAnimationFrame(f);FieldChoreo.moveTo(MossForest.actor('fiona'),{x:MossForest.feet.x+80,y:MossForest.feet.y+30},{ms:800}).then(()=>MossForest.actor('fiona').release())})""")
                check(len(set(x['frame'] for x in timeline))>=5,view+' field animation continues during choreography')
                measurements.append(dict(view=view,variant=variant,choreo=timeline))
                pg.screenshot(path=str(OUT/(view+'-follow.png')))
                pg.evaluate("MossForest.enter({map:'rilde_in_house_01'})");pg.wait_for_function("MossForest.active && MossForest.mapId==='rilde_in_house_01'",timeout=30000);pg.wait_for_timeout(350)
                check(not pg.evaluate(GEOM)['visible'],view+' hidden inside story.interior')
                pg.evaluate("MossForest.enter({map:'dev_height_proto',spawn:'deck',level:1})");pg.wait_for_function("MossForest.active && MossForest.mapId==='dev_height_proto'",timeout=30000);pg.evaluate('closeDialogue();FieldMonsters.removeAll()');pg.wait_for_timeout(1000);g=pg.evaluate(GEOM)
                check(g['lift']==g['fionaLift'],view+' Lou uses Fiona height lift',g)
                pg.screenshot(path=str(OUT/(view+'-height.png')))
                pg.evaluate("startAttackBattle('fieldGob1',100)");pg.wait_for_function("document.body.classList.contains('battleMode')");check(not pg.locator('#forestLou img:not([hidden])').is_visible(),view+' follower hidden during battle')
                pg.evaluate("PrologueCombat.instantKill('normal')");pg.wait_for_function("InputManager.state()==='RESULT'",timeout=30000);pg.locator('#resultContinue').click();pg.wait_for_timeout(800)
                check(pg.locator('#forestLou img:not([hidden])').is_visible(),view+' follower resumes after battle')
                pg.evaluate("closeDialogue();renderSystemTab('save');saveGrowthData();PartyManager.support.joined=false;loadGrowthData()");pg.wait_for_timeout(1000)
                check(pg.evaluate('PartyManager.support.joined') and pg.locator('#forestLou img:not([hidden])').is_visible(),view+' save/load restores follower')
            pg.evaluate("MossForest.enter({map:'moss_forest_02_mossy_ravine'})");pg.wait_for_function("MossForest.active && MossForest.mapId==='moss_forest_02_mossy_ravine'",timeout=30000);pg.evaluate("closeDialogue();FieldMonsters.removeAll();PartyManager.support.joined="+('false' if variant=='hidden' else 'true'));pg.wait_for_timeout(700);pg.evaluate('closeDialogue()')
            decode=[]
            for trial in range(3):
                decode.append(pg.evaluate("""async t=>{const start=performance.now();await Promise.all(BATTLE_IDLE_ASSETS.lou.frames.map(f=>{let im=new Image();im.src=f.path+'?qaDecode='+t;return im.decode()}));return performance.now()-start}""",trial))
            pg.evaluate('closeDialogue()');startFeet=pg.evaluate('MossForest.feet');pg.keyboard.down('ArrowRight');perf=pg.evaluate(METER,3);pg.keyboard.up('ArrowRight');endFeet=pg.evaluate('MossForest.feet');perf['displacement']=((endFeet['x']-startFeet['x'])**2+(endFeet['y']-startFeet['y'])**2)**.5
            measurements.append(dict(view=view,variant=variant,decodeAll6Ms=decode,raf=perf,geometry=pg.evaluate(GEOM)))
            context.close()
    check(not errors,'page errors',errors);b.close()
(OUT/'results.json').write_text(json.dumps(dict(base='31a5f5e',rows=rows,measurements=measurements,errors=errors,note='Cloud Chromium only; decode includes local HTTP load; proposal routed in browser only'),ensure_ascii=False,indent=2))
if _proposal_tmp:_proposal_tmp.cleanup()
n=sum(not r['ok'] for r in rows);print('FAILS',n);sys.exit(bool(n))

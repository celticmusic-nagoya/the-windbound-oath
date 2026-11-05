"""Repeated PC diagnosis on PR155 game inputs. Original criteria, no implementation overrides."""
import os,sys,json,subprocess,time,datetime,platform,hashlib
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/qa'));from browser_support import server
sys.path.insert(0,str(R/'tests/helpers'));from up07_probe import load_probe,criterion_contract
from up07_metrics import write_json
from walk_bootstrap_network import expected_retarget
O=Path(os.getenv('QA_OUT','/tmp/up07-diagnostics'));O.mkdir(parents=True,exist_ok=True);REF='0494f6452548ea476b4cebbc69d9f41d878d540d'
original=subprocess.check_output(['git','show',REF+':tests/moss/m67_up_production.py'],cwd=R,text=True);current=(R/'tests/moss/m67_up_production.py').read_text();assert criterion_contract(original)==criterion_contract(current),'Original predicate or measurement changed'
REC_N=int(os.getenv('UP07_RECORDED_TRIALS','5'));CTRL_N=int(os.getenv('UP07_UNRECORDED_TRIALS','3'));assert REC_N>=3 and CTRL_N>=1
records=[];unexpected=[];executed=[]
def check(name,passed):
 executed.append({'name':name,'pass':bool(passed)});print(('PASS ' if passed else 'FAIL ')+name,flush=True)
 if not passed:raise AssertionError(name)
P=load_probe(R,O,check);go,settle,stop=P['go'],P['settle'],P['stop'];baseline={'fixed_head':REF,'qa_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'original_test_sha256':hashlib.sha256(original.encode()).hexdigest(),'instrumented_test_sha256':hashlib.sha256(current.encode()).hexdigest(),'criteria_and_original_selectors_equal':True,'requested_trials':{'recorded':REC_N,'unrecorded':CTRL_N},'viewport':[960,540],'has_touch':True,'dpr':1,'expected_bank':['pushoff','03','04','01','06'],'period_world':90,'nominal_world_per_second':300,'python':platform.python_version(),'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text().strip() if Path('/sys/fs/cgroup/cpu.max').exists() else 'unavailable','memory_max':Path('/sys/fs/cgroup/memory.max').read_text().strip() if Path('/sys/fs/cgroup/memory.max').exists() else 'unavailable'};write_json(O/'condition.json',baseline)
# This observer only reads app getters/DOM. It never sets movement, frames, flags, HP or SAVE.
with server(8848) as base,sync_playwright() as pw:
 for recording,count in [(True,REC_N),(False,CTRL_N)]:
  for trial in range(1,count+1):
   label=('recorded' if recording else 'unrecorded')+f'-{trial:02}';T=O/label;T.mkdir(exist_ok=True);b=pw.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE') or '/usr/bin/chromium');cfg={'viewport':{'width':960,'height':540},'has_touch':True}
   if recording:cfg.update(record_video_dir=str(T/'video'),record_video_size={'width':960,'height':540})
   c=b.new_context(**cfg);p=c.new_page();bad=[];errors=[]
   p.on('pageerror',lambda e:errors.append(str(e)));p.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);p.on('response',lambda r:errors.append(f'HTTP{r.status} {r.url}') if r.status>=400 else None);p.on('requestfailed',lambda r:bad.append({'url':r.url,'failure':r.failure,'resource_type':r.resource_type,'before_dev':True}))
   try:
    p.goto(base+'/index.html?title=1');p.get_by_role('button',name='NEW GAME',exact=True).click();p.wait_for_function("LoadCoordinator.phase==='READY'&&MossForest.active&&document.body.classList.contains('dialogueOpen')")
    for _ in range(40):
     if p.evaluate("InputManager.state()!=='DIALOGUE'"):break
     p.keyboard.press('Enter');p.wait_for_timeout(80)
    p.wait_for_function("!MossForest.busy&&!LoadingInput.busy&&!document.body.classList.contains('dialogueOpen')");p.wait_for_function("[...document.querySelectorAll('.forest-aidan')].every(i=>i.complete&&i.naturalWidth>0)")
    if bad:
     replacement=p.evaluate("()=>{const i=document.querySelector('#raiderSprite img');return {url:i.currentSrc,loaded:i.complete&&i.naturalWidth>0,registered:BattleMotion.frames('goblin_raider','idle').urls.map(u=>new URL(u,location.href).href)}}")
     for event in bad:check(label+' exact startup retarget',expected_retarget(event,urljoin(base+'/','img/battle/enemies/goblin_raider/goblin_raider_battle_idle.png'),replacement))
     bad.clear()
    bank=p.evaluate("()=>{const d=FieldWalkMotion.ally('aidan','up');return {keys:d.frames.map(f=>f.key),stride:d.stride,bob:d.bobScale,speed:d.speed(),movement:FieldMovement.settings}}");check(label+' original approved bank',bank['keys']==['aidan_walk_up_pushoff','aidan_walk_up_03','aidan_walk_up_04','aidan_walk_up_01','aidan_walk_up_06'] and bank['stride']==90 and bank['bob']==.25 and bank['speed']==300)
    stable=p.evaluate(P['STABLE']);storage=p.evaluate('JSON.stringify({...localStorage})');check(label+' correct map and no comparison hook',p.evaluate("MossForest.mapId==='rilde_in_aidan'&&typeof QAUp06==='undefined'&&typeof DevUpWalkQA==='undefined'"))
    go(p,'ArrowDown','MossForest.feet.y>=370');go(p,'ArrowLeft','MossForest.feet.x<=250');go(p,'ArrowDown','MossForest.feet.y>=620')
    for route,keys in [('straight',['ArrowUp']),('ul',['ArrowUp','ArrowLeft']),('ur',['ArrowUp','ArrowRight'])]:
     if route!='straight':
      go(p,'ArrowDown','MossForest.feet.y>=370');go(p,'ArrowRight' if route=='ul' else 'ArrowLeft','MossForest.feet.x>=820' if route=='ul' else 'MossForest.feet.x<=130');go(p,'ArrowDown','MossForest.feet.y>=550')
     name=label+'/'+route;P['MEASURE_CONTEXT']={**baseline,'trial':trial,'recording':recording,'route':route,'input_keys':keys,'browser_version':b.version,'bank':bank,'preparation':'original m67 NEW GAME/house route and sequential key-down/up; no teleport','measurement_start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python_start_monotonic_ns':time.monotonic_ns()};p.evaluate(P['OBS'])
     for key in keys:p.keyboard.down(key)
     try:p.wait_for_function('MossForest.feet.y<=260',timeout=8000,polling='raf')
     finally:
      for key in keys:p.keyboard.up(key)
     rows=stop(p);P['MEASURE_CONTEXT']['python_end_monotonic_ns']=time.monotonic_ns();before=len(executed);failure=None
     try:P['field_check'](p,rows,name)
     except AssertionError as e:failure=str(e)
     path=O/'measurements'/name.replace('/','_');measurement=json.loads((path/'measurement.json').read_text())
     # Inspect collision candidates after sampling, without modifying coordinates or the hot loop.
     points=[{'x':r['x'],'y':r['y'],'heldKeys':r.get('heldKeys',[])} for r in rows]
     collision=p.evaluate("points=>points.map(p=>{const dx=(p.heldKeys.includes('ArrowRight')?1:0)-(p.heldKeys.includes('ArrowLeft')?1:0),dy=p.heldKeys.includes('ArrowUp')?-1:0,n=Math.hypot(dx,dy)||1;return {blockedHere:MossForest.blocked(p.x,p.y),blockedNominalNext:MossForest.blocked(p.x+dx/n*5,p.y+dy/n*5)}})",points);write_json(path/'collision-readback.json',collision)
     record={'label':name,'recording':recording,'trial':trial,'route':route,'original_check_calls':executed[before:],'first_failed_assertion':failure,'measurement_path':str(path.relative_to(O)),'cadence_pass':measurement['cadence_pass'],'median_world':measurement['measured']['median_cycle_world'],'median_seconds':measurement['measured']['median_cycle_seconds'],'raf_max_ms':measurement['raf_ms']['max'],'sampling_count':measurement['sampling_count'],'reason':measurement['cadence_reason'],'blocked_nominal_points':sum(q['blockedNominalNext'] for q in collision)};records.append(record);write_json(O/'results.json',{'condition':baseline,'records':records,'unexpected_errors':unexpected,'original_failure_deleted':False,'diagnostic_only_not_integration_qa':True});settle(p)
     check(name+' protected game and SAVE unchanged',p.evaluate(P['STABLE'])==stable and p.evaluate('JSON.stringify({...localStorage})')==storage and p.evaluate("[...document.querySelectorAll('.forest-aidan')].find(i=>!i.hidden).style.transform")=="");p.screenshot(path=str(T/f'pc-{route}-stopped.png'))
    if bad or errors:raise AssertionError({'request_failures':bad,'errors':errors})
   except Exception as e:
    unexpected.append({'trial':label,'error':str(e)});write_json(O/'unexpected.json',unexpected);raise
   finally:
    v=p.video if recording else None;c.close()
    if v:
     target=T/'production.webm';v.save_as(str(target))
     for f in (T/'video').glob('*.webm'):f.unlink() # save_as retained an exact copy; no failed measurement is removed.
    b.close()
assert len(records)==3*(REC_N+CTRL_N),'Incomplete diagnostic cohort'
write_json(O/'results.json',{'condition':baseline,'records':records,'unexpected_errors':unexpected,'original_failure_deleted':False,'diagnostic_only_not_integration_qa':True});print('DIAG_COMPLETE '+json.dumps({'measurements':len(records),'cadence_failures':sum(not r['cadence_pass'] for r in records),'original_assertion_failures':sum(bool(r['first_failed_assertion']) for r in records),'unexpected_errors':len(unexpected)}),flush=True)
# A complete investigation may legitimately contain FAIL; never disguise it as product PASS.
sys.exit(1 if unexpected or any(r['first_failed_assertion'] for r in records) else 0)

"""All map/default spawn smoke in four Lou/time-of-day states. No gameplay changes."""
import itertools,json,os,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/qa'))
from browser_support import server
from playwright.sync_api import sync_playwright
OUT=Path('docs/qa/all-maps-smoke-20261013');OUT.mkdir(parents=True,exist_ok=True)
maps=[json.loads(p.read_text()) for p in sorted(Path('data/maps').glob('*.json'))];ids={m['id'] for m in maps};rows=[];events=[];transitions=[];current={}
with server(8834) as base,sync_playwright() as p:
 b=p.chromium.launch(**({'executable_path':os.environ.get('PW_CHROMIUM_EXECUTABLE','/usr/bin/chromium')} if os.environ.get('PW_CHROMIUM_EXECUTABLE') or Path('/usr/bin/chromium').exists() else {}));pg=b.new_page(viewport={'width':1000,'height':640})
 pg.on('pageerror',lambda e:events.append(dict(kind='pageerror',text=str(e),context=dict(current))))
 pg.on('console',lambda e:events.append(dict(kind='console',text=e.text,location=e.location,context=dict(current))) if e.type=='error' else None)
 def fresh():
  pg.goto(base+'/index.html');pg.wait_for_function('window.MossForest && MossForest.active && !MossForest.busy',timeout=30000);pg.wait_for_timeout(400);pg.evaluate('closeDialogue();storyStage=15;MossForest.encounters(false);FieldMonsters.setFrozen(true)')
 fresh()
 for m in maps:
  for t in m.get('transitions',[]):
   target=t.get('toMap');resolved=pg.evaluate('id=>window.RildeVillage?RildeVillage.resolve(id):id',target)
   transitions.append(dict(map=m['id'],exit=t['id'],target=target,resolved=resolved,exists=resolved in ids,enabled=t.get('enabled',True),kind='file' if resolved in ids else 'TBD' if target=='TBD' else 'hook-owned legacy' if target=='lind_village' else 'missing'))
  for joined,tod in itertools.product([False,True],['day','night']):
   current=dict(map=m['id'],joined=joined,tod=tod);start_events=len(events);started=time.monotonic();problems=[];state=None
   try:
    pg.evaluate('j=>{closeDialogue();PartyManager.support.joined=j;FieldMonsters.setFrozen(true)}',joined)
    pg.evaluate('id=>MossForest.enter({map:id})',m['id']);load_ms=(time.monotonic()-started)*1000;pg.wait_for_function('id=>MossForest.active&&!MossForest.busy&&MossForest.mapId===id',arg=m['id'],timeout=30000)
    pg.evaluate('n=>{MossForest.setTimeOfDay(n,{instant:true});closeDialogue()}',tod);pg.wait_for_timeout(200)
    state=pg.evaluate("""(()=>{const feet=MossForest.feet,f=MossForest.actor('fiona').get(),l=document.querySelector('#forestLou'),im=l?[...l.querySelectorAll('img')].find(i=>!i.hidden):null;const visible=e=>{if(!e)return false;const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'};return {map:MossForest.mapId,tod:FieldTimeOfDay.current,feet,blocked:MossForest.blocked(feet.x,feet.y),interior:!!MossForest.map.story?.interior,fionaVisible:visible(document.querySelector('#forestFiona')),fionaDistance:Math.hypot(feet.x-f.x,feet.y-f.y),louVisible:visible(im),louDistance:l?Math.hypot(parseFloat(l.style.left)-feet.x,parseFloat(l.style.top)-feet.y):null,level:MossForest.snapshot().level,nodes:document.querySelectorAll('#forestWorld *').length}})()""")
    if state['blocked']:problems.append('default spawn blocked: map data/collision or level declaration')
    if state['tod']!=tod:problems.append('time of day not applied: code')
    if state['fionaVisible'] and state['fionaDistance']>300:problems.append('Fiona farther than300px: code/data')
    if state['louVisible'] and state['louDistance']>300:problems.append('Lou farther than300px: code/data')
    if state['louVisible'] != (joined and not state['interior']):problems.append('Lou visibility mismatch: code')
    if len(events)>start_events:problems.append('browser errors: inspect URL/message')
   except Exception as e:
    load_ms=(time.monotonic()-started)*1000;problems.append('exception: '+str(e).splitlines()[0])
   row=dict(**current,loadMs=round(load_ms,2),ok=not problems,problems=problems,state=state,events=events[start_events:]);rows.append(row);print(('ok   ' if row['ok'] else 'FAIL ')+m['id']+' '+str(joined)+' '+tod+' '+str(round(load_ms))+'ms '+str(problems),flush=True)
   (OUT/'results.json').write_text(json.dumps(dict(base='f0fe968',maps=len(maps),rows=rows,transitions=transitions,events=events,note='Default spawns only, desktop viewport, AI frozen, optional heightSpecs OFF; loads share browser cache'),ensure_ascii=False,indent=2))
   if any(x.startswith('exception:') for x in problems):fresh()
 b.close()
unresolved=[t for t in transitions if not t['exists']];n=sum(not r['ok'] for r in rows)+len(unresolved)
for t in unresolved:print('FAIL transition target '+json.dumps(t,ensure_ascii=False))
print('CASES',len(rows),'TRANSITION_UNRESOLVED',len(unresolved));print('FAILS',n);sys.exit(bool(n))

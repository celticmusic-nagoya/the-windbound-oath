"""Measure real mobile COMMAND geometry and sprite alpha coverage, proposal only."""
import json,os,sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from browser_support import server
from playwright.sync_api import sync_playwright
OUT=Path('docs/qa/command-initial-open-mobile-20261013');OUT.mkdir(parents=True,exist_ok=True)
MEASURE="""({kind,open})=>{
 const panel=document.querySelector(kind==='normal'?'#normalBattleCmd':'#rbCmd'),r=panel.getBoundingClientRect(),W=innerWidth,H=innerHeight;
 const roots=kind==='normal'?['#bAidan2','#bFiona2','#bGob','#normalEnemy1','#normalEnemy2']:['#rbAidan','#rbFiona','#rbLou','#raiderSprite'];
 const surface=document.createElement('canvas');surface.width=W;surface.height=H;const combined=surface.getContext('2d',{willReadFrequently:true});const actors=[],groups=[];
 const shown=e=>{let st=getComputedStyle(e),q=e.getBoundingClientRect();return st.display!=='none'&&st.visibility!=='hidden'&&parseFloat(st.opacity)>0&&q.width>0&&q.height>0};
 for(const sel of roots){const layer=document.createElement('canvas');layer.width=W;layer.height=H;const ctx=layer.getContext('2d',{willReadFrequently:true});const root=document.querySelector(sel);if(!root||!shown(root))continue;const nodes=[...root.querySelectorAll('img,canvas')].filter(shown);if(root.matches('img,canvas')&&shown(root))nodes.push(root);
  for(const el of nodes){const q=el.getBoundingClientRect();let x=q.x,y=q.y,w=q.width,h=q.height;
   if(el.tagName==='IMG'){if(!el.complete||!el.naturalWidth)continue;let fit=getComputedStyle(el).objectFit;if(fit==='contain'){let s=Math.min(w/el.naturalWidth,h/el.naturalHeight),nw=el.naturalWidth*s,nh=el.naturalHeight*s;x+=(w-nw)/2;y+=(h-nh)/2;w=nw;h=nh}}
   ctx.save();let matrix=getComputedStyle(el).transform;if(matrix.startsWith('matrix(')&&Number(matrix.slice(7).split(',')[0])<0){ctx.translate(x+w,y);ctx.scale(-1,1);ctx.drawImage(el,0,0,w,h)}else ctx.drawImage(el,x,y,w,h);ctx.restore();actors.push({selector:sel,tag:el.tagName,x,y,w,h});
  }
  const mask=ctx.getImageData(0,0,W,H).data;let count=0,overlap=0;for(let y=0;y<H;y++)for(let x=0;x<W;x++){if(mask[(y*W+x)*4+3]<64)continue;count++;if(open&&x>=r.left&&x<r.right&&y>=r.top&&y<r.bottom)overlap++}groups.push({selector:sel,pixels:count,coveredPixels:overlap,coveragePct:count?overlap/count*100:null});combined.drawImage(layer,0,0);
 }
 const pixels=combined.getImageData(0,0,W,H).data;let total=0,covered=0;for(let y=0;y<H;y++)for(let x=0;x<W;x++){if(pixels[(y*W+x)*4+3]<64)continue;total++;if(open&&x>=r.left&&x<r.right&&y>=r.top&&y<r.bottom)covered++}
 const rect=e=>{const q=e.getBoundingClientRect();return {x:q.x,y:q.y,w:q.width,h:q.height}};
 const stage=document.querySelector(kind==='normal'?'#attackBattle .v2BattleStage':'#raiderBattle #rbStage');
 const sr=stage?.getBoundingClientRect();
 const stagePanelIntersection=sr&&open?Math.max(0,Math.min(sr.right,r.right)-Math.max(sr.left,r.left))*Math.max(0,Math.min(sr.bottom,r.bottom)-Math.max(sr.top,r.top)):0;
 return {viewport:{w:W,h:H},stage:stage?rect(stage):null,huds:[...document.querySelectorAll(kind==='normal'?'#attackBattle .v2NearHud':'#raiderBattle .rbNearHud')].filter(shown).map(e=>({id:e.id||null,rect:rect(e),text:e.textContent.trim().slice(0,90)})),stagePanelOverlapPct:sr&&sr.width*sr.height?100*stagePanelIntersection/(sr.width*sr.height):null,panel:rect(panel),panelViewportPct:open?100*Math.max(0,Math.min(W,r.right)-Math.max(0,r.left))*Math.max(0,Math.min(H,r.bottom)-Math.max(0,r.top))/(W*H):0,spritePixels:total,spriteCoveredPixels:covered,spriteCoveragePct:total?covered/total*100:null,actors,groups,buttons:[...panel.querySelectorAll('button'),document.querySelector(kind==='normal'?'#normalCommandToggle':'#rbCommandToggle')].filter(e=>e&&shown(e)).map(e=>{let q=e.getBoundingClientRect(),limit=panel.contains(e)?r:{left:0,top:0,right:W,bottom:H},vw=Math.max(0,Math.min(W,limit.right,q.right)-Math.max(0,limit.left,q.left)),vh=Math.max(0,Math.min(H,limit.bottom,q.bottom)-Math.max(0,limit.top,q.top));return {id:e.id,label:e.textContent.trim(),...rect(e),minimum44:q.width>=44&&q.height>=44,visibleWidth:vw,visibleHeight:vh,visible44:vw>=44&&vh>=44}})};
}"""
rows=[];errors=[]
with server(8814) as base,sync_playwright() as p:
 b=p.chromium.launch(executable_path=(os.getenv('PW_CHROMIUM_EXECUTABLE') or (os.path.exists('/usr/bin/chromium') and '/usr/bin/chromium') or None))
 for view,(w,h) in [('portrait',(390,844)),('landscape',(844,390)),('landscape-small',(800,360)),('small',(360,640))]:
  for kind in ['normal','raider']:
   ctx=b.new_context(viewport={'width':w,'height':h},is_mobile=True,has_touch=True);pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto(base+'/index.html');pg.wait_for_function('window.InputManager && window.BattleIdleMotion');pg.wait_for_timeout(1300)
   if kind=='normal':
    pg.evaluate("devJump('forest')");pg.wait_for_function('MossForest.active',timeout=30000);pg.evaluate("closeDialogue();FieldMonsters.removeAll();startAttackBattle('fieldGob1',100)")
   else:pg.evaluate("closeDialogue();devJump('raider')")
   pg.wait_for_function("InputManager.state()==='BATTLE_COMMAND'",timeout=30000);pg.wait_for_timeout(3000)
   for expanded in [False,True]:
    if expanded:pg.locator('#normalCommandToggle' if kind=='normal' else '#rbCommandToggle').tap()
    else:pg.evaluate(('setNormalCommandDrawer' if kind=='normal' else 'setRaiderCommandDrawer')+'(false)')
    pg.wait_for_timeout(250);m=pg.evaluate(MEASURE,dict(kind=kind,open=expanded));m.update(view=view,kind=kind,expanded=expanded);rows.append(m);pg.screenshot(path=str(OUT/(view+'-'+kind+('-open' if expanded else '-closed')+'.png')))
    if expanded:
     # A scrollable drawer can legitimately start with commands below the fold.
     # Verify every rendered command can be brought fully into its scrollport.
     for button in m['buttons']:
      if button['id'] and not button['visible44']:
       reachable=pg.evaluate("""id=>{
        const el=document.getElementById(id),panel=el?.closest('#normalBattleCmd,#rbCmd');
        if(!el||!panel)return false;
        el.scrollIntoView({block:'nearest',inline:'nearest',behavior:'instant'});
        const a=el.getBoundingClientRect(),p=panel.getBoundingClientRect();
        return Math.min(a.right,p.right,innerWidth)-Math.max(a.left,p.left,0)>=44 &&
               Math.min(a.bottom,p.bottom,innerHeight)-Math.max(a.top,p.top,0)>=44;
       }""",button['id'])
       button['scrollReachable44']=reachable
   ctx.close()
 # UX-MOBILE-20: verify release preview hides development UI without changing battle controls.
 preview_checks=[]
 for kind in ('normal','raider'):
  ctx=b.new_context(viewport={'width':800,'height':360},is_mobile=True,has_touch=True)
  pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(str(e)))
  pg.goto(base+'/index.html?releasePreview=1')
  pg.wait_for_function('window.InputManager && window.BattleIdleMotion')
  pg.wait_for_timeout(1300)
  if kind=='normal':
   pg.evaluate("devJump('forest')");pg.wait_for_function('MossForest.active',timeout=30000)
   pg.evaluate("closeDialogue();FieldMonsters.removeAll();startAttackBattle('fieldGob1',100)")
  else:
   pg.evaluate("closeDialogue();devJump('raider')")
  pg.wait_for_function("InputManager.state()==='BATTLE_COMMAND'",timeout=30000)
  pg.locator('#normalCommandToggle' if kind=='normal' else '#rbCommandToggle').tap()
  pg.wait_for_timeout(250)
  check=pg.evaluate("""kind=>{
   const visible=id=>{const e=document.getElementById(id);return !!e&&!!e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden'};
   return {kind,previewEnabled:document.documentElement.classList.contains('release-ui-preview'),
    devMenuHidden:!visible('devBtn')&&!visible('devPanel'),
    devKillHidden:!visible(kind==='normal'?'nDevKill':'rbDevKill'),
    attackVisible:visible(kind==='normal'?'nAtk':'rbAtk')};
  }""",kind)
  preview_checks.append(check)
  pg.screenshot(path=str(OUT/('landscape-small-'+kind+'-release-preview.png')))
  ctx.close()
 b.close()
# UX-MOBILE-06: diagnostic occlusion review; not a gameplay failure.
for row in rows:
 row['occlusionThresholdPct'] = 20
 row['occlusionReview'] = ('REVIEW' if row['expanded'] and
  row['spriteCoveragePct'] is not None and row['spriteCoveragePct'] > 20 else 'OK')
# UX-MOBILE-08: protect the verified portrait improvement from regressions.
# Landscape is intentionally not gated until the dedicated split-stage layout exists.
portrait_budget = {'portrait': 30.0, 'small': 56.5}
failures = []
for row in rows:
 if row['expanded'] and row['kind'] == 'normal' and row['view'] in portrait_budget:
  pct = row['spriteCoveragePct']
  if pct is None or pct > portrait_budget[row['view']]:
   failures.append(f"{row['view']}/normal: sprite occlusion {pct}% exceeds {portrait_budget[row['view']]}% budget")
# UX-MOBILE-14: protect the verified landscape split against regressions.
# Per-actor budget catches hidden character loss masked by the aggregate.
for row in rows:
 if not (row['expanded'] and row['kind']=='normal' and row['view'] in ('landscape','landscape-small')):
  continue
 if row['stagePanelOverlapPct'] is None or row['stagePanelOverlapPct']>0.1:
  failures.append(f"{row['view']}/normal: stage overlaps command rail ({row['stagePanelOverlapPct']}%)")
 if row['spriteCoveragePct'] is None or row['spriteCoveragePct']>5.0:
  failures.append(f"{row['view']}/normal: sprite occlusion exceeds 5% ({row['spriteCoveragePct']}%)")
 for group in row['groups']:
  if group['coveragePct'] is not None and group['coveragePct']>10.0:
   failures.append(f"{row['view']}/normal: {group['selector']} occlusion exceeds 10% ({group['coveragePct']}%)")
# UX-MOBILE-16: prevent overlapping normal-battle HP labels in landscape.
for row in rows:
 if not (row['expanded'] and row['kind']=='normal' and row['view'] in ('landscape','landscape-small')):
  continue
 huds=[h for h in row.get('huds',[]) if h.get('id') in ('hudAidan','hudFiona','hudGob')]
 for i,a in enumerate(huds):
  for b in huds[i+1:]:
   x=max(0,min(a['rect']['x']+a['rect']['w'],b['rect']['x']+b['rect']['w'])-max(a['rect']['x'],b['rect']['x']))
   y=max(0,min(a['rect']['y']+a['rect']['h'],b['rect']['y']+b['rect']['h'])-max(a['rect']['y'],b['rect']['y']))
   if x*y>1:
    failures.append(f"{row['view']}/normal: HP labels {a['id']} and {b['id']} overlap ({x*y:.1f}px2)")
for row in rows:
 for button in row['buttons']:
  if not button['minimum44']:
   failures.append(f"{row['view']}/{row['kind']}/{row['expanded']}: {button['id']} tap target below 44 CSS px")
  if not button['visible44'] and not button.get('scrollReachable44',False):
   failures.append(f"{row['view']}/{row['kind']}/{row['expanded']}: {button['id']} visible target below 44 CSS px")
# UX-MOBILE-20: release preview must hide dev UI and retain normal attack commands.
for check in preview_checks:
 for key in ('previewEnabled','devMenuHidden','devKillHidden','attackVisible'):
  if not check[key]:
   failures.append(f"releasePreview/{check['kind']}: {key} is false")
# UX-MOBILE-18: explicit release-readiness audit, informational in development.
# Never silently treat the current development build as production-ready.
dev_controls = sorted({b['id'] for row in rows if row['expanded'] for b in row['buttons']
                       if b.get('id') in ('nDevKill','rbDevKill')})
release_audit = {'developmentCommandsVisible':dev_controls,
                 'productionReady':not bool(dev_controls),
                 'note':'Development commands are expected in this development build; block release until hidden or removed.'}
print('RELEASE_UI_AUDIT',json.dumps(release_audit,ensure_ascii=False))
try:
 baseline = subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
except (OSError,subprocess.CalledProcessError):
 baseline = os.getenv('QA_BASE_SHA','UNKNOWN')
(OUT/'results.json').write_text(json.dumps(dict(base=baseline,rows=rows,errors=errors,failures=failures,releaseAudit=release_audit,releasePreviewChecks=preview_checks,alphaThreshold=64,note='CSS-pixel alpha union of visible sprites; drawer rectangle overlap, translucent opacity ignored; cloud mobile emulation'),ensure_ascii=False,indent=2))
print(json.dumps([dict(view=x['view'],kind=x['kind'],expanded=x['expanded'],spritePct=x['spriteCoveragePct'],viewportPct=x['panelViewportPct'],stage=x['stage'],stagePanelOverlapPct=x['stagePanelOverlapPct']) for x in rows],indent=2));print('FAILURES',*failures,sep='\n');print('PAGE_ERRORS',*errors,sep='\n');sys.exit(bool(errors or failures))

"""Measure real mobile COMMAND geometry and sprite alpha coverage, proposal only."""
import json,os,sys
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
 return {viewport:{w:W,h:H},panel:rect(panel),panelViewportPct:open?100*Math.max(0,Math.min(W,r.right)-Math.max(0,r.left))*Math.max(0,Math.min(H,r.bottom)-Math.max(0,r.top))/(W*H):0,spritePixels:total,spriteCoveredPixels:covered,spriteCoveragePct:total?covered/total*100:null,actors,groups,buttons:[...panel.querySelectorAll('button'),document.querySelector(kind==='normal'?'#normalCommandToggle':'#rbCommandToggle')].filter(e=>e&&shown(e)).map(e=>{let q=e.getBoundingClientRect(),limit=panel.contains(e)?r:{left:0,top:0,right:W,bottom:H},vw=Math.max(0,Math.min(W,limit.right,q.right)-Math.max(0,limit.left,q.left)),vh=Math.max(0,Math.min(H,limit.bottom,q.bottom)-Math.max(0,limit.top,q.top));return {id:e.id,label:e.textContent.trim(),...rect(e),minimum44:q.width>=44&&q.height>=44,visibleWidth:vw,visibleHeight:vh,visible44:vw>=44&&vh>=44}})};
}"""
rows=[];errors=[]
with server(8814) as base,sync_playwright() as p:
 b=p.chromium.launch(executable_path=os.getenv('PW_CHROMIUM_EXECUTABLE','/usr/bin/chromium'))
 for view,(w,h) in [('portrait',(390,844)),('landscape',(844,390)),('small',(360,640))]:
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
   ctx.close()
 b.close()
(OUT/'results.json').write_text(json.dumps(dict(base='31a5f5e',rows=rows,errors=errors,alphaThreshold=64,note='CSS-pixel alpha union of visible sprites; drawer rectangle overlap, translucent opacity ignored; cloud mobile emulation'),ensure_ascii=False,indent=2))
print(json.dumps([dict(view=x['view'],kind=x['kind'],expanded=x['expanded'],spritePct=x['spriteCoveragePct'],viewportPct=x['panelViewportPct']) for x in rows],indent=2));print('FAILS',int(bool(errors)));sys.exit(bool(errors))

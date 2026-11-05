// CLS with shift sources, cold load + full scroll, several viewports/DPR.
const {chromium}=require('playwright');(async()=>{const u=process.argv[2];const delayRe=process.argv[3]?new RegExp(process.argv[3]):null;const delayMs=+(process.argv[4]||1200);const b=await chromium.launch();let worst=0;const out=[];
for(const [w,h,m] of [[1440,900,0],[1280,800,0],[1024,768,0],[844,390,1],[768,1024,1],[390,844,1],[360,640,1]])for(const dpr of [1,2,3]){
 const c=await b.newContext({viewport:{width:w,height:h},deviceScaleFactor:dpr,isMobile:!!m,hasTouch:!!m});const p=await c.newPage();await p.route(/fonts\.g/,r=>r.abort());if(delayRe)await p.route(delayRe,async r=>{await new Promise(x=>setTimeout(x,delayMs));await r.continue()});
 await p.addInitScript(()=>{window.__s=[];new PerformanceObserver(l=>{for(const e of l.getEntries())if(!e.hadRecentInput)window.__s.push({v:e.value,src:(e.sources||[]).map(s=>s.node?(s.node.className||s.node.nodeName)+'|'+(s.node.getAttribute&&s.node.getAttribute('alt')||''):'?')})}).observe({type:'layout-shift',buffered:true})});
 await p.goto(u);await p.waitForTimeout(1000+(delayRe?delayMs+800:0));
 await p.evaluate(async()=>{for(let y=0;y<document.body.scrollHeight;y+=200){scrollTo(0,y);await new Promise(r=>setTimeout(r,150))}});await p.waitForTimeout(1500);
 const s=await p.evaluate(()=>window.__s);const cls=s.reduce((a,x)=>a+x.v,0);worst=Math.max(worst,cls);
 out.push(`${w}x${h}@${dpr} CLS=${cls.toFixed(8)} ${s.map(x=>x.v.toFixed(6)+':'+x.src.join(',')).join(' ; ')}`);await c.close()}
console.log(out.join('\n'));console.log('WORST',worst.toFixed(8));await b.close()})();

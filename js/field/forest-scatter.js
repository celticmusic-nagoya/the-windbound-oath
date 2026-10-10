/* Deterministic scatter generation for Moss Forest maps (schema v2). Pure functions, no DOM.
 * Same map JSON + seeds => identical positions on every client. */
(function (root) {
  'use strict';
  function rng(seed){let a=seed>>>0;return function(){a=(a+0x6D2B79F5)>>>0;let t=a;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296;};}
  function segDist(px,py,a,b){const dx=b[0]-a[0],dy=b[1]-a[1],l2=dx*dx+dy*dy;
    const t=l2?Math.max(0,Math.min(1,((px-a[0])*dx+(py-a[1])*dy)/l2)):0;return Math.hypot(px-a[0]-t*dx,py-a[1]-t*dy);}
  function lineDist(px,py,pts){let d=Infinity;for(let i=0;i<pts.length-1;i++)d=Math.min(d,segDist(px,py,pts[i],pts[i+1]));return d;}
  function inPoly(px,py,poly){let c=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){
    const a=poly[i],b=poly[j];if((a[1]>py)!==(b[1]>py)&&px<(b[0]-a[0])*(py-a[1])/(b[1]-a[1])+a[0])c=!c;}return c;}
  const inRect=(px,py,r,m=0)=>px>=r.x-m&&px<=r.x+r.w+m&&py>=r.y-m&&py<=r.y+r.h+m;
  function bbox(poly){let x0=Infinity,y0=Infinity,x1=-Infinity,y1=-Infinity;for(const p of poly){x0=Math.min(x0,p[0]);y0=Math.min(y0,p[1]);x1=Math.max(x1,p[0]);y1=Math.max(y1,p[1]);}return {x:x0,y:y0,w:x1-x0,h:y1-y0};}
  // Region -> {box, test(x,y)}. Supports rect | patch | regions[] | ring | along.
  function region(map,r){
    if(r.regions){const parts=r.regions.map(q=>region(map,q));
      const u=parts.reduce((b,p)=>({x:Math.min(b.x,p.box.x),y:Math.min(b.y,p.box.y),x2:Math.max(b.x2,p.box.x+p.box.w),y2:Math.max(b.y2,p.box.y+p.box.h)}),{x:Infinity,y:Infinity,x2:-Infinity,y2:-Infinity});
      return {box:{x:u.x,y:u.y,w:u.x2-u.x,h:u.y2-u.y},test:(x,y)=>parts.some(p=>p.test(x,y))};}
    if(r.shape==='rect')return {box:r,test:(x,y)=>inRect(x,y,r)};
    if(r.shape==='patch'){const p=map.terrain.patches.find(q=>q.id===r.ref);if(!p)throw new Error('unknown patch '+r.ref);
      return {box:bbox(p.polygon),test:(x,y)=>inPoly(x,y,p.polygon)};}
    if(r.shape==='ring'){const o=r.outer,inner={x:o.x+r.inset,y:o.y+r.inset,w:o.w-2*r.inset,h:o.h-2*r.inset};
      return {box:o,test:(x,y)=>inRect(x,y,o)&&!inRect(x,y,inner)};}
    if(r.shape==='along'){const w=map.terrain.waters.find(q=>q.id===r.ref);if(!w)throw new Error('unknown water '+r.ref);
      const [lo,hi]=r.offset,half=(w.width||0)/2;
      return {box:bbox(w.points),test:(x,y)=>{const d=lineDist(x,y,w.points)-half;return d>=lo&&d<=hi;},boxPad:hi+half};}
    throw new Error('Unsupported scatter region: '+r.shape);
  }
  // Avoid predicate from the map: path_core[:+N] | water[:+N] | blockers | open:* | open:<id>
  function avoider(map,rules,presetRects){
    const paths=map.terrain.paths,waters=map.terrain.waters,opens=map.terrain.openAreas||[];
    const blockers=[];for(const b of map.collision.blockers)for(const r of b.rects)blockers.push({x:r[0],y:r[1],w:r[2],h:r[3]});
    const solid=presetRects||[];
    const parsed=rules.map(s=>{const [k,v]=s.split(':');return {k,v,m:v&&v[0]==='+'?Number(v.slice(1)):0};});
    return (x,y)=>{for(const a of parsed){
      if(a.k==='path_core'){for(const p of paths)if(lineDist(x,y,p.points)<p.width/2+a.m)return true;}
      else if(a.k==='water'){for(const w of waters){
        if(w.points){if(lineDist(x,y,w.points)<(w.width||0)/2+a.m)return true;}
        else if(w.polygon&&inPoly(x,y,w.polygon))return true;}}
      else if(a.k==='blockers'){for(const r of blockers)if(inRect(x,y,r,16))return true;for(const r of solid)if(inRect(x,y,r,16))return true;}
      else if(a.k==='open'){for(const o of opens)if((a.v==='*'||a.v===o.id)&&inRect(x,y,o,a.m))return true;}}
      return false;};
  }
  function generate(map){
    const out=[],propRects=[];
    // Props with collision presets repel scatter ('blockers').
    for(const p of map.props){const pr=map.collision.presets&&map.collision.presets[p.asset.replace(/_\d+$/,'')];if(!pr)continue;
      for(const r of pr)propRects.push({x:p.x+(p.flip?-r[0]-r[2]:r[0]),y:p.y+r[1],w:r[2],h:r[3]});}
    for(const rule of map.scatter){
      const rnd=rng(rule.seed),reg=region(map,rule.region),bad=avoider(map,rule.avoid||[],propRects);
      const cell=Math.max(8,rule.minDist),grid=new Map(),key=(i,j)=>i+','+j,placed=[];
      const pad=reg.boxPad||0,bx=reg.box,w=rule.weights,total=w?w.reduce((a,b)=>a+b,0):0;
      let tries=0;const limit=rule.count*60;
      while(placed.length<rule.count&&tries++<limit){
        const x=bx.x-pad+rnd()*(bx.w+2*pad),y=bx.y-pad+rnd()*(bx.h+2*pad);
        if(x<0||y<0||x>map.world.width||y>map.world.height)continue;
        if(!reg.test(x,y)||bad(x,y))continue;
        const gi=Math.floor(x/cell),gj=Math.floor(y/cell);let near=false;
        for(let i=gi-1;i<=gi+1&&!near;i++)for(let j=gj-1;j<=gj+1&&!near;j++)for(const q of grid.get(key(i,j))||[])if(Math.hypot(q.x-x,q.y-y)<rule.minDist){near=true;break;}
        if(near)continue;
        let pick=0;if(w){let t=rnd()*total;while(pick<w.length-1&&t>=w[pick]){t-=w[pick];pick++;}}else pick=Math.floor(rnd()*rule.pool.length);
        const e={rule:rule.id,asset:rule.pool[pick],x:Math.round(x*10)/10,y:Math.round(y*10)/10,flip:rnd()<.5,render:rule.render};
        placed.push(e);const k=key(gi,gj);if(!grid.has(k))grid.set(k,[]);grid.get(k).push(e);
      }
      for(const e of placed)out.push(e);
    }
    return out;
  }
  const api=Object.freeze({rng,generate,region,lineDist,inPoly});
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.ForestScatter=api;
})(typeof window!=='undefined'?window:globalThis);

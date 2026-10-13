/* Read-only QA: execute the production collision/height modules, never reimplement them. */
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const [root,id]=process.argv.slice(2),ctx={performance:require('node:perf_hooks').performance};ctx.window=ctx;vm.createContext(ctx);
for(const f of ['field-collision.js','field-height.js']) vm.runInContext(fs.readFileSync(path.join(root,'js/field',f),'utf8'),ctx);
const m=JSON.parse(fs.readFileSync(path.join(root,'data/maps',id+'.json'))),s=JSON.parse(fs.readFileSync(path.join(root,'data/height-specs',id+'.json'))),checks=[],warnings=[];
const ck=(ok,label,detail)=>checks.push({ok:!!ok,label,detail}),finite=n=>typeof n==='number'&&Number.isFinite(n),level=n=>Number.isInteger(n)&&n>=0,known=n=>level(n)&&(n===0||Object.hasOwn(s.levels||{},String(n)));
const rect=r=>Array.isArray(r)&&r.length===4&&r.every(finite)&&r[0]>=0&&r[1]>=0&&r[2]>0&&r[3]>0&&r[0]+r[2]<=m.world.width&&r[1]+r[3]<=m.world.height;
ck(finite(s.levelHeight)&&s.levelHeight>0,'positive levelHeight');
for(const [k,v] of Object.entries(s.levels||{})){ck(level(Number(k))&&String(Number(k))===k,'level key '+k);ck(Array.isArray(v.walk)&&v.walk.length>0,'walk list '+k);for(const [i,r]of(v.walk||[]).entries())ck(rect(r),'walk rect '+k+'/'+i);}
const ids=new Set();for(const c of s.connectors||[]){ck(!ids.has(c.id)&&typeof c.id==='string','unique connector '+c.id);ids.add(c.id);ck(rect(c.rect)&&['x','y'].includes(c.axis)&&['min','max'].includes(c.fromEnd)&&known(c.from)&&known(c.to)&&c.from!==c.to&&finite(c.zone??.22)&&(c.zone??.22)>0&&(c.zone??.22)<.5,'connector schema '+c.id);}
for(const d of s.overpasses||[])ck(rect(d.rect)&&known(d.level)&&d.level>0,'overpass '+d.id);
if(checks.some(c=>!c.ok)){console.log(JSON.stringify({map:id,checks,warnings}));process.exit(0)}
const blockers=[...(m.collision?.edgeBlockers||[]),...(m.collision?.blockers||[])],names=[...new Set(blockers.filter(b=>b.enabledWhen).map(b=>b.enabledWhen.flag))];
if(names.length>10)throw Error('Too many conditional blocker combinations');
const contexts=Array.from({length:2**names.length},(_,n)=>{const flags=Object.fromEntries(names.map((k,i)=>[k,!!(n&(1<<i))]));const solid=ctx.FieldCollision.compileMap(blockers,k=>flags[k]);return{flags,solid,h:ctx.FieldHeight.create(s,solid)}});
const B=ctx.FieldCollision.footprint;ck(B.width===22&&B.height===10,'production 22x10 footprint');
const at=(h,x,y,l)=>!h.blockedAtLevel(x-B.anchorX,y-B.anchorY,l);
for(const {h,flags}of contexts){
 for(const c of s.connectors||[]){const [x,y,w,ht]=c.rect,a=c.axis==='x',zone=c.zone??.22;
  for(const [end,l]of [[0,c.from],[1,c.to]]){const t=c.fromEnd==='max'?1-(end?1-zone/2:zone/2):(end?1-zone/2:zone/2),fx=a?x+w*t:x+w/2,fy=a?y+ht/2:y+ht*t;
   ck(at(h,fx,fy,l)&&h.levelAt(fx-B.anchorX,fy-B.anchorY,l)===l,'connector end '+c.id+'/'+l,{feet:[fx,fy],flags});
   const upper=(c.fromEnd==='max'?1-end:end),ox=a?x+(upper?w+12:-12):fx,oy=a?fy:y+(upper?ht+11:-11);
   ck(at(h,ox,oy,l),'continuous floor outside connector '+c.id+'/'+l,{feet:[ox,oy],flags});
  }
 }
 for(const [name,p]of Object.entries(m.spawns?.points||{})){const l=p.level??0;ck(known(l)&&finite(p.x)&&finite(p.y)&&at(h,p.x,p.y,l),'spawn '+name,{declared:l,derived:h.derive(p.x-B.anchorX,p.y-B.anchorY),flags});}
 const start=m.spawns.points[m.spawns.default];
 for(const [k,v]of Object.entries(s.levels))if(Number(k)>0){
  for(const [i,r]of v.walk.entries()){
   const candidates=[.5,.25,.75].flatMap(tx=>[.5,.25,.75].map(ty=>[r[0]+r[2]*tx,r[1]+r[3]*ty])).filter(q=>at(h,...q,Number(k)));
   // A rectangle may include cliff rock; only clear positions claim a floor.
   if(!candidates.length){warnings.push({kind:'solid_walk_rect',level:Number(k),rect:i,flags});continue;}
   h.setLevel(start.level??0);const q=candidates[0],plan=h.plan({x:start.x-B.anchorX,y:start.y-B.anchorY},{x:q[0]-B.anchorX,y:q[1]-B.anchorY,level:Number(k)},{width:m.world.width,height:m.world.height,maxNodes:100000});
   ck(!!plan.path,'reachable floor '+k+'/'+i,{flags,expanded:plan.expanded});
  }
 }
}
const h=contexts[0].h,refs=new Map((m.props||[]).map(p=>[p.id,p]));
for(const group of ['spawns','transitions','eventZones','treasurePoints','symbols','monsters','walkers']){
 const entries=group==='spawns'?Object.entries(m.spawns.points).map(([id,v])=>({id,...v})):(m[group]||[]);
 for(const e of entries){const levels=e.levels??[e.level??0];ck(Array.isArray(levels)&&levels.length>0&&levels.every(known),'entity level '+group+'/'+e.id,{levels});
  const ref=refs.get(e.ref),r=Array.isArray(e.rect)?e.rect:((e.rect?.shape==='rect')?[e.rect.x,e.rect.y,e.rect.w,e.rect.h]:((e.shape?.shape==='rect')?[e.shape.x,e.shape.y,e.shape.w,e.shape.h]:null)),x=e.x??ref?.x??(r?r[0]+r[2]/2:null),y=e.y??ref?.y??(r?r[1]+r[3]/2:null);
  if(!finite(x)||!finite(y)){warnings.push({kind:'coordinates_not_resolved',group,id:e.id});continue;}
  ck(x>=0&&y>=0&&x<=m.world.width&&y<=m.world.height,'entity world coordinates '+group+'/'+e.id);
  const upper=Object.entries(s.levels).filter(([l,v])=>Number(l)>0&&v.walk.some(r=>x>=r[0]&&x<=r[0]+r[2]&&y>=r[1]&&y<=r[1]+r[3])).map(([l])=>Number(l));
  if(e.level==null&&e.levels==null&&upper.length)warnings.push({kind:'undeclared_level_overlaps_upper',group,id:e.id,feet:[x,y],default_level:0,upper});
  if(e.level!=null&&group!=='spawns')ck(levels.some(l=>at(h,x,y,l)),'declared entity floor '+group+'/'+e.id);
 }
}
console.log(JSON.stringify({map:id,footprint:B,checks,warnings}));

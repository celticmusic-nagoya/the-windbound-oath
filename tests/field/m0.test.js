// Run: node tests/field/m0.test.js   (no dependencies)
const fs=require('fs'),vm=require('vm'),path=require('path');
const root=path.join(__dirname,'..','..');
function load(files){const w={performance,console};w.window=w;const ctx=vm.createContext(w);
  for(const f of files)vm.runInContext(fs.readFileSync(path.join(root,f),'utf8'),ctx,{filename:f});return w;}
const base=load(['js/field/field-collision.js','js/field/field-movement.js','js/field/field-navigation.js','js/field/field-culling.js']);
const {FieldCollision:C,FieldMovement:M,FieldNavigation:N,FieldCulling:U}=base;
let fail=0;const ok=(c,m)=>{if(!c){fail++;console.error('FAIL',m);}else console.log('ok  ',m);};
// 1. hashed compile() == brute force over random rects/points (Lind equivalence)
let seed=7;const rnd=()=>(seed=(seed*1664525+1013904223)%4294967296)/4294967296;
const objs=[];for(let i=0;i<400;i++)objs.push({id:'o'+i,x:rnd()*2100,y:rnd()*1450,collisions:[[0,0,10+rnd()*120,6+rnd()*90]]});
const comp=C.compile(objs);let diff=0,hits=0;
for(let n=0;n<20000;n++){const x=rnd()*2160,y=rnd()*1500;const a=comp.blocked(x,y);let b=false;for(const s of comp.shapes)if(C.overlaps(s,x,y)){b=true;break;}if(a!==b)diff++;if(a)hits++;}
ok(diff===0&&hits>0,`hash==brute-force (${hits} blocked samples, ${diff} diffs)`);
// 2. non-rect still throws
let threw=false;try{C.compile([{id:'e',x:0,y:0,collisionShapes:[{type:'ellipse',x:0,y:0,width:5,height:5}]}]);}catch(e){threw=true;}ok(threw,'compile rejects non-rect');
threw=false;try{C.compileMap([{id:'e',shape:'ellipse'}]);}catch(e){threw=true;}ok(threw,'compileMap rejects non-rect');
// 3. compileMap enabledWhen
const flags={moss_a3_seal_open:false};
const cm=C.compileMap([{id:'seal',shape:'rect',x:100,y:100,w:128,h:18,enabledWhen:{flag:'moss_a3_seal_open',is:false}},{id:'w',shape:'rects',rects:[[500,500,20,20],[600,500,20,20]]}],f=>flags[f]);
const px=130-17,py=105-42; // feet at (130,105)
ok(cm.blocked(px,py)===true,'seal blocks while closed');flags.moss_a3_seal_open=true;ok(cm.blocked(px,py)===false,'seal passes when open');
ok(cm.blocked(510-17,510-42+10)===true&&cm.blocked(610-17,510-42+10)===true,'multi-rect blocker');
// 4. movement bounds injection + default
let r=M.advance(2150,100,40,0,()=>false);ok(r.x<=2160,'default bound 2160 kept');
r=M.advance(2150,100,40,0,()=>false,{bounds:{width:9600,height:6000}});ok(r.x>2160,'custom bound allows >2160');
// 5. navigation on a big map
N.configure({width:9600,height:6000,grid:32,maxNodes:40000});
const wall=C.compileMap([{id:'w',shape:'rect',x:4000,y:0,w:60,h:5000}]);
const bl=(x,y)=>wall.blocked(x,y);
const t=N.destination(8000,1000,bl);let pos={x:100,y:1000,target:t},frames=0;
while(pos.target&&frames<9000){pos=N.follow(pos.x,pos.y,pos.target,bl);frames++;}
ok(!pos.unreachable&&Math.hypot(pos.x-8000,pos.y-1000)<=3.5,`A* routes around wall on 9600x6000 (${frames} frames, ${N.status.outcome})`);
N.configure();ok(N.bounds.width===2160&&N.bounds.height===1500,'configure() restores Lind defaults');
// 6. culling
const nodes=new Set();const parent={appendChild(n){nodes.add(n);}};
const cull=U.create({chunk:256,margin:1,maxLiveNodes:800,parent});
for(let i=0;i<6000;i++)cull.add({id:'e'+i,x:rnd()*9600,y:rnd()*6000,w:20,h:20,create(){const n={remove(){nodes.delete(n);}};return n;}});
let peak=0;for(let x=0;x<8000;x+=100){cull.update({x,y:2000,width:1920,height:1080});peak=Math.max(peak,nodes.size);}
ok(peak>0&&peak<=800&&nodes.size===cull.stats.live,`culling keeps live nodes <=800 of 6000 @1920x1080 chunk256 (peak ${peak})`);
process.exit(fail?1:0);

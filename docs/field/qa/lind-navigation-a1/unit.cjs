const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');global.window=global;for(const f of ['field-movement','field-navigation'])vm.runInThisContext(fs.readFileSync('/workspace/the-windbound-oath/js/field/'+f+'.js','utf8'));
const M=FieldMovement,N=FieldNavigation;
const wall=(x,y)=>x>=50&&x<=60&&y<100;
let slide=M.advance(48,50,10,10,wall,{assist:false});assert.ok(slide.x<50&&slide.y>59&&slide.collided&&!slide.stopped);
let thin=M.advance(0,0,22.5,0,x=>x>10&&x<12,{assist:false});assert.ok(thin.x<=10&&thin.stopped);
const corridor=(x,y)=>x>=50&&x<=100&&(y<30||y>40);
let p={x:49,y:28},assist=[];for(let i=0;i<8;i++){const n=M.advance(p.x,p.y,22.5,0,corridor);assist.push(n.assisted);assert.ok(n.assisted<=3&&!corridor(n.x,n.y));p=n;}assert.ok(p.x>100&&assist.some(Boolean));
function travel(start,goal,blocked){let p=start,t=N.destination(goal.x,goal.y,blocked),trace=[];for(let i=0;t&&i<2000;i++){const n=N.follow(p.x,p.y,t,blocked);assert.ok(!blocked(n.x,n.y));assert.ok(Math.hypot(n.x-p.x,n.y-p.y)<=5.001);p=n;t=n.target;trace.push([p.x,p.y]);}return {p,t,trace,status:N.status};}
const routed=travel({x:20,y:50},{x:100,y:50},wall);assert.equal(routed.t,null);assert.equal(routed.status.outcome,'arrived');assert.ok(routed.trace.some(p=>p[1]>=100));
const gap=(x,y)=>x>=50&&x<=60&&(y<22||y>26);const narrow=travel({x:20,y:10},{x:100,y:10},gap);assert.equal(narrow.status.outcome,'arrived');assert.ok(narrow.trace.some(p=>p[1]>=22&&p[1]<=26));assert.equal(N.destination(55,50,wall),null);assert.equal(N.status.outcome,'blocked-destination');
const sealed=(x,y)=>x>=50&&x<=60;const failed=travel({x:20,y:50},{x:100,y:50},sealed);assert.equal(failed.t,null);assert.equal(failed.status.outcome,'no-route');
const arrivals=travel({x:10,y:10},{x:11.5,y:10.5},()=>false);assert.equal(arrivals.t,null);assert.ok(Math.hypot(arrivals.p.x-11.5,arrivals.p.y-10.5)<=3);
const first=N.destination(100,100,()=>false);N.follow(20,20,first,()=>false);const second=N.destination(10,20,()=>false);assert.equal(N.follow(20,20,second,()=>false).target,second);N.cancel();assert.equal(N.status.active,false);
console.log('axis sliding, thin walls, gradual corner assist, swept detour, bounded failure, arrival, replacement PASS');

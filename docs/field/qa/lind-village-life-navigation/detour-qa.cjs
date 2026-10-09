const vm=require('vm'),fs=require('fs'),assert=require('assert/strict');
const root='/workspace/the-windbound-oath',c=vm.createContext({performance});c.window=c;for(const f of ['field-movement.js','field-navigation.js'])vm.runInContext(fs.readFileSync(root+'/js/field/'+f,'utf8'),c);
let enabled=false;const dynamic=(x,y)=>enabled&&x>80&&x<100&&y>80&&y<120,blocked=(x,y)=>dynamic(x,y);blocked.staticBlocked=()=>false;blocked.dynamicBlocked=dynamic;
let x=20,y=100,target=c.FieldNavigation.destination(200,100,blocked);let r=c.FieldNavigation.follow(x,y,target,blocked);x=r.x;y=r.y;enabled=true;let waited=false,detoured=false;
for(let n=0;n<400&&target;n++){r=c.FieldNavigation.follow(x,y,target,blocked);if(r.target)assert.deepEqual({...r.target},{x:200,y:100});x=r.x;y=r.y;target=r.target;waited||=c.FieldNavigation.status.outcome==='waiting-actor';detoured||=c.FieldNavigation.status.outcome==='detouring-actor';assert.equal(dynamic(x,y),false)}
assert.equal(waited,true);assert.equal(detoured,true);assert.equal(c.FieldNavigation.status.outcome,'arrived');
// A destination occupied for longer than the old movement timeout is retained.
target=c.FieldNavigation.destination(90,100,blocked);let saved=target;x=50;y=100;for(let n=0;n<4000;n++){r=c.FieldNavigation.follow(x,y,target,blocked);assert.equal(r.target,saved);x=r.x;y=r.y;target=r.target}
enabled=false;for(let n=0;n<100&&target;n++){r=c.FieldNavigation.follow(x,y,target,blocked);x=r.x;y=r.y;target=r.target}assert.equal(c.FieldNavigation.status.outcome,'arrived');
fs.writeFileSync('/workspace/onboarding/lind-village-life-resume/detour-qa.json',JSON.stringify({lateStationaryActorDetour:true,occupiedDestination4000FramesRetained:true,resumesAfterClear:true},null,2));console.log('Late stationary actor: wait/live detour/arrive PASS; occupied destination retained past old timeout then resumed PASS');

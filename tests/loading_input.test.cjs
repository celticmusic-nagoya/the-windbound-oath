// Real LoadingInput, LoadingView and InputManager; simulated DOM and actual capture/target/bubble ordering.
const vm=require('node:vm'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.join(__dirname,'..');
function fixture(managerFirst=false){
 const windows=new Map(),documents=new Map(),nodes=[],trace=[];let interactions=0,retries=0;
 function listen(map,type,fn,capture){const list=map.get(type)||[];list.push({fn,capture:!!capture});map.set(type,list)}
 const classes=new Set();
 class Node{
  constructor(tag='div'){this.tagName=tag.toUpperCase();this.children=[];this.hidden=false;this.disabled=false;this.attributes={};this.style={};this.classList={contains:()=>false,add(){},remove(){}};this.textContent='';nodes.push(this)}
  append(...items){for(const item of items){this.children.push(item);item.parent=this;}}
  setAttribute(k,v){this.attributes[k]=v}getAttribute(k){return this.attributes[k]??null}
  closest(selector){for(let n=this;n;n=n.parent){if(selector==='button[data-loading-action]'&&n.tagName==='BUTTON'&&n.attributes['data-loading-action'])return n;if(selector.split(',').some(s=>s==='#'+n.id))return n;}return null}
  contains(n){for(;n;n=n.parent)if(n===this)return true;return false}
  matches(selector){return selector==='button,[role="button"]'&&this.tagName==='BUTTON'}
  querySelectorAll(){return this.children.filter(n=>n.tagName==='BUTTON'&&!n.hidden&&!n.disabled)}
  getBoundingClientRect(){return {left:0,top:0,width:80,height:30}}
  focus(){c.document.activeElement=this}
  click(){dispatch('click',this)}
 }
 const body=new Node('body');body.classList={contains:x=>classes.has(x),add:x=>classes.add(x),remove:x=>classes.delete(x)};
 const c={console,window:null,performance,document:{body,activeElement:body,createElement:tag=>new Node(tag),querySelector:s=>nodes.find(n=>'#'+n.id===s)||null,querySelectorAll:()=>[],addEventListener:(t,f,b)=>listen(documents,t,f,b)},addEventListener:(t,f,b)=>listen(windows,t,f,b),dispatchEvent:e=>{for(const l of windows.get(e.type)||[])l.fn(e)},CustomEvent:class{constructor(type){this.type=type}},setInterval(){},matchMedia:()=>({matches:false}),getComputedStyle:n=>({display:n.hidden?'none':'block',visibility:'visible',zIndex:'0'}),MossForest:{active:true,busy:false,interactNearest(){interactions++;trace.push('interaction')}},BattlePresentation:{busy:false}};
 c.window=c;vm.createContext(c);
 function run(p){vm.runInContext(fs.readFileSync(path.join(root,p),'utf8'),c,{filename:p})}
 if(managerFirst)run('js/input-manager.js');run('js/loading-input.js');run('js/loading-view.js');if(!managerFirst)run('js/input-manager.js');
 function dispatch(type,target=body,more={}){
  const e={type,target,repeat:false,key:'',pointerId:1,defaultPrevented:false,stopped:false,preventDefault(){this.defaultPrevented=true},stopImmediatePropagation(){this.stopped=true},...more};
  const phase=(map,capture,name)=>{for(const l of map.get(type)||[]){if(e.stopped)break;if(l.capture===capture){trace.push(name);l.fn(e);}}};
  phase(windows,true,'window-capture');if(!e.stopped)phase(documents,true,'document-capture');
  if(!e.stopped){trace.push('target');if(type==='click')target.onclick?.(e);}
  if(!e.stopped)phase(documents,false,'document-bubble');if(!e.stopped)phase(windows,false,'window-bubble');
  return e;
 }
 const retry=()=>{retries++;trace.push('retry');c.LoadingView.open('battle','loading');};
 return {c,body,trace,dispatch,nodes,run,open(owner='battle',failed=false){c.LoadingView.open(owner,'Loading',failed?retry:null)},close(owner='battle'){c.LoadingView.close(owner)},get button(){return nodes.find(n=>n.tagName==='BUTTON')},get interactions(){return interactions},get retries(){return retries}};
}
let passed=0;function test(name,fn){fn();passed++;console.log('PASS',name)}
for(const owner of ['normal','raider','map'])for(const key of ['Enter',' ','Escape','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'])test(owner+' consumes '+JSON.stringify(key)+' before underlying handlers',()=>{
 const f=fixture();f.open(owner);const e=f.dispatch('keydown',f.body,{key});assert.equal(e.defaultPrevented,true);assert.equal(f.interactions,0);assert.equal(f.c.InputManager.state(),'LOADING');assert.equal(f.trace.includes('document-capture'),false);assert.equal(f.trace.includes('target'),false);f.dispatch('keyup',f.body,{key});
});
test('InputManager itself protects Loading even when registered before the common capture listener',()=>{const f=fixture(true);f.open();f.dispatch('keydown',f.body,{key:'Enter'});assert.equal(f.interactions,0);assert.equal(f.c.InputManager.state(),'LOADING')});
test('window/document capture and target/bubble order: blocked event reaches none of the game listeners',()=>{
 const f=fixture();for(const capture of [true,false])f.c.document.addEventListener('keydown',()=>f.trace.push('game-document'),capture);f.c.addEventListener('keydown',()=>f.trace.push('game-window'),false);f.open();f.dispatch('keydown',f.body,{key:'Enter'});assert.equal(f.trace.includes('game-document'),false);assert.equal(f.trace.includes('game-window'),false);f.dispatch('keyup',f.body,{key:'Enter'});f.close();f.trace.length=0;f.dispatch('keydown',f.body,{key:'Enter'});assert.equal(f.interactions,1);assert.ok(f.trace.indexOf('interaction')<f.trace.indexOf('game-document'));assert.ok(f.trace.indexOf('target')<f.trace.lastIndexOf('game-document'));assert.ok(f.trace.lastIndexOf('game-document')<f.trace.indexOf('game-window'));
});
for(const pointerType of ['mouse','touch'])test(pointerType+' pointerdown/click cannot activate the background during Loading',()=>{const f=fixture();const button=f.c.document.createElement('button');button.onclick=()=>{throw Error('background click')};f.open();for(const type of ['pointerdown','pointermove','pointerup','click'])assert.equal(f.dispatch(type,button,{pointerType}).defaultPrevented,true);assert.equal(f.interactions,0)});
for(const key of ['Enter',' '])test('retry '+JSON.stringify(key)+' activates once, repeats and keyup cannot replay',()=>{const f=fixture();f.open('battle',true);assert.equal(f.c.document.activeElement,f.button);f.dispatch('keydown',f.button,{key});assert.equal(f.retries,1);f.dispatch('keydown',f.button,{key,repeat:true});f.dispatch('keyup',f.button,{key});assert.equal(f.retries,1);assert.equal(f.interactions,0)});
for(const pointerType of ['mouse','touch'])test(pointerType+' explicit retry works after a blocked gesture and only once',()=>{const f=fixture();f.open('battle',true);f.dispatch('pointerdown',f.body,{pointerType});f.dispatch('pointerup',f.body,{pointerType});f.dispatch('click',f.body,{pointerType});f.dispatch('pointerdown',f.button,{pointerType});f.dispatch('pointerup',f.button,{pointerType});f.dispatch('click',f.button,{pointerType});f.dispatch('click',f.button,{pointerType});assert.equal(f.retries,1);assert.equal(f.interactions,0)});
test('held Enter crossing Loading completion is quarantined until release; fresh input works',()=>{const f=fixture();f.open();f.dispatch('keydown',f.body,{key:'Enter'});f.close();f.dispatch('keydown',f.body,{key:'Enter',repeat:true});assert.equal(f.interactions,0);f.dispatch('keyup',f.body,{key:'Enter'});f.dispatch('keydown',f.body,{key:'Enter'});assert.equal(f.interactions,1)});
test('already held direction is cleared and cannot resume movement after unlock until key release',()=>{const f=fixture();f.dispatch('keydown',f.body,{key:'ArrowRight'});assert.ok(f.c.InputManager.heldVector());f.open();assert.equal(f.c.InputManager.heldVector(),null);f.close();assert.equal(f.c.InputManager.heldVector(),null);f.dispatch('keydown',f.body,{key:'ArrowRight',repeat:true});assert.equal(f.c.InputManager.heldVector(),null);f.dispatch('keyup',f.body,{key:'ArrowRight'});f.dispatch('keydown',f.body,{key:'ArrowRight'});assert.ok(f.c.InputManager.heldVector())});
test('Space retry that completes synchronously cannot click again on keyup or leak into field',()=>{const f=fixture();f.open('battle',true);let count=0;f.button.onclick=()=>{count++;f.close()};f.dispatch('keydown',f.button,{key:' '});assert.equal(count,1);assert.equal(f.dispatch('keyup',f.button,{key:' '}).defaultPrevented,true);assert.equal(f.interactions,0)});
test('pointer held across Loading cannot replay a delayed click after completion',()=>{const f=fixture();const b=f.c.document.createElement('button');let clicks=0;b.onclick=()=>clicks++;f.dispatch('pointerdown',b);f.open();f.close();f.dispatch('pointerup',b);f.dispatch('click',b);assert.equal(clicks,0);f.dispatch('pointerdown',b);f.dispatch('pointerup',b);f.dispatch('click',b);assert.equal(clicks,1)});
test('stale owner close cannot unlock a newer map Loading',()=>{const f=fixture();f.open('old');f.open('new');f.close('old');assert.equal(f.c.LoadingInput.busy,true);f.close('new');assert.equal(f.c.LoadingInput.busy,false)});
test('disabled recovery action is never allowed, Tab stays on the permitted recovery control',()=>{const f=fixture();f.open('battle',true);const e=f.dispatch('keydown',f.button,{key:'Tab'});assert.equal(e.defaultPrevented,true);assert.equal(f.c.document.activeElement,f.button);f.dispatch('keyup',f.button,{key:'Tab'});f.button.disabled=true;f.dispatch('keydown',f.button,{key:'Enter'});assert.equal(f.retries,0)});
test('map failure recovery control remains keyboard usable after Loading view closes',()=>{const f=fixture();f.open('map');f.close('map');const panel=f.c.document.createElement('div');panel.id='fieldEntryError';const button=f.c.document.createElement('button');button.setAttribute('data-loading-action','retry');panel.append(button);let retry=0;button.onclick=()=>retry++;f.dispatch('keydown',button,{key:'Enter'});assert.equal(retry,1);assert.equal(f.interactions,0)});
test('keyboard retry remains usable after a blocked touch gesture',()=>{const f=fixture();f.open('map',true);f.dispatch('pointerdown',f.body,{pointerType:'touch'});f.dispatch('pointerup',f.body,{pointerType:'touch'});f.dispatch('keydown',f.button,{key:'Enter'});assert.equal(f.retries,1);assert.equal(f.interactions,0)});
console.log(passed+' PASS; real modules, simulated event phases; browser NOT_RUN');

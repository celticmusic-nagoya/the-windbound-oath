// Run: node tests/issue51_command_lock.test.cjs. Real source, simulated DOM; browser coverage is separate.
const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict'),path=require('node:path');
const root=path.join(__dirname,'..'),html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const css=fs.readFileSync(path.join(root,'css/battle-presentation.css'),'utf8');
const block=html.slice(html.indexOf('// Shared COMMAND lock:'),html.indexOf('\nconst aftermathLines='));
assert.ok(block.length>0);
const classList=()=>{const s=new Set();return {add:x=>s.add(x),remove:x=>s.delete(x),contains:x=>s.has(x),toggle(x,on){on?s.add(x):s.delete(x)}}};
const elements=new Map();for(const id of ['normalCommandToggle','rbCommandToggle','normalBattleCmd','rbCmd','normalCommandClose','rbCommandClose','normalItems'])elements.set('#'+id,{hidden:true,inert:false,disabled:false,attrs:{},classList:classList(),style:{values:{},setProperty(k,v){this.values[k]=v},removeProperty(k){delete this.values[k]}},setAttribute(k,v){this.attrs[k]=v}});
let observer;const c={window:null,document:{body:{classList:classList()}},$:s=>elements.get(s),attackBattleBusy:false,rbBusy:false,BattlePresentation:{busy:false},BattleTargetSelector:{active:false},MutationObserver:class{constructor(fn){observer=fn}observe(){}}};c.window=c;vm.createContext(c);vm.runInContext(block,c);
let passed=0;function check(name,fn){fn();passed++;console.log('PASS',name)}
for(const [mode,set,panelId,toggleId]of [['normal','setNormalCommandDrawer','#normalBattleCmd','#normalCommandToggle'],['raider','setRaiderCommandDrawer','#rbCmd','#rbCommandToggle']]){
 const p=elements.get(panelId),t=elements.get(toggleId);
 check(mode+' closed drawer rejects pointer/keyboard/programmatic open during hold',()=>{c[set](false);c.BattlePresentation.busy=true;c.document.body.classList.add('battlePresentationBusy');observer();assert.equal(t.disabled,true);assert.equal(t.attrs['aria-disabled'],'true');assert.equal(p.inert,true);assert.equal(c[set](true),false);t.onclick();assert.equal(p.hidden,true);assert.equal(p.style.values.display,'none')});
 check(mode+' unlock is immediately usable without a polling timer',()=>{c.BattlePresentation.busy=false;c.document.body.classList.remove('battlePresentationBusy');observer();assert.equal(t.disabled,false);assert.equal(p.inert,false);assert.equal(c[set](true),true);assert.equal(p.hidden,false);assert.equal(p.style.values.display,'grid');assert.equal(p.style.values.visibility,undefined);assert.equal(p.style.values['pointer-events'],undefined)});
 check(mode+' open drawer and descendants disappear during hold and resume afterwards',()=>{c.BattlePresentation.busy=true;observer();assert.equal(p.style.values.display,'none');assert.equal(p.inert,true);assert.equal(c[set](true),false);c.BattlePresentation.busy=false;observer();assert.equal(p.style.values.display,'grid');assert.equal(p.hidden,false)});
 check(mode+' busy/action-cinematic guards agree with drawer gate',()=>{const prop=mode==='normal'?'attackBattleBusy':'rbBusy';c[prop]=true;assert.equal(c[set](true),false);c[prop]=false;c.document.body.classList.add('actionCinematic');observer();assert.equal(c[set](true),false);assert.equal(p.inert,true);c.document.body.classList.remove('actionCinematic');observer();assert.equal(c[set](true),true)});
}
for(const mode of ['normal','raider'])check(mode+' Loading locks COMMAND until readiness or explicit cancellation',()=>{c.BattleLoading={busy:true};observer();const set=mode==='normal'?'setNormalCommandDrawer':'setRaiderCommandDrawer';assert.equal(c[set](true),false);c.BattleLoading.busy=false;observer();assert.equal(c[set](true),true)});
for(const [name,end,mode]of [['chooseNormalAct','function startAttackBattle','normal'],['choosePartyAct','function openRaiderItems','raider']]){
 const start=html.indexOf('function '+name+'(');vm.runInContext(html.slice(start,html.indexOf(end,start)),c);
 check(mode+' action submission rejected throughout presentation lock',()=>{c.BattlePresentation.busy=true;assert.doesNotThrow(()=>c[name]('atk'));c.BattlePresentation.busy=false;c.document.body.classList.add('battlePresentationBusy');assert.doesNotThrow(()=>c[name]('atk'));c.document.body.classList.remove('battlePresentationBusy')});
}
check('lock styling does not depend on viewport orientation',()=>{assert.match(css,/body\.battlePresentationBusy #normalCommandToggle,body\.battlePresentationBusy #rbCommandToggle\{[^}]*pointer-events:none!important/);assert.match(css,/body\.battlePresentationBusy #normalBattleCmd[^\n]*visibility:hidden!important/)});
check('keyboard layer consumes confirmation/navigation during animation',()=>{const input=fs.readFileSync(path.join(root,'js/input-manager.js'),'utf8');assert.match(input,/case 'BATTLE_ANIMATION':[\s\S]*?stopImmediatePropagation/);assert.match(input,/BattlePresentation\.busy/)});
console.log(passed+' PASS; simulated DOM only, not browser rendering');

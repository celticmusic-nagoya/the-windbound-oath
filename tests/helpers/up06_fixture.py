"""Ephemeral browser-only comparison policy. No JS file, production bank or PNG writes."""
INIT=r"""(()=>{
 if(new URLSearchParams(location.search).get('up06QA')!=='1'||new URLSearchParams(location.search).get('dev')!=='1')return;
 let base,wrapped,mode='D';const cache=new WeakMap();
 const choices={A:{order:[3,4,1,6],bob:.25},B:{order:[0,3,4,1,6],bob:.25},C:{order:[1,2,3,4,5,6],bob:.25},D:{order:[1,2,3,4,5,6],bob:1}};
 const path='assets/candidates/player-walk-polish01/up-06-left-boot-outline/aidan_walk_up_pushoff_candidate_v2.png';
 function ally(id,dir,profile=true,state='walk'){
  const d=base.ally(id,dir,profile,state);if(!d||id!=='aidan'||dir!=='up'||state!=='walk'||mode==='D')return d;
  let variants=cache.get(d);if(!variants){variants=new Map();cache.set(d,variants)}
  if(!variants.has(mode)){const c=choices[mode],source=d.frames.find(f=>f.key==='aidan_walk_up_03');const frames=c.order.map(n=>n===0?Object.freeze({...source,key:'aidan_walk_up_02',url:path}):d.frames.find(f=>f.key==='aidan_walk_up_'+String(n).padStart(2,'0')));variants.set(mode,Object.freeze({...d,frames:Object.freeze(frames),stride:90,bobScale:c.bob,note:'QA ONLY '+mode}))}return variants.get(mode);
 }
 const label=()=>{const b=document.getElementById('qaUp06Label');if(b)b.textContent='QA ONLY '+mode+' / '+choices[mode].order.map(n=>n===0?'NEW':String(n).padStart(2,'0')).join('→')+' / 周期90 / bob'+choices[mode].bob*100+'% / 1倍 / 未採用'};
 Object.defineProperty(window,'FieldWalkMotion',{configurable:true,get:()=>wrapped,set(value){
  if(!window.WINDBOUND_DEV){wrapped=value;return}base=value;wrapped=Object.freeze({...base,ally,resolve(group,id,dir,state='walk'){return group==='ally'?ally(id,dir,true,state):base.resolve(group,id,dir,state)}});
  let slot02,slotURL;function fieldSlot(){if(!slot02||!slot02.isConnected){slot02=[...document.querySelectorAll('.forest-aidan')].find(i=>i.dataset.src?.includes('aidan_walk_up_02.png'));slotURL=slot02?.dataset.src}if(slot02){const url=mode==='B'?path:slotURL;slot02.dataset.src=url;slot02.src=url}}
  window.QAUp06=Object.freeze({get condition(){return mode},select(id){if(!Object.hasOwn(choices,id))throw Error('invalid QA condition');mode=id;fieldSlot();label()},reset(){mode='D';fieldSlot();label()},otherDescriptorsUnchanged(){return ['down','left','right'].every(d=>ally('aidan',d)===base.ally('aidan',d))&&ally('fiona','up')===base.ally('fiona','up')&&ally('aidan','up',true,'idle')===base.ally('aidan','up',true,'idle')}});
  window.LoadCoordinator?.onInvalidate(()=>QAUp06.reset());
 }});
 document.addEventListener('DOMContentLoaded',()=>{if(!window.QAUp06)return;const b=document.createElement('div');b.id='qaUp06Label';b.style.cssText='position:fixed;top:0;left:0;z-index:99999;background:#10201cee;color:white;font:12px system-ui;padding:3px;pointer-events:none';document.body.append(b);label()});
})()"""
def install_controls(p):
 p.evaluate("""()=>{const root=document.querySelector('#walkMotionTest');if(root.querySelector('[data-qa=up06-condition]'))return;const s=document.createElement('select');s.dataset.qa='up06-condition';s.setAttribute('aria-label','QA-only up condition');for(const [id,text] of Object.entries({A:'A 4コマ bob25%',B:'B 5コマ bob25%',C:'C 現行6 bob25%',D:'D 本番6 bob100%'})){const o=document.createElement('option');o.value=id;o.textContent=text;s.append(o)}s.value=QAUp06.condition;s.onchange=()=>QAUp06.select(s.value);root.querySelector('header').append(s)}""")
def field_scale(p,enabled):
 p.evaluate("enabled=>{const s=document.querySelector('#walkMotionTest .walkStage');s.style.width=enabled?'150px':'';s.style.justifySelf=enabled?'center':''}",enabled)
 p.wait_for_timeout(100)

def audit_gates():
 """Execute the injected policy in isolated JS contexts without loading the app."""
 import json,subprocess
 code=r"""const vm=require('node:vm'),assert=require('node:assert/strict');const fixture=FIXTURE;const results=[];
 for(const [search,dev,expected] of [['',true,false],['?dev=1',true,false],['?up06QA=1',true,false],['?dev=1&up06QA=1',false,false],['?dev=1&up06QA=1',true,true]]){
  const callbacks={};const s={URLSearchParams,location:{search},WINDBOUND_DEV:dev,document:{addEventListener(t,f){callbacks[t]=f}},LoadCoordinator:{onInvalidate(){}},Object};s.window=s;vm.createContext(s);vm.runInContext(fixture,s);const original=Object.freeze({});s.FieldWalkMotion=original;assert.equal(Boolean(s.QAUp06),expected);if(!expected)assert.equal(s.FieldWalkMotion,original);results.push({name:search+'/DEV='+dev,pass:true});
 }console.log(JSON.stringify(results));""".replace('FIXTURE',json.dumps(INIT))
 return json.loads(subprocess.check_output(['node','-e',code],text=True))

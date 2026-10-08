// Shared manual targeting. Actions own resources; this module never consumes them.
(() => {
  const types = new Set(['enemy_single','enemy_all','ally_single','ally_all','ally_ko_single','self','none']);
  const memory = new Map();
  let pending = null;
  const panel = document.createElement('div'); panel.id='battleTargetPanel'; panel.hidden=true;
  panel.innerHTML='<span></span><button type="button">キャンセル</button>';
  document.body.append(panel);
  panel.querySelector('button').onclick=()=>cancel();
  const eligible = (x,type) => x.active !== false && !x.support && (type==='ally_ko_single' ? x.hp()<=0 : x.hp()>0);
  function clear(){
    document.querySelectorAll('.battleTargetHit').forEach(x=>x.remove());
    panel.hidden=true;
  }
  function cancel(){const p=pending;pending=null;clear();p?.onCancel?.();}
  function confirm(id){
    const p=pending;if(!p)return false;
    const chosen=p.candidates.find(x=>x.id===id);
    if(!chosen||!eligible(chosen,p.type))return false;
    pending=null;clear(); // Clear ownership before invoking action (double tap safe).
    if(p.type.startsWith('enemy'))memory.set(p.battle,id);
    const all=p.type.endsWith('_all');
    p.onConfirm(all?p.candidates.filter(x=>eligible(x,p.type)).map(x=>x.id):id);
    return true;
  }
  function draw(){
    document.querySelectorAll('.battleTargetHit').forEach(x=>x.remove());
    if(!pending)return;
    const p=pending;
    p.candidates.forEach(x=>{
      const node=typeof x.node==='string'?document.querySelector(x.node):x.node;
      if(!node)return;
      const r=node.getBoundingClientRect(),b=document.createElement('button');
      b.type='button';b.className='battleTargetHit';b.dataset.targetId=x.id;
      b.classList.toggle('selected',p.selected===x.id||p.type.endsWith('_all'));
      const w=Math.max(64,Math.min(r.width+16,180)),h=Math.max(72,Math.min(r.height+16,210));
      b.style.left=Math.max(0,Math.min(innerWidth-w,r.left+r.width/2-w/2))+'px';
      b.style.top=Math.max(60,Math.min(innerHeight-h-60,r.top+r.height/2-h/2))+'px';
      b.style.width=w+'px';b.style.height=h+'px';
      b.textContent=x.name;b.setAttribute('aria-label','対象：'+x.name);
      b.onclick=e=>{e.stopPropagation();confirm(x.id)};
      document.body.append(b);
    });
  }
  function open({type,battle='normal',candidates=[],actor,onConfirm,onCancel,label='対象を選択'}){
    if(pending)return false;
    if(!types.has(type))return false;
    if(type==='none'){onConfirm(null);return true;}
    const valid=candidates.filter(x=>eligible(x,type));
    if(type==='self') {const x=valid.find(x=>x.id===actor);if(!x)return false;onConfirm(x.id);return true;}
    if(!valid.length)return false;
    pending={type,battle,candidates:valid,onConfirm,onCancel,selected:valid.some(x=>x.id===memory.get(battle))?memory.get(battle):valid[0].id};
    panel.querySelector('span').textContent=label+' / TARGET';panel.hidden=false;draw();return true;
  }
  addEventListener('keydown',e=>{
    if(!pending)return;
    if(!['ArrowLeft','ArrowRight','Enter',' ','Escape'].includes(e.key))return;
    e.preventDefault();e.stopImmediatePropagation();
    if(e.key==='Escape')return cancel();
    if(e.key==='Enter'||e.key===' ')return confirm(pending.selected);
    const a=pending.candidates,i=a.findIndex(x=>x.id===pending.selected);
    pending.selected=a[(i+(e.key==='ArrowRight'?1:a.length-1))%a.length].id;draw();
  },true);
  addEventListener('resize',draw);
  window.BattleTargetSelector=Object.freeze({open,cancel,confirm,get active(){return !!pending},get selected(){return pending?.selected},reset(battle){cancel();memory.delete(battle)}});
})();

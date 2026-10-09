/* Independent peaceful-village DEV actors; no story/save/PartyManager hooks. */
(function () {
  'use strict';
  if(!window.WINDBOUND_DEV)return;
  const definitions=[
    ['farmer_male','農夫',970,1190,46],['farmer_female','農作業の女性',1150,1200,44],
    ['young_man','青年',630,665,46],['young_woman','若い女性',805,665,44],
    ['elder_man','老人',460,405,42],['elder_woman','村の老婆',790,1060,39],
    ['boy','男の子',600,700,31],['girl','女の子',850,725,31],
    ['merchant','道具屋の商人',420,690,45],['innkeeper','宿屋の主人',850,420,45],
    ['fisherman','釣り人',1447,1367,46],['caretaker','家畜の世話係',1350,1170,45]
  ].map(([id,label,x,footY,height])=>({id,label,x,footY,height,
    path:'img/field/lind/npc/villagers/'+id+'_idle.png'}));
  window.LindFisherman?.configure(definitions.find(d=>d.id==='fisherman'));
  const actors=[];
  let active=false,notice=null,lastInteraction=null,frame=null,previous=null;
  function add(definition) {if(actors.length)throw new Error('Register field NPC before mounting');definitions.push(definition);}
  function mount(parent,controls) {
    notice=document.createElement('div');notice.id='lindNPCNotice';notice.hidden=true;
    notice.setAttribute('role','status');controls.append(notice);
    definitions.forEach(d=>{
      const b=window.LindFieldContentBounds[d.boundsId||d.id+'_idle'];
      const scale=d.height/b[5],width=b[4]*scale;
      const actor={...d,width,y:d.footY-d.height,state:'IDLE',elapsed:0,direction:1,originX:d.x,frames:{},
        foot:{x:d.x-9,y:d.footY-8,width:18,height:8}};
      const el=document.createElement('div');el.className='lind-field-npc';el.dataset.npcId=d.id;
      Object.assign(el.style,{left:d.x-width/2+'px',top:actor.y+'px',width:width+'px',
        height:d.height+'px',zIndex:String(Math.round(d.footY))});
      const img=document.createElement('img');img.src=d.path;img.alt=d.label;
      actor.frames.idle=img;el.append(img);
      if(d.id==='farmer_male'&&window.LindFieldContentBounds.farmer_male_walk){
        const walk=document.createElement('img');walk.src=d.path.replace('_idle.png','_walk.png');walk.alt=d.label;
        actor.frames.walk=walk;el.append(walk);
      }
      parent.append(el);actor.element=el;
      const hit=document.createElement('button');hit.type='button';hit.className='lind-npc-interaction';
      hit.dataset.interactionId=d.id;hit.setAttribute('aria-label',d.label+'と話す');
      Object.assign(hit.style,{left:d.x-22+'px',top:d.footY-Math.max(44,d.height)+'px',
        width:'44px',height:Math.max(44,d.height)+'px',zIndex:String(Math.round(d.footY+1))});
      hit.addEventListener('pointerdown',e=>e.stopPropagation());
      hit.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();interact(d.id)});
      parent.append(hit);actor.hit=hit;actors.push(actor);
      if(d.id==='fisherman')window.LindFisherman?.mount(actor);
      render(actor);
    });
    window.LindChildren?.mount(actors);
    window.LindVillageLife?.mount(actors);
    actors.forEach(render);
  }
  function distance(a) {return Math.hypot(px+17-a.x,py+42-a.footY);}
  function interact(id) {
    if(!active||!window.LindFieldReview?.active)return false;
    const a=actors.find(a=>a.id===id);if(!a)return false;
    notice.hidden=false;
    if(distance(a)>90){notice.textContent=a.label+'へ近づいてください。';return false;}
    target=null;FieldNavigation.cancel();a.interactionPause=2;
    lastInteraction={id:a.id,type:'field_npc',reviewOnly:true};
    notice.textContent='DEV · '+a.label+' — 仮interaction。正式な会話は後工程。';
    window.dispatchEvent(new CustomEvent('lind-field-interaction',{detail:{...lastInteraction}}));return true;
  }
  function nearby() {const a=actors.filter(a=>distance(a)<=60).sort((a,b)=>distance(a)-distance(b))[0];return a?interact(a.id):false;}
  function focus(id) {
    const a=actors.find(a=>a.id===id);if(!a||!active)return false;
    target=null;px=a.x+38;py=a.footY-42;
    if(a.id==='boy')px=a.x-72;
    if(a.id==='fisherman'){const stand=LindFieldRiver.standingAreas.find(s=>s.id==='player');px=Math.max(stand.x,a.x-69);py=stand.y;}
    camera();return true;
  }
  function blocked(x,y) {return active&&actors.some(a=>x+28>a.foot.x&&x+6<a.foot.x+a.foot.width&&y+42>a.foot.y&&y+32<a.foot.y+a.foot.height);}
  function render(a) {
    if(a.fishing){LindFisherman.render(a);return;}
    const state=a.frames.walk&&a.state==='WALK'&&Math.floor(a.elapsed*4)%2?'walk':'idle';
    const b=window.LindFieldContentBounds[a.boundsId||a.id+'_'+state],scale=a.height/b[5];
    a.width=b[4]*scale;a.y=a.footY-a.height;a.foot.x=a.x-9;a.foot.y=a.footY-8;
    Object.assign(a.element.style,{left:a.x-a.width/2+'px',top:a.y+'px',width:a.width+'px',height:a.height+'px',zIndex:String(Math.round(a.footY)),transformOrigin:'50% 100%',transform:a.direction<0?'scaleX(-1)':'none'});
    Object.entries(a.frames).forEach(([key,image])=>{image.hidden=key!==state;});
    Object.assign(a.frames[state].style,{left:-b[2]*scale+'px',top:-b[3]*scale+'px',width:b[0]*scale+'px',height:b[1]*scale+'px'});
    Object.assign(a.hit.style,{left:a.x-22+'px',top:a.footY-Math.max(44,a.height)+'px',zIndex:String(Math.round(a.footY+1))});a.element.dataset.state=a.state;
  }
  function canMove(a,x,y) {
    if(window.LindFieldReview?.staticBlocked(x-17,y-42))return false;
    if(Math.hypot(px+17-x,py+42-y)<32)return false;
    if(actors.some(b=>b!==a&&Math.abs(b.x-x)<21&&Math.abs(b.footY-y)<12))return false;
    return !window.LindFieldAnimals?.blocked(x-17,y-42);
  }
  function moveToward(a,goal,speed,seconds) {
    const dx=goal.x-a.x,dy=goal.y-a.footY,d=Math.hypot(dx,dy);if(d<.001)return true;
    const distance=Math.min(d,speed*seconds),parts=Math.max(1,Math.ceil(distance/2));let progress=false;
    for(let i=0;i<parts;i++){
      const x=a.x+dx/d*distance/parts,y=a.footY+dy/d*distance/parts;
      if(!canMove(a,x,y))break;
      a.x=x;a.footY=y;progress=true;
    }
    if(Math.abs(dx)>.2)a.direction=dx>0?1:-1;
    return progress;
  }
  function update(seconds) {
    actors.forEach(a=>{a.interactionPause=Math.max(0,(a.interactionPause||0)-seconds);});
    actors.filter(a=>a.fishing).forEach(a=>LindFisherman.update(a,seconds));
    window.LindChildren?.update(seconds);
    actors.filter(a=>a.play).forEach(render);
    window.LindVillageLife?.update(seconds);
    actors.filter(a=>a.life).forEach(render);
  }
  function setActive(value) {
    active=Boolean(value);clear();cancelAnimationFrame(frame);previous=null;
    if(!active)return;
    const tick=now=>{if(!active)return;if(previous!==null)update(Math.min((now-previous)/1000,.1));previous=now;frame=requestAnimationFrame(tick);};
    frame=requestAnimationFrame(tick);
  }
  function clear(){lastInteraction=null;if(notice)notice.hidden=true;}
  window.LindFieldNPCs=Object.freeze({add,mount,focus,blocked,interact,nearby,clear,
    setActive,update,canMove,moveToward,get actors(){return actors;},get definitions(){return definitions;},
    get lastInteraction(){return lastInteraction;}});
})();

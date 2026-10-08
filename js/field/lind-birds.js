/* STEP 11: bounded DEV ambience. No collision, dialogue, save or story hooks.
 * Wind owns this timeline; water, villagers and livestock have separate owners. */
(function () {
  'use strict';
  if(!window.WINDBOUND_DEV)return;
  const paths={perched:'img/field/lind/environment/birds/lind_bird_perched.png',
    flying:'img/field/lind/environment/birds/lind_bird_flying.png'};
  const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
  let active=false,frame=null,previous=null,nextFlock=18,flockTime=0,flockActive=false,flockOrigin=null,spawnCount=0;
  const ground=[{id:'plaza_bird',x:575,y:750},{id:'farm_bird',x:1320,y:1175}];
  const flock=[];
  function make(parent) {
    const node=document.createElement('div');node.className='lind-field-bird';node.setAttribute('aria-hidden','true');
    const image=document.createElement('img');node.append(image);parent.append(node);return {node,image};
  }
  function draw(b,type,x,y,visible,opacity=1) {
    const bounds=window.LindFieldContentBounds['lind_bird_'+type];
    const scale=type==='perched'?12/bounds[5]:18/bounds[4],width=bounds[4]*scale,height=bounds[5]*scale;
    b.node.hidden=!visible;b.node.classList.toggle('lind-bird-flying',type==='flying');
    Object.assign(b.node.style,{left:x-width/2+'px',top:y-height+'px',width:width+'px',height:height+'px',
      opacity:String(opacity),zIndex:type==='perched'?String(Math.round(y)): '2000'});
    if(b.image.getAttribute('src')!==paths[type])b.image.src=paths[type];
    Object.assign(b.image.style,{left:-bounds[2]*scale+'px',top:-bounds[3]*scale+'px',
      width:bounds[0]*scale+'px',height:bounds[1]*scale+'px'});
  }
  function distance(b){return Math.hypot(px+17-b.x,py+42-b.y);}
  function mount(parent) {
    ground.forEach(b=>Object.assign(b,make(parent),{state:'ABSENT',age:0}));
    for(let i=0;i<3;i++)flock.push(make(parent));
    ground.forEach(b=>draw(b,'perched',b.x,b.y,false));flock.forEach(b=>draw(b,'flying',0,0,false));
  }
  function update(seconds) {
    if(!active||!window.LindFieldEnvironment.wind)return;
    ground.forEach(b=>{
      b.age+=seconds;
      if(b.state==='PERCHED'&&distance(b)<70){b.state='TAKEOFF';b.age=0;}
      if(b.state==='TAKEOFF'){
        const duration=reduced.matches ? .2 : 1.1,t=Math.min(1,b.age/duration);
        draw(b,'flying',b.x+t*65,b.y-t*45-Math.sin(t*Math.PI)*12,true,Math.min(1,(1-t)*2));
        if(t>=1){b.state='WAITING';b.age=0;draw(b,'flying',b.x,b.y,false);}
      }else if(b.state==='WAITING'){
        draw(b,'perched',b.x,b.y,false);
        if(b.age>=25&&distance(b)>100){b.state='PERCHED';b.age=0;draw(b,'perched',b.x,b.y,true);}
      }else if(b.state==='PERCHED')draw(b,'perched',b.x,b.y,true);
    });
    if(reduced.matches){flockActive=false;flock.forEach(b=>{b.node.hidden=true;});return;}
    if(!flockActive){
      nextFlock-=seconds;
      if(nextFlock<=0){flockActive=true;flockTime=0;flockOrigin={x:px-700,y:Math.max(150,py-Math.min(150,Math.max(25,innerHeight/2-150)))};spawnCount++;}
    }
    if(flockActive){
      flockTime+=seconds;
      flock.forEach((b,i)=>draw(b,'flying',flockOrigin.x+flockTime*140-i*35,
        flockOrigin.y+(i%2)*14+Math.sin(flockTime*1.3+i)*2,true));
      if(flockTime>=12){flockActive=false;nextFlock=45;flock.forEach(b=>{b.node.hidden=true;});}
    }
  }
  function sync() {
    cancelAnimationFrame(frame);frame=null;previous=null;flockActive=false;nextFlock=18;
    flock.forEach(b=>{b.node.hidden=true;});
    const enabled=active&&window.LindFieldEnvironment.wind;
    ground.forEach(b=>{b.state=enabled?(distance(b)>70?'PERCHED':'WAITING'):'ABSENT';b.age=0;
      draw(b,'perched',b.x,b.y,enabled&&b.state==='PERCHED');});
    if(!enabled)return;
    const tick=now=>{if(!active||!LindFieldEnvironment.wind)return;
      if(previous!==null)update(Math.min((now-previous)/1000,.1));previous=now;frame=requestAnimationFrame(tick);};
    frame=requestAnimationFrame(tick);
  }
  function focus(){if(!active)return false;const b=ground[0];target=null;px=b.x+110-17;py=b.y-42;camera();return true;}
  window.addEventListener('lind-wind-change',()=>{if(ground[0].node)sync();});
  window.LindFieldBirds=Object.freeze({paths,mount,update,focus,setActive(value){active=Boolean(value);sync();},
    get status(){return {active,flockActive,spawnCount,nextFlock,ground:ground.map(b=>({id:b.id,state:b.state,x:b.x,y:b.y,visible:b.node?!b.node.hidden:false})),visibleFlock:flock.filter(b=>!b.node.hidden).length};}});
})();

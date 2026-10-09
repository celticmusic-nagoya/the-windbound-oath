/* Provided fishing poses; ambient only. Driven by the existing NPC RAF. */
(function(){
  'use strict';
  if(!window.WINDBOUND_DEV)return;
  const assets=window.LindFishermanAssets,scale=.20;
  function random(a){a.fishing.seed=(Math.imul(a.fishing.seed,1664525)+1013904223)>>>0;return a.fishing.seed/4294967296;}
  function configure(d){
    const deck=LindFieldRiver.crossings.find(c=>c.id==='fishing_deck').polygon;
    d.x=Math.max(...deck.map(p=>p[0]))-38;
    d.footY=(Math.min(...deck.map(p=>p[1]))+Math.max(...deck.map(p=>p[1])))/2+11;
    d.height=40;
  }
  function mount(a){
    a.frames={};a.element.replaceChildren();
    for(const [key,f]of Object.entries(assets)){
      const img=document.createElement('img');img.src=f.path;img.alt=a.label;img.hidden=true;
      a.element.append(img);a.frames[key]=img;
    }
    a.fishing={state:'FISH_IDLE',elapsed:0,time:0,wait:12,seed:8721,catches:0,lastCatch:-90};
    a.direction=1;render(a);
  }
  function update(a,seconds){
    const f=a.fishing;f.time+=seconds;f.elapsed+=seconds;
    if(f.state==='FISH_IDLE'&&f.elapsed>=1){f.state='WAIT';f.elapsed=0;f.wait=8+random(a)*17;}
    else if(f.state==='WAIT'&&f.elapsed>=f.wait){
      f.elapsed=0;
      if(f.time-f.lastCatch>=60&&random(a)<.18)f.state='BITE';
      else {f.state='ROD_ADJUST';}
    }
    else {
      const durations={ROD_ADJUST:1.2,BITE:.8,REEL:1.4,CATCH:1.1,INSPECT:2.8,RESET:1.2};
      if(durations[f.state]&&f.elapsed>=durations[f.state]){
        const next={ROD_ADJUST:'WAIT',BITE:'REEL',REEL:'CATCH',CATCH:'INSPECT',INSPECT:'RESET',RESET:'FISH_IDLE'};
        f.state=next[f.state];f.elapsed=0;
        if(f.state==='WAIT')f.wait=8+random(a)*17;
        if(f.state==='CATCH'){f.catches++;f.lastCatch=f.time;}
      }
    }
    render(a);
  }
  function render(a){
    const f=a.fishing;
    const key=f.state==='BITE'?'bite_01':f.state==='REEL'?(f.elapsed<.7?'reel_01':'reel_02'):
      f.state==='CATCH'?'catch_01':f.state==='INSPECT'?['inspect_01','inspect_02','inspect_03','inspect_04'][Math.min(3,Math.floor(f.elapsed/.7))]:
      f.state==='RESET'?(f.elapsed<.8?'reset_01':'idle_02'):f.state==='ROD_ADJUST'?(f.elapsed<.6?'idle_02':'idle_03'):'idle_01';
    const frame=assets[key];a.state=f.state;a.y=a.footY-40;a.width=frame.width*scale;
    // Fixed body/collision anchor; a rod/splash never changes the actor origin.
    Object.assign(a.element.style,{left:a.x-frame.anchor[0]*scale+'px',top:a.footY-frame.anchor[1]*scale+'px',
      width:frame.width*scale+'px',height:frame.height*scale+'px',zIndex:String(Math.round(a.footY)),transform:'none'});
    for(const [k,img]of Object.entries(a.frames))img.hidden=k!==key;
    Object.assign(a.frames[key].style,{left:'0px',top:'0px',width:frame.width*scale+'px',height:frame.height*scale+'px'});
    Object.assign(a.hit.style,{left:a.x-22+'px',top:a.footY-44+'px',zIndex:String(Math.round(a.footY+1))});
    Object.assign(a.foot,{x:a.x-9,y:a.footY-8});a.element.dataset.state=f.state;a.element.dataset.frame=key;
  }
  window.LindFisherman=Object.freeze({configure,mount,update,render,scale});
})();

// Lou's idle flight: while the raider battle is on screen she drifts around her home slot (idle AND support turns).
// Vertical float is CSS (#rbLou>img, louFloat); the wander is a chain of WAAPI `translate` tweens on #rbLou, which no other code animates.
(() => {
 const TUNE=Object.freeze({rangeX:70,rangeUp:56,rangeDown:22,portraitScale:.55,minMs:1300,maxMs:2400,pauseMin:200,pauseMax:1200,pollMs:500});
 let timer=0,poll=0,pos={x:0,y:0},anim=null,running=false;
 const el=()=>document.getElementById('rbLou');
 const rand=(a,b)=>a+Math.random()*(b-a);
 const reduce=()=>matchMedia('(prefers-reduced-motion: reduce)').matches;
 function stop(){
  running=false;clearTimeout(timer);timer=0;
  if(anim){try{anim.cancel()}catch(e){}anim=null}
  pos={x:0,y:0};const n=el();if(n)n.style.removeProperty('translate');
 }
 function step(){
  const n=el();if(!running||!n||typeof n.animate!=='function')return;
  const k=innerHeight>innerWidth?TUNE.portraitScale:1,
   next={x:rand(-TUNE.rangeX,TUNE.rangeX)*k,y:rand(-TUNE.rangeUp,TUNE.rangeDown)*k},ms=rand(TUNE.minMs,TUNE.maxMs);
  const from=pos;
  const a=n.animate([{translate:from.x+'px '+from.y+'px'},{translate:next.x+'px '+next.y+'px'}],{duration:ms,easing:'ease-in-out',fill:'forwards'});
  if(anim)try{anim.cancel()}catch(e){}
  anim=a;pos=next;
  a.onfinish=()=>{if(anim===a&&running)timer=setTimeout(step,rand(TUNE.pauseMin,TUNE.pauseMax));};
 }
 function start(){if(running||reduce())return;running=true;pos={x:0,y:0};step();}
 function tick(){
  const on=document.body.classList.contains('raiderBattleMode')&&document.getElementById('raiderBattle')?.style.display!=='none';
  if(on&&!running)start();else if(!on&&running)stop();
 }
 poll=setInterval(tick,TUNE.pollMs);
 window.BattleLouFlight=Object.freeze({start,stop,tune:TUNE,get running(){return running},get offset(){return {...pos}}});
})();

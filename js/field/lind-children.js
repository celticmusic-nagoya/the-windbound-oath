/* Two existing children, authored plaza play route; no random world roaming. */
(function(){
  'use strict';if(!window.WINDBOUND_DEV)return;
  let children=[],route=[],zone=null,direction=1,runner=0,elapsed=0,swaps=0,pause=0;
  const metrics={swaps:0,tags:0,reversals:0,pauses:0,yields:0};
  function mount(actors){
    children=['boy','girl'].map(id=>actors.find(a=>a.id===id));
    const plaza=LindTerrainLayout.plaza,stone=LindFieldAssets.objects.find(o=>o.id==='lind_wind_stone');
    const base=stone.y+stone.collision[1]+stone.collision[3],cx=stone.x+stone.width/2;
    zone={left:plaza.x-plaza.width/2+30,right:plaza.x+plaza.width/2-30,top:plaza.y-plaza.height/2+55,bottom:plaza.y+plaza.height/2-18};
    route=[{x:stone.x-35,y:base-58},{x:cx,y:base-58},{x:stone.x+stone.width+35,y:base-45},
      {x:stone.x+stone.width+42,y:base+26},{x:zone.right-10,y:zone.bottom-10},
      {x:cx,y:base+74},{x:stone.x-40,y:base+74},{x:stone.x-45,y:base+16}];
    children.forEach((a,i)=>{const index=i?6:7;a.x=route[index].x;a.footY=route[index].y;
      a.play={index:(index+1)%route.length,blocked:0,rest:0};a.originX=a.x;a.originY=a.footY;a.state=i?'CHASE':'RUN';});
  }
  function turn(){
    runner=1-runner;swaps++;elapsed=0;pause=1.0;metrics.swaps++;metrics.pauses++;
    if(swaps%2===0){direction*=-1;metrics.reversals++;}
    children.forEach((a,i)=>{let nearest=0;route.forEach((p,n)=>{if(Math.hypot(p.x-a.x,p.y-a.footY)<Math.hypot(route[nearest].x-a.x,route[nearest].y-a.footY))nearest=n;});
      a.play.index=(nearest+direction+route.length)%route.length;a.play.blocked=0;a.play.rest=i?.45:0;a.state='PAUSE';a.direction*=-1;});
  }
  function update(seconds){
    if(!children.length)return;elapsed+=seconds;
    if(pause>0){pause-=seconds;children.forEach(a=>a.state='PAUSE');return;}
    const distance=Math.hypot(children[0].x-children[1].x,children[0].footY-children[1].footY);
    if((distance<25&&elapsed>3)||elapsed>35){if(distance<25)metrics.tags++;turn();return;}
    children.forEach((a,i)=>{
      if(a.interactionPause>0){a.state='PAUSE';return;}
      if(a.play.rest>0){a.play.rest-=seconds;a.state='PAUSE';return;}
      const goal=route[a.play.index],speed=(i?29:26)*(i===runner?1:1.15);
      const moved=LindFieldNPCs.moveToward(a,goal,speed,seconds);
      if(moved){a.state=i===runner?'RUN':'CHASE';a.play.blocked=0;}
      else {a.state='YIELD';a.play.blocked+=seconds;metrics.yields++;}
      if(Math.hypot(a.x-goal.x,a.footY-goal.y)<1.5){
        a.play.index=(a.play.index+direction+route.length)%route.length;
        // A staggered look-back at the plaza edge, rather than synchronized laps.
        if(a.play.index===4&&i===runner){a.play.rest=.6;metrics.pauses++;}
      }
      if(a.play.blocked>2.5&&elapsed>3)turn();
    });
  }
  window.LindChildren=Object.freeze({mount,update,get zone(){return zone;},get route(){return route;},get metrics(){return {...metrics};},get direction(){return direction;},get runner(){return children[runner]?.id;}});
})();

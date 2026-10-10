/* Mob NPC "少年剣士": wooden-sword practice loop at the training ground (idle -> 6-frame swing -> idle).
 * Frames boy_swordsman_attack_01..06 (tools/lind/make_swordboy.py). Pure presentation: no battle, save or story hooks. */
(function(){
  'use strict';if(!window.WINDBOUND_DEV)return;
  const FRAME_MS=[110,90,130,70,110,150],REST=[2.2,3.4];   // per-frame ms; pause between practice swings (s)
  let boy=null,t=0,wait=1.2,metrics={swings:0};
  function mount(actors){
    boy=actors.find(a=>a.motion==='swing')||null;if(!boy)return;
    boy.swing={frame:-1};boy.state='IDLE';boy.attackFrame=0;
  }
  function update(seconds){
    if(!boy||!boy.swing)return;
    if(boy.interactionPause>0){boy.state='IDLE';boy.swing.frame=-1;return;}
    if(boy.swing.frame<0){
      wait-=seconds;boy.state='IDLE';
      if(wait<=0){boy.swing.frame=0;t=0;boy.state='ATTACK';boy.attackFrame=0;}
      return;
    }
    t+=seconds*1000;
    if(t>=FRAME_MS[boy.swing.frame]){
      t-=FRAME_MS[boy.swing.frame];boy.swing.frame++;
      if(boy.swing.frame>=FRAME_MS.length){boy.swing.frame=-1;boy.state='IDLE';metrics.swings++;wait=REST[0]+(metrics.swings%3)*(REST[1]-REST[0])/2;return;}
    }
    boy.state='ATTACK';boy.attackFrame=boy.swing.frame;
  }
  window.LindSwordBoy=Object.freeze({mount,update,get metrics(){return {...metrics};}});
})();

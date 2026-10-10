/* Prologue story bindings for the Moss Forest runtime (M4).
 * Keeps all story knowledge (stages 9-12, corruption symbols, Lou, altar, texts) out of the generic runtime.
 * Uses the game's classic-script globals (say, questPop, setObj, startAttackBattle, ...) at call time only. */
(function () {
  'use strict';
  const MAP_IDS={a1:'moss_forest_01_sunlit_path',a2:'moss_forest_02_mossy_ravine',a3:'moss_forest_03_ancient_grove'};
  const TEXTS={
    msg_a1_sign_lind:'『← 村』と彫られた古い木の標識。苔に覆われて、ほとんど読めない。',
    msg_a1_sign_fork:'道が二手に分かれている。片方は水音のする方へ、もう片方は森の奥へ続いているようだ。',
    msg_a1_camp_trace:'冷えきった焚き火の跡。誰かがここで夜を明かしたようだが、ずいぶん前のことらしい。',
    msg_a3_rune_stone:'フィオナ「この石……光ってる。私が近づいたから……？」　古代のルーンが、かすかに風の音を返した。'
  };
  const HOOK_TEXTS={a2_marker_crack_glint:'苔むした古い道標だ。割れ目の奥で、何かが一瞬きらりと光った。'};
  // Rewards are text-only for now (legacy parity); items are decided later (see M4 report).
  const TREASURE={
    tr_a1_hollow:'きずぐすり ×2 を手に入れた。',
    tr_a2_overlook:'風よけの護符 ×1 を手に入れた。',
    tr_a3_shrine:'古びたルーン片 ×1 を手に入れた。'
  };
  const TREASURE_PLACEHOLDER='苔むした小箱の中に、乾いた薬草が少し入っていた。（報酬は仮）';
  const inPrologueForest=()=>storyStage>=9&&storyStage<=12;

  function flagsNow(){
    return {moss_a3_seal_open:PrologueProgress.count()>=3,moss_a3_lou_found:Boolean(louFound),moss_a3_lou_rescued:storyStage>=13};
  }
  function onEvent(z,map){
    if(z.type==='locationCard'){
      const c=map.locationCard;if(c)questPop(c.regionJa+'　―　'+c.areaJa);return;
    }
    switch(z.eventId){
      case 'prologue_rune_stone':
        forestStoneSeen=true;storyStage=Math.max(storyStage,10);say(TEXTS.msg_a3_rune_stone);
        setObj(PrologueProgress.count()>=3?'古代石の周囲で風の気配を探そう':PrologueProgress.objective());return;
      case 'prologue_lou_intro':
        if(PrologueProgress.count()<3)return;
        if(louFound){MossForest.toast('隠された風道が淡く輝いている。');return;}
        startLouIntro();return;
      case 'prologue_altar_scene':
        if(!louFound)return;
        closeDialogue();forestHideScene();startAltarScene();return;
    }
    if(z.textId&&TEXTS[z.textId]){say(TEXTS[z.textId]);return;}
    if(z.hook&&HOOK_TEXTS[z.hook]){say(HOOK_TEXTS[z.hook]);return;}
  }
  function onTreasure(t){MossForest.toast(TREASURE[t.id]||TREASURE_PLACEHOLDER);}
  function onSymbol(sy){startAttackBattle(sy.field,sy.hp||160);}
  function onVillageExit(){
    if(inPrologueForest()||storyStage<15){MossForest.toast('崖の上へ戻る道は、もうない。先へ進むしかなさそうだ。');return true;}
    return false;
  }
  function init(){
    MossForest.configure({hooks:{toast:t=>forestToast(t),isCleared:f=>PrologueProgress.cleared(f),
      sealCorrupted:()=>PrologueProgress.count()<3,onEvent,onTreasure,onSymbol,onVillageExit}});
  }
  // Enter A1 at the cliff-fall spot (new game / DEV jump) or restore a saved position.
  function enterFromStart(){
    MossForest.reset();
    return MossForest.enter({map:MAP_IDS.a1,spawn:'from_cliff_fall',flags:flagsNow()});
  }
  function enterAt(mapId,x,y,state){
    MossForest.restoreState(state);
    return MossForest.enter({map:mapId,x,y,flags:flagsNow()});
  }
  // Restore from a save. v2 carries data.moss; v1 (legacy 1800x1300 forest) is migrated by story progress.
  function fromSave(data,ctx){
    const A=MAP_IDS,moss=data&&data.moss;
    const valid=moss&&Object.values(A).includes(moss.map)&&Number.isFinite(moss.x)&&Number.isFinite(moss.y);
    let mapId,spawn=null,pos=null,state=moss||{};
    if(valid){mapId=moss.map;pos=[moss.x,moss.y];}
    else{
      const chests=(data&&data.forestChests)||{};
      state={opened:[chests.fChest1&&'tr_a1_hollow',chests.fChest2&&'tr_a2_overlook',chests.fChest3&&'tr_a3_shrine'].filter(Boolean),fired:[]};
      if(ctx.louFound||ctx.storyStage>=11){mapId=A.a3;pos=[4395-17,2915-42];}
      else if(ctx.count>=3){mapId=A.a3;pos=[3910-17,3330-42];}
      else if(ctx.count>=1){mapId=A.a3;spawn='from_area2';}
      else{mapId=A.a1;spawn='from_cliff_fall';}
    }
    // A closed seal cannot have the player inside the sanctuary: fall back to the area entrance.
    if(mapId===A.a3&&pos&&ctx.count<3&&pos[1]+42<3300){pos=null;spawn='from_area2';}
    MossForest.reset();MossForest.restoreState(state);
    return MossForest.enter({map:mapId,spawn:spawn||undefined,x:pos?pos[0]:undefined,y:pos?pos[1]:undefined,flags:flagsNow()});
  }
  function syncFlags(){
    const f=flagsNow();for(const [k,v] of Object.entries(f))MossForest.setFlag(k,v);
    MossForest.syncSymbols();
  }
  window.MossForestStory=Object.freeze({init,enterFromStart,enterAt,fromSave,syncFlags,flagsNow,MAP_IDS});
})();

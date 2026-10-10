/* Rilde Village NPC conversation lines (M5). Pure data + a small selector; no story/save hooks.
 * Triggered by the shared 'lind-field-interaction' event (DEV review interaction today). Emma lives in forest-warnings.js.
 * Branch: seal closed (peaceful / unrest) vs open (seal released or prologue cleared). Lines cycle per NPC and state. */
(function () {
  'use strict';
  const NPC={
    boy:{closed:['子どもA「まてー！　待てってばー！　今日の俺は風みたいに速いんだぞー！」',
                 '子どもC「あっ、エイダンお兄ちゃん！　また森へ行くの？　今度、木彫りの剣の振り方教えてよ！」']},
    girl:{closed:['子どもB「きゃはは！　追いつけるわけないでしょー！　エイダンお兄ちゃん、助けてー！」',
                  '子どもD「あ！　エイダンお兄ちゃん、また道に迷いそうになってる！　風の見張り台はあっちだよー！」']},
    young_woman:{closed:['祈る村人「風の神様、どうか今日もこの村に穏やかな風を吹かせてください……。……あ、エイダン。邪魔してごめんね。いつも村を守ってくれてありがとう。」']},
    elder_woman:{closed:['井戸端の村人「井戸のお水も冷たくておいしいけれど、やっぱり美味しいシチューには綺麗な水が欠かせないわね。今夜はうちもシチューにしようかしら。」']},
    hill_old:{closed:['村人「ここは村で一番風がよく通る場所なんだ。落ち込んだ時も、ここで風に吹かれていると不思議と元気が湧いてくるのさ。」',
                      '村人「昔、お前の母さんもよくここから村を眺めていたっけねぇ……。エイダン、お前は本当にお母さん譲りの優しい目をしているよ。」']}
  };
  // Children and villagers keep the same lines after the seal opens until dedicated post-seal text exists.
  const used={};
  const sealOpen=()=>(window.PrologueProgress&&PrologueProgress.count()>=3)||(typeof storyStage==='number'&&storyStage>=13);
  function line(id){
    const set=NPC[id];if(!set)return '';
    const list=(sealOpen()&&set.open)||set.closed,key=id+(list===set.closed?':c':':o');
    const i=(used[key]||0)%list.length;used[key]=i+1;return list[i];
  }
  window.addEventListener('lind-field-interaction',e=>{const id=e.detail&&e.detail.id;if(NPC[id]&&typeof say==='function')say(line(id));});
  window.LindDialogue=Object.freeze({line,NPC});
})();

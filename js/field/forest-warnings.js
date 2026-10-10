/* Elder / Emma warnings about the old forest (M4). Pure lines + state branch; no forest or Lind dependency.
 * Branch: before the seal is released (peaceful village) vs after (seal open / prologue cleared). */
(function () {
  'use strict';
  const LINES={
    elder:{
      closed:['長老「南西の森には近付くでないぞ。あそこの苔は、風を嫌うのじゃ。」',
              '長老「古い森には、古い決まりがあってのう……。若い者がわざわざ確かめに行くものではない。」'],
      open:['長老「……森の風が戻ったと、鳥たちが騒いでおるわい。お前たち、あの森に入ったな。いや、責めはせん。無事で何よりじゃ。」']
    },
    emma:{
      closed:['エマ「エイダン、あの森には入っちゃだめだよ。子どもの頃から言ってるだろう？　……フィオナを連れて行ったら、承知しないからね。」',
              'エマ「風の止まる場所はね、人が長居するところじゃないんだよ。」'],
      open:['エマ「森の風の匂いがするねえ。……何があったのかは聞かないよ。二人とも、ちゃんと帰ってきた。それでいいのさ。」']
    }
  };
  const used={};
  function sealOpen(){return (window.PrologueProgress&&PrologueProgress.count()>=3)||(typeof storyStage==='number'&&storyStage>=13);}
  function line(who){
    const set=LINES[who];if(!set)return '';
    const list=sealOpen()?set.open:set.closed,key=who+(sealOpen()?':open':':closed');
    const i=(used[key]||0)%list.length;used[key]=i+1;return list[i];
  }
  // Emma has no formal conversation yet; the DEV review interaction is the only trigger today.
  window.addEventListener('lind-field-interaction',e=>{if(e.detail&&e.detail.id==='emma'&&typeof say==='function')say(line('emma'));});
  window.ForestWarnings=Object.freeze({line,LINES});
})();

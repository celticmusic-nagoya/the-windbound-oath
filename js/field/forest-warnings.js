/* Elder / Emma warnings about the old forest (M4). Pure lines + state branch; no forest or Lind dependency.
 * Branch: before the seal is released (peaceful village) vs after (seal open / prologue cleared). */
(function () {
  'use strict';
  const LINES={
    elder:{
      closed:['長老「おお、エイダンか。……風の石碑の輝きが弱まっておる。モスの森の奥で、何かが起こっておるのかもしれん。無理は禁物じゃぞ。」',
              '長老「南西の森には近付くでないぞ。あそこの苔は、風を嫌うのじゃ。」'],
      open:['長老「ふむ……森の奥の邪気が晴れ、心地よい風が戻ってきたようじゃな。お前さんたちの頑張りに、風の精霊たちも感謝しておるよ。」']
    },
    emma:{
      closed:['エマ「おや、エイダンかい。……その顔、また何か背負い込んでないかい？　冒険に出るのはお前たちの自由だけどねぇ、無茶をして怪我だけはして帰ってくるんじゃないよ。フィオナも心配するんだからね。」',
              'エマ「最近、モスの森のあたりも空気が重苦しいねぇ……。昔から、あそこは妙な言い伝えがある場所なんだ。あまり奥の方へは近付くんじゃないよ。……ねえエイダン、お前はいつだって誰かを守ろうとするけれどねぇ、自分が傷つくことばかり考えちゃダメだよ。」',
              'フィオナ「おばあちゃん、私たちなら大丈夫だよ。ちゃんと気をつけるから。」　エマ「ふふ、そう言ってすぐ無茶をするんだから。はい、これを持っていきな。私が縫い直したお守りさ。……気をつけてお行き、ふたりとも。」'],
      open:['エマ「やれやれ、村を吹き抜ける風がようやくいつも通りに戻ったようだねぇ。……お前たちが頑張ってくれたおかげかい？　ありがとうねぇ。ほら、こうして穏やかな風を感じながら針仕事ができるだけで、おばあちゃんは十分幸せさね。」',
            'エマ「見てごらん、フィオナ。またエイダンが難しい顔をしてるよ。……まったく、ふたりともいつまでも子供だと思っていたのにねぇ。おいおいエイダン、そんなに真っ赤になって。お似合いのふたりだと言っただけじゃないか。ふふっ。」　フィオナ「もう、おばあちゃん！　からかわないでよ……！」']
    }
  };
  const used={};
  function sealOpen(){return (window.PrologueProgress&&PrologueProgress.count()>=3)||(typeof storyStage==='number'&&storyStage>=13);}
  function line(who){
    const set=LINES[who];if(!set)return '';
    const list=sealOpen()?set.open:set.closed,key=who+(sealOpen()?':open':':closed');
    const i=(used[key]||0)%list.length;used[key]=i+1;return list[i];
  }
  if(window.FieldTalk)FieldTalk.register(['emma','elder'],line);
  window.ForestWarnings=Object.freeze({line,LINES});
})();

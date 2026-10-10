/* Scene conversations (cliff sunset -> stars -> burning village). Pure data, played by FieldScene (js/field/scene-data.js)
 * through FieldTalk, so the speaker plate / tap / choices behave like every other conversation.
 * npc ids are scene ids ("scene_*"), never placed on the field. Format: see js/field/talk-data.js. */
window.TalkDataScenes = Object.freeze({tables: [
  // 風見の断崖のベンチ (stage 3): sit? yes -> flag cliff_bench_sat + the sunset scene (main story advances) / no -> nothing changes, ask again any time
  {npc: 'cliff_bench', entries: [
    {id: 'cliff_bench_ask', priority: 20, when: {stage: [3, 3]}, mode: 'cycle', lines: [{pages: [
      '頂上の草地に、古びたベンチがひとつ。ちょうど、夕日の正面だ。',
      'フィオナ「ねえ、エイダン。少し座っていかない？　……夕日、見ていこうよ。」',
      'ここに座って、夕日を眺めますか？'],
      choice: {options: [
        {label: 'はい', set: {cliff_bench_sat: true}, scene: 'cliff_sunset_to_fire'},
        {label: 'いいえ', reply: ['フィオナ「そっか。……気が向いたら、いつでも声をかけてね。」', 'もう少し、あたりを見ていよう。']}]}}]}]},
  {npc: 'scene_cliff_sunset', entries: [
    {id: 'scene_cliff_sunset_1', priority: 1, mode: 'cycle', lines: [{pages: [
      'フィオナ「間に合ったね。ここから見る夕日は、やっぱりきれい。」',
      '果てのない海が、橙色にとけていく。断崖の草原を、風がやわらかく撫でていった。',
      'エイダン「訓練のあとに、こんな坂道を登らされるとは思わなかったけどな。」',
      'フィオナ「ふふ。エイダン、昔からすぐそういうこと言う。」',
      'フィオナ「ねえ。エイダンは……王都へ行ったら、お父さんみたいな騎士になるの？」',
      'エイダン「まだ分からない。でも――守れるくらいには強くなりたい。」',
      'フィオナ「そっか。」',
      '夕陽が、水平線の向こうへゆっくりと沈んでいく。']}]}]},
  {npc: 'scene_cliff_night', entries: [
    {id: 'scene_cliff_night_1', priority: 1, mode: 'cycle', lines: [{pages: [
      'いつのまにか、空は深い群青に変わっていた。',
      'フィオナ「見て、エイダン。星……こんなにたくさん。」',
      'エイダン「ああ。村の灯りが遠いと、こんなに見えるんだな。」',
      'フィオナ「わたしね、ここで星を見るのが好きなの。……誰かと一緒に見るのは、初めて。」',
      'エイダン「……そうか。」',
      '二人はしばらく、何も言わずに星を見上げていた。',
      'フィオナ「……あれ。風が……止まってる。」',
      '鳥の声も、木々のざわめきも消えた。静けさの底で、遠くから鐘の音が聞こえる。何度も、何度も。',
      'エイダン「鐘……？　こんな時間に？」',
      'フィオナ「村のほうが……なんだか、騒がしい。」']}]}]},
  {npc: 'scene_cliff_fire', entries: [
    {id: 'scene_cliff_fire_1', priority: 1, mode: 'cycle', lines: [{pages: [
      'エイダン「あれは……村が――！」',
      '遠く、リルド村の方角から黒煙が立ちのぼり、赤い炎が夜空を焦がしている。',
      'フィオナ「うそ……みんなが……！」',
      'エイダン「急ぐぞ、フィオナ！　走れるか！」',
      'フィオナ「うん！　……お願い、間に合って……！」']}]}]}
]});

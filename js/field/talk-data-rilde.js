/* 仮(DRAFT) 襲撃後のリルド村の会話. Placeholder wording for the user's scenario to replace.
 * npc ids = the `npc` field of the nodes in data/maps/rilde_village_01_ruin.json (built by tools/moss/build_rilde_village.py).
 * The peaceful village keeps using the M6 tables of talk-data.js (farmer_male, merchant, innkeeper, elder ...).
 * 長老 sets road_dunvall_open (the road east to the fort), same as the legacy village elder did. Delete this file + its <script> tag to remove the draft. */
window.TalkDataRilde = Object.freeze({tables: [
  {npc: 'rr_elder', entries: [
    {id: 'rr_elder_road', priority: 55, mode: 'once', when: {all: [{stage: [15, 99]}, {not: {flag: 'road_dunvall_open'}}]},
     lines: [{pages: ['長老「……エイダンか。よく戻った。村は、見ての通りじゃ。それでも、人は生き延びた。」',
                      '長老「東の街道を行けば、辺境のドゥンヴァル砦に着く。あの砦には、わしの古い知り合いがおる。」',
                      '長老「何かが、この地で目を覚まそうとしておる。お前の旅が、その手がかりになるはずじゃ。」'], set: {road_dunvall_open: true}}]},
    {id: 'rr_elder_fort', priority: 30, mode: 'cycle', when: {flag: 'commander_met'}, lines: ['長老「砦の司令官に会うたか。……あの男は口は堅いが、信用できる。王都でも、風を見失うでないぞ。」']},
    {id: 'rr_elder_a', priority: 10, mode: 'cycle', lines: ['長老「風の石が黙ってしもうた。……風が戻る日まで、わしらはここで待つ。」', '長老「気をつけて行くのじゃぞ。道は、お前の足で開くものじゃ。」']}]},
  // ---- 平和時の長老: talk-data.js の elder_closed に、村の朝の様子の台詞を2つ足す（最初の2つは元のまま）
  {npc: 'elder', entries: [
    {id: 'elder_closed', priority: 10, when: {}, mode: 'cycle', lines: [
      '長老「おお、エイダンか。……風の石碑の輝きが弱まっておる。モスの森の奥地で、何かが起こっておるのかもしれん。無理は禁物じゃぞ。」',
      '長老「南西の森の奥地には、決して近付くでないぞ。あそこの苔は、風を嫌うのじゃ。……手前の森道までなら、気をつけて行くがよい。」',
      '長老「森の奥地には、決して足を踏み入れてはならん。……じゃが近ごろ、その奥から嫌な風が吹いてくるのじゃ。確かめねばならぬ時が来るやもしれん。行くなら、決して無理はするでないぞ。」',
      '長老「今朝は、風が少し重いのう……。訓練に励むのは結構じゃが、日が暮れる前には戻るんじゃぞ。」',
      '長老「風の石碑は、村の見張りじゃ。……お前の父も、よくあの前で剣を握っておった。」']}]},
  {npc: 'rr_oldwoman', entries: [
    {id: 'rr_oldwoman_a', priority: 10, mode: 'cycle', lines: ['村の老婆「家は燃えても、かまどの前で歌った歌は燃えやしないよ。」', '村の老婆「あんたの家の屋根、よく雨漏りしてたねえ。……もう、直す屋根もないけど。」']}]},
  {npc: 'rr_woman', entries: [
    {id: 'rr_woman_a', priority: 10, mode: 'cycle', lines: ['若い女性「井戸の水は濁ってしまって、川まで汲みに行ってるの。」', '若い女性「あの夜のこと、まだ夢に見るわ。……でも、あなたたちが無事で、本当によかった。」']}]},
  {npc: 'rr_farmer', entries: [
    {id: 'rr_farmer_a', priority: 10, mode: 'cycle', lines: ['農夫「麦畑は半分やられた。けど、根は生きてる。来年は、また実るさ。」', '農夫「納屋の梁が焼け落ちる音は、一生忘れんだろうな。」']}]},
  {npc: 'rr_boy', entries: [
    {id: 'rr_boy_a', priority: 10, mode: 'cycle', lines: ['男の子「エイダン兄ちゃん！　フィオナ姉ちゃんと戻ってきてくれたんだ！」', '男の子「僕ね、泣かなかったよ。母さんの手を、ずっと離さなかったんだ。」']}]},
  {npc: 'rr_knight', entries: [
    {id: 'rr_knight_a', priority: 10, mode: 'cycle', lines: ['王国の兵士「ドゥンヴァル砦から救援に来た。怪我人は広場に集めてある。」', '王国の兵士「村の再建には人手がいる。……だが、まずは火を消すのが先だ。」']}]},
  // ---- 街道の開通状況（出口 tr_v_to_fort と東の標識）。出口/標識のどちらも FieldTalk を通す
  {npc: 'rr_road_early', entries: [{id: 'rr_road_early_1', priority: 10, mode: 'cycle', lines: ['街道は東へ続いている。今はまだ、村を離れる時ではない。']}]},
  {npc: 'rr_road_ask', entries: [{id: 'rr_road_ask_1', priority: 10, mode: 'cycle', lines: ['東へ続く街道だ。この先のことは、長老に聞いてみようか。']}]},
  {npc: 'rr_sign_east', entries: [
    {id: 'rr_sign_open', priority: 20, mode: 'cycle', when: {flag: 'road_dunvall_open'}, lines: ['焦げた木の標識：『← リルド村　／　ドゥンヴァル砦 →』', '誰かが標識の根元に、新しい松明を立てかけていった。街道は砦まで続いている。']},
    {id: 'rr_sign_closed', priority: 10, mode: 'cycle', lines: ['焦げた木の標識：『← リルド村　／　ドゥンヴァル砦 →』']}]},
  {npc: 'rr_knight2', entries: [
    {id: 'rr_knight2_a', priority: 10, mode: 'cycle', lines: ['王国の兵士「東の街道は、砦まで安全を確保している。夜は松明を目印にするといい。」']}]}
]});

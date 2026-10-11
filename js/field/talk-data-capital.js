/* 仮(DRAFT) ドゥンヴァル砦・王都の会話 (M8). Placeholder wording for the user's scenario to replace.
 * npc ids = the `npc` field of the map nodes (data/maps/fort_dunvall_*.json, royal_capital_*.json, built by tools/moss/build_town_maps.py).
 * Shops open through a talk choice {shop:id} or directly from a node's `shop` field. Delete this file + its <script> tag to remove the draft. */
window.TalkDataCapital = Object.freeze({tables: [
  // ---- 村の長老: 街道が開く（仮）
  {npc: 'elder', entries: [
    {id: 'elder_road', priority: 55, mode: 'cycle', when: {all: [{stage: [15, 99]}, {not: {flag: 'road_dunvall_open'}}]},
     lines: [{pages: ['長老「エイダンよ。村の東の街道を行けば、辺境のドゥンヴァル砦に着く。」', '長老「あの砦には、わしの古い知り合いがおる。……いずれ、お前の旅の助けになるじゃろう。」'],
              set: {road_dunvall_open: true}}]}
  ]},
  // ---- ドゥンヴァル砦
  {npc: 'f1_captain', entries: [
    {id: 'f1_captain_a', priority: 10, mode: 'cycle', lines: ['砦の隊長「ここはドゥンヴァル砦。辺境を守る最後の砦だ。旅の者なら、兵舎で休んでいくといい。」', '砦の隊長「近ごろ、街道の向こうが騒がしい。王都へ行くなら、気をつけてな。」']}]},
  {npc: 'f1_quartermaster', entries: [
    {id: 'f1_qm_a', priority: 10, mode: 'cycle', lines: [{pages: ['補給係「武具ならここだ。兵士向けの実用品ばかりだが、質は保証するぞ。」'],
       choice: {options: [{label: '買い物をする', shop: 'dunvall_arms'}, {label: 'やめておく', reply: '補給係「必要になったらまた来な。」'}]}}]}]},
  {npc: 'f1_gate_guard', entries: [
    {id: 'f1_gate_a', priority: 10, mode: 'cycle', lines: ['門番「南の門はリルド村への街道、東の門は王都への街道だ。」', '門番「夜は松明の灯りを目印にするといい。」']}]},
  {npc: 'f2_lookout', entries: [
    {id: 'f2_look_a', priority: 10, mode: 'cycle', lines: ['見張りの兵士「ここからは遠くまで見渡せる。……今日は、静かなものだ。」']}]},
  {npc: 'f3_commander', entries: [
    {id: 'f3_cmd_elder', priority: 45, mode: 'once', when: {all: [{flag: 'road_dunvall_open'}, {not: {flag: 'commander_met'}}]},
     lines: [{pages: ['司令官「リルドの長老の使いか。……あの男から、話は聞いている。」', '司令官「森の黒紫の魔物、焼かれた村。辺境だけの事件で済むとは思えん。」',
                      '司令官「王都カエルディンの騎士団へ、お前たちの目で見たものを報告してくれ。街道は東門を出て、まっすぐだ。」'], set: {commander_met: true}}]},
    {id: 'f3_cmd_after', priority: 30, mode: 'cycle', when: {flag: 'commander_met'}, lines: ['司令官「王都は街道の先だ。南大城門をくぐれば、城がよく見える。……風の加護を。」']},
    {id: 'f3_cmd_a', priority: 10, mode: 'cycle', lines: ['司令官「よく来た、旅の剣士よ。砦はいつでも、志ある者を歓迎する。」']}]},
  {npc: 'f3_armory', entries: [
    {id: 'f3_arm_a', priority: 10, mode: 'cycle', lines: ['武器庫番「ここの品は王国の物資だ。勝手には渡せんが……補給係に頼めば、手頃な品が手に入るはずだ。」']}]},
  {npc: 'f1_bed', entries: []},
  // ---- 砦の酒場: 酔っ払いのドワーフ（匿名の先行登場。名前は出さない。王都のブラムの工房で再会する）
  {npc: 'f4_dwarf', entries: [
    {id: 'f4_dw_after', priority: 40, mode: 'cycle', when: {flag: 'liam_joined'},
     lines: ['酔っ払いのドワーフ「旅ぃ？ そんなもん明日にしろ！ 生きてる奴が酒場に集まったんなら宴だ、宴！」', '酔っ払いのドワーフ「ま、行くってんなら止めやせん。……気をつけて行けよ、若造ども。」']},
    {id: 'f4_dw_a', priority: 10, mode: 'cycle',
     lines: ['酔っ払いのドワーフ「素材を仕入れに来ただけだったんだがなぁ……。ここの黒麦酒がうまいのが悪い！」',
             {pages: ['酔っ払いのドワーフ「旅ぃ？ そんなもん明日にしろ！ 生きてる奴が酒場に集まったんなら宴だ、宴！」', 'エイダン「あの、黒紫の魔物を見たことは……」', '酔っ払いのドワーフ「…………黒紫、ねぇ。」', '（一瞬だけ、酔いの抜けた目をした気がした。傍らの荷物から、古い金属片が覗いている。）']}]}]},
  // ---- 王都・南大城門と旅人街
  {npc: 'g_gate_guard', entries: [
    {id: 'g_gg_a', priority: 10, mode: 'cycle', lines: ['門番「ようこそ、王都カエルディンへ。……辺境の方は、最近物騒だと聞く。街道は無事だったか？」', '門番「北へ進めば商業地区、その先が中央広場だ。王城は高台に見えるだろう？」']}]},
  {npc: 'g_merchant', entries: [
    {id: 'g_mc_a', priority: 10, mode: 'cycle', lines: ['荷馬車の商人「検問が長くてね。だが王都の市場は、辺境の何倍も儲かるのさ。」']}]},
  {npc: 'g_pilgrim', entries: [
    {id: 'g_pg_a', priority: 10, mode: 'cycle', lines: ['巡礼者「大聖堂へお参りに来たのです。魔王を封じた英雄たちの姿が、今も祀られていると聞いて。」']}]},
  {npc: 'g_adv', entries: [
    {id: 'g_ad_a', priority: 10, mode: 'cycle', lines: ['駆け出しの冒険者「隣のギルドで依頼を受けたんだ。夜は大酒場になって、すごい賑わいだぜ。」']}]},
  // ---- 冒険者ギルド兼大酒場
  {npc: 'g_reception', entries: [
    {id: 'g_rc_a', priority: 10, mode: 'cycle', lines: ['受付「ここは冒険者ギルドです。討伐、護衛、採取、遺跡調査、配達……依頼は掲示板に貼り出されています。」', '受付「2階は会議室、地下は倉庫です。いまは立ち入れませんが……。」']}]},
  {npc: 'g_barkeep', entries: [
    {id: 'g_bk_a', priority: 10, mode: 'cycle', lines: ['大酒場の主人「昼はおとなしいもんだが、夜になるとここは王都一の大騒ぎさ。また来な。」']}]},
  {npc: 'g_patron1', entries: [
    {id: 'g_p1_a', priority: 10, mode: 'cycle', lines: ['冒険者「遺跡調査の依頼は、いつも王立の連中が先に押さえちまうんだ。」']}]},
  {npc: 'g_patron2', entries: [
    {id: 'g_p2_a', priority: 10, mode: 'cycle', lines: ['酔った旅人「うぃ……宴ってのはいいもんだ。歌と、踊りと、酒があれば……。」']}]},
  {npc: 'g_bard', entries: [
    {id: 'g_bd_a', priority: 10, mode: 'cycle', lines: ['吟遊詩人「この王都は、昔の都の上に建っているんだって。足元に眠る歌も、いつか拾ってみたいね。」']}]},
  {npc: 'g_upstairs', entries: [
    {id: 'g_up_a', priority: 10, mode: 'cycle', lines: ['2階はギルドの会議室になっている。今は関係者以外、立ち入れないようだ。']}]},
  // ---- 宿屋
  {npc: 'r1_inn', entries: [
    {id: 'r1i_a', priority: 10, mode: 'cycle', lines: ['宿屋の主人「ようこそ、旅人の灯へ。ベッドはご自由に。ぐっすり休めば、体力も魔力も元通りですよ。」']}]},
  {npc: 'in_bed', entries: []},
  {npc: 'in_guest', entries: [
    {id: 'in_g_a', priority: 10, mode: 'cycle', lines: ['旅の客「王都の宿は、ギルドの隣が一番だ。依頼帰りにそのまま休めるからね。」']}]},
  // ---- 王都・商業区
  {npc: 'r1_board', entries: [
    {id: 'r1b_report', priority: 60, mode: 'once', when: {quest: {id: 'q_capital_delivery', state: 'complete'}},
     lines: [{pages: ['掲示板の担当「きずぐすり3つ、確かに受け取りました。助かります！」', '掲示板の担当「これは依頼主からのお礼です。どうぞ。」'], take: {potion: 3}, quest: {id: 'q_capital_delivery', action: 'report'}}]},
    {id: 'r1b_active', priority: 50, mode: 'cycle', when: {quest: {id: 'q_capital_delivery', state: 'active'}},
     lines: ['掲示板の担当「納品は、きずぐすり3つです。村の道具屋でも王都の雑貨商でも買えますよ。」']},
    {id: 'r1b_offer', priority: 45, mode: 'cycle', when: {quest: {id: 'q_capital_delivery', state: 'unaccepted'}},
     lines: [{pages: ['掲示板の担当「商業区の納品依頼が出ています。きずぐすりを3つ、急ぎで必要だそうです。」'],
              choice: {options: [{label: '引き受ける', reply: '掲示板の担当「ありがとうございます！　集まったら、また声をかけてください。」', quest: {id: 'q_capital_delivery', action: 'accept'}},
                                 {label: '今はやめておく', reply: '掲示板の担当「分かりました。気が向いたらどうぞ。」'}]}}]},
    {id: 'r1b_thanks', priority: 30, mode: 'cycle', when: {quest: {id: 'q_capital_delivery', state: 'reported'}},
     lines: ['掲示板の担当「先日は助かりました。また依頼が入ったらお願いします。」']}]},
  {npc: 'r1_rumor', entries: [
    {id: 'r1r_a', priority: 10, mode: 'cycle', lines: ['商人「聞いたかい？　辺境の方で、妙な気配がするって噂だ。」', '商人「王都の鍛冶師は腕がいい。武具屋で良い剣を探してみな。」', '商人「城前広場の花壇には、ときどき落とし物があるそうだよ。」']}]},
  {npc: 'r1_child', entries: [
    {id: 'r1c_a', priority: 10, mode: 'cycle', lines: ['子ども「あっち！　あっちに噴水があるんだよ！」', '子ども「おにいちゃん、剣士？　かっこいい！」']}]},
  {npc: 'r1_general', entries: []}, {npc: 'r1_weapon', entries: []},
  // ---- 王都・城前広場
  {npc: 'r2_guard', entries: [
    {id: 'r2g_a', priority: 10, mode: 'cycle', lines: ['衛兵「ここから先は王城だ。今は謁見の予定のない者は通せない。」']}]},
  {npc: 'r2_bard', entries: [
    {id: 'r2b_a', priority: 10, mode: 'cycle', lines: ['吟遊詩人「風の誓いの歌を知っているかい？　古い古い、辺境の歌さ。」', '吟遊詩人「……おや、その剣。いい顔をしているね。」']}]},
  {npc: 'r2_herald', entries: [
    {id: 'r2h_a', priority: 10, mode: 'cycle', lines: ['触れ役「王都の掲示板に、旅の方へのお願いが出ております。商業区の掲示板をご覧ください。」']}]},
  // ---- 王都・住宅街
  {npc: 'r3_resident', entries: [
    {id: 'r3r_a', priority: 10, mode: 'cycle', lines: ['住民「住宅街は静かでいい所よ。商業区は賑やかすぎてね。」', '住民「あのおばあさん、ずっと探し物をしているみたい。声をかけてあげて。」']}]},
  {npc: 'r3_cat_man', entries: [
    {id: 'r3c_a', priority: 10, mode: 'cycle', lines: ['男「この猫、どこの家の子でもないんだ。毎日ここで待ってるのさ。」']}]},
  {npc: 'r3_elder_quest', entries: [
    {id: 'r3e_report', priority: 60, mode: 'once', when: {quest: {id: 'q_capital_comb', state: 'complete'}},
     lines: [{pages: ['老婦人「ああ……！　これよ、この櫛よ。亡くなった主人からの贈り物だったの。」', '老婦人「本当にありがとう。ささやかだけれど、お礼を受け取ってちょうだい。」'], take: {silver_comb: 1}, quest: {id: 'q_capital_comb', action: 'report'}}]},
    {id: 'r3e_active', priority: 50, mode: 'cycle', when: {quest: {id: 'q_capital_comb', state: 'active'}},
     lines: ['老婦人「広場の花壇のあたりで落としたと思うの。銀の櫛なのよ。」']},
    {id: 'r3e_offer', priority: 45, mode: 'cycle', when: {quest: {id: 'q_capital_comb', state: 'unaccepted'}},
     lines: [{pages: ['老婦人「ああ、困ったわ……。大切な銀の櫛を、どこかで失くしてしまって。」', '老婦人「城前広場の花壇のあたりを歩いたの。見てきてくださらないかしら？」'],
              choice: {options: [{label: '探してみる', reply: '老婦人「ありがとう、優しい方ね。お願いしますよ。」', quest: {id: 'q_capital_comb', action: 'accept'}},
                                 {label: '今は難しい', reply: '老婦人「そう……。気が向いたら、また声をかけてね。」'}]}}]},
    {id: 'r3e_thanks', priority: 30, mode: 'cycle', when: {quest: {id: 'q_capital_comb', state: 'reported'}},
     lines: ['老婦人「あの櫛、毎朝つかっているのよ。ありがとうね。」']}]},
  // ---- 街道（砦〜王都）・丘の上からの王都一望（初回はカメラ演出つき）
  {npc: 'road_overlook', entries: [
    {id: 'road_overlook_first', priority: 50, mode: 'once',
     lines: [{pages: ['エイダン「……あれが、王都か。」', 'フィオナ「大きい……。谷の向こうまで、街がずっと続いてる。」',
                      'エイダン「村から出たことのなかった俺たちが、あんな場所へ行くんだな。」', 'フィオナ「うん。……行こう、エイダン。風はこっちに吹いてるよ。」'],
              set: {road_overlook_seen: true}}]}]},
  {npc: 'road_overlook_view', entries: [
    {id: 'road_overlook_again', priority: 10, mode: 'cycle', lines: ['谷の向こうに、王都の城壁と塔が霞んで見える。道はここから、王都へ向かって下っていく。']}]},
  {npc: 'rd_traveler', entries: [
    {id: 'rd_trav_a', priority: 10, mode: 'cycle', lines: ['旅の商人「王都へ行くのかい？ この丘から見える景色は一見の価値ありだ。急がば回れ、ってね。」', '旅の商人「砦の酒場に、王都へ戻る連れを探してる若いのがいたよ。腕は立つらしい。」']}]},
  {npc: 'rd_patrol', entries: [
    {id: 'rd_patrol_a', priority: 10, mode: 'cycle', lines: ['巡回の兵士「この街道は砦の管轄だ。日が落ちる前に、丘を越えておくといい。」']}]},
  // ---- ドゥンヴァル砦・酒場「錆びた角笛」 リアム加入イベント
  {npc: 'liam', entries: [
    {id: 'liam_intro', priority: 70, mode: 'once', when: {stage: [15, 99]},
     lines: [{pages: ['酒場の隅で、赤いバンダナの青年が古びた地図を広げている。', 'リアム「……ん？ 見ない顔だな。その剣、ただの飾りじゃなさそうだ。」', 'エイダン「あなたは？」',
                      'リアム「リアム。つい最近まで、王国の遺跡調査員をやってた——今はしがないトレジャーハンターさ。」',
                      'リアム「腰の短めの剣と、背中の弓。道中の面倒ごとなら、これで十分さ。」',
                      'リアム「王都へ戻る連れを探してたんだ。最近の街道は物騒でね。……どうだい、俺を連れていかないか？ 足と目には自信がある。」'],
              choice: {options: [{label: '仲間に誘う', reply: ['リアム「決まりだな！ よろしく頼むぜ、エイダン。」', 'フィオナ「よろしくね、リアムさん。」', '（リアムが仲間に加わった！）'], set: {liam_joined: true}, join: 'liam'},
                                 {label: 'また今度', reply: 'リアム「そうか。気が変わったら声をかけてくれ。ここで地図とにらめっこしてるよ。」'}]}}]},
    {id: 'liam_ask', priority: 60, mode: 'cycle', when: {all: [{talked: 'liam_intro'}, {not: {flag: 'liam_joined'}}]},
     lines: [{pages: ['リアム「お、考えは決まったかい？ 王都までの道案内なら任せてくれ。」'],
              choice: {options: [{label: '仲間に誘う', reply: ['リアム「待ってたぜ！ 改めて、よろしくな。」', '（リアムが仲間に加わった！）'], set: {liam_joined: true}, join: 'liam'},
                                 {label: 'まだ早い', reply: 'リアム「了解。いつでも声をかけてくれ。」'}]}}]},
    {id: 'liam_after', priority: 20, mode: 'cycle', when: {flag: 'liam_joined'}, lines: ['リアム「さあ、行こうぜ。」']}]},
  {npc: 'f4_barkeep', entries: [
    {id: 'f4_bk_after', priority: 30, mode: 'cycle', when: {flag: 'liam_joined'}, lines: ['酒場の主人「あの兄ちゃん、やっと連れが見つかったか。道中、気をつけてな。」']},
    {id: 'f4_bk_a', priority: 10, mode: 'cycle', lines: ['酒場の主人「ようこそ、錆びた角笛へ。……隅の席の兄ちゃんが、ずっと王都行きの連れを探してるよ。話してみちゃどうだい。」']}]},
  {npc: 'f4_patron1', entries: [
    {id: 'f4_p1_a', priority: 10, mode: 'cycle', lines: ['常連の男「砦の兵隊さんは気前がいい。ここで飲む麦酒は、辺境一だぞ。」']}]},
  {npc: 'f4_patron2', entries: [
    {id: 'f4_p2_a', priority: 10, mode: 'cycle', lines: ['旅の女「王都までは街道を東へ。丘の上から見る景色は、きっと忘れられないわ。」']}]},
  {npc: 'f4_bard', entries: [
    {id: 'f4_bard_a', priority: 10, mode: 'cycle', lines: ['吟遊詩人「風の石の歌を知ってるかい？ 古い辺境の唄さ。……ふふ、続きはまた今度。」']}]}
]});

/* 仮(DRAFT) quest / key-item conversations (M6). Entries are merged into the NPC tables of talk-data.js.
 * Delete this file (and its <script> tag) to remove the draft scenario; nothing else depends on it.
 *   quest states for `when`: unaccepted | active | complete | reported            (see js/quest.js)
 *   effects: {quest:{id,action:'accept'|'report'}} {set:{flag:true}} {give:{item:n}} */
window.TalkDataQuests = Object.freeze({tables: [
  {npc: 'emma', entries: [
    // found the charm before being asked: she recognises it and the quest closes in one conversation
    {id: 'emma_q_found_early', priority: 62, mode: 'once',
     when: {all: [{quest: {id: 'q_emma_charm', state: 'unaccepted'}}, {item: 'charm_windward'}]},
     lines: [{pages: ['エマ「おや、エイダン。それは……わたしの編んだ護符じゃないか！」', 'エマ「森の道で落としたきり、あきらめていたんだよ。ありがとうねぇ。」', 'エマ「これは持っておいき。きっとまた、お前を守ってくれるよ。」'],
              quest: {id: 'q_emma_charm', action: 'report'}}]},
    {id: 'emma_q_report', priority: 60, mode: 'once',
     when: {quest: {id: 'q_emma_charm', state: 'complete'}},
     lines: [{pages: ['エマ「おや、それは……！　わたしの護符じゃないか。」', 'エマ「ほんとうにありがとうよ、エイダン。これは持っておいき。きっとまた、お前を守ってくれるよ。」'],
              quest: {id: 'q_emma_charm', action: 'report'}}]},
    {id: 'emma_q_active', priority: 50, mode: 'cycle',
     when: {quest: {id: 'q_emma_charm', state: 'active'}},
     lines: ['エマ「護符は見つかったかい？　森の道の、見晴らしのよいあたりで落とした気がするんだけどねぇ。」']},
    {id: 'emma_q_offer', priority: 45, mode: 'cycle',
     when: {all: [{quest: {id: 'q_emma_charm', state: 'unaccepted'}}, {any: [{talked: 'emma_closed'}, {talked: 'emma_open'}]}]},
     lines: [{pages: ['エマ「そういえばエイダン。昔わたしが編んだ風よけの護符を、森の道で落としてしまってねぇ。」', 'エマ「もし見つけたら、届けてくれないかい？」'],
              choice: {options: [
                {label: '探してみるよ', reply: 'エマ「ありがとうねぇ。無理はしないでおくれよ。」', quest: {id: 'q_emma_charm', action: 'accept'}},
                {label: '今は難しい', reply: 'エマ「いいんだよ、気が向いたらでね。」'}]}}]},
    {id: 'emma_q_thanks', priority: 30, mode: 'once',
     when: {quest: {id: 'q_emma_charm', state: 'reported'}},
     lines: ['エマ「その護符、大事にしておくれ。風のお守りだからねぇ。」']}
  ]},
  {npc: 'elder', entries: [
    {id: 'elder_shard_ask', priority: 50, mode: 'cycle',
     when: {all: [{item: 'rune_shard_old'}, {not: {flag: 'elder_saw_shard'}}]},
     lines: [{pages: ['長老「エイダンよ、その手に持っているものを、わしに見せてくれんか？」'],
              choice: {options: [
                {label: '見せる', reply: ['長老「……ふむ。古いルーンじゃな。風の石碑のものと、よく似た刻みをしておる。」', '長老「大事にしまっておきなさい。」'], set: {elder_saw_shard: true}},
                {label: '見せない', reply: '長老「そうか。気が向いたら、いつでも見せておくれ。」'}]}}]},
    {id: 'elder_shard_after', priority: 40, mode: 'cycle',
     when: {flag: 'elder_saw_shard'},
     lines: ['長老「その石片のことは、わしも気にかけておこう。何か分かったら、知らせるぞ。」']}
  ]},
  {npc: 'elder_man', entries: [
    {id: 'oldman_q_show', priority: 60, mode: 'cycle',
     when: {all: [{item: 'rune_shard_old'}, {not: {quest: {id: 'q_oldman_rune', state: 'reported'}}}]},
     lines: [{pages: ['老人「ふむ……お前さんの持っておるその石片、ただのガラクタではなさそうじゃな。」', '老人「どれ、少し見せてはくれんか？」'],
              choice: {options: [
                {label: 'ルーン片を見せる', reply: ['老人「おお、これは……！　苔むす森の奥に眠ると言われる、古い刻印じゃ。」', '老人「かつてこの地を守っていた力が、まだ微かに残っておる。」', '老人「見せてくれた礼じゃ。これを持っていきなさい。」'], set: {knows_forest_lore: true}, quest: {id: 'q_oldman_rune', action: 'report'}},
                {label: '見せない', reply: '老人「ほう、用心深いのは良いことじゃ。見せたくなったら、いつでも声をかけなさい。」'}]}}]},
    {id: 'oldman_q_active', priority: 50, mode: 'cycle',
     when: {quest: {id: 'q_oldman_rune', state: 'active'}},
     lines: ['老人「森で古い石の欠片を見かけたら、わしに見せておくれ。」', '老人「風の石碑のあたりに、昔の名残があるやもしれんのう。」']},
    {id: 'oldman_q_offer', priority: 45, mode: 'cycle',
     when: {quest: {id: 'q_oldman_rune', state: 'unaccepted'}},
     lines: [{pages: ['老人「この村も、昔は静かで平和な場所じゃった。」', '老人「近ごろは、森の奥から冷たい風が吹き抜けるようになってのう……何か嫌な予感がするのじゃよ。」', '老人「もし森で古いルーンの欠片を見つけたら、わしに見せてくれんか。昔の言い伝えなら、少しは知っておる。」'],
              choice: {options: [
                {label: '探してみる', reply: '老人「頼むぞ、若いの。無理はせんようにな。」', quest: {id: 'q_oldman_rune', action: 'accept'}},
                {label: '今は難しい', reply: '老人「そうか、そうか。気が向いたらでよい。」'}]}}]},
    {id: 'oldman_q_thanks', priority: 30, mode: 'cycle',
     when: {quest: {id: 'q_oldman_rune', state: 'reported'}},
     lines: ['老人「森の見守りは、まだ消えてはおらん。お前さんの行く道に、古い加護があらんことをな。」']}
  ]},
  {npc: 'farmer_female', entries: [
    {id: 'farmerf_q_report', priority: 60, mode: 'once',
     when: {quest: {id: 'q_farmer_herb', state: 'complete'}},
     lines: [{pages: ['農婦「あら！　頼んでいた薬草を持ってきてくれたのね。」', '農婦「これで畑の土を元どおりに整えられるわ。ほんの気持ちだけど、受け取って！」'],
              take: {herb_moss: 3}, quest: {id: 'q_farmer_herb', action: 'report'}}]},
    {id: 'farmerf_q_active', priority: 50, mode: 'cycle',
     when: {quest: {id: 'q_farmer_herb', state: 'active'}},
     lines: ['農婦「薬草は3つあれば足りるの。森の近くで見つかると思うけど、無理はしないでね。」']},
    {id: 'farmerf_q_offer', priority: 45, mode: 'cycle',
     when: {quest: {id: 'q_farmer_herb', state: 'unaccepted'}},
     lines: [{pages: ['農婦「はぁ……困ったわね。せっかく育った作物が、このままじゃ出荷できないの。」', '農婦「ねえ旅の人、少し手伝ってくれないかしら？」'],
              choice: {options: [
                {label: '話を聞く', reply: ['農婦「ほんと！？　助かるわ！」', '農婦「畑の土を整えるのに、「薬草」が3つ必要なの。森の近くで手に入ると思うから、集まったら声をかけてね。」'], quest: {id: 'q_farmer_herb', action: 'accept'}},
                {label: '今は難しい', reply: '農婦「そうよね、旅の人にも都合があるわよね。手が空いたらまた声をかけて。」'}]}}]},
    {id: 'farmerf_q_thanks', priority: 30, mode: 'cycle',
     when: {quest: {id: 'q_farmer_herb', state: 'reported'}},
     lines: ['農婦「おかげで畑も落ち着いてきたわ。本当にありがとうね。」']}
  ]}
]});

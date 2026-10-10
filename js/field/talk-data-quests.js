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
  ]}
]});

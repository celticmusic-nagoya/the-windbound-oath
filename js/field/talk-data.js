/* Village / forest-warning conversation tables (M5 lines, converted to data in M6). Pure data.
 * Entry: {id, priority, when, mode:'cycle'|'once'|'random', lines:[conversation...]}.
 *   conversation = "話者「台詞」　話者2「台詞」" (a string; split into pages per speaker)
 *                | {pages:["…"|{speaker,text}], choice:{options:[{label, reply?, set?, give?}]}, set?, give?}
 * Highest priority entry whose `when` holds is played (see talk-conditions.js). Entry ids are the save keys: do not rename. */
window.TalkData = Object.freeze({tables: [
 {
  "npc": "boy",
  "entries": [
   {
    "id": "boy_closed",
    "priority": 10,
    "when": {},
    "mode": "cycle",
    "lines": [
     "子どもA「まてー！　待てってばー！　今日の俺は風みたいに速いんだぞー！」",
     "子どもC「あっ、エイダンお兄ちゃん！　また森へ行くの？　今度、木彫りの剣の振り方教えてよ！」"
    ]
   }
  ]
 },
 {
  "npc": "girl",
  "entries": [
   {
    "id": "girl_closed",
    "priority": 10,
    "when": {},
    "mode": "cycle",
    "lines": [
     "子どもB「きゃはは！　追いつけるわけないでしょー！　エイダンお兄ちゃん、助けてー！」",
     "子どもD「あ！　エイダンお兄ちゃん、また道に迷いそうになってる！　風の見張り台はあっちだよー！」"
    ]
   }
  ]
 },
 {
  "npc": "young_woman",
  "entries": [
   {
    "id": "young_woman_closed",
    "priority": 10,
    "when": {},
    "mode": "cycle",
    "lines": [
     "祈る村人「風の神様、どうか今日もこの村に穏やかな風を吹かせてください……。……あ、エイダン。邪魔してごめんね。いつも村を守ってくれてありがとう。」"
    ]
   }
  ]
 },
 {
  "npc": "elder_woman",
  "entries": [
   {
    "id": "elder_woman_closed",
    "priority": 10,
    "when": {},
    "mode": "cycle",
    "lines": [
     "井戸端の村人「井戸のお水も冷たくておいしいけれど、やっぱり美味しいシチューには綺麗な水が欠かせないわね。今夜はうちもシチューにしようかしら。」"
    ]
   }
  ]
 },
 {
  "npc": "farmer_male",
  "entries": [
   {
    "id": "farmer_male_closed",
    "priority": 10,
    "when": {},
    "mode": "cycle",
    "lines": [
     "農夫「やあ、エイダン。今日もいい風が吹いているな。こういう日は作物もよく育つ。……お前さんも、あんまり無理をして体を壊すんじゃないぞ。」"
    ]
   }
  ]
 },
 {
  "npc": "caretaker",
  "entries": [
   {
    "id": "caretaker_closed",
    "priority": 10,
    "when": {},
    "mode": "cycle",
    "lines": [
     "家畜の世話係「おや、エイダン。訓練の帰りかい？　ほら、この牛たちもすっかりお前に慣れてる。……若いのに、いつも村のことを気にかけてくれてありがとうよ。」"
    ]
   }
  ]
 },
 {
  "npc": "young_man",
  "entries": [
   {
    "id": "young_man_closed",
    "priority": 10,
    "when": {},
    "mode": "cycle",
    "lines": [
     "訓練場の村人「あそこの木人、お前が打ち込むからすっかり傷だらけじゃないか。また新しいのを立てておいてやるよ。……でも、無茶して怪我したらフィオナちゃんに怒られるから加減しとけよ？」"
    ]
   }
  ]
 },
 {
  "npc": "innkeeper",
  "entries": [
   {
    "id": "innkeeper_closed",
    "priority": 10,
    "when": {},
    "mode": "cycle",
    "lines": [
     "宿屋の主人「いらっしゃい、エイダン。今日もよく動いていたねぇ。……冒険に出るのも大事だが、しっかり食べてしっかり寝るのが一番の基本さ。あったかいシチューを用意してるから、いつでもおいで。」"
    ]
   }
  ]
 },
 {
  "npc": "inn_traveler",
  "entries": [
   {
    "id": "inn_traveler_closed",
    "priority": 10,
    "when": {},
    "mode": "cycle",
    "lines": [
     "宿泊中の旅人「いやぁ、この村は静かでいい所だねぇ……って、モスの森のあたりは最近なにやら不穏な噂もあるようだが。君はあそこの若い剣士かい？　どうか気をつけてな。」"
    ]
   }
  ]
 },
 {
  "npc": "merchant",
  "entries": [
   {
    "id": "merchant_closed",
    "priority": 10,
    "when": {},
    "mode": "cycle",
    "lines": [
     "道具屋の店主「おお、エイダンか。冒険の準備かい？　うちの薬やロープは品質には自信がある代物さ。森へ行くなら、傷薬は多めに持っていきなよ。」"
    ]
   }
  ]
 },
 {
  "npc": "fisherman",
  "entries": [
   {
    "id": "fisherman_closed",
    "priority": 10,
    "when": {},
    "mode": "cycle",
    "lines": [
     "釣り人「おっ、邪魔するなよ、今いいところなんだから。ここの川の水は冷たくて綺麗なもんでね、うまい魚がよく釣れるんだ。……お前も気分転換にどうだ？」"
    ]
   }
  ]
 },
 {
  "npc": "hill_old",
  "entries": [
   {
    "id": "hill_old_closed",
    "priority": 10,
    "when": {},
    "mode": "cycle",
    "lines": [
     "村人「ここは村で一番風がよく通る場所なんだ。落ち込んだ時も、ここで風に吹かれていると不思議と元気が湧いてくるのさ。」",
     "村人「昔、お前の母さんもよくここから村を眺めていたっけねぇ……。エイダン、お前は本当にお母さん譲りの優しい目をしているよ。」"
    ]
   }
  ]
 },
 {
  "npc": "elder",
  "entries": [
   {
    "id": "elder_closed",
    "priority": 10,
    "when": {},
    "mode": "cycle",
    "lines": [
     "長老「おお、エイダンか。……風の石碑の輝きが弱まっておる。モスの森の奥で、何かが起こっておるのかもしれん。無理は禁物じゃぞ。」",
     "長老「南西の森には近付くでないぞ。あそこの苔は、風を嫌うのじゃ。」"
    ]
   },
   {
    "id": "elder_open",
    "priority": 20,
    "when": {
     "sealOpen": true
    },
    "mode": "cycle",
    "lines": [
     "長老「ふむ……森の奥の邪気が晴れ、心地よい風が戻ってきたようじゃな。お前さんたちの頑張りに、風の精霊たちも感謝しておるよ。」"
    ]
   }
  ]
 },
 {
  "npc": "emma",
  "entries": [
   {
    "id": "emma_closed",
    "priority": 10,
    "when": {},
    "mode": "cycle",
    "lines": [
     "エマ「おや、エイダンかい。……その顔、また何か背負い込んでないかい？　冒険に出るのはお前たちの自由だけどねぇ、無茶をして怪我だけはして帰ってくるんじゃないよ。フィオナも心配するんだからね。」",
     "エマ「最近、モスの森のあたりも空気が重苦しいねぇ……。昔から、あそこは妙な言い伝えがある場所なんだ。あまり奥の方へは近付くんじゃないよ。……ねえエイダン、お前はいつだって誰かを守ろうとするけれどねぇ、自分が傷つくことばかり考えちゃダメだよ。」",
     "フィオナ「おばあちゃん、私たちなら大丈夫だよ。ちゃんと気をつけるから。」　エマ「ふふ、そう言ってすぐ無茶をするんだから。はい、これを持っていきな。私が縫い直したお守りさ。……気をつけてお行き、ふたりとも。」"
    ]
   },
   {
    "id": "emma_open",
    "priority": 20,
    "when": {
     "sealOpen": true
    },
    "mode": "cycle",
    "lines": [
     "エマ「やれやれ、村を吹き抜ける風がようやくいつも通りに戻ったようだねぇ。……お前たちが頑張ってくれたおかげかい？　ありがとうねぇ。ほら、こうして穏やかな風を感じながら針仕事ができるだけで、おばあちゃんは十分幸せさね。」",
     "エマ「見てごらん、フィオナ。またエイダンが難しい顔をしてるよ。……まったく、ふたりともいつまでも子供だと思っていたのにねぇ。おいおいエイダン、そんなに真っ赤になって。お似合いのふたりだと言っただけじゃないか。ふふっ。」　フィオナ「もう、おばあちゃん！　からかわないでよ……！」"
    ]
   }
  ]
 }
]});
